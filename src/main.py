import asyncio

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from tortoise import Tortoise, run_async
from manager import Manager

ACCEPTABLE_FREQUENCIES = [1, 3, 5, 15, 30]


async def init_database():
    await Tortoise.init(
        db_url='postgres://postgres:mysecretpassword@localhost:5433/postgres',
        modules={"models": ["models"]}
    )
    await Tortoise.generate_schemas(safe=True)


async def main():
    while True:
        try:
            expected_frequency = int(
                input(f"Enter request frequency: Should be an integer from {ACCEPTABLE_FREQUENCIES} (minutes)\n"))
            if expected_frequency not in ACCEPTABLE_FREQUENCIES:
                raise ValueError
            Manager.job_interval = expected_frequency
            break
        except (TypeError, ValueError):
            print("Please enter a valid request frequency")

    scheduler = AsyncIOScheduler()
    scheduler.add_job(Manager.job, 'interval', minutes=expected_frequency)
    scheduler.start()
    while True:
        await asyncio.sleep(1000)


if __name__ == '__main__':
    run_async(init_database())
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        pass
