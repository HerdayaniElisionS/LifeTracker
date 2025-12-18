from django.contrib import admin
from .models import Todo, Expense

admin.site.register(Todo)
admin.site.register(Expense)