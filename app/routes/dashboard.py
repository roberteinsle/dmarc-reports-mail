"""
Dashboard routes for DMARC Reports Mail web interface.
"""
from flask import Blueprint, render_template, jsonify, request
from sqlalchemy import func, desc
from app.models.database import db, Report, Record, Alert, ProcessingLog
from datetime import datetime, timedelta
import json

bp = Blueprint('dashboard', __name__)


@bp.route('/')
def index():
    """Dashboard home page with overview statistics."""
    # Get statistics
    total_reports = Report.query.count()
    total_alerts = Alert.query.filter_by(email_sent=True).count()

    # Pass rate calculation
    total_records = Record.query.count()
    passed_records = Record.query.filter(
        Record.spf_result == 'pass',
        Record.dkim_result == 'pass'
    ).count()
    pass_rate = round((passed_records / total_records * 100) if total_records > 0 else 100, 1)

    # Recent reports
    recent_reports = Report.query.order_by(desc(Report.created_at)).limit(10).all()

    # Recent alerts
    recent_alerts = Alert.query.filter_by(email_sent=True).order_by(
        desc(Alert.created_at)
    ).limit(10).all()

    return render_template('dashboard.html',
                         total_reports=total_reports,
                         total_alerts=total_alerts,
                         pass_rate=pass_rate,
                         recent_reports=recent_reports,
                         recent_alerts=recent_alerts)


@bp.route('/reports')
def reports():
    """List all reports with pagination."""
    page = request.args.get('page', 1, type=int)
    per_page = 20

    pagination = Report.query.order_by(desc(Report.created_at)).paginate(
        page=page, per_page=per_page, error_out=False
    )

    return render_template('reports.html', pagination=pagination)


@bp.route('/reports/<int:report_id>')
def report_detail(report_id):
    """Detailed view of a single report."""
    report = Report.query.get_or_404(report_id)
    records = Record.query.filter_by(report_id=report_id).all()
    alerts = Alert.query.filter_by(report_id=report_id).all()

    # Enrich records with IP information
    from app.utils.ip_utils import enrich_records_with_ip_info
    records = enrich_records_with_ip_info(records)

    # Parse Claude analysis
    claude_analysis = None
    if report.claude_analysis:
        try:
            claude_analysis = json.loads(report.claude_analysis)
            # Clean up old format where summary contains JSON code blocks
            if 'summary' in claude_analysis and isinstance(claude_analysis['summary'], str):
                summary = claude_analysis['summary']
                # Remove ```json and ``` markers if present
                if summary.startswith('```json'):
                    # Extract JSON from code block
                    import re
                    json_match = re.search(r'```json\s*(\{.*?\})\s*```', summary, re.DOTALL)
                    if json_match:
                        try:
                            # Parse the inner JSON
                            inner_data = json.loads(json_match.group(1))
                            # Merge with existing data, inner takes precedence
                            claude_analysis.update(inner_data)
                        except json.JSONDecodeError:
                            # If parsing fails, just clean the summary text
                            claude_analysis['summary'] = summary.replace('```json', '').replace('```', '').strip()
                    else:
                        claude_analysis['summary'] = summary.replace('```json', '').replace('```', '').strip()
        except json.JSONDecodeError:
            claude_analysis = {'summary': report.claude_analysis}

    return render_template('report_detail.html',
                         report=report,
                         records=records,
                         alerts=alerts,
                         claude_analysis=claude_analysis)


@bp.route('/alerts')
def alerts():
    """View alert history."""
    page = request.args.get('page', 1, type=int)
    severity_filter = request.args.get('severity')
    per_page = 20

    query = Alert.query

    if severity_filter:
        query = query.filter_by(severity=severity_filter)

    pagination = query.order_by(desc(Alert.created_at)).paginate(
        page=page, per_page=per_page, error_out=False
    )

    return render_template('alerts.html',
                         pagination=pagination,
                         severity_filter=severity_filter)


@bp.route('/api/stats')
def api_stats():
    """API endpoint for dashboard statistics (used by charts)."""
    # Reports over time (last 30 days)
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    reports_by_date = db.session.query(
        func.date(Report.created_at).label('date'),
        func.count(Report.id).label('count')
    ).filter(Report.created_at >= thirty_days_ago).group_by(
        func.date(Report.created_at)
    ).all()

    # SPF/DKIM pass rates
    spf_pass = Record.query.filter_by(spf_result='pass').count()
    spf_fail = Record.query.filter_by(spf_result='fail').count()
    dkim_pass = Record.query.filter_by(dkim_result='pass').count()
    dkim_fail = Record.query.filter_by(dkim_result='fail').count()

    # Top source IPs
    top_ips = db.session.query(
        Record.source_ip,
        func.sum(Record.count).label('total_count')
    ).group_by(Record.source_ip).order_by(
        desc('total_count')
    ).limit(10).all()

    # Alert severity distribution
    alert_severity = db.session.query(
        Alert.severity,
        func.count(Alert.id).label('count')
    ).group_by(Alert.severity).all()

    return jsonify({
        'reports_by_date': [{'date': str(r.date), 'count': r.count} for r in reports_by_date],
        'spf_stats': {'pass': spf_pass, 'fail': spf_fail},
        'dkim_stats': {'pass': dkim_pass, 'fail': dkim_fail},
        'top_ips': [{'ip': ip, 'count': count} for ip, count in top_ips],
        'alert_severity': [{'severity': sev, 'count': count} for sev, count in alert_severity]
    })


@bp.route('/health')
def health():
    """Health check endpoint for Docker and monitoring."""
    health_status = {
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat()
    }

    # Check database
    try:
        db.session.execute(db.text('SELECT 1'))
        health_status['database'] = 'connected'
    except Exception as e:
        health_status['database'] = 'disconnected'
        health_status['status'] = 'unhealthy'
        health_status['error'] = str(e)

    # Check scheduler
    from app.services.scheduler_service import scheduler
    if scheduler and scheduler.running:
        health_status['scheduler'] = 'running'

        # Get last processing log
        last_log = ProcessingLog.query.order_by(desc(ProcessingLog.created_at)).first()
        if last_log:
            health_status['last_check'] = last_log.created_at.isoformat()
    else:
        health_status['scheduler'] = 'stopped'
        health_status['status'] = 'unhealthy'

    status_code = 200 if health_status['status'] == 'healthy' else 503
    return jsonify(health_status), status_code


@bp.route('/api/trigger-processing', methods=['POST'])
def trigger_processing():
    """Manually trigger DMARC report processing."""
    from flask import current_app
    from app.services.scheduler_service import trigger_manual_processing

    result = trigger_manual_processing(current_app._get_current_object())
    status_code = 200 if result['status'] == 'success' else 500

    return jsonify(result), status_code
