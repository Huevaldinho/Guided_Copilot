"""
Notification system for alerting administrators of critical errors.
"""

import logging
import os
import json
from typing import List, Optional, Dict, Any
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


class NotificationService:
    """Handles error notifications through various channels."""

    def __init__(self):
        self.alert_email = os.getenv("ALERT_EMAIL", None)
        self.alerts_dir = Path(os.getenv("ALERTS_DIR", "/data/alerts"))
        self.alerts_dir.mkdir(parents=True, exist_ok=True)

    def notify_error(
        self,
        error_type: str,
        message: str,
        error_code: str,
        details: Optional[Dict[str, Any]] = None,
        severity: str = "WARNING",
    ) -> Dict[str, str]:
        """
        Send error notification through configured channels.

        Args:
            error_type: Category of error
            message: Error message
            error_code: Error code
            details: Additional details
            severity: Severity level (INFO, WARNING, CRITICAL)

        Returns:
            Dictionary with notification status
        """
        notification = {
            "timestamp": datetime.utcnow().isoformat(),
            "error_type": error_type,
            "message": message,
            "error_code": error_code,
            "severity": severity,
            "details": details or {},
        }

        status = {"email": "skipped", "file": "skipped"}

        # Write to file alert (always enabled)
        status["file"] = self._write_alert_file(notification)

        # Email notification for critical errors only
        if severity == "CRITICAL" and self.alert_email:
            status["email"] = self._send_email_alert(notification)
        elif severity == "CRITICAL":
            logger.warning(f"ALERT_EMAIL not configured; cannot send email for {error_code}")
            status["email"] = "skipped_no_email_config"

        return status

    def _write_alert_file(self, notification: Dict[str, Any]) -> str:
        """Write alert to local file."""
        try:
            timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
            alert_file = (
                self.alerts_dir
                / f"alert_{notification['error_code']}_{timestamp}.json"
            )
            with open(alert_file, "w", encoding="utf-8") as f:
                json.dump(notification, f, indent=2)
            logger.info(f"Alert written to {alert_file}")
            return "success"
        except Exception as e:
            logger.error(f"Failed to write alert file: {e}")
            return "failed"

    def _send_email_alert(self, notification: Dict[str, Any]) -> str:
        """
        Send email alert (placeholder for real implementation).
        In production, integrate with AWS SES, SendGrid, or similar.
        """
        try:
            # Placeholder: In production, use smtplib or a service like SendGrid
            subject = f"[{notification['severity']}] LMS Error Alert: {notification['error_code']}"
            body = f"""
LMS Error Notification

Error Code: {notification['error_code']}
Error Type: {notification['error_type']}
Severity: {notification['severity']}
Timestamp: {notification['timestamp']}

Message:
{notification['message']}

Details:
{json.dumps(notification['details'], indent=2)}

This is an automated alert. Please investigate immediately.
            """

            logger.warning(f"EMAIL ALERT (not sent - configure SMTP/SES):\n{body}")
            # TODO: Integrate with actual email service
            # For now, log that email would be sent
            return "logged_not_sent"
        except Exception as e:
            logger.error(f"Failed to send email alert: {e}")
            return "failed"

    def get_recent_alerts(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Retrieve recent alert files."""
        alerts = []
        try:
            alert_files = sorted(self.alerts_dir.glob("alert_*.json"), reverse=True)[
                :limit
            ]
            for alert_file in alert_files:
                with open(alert_file, "r", encoding="utf-8") as f:
                    alerts.append(json.load(f))
        except Exception as e:
            logger.error(f"Failed to read alert files: {e}")
        return alerts


# Global notification service instance
_notification_service = None


def get_notification_service() -> NotificationService:
    """Get or create global notification service."""
    global _notification_service
    if _notification_service is None:
        _notification_service = NotificationService()
    return _notification_service
