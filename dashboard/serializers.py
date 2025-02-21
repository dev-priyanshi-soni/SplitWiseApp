from rest_framework import serializers
from .models import ExpenseParticipants, Expense, SubExpenses, Settlement, Payments
from auth_app.models import User

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'full_name']

class ExpenseParticipantsSerializer(serializers.ModelSerializer):
    added_by = UserSerializer(read_only=True)
    
    class Meta:
        model = ExpenseParticipants
        fields = ['id', 'name', 'added_by']

class ExpenseSerializer(serializers.ModelSerializer):
    participants = ExpenseParticipantsSerializer(many=True, read_only=True)
    created_by = UserSerializer(read_only=True)
    
    class Meta:
        model = Expense
        fields = ['id', 'description', 'created_at', 'category', 'updated_on', 
                 'participants', 'created_by']

class SubExpensesSerializer(serializers.ModelSerializer):
    expense = ExpenseSerializer(read_only=True)
    users_to_pay = ExpenseParticipantsSerializer(many=True, read_only=True)
    paid_by = ExpenseParticipantsSerializer(read_only=True)
    paid_by_name = serializers.CharField(source='paid_by.name', read_only=True)
    paid_by_id = serializers.IntegerField(source='paid_by.id', read_only=True)
    
    class Meta:
        model = SubExpenses
        fields = ['id', 'description', 'amount', 'created_at', 'expense', 
                 'split_type', 'users_to_pay', 'paid_by', 'paid_by_name', 'paid_by_id',
                 'updated_at', 'split_completed']
        
class ExpenseDetailsSerializer(serializers.ModelSerializer):
    participants = ExpenseParticipantsSerializer(many=True, read_only=True)
    created_by = UserSerializer(read_only=True)
    sub_expenses = SubExpensesSerializer(many=True, read_only=True, source='subexpenses_set')
    
    class Meta:
        model = Expense
        fields = ['id', 'description', 'created_at', 'category', 'updated_on',
                 'participants', 'created_by', 'sub_expenses']

class SettlementSerializer(serializers.ModelSerializer):
    from_participant = UserSerializer(read_only=True)
    to_participant = UserSerializer(read_only=True)
    
    class Meta:
        model = Settlement
        fields = ['id', 'from_participant', 'to_participant', 'amount', 'date', 
                 'notes']

class PaymentsSerializer(serializers.ModelSerializer):
    expense = ExpenseSerializer(read_only=True)
    paid_by = UserSerializer(read_only=True)
    paid_to = UserSerializer(read_only=True)
    created_by = UserSerializer(read_only=True)
    
    class Meta:
        model = Payments
        fields = ['id', 'amount', 'expense', 'paid_by', 'paid_to', 'created_by',
                 'created_at', 'updated_at']
