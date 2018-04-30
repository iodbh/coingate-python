import hashlib
import hmac
import time
from urlparse import urlunparse, urljoin
import requests
import arrow

from .constants import LIVE_HOSTNAME, SANDBOX_HOSTNAME, ORDER_SORT_TYPES
from .exceptions import CoinGateAPIException, CoinGateClientException


class CoinGateBaseOrder:
    """Base class for CoinGate orders

    the fields_translation dictionary contains dictionaries that indicates
    how fields returned by CoinGate's API relate to properties of the class.
    Most of them have default arguments. Here are the keys and their possible
    values :
      -  The name of the field in Coingate's schema is given by the key
      - "property_name": The corresponding property on the model. If not set,
        defaults to the value of field_name
      - "casting": function to be called to cast the value of the field.
        defaults to str.
      - "required": if set to True, will raise an exception if the field is
        missing. Defaults to False.
      - "validate": Function used to validate the data, should return a Boolean
        (True if valid, False if invalid). No validation will occur if this is
        set to None. Defaults to None.

    Children classes are expected to have coingate_id and order_id properties
    """

    fields_translation = dict()

    def __str__(self):
        if self.coingate_id is not None:
            return "<CoinGate Order {} ({})>".format(self.order_id, self.coingate_id)
        return "<CoinGate Order {}>".format(self.order_id)

    @classmethod
    def from_response_data(cls, rdata):
        """Creates an CoinGateOrder instance from data returned by the API.

        This is used for creating an instance based on an order that has been
        created on Coingate. As such, the receive_currency shouldn't be set.

        Args:
            rdata: a Dict of data returned by the CoinGate API.

        Returns:
            A CoinGateOrder instance created from the request data.
        """

        args = {}

        for fname, f in cls.fields_translation.items():
            if f.get('required', False) and fname not in rdata:
                raise CoinGateClientException('Field {} is required and missing'.format(fname))
            if fname in rdata:
                if (f.get('validate', None) is not None) and (not f['validate'](rdata[fname])):
                    raise CoinGateClientException('Field {} has invalid value'.format(fname))
                args[f.get('property_name', fname)] = f.get('casting', str)(rdata[fname])

        return cls(**args)


