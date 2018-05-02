import pytest
from os import environ
from coingate.client import CoinGateV2Order, CoinGateV2Client, CoinGateClientException, CoinGateAPIException
from arrow import Arrow

V2_APP_ID = environ.get('COINGATE_TEST_APP_ID', None)
V2_API_TOKEN = environ.get('COINGATE_TEST_API_TOKEN', None)


@pytest.fixture
def v2client():
    if V2_APP_ID is None or V2_API_TOKEN is None:
        raise Exception(
            'Please provide API V2 credentials via the COINGATE_TEST_APP_ID and'
            'COINGATE_TEST_APP_ID environment variables.'
        )
    return CoinGateV2Client(V2_APP_ID, V2_API_TOKEN, env='sandbox')


@pytest.fixture
def v2testorder():
    return {
        'order_id': 'test_order',
        'price_amount': 10,
        'price_currency': 'USD',
        'receive_currency': 'USD',
        'title': 'Test order title',
        'description': 'Test order description',
        'callback_url': 'http://www.example.com/callback',
        'cancel_url': 'http://www.example.com/cancel',
        'success_url': 'http://www.example.com/success',
        'token': 'test-token',
    }


class TestV2Order:

    def test_valid_new_order(self, v2client, v2testorder):
        # test the new contructor with valid data
        # 1. Required arguments only
        #    Constructor
        order = CoinGateV2Order(v2testorder['order_id'], v2testorder['price_amount'], v2testorder['price_currency'], v2testorder['receive_currency'])
        assert order.order_id == v2testorder['order_id']
        assert order.price_amount == v2testorder['price_amount']
        assert order.price_currency == v2testorder['price_currency']
        assert order.receive_currency == v2testorder['receive_currency']
        #    API call
        response = v2client.create_order(order)
        assert isinstance(response, CoinGateV2Order)
        assert response.order_id == v2testorder['order_id']
        assert response.price_amount == v2testorder['price_amount']
        assert response.price_currency == v2testorder['price_currency']
        assert response.receive_currency == v2testorder['receive_currency']
        assert isinstance(response.coingate_id, int)
        assert isinstance(response.payment_url, str)
        assert isinstance(response.created_at, Arrow)
        # 2. Using all optional arguments
        order = CoinGateV2Order(**v2testorder)
        #    Constructor
        assert order.order_id == v2testorder['order_id']
        assert order.price_amount == v2testorder['price_amount']
        assert order.price_currency == v2testorder['price_currency']
        assert order.receive_currency == v2testorder['receive_currency']
        assert order.title == v2testorder['title']
        assert order.description == v2testorder['description']
        assert order.callback_url == v2testorder['callback_url']
        assert order.cancel_url == v2testorder['cancel_url']
        assert order.success_url == v2testorder['success_url']
        assert order.token == v2testorder['token']
        #    API call
        response = v2client.create_order(order)
        assert isinstance(response, CoinGateV2Order)
        assert response.order_id == v2testorder['order_id']
        assert response.price_amount == v2testorder['price_amount']
        assert response.price_currency == v2testorder['price_currency']
        assert response.receive_currency == v2testorder['receive_currency']
        assert isinstance(response.coingate_id, int)
        assert isinstance(response.payment_url, str)
        assert isinstance(response.created_at, Arrow)

    def test_invalid_new_order(self, v2client, v2testorder):
        # Null amount
        order = CoinGateV2Order(v2testorder['order_id'], 0, v2testorder['price_currency'], v2testorder['receive_currency'])
        with pytest.raises(CoinGateAPIException):
            v2client.create_order(order)
        # Invalid price currency
        order = CoinGateV2Order(v2testorder['order_id'], ['price_amount'], 'XXX', v2testorder['receive_currency'])
        with pytest.raises(CoinGateAPIException):
            v2client.create_order(order)
        # Invalid receive currency
        order = CoinGateV2Order(v2testorder['order_id'], ['price_amount'], v2testorder['price_currency'], 'XXX')
        with pytest.raises(CoinGateAPIException):
            v2client.create_order(order)


class TestV2Client:

    def test_get_orders(self, v2client, v2testorder):
        order = CoinGateV2Order(v2testorder['order_id'], v2testorder['price_amount'], v2testorder['price_currency'], v2testorder['receive_currency'])
        result = v2client.create_order(order)
        order_id = result.coingate_id
        # Get order by ID
        order = v2client.get_order(order_id)
        assert isinstance(order, CoinGateV2Order)
        # list orders
        response = v2client.list_orders(per_page=100, page=1, sort_by='created_at_desc')
        assert isinstance(response['orders'], list)
        assert all(isinstance(i, CoinGateV2Order) for i in response['orders'])
        assert response['per_page'] == 100
        assert response['current_page'] == 1
        assert 'total_orders' in response
        assert isinstance(response['total_orders'], int)
        assert 'total_pages' in response
        assert isinstance(response['total_pages'], int)
        # iterate all orders
        all_orders = list(v2client.iterate_all_orders())
        assert all(isinstance(i, CoinGateV2Order) for i in all_orders)

    def test_valid_exchange_rates(self, v2client):
        # All rates
        rates = v2client.get_rates()
        assert isinstance(rates, dict)
        assert 'merchant' in rates
        assert 'trader' in rates
        assert isinstance(rates['merchant'], dict)
        assert isinstance(rates['trader'], dict)
        assert 'buy' in rates['trader']
        assert 'sell' in rates['trader']
        for currency in rates['merchant'].values():
            assert all(isinstance(i, float) for i in currency.values())
        for subcategory, currencies in rates['trader'].items():
            for currency in currencies.values():
                assert all(isinstance(i, float) for i in currency.values())
        # merchant rates
        rates = v2client.get_rates('merchant')
        assert isinstance(rates, dict)
        for currency in rates.values():
            assert all(isinstance(i, float) for i in currency.values())
        # trader rates
        rates = v2client.get_rates('trader')
        assert isinstance(rates, dict)
        assert set(rates.keys()) == set(('buy', 'sell'))
        for subcategory in ('buy', 'sell'):
            for currency in rates[subcategory].values():
                assert all(isinstance(i, float) for i in currency.values())
        # trader rates, subcategories
        for subcategory in ('buy', 'sell'):
            rates = v2client.get_rates('trader', subcategory)
            assert isinstance(rates, dict)
            for currency in rates.values():
                assert all(isinstance(i, float) for i in currency.values())
        # single rate
        rate = v2client.get_rate('BTC', 'USD')
        assert isinstance(rate, float)

    def test_invalid_exchange_rates(self, v2client):
        # per-category rates
        # - Invalid category
        with pytest.raises(CoinGateClientException):
            v2client.get_rates('XXX')
        # - Invalid subcategory
        with pytest.raises(CoinGateClientException):
            v2client.get_rates('trader', 'xxx')
        # - valid subcategory with invalid category
        with pytest.raises(CoinGateClientException):
            v2client.get_rates('merchant', 'buy')
        # Single rate
        # - Invalid "from" currency
        with pytest.raises(CoinGateClientException):
            v2client.get_rate('XXX', 'BTC')
        # - Invalid "to" currency
        with pytest.raises(CoinGateClientException):
            v2client.get_rate('BTC', 'XXX')
        # - Invalid "to" and "from" currencies
        with pytest.raises(CoinGateClientException):
            print(v2client.get_rate('XXX', 'XXX'))
            v2client.get_rate('XXX', 'NOP')


