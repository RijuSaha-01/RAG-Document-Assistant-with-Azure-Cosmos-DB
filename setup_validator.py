#!/usr/bin/env python3
"""
Project Setup Validation Script
===============================

This script validates that the Document Chat Assistant is properly configured
and ready to run. It checks dependencies, environment configuration, and
project structure to ensure everything is set up correctly.

Usage: python validate_fixes.py
"""

import os
import sys
import json
from pathlib import Path

def validate_syntax():
    """Check if all Python files have valid syntax"""
    print("🔍 Validating Python syntax...")
    
    python_files = [
        'run.py', 'api.py', 'cosmos_chatbot.py', 
        'cosmos_db_manager.py', 'document_processor.py', 
        'presentation_generator.py'
    ]
    
    for file in python_files:
        if os.path.exists(file):
            try:
                with open(file, 'r', encoding='utf-8') as f:
                    compile(f.read(), file, 'exec')
                print(f"  ✅ {file} - Syntax OK")
            except SyntaxError as e:
                print(f"  ❌ {file} - Syntax Error: {e}")
                return False
        else:
            print(f"  ⚠️  {file} - File not found")
    
    return True

def validate_imports():
    """Check if critical imports are available"""
    print("\n🔍 Validating critical imports...")
    
    try:
        import flask
        print("  ✅ Flask - Available")
    except ImportError:
        print("  ❌ Flask - Missing")
        return False
    
    try:
        import pymongo
        print("  ✅ PyMongo - Available")
    except ImportError:
        print("  ❌ PyMongo - Missing")
        return False
    
    try:
        import openai
        print("  ✅ OpenAI - Available")
    except ImportError:
        print("  ❌ OpenAI - Missing")
        return False
    
    try:
        from langchain_openai import OpenAIEmbeddings
        print("  ✅ LangChain OpenAI - Available")
    except ImportError:
        print("  ❌ LangChain OpenAI - Missing")
        return False
    
    return True

def validate_env_file():
    """Check if .env file is properly configured"""
    print("\n🔍 Validating environment configuration...")
    
    if not os.path.exists('.env'):
        print("  ❌ .env file not found")
        return False
    
    with open('.env', 'r') as f:
        content = f.read()
    
    if 'OPENAI_API_KEY=' in content:
        print("  ✅ OPENAI_API_KEY - Configured")
    else:
        print("  ❌ OPENAI_API_KEY - Missing")
        return False
    
    if 'COSMOS_DB_CONNECTION_STRING=' in content:
        print("  ✅ COSMOS_DB_CONNECTION_STRING - Configured")
    else:
        print("  ❌ COSMOS_DB_CONNECTION_STRING - Missing")
        return False
    
    return True

def validate_directory_structure():
    """Check if required directories exist"""
    print("\n🔍 Validating directory structure...")
    
    required_dirs = ['Data', 'static']
    for dir_name in required_dirs:
        if os.path.exists(dir_name):
            print(f"  ✅ {dir_name}/ - Exists")
        else:
            print(f"  ⚠️  {dir_name}/ - Missing (will be created)")
            os.makedirs(dir_name, exist_ok=True)
    
    # Check for generated_presentations subdirectory
    presentations_dir = os.path.join('Data', 'generated_presentations')
    if os.path.exists(presentations_dir):
        print(f"  ✅ Data/generated_presentations/ - Exists")
    else:
        print(f"  ⚠️  Data/generated_presentations/ - Missing (will be created)")
        os.makedirs(presentations_dir, exist_ok=True)
    
    return True

def main():
    """Run all validations and provide setup status"""
    print("🚀 Document Chat Assistant - Setup Validation")
    print("=" * 60)
    
    all_passed = True
    
    # Run all validation checks
    all_passed &= validate_syntax()
    all_passed &= validate_imports()
    all_passed &= validate_env_file()
    all_passed &= validate_directory_structure()
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✅ All validations passed! The application is ready to run.")
        print("\n🎯 Next steps:")
        print("  • Run the application: python run.py")
        print("  • Access web interface: http://127.0.0.1:5000")
        print("  • Upload documents and start chatting!")
        print("  • Check system health: http://127.0.0.1:5000/health")
        print("\n📚 For help, see README.md or run: python run.py --help")
    else:
        print("❌ Some validations failed. Please fix the issues above.")
        print("\n🔧 Common solutions:")
        print("  • Install dependencies: pip install -r requirements.txt")
        print("  • Configure .env file with your API keys")
        print("  • Check README.md for detailed setup instructions")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())