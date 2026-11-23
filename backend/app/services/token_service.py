"""Immutable token ledger. Every balance change creates a transaction row."""

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ConflictError
from app.models.monetization import (
    TokenAccount,
    TokenTransaction,
    TransactionType,
)


async def get_or_create_account(session: AsyncSession, user_id) -> TokenAccount:
    account = await session.get(TokenAccount, user_id)
    if account is None:
        account = TokenAccount(user_id=user_id, balance=0)
        session.add(account)
        await session.flush()
    return account


async def transactions_for(
    session: AsyncSession, user_id, limit: int = 50
) -> list[TokenTransaction]:
    account = await session.get(TokenAccount, user_id)
    if account is None:
        return []
    return list(
        (
            await session.execute(
                select(TokenTransaction)
                .where(TokenTransaction.account_id == user_id)
                .order_by(TokenTransaction.created_at.desc())
                .limit(limit)
            )
        ).scalars()
    )


async def _apply(
    session: AsyncSession,
    user_id,
    amount: int,
    transaction_type: str,
    reason: str,
    idempotency_key: str,
    reference_type: str | None = None,
    reference_id: str | None = None,
) -> TokenTransaction:
    existing = (
        await session.execute(
            select(TokenTransaction).where(TokenTransaction.idempotency_key == idempotency_key)
        )
    ).scalar_one_or_none()
    if existing is not None:
        return existing

    account = await session.get(TokenAccount, user_id, with_for_update=True)
    if account is None:
        account = TokenAccount(user_id=user_id, balance=0)
        session.add(account)
        await session.flush()

    new_balance = account.balance + amount
    if new_balance < 0:
        raise ConflictError("Insufficient token balance.")
    account.balance = new_balance
    account.updated_at = datetime.now()

    transaction = TokenTransaction(
        account_id=user_id,
        type=transaction_type,
        amount=amount,
        balance_after=new_balance,
        reason=reason,
        reference_type=reference_type,
        reference_id=reference_id,
        idempotency_key=idempotency_key,
    )
    session.add(transaction)
    await session.flush()
    return transaction


async def credit_tokens(
    session: AsyncSession,
    user_id,
    amount: int,
    reason: str,
    idempotency_key: str,
    reference_type: str | None = None,
    reference_id: str | None = None,
) -> TokenTransaction:
    if amount <= 0:
        raise ValueError("Credit amount must be positive.")
    return await _apply(
        session,
        user_id,
        amount,
        TransactionType.CREDIT,
        reason,
        idempotency_key,
        reference_type,
        reference_id,
    )


async def debit_tokens(
    session: AsyncSession,
    user_id,
    amount: int,
    reason: str,
    idempotency_key: str,
    reference_type: str | None = None,
    reference_id: str | None = None,
) -> TokenTransaction:
    if amount <= 0:
        raise ValueError("Debit amount must be positive.")
    return await _apply(
        session,
        user_id,
        -amount,
        TransactionType.DEBIT,
        reason,
        idempotency_key,
        reference_type,
        reference_id,
    )


async def refund_tokens(
    session: AsyncSession,
    user_id,
    amount: int,
    reason: str,
    idempotency_key: str,
) -> TokenTransaction:
    if amount <= 0:
        raise ValueError("Refund amount must be positive.")
    return await _apply(
        session,
        user_id,
        amount,
        TransactionType.REFUND,
        reason,
        idempotency_key,
        "refund",
        None,
    )
