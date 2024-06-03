from sqlalchemy import text
from sqlalchemy.orm import Session

create_get_personnel_stats_function = text("""
    DROP FUNCTION IF EXISTS get_personnel_stats();
    CREATE OR REPLACE FUNCTION get_personnel_stats()
    RETURNS TABLE (
        personnelId TEXT,
        name TEXT,
        totalChats BIGINT,
        normalizedChats DOUBLE PRECISION,
        totalMessages NUMERIC,
        normalizedMessages DOUBLE PRECISION,
        averageResponseTimeSeconds NUMERIC,
        normalizedResponseTime DOUBLE PRECISION,
        perceivedBusyness INT,
        normalizedBusyness DOUBLE PRECISION,
        normalizedScore DOUBLE PRECISION
    ) AS $$
    BEGIN
        RETURN QUERY
        WITH TotalChats AS (
            SELECT
                "personnelId",
                COUNT(*) AS "totalChats"
            FROM (
                SELECT "personnelId"
                FROM "Chat"
                WHERE "personnelId" IS NOT NULL AND "createdAt" >= NOW() - INTERVAL '1 HOUR'
                UNION ALL
                SELECT "personnelId"
                FROM "ArchivedChat"
                WHERE "personnelId" IS NOT NULL AND "endedAt" >= NOW() - INTERVAL '1 HOUR'
            ) AS combined_chats
            GROUP BY "personnelId"
        ),
        MessagesLastHour AS (
            SELECT "personnelId", COALESCE(SUM("messageCount"), 0) AS "totalMessages"
            FROM (
                SELECT "personnelId", COUNT(*) AS "messageCount"
                FROM "Message"
                JOIN "Chat" ON "Message"."chatId" = "Chat"."id"
                WHERE "Message"."createdAt" > NOW() - INTERVAL '1 HOUR'
                GROUP BY "Chat"."personnelId"
                UNION ALL
                SELECT "personnelId", COUNT(*) AS "messageCount"
                FROM "ArchivedMessage"
                JOIN "ArchivedChat" ON "ArchivedMessage"."chatId" = "ArchivedChat"."id"
                WHERE "ArchivedMessage"."createdAt" > NOW() - INTERVAL '1 HOUR'
                GROUP BY "ArchivedChat"."personnelId"
            ) AS messages
            GROUP BY "personnelId"
        ),
        ResponseTime AS (
            SELECT
                "personnelId",
                AVG(EXTRACT(EPOCH FROM ("nextMessageTime" - "createdAt"))) AS "averageResponseTimeSeconds"
            FROM (
                SELECT
                    "personnelId",
                    "createdAt",
                    LEAD("createdAt") OVER (PARTITION BY "chatId" ORDER BY "createdAt") AS "nextMessageTime"
                FROM (
                    SELECT "personnelId", "chatId", m."createdAt", "isFromUser" FROM "Message" m
                    JOIN "Chat" c ON "chatId" = c.id
                    WHERE m."createdAt" > CURRENT_TIMESTAMP - INTERVAL '1 HOUR'
                    UNION ALL
                    SELECT "personnelId", "chatId", am."createdAt", "isFromUser" FROM "ArchivedMessage" am
                    JOIN "ArchivedChat" ac ON "chatId" = ac.id
                    WHERE am."createdAt" > CURRENT_TIMESTAMP - INTERVAL '1 HOUR'
                ) AS messages
                WHERE "isFromUser" = TRUE
            ) AS filtered_messages
            GROUP BY "personnelId"
        ),
        PerceivedBusyness AS (
            SELECT id AS "personnelId", "busyness" AS "perceivedBusyness"
            FROM "User"
        ),
        MaxValues AS (
            SELECT
                GREATEST(MAX("totalChats"), 1) AS maxChats,
                GREATEST(MAX("totalMessages"), 1) AS maxMessages,
                GREATEST(MAX("averageResponseTimeSeconds"), 1) AS maxResponseTime,
                GREATEST(MAX("perceivedBusyness"), 1) AS maxBusyness
            FROM TotalChats
            JOIN MessagesLastHour USING ("personnelId")
            LEFT JOIN ResponseTime USING ("personnelId")
            JOIN PerceivedBusyness USING ("personnelId")
        )
        SELECT
            t."personnelId",
            u.name,
            t."totalChats",
            t."totalChats"::float / mv.maxChats AS normalizedChats,
            m."totalMessages",
            m."totalMessages"::float / mv.maxMessages AS normalizedMessages,
            r."averageResponseTimeSeconds",
            COALESCE(r."averageResponseTimeSeconds"::float / mv.maxResponseTime, 0) AS normalizedResponseTime,
            p."perceivedBusyness",
            p."perceivedBusyness"::float / mv.maxBusyness AS normalizedBusyness,
            (t."totalChats"::float / mv.maxChats + m."totalMessages"::float / mv.maxMessages +
            COALESCE(r."averageResponseTimeSeconds"::float / mv.maxResponseTime, 0) + p."perceivedBusyness"::float / mv.maxBusyness) AS normalizedScore
        FROM TotalChats t
        LEFT JOIN "User" u ON t."personnelId" = u."id"
        JOIN MessagesLastHour m ON t."personnelId" = m."personnelId"
        LEFT JOIN ResponseTime r ON t."personnelId" = r."personnelId"
        JOIN PerceivedBusyness p ON t."personnelId" = p."personnelId"
        CROSS JOIN MaxValues mv
        ORDER BY normalizedScore ASC;
    END;
    $$ LANGUAGE plpgsql;
""")

create_unarchive_function = text("""
    DROP FUNCTION IF EXISTS unarchive_chat(int);
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

register_queries = [create_get_personnel_stats_function, create_unarchive_function]

get_personnel_stats_query = text("""
    SELECT personnelId FROM get_personnel_stats() WHERE personnelId = ANY(:available_personnel_ids);
""")

def get_least_busy_personnel_id(session: Session, available_personnel_ids: list[str]):
    personnel_by_busyness = session.execute(get_personnel_stats_query, {'available_personnel_ids': available_personnel_ids}).scalars().all() or []
    unmentioned_online_personnel = list(set(available_personnel_ids) - set(personnel_by_busyness))

    return unmentioned_online_personnel[0] if unmentioned_online_personnel else personnel_by_busyness[0]

unarchive_chat_query = text("""
    SELECT unarchive_chat(:chat_id);
""")

def unarchive_chat(session: Session, chat_id: int):
    result = session.execute(unarchive_chat_query, {'chat_id': chat_id}).scalars().one_or_none()
    session.commit()
    return result

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

def get_user_email(session: Session, personnel_id: str):
    return session.execute(text('SELECT email FROM "User" WHERE id = :id'), {'id': personnel_id}).scalar_one()
