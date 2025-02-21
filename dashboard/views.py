from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import Expense,SubExpenses,Settlement,ExpenseParticipants,Payments
from django.utils import timezone
from .validators import AddExpenseValidator,AddParticipantsValidator,AddSubExpenseValidator
from auth_app.models import User
from .utils import *
from .serializers import ExpenseSerializer, SubExpensesSerializer, SettlementSerializer,ExpenseDetailsSerializer
import json

@login_required
def home(request):
    context = {
        'user': request.user,
        'welcome_message': f'Welcome {request.user.username}!'
    }
    return render(request, 'dashboard/home.html', context)

@login_required
def add_expense_view(request):
    return render(request, 'dashboard/add_expense.html')

@login_required
def edit_expense_view(request,expense_id):
    context = get_edit_expense_context(expense_id)
    return render(request, 'dashboard/add_expense.html',{'context':context})

@login_required
def add_expense(request):
    try:
        if request.method == 'POST':
            req_body = request.body.decode('utf-8')
            body = json.loads(req_body)
            expense_descripion = body.get('description')
            expense_category = body.get('category')
        
            validator = AddExpenseValidator(
                description=expense_descripion,
                category=expense_category
            )
            
            expense_manager = ExpenseManager(request.user)
            status,data = expense_manager.create_expense(
                description=expense_descripion,
                category=expense_category,
            )
            if status:
                serialized_expense = ExpenseSerializer(data).data
                return JsonResponse({'Status':True,'Success': 'Expense added successfully','Data': serialized_expense})
            return JsonResponse({'Status':False,'Error': data})
        return JsonResponse({'Status':False,'Error': 'Invalid request method'})
    except Exception as ex:
        return JsonResponse({'Status':False,'Error':'Some Error Occurred','Message':str(ex)})

@login_required 
def add_participants(request):
    try:
        if request.method == 'POST':
            req_body = request.body.decode('utf-8')
            body = json.loads(req_body)
            expense_id = body.get('expense_id')
            expense_participants = body.get('participants')

            validator = AddParticipantsValidator(
                expense_participants=expense_participants
            )

            expense_manager = ExpenseManager(request.user)
            success, expense = expense_manager.get_expense(expense_id)
            if not success:
                return JsonResponse({'Status':False,'Error': expense})

            success, result = expense_manager.add_participant(
                expense_id=expense.id,
                participant_list=expense_participants
            )
            if not success:
                return JsonResponse({'Status':False,'Error': result})
            serialized_expense = ExpenseDetailsSerializer(expense).data
            return JsonResponse({'Status':True,'Success': 'Participants added successfully', 'Data': serialized_expense})
        return JsonResponse({'Status':False,'Error': 'Invalid request method'})
    except Exception as ex:
        return JsonResponse({'Status':False,'Error':'Some Error Occurred','Message':str(ex)})

@login_required
def delete_participant(request):
    try:
        if request.method == 'DELETE':
            req_body = request.body.decode('utf-8')
            body = json.loads(req_body)
            expense_id = body.get('expense_id')
            participant_id = body.get('participant_id')

            expense_manager = ExpenseManager(request.user)
            success, expense = expense_manager.get_expense(expense_id)
            if not success:
                return JsonResponse({'Status':False,'Error': expense})

            success, result = expense_manager.delete_participant(
                expense_id=expense.id,
                participant_id=participant_id
            )
            if not success:
                return JsonResponse({'Status':False,'Error': result})
            serialized_expense = ExpenseDetailsSerializer(expense).data
            return JsonResponse({'Status':True,'Success': 'Participant deleted successfully', 'Data': serialized_expense})
        return JsonResponse({'Status':False,'Error': 'Invalid request method'})
    except Exception as ex:
        return JsonResponse({'Status':False,'Error':'Some Error Occurred','Message':str(ex)})

@login_required
def add_sub_expense(request):
    try:
        if request.method == 'POST':
            req_body = request.body.decode('utf-8')
            body = json.loads(req_body)
            expense_id = body.get('expense_id')
            description = body.get('description')
            amount = Decimal(body.get('amount'))
            split_type = body.get('split_type')
            users_to_pay = body.get('users_to_pay')
            paid_by = body.get('paid_by')
            # split_type = mapper_for_split_choices.get(split_type)

            validator = AddSubExpenseValidator(
                expense_id=expense_id,
                description=description,
                amount=amount,
                split_type=split_type,
                users_to_pay=users_to_pay,
                paid_by=paid_by
            )

            expense_manager = ExpenseManager(request.user)
            success, expense = expense_manager.get_expense(expense_id)
            if not success:
                return JsonResponse({'Status':False,'Error': expense})

            sub_expense_manager = SubExpenseManager(request.user)
            success, sub_expense = sub_expense_manager.add_sub_expense(
                expense_id=expense_id,
                description=description,
                amount=amount,
                split_type=split_type,
                users_to_pay=users_to_pay,
                paid_by=paid_by
            )
            if not success:
                return JsonResponse({'Status':False,'Error': sub_expense})
            serialized_sub_expense = SubExpensesSerializer(sub_expense).data
            return JsonResponse({'Status':True,'Success': 'Sub expense added successfully','Data': serialized_sub_expense})
        return JsonResponse({'Status':False,'Error': 'Invalid request method'})
    except Exception as ex:
        return JsonResponse({'Status':False,'Error':'Some Error Occurred','Message':str(ex)})

