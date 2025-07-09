from datetime import datetime
from warnings import catch_warnings

from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import User, SessionModel, schema_to_model
from app.schemas import UserCreate, UserLogin, SessionSchema
from app.security import generate_session_id, hash_password, verify_password
from app.crud import create_user, save_session, get_user_by_login
from app.database import get_db

app = FastAPI()


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.post("/register")
async def register(new_user: UserCreate, encrypted: bool, db: Session = Depends(get_db)):
    if encrypted:
        print(new_user)
    else:
        new_user.password = hash_password(new_user.password)
        print(new_user)

    user: User = User(**(new_user.model_dump()), user_status="open")
    try:
        created_user = create_user(db, user)
    except IntegrityError:
        raise HTTPException(400, "User already exists")

    session_id = generate_session_id()
    session = SessionSchema(session_id=session_id, user_id=created_user.userid, valid_until=datetime.now())
    sessionModel = SessionModel(**session.model_dump()) # Convert to model for DB operations
    save_session(db, sessionModel)
    return {"message": f"Hello {new_user}, Session: {session}"}

@app.post("/login")
async def login(user: UserLogin, db: Session = Depends(get_db)):
    userModel = schema_to_model(user, User)
    foundUser = get_user_by_login(db, userModel)
    if foundUser is None:
        raise HTTPException(404, f"User not found")

    verify_password(user.password, foundUser.password)
    session_id = generate_session_id()
    session = SessionSchema(session_id=session_id, user_id=user.userid, valid_until=datetime.now())
    sessionModel = schema_to_model(session, SessionModel)
    save_session(db, sessionModel)
    return {"message": f"Hello {foundUser}, Session: {session}"}


