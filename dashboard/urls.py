from django.urls import path
from . import views

urlpatterns = [
    path('home/', views.home, name='home'),
    path('add_expense_view/', views.add_expense_view, name='add_expense_view'),
    path('add_expense/', views.add_expense, name='add_expense'),
    path('add_participants/', views.add_participants, name='add_participants'),
    path('delete_participant/',views.delete_participant,name='delete_participant'),
    path('add_sub_expense/', views.add_sub_expense, name='add_sub_expense'),
    path('update-sub-expense/', views.update_sub_expense, name='update_sub_expense'),
    path('delete_sub_expense/', views.delete_sub_expense, name='delete_sub_expense'),
    path('get-sub-expenses/<int:expense_id>/', views.get_sub_expenses, name='get_sub_expenses'),
    path('get_expense_distribution/<int:expense_id>/', views.get_expense_distribution, name='get_expense_distribution'),
    path('get_settlements/<int:expense_id>/', views.get_settlements, name='get_settlements'),
    path('get-user-balance/<int:expense_id>/<str:participant_name>/', views.get_user_balance, name='get_user_balance'),
    path('get-expenses/',views.get_expenses,name='get-expenses'),
    path('get-expense-categories/',views.get_expense_categories,name='get_expense_categories'),
    path('get-monthly-expense-count/',views.get_monthly_expense_count,name='get_monthly_expense_count'),
    path('get-expense-details/<int:expense_id>/',views.get_expense_details,name='get_expense_details'),
    path('edit-expense/<int:expense_id>/',views.edit_expense_view,name='edit_expense_view'),
    path('get-expense-graph-data/<int:expense_id>/',views.get_expense_graph_data,name='get_expense_graph_data'),
    path('get-debt-settlement/<int:expense_id>/',views.get_minimum_transactions_for_debt_settlement,name='get_minimum_transactions_for_debt_settlement')
]
