from .config import config
from .context import Context
from .derivatives import InvestorDerivatives, MarketRepDerivatives
from .equity import InvestorEquity, MarketRepEquity
from .market import MarketData
from .realtime import RealtimeDataConnection


class _BaseUser:
    SANDBOX = "SANDBOX"
    SANDBOX_ENV = "uat"
    SANDBOX_BROKER_ID = "098"

    def __init__(
        self,
        app_id: str,
        app_secret: str,
        app_code: str,
        broker_id: str,
        is_auto_queue: bool = False,
    ):
        """Base class for all users.

        Parameters
        ----------
        app_id : str
            API key.
        app_secret : str
            API secret.
        app_code : str
            app code.
        broker_id : str
            Broker ID. if broker_id is 'SANDBOX', broker_id is '098' and environment is 'uat'.
        is_auto_queue : bool, optional
            _description_, by default False
        """

        self._app_id = app_id
        self._app_secret = app_secret
        self._app_code = app_code
        self._broker_id = broker_id
        self._is_auto_queue = is_auto_queue

        if self._broker_id.upper() == self.SANDBOX:
            config["environment"] = self.SANDBOX_ENV
            self._broker_id = self.SANDBOX_BROKER_ID

        self._ctx = Context(
            app_id=self._app_id,
            app_secret=self._app_secret,
            app_code=self._app_code,
            broker_id=self._broker_id,
            is_auto_queue=self._is_auto_queue,
        )
        self._ctx.login()

    def MarketData(self):
        return MarketData(self._ctx)

    def RealtimeDataConnection(self):
        return RealtimeDataConnection(self._ctx)


class Investor(_BaseUser):
    def __init__(
        self,
        app_id: str,
        app_secret: str,
        app_code: str,
        broker_id: str,
        is_auto_queue: bool = False,
    ):
        super().__init__(
            app_id=app_id,
            app_secret=app_secret,
            app_code=app_code,
            broker_id=broker_id,
            is_auto_queue=is_auto_queue,
        )

    def Derivatives(self, account_no: str):
        return InvestorDerivatives(self._ctx, account_no)

    def Equity(self, account_no: str):
        return InvestorEquity(self._ctx, account_no)


class MarketRep(_BaseUser):
    def __init__(
        self,
        app_id: str,
        app_secret: str,
        app_code: str,
        broker_id: str,
        is_auto_queue: bool = False,
    ):
        super().__init__(
            app_id=app_id,
            app_secret=app_secret,
            app_code=app_code,
            broker_id=broker_id,
            is_auto_queue=is_auto_queue,
        )

    def Derivatives(self):
        return MarketRepDerivatives(self._ctx)

    def Equity(self):
        return MarketRepEquity(self._ctx)
