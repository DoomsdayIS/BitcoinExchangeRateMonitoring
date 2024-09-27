import asyncio
import os

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from dotenv import load_dotenv
from tortoise import Tortoise, run_async

from manager import Manager
from notification_provider.notification_provider import EmailNotification
from stock_exchange.stock_exchange import Kucoin, Bybit, Binance

load_dotenv()

ACCEPTABLE_FREQUENCIES = [1, 3, 5, 15, 30]
EMAIL_ADDRESS = os.environ.get('SENDER_EMAIL')
EMAIL_PASSWORD = os.environ.get('EMAIL_PASSWORD')
DATABASE_URL = os.environ.get('DATABASE_URL')


async def init_database():
    await Tortoise.init(
        db_url=DATABASE_URL,
        modules={"models": ["models"]}
    )
    await Tortoise.generate_schemas(safe=True)


async def main():
    while True:
        try:
            expected_frequency = int(
                input(f"Enter request frequency: Should be an integer from {ACCEPTABLE_FREQUENCIES} (minutes)\n"))
            current_bitcoin_amount = float(input(f"Enter current bitcoin amount:\n"))
            notification_type = input('Select the notification type: Email(e) or Console(c). For the email type, '
                                      'there must be environment variables SENDER_EMAIL and EMAIL_PASSWORD\n')
            if expected_frequency not in ACCEPTABLE_FREQUENCIES and notification_type in ('e', 'c'):
                raise ValueError
            manager = Manager(exchanges=[Kucoin(symbols=['BTC-USDT', 'ETH-BTC']),
                                         Bybit(symbols=['BTCUSDT', 'ETHBTC']),
                                         Binance(symbols=['BTCUSDT', 'ETHBTC', 'DOGEBTC', 'SOLBTC'])],
                              job_interval=expected_frequency,
                              bitcoin_amount=current_bitcoin_amount,
                              notify_provider=EmailNotification(notification_threshold=0.03,
                                                                email_address=EMAIL_ADDRESS,
                                                                email_password=EMAIL_PASSWORD,
                                                                contacts=[EMAIL_ADDRESS],
                                                                test_mode=True if notification_type == 'c' else False))
            break
        except (TypeError, ValueError):
            print("Please try again")

    scheduler = AsyncIOScheduler()
    scheduler.add_job(manager.job, 'interval', minutes=expected_frequency)
    scheduler.start()
    while True:
        await asyncio.sleep(1000)


if __name__ == '__main__':
    run_async(init_database())
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        pass
