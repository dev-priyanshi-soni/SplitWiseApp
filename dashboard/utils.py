from decimal import Decimal
from typing import Dict, List, Optional, Tuple, Union, Any
from django.db import transaction
from django.utils import timezone
from .models import Expense, ExpenseParticipants, SubExpenses, Settlement, Payments
from auth_app.models import User
from collections import defaultdict
import logging
from django.db.models import Count
from .serializers import ExpenseDetailsSerializer
import json

logger = logging.getLogger(__name__)

mapper_for_split_choices = {
    'perGroup':'G',
    'perPerson':'P'
}

def get_edit_expense_context(expense_id: int) -> Dict:
    """Get context data for editing an expense"""
    try:
        # Get expense details
        expense = Expense.objects.get(id=expense_id)
        expense_details = ExpenseDetailsSerializer(expense).data

        # Get participants data
        participants = ExpenseParticipants.objects.filter(expense=expense)
        participants_data = []
        people = []
        
        for participant in participants:
            participant_dict = {
                "id": participant.id,
                "name": participant.name,
                "added_by": {
                    "id": participant.added_by.id,
                    "username": participant.added_by.username,
                    "full_name": participant.added_by.get_full_name()
                }
            }
            participants_data.append(participant_dict)
            people.append(participant.name)

        # Get sub-expenses/costs data
        sub_expenses = SubExpenses.objects.filter(expense=expense)
        costs = []
        
        for sub_expense in sub_expenses:
            payers = []
            for user in sub_expense.users_to_pay.all():
                payer = {
                    "id": user.id,
                    "name": user.name,
                    "added_by": {
                        "id": user.added_by.id,
                        "username": user.added_by.username,
                        "full_name": user.added_by.get_full_name()
                    }
                }
                payers.append(payer)
            paid_by = {}
            if sub_expense.paid_by:
                paid_by = {
                    "id": sub_expense.paid_by.id,
                    "name": sub_expense.paid_by.name,
                    "added_by": {
                        "id": sub_expense.paid_by.added_by.id,
                        "username": sub_expense.paid_by.added_by.username,
                        "full_name": sub_expense.paid_by.added_by.get_full_name()
                    }
                }

            cost = {
                "type": "perPerson" if sub_expense.split_type == "P" else "perGroup",
                "amount": float(sub_expense.amount),
                "description": sub_expense.description,
                "payers": payers,
                "paidBy": paid_by,
                "isPaid": True if sub_expense.paid_by else False,
                "id": sub_expense.id,
                "expenseId": expense.id,
            }
            costs.append(cost)

        context = {
            "expense": expense_details,
            "costs": costs,
            "people": people,
            "participantsData": participants_data,
            "edit":True,
            "expense_description":expense.description,
            "expense_category":expense.category
        }
        
        return json.dumps(context)

    except Exception as e:
        logger.error(f"Error getting edit expense context: {str(e)}")
        return json.dumps({})

class BaseManager:
    """Base manager class with common functionality"""
    def __init__(self, user: User):
        self.user = user

    def _validate_ownership(self, obj: Any, error_msg: str) -> Tuple[bool, str]:
        """Validate if user owns/created the object"""
        try:
            if obj.created_by != self.user:
                return False, error_msg
            return True, "Success"
        except Exception as e:
            logger.error(f"Error validating ownership: {str(e)}")
            return False, str(e)

