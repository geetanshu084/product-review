#!/usr/bin/env python
"""
Setup Verification Script
Checks if all dependencies and configurations are properly set up
"""

import sys
import os


def check_python_version():
    """Check Python version"""
    version = sys.version_info
    if version.major >= 3 and version.minor >= 8:
        print(f"✓ Python version: {version.major}.{version.minor}.{version.micro}")
        return True
    else:
        print(f"✗ Python version {version.major}.{version.minor} is too old. Required: 3.8+")
        return False


def check_dependencies():
    """Check if required packages are installed"""
    required_packages = [
        'requests',
        'bs4',
        'langchain',
        'langchain_google_genai',
        'redis',
        'dotenv',
        'lxml',
        'fastapi',
        'uvicorn'
    ]

    all_installed = True
    for package in required_packages:
        try:
            __import__(package)
            print(f"✓ {package} installed")
        except ImportError:
            print(f"✗ {package} NOT installed")
            all_installed = False

    return all_installed


def check_env_file():
    """Check if .env file exists and has required variables"""
    if not os.path.exists('.env'):
        print("✗ .env file not found")
        print("  Create .env from .env.example and add your Google API key")
        return False

    print("✓ .env file exists")

    # Check for Google API key
    from dotenv import load_dotenv
    load_dotenv()

    api_key = os.getenv('GOOGLE_API_KEY')
    if api_key and api_key != 'your_google_api_key_here':
        print(f"✓ GOOGLE_API_KEY is configured")
        return True
    else:
        print("✗ GOOGLE_API_KEY not configured in .env")
        print("  Get your API key from: https://makersuite.google.com/app/apikey")
        return False


def check_redis():
    """Check if Redis is running"""
    try:
        import redis
        from dotenv import load_dotenv
        load_dotenv()

        redis_host = os.getenv('REDIS_HOST', 'localhost')
        redis_port = int(os.getenv('REDIS_PORT', 6379))

        r = redis.Redis(host=redis_host, port=redis_port, decode_responses=True)
        r.ping()
        print(f"✓ Redis is running on {redis_host}:{redis_port}")
        return True
    except Exception as e:
        print(f"✗ Redis connection failed: {str(e)}")
        print("  Make sure Redis server is running")
        return False


def check_project_structure():
    """Check if all required files and directories exist"""
    required_paths = [
        'requirements.txt',
        '.env.example',
        'README.md',
        'src/scraper.py',
        'src/analyzer.py',
        'src/chatbot.py',
        'config/prompts/product_analysis_prompt.txt',
        'api/main.py',
        'api/routes/products.py'
    ]

    all_exist = True
    for path in required_paths:
        if os.path.exists(path):
            print(f"✓ {path}")
        else:
            print(f"✗ {path} missing")
            all_exist = False

    return all_exist


def main():
    """Run all checks"""
    print("=" * 60)
    print("Amazon Product Analysis Agent - Setup Verification")
    print("=" * 60)
    print()

    print("Checking Python version...")
    python_ok = check_python_version()
    print()

    print("Checking project structure...")
    structure_ok = check_project_structure()
    print()

    print("Checking dependencies...")
    deps_ok = check_dependencies()
    print()

    print("Checking environment configuration...")
    env_ok = check_env_file()
    print()

    print("Checking Redis connection...")
    redis_ok = check_redis()
    print()

    print("=" * 60)
    if all([python_ok, structure_ok, deps_ok, env_ok, redis_ok]):
        print("✓ ALL CHECKS PASSED! You're ready to run the application.")
        print()
        print("Start the FastAPI backend with:")
        print("  python -m api.main")
    else:
        print("✗ SOME CHECKS FAILED. Please fix the issues above.")
        print()
        print("Setup steps:")
        if not deps_ok:
            print("  1. Install dependencies: pip install -r requirements.txt")
        if not env_ok:
            print("  2. Configure .env: cp .env.example .env")
            print("     Then set GOOGLE_API_KEY with your API key")
            print("     Get key from: https://makersuite.google.com/app/apikey")
        if not redis_ok:
            print("  3. Start Redis: redis-server")
            print("     Or: brew services start redis (macOS)")

    print("=" * 60)


if __name__ == "__main__":
    main()
