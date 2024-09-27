import asyncio
import aiohttp
import itertools

from models import Kline as KlineModel
from src.notification_provider.notification_provider import NotificationProvider
from src.stock_exchange.stock_exchange import StockExchange
from stock_exchange.util import Kline


class Manager:

    def __init__(self, exchanges: list[StockExchange], job_interval: int, bitcoin_amount: float,
                 notify_provider: NotificationProvider):
        self.exchanges = exchanges
        self.job_interval = job_interval
        self.bitcoin_amount = bitcoin_amount
        self.notify_provider = notify_provider

    async def fetch_klines(self) -> list[Kline]:
        async with aiohttp.ClientSession() as client:
            for stock_exchange in self.exchanges:
                stock_exchange.client = client
            tasks = []
            async with asyncio.TaskGroup() as tg:
                for stock_exchange in self.exchanges:
                    task = tg.create_task(stock_exchange.get_klines(interval_min=self.job_interval))
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

    async def job(self) -> None:
        klines = await self.fetch_klines()
        self.notify_provider.send_notification(klines, self.bitcoin_amount)
        await Manager.save_klines_to_db(klines)
