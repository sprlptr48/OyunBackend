import os
from dotenv import load_dotenv
from datetime import datetime, timedelta
from passlib.context import CryptContext
import secrets

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

if not SECRET_KEY:
    raise Exception("SECRET_KEY must be set")


# Encryption
def generate_session_id():
    return secrets.token_hex(nbytes=127)

def verification_code():
    return secrets.token_hex(nbytes=3)

def email_verification_code():
    return secrets.token_hex(nbytes=16)

password_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password):
    password = password_context.hash(password)
    return password

def verify_password(plain_password, password):
    return password_context.verify(plain_password, password)
