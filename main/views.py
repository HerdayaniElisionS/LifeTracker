import datetime
from datetime import datetime, timedelta, date
from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Sum
from django.utils import timezone
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from .models import MonthlyBudget, Expense, Todo, ScheduleItem, Reminder
from .forms import (
    TodoForm, ExpenseForm, MonthlyBudgetForm, ScheduleItemForm, ReminderForm,
    CustomLoginForm, CustomRegisterForm
)

# Authentication -------------------------------------------------------------------------------------------------------------------------
def register(request):
    if request.method == "POST":
        form = CustomRegisterForm(request.POST) 
        if form.is_valid():
            form.save() 
            messages.success(request, 'Account created! Please login.') 
            return redirect('login') 
    else:
        form = CustomRegisterForm() 
    return render(request, 'auth_register.html', {'form': form})

def login_user(request):
    if request.method == 'POST':
        form = CustomLoginForm(data=request.POST) 
        if form.is_valid():
            user = form.get_user() # Retrieve validated user
            login(request, user) # Start session
            response = HttpResponseRedirect(reverse("dashboard"))
            response.set_cookie('last_login', str(datetime.now())) # Persist login time in cookie
            return response
    else:
        form = CustomLoginForm()
    return render(request, 'auth_login.html', {'form': form})

def logout_user(request):
    logout(request) # Terminate session
    response = HttpResponseRedirect(reverse('login'))
    response.delete_cookie('last_login') # Clear tracking cookie
    return response

# Dashboard -------------------------------------------------------------------------------------------------------------------------
@login_required(login_url='/login/')
def dashboard(request):
    now = timezone.now() # Get current server time
    # Filter expenses by current month and year
    expenses = Expense.objects.filter(user=request.user, date__year=now.year, date__month=now.month)
    category_totals = {}
    for expense in expenses:
        category = expense.get_category_display() 
        category_totals[category] = category_totals.get(category, 0) + float(expense.amount) # Sum by category
    
    context = {
        'chart_labels': list(category_totals.keys()), # Keys for chart axis
        'chart_data': list(category_totals.values()), # Values for chart series
        'recent_todos': Todo.objects.filter(user=request.user, done=False).order_by('-created_time')[:5], # Get 5 latest pending
        'reminders': Reminder.objects.filter(user=request.user, is_completed=False).order_by('due_date')[:5], # Get 5 upcoming
        'todays_schedule': ScheduleItem.objects.filter(user=request.user, date=now.date()).order_by('start_time'), # Get today's events
        'total_spent': int(sum(category_totals.values())), # Grand total of expenses
        'current_month_name': now.strftime('%B'), # Format: "January", "February"
        'last_login': request.COOKIES.get('last_login', 'Never'), # Read from browser storage
    }
    return render(request, 'main/dashboard.html', context)
# Planner -------------------------------------------------------------------------------------------------------------------------------
@login_required(login_url='/login/')
def planner_page(request, date_str=None):
    if date_str:
        try:
            view_date = datetime.strptime(date_str, '%Y-%m-%d').date() # Parse URL date
        except ValueError:
            view_date = timezone.now().date() # Go back to today on bad format
    else:
        view_date = timezone.now().date() # Default to today

    context = {
        'view_date': view_date,
        'is_today': view_date == timezone.now().date(), # Check if viewing today
        'prev_day': (view_date - timedelta(days=1)).strftime('%Y-%m-%d'), # Calculate previous date
        'next_day': (view_date + timedelta(days=1)).strftime('%Y-%m-%d'), # Calc next date
        'schedule_items': ScheduleItem.objects.filter(user=request.user, date=view_date).order_by('start_time'),
        'reminders': Reminder.objects.filter(user=request.user).order_by('is_completed', 'due_date'),
        'simple_todos': Todo.objects.filter(user=request.user, created_time__date=view_date).order_by('done', '-created_time'),
        'schedule_form': ScheduleItemForm(initial={'date': view_date}), 
        'todo_form': TodoForm(), 
        'reminder_form': ReminderForm(initial={'due_date': view_date}), 
    }
    return render(request, 'main/planner.html', context)

# Expenses -------------------------------------------------------------------------------------------------------------------------------
@login_required(login_url='/login/')
def expenses_page(request):
    now = timezone.now()
    current_year = int(request.GET.get('year', now.year)) # Get year from URL or default
    current_month = int(request.GET.get('month', now.month)) # Get month from URL or default

    # Ensure budget record exists for selected month
    budget_obj, _ = MonthlyBudget.objects.get_or_create(user=request.user, year=current_year, month=current_month)
    expenses = Expense.objects.filter(user=request.user, date__year=current_year, date__month=current_month).order_by('-date')

    spendable = budget_obj.spendable_budget() # Income - Savings Goal (create monthly budger)
    total_spent = expenses.aggregate(Sum('amount'))['amount__sum'] or 0 # sum all spending 
    
    category_totals = {}
    for expense in expenses:
        cat = expense.get_category_display()
        category_totals[cat] = category_totals.get(cat, 0) + float(expense.amount)

    context = {
        'budget': budget_obj,
        'expenses': expenses,
        'spendable': int(spendable), 
        'total_spent': int(total_spent), 
        'remaining': int(spendable - total_spent), # Calc leftover cash
        'budget_form': MonthlyBudgetForm(instance=budget_obj), # Link form to record
        'expense_form': ExpenseForm(initial={'date': date(current_year, current_month, 1)}), # Default to month start
        'month_name': date(current_year, current_month, 1).strftime('%B'),
        'current_year': current_year, 'current_month': current_month,
        'chart_labels': list(category_totals.keys()),
        'chart_data': list(category_totals.values()),
    }
    return render(request, 'main/expenses.html', context)

