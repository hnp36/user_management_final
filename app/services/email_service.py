from builtins import ValueError, dict, str
from settings.config import settings
from app.utils.smtp_connection import SMTPClient
from app.utils.template_manager import TemplateManager
from app.utils.localization import LocalizationManager, get_localization_manager
from app.models.user_model import User
from typing import Optional, Dict, Any
import logging


class EmailService:
    def __init__(self, template_manager: TemplateManager, localization_manager: Optional[LocalizationManager] = None):
        self.smtp_client = SMTPClient(
            server=settings.smtp_server,
            port=settings.smtp_port,
            username=settings.smtp_username,
            password=settings.smtp_password
        )
        self.template_manager = template_manager
        # Use the provided localization manager or get the default one
        self.localization_manager = localization_manager or get_localization_manager()
        
        # Email type to subject key mapping
        self.email_type_mapping = {
            'email_verification': "email_verification_subject",
            'password_reset': "password_reset_subject",
            'account_locked': "account_locked_subject",
            'welcome': "welcome_subject",
            'account_update': "account_update_subject",
            'subscription': "subscription_subject"
        }

    async def send_user_email(self, user_data: Dict[str, Any], email_type: str) -> bool:
        """
        Send email to a user with proper localization.
        
        Args:
            user_data: User data including email and language preference
            email_type: Type of email to send
        
        Returns:
            bool: True if email was sent successfully
        
        Raises:
            ValueError: If email type is invalid or required data is missing
        """
        if not user_data.get('email'):
            raise ValueError("User email is required")
            
        # Get user's preferred language or fall back to default
        language = user_data.get('preferred_language', self.localization_manager.default_language)
        
        # Validate email type
        if email_type not in self.email_type_mapping:
            raise ValueError(f"Invalid email type: {email_type}. Valid types are: {', '.join(self.email_type_mapping.keys())}")
        
        # Get the localized subject and template
        subject_key = self.email_type_mapping[email_type]
        subject = self.localization_manager.get_localized_text(subject_key, language)
        
        # Prepare template with localized content
        email_content = await self._prepare_email_content(email_type, user_data, language)
        
        # Send email
        return await self.smtp_client.send_email(
            recipient=user_data['email'],
            subject=subject,
            body=email_content,
            is_html=True
        )
    
    async def _prepare_email_content(self, email_type: str, user_data: Dict[str, Any], language: str) -> str:
        """
        Prepare localized email content based on template and user data
        
        Args:
            email_type: Type of email to prepare
            user_data: User data to use in template
            language: Language code for localization
            
        Returns:
            str: Rendered email content
        """
        # Get template path for this email type
        template_path = f"emails/{email_type}.html"
        
        # Prepare template variables with localized text
        template_vars = {
            **user_data,
            # Include common localized text elements
            "greeting": self.localization_manager.get_localized_text("email_greeting", language),
            "footer": self.localization_manager.get_localized_text("email_footer", language),
            "company_name": self.localization_manager.get_localized_text("company_name", language),
        }
        
        # Add email type specific localized variables
        if email_type == "email_verification":
            template_vars.update({
                "verification_button": self.localization_manager.get_localized_text("verify_email_button", language),
                "verification_text": self.localization_manager.get_localized_text("verify_email_text", language),
            })
        elif email_type == "password_reset":
            template_vars.update({
                "reset_button": self.localization_manager.get_localized_text("reset_password_button", language),
                "reset_text": self.localization_manager.get_localized_text("reset_password_text", language),
            })
        
        # Render the template with variables
        return await self.template_manager.render_template(template_path, template_vars)
    
    async def send_batch_emails(self, users: list[User], email_type: str) -> Dict[str, int]:
        """
        Send batch emails to multiple users with proper localization for each.
        
        Args:
            users: List of User objects
            email_type: Type of email to send
            
        Returns:
            Dict with counts of success/failure
        """
        results = {"success": 0, "failed": 0}
        
        for user in users:
            user_data = user.to_dict()
            try:
                success = await self.send_user_email(user_data, email_type)
                if success:
                    results["success"] += 1
                else:
                    results["failed"] += 1
            except Exception:
                results["failed"] += 1
                
        return results
        
    async def send_verification_email(self, user: User) -> bool:
        """
        Send verification email to a newly registered user.
        
        Args:
            user: User object with email and verification token
            
        Returns:
            bool: True if email was sent successfully
        """
        if not hasattr(user, 'email') or not user.email:
            logger = logging.getLogger(__name__)
            logger.error("Cannot send verification email: User has no email address")
            return False
            
        if not hasattr(user, 'verification_token') or not user.verification_token:
            logger = logging.getLogger(__name__)
            logger.error("Cannot send verification email: User has no verification token")
            return False
            
        # Convert user object to dictionary with needed attributes
        user_data = {
            'email': user.email,
            'nickname': getattr(user, 'nickname', ''),
            'id': str(user.id),
            'verification_token': user.verification_token,
            'verification_url': f"{settings.base_url}/verify-email?user_id={user.id}&token={user.verification_token}",
            'preferred_language': getattr(user, 'preferred_language', self.localization_manager.default_language)
        }
        
        # Send the email using our localized email service
        return await self.send_user_email(user_data, 'email_verification')