class CoinGateV1Order(CoinGateBaseOrder):
    """CoinGate Order.
    """

    fields_translation = {
        'order_id': {'required': True},
        'price': {'casting': float, 'required': True},
        'currency': {'required': True},
        'receive_currency': {},
        'title': {'validate': lambda x: x <= 150},
        'description': {'validate': lambda x: x <= 500},
        'callback_url': {},
        'cancel_url': {},
        'success_url': {},
        'id': {'property_name': 'coingate_id', 'casting': int},
        'status': {},
        'created_at': {'casting': arrow.get},
        'expire_at': {'casting': arrow.get},
        'payment_url': {},
        'btc_amount': {'casting': float},
        'bitcoin_address': {},
        'bitcoin_uri': {},
    }

    def __init__(self, order_id, price, currency, receive_currency=None, title=None,
                 description=None, callback_url=None, cancel_url=None,
                 success_url=None, coingate_id=None, status=None,
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
            coingate_id: CoinGate-assigned ID of the order.
            status: Order status.
            created_at: Order creation date. Arrow object.
            expire_at: Order expiration date.
            payment_url: Invoice URL for payment.
            btc_amount: BTC price.
            bitcoin_address: BTC address for payment.
            bitcoin_uri: BTC URI for payment.
        """

        self.order_id = order_id
        self.price = price
        self.currency = currency
        self.receive_currency = receive_currency
        self.title = title
        self.description = description
        self.callback_url = callback_url
        self.cancel_url = cancel_url
        self.success_url = success_url
        self.coingate_id = coingate_id
        self.status = status
        self.created_at = created_at
        self.expire_at = expire_at
        self.payment_url = payment_url
        self.btc_amount = btc_amount
        self.bitcoin_address = bitcoin_address
        self.bitcoin_uri = bitcoin_uri

    def __str__(self):
        if self.coingate_id is not None:
            return "<CoinGate Order {} ({})>".format(self.order_id, self.coingate_id)
        return "<CoinGate Order {}>".format(self.order_id)

    def to_request_data(self):

        if self.receive_currency is None:
            raise CoinGateClientException("Can't serialize an Order without a receive_currency set.")

        rdata = {
            "order_id": self.order_id,
            "price": self.price,
            "currency": self.currency,
            "receive_currency": self.receive_currency,
            "title": self.title,
            "description": self.description,
            "callback_url": self.callback_url,
            "cancel_url": self.cancel_url,
            "success_url": self.success_url
        }

        for field in tuple(rdata.keys()):
            if rdata[field] is None:
                del rdata[field]

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


class CoinGateV2Order(CoinGateBaseOrder):

    fields_translation = {
        'order_id': {'required': True},
        'price_currency': {'required': True},
        'receive_currency': {},
        'price_amount': {'casting': float, 'required': True},
        'title': {'validate': lambda x: x <= 150},
        'description': {'validate': lambda x: x <= 500},
        'callback_url': {},
        'cancel_url': {},
        'success_url': {},
        'id': {'property_name': 'coingate_id', 'casting': int},
        'status': {},
        'created_at': {'casting': arrow.get},
        'expire_at': {'casting': arrow.get},
        'payment_url': {},
        'payment_address': {},
        'token': {},
        'pay_currency': {},
        'pay_amount': {'casting': float},
    }

    def __init__(self, order_id, price_amount, price_currency, receive_currency, title=None,
                 description=None, callback_url=None, cancel_url=None,
                 success_url=None, coingate_id=None, status=None,
                 created_at=None, expire_at=None, payment_address=None, payment_url=None, token=None,
                 pay_currency=None, pay_amount=None):
        """Inits a CoinGateOrder instance/

        The positional arguments the fields required by the Coingate API when
        creating an order.

        All the arguments are Strings unless otherwise specified.

        Args:
            order_id: Merchant's custom order ID.
            price_amount: Float. The price set by the merchant
            price_currency: ISO 4217 currency code which defines the currency in
                which you wish to price your merchandise; used to define price
                parameter.
            receive_currency:
                ISO 4217 currency code which defines the currency in which you
                wish to receive your payouts. Possible values: EUR, USD, BTC.
            title: Max 150 characters.
            description: More details about this order. Max 500 characters. It
                can be cart items, product details or other comment.
            callback_url: Send an automated message to Merchant URL when order
                status is changed.
            cancel_url: Redirect to Merchant URL when buyer canceled order.
            success_url: Redirect to Merchant URL after successful payment.
            coingate_id: CoinGate-assigned ID of the order.
            status: Order status.
            created_at: Order creation date. Arrow object.
            expire_at: Order expiration date.
            payment_url: Invoice URL for payment.
            payment_address: String
            pay_currency: The currency used by the buyer.
            pay_amount: the amount of pay_currency paid by the buyer.
        """

        self.order_id = order_id
        self.price_amount = price_amount
        self.price_currency = price_currency
        self.receive_currency = receive_currency
        self.title = title
        self.description = description
        self.callback_url = callback_url
        self.cancel_url = cancel_url
        self.success_url = success_url
        self.coingate_id = coingate_id
        self.status = status
        self.created_at = created_at
        self.expire_at = expire_at
        self.payment_url = payment_url
        self.payment_address = payment_address
        self.token = token
        self.pay_currency = pay_currency
        self.pay_amount = pay_amount

    def to_request_data(self):

        if self.receive_currency is None:
            raise CoinGateClientException("Can't serialize an Order without a receive_currency set.")

        rdata = {
            "order_id": self.order_id,
            "price_amount": self.price_amount,
            "price_currency": self.price_currency,
            "receive_currency": self.receive_currency,
            "title": self.title,
            "description": self.description,
            "callback_url": self.callback_url,
            "cancel_url": self.cancel_url,
            "success_url": self.success_url,
            "token": self.token,
        }

        for field in tuple(rdata.keys()):
            if rdata[field] is None:
                del rdata[field]

        return rdata

    @classmethod
    def new(cls, order_id, price_amount, price_currency, receive_currency, title=None,
            description=None, callback_url=None, cancel_url=None,
            success_url=None, token=None):
        """Constructs a new order.

            This is a helper function that only takes the arguments relevant to
            the creation of a new order.

        Returns:
            New CoinGateOrder object.
        """

        return cls(order_id, price_amount, price_currency, receive_currency, title,
                   description, callback_url, cancel_url, success_url, token=token)


class CoingateBaseClient:
    """CoinGate API client Base class.
    """

    order_class = CoinGateBaseOrder

    def __init__(self, app_id, env, api_version=1):
        self.ssl_verify = True
        self.api_version = api_version
        self.app_id = app_id
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

    @property
    def auth_headers(self):
        pass

    def api_request(self, route, request_method='get', params=None, raw=False):
        if params is None:
            params = {}

        # Authentication

        headers = self.auth_headers

        # Build the URL

        full_route = '{}/{}'.format(self.base_path, route.lstrip('/'))
        url = urljoin(self.base_url, full_route)

        # Send the request

        try:
            if request_method == 'get':
                req = requests.get(url, headers=headers, params=params, verify=self.ssl_verify)
            elif request_method == 'post':
                headers['Content-Type'] = 'application/x-www-form-urlencoded'
                req = requests.post(url, data=params, headers=headers, verify=self.ssl_verify)
            if not raw:
                status_code, parsed_response = req.status_code, req.json()
            else:
                status_code, parsed_response = req.status_code, req.text
        except requests.RequestException as e:
            raise CoinGateClientException("The connection failed: {}".format(e.message))

        if status_code != 200:
            raise CoinGateAPIException.from_response_dict(parsed_response, status_code)

        return parsed_response

    def iterate_all_orders(self, per_page=100, sort_by='created_at_desc'):
        has_next = True
        current_page = 1
        while has_next:

            response = self.list_orders(page=current_page, per_page=per_page, sort_by=sort_by)
            for order in response["orders"]:
                yield order
            if current_page < response["total_pages"]:
                has_next = True
                current_page += 1
            else:
                has_next = False

    def list_orders(self, per_page=100, page=1, sort_by='created_at_desc'):
        if sort_by not in ORDER_SORT_TYPES:
            raise CoinGateClientException('"sort_by" must be one of {}'.format(', '.join(ORDER_SORT_TYPES)))
        query = {"per_page": per_page, "page": page, "sort_by": sort_by}
        response = self.api_request('/orders', 'get', params=query)
        response["orders"] = [self.order_class.from_response_data(item) for item in response["orders"]]
        return response

    def get_order(self, order_id):
        route = '/orders/{}'.format(order_id)
        response = self.api_request(route, 'get')
        return self.order_class.from_response_data(response)

    def create_order(self, order):
        """Creates a payment order.

        Args:
            order: CoinGateOrder instance for the new payment.

        Returns:
            CoinGateOrder instance with fields populated from the Coingate Response.
        """
        route = '/orders'
        response = self.api_request(route, 'post', params=order.to_request_data())
        return self.order_class.from_response_data(response)

    def get_rates(self, category=None, subcategory=None):
        """
        Gets the list of CoinGate exchange rates.

        Args:
            category: Rates category to fetch. Defaults to all. Can be one of
                "merchant" or "trader"
            subcategory: subcategory for the "trader" category. One of "buy" or
            "sell"

        Returns:
            Rates dictionary.
        """
        route = '/rates'
        if category not in ('merchant', 'trader', None):
            raise CoinGateClientException('Rates category must be "merchant", "trader" or None')
        if subcategory is not None and category != 'trader':
            raise CoinGateClientException('Only the "trader" category supports a subcategory')
        if subcategory not in ('buy', 'sell', None):
            raise CoinGateClientException('Subcategory must be "buy", "sell" or None')
        if category is not None:
            route = '{}/{}'.format(route, category)
        if subcategory is not None:
            route = '{}/{}'.format(route, subcategory)
        response = self.api_request(route, 'get')
        return response

    def get_rate(self, from_, to):
        """
        Gets the CoingGate's exchange rate for a currency pair.

        Args:
            from_: symbol of the currency to exchange from
            to: symbol of the currency to exchange to

        Returns:
            CoinGate exchange rate (Float)
        """
        route = '/rates/merchant/{}/{}'.format(from_, to)
        response = self.api_request(route, 'get', raw=True)
        if not len(response):
            raise CoinGateClientException("No exchange rate available for the {}{} pair".format(from_, to))
        return float(response)


class CoinGateV1Client(CoingateBaseClient):
    """CoinGate API client.
    """

    order_class = CoinGateV1Order

    def __init__(self, app_id, api_key, api_secret, env="sandbox"):

        CoingateBaseClient.__init__(self, app_id, env, api_version=1)

        # Auth
        self.api_key = api_key
        self.api_secret = api_secret

    @property
    def auth_headers(self):
            nonce = str(int(time.time() * 1e6))
            message = str(nonce) + str(self.app_id) + self.api_key
            signature = hmac.new(str(self.api_secret), str(message), hashlib.sha256).hexdigest()

            return {
                'Access-Nonce': nonce,
                'Access-Key': self.api_key,
                'Access-Signature': signature
            }


class CoinGateV2Client(CoingateBaseClient):

    order_class = CoinGateV2Order

    def __init__(self, app_id, api_token, env="sandbox"):

        CoingateBaseClient.__init__(self, app_id, env, 2)

        self.api_token = api_token

    @property
    def auth_headers(self):
            return {'Authorization': 'Token {}'.format(self.api_token)}