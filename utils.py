import logging
from django.core.mail import send_mail
from django.conf import settings
from .models import Notification

logger = logging.getLogger(__name__)


def send_notification(user, title, message, type, send_email=True):
    """
    Creates a database notification record and optionally dispatches an HTML email.
    """
    # 1. Create in-app Notification database record
    notification = Notification.objects.create(
        user=user,
        title=title,
        message=message,
        type=type
    )
    
    # 2. Optionally dispatch Email
    if send_email and user.email:
        subject = f"Notification: {title}"
        email_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #e2e8f0; border-radius: 8px; background-color: #f8fafc;">
                <h2 style="color: #4f46e5; margin-top: 0;">Task Manager Update</h2>
                <hr style="border: 0; border-top: 1px solid #e2e8f0; margin-bottom: 20px;">
                <p style="font-size: 16px; font-weight: bold; color: #0f172a;">{title}</p>
                <p style="font-size: 14px; color: #334155;">{message}</p>
                <div style="margin-top: 30px; padding: 15px; background-color: #edf2f7; border-radius: 6px; font-size: 12px; color: #718096;">
                    This is an automated system alert from your Task Management Dashboard.
                </div>
            </div>
        </body>
        </html>
        """
        
        try:
            send_mail(
                subject=subject,
                message=message,  # Text fallback
                from_email=settings.EMAIL_HOST_USER if settings.EMAIL_HOST_USER else 'noreply@taskmanager.com',
                recipient_list=[user.email],
                html_message=email_body,
                fail_silently=False
            )
            logger.info(f"Notification email successfully sent to {user.email}")
        except Exception as e:
            # Fallback log in case SMTP fails or is not configured
            logger.error(f"Failed to send email to {user.email}: {str(e)}")
            
    return notification
