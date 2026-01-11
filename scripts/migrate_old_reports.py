#!/usr/bin/env python3
"""
Migration script to clean up old DMARC reports that have JSON code blocks in the summary field.

This script:
1. Finds all reports with ```json in the summary
2. Extracts the actual JSON from the code block
3. Updates the report with the cleaned data

Usage:
    python scripts/migrate_old_reports.py
"""
import sys
import os
import re
import json

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.models.database import db, Report


def migrate_report(report):
    """Migrate a single report to clean up JSON code blocks."""
    if not report.claude_analysis:
        return False, "No analysis data"

    try:
        analysis = json.loads(report.claude_analysis)
    except json.JSONDecodeError:
        return False, "Invalid JSON"

    if 'summary' not in analysis or not isinstance(analysis['summary'], str):
        return False, "No summary field"

    summary = analysis['summary']

    if not summary.startswith('```json'):
        return False, "Already clean"

    # Extract JSON from code block
    json_match = re.search(r'```json\s*(\{.*?\})\s*```', summary, re.DOTALL)
    if not json_match:
        return False, "No JSON match found"

    try:
        # Parse the inner JSON
        inner_data = json.loads(json_match.group(1))

        # Update analysis with inner data (inner takes precedence)
        analysis.update(inner_data)

        # Ensure all required fields exist
        if 'action_items' not in analysis:
            analysis['action_items'] = []
        if 'positive_findings' not in analysis:
            analysis['positive_findings'] = []
        if 'next_steps' not in analysis:
            analysis['next_steps'] = []

        # Save back to database
        report.claude_analysis = json.dumps(analysis)
        db.session.commit()

        return True, f"Migrated successfully. Summary: {analysis['summary'][:50]}..."

    except json.JSONDecodeError as e:
        return False, f"JSON parse error: {e}"
    except Exception as e:
        db.session.rollback()
        return False, f"Error: {e}"


def main():
    """Main migration function."""
    app = create_app()

    with app.app_context():
        # Find all reports
        reports = Report.query.all()

        print(f"Found {len(reports)} total reports")
        print("=" * 60)

        migrated = 0
        skipped = 0
        errors = 0

        for report in reports:
            success, message = migrate_report(report)

            if success:
                print(f"✓ Report {report.id} ({report.domain}): {message}")
                migrated += 1
            else:
                if "Already clean" in message:
                    skipped += 1
                else:
                    print(f"✗ Report {report.id} ({report.domain}): {message}")
                    errors += 1

        print("=" * 60)
        print(f"Migration complete:")
        print(f"  Migrated: {migrated}")
        print(f"  Already clean: {skipped}")
        print(f"  Errors: {errors}")
        print(f"  Total: {len(reports)}")


if __name__ == '__main__':
    main()
