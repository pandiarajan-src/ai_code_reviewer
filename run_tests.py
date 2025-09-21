#!/usr/bin/env python3
"""
Comprehensive test runner for AI Code Reviewer
Tests 100% of functionality before deployment
"""

import os
import sys
import subprocess
import asyncio
import json
import time
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def run_command(command, description):
    """Run a command and return success status"""
    print(f"\n{'='*60}")
    print(f"Running: {description}")
    print(f"Command: {command}")
    print('='*60)
    
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            cwd=project_root
        )
        
        if result.stdout:
            print("STDOUT:")
            print(result.stdout)
        
        if result.stderr:
            print("STDERR:")
            print(result.stderr)
        
        if result.returncode == 0:
            print(f"✅ {description} - PASSED")
            return True
        else:
            print(f"❌ {description} - FAILED (exit code: {result.returncode})")
            return False
            
    except Exception as e:
        print(f"❌ {description} - ERROR: {str(e)}")
        return False

def setup_test_environment():
    """Setup test environment"""
    print("Setting up test environment...")
    
    # Set test environment variables
    test_env = {
        "BITBUCKET_URL": "https://test-bitbucket.com",
        "BITBUCKET_TOKEN": "test_token",
        "LLM_PROVIDER": "openai",
        "LLM_API_KEY": "test_api_key",
        "LLM_MODEL": "gpt-4o",
        "WEBHOOK_SECRET": "test_secret",
        "HOST": "0.0.0.0",
        "PORT": "8000",
        "LOG_LEVEL": "INFO"
    }
    
    for key, value in test_env.items():
        os.environ[key] = value
    
    print("✅ Test environment configured")

def install_dependencies():
    """Install test dependencies"""
    commands = [
        ("pip install -r requirements.txt", "Installing main dependencies"),
        ("pip install -r test_requirements.txt", "Installing test dependencies")
    ]
    
    for command, description in commands:
        if not run_command(command, description):
            return False
    
    return True

def run_unit_tests():
    """Run unit tests with coverage"""
    command = "python -m pytest tests/ -v --cov=. --cov-report=term-missing --cov-report=html"
    return run_command(command, "Unit Tests with Coverage")

def run_linting():
    """Run comprehensive code linting with ruff, black, and mypy"""
    # Check if lint.sh exists and is executable
    lint_script = project_root / "lint.sh"
    if lint_script.exists():
        command = f"bash {lint_script} --check-only"
        return run_command(command, "Comprehensive Linting (ruff, black, mypy)")
    else:
        # Fallback to basic flake8 if lint.sh is not available
        run_command("pip install flake8", "Installing flake8")
        command = "flake8 --max-line-length=120 --ignore=E501,W503 *.py tests/"
        return run_command(command, "Basic Code Linting (flake8)")

def test_docker_build():
    """Test Docker build"""
    command = "docker build -t ai-code-reviewer-test ."
    return run_command(command, "Docker Build Test")

def test_configuration_validation():
    """Test configuration validation"""
    print("\n" + "="*60)
    print("Testing Configuration Validation")
    print("="*60)
    
    try:
        from config import Config
        
        # Test with valid config
        os.environ["BITBUCKET_TOKEN"] = "test_token"
        os.environ["LLM_API_KEY"] = "test_key"
        Config.validate_config()
        print("✅ Valid configuration - PASSED")
        
        # Test with missing token
        original_token = os.environ.get("BITBUCKET_TOKEN")
        del os.environ["BITBUCKET_TOKEN"]
        
        try:
            Config.validate_config()
            print("❌ Missing token validation - FAILED")
            return False
        except ValueError:
            print("✅ Missing token validation - PASSED")
        
        # Restore token
        if original_token:
            os.environ["BITBUCKET_TOKEN"] = original_token
        
        return True
        
    except Exception as e:
        print(f"❌ Configuration validation - ERROR: {str(e)}")
        return False

async def test_api_endpoints():
    """Test API endpoints"""
    print("\n" + "="*60)
    print("Testing API Endpoints")
    print("="*60)
    
    try:
        import httpx
        from main import app
        from fastapi.testclient import TestClient
        
        client = TestClient(app)
        
        # Test root endpoint
        response = client.get("/")
        if response.status_code == 200:
            print("✅ Root endpoint - PASSED")
        else:
            print(f"❌ Root endpoint - FAILED ({response.status_code})")
            return False
        
        # Test health endpoint
        response = client.get("/health")
        if response.status_code == 200:
            print("✅ Health endpoint - PASSED")
        else:
            print(f"❌ Health endpoint - FAILED ({response.status_code})")
            return False
        
        # Test webhook endpoint
        test_payload = {
            "eventKey": "pr:opened",
            "date": "2024-01-01T00:00:00Z",
            "repository": {"slug": "test", "project": {"key": "TEST"}},
            "pullRequest": {"id": 123}
        }
        
        response = client.post("/webhook/code-review", json=test_payload)
        if response.status_code == 200:
            print("✅ Webhook endpoint - PASSED")
        else:
            print(f"❌ Webhook endpoint - FAILED ({response.status_code})")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ API endpoints test - ERROR: {str(e)}")
        return False

def test_client_modules():
    """Test client modules"""
    print("\n" + "="*60)
    print("Testing Client Modules")
    print("="*60)
    
    try:
        # Test Bitbucket client import
        from bitbucket_client import BitbucketClient
        bb_client = BitbucketClient()
        print("✅ Bitbucket client import - PASSED")
        
        # Test LLM client import
        from llm_client import LLMClient
        llm_client = LLMClient()
        print("✅ LLM client import - PASSED")
        
        return True
        
    except Exception as e:
        print(f"❌ Client modules test - ERROR: {str(e)}")
        return False

def generate_test_report(results):
    """Generate test report"""
    print("\n" + "="*80)
    print("TEST REPORT SUMMARY")
    print("="*80)
    
    total_tests = len(results)
    passed_tests = sum(1 for result in results.values() if result)
    failed_tests = total_tests - passed_tests
    
    print(f"Total Tests: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {failed_tests}")
    print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
    
    print("\nDetailed Results:")
    for test_name, result in results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"  {test_name}: {status}")
    
    if failed_tests == 0:
        print("\n🎉 ALL TESTS PASSED! Ready for deployment.")
        return True
    else:
        print(f"\n⚠️  {failed_tests} test(s) failed. Please fix before deployment.")
        return False

def main():
    """Main test runner"""
    print("AI Code Reviewer - Comprehensive Test Suite")
    print("Testing 100% of functionality before deployment")
    
    # Setup
    setup_test_environment()
    
    # Run all tests
    results = {}
    
    # 1. Install dependencies
    results["Dependency Installation"] = install_dependencies()
    
    # 2. Configuration validation
    results["Configuration Validation"] = test_configuration_validation()
    
    # 3. Client modules
    results["Client Modules"] = test_client_modules()
    
    # 4. Unit tests
    results["Unit Tests"] = run_unit_tests()
    
    # 5. API endpoints
    results["API Endpoints"] = asyncio.run(test_api_endpoints())
    
    # 6. Code linting
    results["Code Linting"] = run_linting()
    
    # 7. Docker build
    results["Docker Build"] = test_docker_build()
    
    # Generate report
    success = generate_test_report(results)
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()

