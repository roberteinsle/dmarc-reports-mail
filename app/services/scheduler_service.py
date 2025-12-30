"""
Scheduler service for orchestrating DMARC report processing.
"""
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime
import json
import logging
import time

from app.services.imap_service import IMAPService
from app.services.parser_service import DMARCParserService
from app.services.claude_service import ClaudeService
from app.services.alert_service import AlertService
from app.models.database import db, Report, Record, Alert, ProcessingLog

logger = logging.getLogger(__name__)

# Global scheduler instance
scheduler = None


def init_scheduler(app):
    """
    Initialize and start the APScheduler.

    Args:
        app: Flask application instance
    """
    global scheduler

    if scheduler is not None:
        logger.warning("Scheduler already initialized")
        return scheduler

    scheduler = BackgroundScheduler()

    # Get interval from config
    interval_minutes = app.config.get('SCHEDULER_INTERVAL_MINUTES', 5)

    # Add job
    scheduler.add_job(
        func=lambda: scheduled_job(app),
        trigger=IntervalTrigger(minutes=interval_minutes),
        id='dmarc_processing_job',
        name='Process DMARC Reports',
        replace_existing=True
    )

    scheduler.start()
    logger.info(f"Scheduler started with {interval_minutes} minute interval")

    # Run immediately on startup
    logger.info("Running initial DMARC report processing on startup")
    scheduled_job(app)

    return scheduler


def stop_scheduler():
    """Stop the scheduler gracefully."""
    global scheduler
    if scheduler is not None:
        scheduler.shutdown()
        scheduler = None
        logger.info("Scheduler stopped")


def trigger_manual_processing(app):
    """
    Manually trigger DMARC report processing.

    Args:
        app: Flask application instance

    Returns:
        dict: Status of the manual trigger
    """
    logger.info("Manual processing triggered via API")
    try:
        with app.app_context():
            scheduled_job(app)
        return {'status': 'success', 'message': 'Processing started successfully'}
    except Exception as e:
        logger.error(f"Manual processing failed: {e}", exc_info=True)
        return {'status': 'error', 'message': str(e)}


def scheduled_job(app):
    """
    Main scheduled job function that runs every interval.

    Args:
        app: Flask application instance
    """
    with app.app_context():
        logger.info("Starting scheduled DMARC report processing")
        start_time = time.time()

        try:
            process_dmarc_reports(app)
            duration_ms = int((time.time() - start_time) * 1000)

            # Log successful processing
            log_processing('scheduled_job', 'success', 'Completed successfully', duration_ms=duration_ms)

        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            logger.error(f"Scheduled job failed: {e}", exc_info=True)
            log_processing('scheduled_job', 'failure', str(e), duration_ms=duration_ms)


