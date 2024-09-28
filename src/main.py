import asyncio
import json
import os
import time

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
    with open('app_config.json') as config_file:
        config = json.load(config_file)
        expected_frequency = int(config['interval'])
        test_mode = True if config['notification_mode'] == 'test' else False
        bitcoin_amount = float(config['bitcoin_amount'])
        notification_threshold = float(config['notification_threshold'])

    manager = Manager(exchanges=[Kucoin(symbols=['BTC-USDT', 'ETH-BTC']),
                                 Bybit(symbols=['BTCUSDT', 'ETHBTC']),
                                 Binance(symbols=['BTCUSDT', 'ETHBTC', 'DOGEBTC', 'SOLBTC'])],
                      job_interval=expected_frequency,
                      bitcoin_amount=bitcoin_amount,
                      notify_provider=EmailNotification(notification_threshold=notification_threshold,
                                                        email_address=EMAIL_ADDRESS,
                                                        email_password=EMAIL_PASSWORD,
                                                        contacts=[EMAIL_ADDRESS],
                                                        test_mode=test_mode))

    scheduler = AsyncIOScheduler()
    scheduler.add_job(manager.job, 'interval', minutes=expected_frequency)
    scheduler.start()
    while True:
        await asyncio.sleep(1000)


if __name__ == '__main__':
    print(DATABASE_URL)
    while True:
        try:
            run_async(init_database())
            break
        except Exception as e:
            print('Waiting untilll a database is up...')
            print(e)
            time.sleep(30)
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        pass
