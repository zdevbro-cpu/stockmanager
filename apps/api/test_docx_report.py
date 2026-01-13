"""
Test DOCX report generation
"""
import sys
sys.path.insert(0, 'c:\\ProjectCode\\stockmanager\\apps\\api')

from app.services.report_service import generate_ai_report

# Test with Samsung Electronics (company_id=5582, assuming from previous tests)
print("Testing DOCX report generation...")
generate_ai_report(company_id=5582, report_id=200)
print("\nDone! Check artifacts/reports/report_200.docx")
