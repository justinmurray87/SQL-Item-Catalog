
import sys

from sqlalchemy import Column, ForeignKey, Integer, String

from sqlalchemy.ext.declarative import declarative_base

from sqlalchemy.orm import relationship

from sqlalchemy import create_engine

Base = declarative_base()

#####tables######

class User(Base):
    __tablename__ = 'user'
    name = Column(String(80), nullable = False)
    id = Column(Integer, primary_key = True)
    email = Column(String(250), nullable=False)
    picture = Column(String(250))

class Sport(Base):
    __tablename__ = 'sport'
    name = Column(String(80), nullable = False)
    id = Column(Integer, primary_key = True)
    description = Column(String(100), nullable = True)
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)

class Item(Base):
    __tablename__ = 'item'
    name = Column(String(80), nullable = False)
    id = Column(Integer, primary_key = True)
    description = Column(Integer, nullable = False)
    sport_id = Column(Integer, ForeignKey('sport.id'), nullable = False)
    sport = relationship(Sport)
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)

# We added this serialize function to be able to send JSON objects in a
# serializable format
@property
def serialize(self):

    return {
        'sport': self.sport.name,
        'description': self.sport.description,
        'id': self.id,
        }

#####end table definition here######

engine = create_engine(
'sqlite:///sports.db'
)

Base.metadata.create_all(engine)
