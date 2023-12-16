from sqlalchemy import Column, String, Integer
from sqlalchemy.orm import relationship, backref

from src.db.engine import BaseModel


class Chat(BaseModel):
    __tablename__ = 'chat'

    id = Column(Integer, primary_key=True, nullable=False)
    created_at = Column('createdAt', String)
    messages = relationship('Message', backref=backref('chat', lazy='select'))
    user = relationship('User', backref=backref('userChat', lazy='select'))
    personnel = relationship('User', backref=backref('personnelChats', lazy='select'))

# Reference model from Prisma
# model Chat {
#   id          Int       @id @default(autoincrement())
#   createdAt   DateTime  @default(now())
#   user        User      @relation(name: "userChat", fields: [userId], references: [id])
#   userId      String    @unique
#   personnel   User      @relation(name: "personnelChats", fields: [personnelId], references: [id])
#   personnelId String
#   Message     Message[]
# }
