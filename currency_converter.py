#!/usr/bin/env python3
"""
Dynamic Currency Conversion System
"""

import json
import requests
from datetime import datetime, timedelta
import os

class CurrencyConverter:
    def __init__(self):
        self.rates = {}
        self.last_update = None
        self.cache_duration = timedelta(hours=1)

    def get_exchange_rates(self):
        """Fetch current exchange rates from API"""
        if self._is_cache_valid():
            return self.rates

        try:
            # Using free API (replace with paid service for production)
            response = requests.get('https://api.exchangerate-api.com/v4/latest/USD')
            data = response.json()

            self.rates = data['rates']
            self.last_update = datetime.now()

            # Save to cache file
            with open('currency_cache.json', 'w') as f:
                json.dump({
                    'rates': self.rates,
                    'timestamp': self.last_update.isoformat()
                }, f)

        except Exception as e:
            print(f"Exchange rate fetch failed: {e}")
            # Load from cache if available
            self._load_from_cache()

        return self.rates

    def _is_cache_valid(self):
        if not self.last_update:
            return False
        return datetime.now() - self.last_update < self.cache_duration

    def _load_from_cache(self):
        try:
            with open('currency_cache.json', 'r') as f:
                data = json.load(f)
                self.rates = data['rates']
                self.last_update = datetime.fromisoformat(data['timestamp'])
        except:
            # Fallback rates
            self.rates = {
                'EUR': 0.85, 'GBP': 0.73, 'JPY': 110.0, 'CNY': 6.45,
                'INR': 74.5, 'BRL': 5.2, 'RUB': 75.0, 'KRW': 1180.0,
                'CAD': 1.25, 'AUD': 1.35, 'CHF': 0.92, 'SEK': 8.6
            }

    def convert_price(self, base_price: float, from_currency: str = 'USD', to_currency: str = 'USD'):
        """Convert price between currencies"""
        rates = self.get_exchange_rates()

        if from_currency == to_currency:
            return base_price

        # Convert to USD first, then to target currency
        if from_currency != 'USD':
            base_price = base_price / rates[from_currency]

        if to_currency != 'USD':
            base_price = base_price * rates[to_currency]

        return round(base_price, 2)

def get_region_currency(region: str) -> str:
    """Get currency for region"""
    currency_map = {
        'US': 'USD', 'CA': 'CAD', 'GB': 'GBP', 'DE': 'EUR', 'FR': 'EUR',
        'IT': 'EUR', 'ES': 'EUR', 'NL': 'EUR', 'BE': 'EUR', 'AT': 'EUR',
        'CH': 'CHF', 'SE': 'SEK', 'NO': 'NOK', 'DK': 'DKK', 'FI': 'EUR',
        'JP': 'JPY', 'CN': 'CNY', 'KR': 'KRW', 'IN': 'INR', 'BR': 'BRL',
        'MX': 'MXN', 'AR': 'ARS', 'RU': 'RUB', 'AU': 'AUD', 'NZ': 'NZD',
        'ZA': 'ZAR', 'AE': 'AED', 'SA': 'SAR', 'SG': 'SGD', 'HK': 'HKD'
    }
    return currency_map.get(region, 'USD')

def format_price(amount: float, currency: str, locale: str = 'en') -> str:
    """Format price with currency symbol"""
    symbol_map = {
        'USD': '$', 'EUR': '€', 'GBP': '£', 'JPY': '¥', 'CNY': '¥',
        'INR': '₹', 'BRL': 'R$', 'RUB': '₽', 'KRW': '₩', 'CAD': 'C$',
        'AUD': 'A$', 'CHF': 'CHF', 'SEK': 'kr', 'NOK': 'kr', 'DKK': 'kr'
    }

    symbol = symbol_map.get(currency, currency)

    if currency in ['JPY', 'KRW']:
        # No decimal places for these currencies
        return f"{symbol}{int(amount)}"
    else:
        return f"{symbol}{amount:.2f}"

def get_localized_pricing(base_price_usd: float, region: str) -> dict:
    """Get complete localized pricing info"""
    converter = CurrencyConverter()

    local_currency = get_region_currency(region)
    local_price = converter.convert_price(base_price_usd, 'USD', local_currency)

    # Regional pricing adjustments
    discounts = {
        'IN': 0.8,   # 20% discount India
        'BR': 0.9,   # 10% discount Brazil
        'CN': 0.85,  # 15% discount China
        'RU': 0.9,   # 10% discount Russia
        'ZA': 0.85,  # 15% discount South Africa
    }

    if region in discounts:
        local_price *= discounts[region]

    return {
        'base_usd': base_price_usd,
        'local_price': round(local_price, 2),
        'currency': local_currency,
        'formatted': format_price(local_price, local_currency),
        'discount_applied': region in discounts,
        'discount_percentage': discounts.get(region, 1.0) * 100
    }

if __name__ == "__main__":
    converter = CurrencyConverter()

    # Test conversions
    test_regions = ['US', 'DE', 'JP', 'CN', 'IN', 'BR', 'GB', 'RU']

    print("Currency Conversion Test (Base: $59)")
    print("=" * 50)

    for region in test_regions:
        pricing = get_localized_pricing(59, region)
        print(f"{region:2}: {pricing['formatted']} ({pricing['currency']})")

    print("\n✅ Currency conversion system ready!")
    print("💱 Real-time rates with regional pricing adjustments")
