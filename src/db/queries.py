from sqlalchemy import text
from sqlalchemy.orm import Session

getPersonnelQuery = text("""
    SELECT u.id
    FROM "User" u
    LEFT JOIN "_PermissionToUser" up ON u.id = up."B"
    LEFT JOIN "Permission" p ON up."A" = p.id
    LEFT JOIN "_RoleToUser" ur ON u.id = ur."B"
    LEFT JOIN "Role" r ON ur."A" = r.id
    LEFT JOIN "_PermissionToRole" pr ON r.id = pr."B"
    LEFT JOIN "Permission" p2 ON pr."A" = p2.id
    WHERE (p.title = :title OR p2.title = :title)
    AND u.id = ANY(:available_personnel_ids)
""")

def getPersonnel(session: Session, available_personnel_ids: list[str], role_title: str = 'chat'):
    return session.execute(getPersonnelQuery, {'title': role_title, 'available_personnel_ids': available_personnel_ids}).scalars().all()
