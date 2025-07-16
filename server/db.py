from sqlalchemy import create_engine, Column, Integer, String, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship

engine = create_engine('sqlite:///mmorpg.db', echo=False)
Base = declarative_base()
Session = sessionmaker(bind=engine)

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)
    exp = Column(Integer, default=0)
    level = Column(Integer, default=1)

class Friend(Base):
    __tablename__ = 'friends'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    friend_id = Column(Integer, ForeignKey('users.id'))

class Party(Base):
    __tablename__ = 'parties'
    id = Column(Integer, primary_key=True)
    leader_id = Column(Integer, ForeignKey('users.id'))

class PartyMember(Base):
    __tablename__ = 'party_members'
    id = Column(Integer, primary_key=True)
    party_id = Column(Integer, ForeignKey('parties.id'))
    user_id = Column(Integer, ForeignKey('users.id'))

class Item(Base):
    __tablename__ = 'items'
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)
    type = Column(String)

class Inventory(Base):
    __tablename__ = 'inventories'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    item_id = Column(Integer, ForeignKey('items.id'))
    count = Column(Integer, default=1)

Base.metadata.create_all(engine)

def register_user(username, password):
    session = Session()
    if session.query(User).filter_by(username=username).first():
        session.close()
        return False  # 이미 존재
    user = User(username=username, password=password)
    session.add(user)
    session.commit()
    session.close()
    return True

def login_user(username, password):
    session = Session()
    user = session.query(User).filter_by(username=username, password=password).first()
    session.close()
    return user is not None 

def add_friend(username, friendname):
    session = Session()
    user = session.query(User).filter_by(username=username).first()
    friend = session.query(User).filter_by(username=friendname).first()
    if not user or not friend:
        session.close()
        return False
    if session.query(Friend).filter_by(user_id=user.id, friend_id=friend.id).first():
        session.close()
        return False
    session.add(Friend(user_id=user.id, friend_id=friend.id))
    session.commit()
    session.close()
    return True

def get_friends(username):
    session = Session()
    user = session.query(User).filter_by(username=username).first()
    if not user:
        session.close()
        return []
    friends = session.query(Friend).filter_by(user_id=user.id).all()
    friend_names = []
    for f in friends:
        friend = session.query(User).filter_by(id=f.friend_id).first()
        if friend:
            friend_names.append(friend.username)
    session.close()
    return friend_names

def create_party(leadername):
    session = Session()
    leader = session.query(User).filter_by(username=leadername).first()
    if not leader:
        session.close()
        return None
    party = Party(leader_id=leader.id)
    session.add(party)
    session.commit()
    session.add(PartyMember(party_id=party.id, user_id=leader.id))
    session.commit()
    session.close()
    return party.id

def invite_party(party_id, username):
    session = Session()
    user = session.query(User).filter_by(username=username).first()
    if not user:
        session.close()
        return False
    if session.query(PartyMember).filter_by(party_id=party_id, user_id=user.id).first():
        session.close()
        return False
    session.add(PartyMember(party_id=party_id, user_id=user.id))
    session.commit()
    session.close()
    return True

def get_party_members(party_id):
    session = Session()
    members = session.query(PartyMember).filter_by(party_id=party_id).all()
    names = []
    for m in members:
        user = session.query(User).filter_by(id=m.user_id).first()
        if user:
            names.append(user.username)
    session.close()
    return names 

def get_user(username):
    session = Session()
    user = session.query(User).filter_by(username=username).first()
    session.close()
    return user

def add_exp_and_levelup(username, exp_gain):
    session = Session()
    user = session.query(User).filter_by(username=username).first()
    if not user:
        session.close()
        return None
    user.exp += exp_gain
    leveled_up = False
    while user.exp >= user.level * 50:
        user.exp -= user.level * 50
        user.level += 1
        leveled_up = True
    session.commit()
    result = (user.level, user.exp, leveled_up)
    session.close()
    return result 

def add_item_to_user(username, itemname):
    session = Session()
    user = session.query(User).filter_by(username=username).first()
    item = session.query(Item).filter_by(name=itemname).first()
    if not item:
        item = Item(name=itemname, type='etc')
        session.add(item)
        session.commit()
    inv = session.query(Inventory).filter_by(user_id=user.id, item_id=item.id).first()
    if inv:
        inv.count += 1
    else:
        inv = Inventory(user_id=user.id, item_id=item.id, count=1)
        session.add(inv)
    session.commit()
    session.close()

def get_inventory(username):
    session = Session()
    user = session.query(User).filter_by(username=username).first()
    if not user:
        session.close()
        return []
    invs = session.query(Inventory).filter_by(user_id=user.id).all()
    items = []
    for inv in invs:
        item = session.query(Item).filter_by(id=inv.item_id).first()
        if item:
            items.append((item.name, inv.count))
    session.close()
    return items 