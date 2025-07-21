# app/utils/session.py
import re
from datetime import datetime, timezone
from app.schemas import SessionSchema


""" Check if email is in correct form: example@domain.com """
def verify_email_format(email: str):
    regex = r'^[\w\-\.]+@([\w-]+\.)+[\w-]{2,}$'

    matches = re.findall(regex, email, re.MULTILINE)
    if len(matches) != 1:
        return False
    else:
        return True
""" Check if phone number is in correct form:  """
def verify_phone_format(phone: str):
    regex = r'^(?:\+?\d{1,4})?0?\d{10}$'
    return re.fullmatch(regex, phone, re.MULTILINE)
""" Telefon numarasındaki boşlukları ve gereksiz işaretleri siler. """
def normalize_phone(phone: str) -> str:
    # Remove spaces, dashes, underscores, parentheses, asterisks, etc.
    phone = phone.strip()

    # Preserve leading '+' if present, remove all non-digit characters
    if phone.startswith('+'):
        phone = '+' + re.sub(r'\D', '', phone[1:])
    else:
        phone = re.sub(r'\D', '', phone)
    return phone



def validate_session(session: SessionSchema) -> bool:
    valid_until = session.valid_until
    if valid_until.tzinfo is None:
        valid_until = valid_until.replace(tzinfo=timezone.utc)
    return valid_until > datetime.now(timezone.utc)
