"""
Username/password authentication for DMARC Reports Mail.
"""
import hmac
from functools import wraps
import logging

from flask import Blueprint, render_template, request, redirect, url_for, session, flash, current_app

logger = logging.getLogger(__name__)

bp = Blueprint('auth', __name__, url_prefix='/auth')


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
    """Login page - username and password."""
    if session.get('authenticated'):
        return redirect('/')

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        auth_username = current_app.config.get('AUTH_USERNAME', '')
        auth_password = current_app.config.get('AUTH_PASSWORD', '')

        username_ok = hmac.compare_digest(username, auth_username)
        password_ok = hmac.compare_digest(password, auth_password)

        if username_ok and password_ok:
            session['authenticated'] = True
            session.permanent = True
            logger.info(f"User '{username}' authenticated via password login")
            next_url = request.args.get('next', '/')
            return redirect(next_url)

        logger.warning(f"Failed login attempt for username '{username}'")
        flash('Benutzername oder Passwort falsch.', 'danger')

    return render_template('login.html')


@bp.route('/logout')
def logout():
    """Logout and clear session."""
    session.clear()
    return redirect(url_for('auth.login'))
