import hashlib
import hmac
import time
from urlparse import urlunparse, urljoin
import requests
import arrow

from .constants import LIVE_HOSTNAME, SANDBOX_HOSTNAME, ORDER_SORT_TYPES
from .exceptions import CoinGateAPIException, CoinGateClientException


class CoinGateOrder:
    """CoinGate Order.
    """

    def __init__(self, order_id, price, currency, receive_currency=None, title=None,
                 description=None, callback_url=None, cancel_url=None,
                 success_url=None, coinbase_id=None, status=None,
                 created_at=None, expire_at=None, payment_url=None,
                 btc_amount=None, bitcoin_address=None, bitcoin_uri=None):
        """Inits a CoinGateOrder instance/

        The positional arguments the fields required by the Coingate API when
        creating an order.

        All the arguments are Strings unless otherwise specified.

        Args:
            order_id: Merchant's custom order ID.
            price: Float. The price set by the merchant. Float.
            currency: ISO 4217 currency code which defines the currency in
                which you wish to price your merchandise; used to define price
                parameter.
            receive_currency:
                ISO 4217 currency code which defines the currency in which you
                wish to receive your payouts.
            title: Max 150 characters.
            description: More details about this order. Max 500 characters. It
                can be cart items, product details or other comment.
            callback_url: Send an automated message to Merchant URL when order
                status is changed.
            cancel_url: Redirect to Merchant URL when buyer canceled order.
            success_url: Redirect to Merchant URL after successful payment.
            coinbase_id: CoinGate-assigned ID of the order.
            status: Order status.
            created_at: Order creation date. Arrow object.
            expire_at: Order expiration date.
            payment_url: Invoice URL for payment.
            btc_amount: BTC price.
            bitcoin_address: BTC address for payment.
            bitcoin_uri: BTC URI for payment.
        """
        if title is not None and len(title) > 150:
            raise CoinGateAPIException("Order title can't be longer than 150 characters.")
        if description is not None and len(description) > 500:
            raise CoinGateAPIException("Order description can't be longer than 500 characters.")

        self.order_id = order_id
        self.price = price
        self.currency = currency
        self.receive_currency = receive_currency
        self.title = title
        self.description = description
        self.callback_url = callback_url
        self.cancel_url = cancel_url
        self.success_url = success_url
        self.coinbase_id = coinbase_id
        self.status = status
        self.created_at = created_at
        self.expire_at = expire_at
        self.payment_url = payment_url
        self.btc_amount = btc_amount
        self.bitcoin_address = bitcoin_address
        self.bitcoin_uri = bitcoin_uri

    def __str__(self):
        if self.coinbase_id is not None:
            return "<CoinGate Order {} ({})>".format(self.order_id, self.coinbase_id)
        return "<CoinGate Order {}>".format(self.order_id)

    @classmethod
    def from_response_data(cls, rdata):
        """Creates an CoinGateOrder instance from data returned by the API.

        This is used for creating an instance based on an order that has been
        created on Coinbase. As such, the receive_currency shouldn't be set.

        Args:
            rdata: a Dict of data returned by the CoinGate API.

        Returns:
            A CoinGateOrder instance created from the request data.
        """
        return cls(
            rdata["order_id"],
            rdata["price"],
            rdata["currency"],
            receive_currency=None,
            title=rdata.get("title", None),
            description=rdata.get("description", None),
            callback_url=rdata.get("callback_url", None),
            cancel_url=rdata.get("cancel_url", None),
            success_url=rdata.get("success_url", None),
            coinbase_id=rdata.get("id", None),
            status=rdata.get("status", None),
            created_at=arrow.get(rdata["created_at"]),
            expire_at=arrow.get(rdata["expire_at"]),
            payment_url=rdata["payment_url"],
            btc_amount=rdata["btc_amount"],
            bitcoin_address=rdata["bitcoin_address"],
            bitcoin_uri=rdata["bitcoin_uri"]

        )

    def to_request_data(self):

        if self.receive_currency is None:
            raise CoinGateClientException("Can't serialize an Order without a receive_currency set.")

        rdata = {
            "order_id": self.order_id,
            "price": self.price,
            "currency": self.currency,
            "receive_currency" : self.receive_currency,
            "title": "",
            "description": "",
            "callback_url": "",
            "cancel_url": "",
            "success_url": ""
        }

        return rdata

    @classmethod
    def new(cls, order_id, price, currency, receive_currency, title=None,
                 description=None, callback_url=None, cancel_url=None,
                 success_url=None):
        """Constructs a new order.

            This is a helper function that only takes the arguments relevant to
            the creation of a new order.

        Returns:
            New CoinGateOrder object.
        """

        return cls(order_id, price, currency, receive_currency, title,
                 description, callback_url, cancel_url, success_url)


