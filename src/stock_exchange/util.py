from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class Kline:
    stock_exchange: str
    symbol: str
    kline_interval: int
    kline_start_time: str
    open_price: float
    close_price: float
    max_price: float
    min_price: float
    exchange_rate: float


def create_iso_datetime(ms_time: int) -> str:
    return datetime.fromtimestamp(ms_time // 1000).isoformat(sep=' ', timespec='seconds')


def crete_integer_interval(str_interval: str) -> int:
    return int(''.join(char for char in str_interval if char.isnumeric()))


def create_trade_pairs_title(string: str) -> str:
    string = ''.join(char for char in string if char.isalnum())
    if string.startswith('BTC'):
        return string[:3] + '-' + string[3:]
    return string[-3:] + '-' + string[:-3]
