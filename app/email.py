import os

from pydantic import BaseModel, EmailStr
from postmarker.core import PostmarkClient


MAIL_FROM = os.getenv("MAIL_FROM")
POSTMARK_API_KEY = os.getenv("POSTMARK_API_KEY")
if not POSTMARK_API_KEY:
    raise ValueError("POSTMARK_API_KEY environment variable is not set.")
postmark = PostmarkClient(server_token=POSTMARK_API_KEY)

class EmailRequest(BaseModel):
    to_email: EmailStr
    subject: str
    html_body: str
    text_body: str | None = None
    from_email: str = MAIL_FROM #Postmark'ta kayıtlı adres

async def send_email(subject: str, recipient: str, body: str):
    postmark.emails.send(
        From=MAIL_FROM,
        To=recipient,
        Subject=subject,
        HtmlBody=body
    )


async def send_verification_email(email_to: str, verification_code: str):
    subject = "Lütfen Email Adresinizi Doğrulayın"
    body = f"""
    <p>Merhaba,</p>
    <p>Hesabınızı doğrulamak için lütfen aşağıdaki kodu yazın:</p>
    <a href="{verification_code}">{verification_code}</a>
    """
    await send_email(subject, email_to, body)

async def send_password_reset_email(email_to: str, reset_code: str):
    subject = "Şifre Sıfırlama İsteği"
    body = f"""
    <p>Merhaba,</p>
    <p>Şifre sıfırlama kodunuz aşağıdadır. Bu kodu <b>5 dakika içinde</b> kullanarak şifrenizi yenileyebilirsiniz.</p>
    <p style="font-size: 24px; font-weight: bold; text-align: center; color: #007bff;">{reset_code}</p>
    <p>Bu isteği siz yapmadıysanız lütfen bu e-postayı dikkate almayın ve güvenlik için hesabınızı kontrol edin.</p>
    <p>İyi günler dileriz,</p>
    <p>ŞİRKET ADI</p>
    """
    await send_email(subject, email_to, body)
