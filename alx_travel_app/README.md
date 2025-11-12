Perfect! Here’s a **ready-to-use README.md** snippet for your ALX milestone submission. It clearly explains the **Chapa payment integration workflow**, how to run/test it, and shows the workflow end-to-end. You can add screenshots in the `screenshots/` folder if needed.

---

# ALX Travel App – Payment Integration with Chapa API

## Overview

This project demonstrates **secure payment integration** in a Django-based travel booking app using the **Chapa Payment Gateway**. Users can initiate payments, complete them via Chapa, and receive confirmation emails automatically.

---

## Features Implemented

1. **Payment Model**

   * Stores transactions with fields: `tx_ref`, `amount`, `status`, `email`, `user`.
   * Tracks payment `status` (`pending`, `completed`, `failed`).

2. **Payment Initiation**

   * API endpoint `/api/payments/initiate-payment/` to start a payment.
   * Generates a unique `tx_ref` per booking.
   * Returns a **checkout URL** for front-end redirection.
   * Saves initial payment status as `pending`.

3. **Webhook Handling**

   * Endpoint `/api/payments/webhook/` listens for Chapa server-to-server notifications.
   * **CSRF-exempt** for external POST requests.
   * **HMAC-SHA256 signature verification** to ensure authenticity.
   * Updates payment record to `completed` upon success.
   * **Idempotent**: repeated webhook calls do not create duplicate emails or updates.

4. **Email Notifications**

   * Sends confirmation email after successful payment.
   * Can be triggered via **Celery** (recommended for production) or directly in Django.

5. **Security Measures**

   * Sensitive keys stored in environment variables.
   * Webhook validates signature before updating database.
   * Payments cannot be forged or marked successful without verification.

---

## API Endpoints

| Endpoint                          | Method | Description                                                |
| --------------------------------- | ------ | ---------------------------------------------------------- |
| `/api/payments/initiate-payment/` | POST   | Creates payment record and returns Chapa checkout URL      |
| `/api/payments/webhook/`          | POST   | Handles Chapa webhook, updates payment status, sends email |

### Example: Initiate Payment

```http
POST /api/payments/initiate-payment/
Content-Type: application/json

{
    "email": "user@example.com",
    "full_name": "John Doe",
    "amount": "500"
}
```

Response:

```json
{
    "checkout_url": "https://chapa.co/checkout/...",
    "tx_ref": "c1f5a6e2-xxxx-xxxx-xxxx-xxxx"
}
```

---

## Webhook

* CSRF exempt, publicly accessible.
* Verifies `chapa-signature` header using `CHAPA_SECRET_KEY`.
* Updates `Payment` model status to `completed`.
* Triggers confirmation email to the user.

---

## Setup & Configuration

1. Clone repository:

```bash
git clone https://github.com/<yourusername>/alx_travel_app_0x02.git
cd alx_travel_app_0x02
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Create `.env` file:

```env
CHAPA_SECRET_KEY=<your_chapa_secret_key>
CHAPA_PUBLIC_KEY=<your_chapa_public_key>
CHAPA_BASE_URL=https://api.chapa.co/v1
```

4. Run migrations:

```bash
python manage.py migrate
```

5. Start Django server:

```bash
python manage.py runserver
```

6. (Optional) Start Celery for async emails:

```bash
celery -A alx_travel_app worker --loglevel=info
```

7. For local webhook testing, use **ngrok**:

```bash
ngrok http 8000
```

Set ngrok HTTPS URL as **Chapa webhook URL** in sandbox dashboard.

---

## Workflow Summary

1. User clicks **Book** → `initiate-payment/` creates payment record → returns checkout URL.
2. User completes payment on Chapa’s secure page.
3. Chapa sends **webhook POST** to `/webhook/`.
4. Webhook:

   * Validates HMAC signature
   * Updates `Payment` status
   * Sends confirmation email
5. User receives email and sees updated booking/payment status.

---

## Testing

* Tested in **Chapa sandbox environment**.
* Payment initiation, webhook call, status update, and email delivery all verified.
* Idempotency confirmed: repeated webhooks do not duplicate emails or status updates.

---

## Screenshots (Optional)

```
screenshots/
├── checkout_url.png
├── payment_completed_db.png
└── email_confirmation.png
```

---

## Notes

* Ensure **CHAPA_SECRET_KEY** is kept secret.
* Use **sandbox keys** for development/testing.
* In production, configure **SMTP email backend** for real email delivery.

---
