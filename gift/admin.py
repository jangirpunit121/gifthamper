from django.contrib import admin
from .models import CustomUser, Product, Cart, Order, OrderItem, ReturnRequest

admin.site.register(CustomUser)
admin.site.register(Product)
admin.site.register(Cart)
admin.site.register(Order)
admin.site.register(OrderItem)
admin.site.register(ReturnRequest)