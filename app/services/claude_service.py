"""
Claude AI service for analyzing DMARC reports.
"""
import json
import time
from typing import Dict, Optional
import logging
from anthropic import Anthropic, APIError, RateLimitError

logger = logging.getLogger(__name__)


class ClaudeService:
    """Service for Claude AI integration."""

    def __init__(self, api_key: str):
        """
        Initialize Claude service.

        Args:
            api_key: Anthropic API key
        """
        self.client = Anthropic(api_key=api_key)

    def analyze_report(self, report_data: Dict, records_data: list, max_retries: int = 3) -> Optional[Dict]:
        """
        Analyze DMARC report using Claude AI.

        Args:
            report_data: Report metadata and policy
            records_data: List of authentication records
            max_retries: Maximum retry attempts

        Returns:
            Analysis dictionary or None if analysis fails
        """
        prompt = self._format_prompt(report_data, records_data)

        for attempt in range(max_retries):
            try:
                response = self.client.messages.create(
                    model="claude-sonnet-4-5-20250929",
                    max_tokens=2000,
                    messages=[
                        {"role": "user", "content": prompt}
                    ]
                )

                # Extract text from response
                analysis_text = response.content[0].text

                # Try to parse as JSON
                try:
                    analysis = json.loads(analysis_text)
                except json.JSONDecodeError:
                    # If not JSON, wrap in a structure
                    analysis = {
                        'summary': analysis_text,
                        'severity': 'medium',
                        'failures': [],
                        'unauthorized_sources': [],
                        'anomalies': [],
                        'recommendations': []
                    }

                logger.info(f"Claude analysis completed for report {report_data.get('report_id')}")
                return analysis

            except RateLimitError:
                wait_time = 2 ** attempt
                logger.warning(f"Rate limit hit, waiting {wait_time}s (attempt {attempt + 1}/{max_retries})")
                if attempt < max_retries - 1:
                    time.sleep(wait_time)
                else:
                    logger.error("Max retries exceeded for Claude API")
                    return None

            except APIError as e:
                logger.error(f"Claude API error: {e}", exc_info=True)
                if attempt == max_retries - 1:
                    return None
                time.sleep(1)

            except Exception as e:
                logger.error(f"Unexpected error during Claude analysis: {e}", exc_info=True)
                return None

        return None

    def _format_prompt(self, report_data: Dict, records_data: list) -> str:
        """
        Format analysis prompt for Claude.

        Args:
            report_data: Report metadata
            records_data: Authentication records

        Returns:
            Formatted prompt string
        """
        # Calculate statistics
        total_emails = sum(r.get('count', 0) for r in records_data)
        spf_failures = sum(r.get('count', 0) for r in records_data if r.get('spf_result') == 'fail')
        dkim_failures = sum(r.get('count', 0) for r in records_data if r.get('dkim_result') == 'fail')
        quarantined = sum(r.get('count', 0) for r in records_data if r.get('disposition') == 'quarantine')
        rejected = sum(r.get('count', 0) for r in records_data if r.get('disposition') == 'reject')

        # Format records for readability
        formatted_records = []
        for r in records_data[:10]:  # Limit to first 10 records to save tokens
            formatted_records.append(
                f"  - IP: {r.get('source_ip')}, Count: {r.get('count')}, "
                f"SPF: {r.get('spf_result')}, DKIM: {r.get('dkim_result')}, "
                f"Disposition: {r.get('disposition')}"
            )

        records_text = '\n'.join(formatted_records)
        if len(records_data) > 10:
            records_text += f"\n  ... and {len(records_data) - 10} more records"

        prompt = f"""You are a DMARC security analyst. Analyze this DMARC report and identify:
1. Authentication failures (SPF/DKIM/DMARC)
2. Unauthorized sending sources
3. Suspicious patterns or anomalies
4. Recommendations for action

Report Summary:
- Domain: {report_data.get('policy_domain', 'N/A')}
- Reporter: {report_data.get('org_name', 'N/A')}
- Total emails: {total_emails}
- SPF failures: {spf_failures}
- DKIM failures: {dkim_failures}
- Quarantined: {quarantined}
- Rejected: {rejected}

Records (top {min(10, len(records_data))} of {len(records_data)}):
{records_text}

Policy:
- DKIM alignment: {report_data.get('policy_adkim', 'N/A')}
- SPF alignment: {report_data.get('policy_aspf', 'N/A')}
- Policy: {report_data.get('policy_p', 'N/A')}

Provide analysis in JSON format:
{{
  "summary": "Brief overview of findings",
  "failures": ["List of authentication failures"],
  "unauthorized_sources": ["List of unauthorized IPs/sources"],
  "anomalies": ["List of suspicious patterns"],
  "severity": "low|medium|high|critical",
  "recommendations": ["Actionable recommendations"]
}}

Focus on actionable insights. If everything looks normal, say so."""

        return prompt

    def calculate_severity(self, analysis: Dict) -> str:
        """
        Calculate alert severity from analysis.

        Args:
            analysis: Claude analysis dictionary

        Returns:
            Severity level ('low', 'medium', 'high', 'critical')
        """
        if not analysis:
            return 'low'

        # Check explicit severity from Claude
        if 'severity' in analysis:
            return analysis['severity']

        # Calculate based on findings
        failure_count = len(analysis.get('failures', []))
        unauthorized_count = len(analysis.get('unauthorized_sources', []))
        anomaly_count = len(analysis.get('anomalies', []))

        total_issues = failure_count + unauthorized_count + anomaly_count

        if total_issues == 0:
            return 'low'
        elif total_issues <= 2:
            return 'medium'
        elif total_issues <= 5:
            return 'high'
        else:
            return 'critical'
