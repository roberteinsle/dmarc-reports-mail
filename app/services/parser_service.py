"""
DMARC XML report parsing service.
"""
import xml.etree.ElementTree as ET
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


class DMARCParserService:
    """Service for parsing DMARC XML reports."""

    @staticmethod
    def parse_dmarc_xml(xml_string: str) -> Optional[Dict]:
        """
        Parse DMARC XML report.

        Args:
            xml_string: XML content as string

        Returns:
            Dictionary with parsed report data or None if parsing fails
        """
        try:
            root = ET.fromstring(xml_string)
        except ET.ParseError as e:
            logger.error(f"XML parsing error: {e}", exc_info=True)
            return None

        try:
            # Extract report metadata
            metadata = DMARCParserService._extract_report_metadata(root)

            # Extract policy published
            policy = DMARCParserService._extract_policy_published(root)

            # Extract records
            records = DMARCParserService._extract_records(root)

            # Combine all data
            report_data = {
                **metadata,
                **policy,
                'records': records
            }

            logger.info(f"Parsed DMARC report: {metadata.get('report_id')} with {len(records)} record(s)")
            return report_data

        except Exception as e:
            logger.error(f"Failed to parse DMARC report: {e}", exc_info=True)
            return None

    @staticmethod
    def _extract_report_metadata(root: ET.Element) -> Dict:
        """Extract report metadata section."""
        metadata = root.find('report_metadata')
        if metadata is None:
            raise ValueError("Missing report_metadata section")

        org_name = metadata.findtext('org_name', '')
        email_elem = metadata.find('email')
        email_val = email_elem.text if email_elem is not None else ''
        report_id = metadata.findtext('report_id', '')

        date_range = metadata.find('date_range')
        if date_range is not None:
            date_begin = int(date_range.findtext('begin', '0'))
            date_end = int(date_range.findtext('end', '0'))
        else:
            date_begin = 0
            date_end = 0

        return {
            'org_name': org_name,
            'email': email_val,
            'report_id': report_id,
            'date_begin': date_begin,
            'date_end': date_end
        }

    @staticmethod
    def _extract_policy_published(root: ET.Element) -> Dict:
        """Extract policy published section."""
        policy = root.find('policy_published')
        if policy is None:
            logger.warning("Missing policy_published section")
            return {}

        return {
            'policy_domain': policy.findtext('domain', ''),
            'policy_adkim': policy.findtext('adkim', ''),
            'policy_aspf': policy.findtext('aspf', ''),
            'policy_p': policy.findtext('p', ''),
            'policy_sp': policy.findtext('sp', ''),
            'policy_pct': int(policy.findtext('pct', '100'))
        }

    @staticmethod
    def _extract_records(root: ET.Element) -> List[Dict]:
        """Extract all record/row elements."""
        records = []

        for record in root.findall('record'):
            try:
                row = record.find('row')
                if row is None:
                    continue

                # Source IP and count
                source_ip = row.findtext('source_ip', '')
                count = int(row.findtext('count', '0'))

                # Policy evaluated
                policy_evaluated = row.find('policy_evaluated')
                if policy_evaluated is not None:
                    disposition = policy_evaluated.findtext('disposition', '')
                    dkim = policy_evaluated.findtext('dkim', '')
                    spf = policy_evaluated.findtext('spf', '')
                else:
                    disposition = ''
                    dkim = ''
                    spf = ''

                # Identifiers
                identifiers = record.find('identifiers')
                if identifiers is not None:
                    header_from = identifiers.findtext('header_from', '')
                else:
                    header_from = ''

                # Auth results
                auth_results = record.find('auth_results')
                dkim_auth = {}
                spf_auth = {}

                if auth_results is not None:
                    # DKIM
                    dkim_elem = auth_results.find('dkim')
                    if dkim_elem is not None:
                        dkim_auth = {
                            'dkim_domain': dkim_elem.findtext('domain', ''),
                            'dkim_selector': dkim_elem.findtext('selector', ''),
                            'dkim_result_detail': dkim_elem.findtext('result', '')
                        }

                    # SPF
                    spf_elem = auth_results.find('spf')
                    if spf_elem is not None:
                        spf_auth = {
                            'spf_domain': spf_elem.findtext('domain', ''),
                            'spf_scope': spf_elem.findtext('scope', ''),
                            'spf_result_detail': spf_elem.findtext('result', '')
                        }

                # Build record dict
                record_data = {
                    'source_ip': source_ip,
                    'count': count,
                    'disposition': disposition,
                    'dkim_result': dkim,
                    'spf_result': spf,
                    'header_from': header_from,
                    **dkim_auth,
                    **spf_auth
                }

                records.append(record_data)

            except Exception as e:
                logger.warning(f"Failed to parse record: {e}")
                continue

        return records

    @staticmethod
    def validate_xml_structure(xml_string: str) -> bool:
        """
        Validate basic XML structure.

        Args:
            xml_string: XML content

        Returns:
            True if valid, False otherwise
        """
        try:
            root = ET.fromstring(xml_string)
            # Check for required elements
            if root.find('report_metadata') is None:
                return False
            if root.find('policy_published') is None:
                return False
            if not root.findall('record'):
                return False
            return True
        except ET.ParseError:
            return False
