from sqlalchemy import text
from sqlalchemy.orm import Session

create_unarchive_function = text("""
    CREATE OR REPLACE FUNCTION unarchive_chat(chat_id int)
    RETURNS int AS $$
    DECLARE 
        new_chat_id int;
    BEGIN
        INSERT INTO "Chat" ("userId", "personnelId", "createdAt")
        SELECT "userId", "personnelId", "createdAt"
        FROM "ArchivedChat"
        WHERE "id" = chat_id
        RETURNING "id" INTO new_chat_id;

        INSERT INTO "Message" ("chatId", "text", "createdAt", "isFromUser")
        SELECT new_chat_id, "text", "createdAt", "isFromUser"
        FROM "ArchivedMessage"
        WHERE "chatId" = chat_id;

        DELETE FROM "ArchivedChat"
        WHERE "id" = chat_id;
    
        DELETE FROM "ArchivedMessage"
        WHERE "chatId" = chat_id;
        
        RETURN new_chat_id;
    END;
    $$ LANGUAGE plpgsql;
""")

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

get_chat_id_acquainted_with_client_query = text("""
    SELECT c.id
    FROM "User" u
    LEFT JOIN "ArchivedChat" c ON u.id = c."personnelId"
    WHERE (c."userId" = :user_id)
    AND c."personnelId" IS NOT NULL
    AND u.id = ANY(:available_personnel_ids)
    ORDER BY c."endedAt" DESC
    LIMIT 1
""")

def get_acquainted_chat(session: Session, available_personnel_ids: list[str], user_id: str):
    return session.execute(get_chat_id_acquainted_with_client_query, {'user_id': user_id, 'available_personnel_ids': available_personnel_ids}).scalars().one_or_none()

unarchive_chat_query = text("""
    SELECT unarchive_chat(:chat_id);
""")
    # SELECT unarchive_chat((:chat_id)::int);

def unarchive_chat(session: Session, chat_id: int):
    result = session.execute(unarchive_chat_query, {'chat_id': chat_id}).scalars().one_or_none()
    session.commit()
    return result

def get_user_email(session: Session, personnel_id: str):
    return session.execute(text('SELECT email FROM "User" WHERE id = :id'), {'id': personnel_id}).scalar_one()
