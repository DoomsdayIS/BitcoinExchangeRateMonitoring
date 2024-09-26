import asyncio
import aiohttp
import itertools

from models import Kline as KlineModel
from stock_exchange.stock_exchange import Bybit, Binance, Kucoin
from stock_exchange.util import Kline


class Manager:
    exchanges = [Kucoin(symbols=['BTC-USDT', 'ETH-BTC']),
                 Bybit(symbols=['BTCUSDT', 'ETHBTC']),
                 Binance(symbols=['BTCUSDT', 'ETHBTC', 'DOGEBTC', 'SOLBTC'])]
    job_interval = None
    notification_threshold = 0.03
    bitcoin_amount = 3

    @staticmethod
    async def fetch_klines() -> list[Kline]:
        async with aiohttp.ClientSession() as client:
            for stock_exchange in Manager.exchanges:
                stock_exchange.client = client
            tasks = []
            async with asyncio.TaskGroup() as tg:
                for stock_exchange in Manager.exchanges:
                    task = tg.create_task(stock_exchange.get_klines(interval_min=Manager.job_interval))
                    tasks.append(task)
            klines = list(itertools.chain(*[task.result() for task in tasks]))
            return klines

    @staticmethod
    async def save_klines_to_db(klines: list[Kline]) -> None:
        await asyncio.gather(*[KlineModel.create(title_exchange=kline.stock_exchange,
                                                 trading_pairs=kline.symbol,
                                                 kline_length_min=kline.kline_interval,
                                                 kline_start_time=kline.kline_start_time,
                                                 open_price=kline.open_price,
                                                 close_price=kline.close_price,
                                                 max_price=kline.max_price,
                                                 min_price=kline.min_price,
                                                 percent_diff=kline.exchange_rate) for kline in klines])

    @staticmethod
    async def notify_user(klines: list[Kline]) -> None:
        pass

    @staticmethod
    async def job():
        klines = await Manager.fetch_klines()
        await Manager.save_klines_to_db(klines)
