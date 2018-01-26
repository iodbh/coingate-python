# Coingate Python

Simple API client for the [CoinGate](https://coingate.com/) service.

## Usage

```python
from coingate.client import CoinGateClient, CoinGateOrder

# Create a client
# To use the production API, add env="live"
client = CoinGateClient("app_id", "api_key", "api_secret")

# Prepare an order
new_order = CoinGateOrder.new(
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