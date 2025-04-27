from builtins import ValueError, dict, str
from settings.config import settings
from app.utils.smtp_connection import SMTPClient
from app.utils.template_manager import TemplateManager
from app.models.user_model import User
from app.utils.i18n import get_translator  # Added for i18n support

class EmailService:
    def __init__(self, template_manager: TemplateManager):
        self.smtp_client = SMTPClient(
            server=settings.smtp_server,
            port=settings.smtp_port,
            username=settings.smtp_username,
            password=settings.smtp_password
        )
        self.template_manager = template_manager

    async def send_user_email(self, user_data: dict, email_type: str, lang: str = "en"):
        _ = get_translator(lang).gettext  # Use translator for subject translation

        subject_map = {
            'email_verification': _("Verify Your Account"),
            'password_reset': _("Password Reset Instructions"),
            'account_locked': _("Account Locked Notification")
        }

        if email_type not in subject_map:
            raise ValueError(_("Invalid email type"))

        html_content = self.template_manager.render_template(email_type, **user_data)
        self.smtp_client.send_email(subject_map[email_type], html_content, user_data['email'])

    async def send_verification_email(self, user: User):
        lang = getattr(user, "preferred_language", "en")  # Optional: language from user
        verification_url = f"{settings.server_base_url}verify-email/{user.id}/{user.verification_token}"
        await self.send_user_email({
            "name": user.first_name,
            "verification_url": verification_url,
            "email": user.email
        }, 'email_verification', lang)
