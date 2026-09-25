from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, ForbiddenError, NotFoundError
from app.services.group_service import crud
from app.services.group_service.models import Group
from app.services.group_service.schemas import AddMemberIn, GroupCreate, GroupDetail
from app.services.user_service import crud as user_crud
from app.services.user_service.models import User
from app.services.user_service.schemas import UserCreate
from app.services.user_service.service import register_user
from app.shared.enums import Role


def _ensure_teacher_owns(group: Group, teacher: User) -> None:
    if group.teacher_id != teacher.id:
        raise ForbiddenError("Вы не являетесь преподавателем этой группы")


async def create_group(db: AsyncSession, data: GroupCreate, user: User) -> Group:
    existing = await crud.get_by_name(db, data.name)
    if existing:
        raise ConflictError(f"Группа {data.name} уже существует")

    teacher_id = user.id if user.role == Role.TEACHER else None
    group = await crud.create(
        db,
        name=data.name,
        description=data.description,
        teacher_id=teacher_id,
        created_by_id=user.id,
    )
    if user.role == Role.STUDENT:
        await crud.add_member(db, group.id, user.id)
    return group


async def list_my_groups(db: AsyncSession, user: User) -> list[Group]:
    if user.role == Role.TEACHER:
        return await crud.list_for_teacher(db, user.id)
    return await crud.list_for_student(db, user.id)


async def get_group_detail(db: AsyncSession, group_id: int, user: User) -> GroupDetail:
    group = await crud.get_by_id(db, group_id)
    if not group:
        raise NotFoundError("Группа не найдена")

    is_owner = group.teacher_id == user.id
    member = await crud.get_member(db, group_id, user.id)
    if not is_owner and not member:
        raise ForbiddenError("Нет доступа к этой группе")

    members = await crud.list_members(db, group_id)
    return GroupDetail(
        id=group.id,
        name=group.name,
        description=group.description,
        teacher_id=group.teacher_id,
        created_by_id=group.created_by_id,
        created_at=group.created_at,
        members_count=len(members),
        members=[u for u in members],
    )


async def delete_group(db: AsyncSession, group_id: int, teacher: User) -> None:
    group = await crud.get_by_id(db, group_id)
    if not group:
        raise NotFoundError("Группа не найдена")
    _ensure_teacher_owns(group, teacher)
    await crud.delete(db, group)


async def claim_group(db: AsyncSession, group_id: int, teacher: User) -> Group:
    group = await crud.get_by_id(db, group_id)
    if not group:
        raise NotFoundError("Группа не найдена")
    if group.teacher_id is not None:
        raise ConflictError("У группы уже есть преподаватель")
    return await crud.claim(db, group, teacher.id)


async def add_member(
    db: AsyncSession, group_id: int, payload: AddMemberIn, teacher: User
) -> None:
    group = await crud.get_by_id(db, group_id)
    if not group:
        raise NotFoundError("Группа не найдена")
    _ensure_teacher_owns(group, teacher)

    target: User | None = None
    if payload.user_id:
        target = await user_crud.get_by_id(db, payload.user_id)
    elif payload.email:
        target = await user_crud.get_by_email(db, payload.email)

    if target is None:
        if not (payload.email and payload.first_name and payload.last_name and payload.password):
            raise NotFoundError(
                "Студент с таким email не найден. "
                "Заполните имя, фамилию и пароль, чтобы создать аккаунт."
            )
        target = await register_user(
            db,
            UserCreate(
                first_name=payload.first_name,
                last_name=payload.last_name,
                email=payload.email,
                password=payload.password,
                role=Role.STUDENT,
            ),
        )

    if target.role != Role.STUDENT:
        raise ConflictError("Добавлять в группу можно только студентов")
    if await crud.get_member(db, group_id, target.id):
        raise ConflictError("Студент уже состоит в этой группе")

    await crud.add_member(db, group_id, target.id)


async def remove_member(db: AsyncSession, group_id: int, user_id: int, teacher: User) -> None:
    group = await crud.get_by_id(db, group_id)
    if not group:
        raise NotFoundError("Группа не найдена")
    _ensure_teacher_owns(group, teacher)

    member = await crud.get_member(db, group_id, user_id)
    if not member:
        raise NotFoundError("Пользователь не состоит в группе")
    await crud.remove_member(db, member)


async def join_group(db: AsyncSession, group_id: int, user: User) -> None:
    if user.role != Role.STUDENT:
        raise ForbiddenError("Только студент может присоединиться к группе")
    group = await crud.get_by_id(db, group_id)
    if not group:
        raise NotFoundError("Группа не найдена")
    if await crud.get_member(db, group_id, user.id):
        raise ConflictError("Вы уже в этой группе")
    await crud.add_member(db, group_id, user.id)


async def leave_group(db: AsyncSession, group_id: int, user: User) -> None:
    member = await crud.get_member(db, group_id, user.id)
    if not member:
        raise NotFoundError("Вы не состоите в этой группе")
    await crud.remove_member(db, member)