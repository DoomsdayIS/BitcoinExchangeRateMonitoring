import os
import smtplib
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from dotenv import load_dotenv
from aiosmtpd.controller import Controller
import asyncio
import json
from aiosmtpd.smtp import SMTP as Server, syntax
from abc import ABCMeta, abstractmethod
from src.stock_exchange.util import Kline

load_dotenv()

EMAIL_ADDRESS = os.environ.get('SENDER_EMAIL')
EMAIL_PASSWORD = os.environ.get('EMAIL_PASSWORD')

contacts = [EMAIL_ADDRESS]


class NotificationProvider(metaclass=ABCMeta):
    def __init__(self, notification_threshold: float):
        self.notification_threshold = notification_threshold

    def process_klines(self, klines: list[Kline], bitcoin_amount: int) -> None:
        for kline in klines:
            if kline.exchange_rate > self.notification_threshold:
                self.send_notification(kline, bitcoin_amount)

    @abstractmethod
    def send_notification(self, kline: Kline, bitcoin_amount) -> None:
        pass


class EmailNotification(NotificationProvider):

    def __init__(self, notification_threshold: float, email_address: str, email_password: str, contacts: list[str]):
        super().__init__(notification_threshold)
        self.email_address = email_address
        self.email_password = email_password
        self.contacts = contacts

    def _create_message(self, kline: Kline, bitcoin_amount: int) -> MIMEMultipart:
        msg = MIMEMultipart('alternative')
        msg['From'] = self.email_address
        msg['To'] = ', '.join(self.contacts)
        msg['Subject'] = f'{kline.stock_exchange}: {kline.symbol}'
        body = (f'{kline.stock_exchange}: exchange rate {kline.symbol} has increased by {kline.exchange_rate} '
                f'percent in the last {kline.kline_interval} minutes')
        msg.attach(MIMEText(body, 'plain'))
        data = {"Exchange title": kline.stock_exchange,
                "trading_pair": kline.symbol,
                "kash":
                    {
                        "price": kline.close_price,
                        "minmax":
                            {
                                "min price": kline.min_price,
                                "max price": kline.max_price
                            }
                    },
                "difference": (kline.close_price - kline.open_price) * bitcoin_amount,
                "total amount": bitcoin_amount * kline.close_price,
                'datetime': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                }
        attachment = MIMEText(json.dumps(data, indent=4))
        attachment.add_header('Content-Disposition', 'attachment',
                              filename="info.json")
        msg.attach(attachment)
        return msg

    def send_notification(self, kline: Kline, bitcoin_amount: int) -> None:
        msg = self._create_message(kline, bitcoin_amount)
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(self.email_address, self.email_password)
            smtp.sendmail(self.email_address, self.contacts, msg.as_string())


email_notify = EmailNotification(0.03, EMAIL_ADDRESS, EMAIL_PASSWORD,
                                 [EMAIL_ADDRESS])
email_notify.send_notification(
    Kline(stock_exchange='Test market', symbol='BTCETH', kline_interval=1, kline_start_time='dfdf',
          open_price=10, close_price=11, max_price=11, min_price=1, exchange_rate=0.1), bitcoin_amount=3)
