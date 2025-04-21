# IndiaCard Insight API Documentation

## Overview
IndiaCard Insight is a comprehensive credit card management system that helps users track their credit cards, preferences, and activities.

## Authentication
The API uses token-based authentication. To get started:

1. Register a new user:
```http
POST /api/accounts/users/register/
{
    "username": "your_username",
    "email": "your.email@example.com",
    "password": "your_password",
    "confirm_password": "your_password",
    "first_name": "Your",
    "last_name": "Name"
}
```

2. Get your authentication token:
```http
POST /api/token-auth/
{
    "username": "your_username",
    "password": "your_password"
}
```

3. Use the token in all subsequent requests:
```http
Authorization: Token your_token_here
```

## API Endpoints

### User Management
- `POST /api/accounts/users/register/` - Register new user
- `POST /api/accounts/users/change_password/` - Change password
- `GET /api/accounts/users/me/` - Get current user details

### User Profile
- `GET /api/accounts/profiles/` - Get user profile
- `PUT /api/accounts/profiles/{id}/` - Update profile
```json
{
    "phone_number": "1234567890",
    "date_of_birth": "1990-01-01",
    "annual_income": 500000,
    "occupation": "Software Engineer",
    "city": "Mumbai",
    "state": "Maharashtra",
    "pincode": "400001",
    "credit_score": 750
}
```

### User Credit Cards
- `GET /api/accounts/credit-cards/` - List user's credit cards
- `POST /api/accounts/credit-cards/` - Add a new credit card
- `PUT /api/accounts/credit-cards/{id}/` - Update card details
- `DELETE /api/accounts/credit-cards/{id}/` - Remove a card

#### Filtering Credit Cards
- By card name: `?card_name=Regalia`
- By bank: `?bank=HDFC`
- By status: `?status=active`
- By date range: `?joining_date_after=2024-01-01&joining_date_before=2024-12-31`
- By annual fee waiver: `?annual_fee_waived=true`

### User Preferences
- `GET /api/accounts/preferences/` - Get user preferences
- `PUT /api/accounts/preferences/{id}/` - Update preferences
```json
{
    "preferred_banks": [1, 2],
    "preferred_card_types": ["rewards", "cashback"],
    "monthly_spend": 50000,
    "primary_spend_categories": ["dining", "shopping"],
    "max_annual_fee": 1000,
    "notification_preferences": {
        "email_alerts": true,
        "push_notifications": false
    }
}
```

### User Activity
- `GET /api/accounts/activities/` - List user activities

#### Filtering Activities
- By type: `?activity_type=card_added`
- By date range: `?date_from=2024-01-01&date_to=2024-12-31`
- Search description: `?search=updated profile`

## Common Features

### Pagination
All list endpoints are paginated with 10 items per page. Use the following query parameters:
- `?page=1` - Get specific page
- `?page_size=20` - Change items per page

### Ordering
Use `ordering` parameter with field name. Prefix with `-` for descending order:
- `?ordering=-created_at` - Latest first
- `?ordering=joining_date` - Oldest first

### Search
Use `search` parameter for text search across relevant fields:
- `?search=hdfc regalia` - Search cards
- `?search=profile updated` - Search activities

## Interactive Documentation
- Swagger UI: `/swagger/`
- ReDoc: `/redoc/`
- OpenAPI Schema: `/swagger.json`

## Error Handling
The API uses standard HTTP status codes:
- 200: Success
- 201: Created
- 400: Bad Request
- 401: Unauthorized
- 403: Forbidden
- 404: Not Found
- 500: Server Error

Error responses include detailed messages:
```json
{
    "error": "Invalid request",
    "detail": "Specific error message here"
}
```