class ExpenseManager(BaseManager):
    def create_expense(self, description: str, category: str) -> Tuple[bool, Union[Expense, str]]:
        """Create a new expense"""
        try:
            existing_expense = Expense.objects.filter(
                description__iexact=description,
                category=category,
                created_by=self.user
            ).first()

            if existing_expense:
                return False, f"An expense with description '{description}' and category '{category}' already exists"

            expense = Expense.objects.create(
                description=description,
                category=category, 
                created_by=self.user,
                updated_on=timezone.now()
            )
            return True, expense
        except Exception as e:
            logger.error(f"Error creating expense: {str(e)}")
            return False, str(e)

    def get_expense(self, expense_id: int) -> Tuple[bool, Union[Expense, str]]:
        """Get single expense by ID"""
        try:
            expense = Expense.objects.get(id=expense_id)
            return True, expense
        except Expense.DoesNotExist:
            logger.error(f"Expense with id {expense_id} not found")
            return False, f"Expense with id {expense_id} not found"
        except Exception as e:
            logger.error(f"Error getting expense: {str(e)}")
            return False, str(e)

    def get_all_expenses(self) -> Tuple[bool, Union[List[Expense], str]]:
        """Get all expenses for current user"""
        try:
            expenses = Expense.objects.filter(created_by=self.user)
            return True, expenses
        except Exception as e:
            logger.error(f"Error getting all expenses: {str(e)}")
            return False, str(e)

    def get_expense_by_category(self, category: str) -> Tuple[bool, Union[List[Expense], str]]:
        """Get expenses filtered by category"""
        try:
            expenses = Expense.objects.filter(created_by=self.user, category=category)
            return True, expenses
        except Exception as e:
            logger.error(f"Error getting expenses by category: {str(e)}")
            return False, str(e)

    def update_expense(self, expense_id: int, description: str = None, category: str = None) -> Tuple[bool, Union[Expense, str]]:
        """Update an existing expense"""
        try:
            success, expense = self.get_expense(expense_id)
            if not success:
                return False, expense
                
            ownership_success, msg = self._validate_ownership(expense, "Only expense creator can update it")
            if not ownership_success:
                return False, msg
                
            if description:
                expense.description = description
            if category:
                expense.category = category
            expense.updated_on = timezone.now()
            expense.save()
            return True, expense
        except Exception as e:
            logger.error(f"Error updating expense: {str(e)}")
            return False, str(e)

    def delete_expense(self, expense_id: int) -> Tuple[bool, str]:
        """Delete an expense and related data"""
        try:
            success, expense = self.get_expense(expense_id)
            if not success:
                return False, expense
                
            ownership_success, msg = self._validate_ownership(expense, "Only expense creator can delete it")
            if not ownership_success:
                return False, msg
                
            expense.delete()
            return True, "Success"
        except Exception as e:
            logger.error(f"Error deleting expense: {str(e)}")
            return False, str(e)

    def add_participant(self, expense_id: int, participant_list: list) -> Tuple[bool, Union[ExpenseParticipants, str]]:
        """Add a participant to an expense"""
        try:
            success, expense = self.get_expense(expense_id)
            if not success:
                return False, expense
            participant = list()
            
            for participant_name in participant_list:
                if participant_name.lower() == self.user.full_name.lower():
                    return False, "Participant name cannot be same as expense creator"
                    
                existing = expense.participants.filter(name__iexact=participant_name).first()
                if existing:
                    continue

                participant_data, created = ExpenseParticipants.objects.get_or_create(
                    name=participant_name,
                    added_by=self.user
                )
                # Add participant to existing group-split sub-expenses
                group_split_expenses = SubExpenses.objects.filter(
                    expense_id=expense_id,
                    split_type='G'
                )
                for sub_expense in group_split_expenses:
                    sub_expense.users_to_pay.add(participant_data)
                participant.append(participant_data)
                expense.participants.add(participant_data)   
                        
            return True, participant
        except Exception as e:
            logger.error(f"Error adding participant: {str(e)}")
            return False, str(e)
    
    def delete_participant(self, expense_id: int, participant_id: int) -> Tuple[bool, Union[Dict, str]]:
        """Delete a participant from an expense"""
        try:
            expense = Expense.objects.get(id=expense_id)
            
            ownership_valid, msg = self._validate_ownership(expense, "You don't have permission to modify this expense")
            if not ownership_valid:
                return False, msg

            try:
                participant = ExpenseParticipants.objects.get(id=participant_id)
            except ExpenseParticipants.DoesNotExist:
                return False, "Participant not found"

            #when partcpant to remove is the only one who paid and has to pay in sub expenses
            sub_expenses_with_same_paidTo_paidBy = SubExpenses.objects.annotate(
                user_count=Count("users_to_pay")
            ).filter(
                expense_id=expense_id,
                paid_by=participant,
                user_count=1,
                users_to_pay=participant 
            )
            sub_expenses_with_same_paidTo_paidBy.delete()

            paid_by_sub_expenses = SubExpenses.objects.filter(expense=expense, paid_by=participant)
            if paid_by_sub_expenses.exists():
                paid_by_sub_expenses.update(paid_by=None)

            group_split_expenses = SubExpenses.objects.filter(
                expense_id=expense_id,
                users_to_pay=participant,
                split_completed=False,
            )
            if group_split_expenses.exists():
                for sub_expense in group_split_expenses:
                    sub_expense.users_to_pay.remove(participant)

            #records where no user to pay are left
            empty_user_expenses = SubExpenses.objects.annotate(
                user_count=Count('users_to_pay')
            ).filter(
                expense_id=expense_id,
                user_count=0
            )
            empty_user_expenses.delete()
            
            participant.delete()

            return True, "Success"
        except Expense.DoesNotExist:
            return False, f"Expense with id {expense_id} not found"
        except Exception as e:
            logger.error(f"Error deleting participant: {str(e)}")
            return False, str(e)
        
    def get_participants(self, expense_id: int) -> Tuple[bool, Union[List[ExpenseParticipants], str]]:
        """Get all participants for an expense"""
        try:
            success, expense = self.get_expense(expense_id)
            if not success:
                return False, expense
            return True, expense.participants.all()
        except Exception as e:
            logger.error(f"Error getting participants: {str(e)}")
            return False, str(e)

