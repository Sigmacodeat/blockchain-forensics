# Crypto Payments API Documentation

## Overview
The Crypto Payments API provides comprehensive cryptocurrency payment processing with support for multiple blockchains, real-time monitoring, and subscription management.

## Base URL
```
/api/v1/crypto-payments
```

## Authentication
All endpoints require JWT authentication via `Authorization: Bearer <token>` header.

## Endpoints

### BTC Invoice Management

#### Create BTC Invoice
```http
POST /api/v1/crypto-payments/invoice
Content-Type: application/json
Authorization: Bearer <token>

{
  "plan_name": "pro",
  "amount_btc": 0.001,
  "expires_hours": 24,
  "idempotency_key": "optional-unique-key"
}
```

**Response:**
```json
{
  "order_id": "btc_inv_abc123",
  "address": "bc1q...address",
  "expected_amount_btc": "0.00100000",
  "expires_at": "2025-10-26T12:00:00Z",
  "plan_name": "pro"
}
```

**Features:**
- Idempotent with `idempotency_key` (prevents duplicates)
- Rate limited: 5 invoices per user per hour
- Generates unique bech32 addresses
- 24-hour expiration by default

#### Get Invoice Status
```http
GET /api/v1/crypto-payments/invoice/{order_id}
Authorization: Bearer <token>
```

**Response:**
```json
{
  "order_id": "btc_inv_abc123",
  "status": "pending|paid|expired",
  "received_amount_btc": "0.00100000",
  "expected_amount_btc": "0.00100000",
  "address": "bc1q...address",
  "txid": "a1b2c3...",
  "paid_at": "2025-10-26T10:30:00Z",
  "expires_at": "2025-10-26T12:00:00Z",
  "plan_name": "pro"
}
```

**Real-time Updates:**
- WebSocket: `ws://localhost:8000/api/v1/ws/invoice/{order_id}?token=<jwt>`
- Messages: `{"type": "invoice_status_update", ...}`

### NOWPayments Integration

#### Get Available Currencies
```http
GET /api/v1/crypto-payments/currencies
```

#### Create Payment
```http
POST /api/v1/crypto-payments/create
{
  "plan": "pro",
  "currency": "btc",
  "recurring": false
}
```

#### Get Payment Status
```http
GET /api/v1/crypto-payments/status/{payment_id}
```

### Web3 Payments (MetaMask)

#### Create Web3 Payment
```http
POST /api/v1/crypto-payments/web3/modern
{
  "plan_name": "pro",
  "amount_usd": 299,
  "currency": "ETH",
  "network": "ethereum"
}
```

**Response includes EIP-681 URL:**
```
ethereum:0x742d35Cc6634C0532925a3b844Bc454e4438f44e@1000000000000000000
```

#### Get Supported Networks
```http
GET /api/v1/crypto-payments/web3/networks
```

### Analytics & Monitoring (Admin Only)

#### Revenue Summary
```http
GET /api/v1/crypto-payments/analytics/revenue-summary?days=30
```

#### Daily Revenue
```http
GET /api/v1/crypto-payments/analytics/daily-revenue?days=30
```

#### Conversion Funnel
```http
GET /api/v1/crypto-payments/analytics/conversion-funnel?days=30
```

## WebSocket Real-time Updates

### Invoice Status Updates
```javascript
const ws = new WebSocket('ws://localhost:8000/api/v1/ws/invoice/order_id?token=jwt_token');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  if (data.type === 'invoice_status_update') {
    console.log('Status:', data.status);
    console.log('Received:', data.received_amount_btc);
  }
};
```

### Payment Status Updates
```javascript
const ws = new WebSocket('ws://localhost:8000/api/v1/ws/payment/payment_id?token=jwt_token');
```

## Error Handling

### Rate Limiting
```json
{
  "detail": "Rate limit exceeded: Maximum 5 invoices per hour",
  "status_code": 429
}
```

### Idempotency
```json
{
  "detail": "Use idempotency_key to prevent duplicates",
  "status_code": 200
}
```

## Security Features

- **Idempotency**: Prevent duplicate invoices
- **Rate Limiting**: 5 invoices/hour per user
- **User Isolation**: Users only see their own payments
- **JWT Authentication**: Secure WebSocket connections
- **Input Validation**: Comprehensive request validation

## Monitoring

- Prometheus metrics for all endpoints
- Invoice monitoring worker (60s intervals)
- WebSocket connection tracking
- Payment conversion analytics

## Integration Examples

### Frontend (React)
```typescript
// Create invoice
const response = await fetch('/api/v1/crypto-payments/invoice', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${token}`
  },
  body: JSON.stringify({
    plan_name: 'pro',
    amount_btc: 0.001,
    idempotency_key: Date.now().toString()
  })
});

// WebSocket for real-time updates
const ws = new WebSocket(`${wsUrl}/api/v1/ws/invoice/${orderId}?token=${token}`);
```

### Backend (Python)
```python
import httpx

async def create_invoice(user_id: str, plan: str, amount: float):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{API_BASE}/crypto-payments/invoice",
            json={
                "plan_name": plan,
                "amount_btc": amount,
                "idempotency_key": f"{user_id}_{int(time.time())}"
            },
            headers={"Authorization": f"Bearer {jwt_token}"}
        )
        return response.json()
```