# Add, Delete, toggle --------------------------------------------------------------------------------------------------------------------
@login_required(login_url='/login/')
def add_schedule_event(request):
    date_str = request.POST.get('view_date')
    if request.method == "POST":
        title = request.POST.get('title')
        start_str = request.POST.get('start_time')
        end_str = request.POST.get('end_time')

        if start_str and end_str:
            start_t = datetime.strptime(start_str, '%H:%M').time() # Convert str to time object
            end_t = datetime.strptime(end_str, '%H:%M').time() # Convert str to time object

            if end_t <= start_t:
                messages.error(request, "End time must be after start time.") # Validate duration
                return redirect('planner_page', date_str=date_str)

        form = ScheduleItemForm(request.POST)
        if form.is_valid(): 
            item = form.save(commit=False) # Hold save for manual fields
            item.user = request.user 
            item.date = datetime.strptime(date_str, '%Y-%m-%d').date() if date_str else timezone.now().date()
            item.save() # Commit to DB
        else:
            if title and start_str and end_str:
                ScheduleItem.objects.create(
                    user=request.user,
                    title=title,
                    start_time=start_str,
                    end_time=end_str,
                    date=datetime.strptime(date_str, '%Y-%m-%d').date() if date_str else timezone.now().date()
                )
                
    return redirect('planner_page', date_str=date_str if date_str else timezone.now().strftime('%Y-%m-%d'))

@login_required(login_url='/login/')
def toggle_reminder(request, pk):
    reminder = get_object_or_404(Reminder, pk=pk, user=request.user)
    reminder.is_completed = not reminder.is_completed 
    reminder.save()
    referer = request.META.get('HTTP_REFERER') # Get previous page URL
    return HttpResponseRedirect(referer) if referer else redirect('planner_page', date_str=timezone.now().strftime('%Y-%m-%d'))

@login_required(login_url='/login/')
def delete_reminder(request, pk):
    reminder = get_object_or_404(Reminder, pk=pk, user=request.user)
    reminder.delete() # Remove from DB
    referer = request.META.get('HTTP_REFERER')
    return HttpResponseRedirect(referer) if referer else redirect('planner_page', date_str=timezone.now().strftime('%Y-%m-%d'))

@login_required(login_url='/login/')
def add_reminder(request):
    date_str = request.POST.get('view_date', timezone.now().strftime('%Y-%m-%d'))
    if request.method == "POST":
        form = ReminderForm(request.POST)
        if form.is_valid():
            reminder = form.save(commit=False)
            reminder.user = request.user # Link to current user
            reminder.save()
    return redirect('planner_page', date_str=date_str)

@login_required(login_url='/login/')
def add_todo(request):
    date_str = request.POST.get('view_date', timezone.now().strftime('%Y-%m-%d'))
    if request.method == "POST":
        form = TodoForm(request.POST)
        if form.is_valid(): 
            todo = form.save(commit=False)
            todo.user = request.user
            todo.created_time = datetime.strptime(date_str, '%Y-%m-%d') # Tag to specific date
            todo.save()
    return redirect('planner_page', date_str=date_str)

@login_required(login_url='/login/')
def toggle_todo(request, pk):
    todo = get_object_or_404(Todo, pk=pk, user=request.user)
    todo.done = not todo.done # Mark complete/incomplete
    todo.save()
    referer = request.META.get('HTTP_REFERER')
    return HttpResponseRedirect(referer) if referer else redirect('planner_page', date_str=timezone.now().strftime('%Y-%m-%d'))

@login_required(login_url='/login/')
def delete_todo(request, pk):
    get_object_or_404(Todo, pk=pk, user=request.user).delete() 
    referer = request.META.get('HTTP_REFERER')
    return HttpResponseRedirect(referer) if referer else redirect('planner_page', date_str=timezone.now().strftime('%Y-%m-%d'))

@login_required(login_url='/login/')
def delete_schedule_event(request, pk):
    get_object_or_404(ScheduleItem, pk=pk, user=request.user).delete()
    referer = request.META.get('HTTP_REFERER')
    return HttpResponseRedirect(referer) if referer else redirect('planner_page', date_str=timezone.now().strftime('%Y-%m-%d'))

@login_required(login_url='/login/')
def add_expense(request):
    if request.method == "POST":
        form = ExpenseForm(request.POST)
        if form.is_valid():
            expense = form.save(commit=False)
            expense.user = request.user
            expense.save()
            return redirect(f'/expenses/?year={expense.date.year}&month={expense.date.month}') # Redirect to correct month
    return redirect('expenses')

@login_required(login_url='/login/')
def delete_expense(request, pk):
    exp = get_object_or_404(Expense, pk=pk, user=request.user)
    y, m = exp.date.year, exp.date.month # Store date for redirect before delete
    exp.delete()
    return redirect(f'/expenses/?year={y}&month={m}')

@login_required(login_url='/login/')
def update_budget(request):
    if request.method == "POST":
        year = request.POST.get('year')
        month = request.POST.get('month')
        budget = get_object_or_404(MonthlyBudget, user=request.user, year=year, month=month)
        form = MonthlyBudgetForm(request.POST, instance=budget) 
        if form.is_valid(): form.save()
        return redirect(f'/expenses/?year={year}&month={month}')
    return redirect('expenses')