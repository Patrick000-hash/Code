import os
import time
import logging
from typing import Optional

from binance import Client, ThreadedWebsocketManager
from binance.enums import FuturesType
from binance.exceptions import BinanceAPIException


class BinanceFuturesBot:
    """Simple Binance Futures trading bot using moving average signals."""

    def __init__(self, api_key: str, api_secret: str, symbol: str = "BTCUSDT"):
        self.client = Client(api_key, api_secret)
        self.client.futures_change_leverage(symbol=symbol, leverage=1)
        self.symbol = symbol
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.setLevel(logging.INFO)
        if not self.logger.handlers:
            ch = logging.StreamHandler()
            ch.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
            self.logger.addHandler(ch)

    def get_klines(self, interval: str = Client.KLINE_INTERVAL_1MINUTE, limit: int = 100):
        try:
            return self.client.futures_klines(symbol=self.symbol, interval=interval, limit=limit)
        except BinanceAPIException as e:
            self.logger.error(f"Error fetching klines: {e}")
            return []

    def place_order(self, side: str, quantity: float, order_type: str = Client.FUTURE_ORDER_TYPE_MARKET):
        try:
            order = self.client.futures_create_order(
                symbol=self.symbol, side=side, type=order_type, quantity=quantity
            )
            self.logger.info(f"Order placed: {order}")
            return order
        except BinanceAPIException as e:
            self.logger.error(f"Order failed: {e}")
            return None

    def calculate_signals(self, closes):
        if len(closes) < 20:
            return None
        short_ma = sum(closes[-5:]) / 5
        long_ma = sum(closes[-20:]) / 20
        if short_ma > long_ma:
            return "BUY"
        elif short_ma < long_ma:
            return "SELL"
        else:
            return None

    def run(self, quantity: float = 0.001):
        self.logger.info(f"Starting bot for {self.symbol}")
        while True:
            klines = self.get_klines()
            closes = [float(k[4]) for k in klines]
            signal = self.calculate_signals(closes)
            if signal == "BUY":
                self.place_order(Client.SIDE_BUY, quantity)
            elif signal == "SELL":
                self.place_order(Client.SIDE_SELL, quantity)
            time.sleep(60)


if __name__ == "__main__":
    API_KEY = os.getenv("BINANCE_API_KEY")
    API_SECRET = os.getenv("BINANCE_API_SECRET")
    if not API_KEY or not API_SECRET:
        raise SystemExit("Please set BINANCE_API_KEY and BINANCE_API_SECRET environment variables")

    bot = BinanceFuturesBot(api_key=API_KEY, api_secret=API_SECRET, symbol="BTCUSDT")
    bot.run(quantity=0.001)
