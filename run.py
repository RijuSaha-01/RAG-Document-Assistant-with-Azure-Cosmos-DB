#!/usr/bin/env python3
"""
Simple runner script for the Document Chat Assistant
"""
import os
import sys
import subprocess
from pathlib import Path

def check_env_file():
    """Check if .env file exists and has required keys"""
    env_file = Path('.env')
    if not env_file.exists():
        print("❌ .env file not found!")
        print("Please create a .env file with your API keys:")
        print("OPENAI_API_KEY=your_openai_key_here")
        print("COSMOS_DB_CONNECTION_STRING=your_cosmos_db_connection_string_here")
        return False
    
    # Check if keys are present
    with open('.env', 'r') as f:
        content = f.read()
        if 'OPENAI_API_KEY=' not in content:
            print("❌ OPENAI_API_KEY not found in .env file")
            return False
        if 'COSMOS_DB_CONNECTION_STRING=' not in content:
            print("❌ COSMOS_DB_CONNECTION_STRING not found in .env file")
            return False
    
    print("✅ Environment file configured")
    return True

def check_dependencies():
    """Check if required packages are installed"""
    try:
        import flask
        import pymongo
        import openai
        import langchain_openai
        print("✅ Dependencies installed")
        return True
    except ImportError as e:
        print(f"❌ Missing dependencies: {e}")
        print("Run: pip install -r requirements.txt")
        return False

def main():
    """Main runner function"""
    print("🚀 Document Chat Assistant with Cosmos DB")
    print("=" * 50)
    
    # Check environment
    if not check_env_file():
        return False
    
    # Check dependencies
    if not check_dependencies():
        return False
    
    # Create Data directory if it doesn't exist
    os.makedirs('Data', exist_ok=True)
    print("✅ Data directory ready")
    
    print("\n🌐 Starting the application...")
    print("Access it at: http://127.0.0.1:5000")
    print("Press Ctrl+C to stop")
    print("-" * 50)
    
    # Run the API
    try:
        subprocess.run([sys.executable, 'api.py'], check=True)
    except KeyboardInterrupt:
        print("\n👋 Application stopped")
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Error running application: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)