class SubExpenseManager(ExpenseManager):
    def get_sub_expense(self, sub_expense_id: int) -> Tuple[bool, Union[SubExpenses, str]]:
        """Get single sub-expense by ID"""
        try:
            sub_expense = SubExpenses.objects.get(id=sub_expense_id)
            return True, sub_expense
        except SubExpenses.DoesNotExist:
            logger.error(f"Sub expense with id {sub_expense_id} not found")
            return False, f"Sub expense with id {sub_expense_id} not found"
        except Exception as e:
            logger.error(f"Error getting sub expense: {str(e)}")
            return False, str(e)

    def get_all_sub_expenses(self, expense_id: int) -> Tuple[bool, Union[List[SubExpenses], str]]:
        """Get all sub-expenses for an expense"""
        try:
            success, expense = self.get_expense(expense_id)
            if not success:
                return False, expense
                
            ownership_success, msg = self._validate_ownership(expense, "Only expense creator can update it")
            if not ownership_success:
                return False, msg
            serialized_data = ExpenseDetailsSerializer(expense)
            return True, serialized_data.data
        except Exception as e:
            logger.error(f"Error getting all sub expenses: {str(e)}")
            return False, str(e)

    def get_user_sub_expenses(self, expense_id: int, participant_id: int) -> Tuple[bool, Union[List[SubExpenses], str]]:
        """Get sub-expenses for specific participant"""
        try:
            sub_expenses = SubExpenses.objects.filter(
                expense_id=expense_id,
                users_to_pay__id=participant_id
            )
            return True, sub_expenses
        except Exception as e:
            logger.error(f"Error getting user sub expenses: {str(e)}")
            return False, str(e)

    def add_sub_expense(
        self, 
        expense_id: int,
        description: str,
        amount: Decimal,
        split_type: str,
        users_to_pay: List[int],
        paid_by: str
    ) -> Tuple[bool, Union[SubExpenses, str]]:
        """Add a sub-expense to an expense"""
        try:
            if not users_to_pay:
                return False, "Must specify at least one user to pay"
            
            paid_by_user = ExpenseParticipants.objects.filter(id=paid_by)
            if not paid_by_user.exists():
                return False, f"This user is not a participant in this expense"
            paid_by_user = paid_by_user.last()
            
            # Check if sub expense already exists
            existing_sub_expense = SubExpenses.objects.filter(
                description__iexact=description,
                expense_id=expense_id,
            )
            
            if existing_sub_expense:
                return False, f"Sub expense '{description}' already exists for this expense"
                
            sub_expense = SubExpenses.objects.create(
                description=description,
                amount=amount,
                expense_id=expense_id,
                split_type=split_type,
                paid_by=paid_by_user,
                updated_at=timezone.now()
            )
            
            participants = ExpenseParticipants.objects.filter(id__in=users_to_pay)
            sub_expense.users_to_pay.set(participants)
            
            return True, sub_expense
        except Exception as e:
            logger.error(f"Error adding sub expense: {str(e)}")
            return False, str(e)

    def update_sub_expense(
        self,
        sub_expense_id: int,
        description: str = None,
        amount: Decimal = None,
        split_type: str = None,
        users_to_pay: List[str] = None,
        paid_by: str = None
    ) -> Tuple[bool, Union[SubExpenses, str]]:
        """Update a sub-expense"""
        try:
            success, sub_expense = self.get_sub_expense(sub_expense_id)
            if not success:
                return False, sub_expense
            
            if description:
                sub_expense.description = description
            if amount:
                sub_expense.amount = amount
            if split_type:
                sub_expense.split_type = split_type
            if users_to_pay:
                participants = ExpenseParticipants.objects.filter(
                    expense=sub_expense.expense,
                    name__in=users_to_pay
                )
                if participants.count() != len(users_to_pay):
                    return False, "One or more users are not participants in this expense"
                sub_expense.users_to_pay.set(participants)
            
            curr_payer_name = sub_expense.paid_by.name if sub_expense.paid_by else None
            if paid_by and paid_by != curr_payer_name:
                paid_by_user = ExpenseParticipants.objects.filter(
                    expense=sub_expense.expense,
                    name=paid_by
                ).first()
                if not paid_by_user:
                    return False, f"User {paid_by} is not a participant in this expense"
                sub_expense.paid_by = paid_by_user
            if not paid_by:
                sub_expense.paid_by = None                
            sub_expense.updated_at = timezone.now()
            sub_expense.save()
            return True, sub_expense
        except Exception as e:
            logger.error(f"Error updating sub expense: {str(e)}")
            return False, str(e)

    def delete_sub_expense(self, sub_expense_id: int) -> Tuple[bool, str]:
        """Delete a sub-expense"""
        try:
            success, sub_expense = self.get_sub_expense(sub_expense_id)
            if not success:
                return False, sub_expense
                
            if sub_expense.split_completed:
                return False, "Cannot delete a completed sub-expense"
            sub_expense.delete()
            return True, "Success"
        except Exception as e:
            logger.error(f"Error deleting sub expense: {str(e)}")
            return False, str(e)

