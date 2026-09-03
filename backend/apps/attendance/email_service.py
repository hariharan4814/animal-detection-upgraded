"""
FarmSync Automated Attendance & Work Report Email Service.
Handles transmission of daily work reports to farmers and farm administrators upon shift checkout.
"""

import logging
from typing import Dict, Any, Optional, List
from django.conf import settings
from django.utils import timezone
from django.template.loader import render_to_string
from django.core.mail import EmailMultiAlternatives, get_connection

from apps.attendance.models import Attendance
from apps.settings_app.models import EmailSenderConfig

logger = logging.getLogger(__name__)


class AttendanceEmailService:
    """
    Service for formatting and dispatching worker attendance and daily work summary emails.
    """

    @classmethod
    def get_admin_recipient(cls) -> str:
        """
        Retrieves the designated administrator email for worker attendance reports.
        Defaults to 'hariharan4814@gmail.com'.
        """
        admin_email = getattr(settings, 'WORK_REPORT_ADMIN_EMAIL', 'hariharan4814@gmail.com')
        return admin_email.strip() if admin_email else 'hariharan4814@gmail.com'

    @classmethod
    def send_farmer_checkout_report(cls, attendance: Attendance) -> Dict[str, Any]:
        """
        Constructs and dispatches the daily work report email upon worker checkout.
        Sends to both the farmer and the system administrator.
        """
        if not attendance or not attendance.farmer:
            return {"sent": False, "error": "Invalid attendance record or farmer relationship."}

        farmer = attendance.farmer
        farmer_email = (farmer.email or '').strip()
        admin_email = cls.get_admin_recipient()

        # Build deduplicated recipient list
        recipients: List[str] = []
        if farmer_email and '@' in farmer_email:
            recipients.append(farmer_email)
        if admin_email and '@' in admin_email and admin_email.lower() not in [r.lower() for r in recipients]:
            recipients.append(admin_email)

        if not recipients:
            err_msg = f"No valid email addresses found for farmer ({farmer.name}) or administrator."
            logger.warning(err_msg)
            return {"sent": False, "error": err_msg}

        # Prepare template context
        date_str = attendance.date.strftime('%Y-%m-%d') if hasattr(attendance.date, 'strftime') else str(attendance.date)
        check_in_str = attendance.check_in.strftime('%H:%M:%S') if attendance.check_in else "—"
        check_out_str = attendance.check_out.strftime('%H:%M:%S') if attendance.check_out else "—"
        total_hours_val = f"{attendance.total_hours:.2f}" if attendance.total_hours is not None else "0.00"
        work_desc = (attendance.work_description or '').strip() or "General agricultural duties and farm maintenance completed."

        context = {
            'farmer_name': farmer.name,
            'farmer_email': farmer_email or 'Unregistered',
            'record_date': date_str,
            'check_in_time': check_in_str,
            'check_out_time': check_out_str,
            'total_hours': total_hours_val,
            'location': attendance.location or farmer.field or "Main Field",
            'work_description': work_desc,
            'admin_email': admin_email,
            'attendance_id': attendance.id,
        }

        subject = f"FarmSync Daily Work Report – {farmer.name} – {date_str}"

        # Plain-text fallback version
        text_body = (
            f"Hello {farmer.name},\n\n"
            f"Your work session has been successfully recorded.\n\n"
            f"WORK SESSION SUMMARY\n"
            f"----------------------------------------\n"
            f"Farmer: {farmer.name}\n"
            f"Email: {farmer_email}\n"
            f"Date: {date_str}\n"
            f"Location: {context['location']}\n"
            f"Check-In: {check_in_str}\n"
            f"Check-Out: {check_out_str}\n"
            f"Total Working Time: {total_hours_val} hrs\n\n"
            f"WORK COMPLETED TODAY\n"
            f"----------------------------------------\n"
            f"{work_desc}\n\n"
            f"Your attendance and work report have been successfully recorded in FarmSync.\n"
            f"A copy of this report has also been sent to the FarmSync administrator ({admin_email}).\n\n"
            f"Thank you,\n"
            f"FarmSync – Smart Agriculture & AI Monitoring System\n"
        )

        # HTML template rendering
        try:
            html_body = render_to_string('emails/farmer_checkout_report.html', context)
        except Exception as tpl_err:
            logger.error(f"Error rendering farmer checkout report email template: {tpl_err}", exc_info=True)
            html_body = f"<pre>{text_body}</pre>"

        # Retrieve dynamic SMTP sender configuration
        sender_config = EmailSenderConfig.get_active_config()
        from_email = f"{sender_config.sender_name} <{sender_config.sender_email}>"
        clean_password = (sender_config.smtp_password or '').replace(' ', '').strip()

        try:
            backend_cls = getattr(settings, 'EMAIL_BACKEND', 'django.core.mail.backends.smtp.EmailBackend')
            if 'locmem' in backend_cls:
                connection = get_connection(backend=backend_cls)
            else:
                connection = get_connection(
                    backend='django.core.mail.backends.smtp.EmailBackend',
                    host=sender_config.smtp_host,
                    port=sender_config.smtp_port,
                    username=sender_config.smtp_username or sender_config.sender_email,
                    password=clean_password,
                    use_tls=sender_config.use_tls,
                    use_ssl=sender_config.use_ssl,
                    timeout=15
                )

            email_msg = EmailMultiAlternatives(
                subject=subject,
                body=text_body,
                from_email=from_email,
                to=recipients,
                connection=connection
            )
            email_msg.attach_alternative(html_body, "text/html")
            email_msg.send(fail_silently=False)

            logger.info(f"Daily work report email successfully sent to {recipients} for {farmer.name} (Attendance #{attendance.id})")
            return {
                "sent": True,
                "recipients": recipients,
                "subject": subject,
                "error": None
            }

        except Exception as send_err:
            logger.error(f"Failed to dispatch daily work report email for attendance #{attendance.id}: {send_err}", exc_info=True)
            return {
                "sent": False,
                "recipients": recipients,
                "subject": subject,
                "error": str(send_err)
            }
