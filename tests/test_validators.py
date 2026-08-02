"""
Unit tests for InvestWise AI 3.0 input validators.
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend')))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')

import django
django.setup()

from django.core.exceptions import ValidationError
from core.validators import (
    SymbolValidator,
    EmailValidator,
    PasswordValidator,
    PhoneNumberValidator,
    AmountValidator,
    PercentageValidator
)


class TestSymbolValidator(unittest.TestCase):
    def test_valid_symbols(self):
        self.assertEqual(SymbolValidator.validate("AAPL"), "AAPL")
        self.assertEqual(SymbolValidator.validate("msft"), "MSFT")
        self.assertEqual(SymbolValidator.validate("RELIANCE.NS"), "RELIANCE.NS")
        self.assertEqual(SymbolValidator.validate("TCS.BO"), "TCS.BO")

    def test_invalid_symbols(self):
        with self.assertRaises(ValidationError):
            SymbolValidator.validate("")
        with self.assertRaises(ValidationError):
            SymbolValidator.validate("INVALID!!!")
        with self.assertRaises(ValidationError):
            SymbolValidator.validate("A" * 21)  # Too long


class TestEmailValidator(unittest.TestCase):
    def test_valid_emails(self):
        self.assertEqual(EmailValidator.validate("user@example.com"), "user@example.com")
        self.assertEqual(EmailValidator.validate("Test.User@domain.co.in"), "test.user@domain.co.in")

    def test_invalid_emails(self):
        with self.assertRaises(ValidationError):
            EmailValidator.validate("")
        with self.assertRaises(ValidationError):
            EmailValidator.validate("invalid-email")
        with self.assertRaises(ValidationError):
            EmailValidator.validate("user@tempmail.com")  # Disposable domain


class TestPasswordValidator(unittest.TestCase):
    def test_valid_passwords(self):
        pwd = PasswordValidator.validate("SecurePass123!")
        self.assertEqual(pwd, "SecurePass123!")

    def test_invalid_passwords(self):
        with self.assertRaises(ValidationError):
            PasswordValidator.validate("")  # Empty
        with self.assertRaises(ValidationError):
            PasswordValidator.validate("short1!")  # Too short
        with self.assertRaises(ValidationError):
            PasswordValidator.validate("NoNumbers!")  # No digits
        with self.assertRaises(ValidationError):
            PasswordValidator.validate("nonumbers1!")  # No uppercase
        with self.assertRaises(ValidationError):
            PasswordValidator.validate("NOLOWERCASE1!")  # No lowercase
        with self.assertRaises(ValidationError):
            PasswordValidator.validate("NoSpecial1")  # No special char


class TestPhoneNumberValidator(unittest.TestCase):
    def test_valid_phones(self):
        self.assertEqual(PhoneNumberValidator.validate("+1234567890"), "+1234567890")
        self.assertEqual(PhoneNumberValidator.validate("+919876543210"), "+919876543210")

    def test_invalid_phones(self):
        with self.assertRaises(ValidationError):
            PhoneNumberValidator.validate("")
        with self.assertRaises(ValidationError):
            PhoneNumberValidator.validate("123456789")  # Too short
        with self.assertRaises(ValidationError):
            PhoneNumberValidator.validate("+1234567890123456")  # Too long


class TestAmountValidator(unittest.TestCase):
    def test_valid_amounts(self):
        self.assertEqual(AmountValidator.validate(100.0), 100.0)
        self.assertEqual(AmountValidator.validate(0.0), 0.0)
        self.assertEqual(AmountValidator.validate(999999999.0), 999999999.0)

    def test_invalid_amounts(self):
        with self.assertRaises(ValidationError):
            AmountValidator.validate(-1.0)
        with self.assertRaises(ValidationError):
            AmountValidator.validate(1000000000.0)  # Exceeds max


class TestPercentageValidator(unittest.TestCase):
    def test_valid_percentages(self):
        self.assertEqual(PercentageValidator.validate(0.0), 0.0)
        self.assertEqual(PercentageValidator.validate(50.5), 50.5)
        self.assertEqual(PercentageValidator.validate(100.0), 100.0)

    def test_invalid_percentages(self):
        with self.assertRaises(ValidationError):
            PercentageValidator.validate(-1.0)
        with self.assertRaises(ValidationError):
            PercentageValidator.validate(101.0)


if __name__ == "__main__":
    unittest.main()