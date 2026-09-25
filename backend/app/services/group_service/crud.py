from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.group_service.models import Group, GroupMember
from app.services.user_service.models import User


async def get_by_id(db: AsyncSession, group_id: int) -> Group | None:
    return await db.get(Group, group_id)


async def get_by_name(db: AsyncSession, name: str) -> Group | None:
    result = await db.execute(select(Group).where(Group.name == name))
    return result.scalar_one_or_none()


async def create(
    db: AsyncSession,
    *,
    name: str,
    teacher_id: int | None,
    created_by_id: int,
    description: str | None = None,
) -> Group:
    group = Group(
        name=name,
        description=description,
        teacher_id=teacher_id,
        created_by_id=created_by_id,
    )
    db.add(group)
    await db.commit()
    await db.refresh(group)
    return group


async def delete(db: AsyncSession, group: Group) -> None:
    await db.delete(group)
    await db.commit()


async def claim(db: AsyncSession, group: Group, teacher_id: int) -> Group:
    group.teacher_id = teacher_id
    await db.commit()
    await db.refresh(group)
    return group


async def get_member(db: AsyncSession, group_id: int, user_id: int) -> GroupMember | None:
    result = await db.execute(
        select(GroupMember).where(
            GroupMember.group_id == group_id, GroupMember.user_id == user_id
        )
    )
    return result.scalar_one_or_none()


async def add_member(db: AsyncSession, group_id: int, user_id: int) -> GroupMember:
    member = GroupMember(group_id=group_id, user_id=user_id)
    db.add(member)
    await db.commit()
    await db.refresh(member)
    return member


async def remove_member(db: AsyncSession, member: GroupMember) -> None:
    await db.delete(member)
    await db.commit()


async def list_members(db: AsyncSession, group_id: int) -> list[User]:
    result = await db.execute(
        select(User)
        .join(GroupMember, GroupMember.user_id == User.id)
        .where(GroupMember.group_id == group_id)
        .order_by(User.last_name, User.first_name)
    )
    return list(result.scalars().all())


async def members_count(db: AsyncSession, group_id: int) -> int:
    result = await db.execute(
        select(func.count()).select_from(GroupMember).where(GroupMember.group_id == group_id)
    )
    return int(result.scalar_one())


async def list_for_teacher(db: AsyncSession, teacher_id: int) -> list[Group]:
    result = await db.execute(
        select(Group).where(Group.teacher_id == teacher_id).order_by(Group.name)
    )
    return list(result.scalars().all())


async def list_for_student(db: AsyncSession, user_id: int) -> list[Group]:
    result = await db.execute(
        select(Group)
        .join(GroupMember, GroupMember.group_id == Group.id)
        .where(GroupMember.user_id == user_id)
        .order_by(Group.name)
    )
    return list(result.scalars().all())