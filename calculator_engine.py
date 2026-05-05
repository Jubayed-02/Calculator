from sympy import sympify, SympifyError, simplify, N
import math
from unit_converter import UnitConverter
from clipboard_solver import ClipboardSolver

class CalculatorEngine:
    def __init__(self):
        self.unit_converter = UnitConverter()
        self.clipboard_solver = ClipboardSolver()
        self.allowed_functions = {
            'sin': math.sin, 'cos': math.cos, 'tan': math.tan,
            'asin': math.asin, 'acos': math.acos, 'atan': math.atan,
            'sqrt': math.sqrt, 'log': math.log10, 'ln': math.log,
            'exp': math.exp, 'abs': abs, 'factorial': math.factorial,
            'pi': math.pi, 'e': math.e
        }
    
    def evaluate(self, expression):
        """Safely evaluate mathematical expression"""
        try:
            # First, check if it's a conversion request
            conv_result, conv_type = self.unit_converter.detect_conversion(expression)
            if conv_result is not None:
                return {
                    'value': conv_result,
                    'type': 'conversion',
                    'category': conv_type,
                    'expression': expression
                }
            
            # Handle regular math
            expr = expression.replace('^', '**')
            
            # Parse with SymPy
            parsed = sympify(expr)
            
            # Simplify and evaluate
            result = simplify(parsed)
            
            # Convert to float if it's a number
            if result.is_number:
                numeric_result = float(N(result))
                # Round to reasonable precision
                if abs(numeric_result - round(numeric_result)) < 1e-10:
                    numeric_result = round(numeric_result)
                else:
                    numeric_result = round(numeric_result, 8)
                return {
                    'value': numeric_result,
                    'type': 'numeric',
                    'category': 'standard',
                    'expression': expression
                }
            else:
                return {
                    'value': str(result),
                    'type': 'symbolic',
                    'category': 'standard',
                    'expression': expression
                }
                
        except SympifyError as e:
            return {
                'error': f"Invalid expression: {str(e)}",
                'type': 'error'
            }
        except Exception as e:
            return {
                'error': f"Calculation error: {str(e)}",
                'type': 'error'
            }
    
    def solve_clipboard(self):
        """Solve math from clipboard content"""
        result = self.clipboard_solver.get_clipboard_and_solve()
        if result['success']:
            return {
                'value': result['result'],
                'type': 'clipboard',
                'category': 'smart',
                'expression': result['expression'],
                'original_text': result['original']
            }
        return result