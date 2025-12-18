from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from .models import Todo, Expense, MonthlyBudget, ScheduleItem, Reminder

CLASS_INPUT = "auth-input"

class CustomLoginForm(AuthenticationForm):
    username = forms.CharField(widget=forms.TextInput(attrs={
        'class': CLASS_INPUT, 'placeholder': 'Username'
    }))
    password = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': CLASS_INPUT, 'placeholder': 'Password'
    }))

class CustomRegisterForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['first_name', 'username'] 

    def __init__(self, *args, **kwargs):
        super(CustomRegisterForm, self).__init__(*args, **kwargs)
        
        self.fields['first_name'].required = True 
        
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = CLASS_INPUT 
            field.widget.attrs['placeholder'] = field.label 
            field.help_text = "" 

class MonthlyBudgetForm(forms.ModelForm):
    class Meta:
        model = MonthlyBudget
        fields = ['total_income', 'savings_goal']
        widgets = {
            'total_income': forms.NumberInput(attrs={
                'class': 'modern-input', 
                'placeholder': '0.00', 
                'step': '0.01',
                'min': '0'
            }),
            'savings_goal': forms.NumberInput(attrs={
                'class': 'modern-input', 
                'placeholder': '0.00', 
                'step': '0.01',
                'min': '0'
            }),
        }
    
    def clean_total_income(self):
        total_income = self.cleaned_data.get('total_income')
        if total_income is not None and total_income < 0:
            raise ValidationError("Income cannot be negative.") #Prevent negative value
        return total_income
    
    def clean_savings_goal(self):
        savings_goal = self.cleaned_data.get('savings_goal')
        if savings_goal is not None and savings_goal < 0:
            raise ValidationError("Savings goal cannot be negative.") # Prevent invalid goals
        return savings_goal

class ExpenseForm(forms.ModelForm):
    class Meta:
        model = Expense
        fields = ['title', 'amount', 'category', 'date']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'modern-input', 
                'placeholder': 'e.g., Coffee'
            }),
            'amount': forms.NumberInput(attrs={
                'class': 'modern-input', 
                'placeholder': '0.00', 
                'step': '0.01',
                'min': '0.01'
            }),
            'category': forms.Select(attrs={'class': 'modern-input'}),
            'date': forms.DateInput(attrs={
                'class': 'modern-input', 
                'type': 'date'
            }),
        }
    
    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        if amount is not None and amount <= 0:
            raise ValidationError("Amount must be greater than zero.") # Spending must be positive 
        return amount

class ReminderForm(forms.ModelForm):
    class Meta:
        model = Reminder
        fields = ['title', 'due_date', 'priority']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'glass-input', 
                'placeholder': 'Reminder...'
            }),
            'due_date': forms.DateTimeInput(attrs={
                'class': 'glass-input', 
                'type': 'datetime-local' # HTML datetime picker
            }),
            'priority': forms.Select(attrs={'class': 'glass-input'}),
        }

class TodoForm(forms.ModelForm):
    class Meta:
        model = Todo
        fields = ['title']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'glass-input', 
                'placeholder': 'Add task...'
            }),
        }

class ScheduleItemForm(forms.ModelForm):
    class Meta:
        model = ScheduleItem
        fields = ['title', 'start_time', 'end_time', 'date']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'glass-input', 
                'placeholder': 'Event Title...'
            }),
            'start_time': forms.TimeInput(attrs={
                'class': 'glass-input', 
                'type': 'time' #time picker
            }),
            'end_time': forms.TimeInput(attrs={
                'class': 'glass-input', 
                'type': 'time'
            }),
            'date': forms.DateInput(attrs={'type': 'hidden'}), # Controlled by UI/URL
        }