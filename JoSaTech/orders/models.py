from django.contrib.auth.models import Permission, User
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator

class Order(models.Model):
    order_id = models.PositiveIntegerField(default=0)
    user = models.ForeignKey(User, default=1)
    fund_name = models.CharField(max_length=250)
    share_name = models.CharField(max_length=100)
    quantity = models.PositiveIntegerField(max_length=8, validators=[MinValueValidator(1), MaxValueValidator(500000)])
    price = models.FloatField(max_length=8, validators=[MinValueValidator(0.1)])
    total_order = models.FloatField(max_length=8)
    buysell = models.CharField(max_length=4)
    timestamp = models.DateTimeField(auto_now_add=True)
    filled = models.IntegerField(max_length=8, default=0)

    def __str__(self):
        return str(self.id) + ' - ' + self.fund_name + ' - ' + self.share_name + ' - ' + str(self.total_order)

class Trade(models.Model):
    trade_id = models.PositiveIntegerField(default=0)
    share_name = models.CharField(max_length=100)
    quantity = models.PositiveIntegerField(max_length=8, validators=[MinValueValidator(1)])
    price = models.FloatField(max_length=8, validators=[MinValueValidator(0.1)])
    total_order = models.FloatField(max_length=8)
    selling_fund = models.CharField(max_length=250)
    buying_fund = models.CharField(max_length=250)
    selling_orderID = models.CharField(max_length=10)
    buying_orderID = models.CharField(max_length=10)
    index = models.FloatField(max_length=8)

    def __str__(self):
        return str(self.id) + ' - ' + self.share_name + ' - ' + str(self.total_order)

class Price(models.Model):
    share_name = models.CharField(max_length=100)
    close_price = models.FloatField(max_length=8)

    def __str__(self):
        return self.share_name + ' - ' + str(self.close_price)