"""
Comprehensive API and Database Test Suite
Tests the complete procurement system functionality with Supabase
"""

import asyncio
import logging
import sys
from pathlib import Path
from typing import Dict, Any
import httpx
import json
from datetime import datetime

# Add the parent directory to the path
sys.path.append(str(Path(__file__).parent.parent))

from app.core.database import AsyncSessionLocal
from app.core.config import settings
from sqlalchemy import text

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ProcurementSystemTester:
    """Complete test suite for the procurement system."""
    
    def __init__(self, base_url: str = "http://localhost:8001"):
        self.base_url = base_url
        self.session = None
        self.auth_token = None
        self.test_results = {}
    
    async def __aenter__(self):
        self.session = httpx.AsyncClient(timeout=30.0)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.aclose()
    
    def log_test_result(self, test_name: str, success: bool, message: str = ""):
        """Log test results."""
        self.test_results[test_name] = {
            'success': success,
            'message': message,
            'timestamp': datetime.now().isoformat()
        }
        
        status = "✅ PASS" if success else "❌ FAIL"
        logger.info(f"{status} - {test_name}: {message}")
    
    async def test_database_connection(self):
        """Test direct database connection."""
        try:
            async with AsyncSessionLocal() as db:
                result = await db.execute(text("SELECT COUNT(*) FROM users"))
                user_count = result.scalar()
                
                result = await db.execute(text("SELECT COUNT(*) FROM units"))
                unit_count = result.scalar()
                
                result = await db.execute(text("SELECT COUNT(*) FROM products"))
                product_count = result.scalar()
                
                self.log_test_result(
                    "Database Connection", 
                    True, 
                    f"Connected successfully. Users: {user_count}, Units: {unit_count}, Products: {product_count}"
                )
                return True
                
        except Exception as e:
            self.log_test_result("Database Connection", False, str(e))
            return False
    
    async def test_api_health(self):
        """Test API health endpoint."""
        try:
            response = await self.session.get(f"{self.base_url}/health")
            if response.status_code == 200:
                data = response.json()
                self.log_test_result(
                    "API Health Check", 
                    True, 
                    f"API is healthy. Status: {data.get('status', 'unknown')}"
                )
                return True
            else:
                self.log_test_result(
                    "API Health Check", 
                    False, 
                    f"API returned status code: {response.status_code}"
                )
                return False
                
        except Exception as e:
            self.log_test_result("API Health Check", False, str(e))
            return False
    
    async def test_user_authentication(self):
        """Test user login functionality."""
        try:
            # Test login with sample user
            login_data = {
                "username": "admin@hotel.com",  # Using email as username
                "password": "password123"
            }
            
            response = await self.session.post(
                f"{self.base_url}/api/v1/auth/login",
                data=login_data,
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            
            if response.status_code == 200:
                data = response.json()
                self.auth_token = data.get("access_token")
                
                self.log_test_result(
                    "User Authentication", 
                    True, 
                    f"Login successful. Token type: {data.get('token_type')}"
                )
                return True
            else:
                self.log_test_result(
                    "User Authentication", 
                    False, 
                    f"Login failed with status: {response.status_code}. Response: {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_test_result("User Authentication", False, str(e))
            return False
    
    async def test_protected_endpoints(self):
        """Test protected API endpoints."""
        if not self.auth_token:
            self.log_test_result("Protected Endpoints", False, "No auth token available")
            return False
        
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        
        endpoints_to_test = [
            ("/api/v1/users/me", "Get Current User"),
            ("/api/v1/units/", "Get Units"),
            ("/api/v1/products/", "Get Products"),
            ("/api/v1/requisitions/", "Get Requisitions")
        ]
        
        all_passed = True
        
        for endpoint, description in endpoints_to_test:
            try:
                response = await self.session.get(f"{self.base_url}{endpoint}", headers=headers)
                
                if response.status_code == 200:
                    data = response.json()
                    self.log_test_result(
                        f"Protected Endpoint - {description}", 
                        True, 
                        f"Retrieved data successfully"
                    )
                else:
                    self.log_test_result(
                        f"Protected Endpoint - {description}", 
                        False, 
                        f"Status: {response.status_code}"
                    )
                    all_passed = False
                    
            except Exception as e:
                self.log_test_result(f"Protected Endpoint - {description}", False, str(e))
                all_passed = False
        
        return all_passed
    
    async def test_crud_operations(self):
        """Test CRUD operations on key entities."""
        if not self.auth_token:
            self.log_test_result("CRUD Operations", False, "No auth token available")
            return False
        
        headers = {
            "Authorization": f"Bearer {self.auth_token}",
            "Content-Type": "application/json"
        }
        
        try:
            # Test creating a new unit
            unit_data = {
                "name": "Test Hotel API",
                "code": "TEST001",
                "description": "Test hotel created via API",
                "city": "Test City",
                "country": "Test Country"
            }
            
            response = await self.session.post(
                f"{self.base_url}/api/v1/units/",
                json=unit_data,
                headers=headers
            )
            
            if response.status_code in [200, 201]:
                created_unit = response.json()
                unit_id = created_unit.get("id")
                
                self.log_test_result(
                    "CRUD - Create Unit", 
                    True, 
                    f"Unit created with ID: {unit_id}"
                )
                
                # Test retrieving the created unit
                response = await self.session.get(
                    f"{self.base_url}/api/v1/units/{unit_id}",
                    headers=headers
                )
                
                if response.status_code == 200:
                    self.log_test_result(
                        "CRUD - Read Unit", 
                        True, 
                        "Unit retrieved successfully"
                    )
                else:
                    self.log_test_result(
                        "CRUD - Read Unit", 
                        False, 
                        f"Failed to retrieve unit: {response.status_code}"
                    )
                
                return True
            else:
                self.log_test_result(
                    "CRUD - Create Unit", 
                    False, 
                    f"Failed to create unit: {response.status_code}. Response: {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_test_result("CRUD Operations", False, str(e))
            return False
    
    async def test_database_views(self):
        """Test the database views we created."""
        try:
            async with AsyncSessionLocal() as db:
                # Test user dashboard view
                result = await db.execute(text("SELECT * FROM user_dashboard LIMIT 5"))
                dashboard_data = result.fetchall()
                
                # Test requisition summary view
                result = await db.execute(text("SELECT * FROM requisition_summary LIMIT 5"))
                requisition_data = result.fetchall()
                
                # Test supplier performance view
                result = await db.execute(text("SELECT * FROM supplier_performance LIMIT 5"))
                supplier_data = result.fetchall()
                
                self.log_test_result(
                    "Database Views", 
                    True, 
                    f"Views working. Dashboard: {len(dashboard_data)}, Requisitions: {len(requisition_data)}, Suppliers: {len(supplier_data)}"
                )
                return True
                
        except Exception as e:
            self.log_test_result("Database Views", False, str(e))
            return False
    
    async def generate_test_report(self):
        """Generate a comprehensive test report."""
        logger.info("\n" + "="*60)
        logger.info("PROCUREMENT SYSTEM TEST REPORT")
        logger.info("="*60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results.values() if result['success'])
        failed_tests = total_tests - passed_tests
        
        logger.info(f"Total Tests: {total_tests}")
        logger.info(f"Passed: {passed_tests}")
        logger.info(f"Failed: {failed_tests}")
        logger.info(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        logger.info("\nDETAILED RESULTS:")
        logger.info("-" * 40)
        
        for test_name, result in self.test_results.items():
            status = "✅ PASS" if result['success'] else "❌ FAIL"
            logger.info(f"{status} {test_name}")
            if result['message']:
                logger.info(f"    {result['message']}")
        
        logger.info("\n" + "="*60)
        
        if failed_tests == 0:
            logger.info("🎉 ALL TESTS PASSED! Your procurement system is working perfectly!")
        else:
            logger.info(f"⚠️  {failed_tests} test(s) failed. Please check the issues above.")
        
        logger.info("="*60)
        
        return failed_tests == 0

async def main():
    """Run the complete test suite."""
    logger.info("🚀 Starting Procurement System Test Suite")
    logger.info(f"Testing against: {settings.DATABASE_URL.split('@')[0]}@***")
    
    async with ProcurementSystemTester() as tester:
        # Run all tests
        await tester.test_database_connection()
        await tester.test_api_health()
        await tester.test_user_authentication()
        await tester.test_protected_endpoints()
        await tester.test_crud_operations()
        await tester.test_database_views()
        
        # Generate report
        success = await tester.generate_test_report()
        
        if success:
            logger.info("\n🎯 Next Steps:")
            logger.info("1. Your backend API is working correctly")
            logger.info("2. Database connection to Supabase is successful")
            logger.info("3. Sample data is available for testing")
            logger.info("4. You can now connect your frontend!")
            logger.info("\n📋 Test Credentials:")
            logger.info("Email: admin@hotel.com")
            logger.info("Password: password123")
        else:
            logger.error("\n❌ Some tests failed. Please fix the issues before proceeding.")
            sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
