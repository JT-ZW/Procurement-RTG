# 🚀 Procurement System API Testing Guide with Postman

## 📋 **Prerequisites**

1. **Start the FastAPI Server:**

   ```bash
   cd backend
   uvicorn app.main:app --reload --port 8000
   ```

2. **Database Setup:**

   ```bash
   # Run migrations if not already done
   alembic upgrade head
   ```

3. **Access API Documentation:**
   - Swagger UI: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc

---

## 🔧 **Postman Setup**

### 1. Create New Collection

- Name: "Procurement System API"
- Description: "Multi-tenant procurement system testing"

### 2. Collection Variables

Create these variables in your collection:

- `base_url`: `http://localhost:8000`
- `access_token`: (will be set after login)
- `refresh_token`: (will be set after login)
- `user_id`: (will be set after login)
- `unit_id`: (will be set after creating/getting units)

---

## 🔐 **Authentication Testing**

### **Step 1: Register a User**

**Request:** `POST {{base_url}}/auth/register`

**Headers:**

```
Content-Type: application/json
```

**Body (JSON):**

```json
{
  "email": "admin@hotel.com",
  "password": "SecurePass123!",
  "full_name": "System Administrator",
  "role": "super_admin",
  "is_active": true
}
```

**Expected Response:** `201 Created`

```json
{
  "id": "uuid-here",
  "email": "admin@hotel.com",
  "full_name": "System Administrator",
  "role": "super_admin",
  "is_active": true,
  "created_at": "2025-07-25T..."
}
```

### **Step 2: Login**

**Request:** `POST {{base_url}}/auth/login`

**Headers:**

```
Content-Type: application/x-www-form-urlencoded
```

**Body (form-data):**

```
username: admin@hotel.com
password: SecurePass123!
```

**Expected Response:** `200 OK`

```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer",
  "expires_in": 3600,
  "user": {
    "id": "uuid-here",
    "email": "admin@hotel.com",
    "full_name": "System Administrator",
    "role": "super_admin"
  }
}
```

**Post-response Script:**

```javascript
if (pm.response.code === 200) {
  const response = pm.response.json();
  pm.collectionVariables.set("access_token", response.access_token);
  pm.collectionVariables.set("refresh_token", response.refresh_token);
  pm.collectionVariables.set("user_id", response.user.id);
}
```

---

## 🏢 **Units Management Testing**

### **Step 3: Create a Unit**

**Request:** `POST {{base_url}}/api/v1/units/`

**Headers:**

```
Authorization: Bearer {{access_token}}
Content-Type: application/json
```

**Body (JSON):**

```json
{
  "name": "Grand Hotel Downtown",
  "code": "GHD001",
  "description": "Main downtown hotel location",
  "address": "123 Main Street, Downtown",
  "contact_person": "John Manager",
  "contact_email": "john@grandhotel.com",
  "contact_phone": "+1-555-0123",
  "is_active": true
}
```

**Post-response Script:**

```javascript
if (pm.response.code === 201) {
  const response = pm.response.json();
  pm.collectionVariables.set("unit_id", response.id);
}
```

### **Step 4: Get All Units**

**Request:** `GET {{base_url}}/api/v1/units/`

**Headers:**

```
Authorization: Bearer {{access_token}}
```

**Query Parameters:**

- `skip`: 0
- `limit`: 10

---

## 👥 **Users Management Testing**

### **Step 5: Create Additional Users**

**Request:** `POST {{base_url}}/api/v1/users/`

**Headers:**

```
Authorization: Bearer {{access_token}}
Content-Type: application/json
```

**Body (JSON):**

```json
{
  "email": "manager@hotel.com",
  "password": "ManagerPass123!",
  "full_name": "Unit Manager",
  "role": "unit_manager",
  "unit_assignments": [
    {
      "unit_id": "{{unit_id}}",
      "role": "unit_manager",
      "is_primary": true
    }
  ]
}
```

### **Step 6: Get All Users**

**Request:** `GET {{base_url}}/api/v1/users/`

**Headers:**

```
Authorization: Bearer {{access_token}}
```

---

## 📦 **Products Management Testing**

### **Step 7: Create Product Categories**

