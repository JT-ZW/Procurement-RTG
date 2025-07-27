#!/usr/bin/env python3
"""
Hash generator for passwords
"""
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')

print("Password Hashes:")
print("================")
print(f"password123: {pwd_context.hash('password123')}")
print(f"secret123: {pwd_context.hash('secret123')}")

# Test verification
password123_hash = '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj.vK8NlG.DW'
print(f"\nTesting existing hash:")
print(f"password123 matches existing hash: {pwd_context.verify('password123', password123_hash)}")
print(f"secret123 matches existing hash: {pwd_context.verify('secret123', password123_hash)}")
