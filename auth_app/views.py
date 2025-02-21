from django.shortcuts import render
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from .models import User
from .validators import UserValidator
import json

def signup_view(request):
    if request.method == 'POST':
        req_body = request.body.decode("utf-8")
        body = json.loads(req_body)
        username = body.get('username')
        email = body.get('email')
        password1 = body.get('password1')
        password2 = body.get('password2')
        full_name = body.get('full_name')
        phone_number = body.get('phone_number')
        phone_number_country_code = body.get('phone_number_country_code')
        country = body.get('country')

        if User.objects.filter(username=username).exists():
            return JsonResponse({
                'status': False,
                'error': 'This username is already taken. Please choose another one.',
                'message': 'Username already exists in database'
            })

        if User.objects.filter(email=email).exists():
            return JsonResponse({
                'status': False,
                'error': 'An account with this email already exists. Please use a different email.',
                'message': 'Email already exists in database'
            })

        if phone_number and User.objects.filter(phone_number=phone_number).exists():
            return JsonResponse({
                'status': False,
                'error': 'This phone number is already registered. Please use a different number.',
                'message': 'Phone number already exists in database'
            })

        try:
            validator = UserValidator(
                username=username,
                email=email,
                password1=password1, 
                password2=password2,
                full_name=full_name,
                phone_number=phone_number,
                phone_number_country_code=phone_number_country_code,
                country=country
            )

            user = User.objects.create_user(
                username=validator.username,
                email=validator.email,
                password=validator.password1,
                full_name=validator.full_name,
                phone_number=validator.phone_number,
                phone_number_country_code=validator.phone_number_country_code,
                country=validator.country
            )
            return JsonResponse({
                'status': True,
                'error': None,
                'message': 'User created successfully'
            })

        except ValueError as e:
            return JsonResponse({
                'status': False,
                'error': str(e),
                'message': f'Validation error occurred: {str(e)}'
            })
        except Exception as e:
            return JsonResponse({
                'status': False,
                'error': 'Something went wrong while creating your account. Please try again.',
                'message': f'Exception occurred while creating user: {str(e)}'
            })

    return render(request, 'auth_app/signup.html')

def login_view(request):
    if request.user.is_authenticated:
        return redirect('home')
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, 'Logged in successfully!')
            return redirect('home')  
        else:
            messages.error(request, 'Invalid username or password.')
    return render(request, 'auth_app/login.html')

def logout_view(request):
    logout(request)
    messages.info(request, 'Logged out successfully!')
    return redirect('login')  
