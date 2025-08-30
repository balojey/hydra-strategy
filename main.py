from pprint import pprint
from os import getenv

from lumibot.strategies import Strategy
from lumibot.brokers import Alpaca
from lumibot.traders import Trader
from lumibot.entities import Asset


from os import getenv

from lumibot.brokers import Ccxt

WOOFI_PRO_CONFIG = {
    "exchange_id": "woofipro",
    "api_key": getenv("WOOFIPRO_API_KEY"),
    "secret": getenv("WOOFIPRO_API_SECRET"),
    "accountId": getenv("WOOFIPRO_ACCOUNT_ID"),
    "privateKey": getenv("WALLET_PRIVATE_KEY"),
    "sandbox": True if getenv("WOOFIPRO_IS_SANDBOX", "true").lower() == "true" else False,
}

broker = Ccxt(WOOFI_PRO_CONFIG)
pprint(broker._fetch_balance())

class MyStrategy(Strategy):
    def on_trading_iteration(self):
        if self.first_iteration:
            # Buy 100 shares of SPY
            order = self.create_order(
                Asset(symbol="SPY", asset_type="stock"),
                quantity=100,
                side="buy"
            )
            self.submit_order(order)


strategy = MyStrategy(broker=broker)
trader = Trader()
trader.add_strategy(strategy)
trader.run_all()