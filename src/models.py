from tortoise import fields
from tortoise.models import Model


class Kline(Model):
    id = fields.IntField(primary_key=True)
    title_exchange = fields.CharField(max_length=40)
    trading_pairs = fields.CharField(max_length=15)
    kline_length_min = fields.IntField()
    kline_start_time = fields.DatetimeField()
    open_price = fields.FloatField()
    close_price = fields.FloatField()
    min_price = fields.FloatField()
    max_price = fields.FloatField()
    percent_diff = fields.FloatField()

    class Meta:
        table = "klines"
        table_description = "This table contains info about all processed klines"

    def __str__(self):
        return (f"{self.title_exchange}: {self.trading_pairs}. "
                f"Kline started in {self.kline_start_time}  and lasted {self.kline_interval} minutes")
