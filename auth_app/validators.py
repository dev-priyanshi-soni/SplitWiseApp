from pydantic import BaseModel, validator, constr
import re

class UserValidator:
    def __init__(self, username, email, password1, password2, full_name, phone_number=None, phone_number_country_code=None, country=None):
        self.username = self.validate_username(username)
        self.email = self.validate_email(email)
        self.password1 = self.validate_password(password1, password2)
        self.password2 = password2
        self.full_name = self.validate_full_name(full_name)
        self.phone_number = self.validate_phone_number(phone_number)
        self.phone_number_country_code = self.validate_country_code(phone_number_country_code)
        self.country = country

    def validate_username(self, username):
        if not username:
            raise ValueError("Username is required")
        if len(username) < 3:
            raise ValueError("Username must be at least 3 characters long")
        if not username.isalnum() and '_' not in username:
            raise ValueError("Username can only contain letters, numbers and underscores")
        return username

    def validate_email(self, email):
        if not email:
            raise ValueError("Email is required")
        if '@' not in email or '.' not in email:
            raise ValueError("Please enter a valid email address")
        
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email):
            raise ValueError("Please enter a valid email address")
        return email

    def validate_password(self, password1, password2):
        if not password1:
            raise ValueError("Password is required")
        if len(password1) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if not any(char.isdigit() for char in password1):
            raise ValueError("Password must contain at least one number")
        if not any(char in "!@#$%^&*(),.?\":{}|<>" for char in password1):
            raise ValueError("Password must contain at least one special character")
        if password1 != password2:
            raise ValueError("Passwords do not match")
        return password1

    def validate_full_name(self, full_name):
        if not full_name or not full_name.strip():
            raise ValueError("Full name is required")
        return full_name.strip()

    def validate_phone_number(self, phone_number):
        if phone_number:
            if not phone_number.isdigit():
                raise ValueError("Phone number must contain only digits")
            if len(phone_number) != 10:
                raise ValueError("Phone number must be exactly 10 digits")
        return phone_number

    def validate_country_code(self, country_code):
        if country_code:
            if not country_code.startswith('+'):
                country_code = '+' + country_code
            if not country_code[1:].isdigit():
                raise ValueError("Invalid country code format")
            if not 1 <= len(country_code[1:]) <= 4:
                raise ValueError("Country code must be between 1 and 4 digits")
        return country_code
