"""
Alert service for sending email notifications via AWS SES.
"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Optional
from datetime import datetime, timedelta
import logging
import json

logger = logging.getLogger(__name__)


class AlertService:
    """Service for handling alert notifications."""

    def __init__(self, smtp_host: str, smtp_port: int, smtp_user: str,
                 smtp_password: str, smtp_from: str, alert_recipient: str):
        """
        Initialize Alert service.

        Args:
            smtp_host: SMTP server hostname
            smtp_port: SMTP server port
            smtp_user: SMTP username
            smtp_password: SMTP password
            smtp_from: From email address
            alert_recipient: Alert recipient email address
        """
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.smtp_user = smtp_user
        self.smtp_password = smtp_password
        self.smtp_from = smtp_from
        self.alert_recipient = alert_recipient

    def evaluate_alert_criteria(self, report_data: Dict, records: list,
                                claude_analysis: Optional[Dict]) -> Optional[Dict]:
        """
        Evaluate if alert should be sent based on criteria.

        Args:
            report_data: Report metadata
            records: Authentication records
            claude_analysis: Claude AI analysis results

        Returns:
            Alert data dict if alert needed, None otherwise
        """
        alerts = []

        # Check for DMARC/SPF/DKIM failures
        for record in records:
            count = record.get('count', 0)

            # DMARC failures (quarantine/reject)
            if record.get('disposition') in ['quarantine', 'reject'] and count > 0:
                alerts.append({
                    'type': 'dmarc_failure',
                    'severity': 'high' if record.get('disposition') == 'reject' else 'medium',
                    'message': f"{count} email(s) from {record.get('source_ip')} were {record.get('disposition')}d"
                })

            # SPF failures
            if record.get('spf_result') == 'fail' and count > 5:
                alerts.append({
                    'type': 'spf_failure',
                    'severity': 'medium',
                    'message': f"{count} email(s) failed SPF check from {record.get('source_ip')}"
                })

            # DKIM failures
            if record.get('dkim_result') == 'fail' and count > 5:
                alerts.append({
                    'type': 'dkim_failure',
                    'severity': 'medium',
                    'message': f"{count} email(s) failed DKIM check from {record.get('source_ip')}"
                })

        # Check Claude analysis for unauthorized sources and anomalies
        if claude_analysis:
            unauthorized = claude_analysis.get('unauthorized_sources', [])
            if unauthorized:
                alerts.append({
                    'type': 'unauthorized_sender',
                    'severity': 'high',
                    'message': f"Unauthorized sending sources detected: {', '.join(str(s) for s in unauthorized[:3])}"
                })

            anomalies = claude_analysis.get('anomalies', [])
            if anomalies:
                severity = claude_analysis.get('severity', 'medium')
                alerts.append({
                    'type': 'suspicious_pattern',
                    'severity': severity,
                    'message': f"Suspicious patterns detected: {anomalies[0] if anomalies else 'See details'}"
                })

        # Return alert data if any alerts triggered
        if alerts:
            # Use highest severity
            severity_order = {'low': 0, 'medium': 1, 'high': 2, 'critical': 3}
            max_severity = max(alerts, key=lambda x: severity_order.get(x['severity'], 0))['severity']

            return {
                'alert_type': alerts[0]['type'],  # Primary alert type
                'severity': max_severity,
                'title': f"DMARC Alert: {report_data.get('policy_domain', 'Unknown')}",
                'alerts': alerts,
                'report_data': report_data,
                'claude_analysis': claude_analysis
            }

        return None

    def send_alert_email(self, alert_data: Dict) -> bool:
        """
        Send alert email via AWS SES SMTP.

        Args:
            alert_data: Alert data dictionary

        Returns:
            True if email sent successfully, False otherwise
        """
        try:
            # Create email
            msg = MIMEMultipart('alternative')
            msg['Subject'] = f"[{alert_data['severity'].upper()}] {alert_data['title']}"
            msg['From'] = self.smtp_from
            msg['To'] = self.alert_recipient

            # Create HTML body
            html_body = self._format_alert_html(alert_data)

            # Create plain text body
            text_body = self._format_alert_text(alert_data)

            # Attach both parts
            part1 = MIMEText(text_body, 'plain')
            part2 = MIMEText(html_body, 'html')
            msg.attach(part1)
            msg.attach(part2)

            # Connect and send
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)

            logger.info(f"Alert email sent to {self.alert_recipient}")
            return True

        except Exception as e:
            logger.error(f"Failed to send alert email: {e}", exc_info=True)
            return False

    def _format_alert_html(self, alert_data: Dict) -> str:
        """Format alert as HTML email."""
        severity = alert_data['severity']
        severity_color = {
            'low': '#28a745',
            'medium': '#ffc107',
            'high': '#fd7e14',
            'critical': '#dc3545'
        }.get(severity, '#6c757d')

        alerts_html = ''
        for alert in alert_data.get('alerts', []):
            alerts_html += f"""
            <li style="margin-bottom: 10px;">
                <strong>{alert['type'].replace('_', ' ').title()}:</strong><br>
                {alert['message']}
            </li>
            """

        recommendations_html = ''
        if alert_data.get('claude_analysis') and alert_data['claude_analysis'].get('recommendations'):
            recommendations_html = '<h3>Recommendations:</h3><ul>'
            for rec in alert_data['claude_analysis']['recommendations']:
                recommendations_html += f'<li>{rec}</li>'
            recommendations_html += '</ul>'

        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; }}
                .header {{ background-color: {severity_color}; color: white; padding: 20px; }}
                .content {{ padding: 20px; }}
                .severity {{ display: inline-block; padding: 5px 10px; background-color: {severity_color}; color: white; border-radius: 3px; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h2>{alert_data['title']}</h2>
                <span class="severity">{severity.upper()}</span>
            </div>
            <div class="content">
                <h3>Issues Detected:</h3>
                <ul>
                    {alerts_html}
                </ul>

                {recommendations_html}

                <hr>
                <p><small>
                    Domain: {alert_data.get('report_data', {}).get('policy_domain', 'N/A')}<br>
                    Reporter: {alert_data.get('report_data', {}).get('org_name', 'N/A')}<br>
                    Report ID: {alert_data.get('report_data', {}).get('report_id', 'N/A')}
                </small></p>
            </div>
        </body>
        </html>
        """
        return html

    def _format_alert_text(self, alert_data: Dict) -> str:
        """Format alert as plain text email."""
        text = f"""DMARC ALERT - {alert_data['severity'].upper()}

{alert_data['title']}

Issues Detected:
"""
        for alert in alert_data.get('alerts', []):
            text += f"\n- {alert['type'].replace('_', ' ').title()}:\n  {alert['message']}\n"

        if alert_data.get('claude_analysis') and alert_data['claude_analysis'].get('recommendations'):
            text += "\nRecommendations:\n"
            for rec in alert_data['claude_analysis']['recommendations']:
                text += f"- {rec}\n"

        text += f"""
---
Domain: {alert_data.get('report_data', {}).get('policy_domain', 'N/A')}
Reporter: {alert_data.get('report_data', {}).get('org_name', 'N/A')}
Report ID: {alert_data.get('report_data', {}).get('report_id', 'N/A')}
"""
        return text

    def should_throttle_alert(self, alert_type: str, db_session, timeframe_minutes: int = 60) -> bool:
        """
        Check if alert should be throttled to prevent spam.

        Args:
            alert_type: Type of alert
            db_session: Database session
            timeframe_minutes: Throttle timeframe in minutes

        Returns:
            True if should throttle (already sent recently), False otherwise
        """
        from app.models.database import Alert

        # Check for recent alerts of same type
        threshold = datetime.utcnow() - timedelta(minutes=timeframe_minutes)
        recent_alert = db_session.query(Alert).filter(
            Alert.alert_type == alert_type,
            Alert.email_sent == True,
            Alert.created_at >= threshold
        ).first()

        if recent_alert:
            logger.info(f"Throttling alert of type {alert_type} (sent recently)")
            return True

        return False
