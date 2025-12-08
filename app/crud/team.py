from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.team import Team
from app.models.user import User, UserRole
from app.schemas.team import TeamCreate


async def create_team(db: AsyncSession, team_create: TeamCreate, admin_id: int) -> Team:
    existing = await db.execute(select(Team).where(Team.name == team_create.name))
    if existing.scalars().first():
        raise ValueError("Team name already exists")

    team = Team(name=team_create.name, admin_id=admin_id)
    db.add(team)
    await db.commit()
    await db.refresh(team)
    return team


async def get_team_by_id(db: AsyncSession, team_id: int) -> Team | None:
    result = await db.execute(select(Team).where(Team.id == team_id))
    return result.scalars().first()


async def add_user_to_team(db: AsyncSession, user_id: int, team_id: int) -> bool:
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalars().first()
    if not user:
        return False
    user.team_id = team_id
    await db.commit()
    return True


async def remove_user_from_team(db: AsyncSession, user_id: int) -> bool:
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalars().first()
    if user and user.team_id:
        user.team_id = None
        user.role = UserRole.MEMBER
        await db.commit()
        return True
    return False


async def set_user_role_in_team(db: AsyncSession, user_id: int, role: UserRole) -> bool:
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalars().first()
    if user and user.team_id:
        user.role = role
        await db.commit()
        return True
    return False


async def get_team_members(db: AsyncSession, team_id: int) -> list[User]:
    result = await db.execute(select(User).where(User.team_id == team_id))
    return result.scalars().all()