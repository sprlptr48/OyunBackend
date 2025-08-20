# app/utils/session.py
import re
from datetime import datetime, timezone
from app.auth.schemas import SessionSchema


def verify_email_format(email: str):
    """ Check if email is in correct form: example@domain.com """
    regex = r'^[\w\-\.]+@([\w-]+\.)+[\w-]{2,}$'
    return bool(re.fullmatch(regex, email))

def verify_phone_format(phone: str):
    """ Check if phone number is in correct form:  """
    regex = r'^(?:\+?\d{1,4})?0?\d{10}$'
    return re.fullmatch(regex, phone, re.MULTILINE)

def normalize_phone(phone: str) -> str:
    """ Telefon numarasındaki boşlukları ve gereksiz işaretleri siler. """
    if not isinstance(phone, str):
        return ""
    # Remove spaces, dashes, underscores, parentheses, asterisks, etc.
    phone = phone.strip()

    # Preserve leading '+' if present, remove all non-digit characters
    if phone.startswith('+'):
        phone = '+' + re.sub(r'\D', '', phone[1:])
    else:
        phone = re.sub(r'\D', '', phone)
    return phone


def validate_session(session: SessionSchema) -> bool:
    """Session verisi hala geçerli mi, süresi bitti mi?"""
    valid_until = session.valid_until
    if valid_until.tzinfo is None:
        valid_until = valid_until.replace(tzinfo=timezone.utc)
    return valid_until > datetime.now(timezone.utc)
