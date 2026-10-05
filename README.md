# Digital Product Store Backend

FastAPI backend-only REST API for a digital product store. It uses MySQL + SQLAlchemy, JWT authentication, role-based access, cart/order management, Stripe Checkout, verified Stripe webhooks, SQL aggregate reports, Swagger, and Pytest.

## Features
- JWT Bearer authentication and bcrypt password hashing
- USER/ADMIN authorization
- Product CRUD and database-level pagination/search
- Per-user cart with ownership checks
- Order snapshots preserving historical product name/price
- Stripe Checkout in test mode
- Verified and idempotent-style webhook updates
- SQL aggregate admin reports
- CORS for `http://localhost:5173`
- Swagger `/docs` and ReDoc `/redoc`

## Structure
See the repository tree. Business logic is split between routers, services, models, schemas, dependencies and utilities.

## Requirements
Python 3.11+, MySQL 8+, Stripe test account/CLI for payment testing.

## Windows PowerShell setup
```powershell
cd digital-product-store\backend
python -m venv venv
venv\Scripts\activate
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Edit `.env`. Example:
```env
DATABASE_URL=mysql+pymysql://root:YOUR_MYSQL_PASSWORD@localhost:3306/digital_product_store
SECRET_KEY=replace-with-a-long-random-secret
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
STRIPE_SECRET_KEY=sk_test_your_key
STRIPE_WEBHOOK_SECRET=whsec_your_secret
FRONTEND_URL=http://localhost:5173
```

## MySQL
```sql
CREATE DATABASE digital_product_store CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```
If your MySQL root user has no password, use `mysql+pymysql://root@localhost:3306/digital_product_store`; otherwise include the password. Never commit `.env`.

The app calls `Base.metadata.create_all()` at startup. It does not drop tables or existing data.

## Run
```powershell
cd digital-product-store\backend
venv\Scripts\activate
python -m uvicorn app.main:app --reload
```
Open `http://127.0.0.1:8000/docs` or `http://127.0.0.1:8000/redoc`.

## Seed development data
```powershell
python seed.py
```
Development-only credentials created by the seed script:
- Admin: `admin@example.com` / `Admin@12345`
- User: `user@example.com` / `User@12345`
Do not use these credentials in production.

## Authentication flow
1. `POST /auth/register`
2. `POST /auth/login`
3. Copy `access_token` into Swagger Authorize as `Bearer <token>`.
4. `GET /auth/me`

## API groups
Authentication: `/auth/register`, `/auth/login`, `/auth/me`

Products: `POST/GET /products`, `GET/PUT/DELETE /products/{product_id}`. Writes require ADMIN.

Cart: `GET /cart`, `POST /cart/items`, `PUT/DELETE /cart/items/{item_id}`, `DELETE /cart`.

Orders: `GET /orders`, `GET /orders/{order_id}`. Users can only see their own orders.

Payments: `POST /payments/create-checkout-session`, `POST /payments/webhook`.

Admin: `/admin/products`, `/admin/orders`, `/admin/stats` and SQL reports under `/admin/reports/*`.

## Stripe
Use test keys only. Checkout prices are always taken from the database. The success URL never marks an order paid; payment state is changed only by a verified Stripe webhook.

Optional local forwarding:
```powershell
stripe listen --forward-to localhost:8000/payments/webhook
```
Copy the generated `whsec_...` value to `STRIPE_WEBHOOK_SECRET` and restart the API.

Relevant events:
- `checkout.session.completed` -> Order/Payment PAID and cart cleared
- `payment_intent.payment_failed` -> Order/Payment FAILED

## Reports
Admin reports use SQL joins/grouping/aggregates rather than loading all rows into Python:
- total revenue / paid orders / failed orders
- most purchased products
- orders per user
- top customers
- products never purchased

## Tests
Tests use a separate SQLite database and never use production MySQL. Stripe checkout is mocked.
```powershell
cd digital-product-store\backend
python -m pytest -q
```

## Error handling
401 is used for missing/invalid authentication, 403 for inactive/forbidden access, 404 for missing resources, 409 for duplicate registration, 422 for Pydantic validation, 400 for invalid checkout/webhook requests, and 502 for Stripe checkout failures.

## Security notes
- Passwords are bcrypt-hashed.
- JWT contains user ID, email, role and expiration.
- User ownership is derived from the authenticated JWT user, not request-supplied user IDs.
- Product prices, order/payment statuses and payment confirmation are not trusted from the frontend.
- Stripe webhook signatures are verified using the configured webhook secret.
- Secrets belong only in environment variables.
