from typing import Any, Dict, List, Optional

from .context import Context, Option
from .logger import LogWrapperMetaClass
from .util import response_to_dict


class _BaseDerivatives:
    def __init__(self, context: Context):
        self._ctx = context


class InvestorDerivatives(_BaseDerivatives, metaclass=LogWrapperMetaClass):
    def __init__(self, context: Context, account_no: str):
        super().__init__(context)
        self._account_no = account_no
        self.base_url = (
            f"{self._ctx.base_url}/api/seosd/v3/{self._ctx.broker_id}/accounts"
        )

    def get_account_info(self) -> Dict[str, Any]:
        path = f"{self.base_url}/{self._account_no}/account-info"
        response = self._ctx.dispatch(Option("GET", path))
        return response_to_dict(response)

    # def get_account_info_detail(self) -> Dict[str, Any]:
    #     path = f"{self.base_url}/{self._account_no}/account-info-detail"
    #     response = self._ctx.dispatch(Option("GET", path))
    #     return response_to_dict(response)

    # def get_commission(self) -> Dict[str, Any]:
    #     path = f"{self.base_url}/{self._account_no}/commission"
    #     response = self._ctx.dispatch(Option("GET", path))
    #     return response_to_dict(response)

    def get_order(self, order_no: int) -> Dict[str, Any]:
        path = f"{self.base_url}/{self._account_no}/orders/{order_no}"
        response = self._ctx.dispatch(Option("GET", path))
        return response_to_dict(response)

    def get_orders(self) -> List[Dict[str, Any]]:
        path = f"{self.base_url}/{self._account_no}/orders"
        response = self._ctx.dispatch(Option("GET", path))
        return response_to_dict(response)  # type: ignore

    def get_portfolios(self) -> Dict[str, Any]:
        path = f"{self.base_url}/{self._account_no}/portfolios"
        response = self._ctx.dispatch(Option("GET", path))
        return response_to_dict(response)

    def get_trades(self) -> List[Dict[str, Any]]:
        path = f"{self.base_url}/{self._account_no}/trades"
        response = self._ctx.dispatch(Option("GET", path))
        return response_to_dict(response)  # type: ignore

    # def get_trade_summaries(self) -> List[Dict[str, Any]]:
    #     path = f"{self.base_url}/{self._account_no}/trade-summaries"
    #     response = self._ctx.dispatch(Option("GET", path))
    #     return response_to_dict(response)  # type: ignore

    def place_order(
        self,
        pin: str,
        symbol: str,
        side: str,
        position: str,
        price: float,
        volume: int,
        price_type: str = "Limit",
        iceberg_vol: Optional[int] = None,
        validity_type: str = "Day",
        validity_date_condition: Optional[str] = None,
        stop_condition: Optional[str] = None,
        stop_symbol: Optional[str] = None,
        stop_price: Optional[float] = None,
        trigger_session: Optional[str] = None,
        bypass_warning: Optional[bool] = None,
    ) -> Dict[str, Any]:
        path = f"{self.base_url}/{self._account_no}/orders"
        body = {
            "symbol": symbol,
            "side": side,
            "position": position,
            "priceType": price_type,
            "price": price,
            "volume": volume,
            "icebergVol": iceberg_vol,
            "validityType": validity_type,
            "validityDateCondition": validity_date_condition,
            "stopCondition": stop_condition,
            "stopSymbol": stop_symbol,
            "stopPrice": stop_price,
            "triggerSession": trigger_session,
            "bypassWarning": bypass_warning,
            "pin": pin,
        }
        body = {k: v for k, v in body.items() if v is not None}

        response = self._ctx.dispatch(
            Option(method="POST", endpoint=path, payload=body)
        )
        return response_to_dict(response)

    def _place_orders(self, pin: str, order_list: List[dict]) -> Dict[str, Any]:
        path = f"{self.base_url}/{self._account_no}/orders/place-multiple"
        body = {
            "orders": order_list,
            "pin": pin,
        }
        response = self._ctx.dispatch(
            Option(method="POST", endpoint=path, payload=body)
        )
        return response_to_dict(response)

    def change_order(
        self,
        pin: str,
        order_no: int,
        new_price: Optional[float] = None,
        new_volume: Optional[int] = None,
        bypass_warning: Optional[bool] = None,
    ):
        path = f"{self.base_url}/{self._account_no}/orders/{order_no}/change"
        body = {
            "newPrice": new_price,
            "newVolume": new_volume,
            "bypassWarning": bypass_warning,
            "pin": pin,
        }
        body = {k: v for k, v in body.items() if v is not None}

        response = self._ctx.dispatch(
            Option(method="PATCH", endpoint=path, payload=body)
        )
        return response_to_dict(response)

    def cancel_order(self, order_no: int, pin: str):
        path = f"{self.base_url}/{self._account_no}/orders/{order_no}/cancel"
        body = {
            "pin": pin,
        }
        response = self._ctx.dispatch(
            Option(method="PATCH", endpoint=path, payload=body)
        )
        return response_to_dict(response)

    def cancel_orders(self, order_no_list: List[int], pin: str) -> Dict[str, Any]:
        path = f"{self.base_url}/{self._account_no}/cancel"
        body = {
            "pin": pin,
            "orders": order_no_list,
        }
        response = self._ctx.dispatch(
            Option(method="PATCH", endpoint=path, payload=body)
        )
        return response_to_dict(response)


