"""
Celery Background Tasks

Defines async tasks for background processing.
"""
import logging
from datetime import datetime
from typing import List, Optional

from app.core.celery_app import celery_app

logger = logging.getLogger("bookapi.tasks")


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def send_email_task(self, to_emails: List[str], subject: str, body: str, html_body: Optional[str] = None):
    """
    Send email asynchronously.

    Args:
        to_emails: List of recipient email addresses
        subject: Email subject
        body: Plain text body
        html_body: Optional HTML body
    """
    try:
        logger.info(f"Sending email to {to_emails} with subject: {subject}")

        # Import here to avoid circular imports
        from app.services.email_service import EmailService
        import asyncio

        email_service = EmailService()

        # Run async function in sync context
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(
                email_service.send_email(
                    to_emails=to_emails,
                    subject=subject,
                    body=body,
                    html_body=html_body
                )
            )
            logger.info(f"Email sent successfully to {to_emails}")
            return {"status": "success", "recipients": to_emails}
        finally:
            loop.close()

    except Exception as exc:
        logger.error(f"Failed to send email: {exc}")
        raise self.retry(exc=exc)


@celery_app.task(bind=True, max_retries=3)
def process_file_task(self, file_path: str, operation: str, user_id: int):
    """
    Process uploaded file asynchronously.

    Args:
        file_path: Path to the uploaded file
        operation: Operation to perform (e.g., "resize", "convert", "analyze")
        user_id: ID of the user who uploaded the file
    """
    try:
        logger.info(f"Processing file {file_path} with operation {operation}")

        # Simulate file processing
        import time
        time.sleep(2)  # Simulate processing time

        result = {
            "status": "completed",
            "file_path": file_path,
            "operation": operation,
            "processed_at": datetime.utcnow().isoformat()
        }

        logger.info(f"File processing completed: {result}")
        return result

    except Exception as exc:
        logger.error(f"Failed to process file: {exc}")
        raise self.retry(exc=exc)


@celery_app.task
def cleanup_expired_tokens():
    """
    Periodic task to clean up expired tokens from Redis.
    Runs every hour.
    """
    try:
        logger.info("Starting cleanup of expired tokens")

        # Import here to avoid circular imports
        from app.core.redis import redis_client
        import asyncio

        async def cleanup():
            # Get all blacklisted token keys
            pattern = "blacklist:token:*"
            # Redis will auto-expire keys, this is just for logging
            return {"status": "completed", "cleaned_at": datetime.utcnow().isoformat()}

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(cleanup())
            logger.info(f"Token cleanup completed: {result}")
            return result
        finally:
            loop.close()

    except Exception as exc:
        logger.error(f"Token cleanup failed: {exc}")
        return {"status": "failed", "error": str(exc)}


@celery_app.task
def send_daily_digest():
    """
    Send daily digest emails to users.
    Runs daily.
    """
    try:
        logger.info("Starting daily digest generation")

        # Placeholder for daily digest logic
        result = {
            "status": "completed",
            "sent_at": datetime.utcnow().isoformat(),
            "recipients_count": 0
        }

        logger.info(f"Daily digest completed: {result}")
        return result

    except Exception as exc:
        logger.error(f"Daily digest failed: {exc}")
        return {"status": "failed", "error": str(exc)}


@celery_app.task(bind=True)
def send_notification_task(self, user_id: int, notification_type: str, data: dict):
    """
    Send notification to user asynchronously.

    Args:
        user_id: ID of the user to notify
        notification_type: Type of notification
        data: Notification data
    """
    try:
        logger.info(f"Sending {notification_type} notification to user {user_id}")

        result = {
            "status": "sent",
            "user_id": user_id,
            "notification_type": notification_type,
            "sent_at": datetime.utcnow().isoformat()
        }

        return result

    except Exception as exc:
        logger.error(f"Failed to send notification: {exc}")
        raise self.retry(exc=exc)


@celery_app.task
def generate_report_task(report_type: str, params: dict, user_id: int):
    """
    Generate a report asynchronously.

    Args:
        report_type: Type of report to generate
        params: Report parameters
        user_id: ID of the user requesting the report
    """
    try:
        logger.info(f"Generating {report_type} report for user {user_id}")

        import time
        time.sleep(5)  # Simulate report generation

        result = {
            "status": "completed",
            "report_type": report_type,
            "generated_at": datetime.utcnow().isoformat(),
            "download_url": f"/api/v1/files/reports/{report_type}_{user_id}.pdf"
        }

        logger.info(f"Report generation completed: {result}")
        return result

    except Exception as exc:
        logger.error(f"Report generation failed: {exc}")
        return {"status": "failed", "error": str(exc)}
