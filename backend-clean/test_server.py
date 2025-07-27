#!/usr/bin/env python3
"""
Quick server test script
"""

try:
    print("Starting server test...")
    
    # Test imports
    print("Testing imports...")
    from fastapi import FastAPI
    print("✓ FastAPI imported successfully")
    
    from app.core.config import settings
    print(f"✓ Settings loaded: {settings.APP_NAME}")
    
    # Try importing our main app
    print("Testing main app import...")
    import main
    print("✓ Main app imported successfully")
    
    print("✓ All imports successful!")
    print(f"Server should be available at: http://0.0.0.0:8000")
    print("Try running: python main.py")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