**Request:** `POST {{base_url}}/api/v1/products/categories/`

**Headers:**

```
Authorization: Bearer {{access_token}}
Content-Type: application/json
```

**Body (JSON):**

```json
{
  "name": "Kitchen Supplies",
  "description": "All kitchen-related products and equipment",
  "is_active": true
}
```

### **Step 8: Create Products**

**Request:** `POST {{base_url}}/api/v1/products/`

**Headers:**

```
Authorization: Bearer {{access_token}}
Content-Type: application/json
X-Current-Unit: {{unit_id}}
```

**Body (JSON):**

```json
{
  "name": "Premium Coffee Beans",
  "description": "High-quality arabica coffee beans",
  "sku": "COFFEE-001",
  "category_id": "category-uuid-from-step-7",
  "unit_of_measure": "kg",
  "unit_price": 25.5,
  "minimum_stock_level": 10,
  "maximum_stock_level": 100,
  "reorder_point": 20,
  "is_active": true,
  "specifications": {
    "origin": "Colombia",
    "roast_level": "Medium",
    "certification": "Organic"
  }
}
```

### **Step 9: Get Products**

**Request:** `GET {{base_url}}/api/v1/products/`

**Headers:**

```
Authorization: Bearer {{access_token}}
X-Current-Unit: {{unit_id}}
```

**Query Parameters:**

- `skip`: 0
- `limit`: 10
- `search`: "coffee" (optional)
- `category_id`: "category-uuid" (optional)

---

## 🏪 **Suppliers Management Testing**

### **Step 10: Create Suppliers**

**Request:** `POST {{base_url}}/api/v1/suppliers/`

**Headers:**

```
Authorization: Bearer {{access_token}}
Content-Type: application/json
X-Current-Unit: {{unit_id}}
```

**Body (JSON):**

```json
{
  "name": "Premium Food Distributors",
  "supplier_code": "PFD001",
  "email": "orders@premiumfood.com",
  "phone": "+1-555-0456",
  "address": "456 Supply Ave, Industrial District",
  "contact_person": "Sarah Supplier",
  "tax_id": "TAX123456789",
  "payment_terms": "Net 30",
  "status": "active",
  "categories": ["Kitchen Supplies", "Food & Beverage"]
}
```

### **Step 11: Get Suppliers**

**Request:** `GET {{base_url}}/api/v1/suppliers/`

**Headers:**

```
Authorization: Bearer {{access_token}}
X-Current-Unit: {{unit_id}}
```

---

## 📊 **Stock Management Testing**

### **Step 12: Add Stock Entry**

**Request:** `POST {{base_url}}/api/v1/stock/`

**Headers:**

```
Authorization: Bearer {{access_token}}
Content-Type: application/json
X-Current-Unit: {{unit_id}}
```

**Body (JSON):**

```json
{
  "product_id": "product-uuid-from-step-8",
  "quantity": 50,
  "unit_price": 25.5,
  "supplier_id": "supplier-uuid-from-step-10",
  "transaction_type": "receipt",
  "reference_number": "PO-2025-001",
  "notes": "Initial stock purchase"
}
```

### **Step 13: Get Stock Levels**

**Request:** `GET {{base_url}}/api/v1/stock/`

**Headers:**

```
Authorization: Bearer {{access_token}}
X-Current-Unit: {{unit_id}}
```

---

## 📋 **Purchase Requisitions Testing**

### **Step 14: Create Purchase Requisition**

**Request:** `POST {{base_url}}/api/v1/requisitions/`

**Headers:**

```
Authorization: Bearer {{access_token}}
Content-Type: application/json
X-Current-Unit: {{unit_id}}
```

**Body (JSON):**

```json
{
  "title": "Monthly Kitchen Supply Requisition",
  "description": "Regular monthly order for kitchen supplies",
  "required_by_date": "2025-08-15T10:00:00Z",
  "business_justification": "Essential supplies for daily operations",
  "estimated_total_value": 500.0,
  "priority": "medium",
  "items": [
    {
      "line_number": 1,
      "product_id": "product-uuid-from-step-8",
      "product_name": "Premium Coffee Beans",
      "quantity_requested": 20,
      "unit_of_measure": "kg",
      "estimated_unit_price": 25.5,
      "estimated_total_price": 510.0
    }
  ]
}
```

