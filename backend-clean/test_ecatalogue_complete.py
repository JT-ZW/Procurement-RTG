#!/usr/bin/env python3
"""
E-catalogue Module 1 Testing Script
Comprehensive testing of the enhanced product management system
"""

import asyncio
import requests
import json
import sys
from datetime import datetime, date

# Configuration
BASE_URL = "http://localhost:8001"
API_BASE = f"{BASE_URL}/api/v1"

class ECatalogueTestSuite:
    def __init__(self):
        self.token = None
        self.test_results = []
        self.test_data = {}
        
    def log_test(self, test_name, passed, details=""):
        """Log test results"""
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} {test_name}")
        if details:
            print(f"   📝 {details}")
        
        self.test_results.append({
            "test": test_name,
            "passed": passed,
            "details": details
        })
    
    def authenticate(self):
        """Authenticate and get token"""
        print("\n🔐 AUTHENTICATION")
        print("=" * 50)
        
        try:
            response = requests.post(f"{API_BASE}/auth/login", data={
                "username": "admin@hotel.com",
                "password": "password123"
            })
            
            if response.status_code == 200:
                data = response.json()
                self.token = data.get("access_token")
                self.log_test("Admin Authentication", True, f"Token obtained")
                return True
            else:
                self.log_test("Admin Authentication", False, f"Status: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Admin Authentication", False, str(e))
            return False
    
    def test_database_migration(self):
        """Test if database migration was successful"""
        print("\n🗄️ DATABASE MIGRATION VERIFICATION")
        print("=" * 50)
        
        headers = {"Authorization": f"Bearer {self.token}"}
        
        try:
            # Test the E-catalogue endpoint
            response = requests.get(f"{API_BASE}/products/e-catalogue/", headers=headers)
            if response.status_code == 200:
                self.log_test("E-catalogue Endpoint", True, "Endpoint accessible")
                
                products = response.json()
                self.log_test("E-catalogue Data", len(products) >= 0, f"{len(products)} products in catalogue")
                
                # Check if we have the required E-catalogue fields
                if products:
                    product = products[0]
                    required_fields = [
                        'id', 'name', 'code', 'unit_of_measure', 'effective_unit_price',
                        'current_stock_quantity', 'minimum_stock_level', 'maximum_stock_level',
                        'estimated_consumption_rate_per_day', 'estimated_days_stock_will_last',
                        'stock_status'
                    ]
                    
                    missing_fields = [f for f in required_fields if f not in product]
                    self.log_test("E-catalogue Fields", len(missing_fields) == 0, 
                                f"All required fields present" if not missing_fields else f"Missing: {missing_fields}")
                
            else:
                self.log_test("E-catalogue Endpoint", False, f"Status: {response.status_code}")
                
        except Exception as e:
            self.log_test("Database Migration", False, str(e))
    
    def test_product_categories(self):
        """Test product categories functionality"""
        print("\n📂 PRODUCT CATEGORIES TESTING")
        print("=" * 50)
        
        headers = {"Authorization": f"Bearer {self.token}", "Content-Type": "application/json"}
        
        try:
            # Create a test category
            category_data = {
                "name": "E-catalogue Test Category",
                "code": "ECAT-TEST",
                "description": "Test category for E-catalogue functionality",
                "is_active": True
            }
            
            response = requests.post(f"{API_BASE}/products/categories/", 
                                   headers=headers, json=category_data)
            
            if response.status_code == 201:
                category = response.json()
                self.test_data['category_id'] = category['id']
                self.log_test("Create Product Category", True, f"Category ID: {category['id']}")
            else:
                self.log_test("Create Product Category", False, f"Status: {response.status_code}")
                
            # Get categories
            response = requests.get(f"{API_BASE}/products/categories/", headers=headers)
            if response.status_code == 200:
                categories = response.json()
                self.log_test("Get Product Categories", len(categories) > 0, f"{len(categories)} categories found")
            else:
                self.log_test("Get Product Categories", False, f"Status: {response.status_code}")
                
        except Exception as e:
            self.log_test("Product Categories", False, str(e))
    
    def test_product_crud(self):
        """Test enhanced product CRUD operations"""
        print("\n📦 ENHANCED PRODUCT CRUD TESTING")
        print("=" * 50)
        
        headers = {"Authorization": f"Bearer {self.token}", "Content-Type": "application/json"}
        
        try:
            # Create a comprehensive E-catalogue product
            product_data = {
                "name": "Premium Coffee Beans - E-catalogue Test",
                "code": "ECAT-COFFEE-001",
                "description": "High-quality arabica coffee beans for hotel restaurant service",
                "category_id": self.test_data.get('category_id'),
                "unit_of_measure": "kg",
                "standard_cost": 25.50,
                "contract_price": 23.75,
                "currency": "USD",
                "current_stock_quantity": 150.0,
                "minimum_stock_level": 20,
                "maximum_stock_level": 300,
                "reorder_point": 50,
                "estimated_consumption_rate_per_day": 5.5,
                "specifications": {
                    "origin": "Colombia",
                    "roast_level": "Medium",
                    "certification": "Organic",
                    "packaging": "25kg bags"
                },
                "is_active": True
            }
            
            # Create product
            response = requests.post(f"{API_BASE}/products/", headers=headers, json=product_data)
            
            if response.status_code == 201:
                product = response.json()
                self.test_data['product_id'] = product['id']
                self.log_test("Create E-catalogue Product", True, f"Product ID: {product['id']}")
                
                # Verify all E-catalogue fields
                expected_fields = {
                    'effective_unit_price': 23.75,  # Should use contract_price
                    'estimated_days_stock_will_last': round(150.0 / 5.5, 2),  # 27.27 days
                    'stock_status': 'NORMAL'  # Should be normal (150 > 50 reorder point)
                }
                
                for field, expected_value in expected_fields.items():
                    actual_value = product.get(field)
                    if field == 'estimated_days_stock_will_last':
                        # Allow for small floating point differences
                        passed = abs(actual_value - expected_value) < 0.1 if actual_value else False
                    else:
                        passed = actual_value == expected_value
                    
                    self.log_test(f"E-catalogue Field: {field}", passed, 
                                f"Expected: {expected_value}, Got: {actual_value}")
                
            else:
                self.log_test("Create E-catalogue Product", False, 
                            f"Status: {response.status_code}, Response: {response.text}")
                return
            
            # Test product retrieval
            product_id = self.test_data['product_id']
            response = requests.get(f"{API_BASE}/products/{product_id}", headers=headers)
            
            if response.status_code == 200:
                product = response.json()
                self.log_test("Get Single Product", True, f"Retrieved product: {product['name']}")
            else:
                self.log_test("Get Single Product", False, f"Status: {response.status_code}")
            
            # Test stock update
            stock_update = {
                "current_stock_quantity": 25.0,
                "last_restocked_date": datetime.now().isoformat()
            }
            
            response = requests.patch(f"{API_BASE}/products/{product_id}/stock", 
                                    headers=headers, json=stock_update)
            
            if response.status_code == 200:
                updated_product = response.json()
                new_quantity = updated_product.get('current_stock_quantity')
                new_status = updated_product.get('stock_status')
                
                self.log_test("Update Product Stock", True, 
                            f"New quantity: {new_quantity}, Status: {new_status}")
                
                # Should now be LOW_STOCK (25 <= 20 minimum)
                self.log_test("Stock Status Calculation", new_status == 'REORDER_NEEDED', 
                            f"Expected REORDER_NEEDED, got {new_status}")
                
            else:
                self.log_test("Update Product Stock", False, f"Status: {response.status_code}")
            
            # Test consumption rate update
            consumption_update = {
                "estimated_consumption_rate_per_day": 2.0,
                "last_consumption_update": datetime.now().isoformat()
            }
            
            response = requests.patch(f"{API_BASE}/products/{product_id}/consumption", 
                                    headers=headers, json=consumption_update)
            
            if response.status_code == 200:
                updated_product = response.json()
                new_rate = updated_product.get('estimated_consumption_rate_per_day')
                new_days = updated_product.get('estimated_days_stock_will_last')
                
                self.log_test("Update Consumption Rate", True, 
                            f"New rate: {new_rate}/day, Days remaining: {new_days}")
                
                # Should be 25.0 / 2.0 = 12.5 days
                expected_days = 25.0 / 2.0
                days_correct = abs(new_days - expected_days) < 0.1 if new_days else False
                self.log_test("Days Calculation", days_correct, 
                            f"Expected: {expected_days}, Got: {new_days}")
                
            else:
                self.log_test("Update Consumption Rate", False, f"Status: {response.status_code}")
                
        except Exception as e:
            self.log_test("Product CRUD Operations", False, str(e))
    
    def test_e_catalogue_filtering(self):
        """Test E-catalogue filtering and search functionality"""
        print("\n🔍 E-CATALOGUE FILTERING TESTING")
        print("=" * 50)
        
        headers = {"Authorization": f"Bearer {self.token}"}
        
        try:
            # Test stock status filtering
            for status in ['LOW_STOCK', 'REORDER_NEEDED', 'NORMAL', 'OVERSTOCK']:
                response = requests.get(f"{API_BASE}/products/e-catalogue/?stock_status={status}", 
                                      headers=headers)
                
                if response.status_code == 200:
                    products = response.json()
                    self.log_test(f"Filter by {status}", True, f"{len(products)} products found")
                else:
                    self.log_test(f"Filter by {status}", False, f"Status: {response.status_code}")
            
            # Test low stock filter
            response = requests.get(f"{API_BASE}/products/e-catalogue/?low_stock_only=true", 
                                  headers=headers)
            
            if response.status_code == 200:
                products = response.json()
                self.log_test("Low Stock Filter", True, f"{len(products)} low stock products")
                
                # Verify all returned products are actually low stock
                if products:
                    all_low_stock = all(p['stock_status'] in ['LOW_STOCK', 'REORDER_NEEDED'] for p in products)
                    self.log_test("Low Stock Filter Accuracy", all_low_stock, 
                                "All returned products have correct status")
                
            else:
                self.log_test("Low Stock Filter", False, f"Status: {response.status_code}")
            
            # Test search functionality
            response = requests.get(f"{API_BASE}/products/e-catalogue/?search=coffee", 
                                  headers=headers)
            
            if response.status_code == 200:
                products = response.json()
                self.log_test("Search Functionality", len(products) > 0, 
                            f"{len(products)} products found for 'coffee'")
            else:
                self.log_test("Search Functionality", False, f"Status: {response.status_code}")
                
        except Exception as e:
            self.log_test("E-catalogue Filtering", False, str(e))
    
    def test_data_validation(self):
        """Test data validation for E-catalogue requirements"""
        print("\n✅ DATA VALIDATION TESTING")
        print("=" * 50)
        
        headers = {"Authorization": f"Bearer {self.token}", "Content-Type": "application/json"}
        
        try:
            # Test creating product with missing mandatory fields
            invalid_product = {
                "name": "Invalid Product",
                "code": "INVALID-001"
                # Missing required E-catalogue fields
            }
            
            response = requests.post(f"{API_BASE}/products/", headers=headers, json=invalid_product)
            
            # Should fail validation
            self.log_test("Mandatory Fields Validation", response.status_code == 422, 
                        f"Correctly rejected invalid product (Status: {response.status_code})")
            
            # Test invalid stock levels
            invalid_product2 = {
                "name": "Invalid Stock Product",
                "code": "INVALID-002",
                "unit_of_measure": "pieces",
                "minimum_stock_level": 100,
                "maximum_stock_level": 50,  # Max < Min (invalid)
                "estimated_consumption_rate_per_day": 1.0
            }
            
            response = requests.post(f"{API_BASE}/products/", headers=headers, json=invalid_product2)
            
            # Should fail validation
            self.log_test("Stock Level Validation", response.status_code == 422, 
                        f"Correctly rejected invalid stock levels (Status: {response.status_code})")
            
        except Exception as e:
            self.log_test("Data Validation", False, str(e))
    
    def test_bulk_operations(self):
        """Test bulk operations and performance"""
        print("\n⚡ BULK OPERATIONS TESTING")
        print("=" * 50)
        
        headers = {"Authorization": f"Bearer {self.token}"}
        
        try:
            # Test getting large dataset
            response = requests.get(f"{API_BASE}/products/?limit=1000", headers=headers)
            
            if response.status_code == 200:
                products = response.json()
                self.log_test("Large Dataset Retrieval", True, f"{len(products)} products retrieved")
            else:
                self.log_test("Large Dataset Retrieval", False, f"Status: {response.status_code}")
            
            # Test pagination
            response = requests.get(f"{API_BASE}/products/?limit=10&skip=0", headers=headers)
            
            if response.status_code == 200:
                first_page = response.json()
                
                response = requests.get(f"{API_BASE}/products/?limit=10&skip=10", headers=headers)
                if response.status_code == 200:
                    second_page = response.json()
                    
                    # Check that pages are different
                    different_pages = len(set(p['id'] for p in first_page) & set(p['id'] for p in second_page)) == 0
                    self.log_test("Pagination", different_pages, 
                                f"Page 1: {len(first_page)} items, Page 2: {len(second_page)} items")
                
            else:
                self.log_test("Pagination", False, f"Status: {response.status_code}")
                
        except Exception as e:
            self.log_test("Bulk Operations", False, str(e))
    
    def cleanup_test_data(self):
        """Clean up test data"""
        print("\n🧹 CLEANUP")
        print("=" * 50)
        
        headers = {"Authorization": f"Bearer {self.token}"}
        
        try:
            # Delete test product
            if 'product_id' in self.test_data:
                response = requests.delete(f"{API_BASE}/products/{self.test_data['product_id']}", 
                                         headers=headers)
                self.log_test("Delete Test Product", response.status_code == 204, 
                            f"Product cleanup status: {response.status_code}")
                
        except Exception as e:
            self.log_test("Cleanup", False, str(e))
    
    def run_all_tests(self):
        """Run all test suites"""
        print("🚀 E-CATALOGUE MODULE 1 - COMPREHENSIVE TEST SUITE")
        print("=" * 80)
        print(f"🕐 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)
        
        if not self.authenticate():
            print("❌ Authentication failed. Cannot proceed with tests.")
            return False
        
        # Run all test suites
        self.test_database_migration()
        self.test_product_categories()
        self.test_product_crud()
        self.test_e_catalogue_filtering()
        self.test_data_validation()
        self.test_bulk_operations()
        self.cleanup_test_data()
        
        # Print summary
        print("\n📊 TEST SUMMARY")
        print("=" * 50)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['passed'])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        if failed_tests > 0:
            print("\n❌ FAILED TESTS:")
            for result in self.test_results:
                if not result['passed']:
                    print(f"   • {result['test']}: {result['details']}")
        
        print(f"\n🏁 Testing completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        return failed_tests == 0


async def main():
    """Main test execution"""
    tester = ECatalogueTestSuite()
    success = tester.run_all_tests()
    
    if success:
        print("\n🎉 ALL TESTS PASSED! E-catalogue Module 1 is ready for production.")
        sys.exit(0)
    else:
        print("\n💥 SOME TESTS FAILED! Please review and fix issues before deployment.")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
