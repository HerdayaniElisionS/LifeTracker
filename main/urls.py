from django.urls import path
from . import views


urlpatterns = [
    #authentication
    path('register/', views.register, name='register'),
    path('login/', views.login_user, name='login'),
    path('logout/', views.logout_user, name='logout'),
    
    # Pages
    path('', views.dashboard, name='dashboard'),
    path('expenses/', views.expenses_page, name='expenses'),
    path('planner/', views.planner_page, name='planner'),
    path('planner/<str:date_str>/', views.planner_page, name='planner_page'),

    # Actions - Budget & Expenses
    path('update-budget/', views.update_budget, name='update_budget'),
    path('add-expense/', views.add_expense, name='add_expense'),
    path('delete-expense/<int:pk>/', views.delete_expense, name='delete_expense'),

    # Actions - Schedule 
    path('add-schedule/', views.add_schedule_event, name='add_schedule_event'), 
    path('delete-schedule/<int:pk>/', views.delete_schedule_event, name='delete_schedule_event'),

    # Actions - Todos
    path('add-todo/', views.add_todo, name='add_todo'),
    path('delete-todo/<int:pk>/', views.delete_todo, name='delete_todo'),
    path('toggle-todo/<int:pk>/', views.toggle_todo, name='toggle_todo'),

    # Actions - Reminders
    path('add-reminder/', views.add_reminder, name='add_reminder'),
    path('delete-reminder/<int:pk>/', views.delete_reminder, name='delete_reminder'),
    path('toggle-reminder/<int:pk>/', views.toggle_reminder, name='toggle_reminder'),
]