class SettlementManager(BaseManager):
    def __init__(self, user):
        """Initialize settlement manager with user"""
        super().__init__(user)

    def get_expense_graph_data(self, expense_id: int) -> Tuple[bool, Union[Dict, str]]:
        """Get graph data showing borrowings and lendings between participants"""
        try:
            expense = Expense.objects.get(id=expense_id)
            participants = ExpenseParticipants.objects.filter(expense=expense)
            
            nodes = []
            participant_balances = {}  # Track total balance for each participant
            
            for idx, participant in enumerate(participants, start=1):
                nodes.append({
                    'id': idx,
                    'label': participant.name,
                    'color': '#3498db'  
                })
                participant_balances[participant.name] = 0  

            edges = []
            participant_id_map = {p.name: idx for idx, p in enumerate(participants, start=1)}
            
            amount_map = {}
            
            sub_expenses = SubExpenses.objects.filter(expense=expense)
            for sub_expense in sub_expenses:
                if not sub_expense.paid_by:
                    continue
                    
                payer = sub_expense.paid_by
                amount_per_person = float(sub_expense.amount) if sub_expense.split_type == "P" else float(sub_expense.amount) / sub_expense.users_to_pay.count()
                
                for user in sub_expense.users_to_pay.all():
                    if user.name == payer.name:
                        if sub_expense.split_type == "G":
                            participant_balances[payer.name] += float(sub_expense.amount) - amount_per_person
                        else:
                            total_participants = len(sub_expense.users_to_pay.all())
                            money_to_get_from_gp_members = total_participants * float(amount_per_person)
                            participant_balances[payer.name] += money_to_get_from_gp_members - amount_per_person
                    else:
                        participant_balances[user.name] -= amount_per_person
                        
                        key = (participant_id_map[user.name], participant_id_map[payer.name])
                        if key in amount_map:
                            amount_map[key] = float(amount_map[key]) + amount_per_person
                        else:
                            amount_map[key] = amount_per_person

            for node in nodes:
                participant_name = next(p.name for p in participants if participant_id_map[p.name] == node['id'])
                balance = round(participant_balances[participant_name], 2)
                node['label'] = f"{participant_name}\n(₹{balance})"
                node['color'] = '#2ecc71' if balance >= 0 else '#e74c3c'

            for (from_id, to_id), total_amount in amount_map.items():
                edges.append({
                    'from': from_id,
                    'to': to_id,
                    'label': f'₹{round(total_amount, 2)}',
                    'arrows': 'to',
                    'color': {'color': '#e74c3c'}
                })

            return True, {
                'nodes': nodes,
                'edges': edges
            }
        except Expense.DoesNotExist:
            return False, "Expense not found"
        except Exception as e:
            logger.error(f"Error getting expense graph data: {str(e)}")
            return False, str(e)

    def get_user_balance(self, expense_id: int, participant_name: str) -> Tuple[bool, Union[Dict, str]]:
        """Get balance details for a specific user in an expense"""
        try:
            expense = Expense.objects.get(id=expense_id)
            participant = ExpenseParticipants.objects.filter(
                expense=expense,
                name=participant_name
            ).first()

            if not participant:
                return False, "Participant not found"

            to_pay_expenses = SubExpenses.objects.filter(
                expense=expense,
                users_to_pay=participant
            )

            paid_expenses = SubExpenses.objects.filter(
                expense=expense,
                paid_by=participant
            )

            to_give = {}
            for expense in to_pay_expenses:
                if expense.paid_by and expense.paid_by.name != participant_name:
                    payer_name = expense.paid_by.name
                    payers_count = expense.users_to_pay.count()
                    amount_per_person = expense.amount if expense.split_type == "P" else expense.amount / payers_count
                    
                    if payer_name in to_give:
                        to_give[payer_name] = float(to_give[payer_name]) + float(amount_per_person)
                    else:
                        to_give[payer_name] = float(amount_per_person)

            to_receive = {}
            for expense in paid_expenses:
                for user in expense.users_to_pay.all():
                    if user.name != participant_name:
                        user_name = user.name
                        payers_count = expense.users_to_pay.count()
                        amount_per_person = expense.amount if expense.split_type == "P" else expense.amount / payers_count
                        
                        if user_name in to_receive:
                            to_receive[user_name] = float(to_receive[user_name]) + float(amount_per_person)
                        else:
                            to_receive[user_name] = float(amount_per_person)

            response_data = {
                'to_give': [{'name': name, 'amount': round(amount, 2)} for name, amount in to_give.items()],
                'to_receive': [{'name': name, 'amount': round(amount, 2)} for name, amount in to_receive.items()]
            }
            
            return True, response_data

        except Exception as e:
            logger.error(f"Error getting user balance: {str(e)}")
            return False, str(e)
    
    def get_minimum_transactions_for_debt_settlement(self,expense_id:int):
        '''
        Method for debt simplification in group of participants with min num of transactions
        Step 1: create the incoming - outgoing for each user and store in balances list.
        Step 2: iterate over balances list and then iterate over them and then for each -ve value find next +ve value and change the value of it and vice versa.
                Its a recursive call where at the end each ele becomes 0 which means balanced.
        '''
        try:
            resultant_data = list()
            #first we create the incoming - outgoing for each user.
            expense = Expense.objects.get(id=expense_id)
            participants = ExpenseParticipants.objects.filter(expense=expense)            
            participant_balances = {}
            
            for idx, participant in enumerate(participants, start=1):
                participant_balances[participant.name] = 0  

            sub_expenses = SubExpenses.objects.filter(expense=expense)
            for sub_expense in sub_expenses:
                if not sub_expense.paid_by:
                    continue
                    
                payer = sub_expense.paid_by
                amount_per_person = float(sub_expense.amount) if sub_expense.split_type == "P" else float(sub_expense.amount) / sub_expense.users_to_pay.count()
                
                for user in sub_expense.users_to_pay.all():
                    if user.name == payer.name:
                        if sub_expense.split_type == "G":
                            participant_balances[payer.name] += float(sub_expense.amount) - amount_per_person
                        else:
                            total_participants = len(sub_expense.users_to_pay.all())
                            money_to_get_from_gp_members = total_participants * float(amount_per_person)
                            participant_balances[payer.name] += money_to_get_from_gp_members - amount_per_person
                    else:
                        participant_balances[user.name] -= amount_per_person
            resultant_data = self.dfs_for_settlements(balances=participant_balances,transactions=None)
            return True,resultant_data
        except Expense.DoesNotExist:
            return False, "Expense not found"
        except Exception as e:
            logger.error(f"Error getting expense graph data: {str(e)}")
            return False, str(e)
        
    def dfs_for_settlements(self,balances: dict, transactions: list = None) -> list:
        '''
        Takes a dictionary of name:balance pairs where balance represents net amount 
        (incoming - outgoing) for each person.
        '''
        if transactions is None:
            transactions = []
            
        if all(abs(bal) < 0.01 for bal in balances.values()):
            return transactions
        debtor = min(balances.items(), key=lambda x: x[1]) 
        creditor = max(balances.items(), key=lambda x: x[1])  
        
        if abs(debtor[1]) < 0.01 and abs(creditor[1]) < 0.01:
            return transactions
            
        amount = min(abs(debtor[1]), abs(creditor[1]))
        
        transactions.append({
            'from': debtor[0], 
            'to': creditor[0], 
            'amount': round(amount, 2)
        })
        
        balances[debtor[0]] += amount  
        balances[creditor[0]] -= amount 
        return self.dfs_for_settlements(balances, transactions)

    def get_expense_distribution(self, expense_id: int) -> Tuple[bool, Union[Dict[str, Decimal], str]]:
        """Get expense distribution among all participants"""
        try:
            expense = Expense.objects.get(id=expense_id)
            distribution = defaultdict(Decimal)
            
            # Calculate shares from sub-expenses
            for sub in SubExpenses.objects.filter(expense=expense):
                num_payers = sub.users_to_pay.count()
                share = sub.amount if sub.split_type == 'P' else sub.amount / num_payers
                
                for user in sub.users_to_pay.all():
                    distribution[user.name] += share
            
            # Adjust for direct payments
            payments = Payments.objects.filter(expense=expense)
            for payment in payments:
                distribution[payment.paid_by.username] -= payment.amount
                    
            return True, dict(distribution)
        except Exception as e:
            logger.error(f"Error getting expense distribution: {str(e)}")
            return False, str(e)

    def calculate_settlements(self, expense_id: int) -> Tuple[bool, Union[Dict[str, List[Dict]], str]]:
        """Calculate optimal settlements using a greedy approach"""
        try:
            expense = Expense.objects.get(id=expense_id)
            balance = defaultdict(Decimal)
            expense_records = []
            
            # Calculate balances from sub-expenses
            for sub in SubExpenses.objects.filter(expense=expense):
                share = sub.amount if sub.split_type == 'P' else sub.amount / sub.users_to_pay.count()
                    
                for user in sub.users_to_pay.all():
                    balance[user.name] -= share
                    balance[sub.paid_by] += share
                    expense_records.append({
                        'from_user': user.name,
                        'to_user': sub.paid_by,
                        'amount': share,
                        'expense_id': expense.id,
                        'sub_expense_id': sub.id
                    })
            
            # Adjust balances for direct payments
            payments = Payments.objects.filter(expense=expense)
            for payment in payments:
                balance[payment.paid_by.username] += payment.amount
                expense_records.append({
                    'from_user': payment.created_by.username,
                    'to_user': payment.paid_by.username,
                    'amount': payment.amount,
                    'expense_id': expense.id,
                    'payment_id': payment.id
                })

            settlements = []
            while balance:
                max_debtor = max(balance.items(), key=lambda x: x[1])[0]
                max_creditor = min(balance.items(), key=lambda x: x[1])[0]
                
                if abs(balance[max_debtor]) < 0.01 and abs(balance[max_creditor]) < 0.01:
                    break
                    
                amount = min(balance[max_debtor], -balance[max_creditor])
                balance[max_debtor] -= amount
                balance[max_creditor] += amount
                
                if abs(balance[max_debtor]) < 0.01:
                    del balance[max_debtor]
                if abs(balance[max_creditor]) < 0.01:
                    del balance[max_creditor]
                    
                settlements.append({
                    'from_user': max_debtor,
                    'to_user': max_creditor,
                    'amount': amount
                })
                
            return True, {
                'settlements': settlements,
                'expense_records': expense_records
            }
        except Exception as e:
            logger.error(f"Error calculating settlements: {str(e)}")
            return False, str(e)
