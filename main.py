from typing import List, Optional
from pydantic import BaseModel
from requests import Session
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from fastapi import Depends, FastAPI, HTTPException

# thi is the fastAPI class set to a variable
app = FastAPI()

# ------------
# 1. connect to a small local database file
# 2. create a tool (engine) to talk to the database.
# 3. create database sessions that handle transactions.
# 4. make a base class (Base) for defining your table structure using Python classes.
# ------------

#This is the database connection string
#It tells SQLAlchemy to use SQLite and create (or use) a file named .test.db in the current directory.
DATABASE_URL = "sqlite:///.test.db"

#creates a SQLAlchemy engine, which manages connections to the database.
#connect_args={"check_same_thread": False} is specific to SQLite.
#SQLite has a default setting that disallows using the same connection across different threads.
#Setting check_same_thread=False disables that check. It's usually required when using SQLite with frameworks like FastAPI that might handle requests in different threads.
engine = create_engine(DATABASE_URL,connect_args={"check_same_thread": False})

#sessionmaker is a factory for database sessions
#A session is how SQLAlchemy communicates with the database.
#autocommit=False: Transactions won't be committed automatically 
#autoflush=False: SQLAlchemy won’t automatically push changes unless you flush or commit
#bind=engine: This tells the session to use the engine you created earlier to talk to the database.
sessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

#This creates a base class for all your database models (ORM classes).
Base = declarative_base()

#This defines a Python class that maps to a table in the database using SQLAlchemy’s ORM (Object Relational Mapper)
class User(Base):
    #This tells SQLAlchemy to use the table name "users" in the database.
    #If omitted, it would use the class name (User) by default.
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    email = Column(String, unique=True, index=True)

#This is the actual step that creates the table in your SQLite .test.db file.
#Base.metadata holds all the models you’ve defined.
#create_all() generates the necessary SQL (e.g., CREATE TABLE) and applies it to the database.
# Important: This only creates tables that don’t already exist. It won’t drop or modify existing ones. For schema updates, you’d use tools like Alembic.
Base.metadata.create_all(bind=engine)



def get_db():
    db = sessionLocal()
    try:
        yield db
    finally:
        db.close()

class UserCreate(BaseModel):
    name: str
    email: str

class UserResponse(BaseModel):
    name: str
    email: str

    class Config:
        orm_mode = True


@app.post("/users/", response_model=UserResponse)
def create_user(user:UserCreate, db: Session = Depends(get_db)):
    db_user = User(name=user.name, email=user.email)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@app.get("/users/", response_model=List[UserResponse])
def read_users(skip: int = 0, Limit: int = 10, db: Session = Depends(get_db)):
   users = db.query(User).offset(skip).limit(Limit).all()
   return users 

@app.get("/users/{user_id}", response_model=UserResponse)
def read_user(user_id: int, db:Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()

    if user is None:
        raise HTTPException(status_code=404, detail="User not dound")
    return user


class userUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None

@app.post("/users/{user_id}", response_model=UserResponse)
def create_user(user_id: int, user:userUpdate, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.id == user_id).first()

    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    
    db_user.name = user.name if user.name is not None else db_user.name
    db_user.email = user.email if user.email is not None else db_user.email
    db.commit()
    db.refresh(db_user)
    return db_user

@app.delete("/users/{user_id}", response_model=UserResponse)
def delete_user(user_id: int, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.id == user_id).first()

    if db_user is None:
        raise HTTPException(status_code=404, details="User not found")
    
    db.delete(db_user)
    db.commit()
    return db_user
