from datetime import datetime
import requests

import ta
import pandas as pd

from lumibot.strategies import Strategy
from lumibot.backtesting import PandasDataBacktesting
from lumibot.entities import Asset, Bars, Data

base_asset = 'ETH'
quote_asset = 'USDC'
resolution = '5'  # 5 minute

class HydraStrategy(Strategy):
    parameters = {
        'fast_ema_period': 5,
        'slow_ema_period': 20,
        "rsi_period": 14,
        "rsi_overbought": 70,
        "rsi_oversold": 30,
    }

    def initialize(self):
        self.set_market('24/7')

    def on_trading_iteration(self):
        self.base = Asset(base_asset, Asset.AssetType.CRYPTO)
        self.quote = Asset(quote_asset, Asset.AssetType.CRYPTO)
        # print(f'Portfolio value: {self.portfolio_value}')

        # If cash exceeds initial budget by more than 10%, log a warning that target has been reached
        if self.cash >= self.initial_budget + (self.initial_budget * 0.1):
            print(f"Cash {self.cash} exceeds initial budget {self.initial_budget} by more than 10%.")
            self.close_positions([self.base])
        elif self.cash <= self.initial_budget - (self.initial_budget * 0.5):
            print(f"Cash {self.cash} below initial budget {self.initial_budget} by more than 50%.")
            self.close_positions([self.base])
        else:
            bars: Bars = self.get_historical_prices(
                asset=self.base,
                quote=self.quote,
                timestep='5 minutes',
                length=100,
                timeshift=100 if self.first_iteration else 0
            )
            fast_ema = ta.trend.EMAIndicator(bars.df['close'], self.parameters["fast_ema_period"])
            slow_ema = ta.trend.EMAIndicator(bars.df['close'], self.parameters["slow_ema_period"])
            rsi = ta.momentum.RSIIndicator(bars.df['close'], self.parameters["rsi_period"])

            if (
                (fast_ema.ema_indicator().iloc[-1] > slow_ema.ema_indicator().iloc[-1])
                and
                (self.parameters["rsi_oversold"] < rsi.rsi().iloc[-1] < self.parameters["rsi_overbought"])
                ):
                # print("Golden cross detected!")
                if not self.get_position(self.base):
                    # print("Placing buy order!")
                    order = self.create_order(
                        asset=self.base,
                        quote=self.quote,
                        quantity=100,
                        side='buy'
                    )
                    self.submit_order(order)
                    if not self.is_backtesting: self.wait_for_order_execution(order)
            elif (
                (fast_ema.ema_indicator().iloc[-1] < slow_ema.ema_indicator().iloc[-1])
                and
                (self.parameters["rsi_oversold"] < rsi.rsi().iloc[-1] < self.parameters["rsi_overbought"])
                ):
                # print("Death cross detected!")
                if self.get_position(self.base):
                    # print("Placing sell order!")
                    order = self.create_order(
                        asset=self.base,
                        quote=self.quote,
                        quantity=100,
                        side='sell'
                    )
                    self.submit_order(order)
                    if not self.is_backtesting: self.wait_for_order_execution(order)


strategy = HydraStrategy()

backtesting_start = datetime(2025, 8, 23)
backtesting_end = datetime(2025, 8, 30)

url = "https://api.orderly.org/v1/tv/history"
querystring = {
    "symbol": f"PERP_{base_asset}_{quote_asset}",
    "resolution": resolution,
    "from": str(int(backtesting_start.timestamp())),
    "to": str(int(backtesting_end.timestamp())),
}
response = requests.get(url, params=querystring)
data = response.json()
df = pd.DataFrame({
    'datetime': data.get('t', []),
    'open': data.get('o', []),
    'high': data.get('h', []),
    'low': data.get('l', []),
    'close': data.get('c', []),
    'volume': data.get('v', [])
})
df['datetime'] = pd.to_datetime(df['datetime'], unit='s')
df.set_index('datetime', inplace=True)
asset = Asset(base_asset, Asset.AssetType.CRYPTO)
quote = Asset(quote_asset, Asset.AssetType.CRYPTO)
pandas_data = {
    asset: Data(
        asset,
        df,
        timestep='minute',
        quote=quote,
    )
}
# print(df.tail())

strategy.backtest(
    PandasDataBacktesting,
    backtesting_start=pandas_data[asset].datetime_start,
    backtesting_end=pandas_data[asset].datetime_end,
    budget=2000000,
    pandas_data=pandas_data,
    benchmark_asset=asset,
    quote_asset=quote,
)