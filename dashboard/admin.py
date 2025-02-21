# Register your models here.
from django.contrib import admin
from .models import Expense, ExpenseParticipants, SubExpenses, Settlement, Payments

@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ('id', 'description', 'category', 'created_by', 'created_at', 'updated_on')
    list_filter = ('category', 'created_at', 'updated_on', 'created_by', 'participants')
    search_fields = ('description', 'category', 'created_by__email', 'created_by__full_name', 'participants__name')
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)
    filter_horizontal = ('participants',)

@admin.register(ExpenseParticipants)
class ExpenseParticipantsAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'added_by')
    list_filter = ('added_by', 'name')
    search_fields = ('name', 'added_by__email', 'added_by__full_name')
    ordering = ('id',)

@admin.register(SubExpenses)
class SubExpensesAdmin(admin.ModelAdmin):
    list_display = ('id', 'expense', 'description', 'amount', 'split_type', 'paid_by', 'split_completed', 'created_at', 'updated_at')
    list_filter = ('split_completed', 'split_type', 'created_at', 'updated_at', 'expense__category', 'users_to_pay')
    search_fields = ('description', 'expense__description', 'paid_by', 'amount', 'users_to_pay__name')
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)
    filter_horizontal = ('users_to_pay',)

@admin.register(Settlement)
class SettlementAdmin(admin.ModelAdmin):
    list_display = ('id', 'from_participant', 'to_participant', 'amount', 'date')
    list_filter = ('date', 'from_participant', 'to_participant')
    search_fields = ('from_participant__username', 'to_participant__username', 'amount', 'notes')
    date_hierarchy = 'date'
    ordering = ('-date',)

@admin.register(Payments)
class PaymentsAdmin(admin.ModelAdmin):
    list_display = ('id', 'amount', 'expense', 'paid_by', 'paid_to', 'created_by', 'created_at', 'updated_at')
    list_filter = ('created_at', 'updated_at', 'paid_by', 'paid_to', 'created_by', 'expense')
    search_fields = ('amount', 'expense__description', 'paid_by__username', 'paid_to__username', 'created_by__username')
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)
