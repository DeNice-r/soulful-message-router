from sqlalchemy import text
from sqlalchemy.orm import Session

get_user_ids_by_permission_query = text("""
    SELECT u.id
    FROM "User" u
    LEFT JOIN "_PermissionToUser" up ON u.id = up."B"
    LEFT JOIN "Permission" p ON up."A" = p.id
    LEFT JOIN "_RoleToUser" ur ON u.id = ur."B"
    LEFT JOIN "Role" r ON ur."A" = r.id
    LEFT JOIN "_PermissionToRole" pr ON r.id = pr."B"
    LEFT JOIN "Permission" p2 ON pr."A" = p2.id
    WHERE (p.title = ANY(:titles) OR p2.title = ANY(:titles))
    AND u.id = ANY(:available_personnel_ids)
""")

def get_personnel(session: Session, available_personnel_ids: list[str], role_titles: list[str] = None):
    if not role_titles:
        role_titles = ['chat:*', 'chat:*:*', '*:*', '*:*:*']
    return session.execute(get_user_ids_by_permission_query, {'titles': role_titles, 'available_personnel_ids': available_personnel_ids}).scalars().all()
