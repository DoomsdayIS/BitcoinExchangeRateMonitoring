# Bitcoin exchange rate monitoring

## Описание проекта

Данный проект реализует отслеживание курса криптовалюты Bitcoin на таких биржах как Binance, ByBit, KuCoin. Изменения курса сохраняются в БД PostgreSQL. Настроены отчеты на почту и уведомления в консоль, триггер - повышения курса за задданный интервал более чем на заданный процент.
Проект развертывается с помощью docker-compose

## Установка
1. Склонируйте репозиторий
``` sh
$ git clone https://github.com/DoomsdayIS/BitcoinExchangeRateMonitoring
```

2. Создайте env файлы, для размещения переменных окружения

```
echo > .env
mkdir postgres; cd postgres; echo > .env
```

3. Установите и запустите Docker

## Использование
1. Конфигурация запуска

В файле app_config.json укажите желаемые настройки:
 * частоту работы программы (interval : int) в минутах
 * тип уведомлений "test" или "prod"
 * количество bitcoin
 * порог изменения для отправки уведомления (notification_threshold: float)

Пример: 
```json
{
    "interval": 1,
    "notification_mode": "test",
    "bitcoin_amount": 3,
    "notification_threshold": 0.03
}
```
2. Необходимые переменные окружения для работ
python-app
```
SENDER_EMAIL={YOUR EMAIL}
EMAIL_PASSWORD={YOUR_EMAIL_PASSWORD}
DATABASE_URL=postgres://postgres:{YOUR_PSQL_PASSWORD}@postgres:5432/postgres
PYTHONPATH=":/usr/app/"
```

postgres
```
POSTGRES_PASSWORD={YOUR_PSQL_PASSWORD}
```

3. Docker-compose up

## Ожидаемый результат
* Результат сборки:

![docker-compose](https://github.com/DoomsdayIS/BitcoinExchangeRateMonitoring/blob/master/images/3.png ) 

* База Данных:

![DB](https://github.com/DoomsdayIS/BitcoinExchangeRateMonitoring/blob/master/images/2.png) 

* Уведомление в консоль:

![test](https://github.com/DoomsdayIS/BitcoinExchangeRateMonitoring/blob/master/images/4.png)

* Уведомление на почту:

![prod](https://github.com/DoomsdayIS/BitcoinExchangeRateMonitoring/blob/master/images/5.png)
![prod_2](https://github.com/DoomsdayIS/BitcoinExchangeRateMonitoring/blob/master/images/6.png) 


