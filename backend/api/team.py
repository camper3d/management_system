from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from backend.db.session import get_db
from backend.schemas.team import TeamCreate, TeamOut, TeamMemberUpdate
from backend.crud.team import create_team, get_team_by_id, add_user_to_team,\
    remove_user_from_team, set_user_role_in_team, get_team_members
from backend.api.deps import get_current_user
from backend.models.user import User, UserRole


router = APIRouter(prefix="/teams", tags=["teams"])


@router.post("/", response_model=TeamOut)
async def create_new_team(
        team_in: TeamCreate,
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """
        Создать новую команду и назначить текущего пользователя её администратором.

        Args:
            team_in (TeamCreate): Данные для создания команды (название и др.).
            db (AsyncSession): Асинхронная сессия SQLAlchemy.
            current_user (User): Текущий пользователь.

        Returns:
            TeamOut: Объект созданной команды с её участниками.

        Raises:
            HTTPException:
                - 400: Если пользователь уже состоит в команде.
        """

    if current_user.team_id is not None:
        raise HTTPException(status_code=400, detail="You are already in a team")

    team = await create_team(db, team_in, current_user.id)
    current_user.team_id = team.id
    current_user.role = UserRole.ADMIN
    await db.commit()

    members = [current_user]
    return TeamOut(id=team.id, name=team.name, admin_id=team.admin_id, members=members)


@router.get("/me", response_model=TeamOut)
async def get_my_team(
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """
        Получить информацию о команде текущего пользователя.

        Args:
            db (AsyncSession): Асинхронная сессия SQLAlchemy.
            current_user (User): Текущий пользователь.

        Returns:
            TeamOut: Объект команды с её участниками.

        Raises:
            HTTPException:
                - 404: Если пользователь не состоит в команде или команда не найдена.
        """

    if current_user.team_id is None:
        raise HTTPException(status_code=404, detail="You are not in a team")

    team = await get_team_by_id(db, current_user.team_id)
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")

    members = await get_team_members(db, team.id)
    return TeamOut(
        id=team.id,
        name=team.name,
        admin_id=team.admin_id,
        members=members
    )


@router.post("/{team_id}/add-member")
async def add_member_to_team(
        team_id: int,
        member_update: TeamMemberUpdate,
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """
        Добавить нового участника в команду.

        Args:
            team_id (int): Идентификатор команды.
            member_update (TeamMemberUpdate): Данные участника (user_id).
            db (AsyncSession): Асинхронная сессия SQLAlchemy.
            current_user (User): Текущий пользователь.

        Returns:
            dict: Сообщение об успешном добавлении {"message": "Member added"}.

        Raises:
            HTTPException:
                - 403: Если текущий пользователь не является администратором команды.
                - 404: Если пользователь не найден.
        """

    if current_user.team_id != team_id or current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Only admin can add members")

    success = await add_user_to_team(db, member_update.user_id, team_id)
    if not success:
        raise HTTPException(status_code=404, detail="User not found")

    return {"message": "Member added"}


@router.post("/{team_id}/set-role")
async def set_member_role(
        team_id: int,
        role_update: TeamMemberUpdate,
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """
        Установить роль участнику команды.

        Args:
            team_id (int): Идентификатор команды.
            role_update (TeamMemberUpdate): Данные участника (user_id и новая роль).
            db (AsyncSession): Асинхронная сессия SQLAlchemy.
            current_user (User): Текущий пользователь.

        Returns:
            dict: Сообщение об успешном изменении роли {"message": "..."}.

        Raises:
            HTTPException:
                - 403: Если текущий пользователь не является администратором команды.
                - 400: Если указана недопустимая роль.
                - 404: Если пользователь не найден или не состоит в команде.
        """

    if current_user.team_id != team_id or current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Only admin can change roles")

    allowed_roles = {UserRole.MANAGER, UserRole.MEMBER}
    if role_update.role not in allowed_roles:
        raise HTTPException(status_code=400, detail="Invalid role")

    success = await set_user_role_in_team(db, role_update.user_id, UserRole(role_update.role))
    if not success:
        raise HTTPException(status_code=404, detail="User not in team or not found")

    return {"message": f"Role set to {role_update.role}"}


@router.delete("/{team_id}/remove-member/{user_id}")
async def remove_member(
        team_id: int,
        user_id: int,
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """
        Удалить участника из команды.

        Args:
            team_id (int): Идентификатор команды.
            user_id (int): Идентификатор пользователя, которого нужно удалить.
            db (AsyncSession): Асинхронная сессия SQLAlchemy.
            current_user (User): Текущий пользователь.

        Returns:
            dict: Сообщение об успешном удалении {"message": "Member removed"}.

        Raises:
            HTTPException:
                - 403: Если текущий пользователь не является администратором команды.
                - 400: Если администратор пытается удалить сам себя.
                - 404: Если пользователь не найден или не состоит в команде.
        """

    if current_user.team_id != team_id or current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Only admin can remove members")

    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="Admin cannot remove themselves")

    success = await remove_user_from_team(db, user_id)
    if not success:
        raise HTTPException(status_code=404, detail="User not found or not in team")

    return {"message": "Member removed"}