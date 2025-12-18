from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
import datetime

class MonthlyBudget(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE) # Link budget to specific user
    month = models.IntegerField()
    year = models.IntegerField()
    total_income = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    savings_goal = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    class Meta:
        unique_together = ('user', 'month', 'year') # Prevent multiple budgets for same user/month

    def __str__(self):
        return f"{self.user.username} - {self.month}/{self.year}"
    
    def spendable_budget(self):
        return self.total_income - self.savings_goal # Calc net amount for spending


class Expense(models.Model):
    CATEGORY_CHOICES = [
        ('FOOD', 'Food'),
        ('TRANSPORT', 'Transport'),
        ('SCHOOL', 'School'),
        ('UTILITIES', 'Utilities'),
        ('ENTERTAINMENT', 'Entertainment'),
        ('OTHER', 'Other'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=100)
    amount = models.DecimalField(max_digits=10, decimal_places=2) 
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='OTHER')
    date = models.DateField()
    created_time = models.DateTimeField(auto_now_add=True) # Date 

    def __str__(self):
        return f"{self.title} - ${self.amount}"

class Todo(models.Model):
    PRIORITY_CHOICES = [
        ('HIGH', 'High'),
        ('MEDIUM', 'Medium'),
        ('LOW', 'Low'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    done = models.BooleanField(default=False) # Completion status
    created_time = models.DateTimeField(auto_now_add=True)
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='MEDIUM')

    def __str__(self):
        return self.title

class Reminder(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    due_date = models.DateTimeField() # Target deadline
    is_completed = models.BooleanField(default=False)
    
    PRIORITY_CHOICES = [
        ('HIGH', 'High'),
        ('MEDIUM', 'Medium'),
        ('LOW', 'Low'),
    ]
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='MEDIUM')

    def __str__(self):
        return self.title

class ScheduleItem(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    date = models.DateField(default=timezone.now) 
    start_time = models.TimeField()
    end_time = models.TimeField()

    def __str__(self):
        return f"{self.date} | {self.start_time} - {self.title}"