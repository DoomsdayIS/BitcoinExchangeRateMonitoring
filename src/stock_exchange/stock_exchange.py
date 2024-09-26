import asyncio
from abc import abstractmethod, ABCMeta
from typing import List

import aiohttp

from src.stock_exchange.util import Kline, create_iso_datetime, crete_integer_interval, create_trade_pairs_title


class StockExchange(metaclass=ABCMeta):
    existing_intervals = {}

    def __init__(self, symbols: List[str], client: aiohttp.ClientSession = None):
        self.symbols = symbols
        self.client = client

    @abstractmethod
    async def get_server_time(self) -> int:
        """
        :return: Current server time in milliseconds (ms), e.g. 1727043000063
        """
        pass

    @abstractmethod
    async def _fetch_kline(self, symbol: str, interval: str, start_time: int):
        pass

    @abstractmethod
    def _create_kline(self, fetch_result) -> Kline:
        pass

    async def get_klines(self, interval_min: int) -> List[Kline]:
        """
        :param interval_min: Kline interval in minutes
        :return: List of Kline instances, one instance for every symbol in self.symbols
        """
        cur_time = await self.get_server_time()
        start_time = cur_time - (interval_min) * 60000
        interval = self.existing_intervals[interval_min]
        fetch_results = await asyncio.gather(
            *[self._fetch_kline(symbol, interval, start_time) for symbol in self.symbols])

        klines = []
        for result in fetch_results:
            try:
                kline = self._create_kline(result)
                klines.append(kline)
            except Exception:
                continue
        return klines

    @staticmethod
    def calculate_exchange_rate_percent(open_price: float, close_price: float) -> float:
        """
        Рассчитываем процент изменения курса за время kline_interval
        """
        return (close_price - open_price) * 100 / open_price


class Binance(StockExchange):
    existing_intervals = {
        1: "1m",
        3: "3m",
        5: "5m",
        15: "15m",
        30: "30m"
    }
    name = 'Binance'

    async def get_server_time(self) -> int:
        async with self.client.get("https://data-api.binance.vision/api/v3/time") as resp:
            response_json = await resp.json()
        return response_json['serverTime']

    async def _fetch_kline(self, symbol, interval, start_time):
        start_time -= 60000
        async with self.client.get("https://data-api.binance.vision/api/v3/klines",
                                   params={"symbol": symbol,
                                           "interval": interval,
                                           "startTime": start_time,
                                           "limit": 1}) as resp:
            response = await resp.json()
            response[0].extend([interval, symbol])
            return response

    def _create_kline(self, fetch_result) -> Kline:
        kline_info = fetch_result[0]
        prices = [round(float(price), 2) if kline_info[-1].startswith("BTC") else round(1 / float(price), 2) for price
                  in kline_info[1:5]]
        if kline_info[-1].startswith("BTC"):
            prices[1], prices[2] = prices[2], prices[1]
        return Kline(stock_exchange=self.name, symbol=create_trade_pairs_title(kline_info[-1]),
                     kline_interval=crete_integer_interval(kline_info[-2]),
                     kline_start_time=create_iso_datetime(kline_info[0]),
                     open_price=prices[0], close_price=prices[3],
                     max_price=prices[2], min_price=prices[1],
                     exchange_rate=self.calculate_exchange_rate_percent(
                         prices[0], prices[3]
                     ))


class Bybit(StockExchange):
    existing_intervals = {
        1: "1",
        3: "3",
        5: "5",
        15: "15",
        30: "30",
        60: "60",
        120: "120"
    }
    name = 'Bybit'

    async def get_server_time(self) -> int:
        async with self.client.get("https://api.bybit.com/v5/market/time") as resp:
            response_json = await resp.json()
        return response_json['time']

    async def _fetch_kline(self, symbol, interval, start_time):
        async with self.client.get("https://api.bybit.com/v5/market/kline",
                                   params={"category": "spot",
                                           "symbol": symbol,
                                           "interval": interval,
                                           "start": start_time,
                                           "limit": 1}) as resp:
            response = await resp.json()
            response['interval'] = interval
            return response

    def _create_kline(self, fetch_result) -> Kline:
        kline_info = fetch_result['result']['list'][0]
        prices = [
            round(float(price), 2) if fetch_result['result']['symbol'].startswith("BTC") else round(1 / float(price), 2)
            for price in kline_info[1:5]]
        if fetch_result['result']['symbol'].startswith("BTC"):
            prices[1], prices[2] = prices[2], prices[1]
        return Kline(stock_exchange=self.name, symbol=create_trade_pairs_title(fetch_result['result']['symbol']),
                     kline_interval=crete_integer_interval(fetch_result['interval']),
                     kline_start_time=create_iso_datetime(int(kline_info[0])),
                     open_price=prices[0], close_price=prices[3],
                     max_price=prices[2], min_price=prices[1],
                     exchange_rate=self.calculate_exchange_rate_percent(open_price=prices[0], close_price=prices[3]))


class Kucoin(StockExchange):
    existing_intervals = {
        1: "1min",
        3: "3min",
        5: "5min",
        15: "15min",
        30: "30min",
    }
    name = 'Kucoin'

    async def get_server_time(self) -> int:
        async with self.client.get("https://api.kucoin.com/api/v1/timestamp") as resp:
            response_json = await resp.json()
        return response_json['data']

    async def _fetch_kline(self, symbol: str, interval: str, start_time: int):
        async with self.client.get("https://api.kucoin.com/api/v1/market/candles",
                                   params={
                                       "symbol": symbol,
                                       "type": interval,
                                       "startAt": start_time // 1000 - 60,
                                   }) as resp:
            response = await resp.json()
            response['interval'] = interval
            response['symbol'] = symbol
        return response

    def _create_kline(self, fetch_result) -> Kline:
        kline_info = fetch_result['data'][-1]
        prices = [round(float(price), 2) if fetch_result['symbol'].startswith("BTC") else round(1 / float(price), 2)
                  for price in kline_info[1:5]]
        if fetch_result['symbol'].startswith("BTC"):
            prices[2], prices[3] = prices[3], prices[2]
        return Kline(stock_exchange=self.name, symbol=create_trade_pairs_title(fetch_result['symbol']),
                     kline_interval=crete_integer_interval(fetch_result['interval']),
                     kline_start_time=create_iso_datetime(int(kline_info[0]) * 1000),
                     open_price=prices[0], close_price=prices[1],
                     max_price=prices[3], min_price=prices[2],
                     exchange_rate=self.calculate_exchange_rate_percent(open_price=prices[0], close_price=prices[1]))
