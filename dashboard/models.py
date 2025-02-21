from django.db import models
from auth_app.models import User
from django.core.validators import MinValueValidator
from decimal import Decimal
from django.contrib.postgres.fields import ArrayField

class ExpenseParticipants(models.Model):
    name = models.CharField(max_length=255)
    added_by = models.ForeignKey(to=User,on_delete=models.CASCADE)

class Expense(models.Model):
    CATEGORY_CHOICES = [
        ('food', 'Food'),
        ('transport', 'Transport'),
        ('utilities', 'Utilities'), 
        ('entertainment', 'Entertainment'),
        ('others', 'Others')
    ]

    description = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    updated_on = models.DateTimeField()
    participants = models.ManyToManyField(to=ExpenseParticipants)
    created_by = models.ForeignKey(to=User,on_delete=models.CASCADE)
    def __str__(self):
        return f"{self.description} - ₹{self.created_by.full_name}"

class SubExpenses(models.Model):
    SPLIT_CHOICES = [
        ('G','per Group'),
        ('P','per person')
    ]
    description = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])#this can be per person amount or whole amount to be shared in group based on splt_type
    created_at = models.DateTimeField(auto_now_add=True)
    expense = models.ForeignKey(to=Expense,on_delete=models.CASCADE)
    split_type = models.CharField(max_length=2,choices=SPLIT_CHOICES,null=False)
    users_to_pay = models.ManyToManyField(to=ExpenseParticipants,related_name='users_to_pay')#users who need to pay 
    paid_by = models.ForeignKey(to=ExpenseParticipants,on_delete=models.SET_NULL,related_name='paid_by_user',null=True,blank=True) #user who has paid the bill.
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now_add=True)
    split_completed = models.BooleanField(default=False)

class Settlement(models.Model):
    from_participant = models.ForeignKey(User, on_delete=models.CASCADE, related_name='settlements_paid')
    to_participant = models.ForeignKey(User, on_delete=models.CASCADE, related_name='settlements_received')
    amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    date = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True)
    def __str__(self):
        return f"{self.from_participant.username} paid ₹{self.amount} to {self.to_participant.username}"

class Payments(models.Model):
    amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    expense = models.ForeignKey(to=Expense, on_delete=models.CASCADE)
    paid_by = models.ForeignKey(to=User, on_delete=models.CASCADE, related_name='payments_made_by')
    paid_to = models.ForeignKey(to=User,on_delete=models.CASCADE, related_name='payments_made_to')
    created_by = models.ForeignKey(to=User, on_delete=models.CASCADE, related_name='payments_created')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Payment of ₹{self.amount} for {self.expense.description} by {self.paid_by.username}"
