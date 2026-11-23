"""Token package purchase verification and idempotent crediting."""

from dataclasses import dataclass
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ConflictError
from app.models.identity import User
from app.models.monetization import PurchaseStatus, TokenPackage, TokenPurchase
from app.services.billing_service import get_purchase_verifier
from app.services.token_service import credit_tokens


@dataclass
class PurchaseResultOut:
    credited_tokens: int
    balance: int
    order_id: str
    already_credited: bool = False


async def ensure_packages(session: AsyncSession) -> None:
    existing = {
        row.google_play_product_id
        for row in (await session.execute(select(TokenPackage))).scalars()
    }
    for product_id, name, tokens, price in [
        ("com.prediqo.tokens.starter", "Starter", 5, 9900),
        ("com.prediqo.tokens.pro", "Pro", 20, 29900),
        ("com.prediqo.tokens.elite", "Elite", 60, 74900),
    ]:
        if product_id not in existing:
            session.add(
                TokenPackage(
                    name=name,
                    tokens=tokens,
                    price_minor=price,
                    currency="KES",
                    google_play_product_id=product_id,
                    active=True,
                )
            )
    await session.flush()


async def verify_token_purchase(
    session: AsyncSession,
    user: User,
    product_id: str,
    purchase_token: str,
) -> PurchaseResultOut:
    await ensure_packages(session)
    package = (
        await session.execute(
            select(TokenPackage).where(
                TokenPackage.google_play_product_id == product_id,
                TokenPackage.active.is_(True),
            )
        )
    ).scalar_one_or_none()
    if package is None:
        raise ConflictError("Unknown token package.")

    existing = (
        await session.execute(
            select(TokenPurchase).where(TokenPurchase.google_play_purchase_token == purchase_token)
        )
    ).scalar_one_or_none()
    if existing is not None:
        from app.services.token_service import transactions_for

        txns = await transactions_for(session, user.id, limit=1)
        return PurchaseResultOut(
            credited_tokens=0,
            balance=txns[0].balance_after if txns else 0,
            order_id=existing.google_play_order_id,
            already_credited=True,
        )

    verified = await get_purchase_verifier().verify(product_id, purchase_token)
    session.add(
        TokenPurchase(
            user_id=user.id,
            package_id=package.id,
            google_play_order_id=verified.order_id,
            google_play_purchase_token=purchase_token,
            status=PurchaseStatus.VERIFIED,
            verified_at=datetime.now(UTC),
        )
    )
    await session.flush()
    transaction = await credit_tokens(
        session,
        user.id,
        package.tokens,
        "TOKEN_PACKAGE_PURCHASE",
        idempotency_key=f"purchase:{purchase_token}",
        reference_type="token_purchase",
        reference_id=purchase_token,
    )
    await session.commit()
    return PurchaseResultOut(
        credited_tokens=package.tokens,
        balance=transaction.balance_after,
        order_id=verified.order_id,
    )


def serialize_package(package: TokenPackage) -> dict:
    return {
        "id": str(package.id),
        "name": package.name,
        "tokens": package.tokens,
        "price_minor": package.price_minor,
        "currency": package.currency,
        "google_play_product_id": package.google_play_product_id,
    }
