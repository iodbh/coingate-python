class CoinGateException(Exception):
    """Parent class for CoinGate exceptions.
    """
    pass


class CoinGateAPIException(CoinGateException):
    """CoinGate API exception.

        Raised if an error occurs within a CoinGate API call.
    """

    def __init__(self, message, response):
        super(CoinGateAPIException, self).__init__(message)

        # Now for your custom code...
        self.response = response

    @classmethod
    def from_response_dict(cls, dict, status):
        """Instantiates an exception from a CoinGate API error response.

        Args:
            dict: Dictionary parsed from a CoinGate error response.
            status: status code of the response.

        Returns:
            CoinGateAPIException instance with a message reflecting the API's
            response.
        """
        message = "{} ({}): {}".format(dict["reason"], status, dict["message"])
        return cls(message, dict)

    def __repr__(self):
        return "{} ({}): {}".format(self.api_reason, self.api_status, self.api_message)


class CoinGateClientException(CoinGateException):
    """CoinGate client exception.

        Raised if an error occurs outside of CoinGate's API.
    """
    pass
