import smtplib
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from aiosmtpd.controller import Controller
import asyncio
import json
from aiosmtpd.smtp import SMTP as Server, syntax
from abc import ABCMeta, abstractmethod
from src.stock_exchange.util import Kline


class NotificationProvider(metaclass=ABCMeta):
    def __init__(self, notification_threshold: float):
        self.notification_threshold = notification_threshold

    @abstractmethod
    def send_notification(self, klines: list[Kline], bitcoin_amount: float) -> None:
        pass


class EmailNotification(NotificationProvider):

    def __init__(self, notification_threshold: float, email_address: str, email_password: str, contacts: list[str]):
        super().__init__(notification_threshold)
        self.email_address = email_address
        self.email_password = email_password
        self.contacts = contacts

    @staticmethod
    def _add_info_to_dict(kline_dict: dict, kline: Kline, bitcoin_amount: float):
        kash = kline_dict.setdefault(kline.stock_exchange, {"kash": [], "trading_pairs": []})["kash"]
        kline_dict[kline.stock_exchange]["trading_pairs"].append(kline.symbol)
        kash.append({
            "price": kline.close_price,
            "percent_diff": kline.exchange_rate,
            "minmax":
                {
                    "min price": kline.min_price,
                    "max price": kline.max_price
                },
            "difference": (kline.close_price - kline.open_price) * bitcoin_amount,
            "total amount": bitcoin_amount * kline.close_price
        })

    def _create_kline_info(self, klines: list[Kline], bitcoin_amount: int) -> dict:
        kline_info = {}
        for kline in klines:
            if kline.exchange_rate > self.notification_threshold:
                EmailNotification._add_info_to_dict(kline_info, kline, bitcoin_amount)
        return kline_info

    def _create_message(self, klines_data: dict) -> MIMEMultipart:
        msg = MIMEMultipart('alternative')
        msg['From'] = self.email_address
        msg['To'] = ', '.join(self.contacts)
        msg['Subject'] = f'Exchange rate report: {klines_data['datetime']}'
        body = (
            f'Information about trading pairs that have increased by more than {self.notification_threshold} percent '
            f'in the last {klines_data['interval']} minutes')
        msg.attach(MIMEText(body, 'plain'))
        attachment = MIMEText(json.dumps(klines_data, indent=4))
        attachment.add_header('Content-Disposition', 'attachment',
                              filename="info.json")
        msg.attach(attachment)
        return msg

    def send_notification(self, klines: list[Kline], bitcoin_amount: int) -> None:
        kline_info = self._create_kline_info(klines, bitcoin_amount)
        if not kline_info:
            return
        kline_info['datetime'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        kline_info['interval'] = klines[0].kline_interval
        msg = self._create_message(kline_info)
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(self.email_address, self.email_password)
            smtp.sendmail(self.email_address, self.contacts, msg.as_string())
