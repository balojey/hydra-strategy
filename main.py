from os import getenv

from lumibot.strategies import Strategy
from lumibot.brokers import Alpaca
from lumibot.traders import Trader
from lumibot.entities import Asset


ALPACA_CONFIG = {
    'API_KEY': getenv('ALPACA_API_KEY'),
    'API_SECRET': getenv('ALPACA_API_SECRET'),
    "PAPER": True if getenv('ALPACA_IS_PAPER', 'true').lower() == 'true' else False,
}

broker = Alpaca(ALPACA_CONFIG)

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