"""User provisioning and entitlement helpers."""

from sqlalchemy import delete, insert, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import AuthContext
from app.core.errors import ConflictError, NotFoundError
from app.models.identity import (
    ROLE_PERMISSIONS,
    Permission,
    Profile,
    Role,
    RoleCode,
    User,
    UserStatus,
    role_permissions,
)


async def ensure_seed_roles(session: AsyncSession) -> None:
    """Idempotently create roles, permissions and their mappings."""
    existing_permissions = {
        row.code for row in (await session.execute(select(Permission))).scalars()
    }
    for code in {code for codes in ROLE_PERMISSIONS.values() for code in codes}:
        if code not in existing_permissions:
            session.add(Permission(code=code, description=code.replace(":", " ")))

    await session.flush()

    existing_roles = {row.code: row for row in (await session.execute(select(Role))).scalars()}

    for role_code in ROLE_PERMISSIONS:
        if role_code not in existing_roles:
            role = Role(code=role_code, description=role_code.replace("_", " ").title())
            session.add(role)
    await session.flush()

    # Rebuild the join table with Core DML. Assigning the ORM relationship here
    # would trigger a lazy load, which is invalid inside an async session.
    roles_by_code = {row.code: row.id for row in (await session.execute(select(Role))).scalars()}
    permission_ids = {
        row.code: row.id for row in (await session.execute(select(Permission))).scalars()
    }
    await session.execute(delete(role_permissions))
    await session.execute(
        insert(role_permissions),
        [
            {"role_id": roles_by_code[role_code], "permission_id": permission_ids[code]}
            for role_code, codes in ROLE_PERMISSIONS.items()
            for code in codes
        ],
    )


async def upsert_user(session: AsyncSession, context: AuthContext) -> User:
    """Create or refresh a user from verified identity data."""
    await ensure_seed_roles(session)
    result = await session.execute(select(User).where(User.firebase_uid == context.firebase_uid))
    user = result.scalar_one_or_none()

    if user is None:
        user = User(
            firebase_uid=context.firebase_uid,
            email=context.email,
            display_name=context.display_name,
            status=UserStatus.ACTIVE,
            profile=Profile(),
        )
        user_role = await session.execute(select(Role).where(Role.code == RoleCode.USER))
        user.roles.append(user_role.scalar_one())
        session.add(user)
    else:
        if user.status == UserStatus.DELETED:
            raise ConflictError("This account has been deleted.")
        if context.email and user.email != context.email:
            user.email = context.email
        if context.display_name and user.display_name != context.display_name:
            user.display_name = context.display_name

    await session.commit()
    await session.refresh(user, attribute_names=["profile", "roles"])
    for role in user.roles:
        await session.refresh(role, attribute_names=["permissions"])
    return user


async def get_user_by_id(session: AsyncSession, user_id) -> User:
    user = await session.get(User, user_id)
    if user is None:
        raise NotFoundError("User not found.")
    return user


def permission_codes(user: User) -> set[str]:
    return {permission.code for role in user.roles for permission in role.permissions}
