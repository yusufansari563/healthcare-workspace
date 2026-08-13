import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Any, List, Optional
from src.config import settings

logger = logging.getLogger(__name__)

class EmailService:
    """
    Email notification service for sending workflow completion reports to the user.
    """

    def __init__(self):
        self.smtp_host = settings.SMTP_HOST
        self.smtp_port = settings.SMTP_PORT
        self.smtp_user = settings.SMTP_USER
        self.smtp_password = settings.SMTP_PASSWORD
        self.recipient_email = settings.NOTIFICATION_EMAIL or "yusufansari563@gmail.com"

    def is_configured(self) -> bool:
        return bool(self.smtp_user and self.smtp_password and "app_password" not in self.smtp_password.lower())

    def send_completion_email(
        self,
        instruction: str,
        plan: List[Dict[str, Any]],
        tickets: List[Dict[str, Any]],
        pr_info: Dict[str, Any],
        token_stats: Dict[str, Any],
        recipient: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Sends HTML notification email summarizing workflow execution.
        """
        target_email = recipient or self.recipient_email
        subject = f"🚀 [Agentic Workflow Completed] Task Execution Report"
        
        # Build HTML content
        tickets_html = ""
        for t in tickets:
            name = t.get("name", t.get("title", "Task"))
            url = t.get("url", "#")
            tickets_html += f"<li><strong>{name}</strong> - <a href='{url}' target='_blank'>View in ClickUp</a></li>"

        pr_url = pr_info.get("pr_url", "#")
        pr_title = pr_info.get("title", "Pull Request")
        
        html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; color: #333; line-height: 1.6; max-width: 650px; margin: 0 auto; padding: 20px; border: 1px solid #e0e0e0; border-radius: 8px;">
            <div style="background: linear-gradient(135deg, #4F46E5, #7C3AED); padding: 20px; border-radius: 6px; color: white; text-align: center;">
                <h2 style="margin: 0;">Agentic AI Workflow Finished</h2>
                <p style="margin-top: 5px; opacity: 0.9;">Your automated task execution is complete!</p>
            </div>
            
            <h3 style="color: #4F46E5; margin-top: 25px;">📌 Initial Instruction</h3>
            <p style="background: #f4f5f7; padding: 12px; border-left: 4px solid #4F46E5; border-radius: 4px;">{instruction}</p>
            
            <h3 style="color: #4F46E5;">📋 ClickUp Tickets Created</h3>
            <ul>
                {tickets_html if tickets_html else '<li>No tickets generated</li>'}
            </ul>
            
            <h3 style="color: #4F46E5;">🔀 GitHub Pull Request</h3>
            <p><strong><a href="{pr_url}" target="_blank">{pr_title}</a></strong> (Branch: <code>{pr_info.get('branch_name', 'main')}</code>)</p>
            
            <h3 style="color: #4F46E5;">⚡ Token & Cost Savings</h3>
            <table style="width: 100%; border-collapse: collapse; margin-top: 10px;">
                <tr style="background: #f9fafb;">
                    <td style="padding: 8px; border: 1px solid #ddd;"><strong>Total Tokens Used:</strong></td>
                    <td style="padding: 8px; border: 1px solid #ddd;">{token_stats.get('total_tokens', 0):,}</td>
                </tr>
                <tr>
                    <td style="padding: 8px; border: 1px solid #ddd;"><strong>Estimated High-End LLM Cost:</strong></td>
                    <td style="padding: 8px; border: 1px solid #ddd;">${token_stats.get('estimated_gpt4_cost', 0)}</td>
                </tr>
                <tr style="background: #f9fafb;">
                    <td style="padding: 8px; border: 1px solid #ddd;"><strong>Actual Cost (Optimized/Open-Source):</strong></td>
                    <td style="padding: 8px; border: 1px solid #ddd; color: #16a34a;"><strong>${token_stats.get('estimated_actual_cost', 0)}</strong></td>
                </tr>
                <tr>
                    <td style="padding: 8px; border: 1px solid #ddd;"><strong>Estimated Saved:</strong></td>
                    <td style="padding: 8px; border: 1px solid #ddd; color: #16a34a;"><strong>${token_stats.get('saved_dollars', 0)}</strong></td>
                </tr>
            </table>

            <hr style="margin-top: 30px; border: 0; border-top: 1px solid #eee;" />
            <p style="font-size: 0.85em; color: #777; text-align: center;">Sent automatically by Agentic AI Workflow System</p>
        </body>
        </html>
        """

        if not self.is_configured():
            logger.info(f"[Email Service - Mock Mode] Email dispatch to {target_email} simulated successfully.")
            logger.info(f"Summary: Instruction='{instruction}', Tickets={len(tickets)}, PR={pr_url}")
            return {
                "status": "sent_mock",
                "recipient": target_email,
                "subject": subject,
                "mode": "mock",
                "message": "SMTP credentials not provided in .env - email output logged to console."
            }

        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = self.smtp_user
            msg["To"] = target_email
            msg.attach(MIMEText(html_body, "html"))

            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.sendmail(self.smtp_user, target_email, msg.as_string())

            logger.info(f"[Email Service] Successfully sent email to {target_email}")
            return {
                "status": "sent",
                "recipient": target_email,
                "subject": subject,
                "mode": "live"
            }
        except Exception as e:
            logger.exception(f"[Email Service] Error sending email via SMTP: {e}")
            return {
                "status": "error",
                "error": str(e),
                "recipient": target_email,
                "mode": "fallback"
            }

# Global singleton
email_service = EmailService()
