import requests
import json
from datetime import datetime, timedelta
import os

class UnitConverter:
    def __init__(self, cache_file="currency_cache.json"):
        self.cache_file = cache_file
        self.currency_rates = {}
        self.last_update = None
        self._load_cache()
        
        # Unit conversion factors (to base unit)
        # Include both singular and plural variants
        self.length_units = {
            'm': 1, 'meter': 1, 'meters': 1,
            'km': 1000, 'kilometer': 1000, 'kilometers': 1000,
            'cm': 0.01, 'centimeter': 0.01, 'centimeters': 0.01,
            'mm': 0.001, 'millimeter': 0.001, 'millimeters': 0.001,
            'mi': 1609.34, 'mile': 1609.34, 'miles': 1609.34,
            'yd': 0.9144, 'yard': 0.9144, 'yards': 0.9144,
            'ft': 0.3048, 'foot': 0.3048, 'feet': 0.3048,
            'in': 0.0254, 'inch': 0.0254, 'inches': 0.0254
        }
        
        self.weight_units = {
            'kg': 1, 'kilogram': 1, 'kilograms': 1,
            'g': 0.001, 'gram': 0.001, 'grams': 0.001,
            'mg': 0.000001, 'milligram': 0.000001, 'milligrams': 0.000001,
            'lb': 0.453592, 'pound': 0.453592, 'pounds': 0.453592,
            'oz': 0.0283495, 'ounce': 0.0283495, 'ounces': 0.0283495,
            'st': 6.35029, 'stone': 6.35029, 'stones': 6.35029,
            'ton': 1000, 'tons': 1000, 'tonne': 1000, 'tonnes': 1000
        }
        
        self.volume_units = {
            'l': 1, 'liter': 1, 'liters': 1, 'litre': 1, 'litres': 1,
            'ml': 0.001, 'milliliter': 0.001, 'milliliters': 0.001,
            'gal': 3.78541, 'gallon': 3.78541, 'gallons': 3.78541,
            'qt': 0.946353, 'quart': 0.946353, 'quarts': 0.946353,
            'pt': 0.473176, 'pint': 0.473176, 'pints': 0.473176,
            'cup': 0.236588, 'cups': 0.236588,
            'fl oz': 0.0295735, 'fluid ounce': 0.0295735, 'fluid ounces': 0.0295735
        }
        
        self.time_units = {
            's': 1, 'sec': 1, 'second': 1, 'seconds': 1,
            'min': 60, 'minute': 60, 'minutes': 60,
            'hr': 3600, 'hour': 3600, 'hours': 3600,
            'day': 86400, 'days': 86400,
            'week': 604800, 'weeks': 604800,
            'month': 2592000, 'months': 2592000,  # 30 days approx
            'year': 31536000, 'years': 31536000   # 365 days
        }
        
        # Currency symbols and codes mapping
        self.currency_symbols = {
            '$': 'USD', '€': 'EUR', '£': 'GBP', '¥': 'JPY',
            '₹': 'INR', '₽': 'RUB', '₩': 'KRW', '₿': 'BTC'
        }
    
    def _load_cache(self):
        """Load cached currency rates"""
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'r') as f:
                    data = json.load(f)
                    self.currency_rates = data.get('rates', {})
                    timestamp_str = data.get('timestamp', '2000-01-01T00:00:00')
                    self.last_update = datetime.fromisoformat(timestamp_str)
            except:
                pass
    
    def _save_cache(self):
        """Save currency rates to cache"""
        with open(self.cache_file, 'w') as f:
            json.dump({
                'rates': self.currency_rates,
                'timestamp': datetime.now().isoformat()
            }, f)
    
    def update_currency_rates(self, force=False):
        """Fetch latest exchange rates from API"""
        if not force and self.last_update and (datetime.now() - self.last_update) < timedelta(hours=1):
            return True  # Cache is fresh
        
        try:
            # Free API - no key needed
            url = "https://api.exchangerate-api.com/v4/latest/USD"
            response = requests.get(url, timeout=5)
            data = response.json()
            self.currency_rates = data['rates']
            self.last_update = datetime.now()
            self._save_cache()
            return True
        except Exception as e:
            print(f"Currency update failed: {e}")
            # If API fails, use fallback rates
            if not self.currency_rates:
                self.currency_rates = {
                    'USD': 1.0, 'EUR': 0.92, 'GBP': 0.79, 'JPY': 150.5,
                    'CAD': 1.36, 'AUD': 1.52, 'CHF': 0.88, 'CNY': 7.24,
                    'INR': 83.5, 'BRL': 5.12, 'MXN': 17.1, 'KRW': 1330.0
                }
            return False
    
    def convert_currency(self, amount, from_currency, to_currency):
        """Convert between currencies"""
        from_curr = from_currency.upper()
        to_curr = to_currency.upper()
        
        # Handle currency symbols
        if from_curr in self.currency_symbols:
            from_curr = self.currency_symbols[from_curr]
        if to_curr in self.currency_symbols:
            to_curr = self.currency_symbols[to_curr]
        
        self.update_currency_rates()
        
        if from_curr not in self.currency_rates:
            raise ValueError(f"Unknown currency: {from_curr}. Supported: {', '.join(self.currency_rates.keys())}")
        if to_curr not in self.currency_rates:
            raise ValueError(f"Unknown currency: {to_curr}. Supported: {', '.join(self.currency_rates.keys())}")
        
        # Convert to USD first, then to target
        usd_amount = amount / self.currency_rates[from_curr]
        result = usd_amount * self.currency_rates[to_curr]
        return round(result, 4)
    
    def convert_unit(self, value, from_unit, to_unit, unit_type):
        """Convert between units of same type"""
        unit_maps = {
            'length': self.length_units,
            'weight': self.weight_units,
            'volume': self.volume_units,
            'time': self.time_units
        }
        
        unit_map = unit_maps.get(unit_type)
        if not unit_map:
            raise ValueError(f"Unknown unit type: {unit_type}")
        
        from_unit_lower = from_unit.lower()
        to_unit_lower = to_unit.lower()
        
        # Try to find matching unit (handle partial matches)
        from_factor = None
        to_factor = None
        
        for unit, factor in unit_map.items():
            if unit == from_unit_lower or unit.startswith(from_unit_lower):
                from_factor = factor
            if unit == to_unit_lower or unit.startswith(to_unit_lower):
                to_factor = factor
        
        if from_factor is None:
            similar = [u for u in unit_map.keys() if from_unit_lower in u]
            if similar:
                raise ValueError(f"Unknown unit: '{from_unit}'. Did you mean: {', '.join(similar[:3])}?")
            else:
                raise ValueError(f"Unknown unit: '{from_unit}'. Available: {', '.join(list(unit_map.keys())[:10])}")
        
        if to_factor is None:
            similar = [u for u in unit_map.keys() if to_unit_lower in u]
            if similar:
                raise ValueError(f"Unknown unit: '{to_unit}'. Did you mean: {', '.join(similar[:3])}?")
            else:
                raise ValueError(f"Unknown unit: '{to_unit}'")
        
        # Convert to base unit then to target
        base_value = value * from_factor
        result = base_value / to_factor
        return round(result, 6)
    
    def detect_conversion(self, expression):
        """Detect and handle conversion patterns in expression"""
        import re
        
        # Clean expression
        expression = expression.lower().strip()
        
        # Currency pattern with symbols: "$100 to eur" or "100$ in gbp"
        symbol_pattern = r'([€$£¥₹])\s*(\d+\.?\d*)\s+(?:to|in)\s+([a-zA-Z]{3})'
        match = re.search(symbol_pattern, expression)
        if match:
            symbol = match.group(1)
            amount = float(match.group(2))
            to_curr = match.group(3)
            from_curr = self.currency_symbols.get(symbol, 'USD')
            try:
                return self.convert_currency(amount, from_curr, to_curr), 'currency'
            except:
                pass
        
        # Standard currency pattern: "100 usd to eur" or "50 eur in gbp"
        currency_pattern = r'(\d+\.?\d*)\s*([a-zA-Z]{3})\s+(?:to|in)\s+([a-zA-Z]{3})'
        match = re.search(currency_pattern, expression)
        if match:
            amount = float(match.group(1))
            from_curr = match.group(2)
            to_curr = match.group(3)
            try:
                result = self.convert_currency(amount, from_curr, to_curr)
                return result, 'currency'
            except Exception as e:
                error_msg = str(e)
                return None, None
        
        # Unit pattern: "5 km to miles" or "10 kg in lbs" or "6 mile to km"
        unit_pattern = r'(\d+\.?\d*)\s*([a-zA-Z\s]+?)\s+(?:to|in)\s+([a-zA-Z\s]+?)(?:\s|$)'
        match = re.search(unit_pattern, expression)
        if match:
            amount = float(match.group(1))
            from_unit = match.group(2).strip()
            to_unit = match.group(3).strip()
            
            # Detect unit type
            for unit_type, unit_map in [
                ('length', self.length_units),
                ('weight', self.weight_units),
                ('volume', self.volume_units),
                ('time', self.time_units)
            ]:
                # Check if both units exist in this category
                from_match = None
                to_match = None
                
                for unit in unit_map.keys():
                    if unit == from_unit or unit.startswith(from_unit) or from_unit.startswith(unit):
                        from_match = unit
                    if unit == to_unit or unit.startswith(to_unit) or to_unit.startswith(unit):
                        to_match = unit
                
                if from_match and to_match:
                    try:
                        result = self.convert_unit(amount, from_match, to_match, unit_type)
                        return result, unit_type
                    except Exception as e:
                        continue
            
            # If no match found, provide helpful error
            all_units = []
            for unit_map in [self.length_units, self.weight_units, self.volume_units, self.time_units]:
                all_units.extend(list(unit_map.keys())[:5])
            
            # Try to guess what user meant
            suggestions = []
            for unit_map in [self.length_units, self.weight_units, self.volume_units, self.time_units]:
                for unit in unit_map.keys():
                    if from_unit in unit or unit in from_unit:
                        suggestions.append(unit)
            
            if suggestions:
                print(f"Did you mean one of these? {', '.join(suggestions[:5])}")
        
        return None, None