"""
Input validation utilities for InvestWise AI 3.0.
Provides reusable validators for API endpoints.
"""
import re
from typing import Optional
from decimal import Decimal
from django.core.exceptions import ValidationError
from rest_framework import serializers


class SymbolValidator:
    """
    Validates stock symbols (e.g., AAPL, MSFT, RELIANCE.NS).
    """
    @staticmethod
    def validate(symbol: str) -> str:
        if not symbol:
            raise ValidationError("Symbol is required.")
        
        symbol = symbol.strip().upper()
        
        # Allow alphanumeric, dots, hyphens (for .NS, .BO suffixes)
        if not re.match(r'^[A-Z0-9][A-Z0-9.\-]{0,19}$', symbol):
            raise ValidationError(
                "Invalid symbol format. Must be 1-20 characters, alphanumeric with optional . or - suffixes."
            )
        
        return symbol


class EmailValidator:
    """
    Validates email addresses with additional security checks.
    """
    @staticmethod
    def validate(email: str) -> str:
        if not email:
            raise ValidationError("Email is required.")
        
        email = email.strip().lower()
        
        # Basic email regex
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
            raise ValidationError("Invalid email format.")
        
        # Check for disposable email domains (basic list)
        disposable_domains = ['tempmail.com', 'throwaway.com', 'guerrillamail.com']
        domain = email.split('@')[1] if '@' in email else ''
        if domain in disposable_domains:
            raise ValidationError("Disposable email addresses are not allowed.")
        
        return email


class PasswordValidator:
    """
    Validates password strength.
    """
    @staticmethod
    def validate(password: str) -> str:
        if not password:
            raise ValidationError("Password is required.")
        
        if len(password) < 8:
            raise ValidationError("Password must be at least 8 characters long.")
        
        if len(password) > 128:
            raise ValidationError("Password must not exceed 128 characters.")
        
        # Check for at least one number
        if not re.search(r'\d', password):
            raise ValidationError("Password must contain at least one number.")
        
        # Check for at least one uppercase letter
        if not re.search(r'[A-Z]', password):
            raise ValidationError("Password must contain at least one uppercase letter.")
        
        # Check for at least one lowercase letter
        if not re.search(r'[a-z]', password):
            raise ValidationError("Password must contain at least one lowercase letter.")
        
        # Check for at least one special character
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            raise ValidationError("Password must contain at least one special character.")
        
        return password


class PhoneNumberValidator:
    """
    Validates phone numbers (basic international format).
    """
    @staticmethod
    def validate(phone: str) -> str:
        if not phone:
            raise ValidationError("Phone number is required.")
        
        # Remove all non-digit characters except +
        cleaned = re.sub(r'[^\d+]', '', phone)
        
        # Check if it starts with + and has 10-15 digits
        if not re.match(r'^\+?[1-9]\d{9,14}$', cleaned):
            raise ValidationError("Invalid phone number format. Use international format (e.g., +1234567890).")
        
        return cleaned


class AmountValidator:
    """
    Validates monetary amounts.
    """
    @staticmethod
    def validate(amount: float, min_value: float = 0.0, max_value: float = 999_999_999.0) -> float:
        if amount is None:
            raise ValidationError("Amount is required.")
        
        if not isinstance(amount, (int, float)):
            raise ValidationError("Amount must be a number.")
        
        if amount < min_value:
            raise ValidationError(f"Amount must be at least {min_value}.")
        
        if amount > max_value:
            raise ValidationError(f"Amount must not exceed {max_value}.")
        
        return float(amount)


class PercentageValidator:
    """
    Validates percentage values (0-100).
    """
    @staticmethod
    def validate(percentage: float) -> float:
        if percentage is None:
            raise ValidationError("Percentage is required.")
        
        if not isinstance(percentage, (int, float)):
            raise ValidationError("Percentage must be a number.")
        
        if percentage < 0 or percentage > 100:
            raise ValidationError("Percentage must be between 0 and 100.")
        
        return float(percentage)


# DRF Serializer Field Validators
class ValidatedSymbolField(serializers.CharField):
    """
    DRF field that validates stock symbols.
    """
    def to_internal_value(self, data):
        data = super().to_internal_value(data)
        return SymbolValidator.validate(data)


class ValidatedEmailField(serializers.EmailField):
    """
    DRF field that validates emails with additional security checks.
    """
    def to_internal_value(self, data):
        data = super().to_internal_value(data)
        return EmailValidator.validate(data)


class ValidatedPasswordField(serializers.CharField):
    """
    DRF field that validates password strength.
    """
    def __init__(self, **kwargs):
        kwargs.setdefault('write_only', True)
        kwargs.setdefault('style', {'input_type': 'password'})
        super().__init__(**kwargs)
    
    def to_internal_value(self, data):
        data = super().to_internal_value(data)
        return PasswordValidator.validate(data)


class ValidatedAmountField(serializers.DecimalField):
    """
    DRF field that validates monetary amounts.
    """
    def __init__(self, **kwargs):
        # Convert float min/max values to Decimal to avoid DRF warnings
        if 'min_value' in kwargs and isinstance(kwargs['min_value'], (int, float)):
            kwargs['min_value'] = Decimal(str(kwargs['min_value']))
        else:
            kwargs.setdefault('min_value', Decimal('0.0'))
        
        if 'max_value' in kwargs and isinstance(kwargs['max_value'], (int, float)):
            kwargs['max_value'] = Decimal(str(kwargs['max_value']))
        else:
            kwargs.setdefault('max_value', Decimal('999999999.0'))
        
        kwargs.setdefault('max_digits', 15)
        kwargs.setdefault('decimal_places', 2)
        super().__init__(**kwargs)
    
    def to_internal_value(self, data):
        data = super().to_internal_value(data)
        return AmountValidator.validate(float(data))


class ValidatedPercentageField(serializers.FloatField):
    """
    DRF field that validates percentages.
    """
    def to_internal_value(self, data):
        data = super().to_internal_value(data)
        return PercentageValidator.validate(data)