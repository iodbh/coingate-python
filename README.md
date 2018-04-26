# Coingate Python

Simple API client for the [CoinGate](https://coingate.com/) service.

## Usage

### API V2

```python
from coingate.client import CoinGateV2Client, CoinGateV2Order

# Create a client
# To use the production API, add env="live"
client = CoinGateV1Client("app_id", "api_token"")

# Prepare an order
new_order = CoinGateV2Order.new(
    "order-ID",
    10.5,
    "USD",
    "USD",
    callback_url='https://api.example.com/paymentcallback?token=randomtoken',
    cancel_url='https://www.example.com/ordercancelled',
    success_url='https://www.example.com/orderprocessed')

# Create the order
placed_order = client.create_order(new_order)

# Get the payment URL:
print(placed_order.payment_url)

# List orders :
orders = list(client.iterate_all_orders())

# Get an order by id:
order = orders[0].coingate_id
```

### API V1

```python
from coingate.client import CoinGateV1Client, CoinGateV1Order

# Create a client
# To use the production API, add env="live"
client = CoinGateV1Client("app_id", "api_key", "api_secret")

# Prepare an order
new_order = CoinGateV1Order.new(
    "order-ID",
    10.5,
    "USD",
    "USD",
    callback_url='https://api.example.com/paymentcallback?token=randomtoken',
    cancel_url='https://www.example.com/ordercancelled',
    success_url='https://www.example.com/orderprocessed')
    
# Create the order
placed_order = client.create_order(new_order)

# Get the payment URL:
print(placed_order.payment_url)

# List orders :
orders = list(client.iterate_all_orders())

# Get an order by id:
order = orders[0].coingate_id
```