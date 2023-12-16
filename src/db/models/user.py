from sqlalchemy import Column, DateTime, String, Integer
from sqlalchemy.orm import relationship, backref

from src.db.engine import BaseModel


class User(BaseModel):
    __tablename__ = 'user'

    id = Column(String, primary_key=True, not_null=True)
    name = Column(String)
    email = Column(String, unique=True)
    email_verified = Column('emailVerified', DateTime)
    image = Column(String)
    role = Column(String, nullable=False)

    # Unused on backend
    # posts = relationship('Post', backref=backref('user', lazy='select'))
    # accounts = relationship('Account', backref=backref('user', lazy='select'))
    # sessions = relationship('Session', backref=backref('user', lazy='select'))


# Reference model from Prisma
# model User {
#   id            String    @id @default(cuid())
#   name          String?
#   email         String?   @unique
#   emailVerified DateTime?
#   image         String?
#   role          String    @default("user")
#   posts         Post[]
#   accounts      Account[]
#   sessions      Session[]
# }