class CoinGateClient:
    """CoinGate API client.
    """

    def __init__(self, app_id, api_key, api_secret, env="sandbox", api_version="1"):

        # Construct the base URL for API requests
        if env == "sandbox":
            hostname = SANDBOX_HOSTNAME
        elif env == "live":
            hostname = LIVE_HOSTNAME
        else:
            raise CoinGateClientException('Invalid environment, please specify either "live" or "sandbox"')

        self.base_path = '/v{}'.format(api_version)
        base_url_components = ('https', hostname, self.base_path, '', '', '')
        self.base_url = urlunparse(base_url_components)

        # Auth

        self.app_id = app_id
        self.api_key = api_key
        self.api_secret = api_secret

    def api_request(self, route, request_method='get', params=None):
        if params is None:
            params = {}

        # Authentication

        nonce = str(int(time.time() * 1e6))
        message = str(nonce) + str(self.app_id) + self.api_key
        signature = hmac.new(self.api_secret, message, hashlib.sha256).hexdigest()

        headers = {
            'Access-Nonce': nonce,
            'Access-Key': self.api_key,
            'Access-Signature': signature
        }

        # Build the URL

        full_route = '{}/{}'.format(self.base_path, route.lstrip('/'))
        url = urljoin(self.base_url, full_route)

        # Send the request

        try:
            if request_method == 'get':
                req = requests.get(url, headers=headers, params=params)
            elif request_method == 'post':
                headers['Content-Type'] = 'application/x-www-form-urlencoded'
                req = requests.post(url, data=params, headers=headers)
            status_code, parsed_response = req.status_code, req.json()
        except requests.RequestException as e:
            raise CoinGateClientException("The connection failed: {}".format(e.message))

        if status_code != 200:
            raise CoinGateAPIException.from_response_dict(parsed_response, status_code)

        return parsed_response

    def iterate_all_orders(self, per_page=100, sort_by='created_at_desc'):
        has_next = True
        current_page = 1
        while has_next:

            print('current page: {}'.format(current_page))
            response = self.list_orders(page=current_page, per_page=per_page, sort_by=sort_by)
            print('total pages: {}'.format(response["total_pages"]))
            print('total pages: {}'.format(type(response["total_pages"])))
            for order in response["orders"]:
                yield order
            if current_page < response["total_pages"]:
                has_next = True
                print(has_next)
                current_page += 1
            else:
                has_next = False

    def list_orders(self, per_page=100, page=1, sort_by='created_at_desc'):
        if sort_by not in ORDER_SORT_TYPES:
            raise CoinGateClientException('"sort_by" must be one of {}'.format(', '.join(ORDER_SORT_TYPES)))
        query = {"per_page": per_page, "page": page, "sort_by": sort_by}
        response = self.api_request('/orders', 'get', params=query)
        response["orders"] = [CoinGateOrder.from_response_data(item) for item in response["orders"]]
        return response

    def get_order(self, order_id):
        route = '/orders/{}'.format(order_id)
        response = self.api_request(route, 'get')
        return CoinGateOrder.from_response_data(response)

    def create_order(self, order):
        """Creates a payment order.

        Args:
            order: CoinGateOrder instance for the new payment.

        Returns:

        """
        route = '/orders'
        response = self.api_request(route, 'post', params=order.to_request_data())
        return CoinGateOrder.from_response_data(response)