@login_required
def update_sub_expense(request):
    try:
        if request.method == 'PUT':
            req_body = request.body.decode('utf-8')
            body = json.loads(req_body)
            sub_expense_id = body.get('sub_expense_id')
            description = body.get('description')
            amount = body.get('amount')
            if amount:
                amount = Decimal(amount)
            split_type = body.get('split_type')
            users_to_pay = body.get('users_to_pay')
            paid_by = body.get('paid_by')

            sub_expense_manager = SubExpenseManager(request.user)
            success, sub_expense = sub_expense_manager.update_sub_expense(
                sub_expense_id=sub_expense_id,
                description=description,
                amount=amount,
                split_type=split_type,
                users_to_pay=users_to_pay,
                paid_by=paid_by
            )
            if not success:
                return JsonResponse({'Status':False,'Error': sub_expense})
            serialized_sub_expense = SubExpensesSerializer(sub_expense).data
            return JsonResponse({'Status':True,'Success': 'Sub expense updated successfully', 'Data': serialized_sub_expense})
        return JsonResponse({'Status':False,'Error': 'Invalid request method'})
    except Exception as ex:
        return JsonResponse({'Status':False,'Error':'Some Error Occurred','Message':str(ex)})

@login_required
def delete_sub_expense(request):
    try:
        if request.method == 'DELETE':
            req_body = request.body
            body_data = req_body.decode("utf-8")
            body = json.loads(body_data)
            sub_expense_id = body.get('sub_expense_id')
            
            sub_expense_manager = SubExpenseManager(request.user)
            success, message = sub_expense_manager.delete_sub_expense(sub_expense_id)
            if not success:
                return JsonResponse({'Status':False,'Error': message})
            return JsonResponse({'Status':True,'Success': 'Sub expense deleted successfully'})
        return JsonResponse({'Status':False,'Error': 'Invalid request method'})
    except Exception as ex:
        return JsonResponse({'Status':False,'Error':'Some Error Occurred','Message':str(ex)})

@login_required
def get_sub_expenses(request, expense_id):
    try:
        if request.method == 'GET':
            sub_expense_manager = SubExpenseManager(request.user)
            success, sub_expenses = sub_expense_manager.get_all_sub_expenses(expense_id)
            if not success:
                return JsonResponse({'Status':False,'Error': sub_expenses})
            return JsonResponse({'Status':True,'Data':sub_expenses})
        return JsonResponse({'Status':False,'Error': 'Invalid request method'})
    except Exception as ex:
        return JsonResponse({'Status':False,'Error':'Some Error Occurred','Message':str(ex)})

@login_required
def get_expense_distribution(request, expense_id):
    try:
        if request.method == 'GET':
            settlement_manager = SettlementManager(request.user)
            success, distribution = settlement_manager.get_expense_distribution(expense_id)
            if not success:
                return JsonResponse({'Status':False,'Error': distribution})
            return JsonResponse({'Status':True,'data': {k: str(v) for k,v in distribution.items()}})
        return JsonResponse({'Status':False,'Error': 'Invalid request method'})
    except Exception as ex:
        return JsonResponse({'Status':False,'Error':'Some Error Occurred','Message':str(ex)})

@login_required
def get_settlements(request, expense_id):
    try:
        if request.method == 'GET':
            settlement_manager = SettlementManager(request.user)
            success, settlements = settlement_manager.calculate_settlements(expense_id)
            if not success:
                return JsonResponse({'Status':False,'Error': settlements})
            # Convert Decimal to string for JSON serialization
            for settlement in settlements['settlements']:
                settlement['amount'] = str(settlement['amount'])
            for record in settlements['expense_records']:
                record['amount'] = str(record['amount'])
            return JsonResponse({'Status':True,'data': settlements})
        return JsonResponse({'Status':False,'Error': 'Invalid request method'})
    except Exception as ex:
        return JsonResponse({'Status':False,'Error':'Some Error Occurred','Message':str(ex)})

