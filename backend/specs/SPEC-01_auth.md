# SPEC-01: Authentication System

> **Status:** ✅ Complete  
> **Dependencies:** None  
> **Implemented by:** Fahd Azmy  

---

## Overview

Full user authentication system with registration, email verification, JWT-based login (access + refresh tokens), password reset, and protected routes.

## Files (Already Built)

| File | Purpose |
|---|---|
| `src/routes/auth_routes.py` | Auth API endpoints |
| `src/controllers/auth_controller.py` | Auth business logic |
| `src/helpers/security.py` | JWT creation/verification, password hashing |
| `src/helpers/email_service.py` | Email sending (verification, reset) |
| `src/models/db_scheams/user.py` | User database model |

## Database Schema

### `users` table
| Column | Type | Constraints |
|---|---|---|
| `id` | UUID | PK, default uuid4 |
| `name` | String(100) | NOT NULL |
| `email` | String(255) | UNIQUE, NOT NULL, INDEX |
| `hashed_password` | String(255) | NOT NULL |
| `is_active` | Boolean | default False |
| `is_verified` | Boolean | default False |
| `verification_token` | String(255) | nullable |
| `role` | String(20) | default "user" |
| `created_at` | DateTime | default utcnow |
| `updated_at` | DateTime | auto-update |

## API Endpoints

| Method | Endpoint | Description | Auth |
|---|---|---|---|
| POST | `/auth/register` | Register new user | ❌ |
| POST | `/auth/login` | Login, returns JWT | ❌ |
| POST | `/auth/refresh` | Refresh access token | 🔑 Refresh token |
| GET | `/auth/verify/{token}` | Verify email | ❌ |
| POST | `/auth/forgot-password` | Send reset email | ❌ |
| POST | `/auth/reset-password` | Reset password | ❌ |
| GET | `/auth/profile` | Get current user | 🔑 Access token |

## Key Dependency for Other Specs

All other specs depend on the `get_current_user` dependency from `src/helpers/security.py` to authenticate requests:

```python
from src.helpers.security import get_current_user

@router.get("/protected")
async def protected_route(current_user = Depends(get_current_user)):
    # current_user is a User object
    # current_user.id → UUID
    pass
```

## Acceptance Criteria ✅

- [x] User can register with name, email, password
- [x] Verification email is sent on registration
- [x] User can verify email via token link
- [x] User can login and receive access + refresh tokens
- [x] User can refresh expired access tokens
- [x] User can request password reset via email
- [x] Protected routes reject unauthenticated requests
- [x] User profile endpoint returns current user data
