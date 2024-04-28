from sqlalchemy import Column, DateTime, String, Integer, Boolean
from sqlalchemy.orm import relationship, backref
from datetime import datetime as dt

from src.db.engine import BaseModel


class User(BaseModel):
    __tablename__ = 'User'

    id = Column(String, primary_key=True, nullable=False)
    name = Column(String)
    email = Column(String, unique=True)
    email_verified = Column('emailVerified', DateTime)
    image = Column(String)
    isOnline = Column(Boolean, default=False)
    latestStatusConfirmationAt = Column(DateTime, default=dt.now)
    suspended = Column(Boolean, default=False)

    # role = Column(String, nullable=False)
#  isOnline                   Boolean        @default(false)
    #latestStatusConfirmationAt DateTime       @default(now())
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