@login_required
def get_expenses(request):
    try:
        if request.method == 'GET':
            page = int(request.GET.get('page', 1))
            limit = int(request.GET.get('limit', 10))
            
            offset = (page - 1) * limit
            
            total_expenses = Expense.objects.filter(created_by=request.user).count()
            total_pages = (total_expenses + limit - 1) // limit
            
            expenses = Expense.objects.filter(created_by=request.user).order_by('-created_at')[offset:offset + limit]
            
            serialized_expenses = ExpenseSerializer(expenses, many=True).data
            
            has_next = page < total_pages
            has_prev = page > 1
            
            response_data = {
                'Status': True,
                'data': {
                    'expenses': serialized_expenses,
                    'pagination': {
                        'total_pages': total_pages,
                        'current_page': page,
                        'has_next': has_next,
                        'has_prev': has_prev,
                        'total_records': total_expenses
                    }
                }
            }
            
            return JsonResponse(response_data)
            
        return JsonResponse({'Status':False,'Error': 'Invalid request method'})
    except Exception as ex:
        return JsonResponse({'Status':False,'Error':'Some Error Occurred','Message':str(ex)})
    
@login_required
def get_expense_categories(request):
    try:
        if request.method == 'GET':
            today = timezone.now()
            month_start = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            if today.month == 12:
                month_end = today.replace(year=today.year + 1, month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
            else:
                month_end = today.replace(month=today.month + 1, day=1, hour=0, minute=0, second=0, microsecond=0)

            expenses = Expense.objects.filter(
                created_by=request.user,
                created_at__gte=month_start,
                created_at__lt=month_end
            )
            
            category_totals = {}
            
            for expense in expenses:
                category = expense.category
                sub_expenses = SubExpenses.objects.filter(expense=expense)
                category_total = sum(sub_expense.amount for sub_expense in sub_expenses)
                
                if category in category_totals:
                    category_totals[category] += category_total
                else:
                    category_totals[category] = category_total

            categories = list(category_totals.keys())
            amounts = [float(amount) for amount in category_totals.values()]

            response_data = {
                'Status': True,
                'data': {
                    'categories': categories,
                    'amounts': amounts
                }
            }
            
            return JsonResponse(response_data)

        return JsonResponse({'Status': False, 'Error': 'Invalid request method'})
    except Exception as ex:
        return JsonResponse({'Status': False, 'Error': 'Some Error Occurred', 'Message': str(ex)})

@login_required
def get_monthly_expense_count(request):
    try:
        if request.method == 'GET':
            today = timezone.now()
            year_start = today.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
            
            expenses = Expense.objects.filter(
                created_by=request.user,
                created_at__gte=year_start,
                created_at__lte=today
            )
            
            monthly_totals = {i: 0 for i in range(1, 13)}
            
            for expense in expenses:
                month = expense.created_at.month
                sub_expenses = SubExpenses.objects.filter(expense=expense)
                month_total = sum(sub_expense.amount for sub_expense in sub_expenses)
                monthly_totals[month] += float(month_total)
            
            months = list(monthly_totals.keys())
            amounts = list(monthly_totals.values())
            
            response_data = {
                'Status': True,
                'data': {
                    'months': months,
                    'amounts': amounts
                }
            }
            
            return JsonResponse(response_data)
            
        return JsonResponse({'Status': False, 'Error': 'Invalid request method'})
    except Exception as ex:
        return JsonResponse({'Status': False, 'Error': 'Some Error Occurred', 'Message': str(ex)})

@login_required
def get_expense_details(request,expense_id):
    return render(request, 'dashboard/view_expenses_details.html')

@login_required
def get_user_balance(request, expense_id, participant_name):
    try:
        if request.method == 'GET':
            settlement_manager = SettlementManager(request.user)
            success, data = settlement_manager.get_user_balance(expense_id=expense_id,participant_name=participant_name)
            if not success:
                return JsonResponse({'Status': False, 'Error': data})
            return JsonResponse({'Status':True,'Data':data})
        return JsonResponse({'Status': False, 'Error': 'Invalid request method'})
    except Exception as ex:
        return JsonResponse({'Status': False, 'Error': 'Some Error Occurred', 'Message': str(ex)})

@login_required
def get_expense_graph_data(request, expense_id):
    try:
        if request.method == 'GET':
            settlement_manager = SettlementManager(request.user)
            success, data = settlement_manager.get_expense_graph_data(expense_id=expense_id)
            if not success:
                return JsonResponse({'Status': False, 'Error': data})
            return JsonResponse({'Status':True,'Data':data})
        return JsonResponse({'Status': False, 'Error': 'Invalid request method'})
    except Exception as ex:
        return JsonResponse({'Status': False, 'Error': 'Some Error Occurred', 'Message': str(ex)})

@login_required
def get_minimum_transactions_for_debt_settlement(request,expense_id):
    try:
        if request.method == 'GET':
            settlement_manager = SettlementManager(request.user)
            success, data = settlement_manager.get_minimum_transactions_for_debt_settlement(expense_id=expense_id)
            if not success:
                return JsonResponse({'Status': False, 'Error': data})
            return JsonResponse({'Status':True,'Data':data})
        return JsonResponse({'Status': False, 'Error': 'Invalid request method'})
    except Exception as ex:
        return JsonResponse({'Status': False, 'Error': 'Some Error Occurred', 'Message': str(ex)})
    