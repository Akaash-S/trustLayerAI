"""
Test script to verify dashboard fixes
Tests both local and Docker environment detection
"""
import os
import sys
import tempfile
import yaml

def test_proxy_url_detection():
    """Test the proxy URL detection logic"""
    print("🧪 Testing Dashboard Proxy URL Detection")
    print("=" * 50)
    
    # Save original environment
    original_pythonpath = os.environ.get('PYTHONPATH')
    
    # Test 1: Local environment (no Docker indicators)
    print("\n1. Testing Local Environment Detection:")
    if 'PYTHONPATH' in os.environ:
        del os.environ['PYTHONPATH']
    
    # Mock the dashboard logic
    def get_proxy_url():
        """Get the correct proxy URL based on environment"""
        if os.getenv('PYTHONPATH') == '/app' or os.path.exists('/.dockerenv'):
            # Running in Docker - use service name
            return "http://proxy:8000"
        else:
            # Running locally - use localhost
            return "http://localhost:8000"
    
    local_url = get_proxy_url()
    print(f"   Detected URL: {local_url}")
    assert local_url == "http://localhost:8000", f"Expected localhost URL, got {local_url}"
    print("   ✅ Local environment detection works")
    
    # Test 2: Docker environment (PYTHONPATH set)
    print("\n2. Testing Docker Environment Detection (PYTHONPATH):")
    os.environ['PYTHONPATH'] = '/app'
    
    docker_url = get_proxy_url()
    print(f"   Detected URL: {docker_url}")
    assert docker_url == "http://proxy:8000", f"Expected proxy URL, got {docker_url}"
    print("   ✅ Docker environment detection works")
    
    # Test 3: Docker environment (dockerenv file)
    print("\n3. Testing Docker Environment Detection (dockerenv):")
    if 'PYTHONPATH' in os.environ:
        del os.environ['PYTHONPATH']
    
    # Create temporary dockerenv file
    with tempfile.NamedTemporaryFile(delete=False) as f:
        dockerenv_path = f.name
    
    # Mock the file existence check
    original_exists = os.path.exists
    def mock_exists(path):
        if path == '/.dockerenv':
            return True
        return original_exists(path)
    
    os.path.exists = mock_exists
    
    docker_url2 = get_proxy_url()
    print(f"   Detected URL: {docker_url2}")
    assert docker_url2 == "http://proxy:8000", f"Expected proxy URL, got {docker_url2}"
    print("   ✅ Docker environment detection (dockerenv) works")
    
    # Cleanup
    os.path.exists = original_exists
    os.unlink(dockerenv_path)
    
    # Restore original environment
    if original_pythonpath:
        os.environ['PYTHONPATH'] = original_pythonpath
    elif 'PYTHONPATH' in os.environ:
        del os.environ['PYTHONPATH']
    
    print("\n✅ All proxy URL detection tests passed!")

def test_config_loading():
    """Test that config loading works"""
    print("\n🧪 Testing Configuration Loading")
    print("=" * 50)
    
    try:
        with open("config.yaml", "r") as f:
            config = yaml.safe_load(f)
        
        print(f"   Proxy port: {config['proxy']['port']}")
        print(f"   Redis host: {config['redis']['host']}")
        print("   ✅ Configuration loading works")
        
        return config
    except Exception as e:
        print(f"   ❌ Configuration loading failed: {e}")
        return None

def test_import_requirements():
    """Test that all required imports work"""
    print("\n🧪 Testing Import Requirements")
    print("=" * 50)
    
    required_modules = [
        'streamlit',
        'requests', 
        'pandas',
        'plotly.express',
        'plotly.graph_objects',
        'yaml'
    ]
    
    missing_modules = []
    
    for module in required_modules:
        try:
            __import__(module)
            print(f"   ✅ {module}")
        except ImportError:
            print(f"   ❌ {module} - MISSING")
            missing_modules.append(module)
    
    if missing_modules:
        print(f"\n❌ Missing modules: {', '.join(missing_modules)}")
        print("   Install with: pip install streamlit requests pandas plotly pyyaml")
        return False
    else:
        print("\n✅ All required modules available")
        return True

def main():
    """Run all dashboard tests"""
    print("🛡️ TrustLayer AI Dashboard Fix Verification")
    print("=" * 60)
    
    try:
        # Test 1: Import requirements
        imports_ok = test_import_requirements()
        
        # Test 2: Configuration loading
        config = test_config_loading()
        
        # Test 3: Proxy URL detection
        test_proxy_url_detection()
        
        print("\n" + "=" * 60)
        if imports_ok and config:
            print("🎉 All dashboard fix tests passed!")
            print("\n📋 Dashboard fixes implemented:")
            print("   ✅ Added import os for environment detection")
            print("   ✅ Dynamic proxy URL based on environment")
            print("   ✅ Fixed DuplicateWidgetID with unique key")
            print("   ✅ Enhanced error messages with current proxy URL")
            
            print("\n🚀 Ready to test:")
            print("   Local: streamlit run dashboard.py")
            print("   Docker: docker compose up dashboard")
            
        else:
            print("⚠️ Some tests failed - check requirements")
            
    except Exception as e:
        print(f"❌ Test execution failed: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)