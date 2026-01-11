"""
IP address utility functions.
"""
import ipaddress
import socket
import logging

logger = logging.getLogger(__name__)


def get_ip_info(ip_address: str) -> dict:
    """
    Get information about an IP address.

    Args:
        ip_address: IP address (IPv4 or IPv6)

    Returns:
        Dictionary with IP information:
        - hostname: Reverse DNS hostname (if available)
        - ip_type: 'IPv4' or 'IPv6'
        - is_private: Boolean indicating if IP is private
    """
    info = {
        'hostname': None,
        'ip_type': None,
        'is_private': False,
        'is_global': False
    }

    try:
        # Parse IP address
        ip_obj = ipaddress.ip_address(ip_address)
        info['ip_type'] = 'IPv6' if ip_obj.version == 6 else 'IPv4'
        info['is_private'] = ip_obj.is_private
        info['is_global'] = ip_obj.is_global

        # Try reverse DNS lookup
        try:
            hostname = socket.gethostbyaddr(ip_address)[0]
            info['hostname'] = hostname
        except (socket.herror, socket.gaierror):
            # No reverse DNS available
            pass

    except ValueError as e:
        logger.warning(f"Invalid IP address: {ip_address} - {e}")

    return info


def enrich_records_with_ip_info(records: list) -> list:
    """
    Enrich record list with IP information.

    Args:
        records: List of Record objects

    Returns:
        List of records with added 'ip_info' attribute
    """
    enriched_records = []

    for record in records:
        # Get IP info
        ip_info = get_ip_info(record.source_ip)

        # Add as attribute to record object
        record.ip_info = ip_info
        enriched_records.append(record)

    return enriched_records


def get_provider_from_hostname(hostname: str) -> str:
    """
    Identify email provider from hostname.

    Args:
        hostname: Reverse DNS hostname

    Returns:
        Provider name or 'Unknown'
    """
    if not hostname:
        return 'Unknown'

    hostname_lower = hostname.lower()

    # Known providers
    providers = {
        'google': ['google.com', 'googlemail.com', '1e100.net'],
        'microsoft': ['outlook.com', 'hotmail.com', 'microsoft.com', 'protection.outlook.com'],
        'amazon': ['amazon.com', 'amazonaws.com', 'amazonses.com'],
        'mailgun': ['mailgun.', 'mailgun.org'],
        'sendgrid': ['sendgrid.', 'sendgrid.net'],
        'cloudflare': ['cloudflare.com'],
        'exclaimer': ['exclaimer.'],
        'proofpoint': ['proofpoint.com', 'pphosted.com'],
        'mimecast': ['mimecast.com'],
        'office365': ['protection.outlook.com', 'outlook.com'],
    }

    for provider, domains in providers.items():
        if any(domain in hostname_lower for domain in domains):
            return provider.title()

    return 'Unknown'
