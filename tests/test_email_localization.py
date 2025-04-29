import pytest
from unittest.mock import Mock, patch, MagicMock
from app.services.email_service import EmailService
from app.utils.localization import LocalizationManager
from app.utils.template_manager import TemplateManager

pytestmark = pytest.mark.asyncio

class TestEmailServiceLocalization:
    """Tests for the localization features of EmailService"""
    
    @pytest.fixture
    def mock_template_manager(self):
        """Create a mock template manager"""
        template_manager = Mock(spec=TemplateManager)
        template_manager.render_template = MagicMock(return_value="Rendered Template")
        return template_manager
    
    @pytest.fixture
    def mock_localization_manager(self):
        """Create a mock localization manager with predefined texts"""
        localization_manager = Mock(spec=LocalizationManager)
        localization_manager.default_language = "en"
        
        # Define mock localized texts for different languages
        def get_localized_text_side_effect(key, language=None):
            lang = language or "en"
            localizations = {
                "en": {
                    "email_verification_subject": "Verify Your Email",
                    "verify_email_button": "Verify Email",
                    "email_greeting": "Hello",
                    "email_footer": "Regards, The Team"
                },
                "es": {
                    "email_verification_subject": "Verifique su correo electrónico",
                    "verify_email_button": "Verificar correo electrónico",
                    "email_greeting": "Hola",
                    "email_footer": "Saludos, El Equipo"
                },
                "fr": {
                    "email_verification_subject": "Vérifiez votre e-mail",
                    "verify_email_button": "Vérifier l'e-mail",
                    "email_greeting": "Bonjour",
                    "email_footer": "Cordialement, L'équipe"
                }
            }
            
            return localizations.get(lang, {}).get(key, key)
        
        # Create the mock method and then assign the side effect
        localization_manager.get_localized_text = MagicMock()
        localization_manager.get_localized_text.side_effect = get_localized_text_side_effect
        return localization_manager
    
    @pytest.fixture
    def email_service(self, mock_template_manager, mock_localization_manager):
        """Create an email service with mocked dependencies"""
        with patch('app.services.email_service.SMTPClient') as mock_smtp:
            instance = mock_smtp.return_value
            instance.send_email.return_value = True
            
            # Create the email service with the mocked dependencies
            email_service = EmailService(
                template_manager=mock_template_manager,
                localization_manager=mock_localization_manager
            )
            
            # Ensure the fixture returns the correct mocked dependencies
            yield email_service
    
    async def test_send_user_email_respects_language_preference(self, email_service, mock_localization_manager):
        """Test that send_user_email uses the user's preferred language"""
        # Create test user data with Spanish language preference
        user_data = {
            'email': 'test@example.com',
            'preferred_language': 'es'
        }
        
        # Send verification email
        result = await email_service.send_user_email(user_data, 'email_verification')
        
        # Verify that the localization manager was called with Spanish
        mock_localization_manager.get_localized_text.assert_any_call(
            "email_verification_subject", "es"
        )
        
        # Verify the email was sent
        assert result is True
    
    async def test_send_verification_email_with_localization(self, email_service, mock_localization_manager):
        """Test sending verification email with proper localization"""
        # Create mock user with French language preference
        mock_user = Mock()
        mock_user.id = "user123"
        mock_user.email = "test@example.com"
        mock_user.verification_token = "abc123token"
        mock_user.preferred_language = "fr"
        mock_user.nickname = "TestUser"
        mock_user.to_dict = MagicMock(return_value={
            'id': mock_user.id,
            'email': mock_user.email,
            'verification_token': mock_user.verification_token,
            'preferred_language': mock_user.preferred_language,
            'nickname': mock_user.nickname
        })
        
        # Send verification email
        with patch('app.services.email_service.settings') as mock_settings:
            mock_settings.base_url = "https://example.com"
            result = await email_service.send_verification_email(mock_user)
        
        # Verify the email was sent
        assert result is True
        
        # Check if the localization manager was called with French
        mock_localization_manager.get_localized_text.assert_any_call(
            "email_verification_subject", "fr"
        )
    
    async def test_fallback_to_default_language(self, email_service, mock_localization_manager):
        """Test that the system falls back to default language if preferred language is not available"""
        # Create test user data with unsupported language
        user_data = {
            'email': 'test@example.com',
            'preferred_language': 'invalid_language'
        }
        
        # Override the mocked method to simulate language fallback
        original_side_effect = mock_localization_manager.get_localized_text.side_effect
        mock_localization_manager.get_localized_text.side_effect = lambda key, language=None: f"Default {key}"
        
        # Send email
        await email_service.send_user_email(user_data, 'email_verification')
        
        # Verify the localization manager was called
        mock_localization_manager.get_localized_text.assert_called()
        
        # Restore original side effect for other tests
        mock_localization_manager.get_localized_text.side_effect = original_side_effect