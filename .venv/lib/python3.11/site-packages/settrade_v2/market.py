from typing import Optional

from .config import config
from .context import Context, Option
from .errors import InvalidEnvironmentError
from .logger import LogWrapperMetaClass
from .util import response_to_dict


class MarketData(metaclass=LogWrapperMetaClass):
    def __init__(self, context: Context):
        self._ctx = context

        if config["environment"] == "prod":
            self.market_url = "https://marketapi.settrade.com"
        elif config["environment"] == "uat":
            self.market_url = "https://marketapi-test.settrade.com"
        else:
            raise InvalidEnvironmentError()

        self.market_url += f"/api/marketdata/v3/{self._ctx.broker_id}"

    def get_candlestick(
        self,
        symbol: str,
        interval: str,
        limit: Optional[int] = None,
        start: Optional[str] = None,
        end: Optional[str] = None,
        normalized: Optional[bool] = None,
    ):
        path = f"{self.market_url}/candlesticks".replace("marketdata", "techchart", 1)
        params = {
            "symbol": symbol,
            "interval": interval,
            "limit": limit,
            "start": start,
            "end": end,
            "normalized": normalized,
        }
        params = {k: v for k, v in params.items() if v is not None}

        response = self._ctx.dispatch(Option("GET", path, params=params))
        return response_to_dict(response)

    # def get_quote_stock(self, symbol: str):
    #     path = f"{self.market_url}/stocks/{symbol}/quote"
    #     response = self._ctx.dispatch(Option("GET", path))
    #     return response_to_dict(response)

    def get_quote_symbol(self, symbol: str):
        path = f"{self.market_url}/quote/{symbol}"
        response = self._ctx.dispatch(Option("GET", path))
        return response_to_dict(response)

    # def get_quote_option(
    #     self,
    #     symbol: str,
    #     underlying_price: float,
    #     volatility: float,
    #     remain_day: float,
    #     interest_rate: float,
    #     dividend: float,
    # ):
    #     path = f"{self.market_url}/options/{symbol}/quote"
    #     params = {
    #         "underlyingPrice": underlying_price,
    #         "volatility": volatility,
    #         "remainDay": remain_day,
    #         "interestRate": interest_rate,
    #         "dividend": dividend,
    #     }
    #     response = self._ctx.dispatch(Option("GET", path, params=params))
    #     return response_to_dict(response)

    # def get_series_option(
    #     self,
    #     underlying: str,
    #     underlying_price: float,
    #     volatility: float,
    #     remain_day: float,
    #     interest_rate: float,
    #     dividend: float,
    # ):
    #     # TODO: add exp_month and exp_year
    #     path = f"{self.market_url}/options/series/{underlying}"
    #     params = {
    #         # expMonth: exp_month,
    #         # expYear: exp_year,
    #         "underlyingPrice": underlying_price,
    #         "volatility": volatility,
    #         "remainDay": remain_day,
    #         "interestRate": interest_rate,
    #         "dividend": dividend,
    #     }
    #     response = self._ctx.dispatch(Option("GET", path, params=params))
    #     return response_to_dict(response)

    # def get_quote_futures(self, symbol: str):
    #     path = f"{self.market_url}/futures/{symbol}/quote"
    #     response = self._ctx.dispatch(Option("GET", path))
    #     return response_to_dict(response)

    # def get_series_futures(self, underlying: str):
    #     path = f"{self.market_url}/futures/series/{underlying}"
    #     response = self._ctx.dispatch(Option("GET", path))
    #     return response_to_dict(response)
