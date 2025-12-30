"""
Database models for DMARC Reports Mail application.
"""
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Report(db.Model):
    """DMARC Report model."""
    __tablename__ = 'reports'

    id = db.Column(db.Integer, primary_key=True)
    report_id = db.Column(db.String(255), unique=True, nullable=False, index=True)
    org_name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255))
    domain = db.Column(db.String(255), nullable=False, index=True)
    date_begin = db.Column(db.Integer, nullable=False, index=True)
    date_end = db.Column(db.Integer, nullable=False)

    # Policy published
    policy_domain = db.Column(db.String(255))
    policy_adkim = db.Column(db.String(10))
    policy_aspf = db.Column(db.String(10))
    policy_p = db.Column(db.String(20))
    policy_sp = db.Column(db.String(20))
    policy_pct = db.Column(db.Integer)

    # Processing metadata
    received_at = db.Column(db.DateTime, default=datetime.utcnow)
    processed_at = db.Column(db.DateTime)
    claude_analysis = db.Column(db.Text)  # JSON blob

    # Status
    status = db.Column(db.String(20), default='pending', index=True)
    error_message = db.Column(db.Text)

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    records = db.relationship('Record', backref='report', lazy='dynamic', cascade='all, delete-orphan')
    alerts = db.relationship('Alert', backref='report', lazy='dynamic', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Report {self.report_id} - {self.domain}>'

    def to_dict(self):
        """Convert report to dictionary."""
        return {
            'id': self.id,
            'report_id': self.report_id,
            'org_name': self.org_name,
            'email': self.email,
            'domain': self.domain,
            'date_begin': self.date_begin,
            'date_end': self.date_end,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'processed_at': self.processed_at.isoformat() if self.processed_at else None,
        }


class Record(db.Model):
    """Individual email authentication record."""
    __tablename__ = 'records'

    id = db.Column(db.Integer, primary_key=True)
    report_id = db.Column(db.Integer, db.ForeignKey('reports.id', ondelete='CASCADE'), nullable=False, index=True)

    # Row data
    source_ip = db.Column(db.String(45), nullable=False, index=True)
    count = db.Column(db.Integer, nullable=False)

    # Policy evaluated
    disposition = db.Column(db.String(20))
    dkim_result = db.Column(db.String(20))
    spf_result = db.Column(db.String(20))

    # DKIM auth results
    dkim_domain = db.Column(db.String(255))
    dkim_selector = db.Column(db.String(255))
    dkim_result_detail = db.Column(db.String(20))

    # SPF auth results
    spf_domain = db.Column(db.String(255))
    spf_scope = db.Column(db.String(20))
    spf_result_detail = db.Column(db.String(20))

    # Header from
    header_from = db.Column(db.String(255))

    # Timestamp
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Record {self.source_ip} - Count: {self.count}>'

    def to_dict(self):
        """Convert record to dictionary."""
        return {
            'id': self.id,
            'source_ip': self.source_ip,
            'count': self.count,
            'disposition': self.disposition,
            'dkim_result': self.dkim_result,
            'spf_result': self.spf_result,
            'header_from': self.header_from,
        }


class Alert(db.Model):
    """Alert model for DMARC issues."""
    __tablename__ = 'alerts'

    id = db.Column(db.Integer, primary_key=True)
    report_id = db.Column(db.Integer, db.ForeignKey('reports.id', ondelete='SET NULL'), index=True)

    # Alert details
    alert_type = db.Column(db.String(50), nullable=False)
    severity = db.Column(db.String(20), nullable=False, index=True)
    title = db.Column(db.String(255), nullable=False)
    message = db.Column(db.Text, nullable=False)
    details = db.Column(db.Text)  # JSON blob

    # Email tracking
    email_sent = db.Column(db.Boolean, default=False)
    email_sent_at = db.Column(db.DateTime)
    email_recipient = db.Column(db.String(255))

    # Timestamp
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    def __repr__(self):
        return f'<Alert {self.alert_type} - {self.severity}>'

    def to_dict(self):
        """Convert alert to dictionary."""
        return {
            'id': self.id,
            'alert_type': self.alert_type,
            'severity': self.severity,
            'title': self.title,
            'message': self.message,
            'email_sent': self.email_sent,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


class ProcessingLog(db.Model):
    """Processing log for audit trail."""
    __tablename__ = 'processing_log'

    id = db.Column(db.Integer, primary_key=True)
    job_type = db.Column(db.String(50), nullable=False, index=True)
    status = db.Column(db.String(20), nullable=False)
    message = db.Column(db.Text)
    details = db.Column(db.Text)  # JSON blob
    duration_ms = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    def __repr__(self):
        return f'<ProcessingLog {self.job_type} - {self.status}>'

    def to_dict(self):
        """Convert processing log to dictionary."""
        return {
            'id': self.id,
            'job_type': self.job_type,
            'status': self.status,
            'message': self.message,
            'duration_ms': self.duration_ms,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
