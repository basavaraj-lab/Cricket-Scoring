from sqlalchemy import Column, Integer, String, ForeignKey
from database import Base

class user(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    password = Column(String)

class admin(Base):
    __tablename__ = "admins"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    password = Column(String)

class match(Base):
    __tablename__ = "matches"
    id = Column(Integer, primary_key=True, index=True)
    team1 = Column(String)
    team2 = Column(String)
    score1 = Column(Integer, default=0)
    score2 = Column(Integer, default=0)
    overs1 = Column(Integer, default=0)
    overs2 = Column(Integer, default=0)
    wickets1 = Column(Integer, default=0)
    wickets2 = Column(Integer, default=0)

class player(Base):
    __tablename__ = "players"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    team = Column(String)
    runs = Column(Integer, default=0)
    balls_faced = Column(Integer, default=0)
    fours = Column(Integer, default=0)
    sixes = Column(Integer, default=0)
    wickets = Column(Integer, default=0)
    overs_bowled = Column(Integer, default=0)