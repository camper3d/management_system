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
    if current_user.team_id != team_id or current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Only admin can remove members")

    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="Admin cannot remove themselves")

    success = await remove_user_from_team(db, user_id)
    if not success:
        raise HTTPException(status_code=404, detail="User not found or not in team")

    return {"message": "Member removed"}