### **Step 15: Get Requisitions**

**Request:** `GET {{base_url}}/api/v1/requisitions/`

**Headers:**

```
Authorization: Bearer {{access_token}}
X-Current-Unit: {{unit_id}}
```

---

## 👑 **Admin Dashboard Testing**

### **Step 16: Get Dashboard Overview**

**Request:** `GET {{base_url}}/api/v1/admin/dashboard`

**Headers:**

```
Authorization: Bearer {{access_token}}
```

### **Step 17: Get System Statistics**

**Request:** `GET {{base_url}}/api/v1/admin/stats`

**Headers:**

```
Authorization: Bearer {{access_token}}
```

### **Step 18: Access Admin Dashboard UI**

**Request:** `GET {{base_url}}/admin/dashboard`

**Headers:**

```
Authorization: Bearer {{access_token}}
```

---

## 🔄 **Advanced Testing Scenarios**

### **Multi-Unit Testing**

1. Create multiple units
2. Switch unit context using `X-Current-Unit` header
3. Verify data isolation between units

### **Role-Based Access Testing**

1. Create users with different roles
2. Test access permissions for each role
3. Verify unauthorized access returns 403

### **Workflow Testing**

1. Create requisition → Submit → Approve → Fulfill
2. Test approval workflows
3. Test rejection scenarios

---

## 📈 **Performance Testing**

### **Bulk Operations**

- Create multiple products in batch
- Test pagination with large datasets
- Monitor response times

### **Concurrent Users**

- Use Postman Runner for load testing
- Test with multiple simultaneous requests
- Verify data consistency

---

## 🔍 **Error Handling Testing**

### **Invalid Data Testing**

```json
{
  "email": "invalid-email",
  "password": "123",
  "full_name": ""
}
```

### **Authentication Errors**

- Test expired tokens
- Test invalid credentials
- Test missing authentication

### **Authorization Errors**

- Test access to forbidden resources
- Test cross-unit data access
- Test role-based restrictions

---

## 📝 **Test Scripts for Automation**

### **Collection Pre-request Script**

```javascript
// Auto-refresh token if expired
if (pm.collectionVariables.get("access_token")) {
  const token = pm.collectionVariables.get("access_token");
  const tokenData = JSON.parse(atob(token.split(".")[1]));
  const now = Math.floor(Date.now() / 1000);

  if (tokenData.exp < now + 300) {
    // Refresh 5 minutes before expiry
    // Add refresh logic here
  }
}
```

### **Collection Test Script**

```javascript
// Common assertions
pm.test("Status code is successful", function () {
  pm.expect(pm.response.code).to.be.oneOf([200, 201, 204]);
});

pm.test("Response time is acceptable", function () {
  pm.expect(pm.response.responseTime).to.be.below(5000);
});

pm.test("Content-Type is JSON", function () {
  pm.expect(pm.response.headers.get("Content-Type")).to.include(
    "application/json"
  );
});
```

---

## 🎯 **Quick Start Commands**

```bash
# Start the server
cd backend
uvicorn app.main:app --reload --port 8000

# Run database migrations
alembic upgrade head

# Create initial admin user (if needed)
python -c "
from app.core.database import SessionLocal
from app.crud.user import crud_user
from app.schemas.user import UserCreate

db = SessionLocal()
user_data = UserCreate(
    email='admin@test.com',
    password='admin123',
    full_name='Admin User',
    role='super_admin'
)
crud_user.create(db, obj_in=user_data)
print('Admin user created!')
"
```

---

## 🔧 **Troubleshooting**

### **Common Issues:**

1. **401 Unauthorized:** Check token validity and format
2. **403 Forbidden:** Verify user permissions and unit access
3. **422 Validation Error:** Check request body format and required fields
4. **500 Internal Error:** Check server logs and database connection

### **Debug Headers:**

Add these headers for debugging:

```
X-Debug-Mode: true
X-Request-ID: unique-request-id
```

---

**Happy Testing! 🚀**

Your procurement system API is now ready for comprehensive testing with Postman!
