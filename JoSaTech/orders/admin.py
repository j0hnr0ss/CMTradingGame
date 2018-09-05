from django.contrib import admin
from .models import Order, Trade, Price

admin.site.register(Order)
admin.site.register(Trade)
admin.site.register(Price)