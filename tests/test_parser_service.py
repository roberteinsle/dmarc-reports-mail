"""
Tests for DMARC Parser Service.
"""
import pytest
from app.services.parser_service import DMARCParserService


def test_parse_valid_dmarc_xml():
    """Test parsing a valid DMARC XML report."""
    with open('tests/fixtures/sample_dmarc_report.xml', 'r') as f:
        xml_content = f.read()

    result = DMARCParserService.parse_dmarc_xml(xml_content)

    assert result is not None
    assert result['org_name'] == 'google.com'
    assert result['policy_domain'] == 'einsle.cloud'
    assert result['report_id'] == '12345678901234567890'
    assert len(result['records']) == 1
    assert result['records'][0]['source_ip'] == '209.85.220.41'
    assert result['records'][0]['count'] == 2
    assert result['records'][0]['spf_result'] == 'pass'
    assert result['records'][0]['dkim_result'] == 'pass'


def test_parse_invalid_xml():
    """Test parsing invalid XML."""
    invalid_xml = '<invalid>xml</invalid>'

    result = DMARCParserService.parse_dmarc_xml(invalid_xml)

    assert result is None


def test_validate_xml_structure():
    """Test XML structure validation."""
    with open('tests/fixtures/sample_dmarc_report.xml', 'r') as f:
        xml_content = f.read()

    assert DMARCParserService.validate_xml_structure(xml_content) is True

    invalid_xml = '<feedback><invalid></invalid></feedback>'
    assert DMARCParserService.validate_xml_structure(invalid_xml) is False
