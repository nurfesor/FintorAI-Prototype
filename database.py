import os
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, desc
from sqlalchemy.orm import sessionmaker, declarative_base

# Use an absolute path for the database file to avoid issues
DATABASE_URL = "sqlite:///" + os.path.join(os.path.dirname(os.path.abspath(__file__)), "fintor.db")

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class TransactionDB(Base):
    """ORM Model for a transaction in the database."""
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    transaction_date = Column(DateTime, default=datetime.utcnow)
    category = Column(String, nullable=False)
    group = Column(String, nullable=False)
    subcategory = Column(String, nullable=False)
    amount = Column(Float, nullable=False)
    description = Column(String)

def init_db():
    """Creates all database tables based on the models."""
    Base.metadata.create_all(bind=engine)

def add_transaction_db(user_id: int, trans_data: dict):
    """Adds a new transaction to the database."""
    db = SessionLocal()
    try:
        db_transaction = TransactionDB(user_id=user_id, **trans_data)
        db.add(db_transaction)
        db.commit()
    finally:
        db.close()

def get_last_transactions_db(user_id: int, limit: int = 5) -> list[TransactionDB]:
    """Retrieves the last N transactions for a specific user."""
    db = SessionLocal()
    try:
        transactions = (
            db.query(TransactionDB)
            .filter(TransactionDB.user_id == user_id)
            .order_by(desc(TransactionDB.transaction_date))
            .limit(limit)
            .all()
        )
        return transactions
    finally:
        db.close()
