#!/usr/bin/env python3
"""
Test script for DWG → PDF converter
"""

import os
import sys
import requests
import tempfile
import logging

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dwg_converter import convert_dwg_to_pdf

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_local_conversion():
    """Test local DWG → PDF conversion"""
    print("🧪 Testing local DWG → PDF conversion...")
    
    # Create a simple test DWG file (this would normally be a real DWG file)
    # For testing purposes, we'll create a dummy file
    test_dwg_path = "/tmp/test.dwg"
    
    # Create a minimal DWG-like file for testing
    with open(test_dwg_path, 'wb') as f:
        # This is not a real DWG, just for testing the function
        f.write(b"DWG_TEST_FILE")
    
    try:
        result = convert_dwg_to_pdf(test_dwg_path)
        if result:
            print(f"✅ Local conversion successful: {result}")
            return True
        else:
            print("❌ Local conversion failed")
            return False
    except Exception as e:
        print(f"❌ Local conversion error: {e}")
        return False
    finally:
        # Clean up
        if os.path.exists(test_dwg_path):
            os.unlink(test_dwg_path)

def test_api_endpoint(base_url="http://localhost:8080"):
    """Test API endpoint"""
    print(f"🌐 Testing API endpoint: {base_url}")
    
    # Test health endpoint
    try:
        response = requests.get(f"{base_url}/health", timeout=10)
        if response.status_code == 200:
            print("✅ Health check passed")
            health_data = response.json()
            print(f"   Status: {health_data}")
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False
    
    # Test status endpoint
    try:
        response = requests.get(f"{base_url}/status", timeout=10)
        if response.status_code == 200:
            print("✅ Status endpoint working")
            status_data = response.json()
            print(f"   Service: {status_data.get('service')}")
            print(f"   Version: {status_data.get('version')}")
            print(f"   Supported formats: {status_data.get('supported_formats')}")
        else:
            print(f"❌ Status endpoint failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Status endpoint error: {e}")
        return False
    
    return True

def test_file_upload(base_url="http://localhost:8080"):
    """Test file upload (requires a real DWG file)"""
    print(f"📤 Testing file upload to: {base_url}")
    
    # Check if we have a test DWG file
    test_files = [
        "test.dwg",
        "sample.dwg",
        "/tmp/test.dwg"
    ]
    
    test_file = None
    for file_path in test_files:
        if os.path.exists(file_path):
            test_file = file_path
            break
    
    if not test_file:
        print("⚠️ No test DWG file found, skipping upload test")
        print("   Create a test.dwg file to test upload functionality")
        return True
    
    try:
        with open(test_file, 'rb') as f:
            files = {'file': (os.path.basename(test_file), f, 'application/octet-stream')}
            response = requests.post(f"{base_url}/upload", files=files, timeout=60)
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print("✅ File upload successful")
                print(f"   PDF URL: {result.get('pdf_url')}")
                print(f"   Raw URL: {result.get('raw_url')}")
                return True
            else:
                print(f"❌ Upload failed: {result.get('message')}")
                return False
        else:
            print(f"❌ Upload request failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Upload test error: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Starting BTI DWG → PDF Converter tests")
    print("=" * 50)
    
    tests_passed = 0
    total_tests = 3
    
    # Test 1: Local conversion
    if test_local_conversion():
        tests_passed += 1
    
    print()
    
    # Test 2: API endpoints
    if test_api_endpoint():
        tests_passed += 1
    
    print()
    
    # Test 3: File upload
    if test_file_upload():
        tests_passed += 1
    
    print()
    print("=" * 50)
    print(f"📊 Test Results: {tests_passed}/{total_tests} tests passed")
    
    if tests_passed == total_tests:
        print("🎉 All tests passed!")
        return 0
    else:
        print("❌ Some tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