def process_dmarc_reports(app):
    """
    Main processing pipeline for DMARC reports.

    Args:
        app: Flask application instance
    """
    # Initialize services
    imap_service = IMAPService(
        host=app.config['IMAP_HOST'],
        port=app.config['IMAP_PORT'],
        user=app.config['IMAP_USER'],
        password=app.config['IMAP_PASSWORD'],
        folder=app.config['IMAP_FOLDER']
    )

    claude_service = ClaudeService(api_key=app.config['ANTHROPIC_API_KEY'])

    alert_service = AlertService(
        smtp_host=app.config['SMTP_HOST'],
        smtp_port=app.config['SMTP_PORT'],
        smtp_user=app.config['SMTP_USER'],
        smtp_password=app.config['SMTP_PASSWORD'],
        smtp_from=app.config['SMTP_FROM'],
        alert_recipient=app.config['ALERT_RECIPIENT']
    )

    parser_service = DMARCParserService()

    processed_count = 0
    error_count = 0

    # Connect to IMAP
    if not imap_service.connect():
        logger.error("Failed to connect to IMAP server")
        return

    try:
        # Search for DMARC reports
        message_ids = imap_service.search_dmarc_reports()

        for msg_id in message_ids:
            try:
                # Fetch email
                email_message = imap_service.fetch_email(msg_id)
                if not email_message:
                    continue

                # Extract attachments
                attachments = imap_service.extract_attachments(email_message)

                for filename, file_bytes in attachments:
                    # Skip non-XML files
                    if not (filename.endswith('.xml') or filename.endswith('.gz') or filename.endswith('.zip')):
                        continue

                    # Decompress if needed
                    xml_bytes = imap_service.decompress_file(file_bytes, filename)
                    if not xml_bytes:
                        continue

                    # Parse XML
                    xml_string = xml_bytes.decode('utf-8', errors='ignore')
                    report_data = parser_service.parse_dmarc_xml(xml_string)

                    if not report_data:
                        logger.warning(f"Failed to parse report from {filename}")
                        continue

                    # Check if report already exists
                    existing_report = Report.query.filter_by(
                        report_id=report_data['report_id']
                    ).first()

                    if existing_report:
                        logger.info(f"Report {report_data['report_id']} already processed, skipping")
                        continue

                    # Save report to database
                    records_data = report_data.pop('records', [])
                    report = Report(**{k: v for k, v in report_data.items() if hasattr(Report, k)})
                    db.session.add(report)
                    db.session.flush()  # Get report.id

                    # Save records
                    for record_data in records_data:
                        record = Record(report_id=report.id, **record_data)
                        db.session.add(record)

                    # Analyze with Claude
                    logger.info(f"Analyzing report {report.report_id} with Claude AI")
                    claude_analysis = claude_service.analyze_report(report_data, records_data)

                    if claude_analysis:
                        report.claude_analysis = json.dumps(claude_analysis)
                        report.processed_at = datetime.utcnow()
                        report.status = 'processed'

                        # Evaluate alert criteria
                        alert_data = alert_service.evaluate_alert_criteria(
                            report_data, records_data, claude_analysis
                        )

                        if alert_data:
                            # Check throttling
                            if not alert_service.should_throttle_alert(
                                alert_data['alert_type'], db.session
                            ):
                                # Create alert record
                                alert = Alert(
                                    report_id=report.id,
                                    alert_type=alert_data['alert_type'],
                                    severity=alert_data['severity'],
                                    title=alert_data['title'],
                                    message=json.dumps(alert_data['alerts']),
                                    details=json.dumps(claude_analysis),
                                    email_recipient=app.config['ALERT_RECIPIENT']
                                )
                                db.session.add(alert)
                                db.session.flush()

                                # Send alert email
                                if alert_service.send_alert_email(alert_data):
                                    alert.email_sent = True
                                    alert.email_sent_at = datetime.utcnow()
                                    logger.info(f"Alert sent for report {report.report_id}")
                            else:
                                logger.info(f"Alert throttled for report {report.report_id}")
                    else:
                        report.status = 'error'
                        report.error_message = 'Claude analysis failed'

                    db.session.commit()
                    processed_count += 1

                    logger.info(f"Successfully processed report {report.report_id}")

                # Delete email after successful processing
                imap_service.delete_email(msg_id)

            except Exception as e:
                logger.error(f"Failed to process email {msg_id}: {e}", exc_info=True)
                db.session.rollback()
                error_count += 1
                continue

    finally:
        imap_service.close()

    logger.info(f"Processing complete: {processed_count} reports processed, {error_count} errors")


def log_processing(job_type: str, status: str, message: str, details: dict = None, duration_ms: int = None):
    """
    Log processing event to database.

    Args:
        job_type: Type of job
        status: Status (success, failure, partial)
        message: Log message
        details: Additional details as dict
        duration_ms: Duration in milliseconds
    """
    try:
        log_entry = ProcessingLog(
            job_type=job_type,
            status=status,
            message=message,
            details=json.dumps(details) if details else None,
            duration_ms=duration_ms
        )
        db.session.add(log_entry)
        db.session.commit()
    except Exception as e:
        logger.error(f"Failed to log processing event: {e}", exc_info=True)
        db.session.rollback()