class MarketRepDerivatives(_BaseDerivatives, metaclass=LogWrapperMetaClass):
    def __init__(self, context: Context):
        super().__init__(context)
        self.base_url = (
            f"{self._ctx.base_url}/api/seosd/v3/{self._ctx.broker_id}/mktrep"
        )

    def get_account_info(self, account_no: str) -> Dict[str, Any]:
        path = f"{self.base_url}/accounts/{account_no}/account-info"
        response = self._ctx.dispatch(Option("GET", path))
        return response_to_dict(response)

    # def get_account_info_detail(self, account_no: str) -> Dict[str, Any]:
    #     path = f"{self.base_url}/accounts/{account_no}/account-info-detail"
    #     response = self._ctx.dispatch(Option("GET", path))
    #     return response_to_dict(response)

    # def get_commission(self, account_no: str) -> Dict[str, Any]:
    #     path = f"{self.base_url}/accounts/{account_no}/commission"
    #     response = self._ctx.dispatch(Option("GET", path))
    #     return response_to_dict(response)

    def get_order(self, order_no: int) -> Dict[str, Any]:
        path = f"{self.base_url}/orders/{order_no}"
        response = self._ctx.dispatch(Option("GET", path))
        return response_to_dict(response)

    def get_orders(self) -> List[Dict[str, Any]]:
        path = f"{self.base_url}/orders"
        response = self._ctx.dispatch(Option("GET", path))
        return response_to_dict(response)  # type: ignore

    def get_orders_by_account_no(self, account_no: str) -> List[Dict[str, Any]]:
        path = f"{self.base_url}/accounts/{account_no}/orders"
        response = self._ctx.dispatch(Option("GET", path))
        return response_to_dict(response)  # type: ignore

    def get_portfolios(self, account_no: str) -> Dict[str, Any]:
        path = f"{self.base_url}/accounts/{account_no}/portfolios"
        response = self._ctx.dispatch(Option("GET", path))
        return response_to_dict(response)

    def get_trades(self, account_no: str) -> List[Dict[str, Any]]:
        path = f"{self.base_url}/accounts/{account_no}/trades"
        response = self._ctx.dispatch(Option("GET", path))
        return response_to_dict(response)  # type: ignore

    # def get_trade_summaries(self, account_no: str) -> List[Dict[str, Any]]:
    #     path = f"{self.base_url}/accounts/{account_no}/trade-summaries"
    #     response = self._ctx.dispatch(Option("GET", path))
    #     return response_to_dict(response)  # type: ignore

    def place_order(
        self,
        account_no: str,
        symbol: str,
        side: str,
        position: str,
        price: float,
        volume: int,
        price_type: str = "Limit",
        iceberg_vol: Optional[int] = None,
        validity_type: str = "Day",
        validity_date_condition: Optional[str] = None,
        stop_condition: Optional[str] = None,
        stop_symbol: Optional[str] = None,
        stop_price: Optional[float] = None,
        trigger_session: Optional[str] = None,
        bypass_warning: Optional[bool] = None,
    ) -> Dict[str, Any]:
        path = f"{self.base_url}/accounts/{account_no}/orders"
        body = {
            "symbol": symbol,
            "side": side,
            "position": position,
            "priceType": price_type,
            "price": price,
            "volume": volume,
            "icebergVol": iceberg_vol,
            "validityType": validity_type,
            "validityDateCondition": validity_date_condition,
            "stopCondition": stop_condition,
            "stopSymbol": stop_symbol,
            "stopPrice": stop_price,
            "triggerSession": trigger_session,
            "bypassWarning": bypass_warning,
        }
        body = {k: v for k, v in body.items() if v is not None}

        response = self._ctx.dispatch(
            Option(method="POST", endpoint=path, payload=body)
        )
        return response_to_dict(response)

    def _place_orders(self, account_no: str, order_list: List[dict]) -> Dict[str, Any]:
        path = f"{self.base_url}/accounts/{account_no}/orders/place-multiple"
        body = {
            "orders": order_list,
        }
        response = self._ctx.dispatch(
            Option(method="POST", endpoint=path, payload=body)
        )
        return response_to_dict(response)

    def change_order(
        self,
        account_no: str,
        order_no: int,
        new_price: Optional[float] = None,
        new_volume: Optional[int] = None,
        bypass_warning: Optional[bool] = None,
        new_account_no: Optional[str] = None,
    ):
        path = f"{self.base_url}/accounts/{account_no}/orders/{order_no}/change"
        body = {
            "newPrice": new_price,
            "newVolume": new_volume,
            "bypassWarning": bypass_warning,
            "newAccountNo": new_account_no,
        }
        body = {k: v for k, v in body.items() if v is not None}

        response = self._ctx.dispatch(
            Option(method="PATCH", endpoint=path, payload=body)
        )
        return response_to_dict(response)

    def cancel_order(self, account_no: str, order_no: int):
        path = f"{self.base_url}/accounts/{account_no}/orders/{order_no}/cancel"
        body = {}
        response = self._ctx.dispatch(
            Option(method="PATCH", endpoint=path, payload=body)
        )
        return response_to_dict(response)

    def cancel_orders(
        self, account_no: str, order_no_list: List[int]
    ) -> Dict[str, Any]:
        path = f"{self.base_url}/accounts/{account_no}/cancel"
        response = self._ctx.dispatch(
            Option(method="PATCH", endpoint=path, payload=order_no_list)
        )
        return response_to_dict(response)

    def place_trade_report(
        self,
        symbol: str,
        position: str,
        price: float,
        volume: int,
        cpm: str,
        ty_type: str,
        buyer: Optional[str] = None,
        seller: Optional[str] = None,
        control_key: Optional[str] = None,
    ):
        path = f"{self.base_url}/orders/tradeReport"
        body = {
            "buyer": buyer,
            "seller": seller,
            "symbol": symbol,
            "position": position,
            "price": price,
            "volume": volume,
            "cpm": cpm,
            "trType": ty_type,
            "controlKey": control_key,
        }
        body = {k: v for k, v in body.items() if v is not None}
        response = self._ctx.dispatch(
            Option(method="POST", endpoint=path, payload=body)
        )
        return response_to_dict(response)
