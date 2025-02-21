from pydantic import BaseModel, validator, constr
from typing import List

from decimal import Decimal
from typing import Optional
from .models import Expense,SubExpenses

class AddExpenseValidator(BaseModel):
    description: constr(min_length=1, strip_whitespace=True)
    category: str

    @validator('description')
    def validate_description(cls, value):
        if not value.strip():
            raise ValueError("Description cannot be empty or contain only whitespace")
        return value
    
    @validator('category')
    def validate_category(cls, value):
        valid_categories = [choice[0] for choice in Expense.CATEGORY_CHOICES]
        if value not in valid_categories:
            raise ValueError(f"Invalid category. Must be one of: {', '.join(valid_categories)}")
        return value
        
    class Config:
        arbitrary_types_allowed = True

class AddParticipantsValidator(BaseModel):
    expense_participants: List[str]

    @validator('expense_participants')
    def validate_expense_participants(cls,value):
        if not value:
            raise ValueError(f"Please enter participants")

class AddSubExpenseValidator(BaseModel):
    expense_id: int
    description: constr(min_length=1, strip_whitespace=True)
    amount: Decimal
    split_type: str
    users_to_pay: List[int]
    paid_by: Optional[int]

    @validator('description')
    def validate_description(cls, value):
        if not value.strip():
            raise ValueError("Description cannot be empty or contain only whitespace")
        return value

    @validator('amount')
    def validate_amount(cls, value):
        if value <= 0:
            raise ValueError("Amount must be greater than 0")
        return value

    @validator('split_type')
    def validate_split_type(cls, value):
        valid_types = [choice[0] for choice in SubExpenses.SPLIT_CHOICES]
        if value not in valid_types:
            raise ValueError(f"Invalid split type. Must be one of: {', '.join(valid_types)}")
        return value

    @validator('users_to_pay')
    def validate_users_to_pay(cls, value):
        if not value:
            raise ValueError("Must specify at least one user to pay")
        return value

    class Config:
        arbitrary_types_allowed = True
