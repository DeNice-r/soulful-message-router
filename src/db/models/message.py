from sqlalchemy import Column, DateTime, String, Integer, Boolean, ForeignKey
from datetime import datetime as dt
from src.db.engine import BaseModel


class Message(BaseModel):
    __tablename__ = 'Message'

    id = Column(Integer, primary_key=True, nullable=False)
    created_at = Column('createdAt', DateTime, default=dt.now)
    text = Column(String, nullable=False)
    is_from_user = Column('isFromUser', Boolean, nullable=False)
    chat_id = Column('chatId', ForeignKey('Chat.id'), nullable=False)

# Reference model from Prisma
# model Message {
#   id         Int      @id @default(autoincrement())
#   createdAt  DateTime @default(now())
#   text       String
#   chat       Chat     @relation(fields: [chatId], references: [id])
#   chatId     Int
#   isFromUser Boolean
#   // user          User        @relation(fields: [userId],      references: [id])
#   // userId        String
#   // personnel     Personnel   @relation(fields: [personnelId], references: [id])
#   // personnelId   String
# }
