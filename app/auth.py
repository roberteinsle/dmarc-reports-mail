"""
Magic Link authentication for DMARC Reports Mail.
"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from functools import wraps
import logging

from flask import Blueprint, render_template, request, redirect, url_for, session, flash, current_app
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature

logger = logging.getLogger(__name__)

bp = Blueprint('auth', __name__, url_prefix='/auth')

# Token validity: 15 minutes
TOKEN_MAX_AGE = 900


def get_serializer():
    """Get URL-safe timed serializer using app secret key."""
    return URLSafeTimedSerializer(current_app.config['SECRET_KEY'])


def generate_magic_token(email: str) -> str:
    """Generate a time-limited magic link token."""
    s = get_serializer()
    return s.dumps(email, salt='magic-link')


def verify_magic_token(token: str) -> str | None:
    """Verify magic link token and return email if valid."""
    s = get_serializer()
    try:
        email = s.loads(token, salt='magic-link', max_age=TOKEN_MAX_AGE)
        return email
    except (SignatureExpired, BadSignature):
        return None


def send_magic_link(email: str, link: str):
    """Send magic link email via SMTP."""
    app = current_app

    msg = MIMEMultipart('alternative')
    msg['Subject'] = 'DMARC Reports - Anmelde-Link'
    msg['From'] = app.config['SMTP_FROM']
    msg['To'] = email

    text = f"""DMARC Reports Mail - Anmeldung

Klicke auf den folgenden Link um dich anzumelden:

{link}

Dieser Link ist 15 Minuten gültig.

Falls du diese Anmeldung nicht angefordert hast, kannst du diese E-Mail ignorieren.
"""

    html = f"""
    <!DOCTYPE html>
    <html lang="de">
    <head><style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; }}
        .container {{ max-width: 500px; margin: 0 auto; padding: 20px; }}
        .btn {{ display: inline-block; padding: 12px 24px; background-color: #0d6efd;
                color: white; text-decoration: none; border-radius: 5px; margin: 20px 0; }}
        .footer {{ margin-top: 30px; font-size: 0.85em; color: #6c757d; }}
    </style></head>
    <body>
        <div class="container">
            <h2>DMARC Reports Mail</h2>
            <p>Klicke auf den Button um dich anzumelden:</p>
            <a href="{link}" class="btn">Jetzt anmelden</a>
            <p class="footer">
                Dieser Link ist 15 Minuten gültig.<br>
                Falls du diese Anmeldung nicht angefordert hast, kannst du diese E-Mail ignorieren.
            </p>
        </div>
    </body>
    </html>
    """

    msg.attach(MIMEText(text, 'plain'))
    msg.attach(MIMEText(html, 'html'))

    with smtplib.SMTP(app.config['SMTP_HOST'], app.config['SMTP_PORT']) as server:
        server.starttls()
        server.login(app.config['SMTP_USER'], app.config['SMTP_PASSWORD'])
        server.send_message(msg)

    logger.info(f"Magic link sent to {email}")


def login_required(f):
    """Decorator to require authentication."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('authenticated'):
            return redirect(url_for('auth.login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function


@bp.route('/login', methods=['GET', 'POST'])
def login():
    """Login page - request magic link."""
    if session.get('authenticated'):
        return redirect('/')

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        auth_email = current_app.config.get('AUTH_EMAIL', '').strip().lower()

        if email and email == auth_email:
            try:
                token = generate_magic_token(email)
                link = url_for('auth.verify', token=token, _external=True)
                send_magic_link(email, link)
            except Exception as e:
                logger.error(f"Failed to send magic link: {e}", exc_info=True)
                # Don't reveal the error to prevent email enumeration
                pass

        # Always show the same message to prevent email enumeration
        return render_template('check_email.html')

    return render_template('login.html')


@bp.route('/verify')
def verify():
    """Verify magic link token."""
    token = request.args.get('token', '')
    email = verify_magic_token(token)

    if email:
        auth_email = current_app.config.get('AUTH_EMAIL', '').strip().lower()
        if email == auth_email:
            session['authenticated'] = True
            session.permanent = True
            logger.info(f"User {email} authenticated via magic link")
            next_url = request.args.get('next', '/')
            return redirect(next_url)

    flash('Der Anmelde-Link ist ungültig oder abgelaufen.', 'danger')
    return redirect(url_for('auth.login'))


@bp.route('/logout')
def logout():
    """Logout and clear session."""
    session.clear()
    return redirect(url_for('auth.login'))
