"""
Test script for file upload and extraction functionality
"""
import requests
import io
import json
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
import pandas as pd

def create_test_pdf():
    """Create a test PDF with PII data"""
    print("📄 Creating test PDF with PII...")
    
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    
    # Add content with PII
    p.drawString(100, 750, "CONFIDENTIAL EMPLOYEE REPORT")
    p.drawString(100, 720, "Employee Name: Alice Johnson")
    p.drawString(100, 700, "Email: alice.johnson@company.com")
    p.drawString(100, 680, "Phone: (555) 987-6543")
    p.drawString(100, 660, "SSN: 123-45-6789")
    p.drawString(100, 640, "Address: 123 Main St, New York, NY 10001")
    p.drawString(100, 620, "Department: Human Resources")
    p.drawString(100, 600, "Manager: Dr. Robert Smith (robert.smith@company.com)")
    p.drawString(100, 580, "Salary: $75,000")
    p.drawString(100, 560, "Start Date: January 15, 2023")
    
    p.save()
    buffer.seek(0)
    return buffer.getvalue()

def create_test_excel():
    """Create a test Excel file with PII data"""
    print("📊 Creating test Excel with PII...")
    
    data = {
        'Employee_ID': [1001, 1002, 1003, 1004],
        'Full_Name': ['John Doe', 'Jane Smith', 'Michael Brown', 'Sarah Wilson'],
        'Email': ['john.doe@corp.com', 'jane.smith@corp.com', 'michael.brown@corp.com', 'sarah.wilson@corp.com'],
        'Phone': ['555-123-4567', '555-234-5678', '555-345-6789', '555-456-7890'],
        'SSN': ['123-45-6789', '234-56-7890', '345-67-8901', '456-78-9012'],
        'Department': ['Engineering', 'Marketing', 'Finance', 'HR'],
        'Salary': [85000, 65000, 75000, 70000]
    }
    
    df = pd.DataFrame(data)
    buffer = io.BytesIO()
    df.to_excel(buffer, index=False, engine='openpyxl')
    buffer.seek(0)
    return buffer.getvalue()

def create_test_csv():
    """Create a test CSV file with PII data"""
    print("📋 Creating test CSV with PII...")
    
    csv_content = """Name,Email,Phone,Credit_Card,Address
Dr. Emily Davis,emily.davis@hospital.org,555-111-2222,4532-1234-5678-9012,"456 Oak Ave, Boston, MA"
Prof. David Lee,david.lee@university.edu,555-333-4444,5555-6666-7777-8888,"789 Pine St, Chicago, IL"
Ms. Lisa Chen,lisa.chen@startup.io,555-555-6666,4111-1111-1111-1111,"321 Elm Dr, Austin, TX"
"""
    return csv_content.encode('utf-8')

def test_pdf_upload():
    """Test PDF file upload and PII extraction"""
    print("\n🧪 Testing PDF Upload and PII Extraction...")
    
    try:
        pdf_content = create_test_pdf()
        
        files = {
            'file': ('employee_report.pdf', io.BytesIO(pdf_content), 'application/pdf')
        }
        
        # Simulate file upload to OpenAI Files API
        response = requests.post(
            "http://localhost:8000/v1/files",
            headers={
                "Host": "api.openai.com",
                "Authorization": "Bearer test-key"
            },
            files=files,
            timeout=15
        )
        
        print(f"✅ PDF Upload Status: {response.status_code}")
        
        if response.status_code == 502:
            print("ℹ️  Expected 502 - No real API, but PDF extraction and PII redaction should have occurred")
        else:
            print(f"📄 Response: {response.text[:200]}...")
            
    except Exception as e:
        print(f"❌ PDF upload test failed: {e}")

def test_excel_upload():
    """Test Excel file upload and PII extraction"""
    print("\n🧪 Testing Excel Upload and PII Extraction...")
    
    try:
        excel_content = create_test_excel()
        
        files = {
            'file': ('employees.xlsx', io.BytesIO(excel_content), 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        }
        
        response = requests.post(
            "http://localhost:8000/v1/files",
            headers={
                "Host": "api.openai.com",
                "Authorization": "Bearer test-key"
            },
            files=files,
            timeout=15
        )
        
        print(f"✅ Excel Upload Status: {response.status_code}")
        
        if response.status_code == 502:
            print("ℹ️  Expected 502 - No real API, but Excel extraction and PII redaction should have occurred")
        else:
            print(f"📄 Response: {response.text[:200]}...")
            
    except Exception as e:
        print(f"❌ Excel upload test failed: {e}")

def test_csv_upload():
    """Test CSV file upload and PII extraction"""
    print("\n🧪 Testing CSV Upload and PII Extraction...")
    
    try:
        csv_content = create_test_csv()
        
        files = {
            'file': ('contacts.csv', io.BytesIO(csv_content), 'text/csv')
        }
        
        response = requests.post(
            "http://localhost:8000/v1/files",
            headers={
                "Host": "api.openai.com",
                "Authorization": "Bearer test-key"
            },
            files=files,
            timeout=15
        )
        
        print(f"✅ CSV Upload Status: {response.status_code}")
        
        if response.status_code == 502:
            print("ℹ️  Expected 502 - No real API, but CSV extraction and PII redaction should have occurred")
        else:
            print(f"📄 Response: {response.text[:200]}...")
            
    except Exception as e:
        print(f"❌ CSV upload test failed: {e}")

def test_multipart_form_with_text():
    """Test multipart form with both file and text data"""
    print("\n🧪 Testing Multipart Form with Mixed Data...")
    
    try:
        # Create form data with both file and text
        files = {
            'file': ('document.txt', io.BytesIO(b"Employee: John Smith\nEmail: john.smith@company.com\nPhone: 555-999-8888"), 'text/plain'),
            'purpose': (None, 'fine-tune'),
            'model': (None, 'gpt-3.5-turbo'),
            'instructions': (None, 'Process this employee data for Sarah Johnson (sarah.j@corp.com)')
        }
        
        response = requests.post(
            "http://localhost:8000/v1/fine_tuning/jobs",
            headers={
                "Host": "api.openai.com",
                "Authorization": "Bearer test-key"
            },
            files=files,
            timeout=15
        )
        
        print(f"✅ Multipart Form Status: {response.status_code}")
        
        if response.status_code == 502:
            print("ℹ️  Expected 502 - No real API, but multipart PII redaction should have occurred")
        else:
            print(f"📄 Response: {response.text[:200]}...")
            
    except Exception as e:
        print(f"❌ Multipart form test failed: {e}")

def main():
    """Run all file upload tests"""
    print("📁 Starting File Upload and Extraction Tests")
    print("=" * 50)
    
    # Check if required libraries are available
    try:
        import reportlab
        import openpyxl
        print("✅ Required libraries available")
    except ImportError as e:
        print(f"❌ Missing required library: {e}")
        print("💡 Install with: pip install reportlab openpyxl")
        return
    
    # Run file upload tests
    test_pdf_upload()
    test_excel_upload()
    test_csv_upload()
    test_multipart_form_with_text()
    
    print("\n" + "=" * 50)
    print("🎯 File upload tests completed!")
    print("📊 Check the dashboard for PII blocking statistics")
    print("📝 Check proxy logs for file extraction details")
    print("\n💡 Expected behavior:")
    print("   - Files should be extracted and scanned for PII")
    print("   - Names, emails, phones, SSNs should be redacted")
    print("   - Redacted content should be forwarded to AI APIs")
    print("   - Dashboard should show increased PII blocking count")

if __name__ == "__main__":
    main()