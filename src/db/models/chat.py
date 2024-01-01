from sqlalchemy import Column, String, Integer, ForeignKey, DateTime
from sqlalchemy.orm import relationship, backref, mapped_column
from datetime import datetime as dt

from src.db.engine import BaseModel


class Chat(BaseModel):
    __tablename__ = 'Chat'

    id = Column(Integer, primary_key=True, nullable=False)
    created_at = Column('createdAt', DateTime, default=dt.now)
    # messages = relationship('Message', backref=backref('chat', lazy='select'))
    user_id = mapped_column('userId', ForeignKey('User.id'))
    # user = relationship('User', backref=backref('userChat', lazy='select'))
    # personnel = relationship('User', backref=backref('personnelChats', lazy='select'))
    personnel_id = mapped_column('personnelId', ForeignKey('User.id'))

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
