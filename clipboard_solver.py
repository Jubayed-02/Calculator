import re
from sympy import sympify, SympifyError
import pyperclip  # You'll need to add this to requirements

class ClipboardSolver:
    def __init__(self):
        self.math_patterns = [
            # Basic arithmetic
            (r'(\d+\.?\d*)\s*([\+\-\*/])\s*(\d+\.?\d*)', self._format_arithmetic),
            # Percentage: "15% of 80" or "80 plus 15% tip"
            (r'(\d+)\s*%\s+of\s+(\d+)', self._format_percentage_of),
            (r'(\d+\.?\d*)\s+(?:plus|add)\s+(\d+)\s*%\s*(?:tip)?', self._format_tip),
            # Split bill: "split 150 between 4 people"
            (r'split\s+(\d+\.?\d*)\s+(?:between|among)\s+(\d+)\s*(?:people|ways)?', self._format_split),
            # Discount: "20% off 45" or "45 minus 20%"
            (r'(\d+)\s*%\s+off\s+(\d+\.?\d*)', self._format_discount),
            (r'(\d+\.?\d*)\s+minus\s+(\d+)\s*%', self._format_discount_reverse),
        ]
    
    def _format_arithmetic(self, match):
        """Format basic math: 5 + 3"""
        ops = {'+': '+', '-': '-', '*': '*', '/': '/'}
        return f"{match.group(1)} {ops[match.group(2)]} {match.group(3)}"
    
    def _format_percentage_of(self, match):
        """15% of 80 -> 80 * 0.15"""
        percent = float(match.group(1))
        value = float(match.group(2))
        return f"{value} * {percent/100}"
    
    def _format_tip(self, match):
        """80 plus 15% tip -> 80 * 1.15"""
        base = float(match.group(1))
        tip = float(match.group(2))
        return f"{base} * {1 + tip/100}"
    
    def _format_split(self, match):
        """split 150 between 4 -> 150 / 4"""
        total = float(match.group(1))
        people = int(match.group(2))
        return f"{total} / {people}"
    
    def _format_discount(self, match):
        """20% off 45 -> 45 * 0.8"""
        discount = float(match.group(1))
        price = float(match.group(2))
        return f"{price} * {1 - discount/100}"
    
    def _format_discount_reverse(self, match):
        """45 minus 20% -> 45 * 0.8"""
        price = float(match.group(1))
        discount = float(match.group(2))
        return f"{price} * {1 - discount/100}"
    
    def parse_text(self, text):
        """Extract and solve math from natural language text"""
        text = text.lower().strip()
        
        # Try each pattern
        for pattern, formatter in self.math_patterns:
            match = re.search(pattern, text)
            if match:
                math_expr = formatter(match)
                try:
                    result = sympify(math_expr)
                    return {
                        'original': text,
                        'expression': math_expr,
                        'result': float(result) if result.is_number else str(result),
                        'success': True
                    }
                except SympifyError:
                    continue
        
        # Fallback: Look for any numbers and operators
        numbers_ops = re.findall(r'[\d\.\+\-\*/\(\)]+', text)
        if numbers_ops:
            expr = ''.join(numbers_ops)
            try:
                result = sympify(expr)
                return {
                    'original': text,
                    'expression': expr,
                    'result': float(result) if result.is_number else str(result),
                    'success': True
                }
            except:
                pass
        
        return {'success': False, 'error': 'No mathematical expression found'}
    
    def get_clipboard_and_solve(self):
        """Get text from clipboard and solve it"""
        try:
            clipboard_text = pyperclip.paste()
            if not clipboard_text:
                return {'success': False, 'error': 'Clipboard is empty'}
            
            return self.parse_text(clipboard_text)
        except Exception as e:
            return {'success': False, 'error': str(e)}