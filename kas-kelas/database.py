from sqlalchemy import create_engine, Column, Integer, String, Float, Date, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    password_hash = Column(String(100), nullable=False)
    created_at = Column(DateTime, default=datetime.now)
    transactions = relationship("Transaction", back_populates="user")

class Transaction(Base):
    __tablename__ = 'transactions'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    type = Column(String(10))
    jumlah = Column(Float, nullable=False)
    deskripsi = Column(String(200))
    tanggal = Column(Date, nullable=False)
    created_at = Column(DateTime, default=datetime.now)
    user = relationship("User", back_populates="transactions")

engine = create_engine('sqlite:///kas_kelas.db')
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)

def get_session():
    return Session()

def add_user(username: str, password_hash: str):
    session = get_session()
    user = User(username=username, password_hash=password_hash)
    session.add(user)
    session.commit()
    session.close()

def get_user_by_username(username: str):
    session = get_session()
    user = session.query(User).filter(User.username == username).first()
    session.close()
    return user

def add_transaction(user_id: int, type: str, jumlah: float, deskripsi: str, tanggal):
    session = get_session()
    trans = Transaction(user_id=user_id, type=type, jumlah=jumlah, deskripsi=deskripsi, tanggal=tanggal)
    session.add(trans)
    session.commit()
    session.close()

def get_transactions(user_id: int):
    session = get_session()
    trans = session.query(Transaction).filter(Transaction.user_id == user_id).order_by(Transaction.tanggal.desc()).all()
    session.close()
    return trans

def get_balance(user_id: int):
    session = get_session()
    masuk = session.query(Transaction).filter(Transaction.user_id == user_id, Transaction.type == 'masuk').all()
    keluar = session.query(Transaction).filter(Transaction.user_id == user_id, Transaction.type == 'keluar').all()
    session.close()
    total_masuk = sum(t.jumlah for t in masuk)
    total_keluar = sum(t.jumlah for t in keluar)
    return total_masuk - total_keluar