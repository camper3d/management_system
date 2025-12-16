from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from backend.models.team import Team
from backend.models.user import User, UserRole
from backend.schemas.team import TeamCreate


async def create_team(db: AsyncSession, team_create: TeamCreate, admin_id: int) -> Team:
    """
        Создать новую команду.

        Args:
            db (AsyncSession): Асинхронная сессия SQLAlchemy.
            team_create (TeamCreate): Входные данные для команды (название).
            admin_id (int): Идентификатор пользователя, назначаемого администратором команды.

        Returns:
            Team: Созданный объект команды.

        Raises:
            ValueError: Если команда с таким названием уже существует.
        """

    existing = await db.execute(select(Team).where(Team.name == team_create.name))
    if existing.scalars().first():
        raise ValueError("Team name already exists")

    team = Team(name=team_create.name, admin_id=admin_id)
    db.add(team)
    await db.commit()
    await db.refresh(team)
    return team


async def get_team_by_id(db: AsyncSession, team_id: int) -> Team | None:
    """
        Получить команду по её идентификатору.

        Args:
            db (AsyncSession): Асинхронная сессия SQLAlchemy.
            team_id (int): Идентификатор команды.

        Returns:
            Team | None: Объект команды, если найден, иначе None.
        """

    result = await db.execute(select(Team).where(Team.id == team_id))
    return result.scalars().first()


async def add_user_to_team(db: AsyncSession, user_id: int, team_id: int) -> bool:
    """
        Добавить пользователя в команду.

        Args:
            db (AsyncSession): Асинхронная сессия SQLAlchemy.
            user_id (int): Идентификатор пользователя.
            team_id (int): Идентификатор команды.

        Returns:
            bool: True, если пользователь успешно добавлен в команду, иначе False.
        """

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalars().first()
    if not user:
        return False
    user.team_id = team_id
    await db.commit()
    return True


async def remove_user_from_team(db: AsyncSession, user_id: int) -> bool:
    """
        Удалить пользователя из команды.

        Args:
            db (AsyncSession): Асинхронная сессия SQLAlchemy.
            user_id (int): Идентификатор пользователя.

        Returns:
            bool: True, если пользователь успешно удалён из команды, иначе False.

        Notes:
            При удалении пользователь получает роль UserRole.MEMBER.
        """

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalars().first()
    if user and user.team_id:
        user.team_id = None
        user.role = UserRole.MEMBER
        await db.commit()
        return True
    return False


async def set_user_role_in_team(db: AsyncSession, user_id: int, role: UserRole) -> bool:
    """
        Установить роль пользователю в команде.

        Args:
            db (AsyncSession): Асинхронная сессия SQLAlchemy.
            user_id (int): Идентификатор пользователя.
            role (UserRole): Новая роль пользователя в команде.

        Returns:
            bool: True, если роль успешно изменена, иначе False.
        """

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalars().first()
    if user and user.team_id:
        user.role = role
        await db.commit()
        return True
    return False


async def get_team_members(db: AsyncSession, team_id: int) -> list[User]:
    """
        Получить список участников команды.

        Args:
            db (AsyncSession): Асинхронная сессия SQLAlchemy.
            team_id (int): Идентификатор команды.

        Returns:
            list[User]: Список пользователей, входящих в команду.
        """

    result = await db.execute(select(User).where(User.team_id == team_id))
    return result.scalars().all()