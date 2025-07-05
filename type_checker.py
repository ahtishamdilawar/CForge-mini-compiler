class TypeChecker:
    @staticmethod
    def check_arithmetic_operation(left_type, right_type, operation, line_number):
        # Define type compatibility for arithmetic operations
        valid_types = {
            'int': ['int', 'float'],
            'float': ['int', 'float']
        }
        
        # Check if operation is valid
        if left_type not in valid_types or right_type not in valid_types[left_type]:
            raise TypeError(f"Invalid arithmetic operation between {left_type} and {right_type} "
                            f"at line {line_number}")
        
        # Determine result type (float if any operand is float)
        return 'float' if 'float' in [left_type, right_type] else 'int'
    
    @staticmethod
    def check_logical_operation(left_type, right_type, operation, line_number):
        # Logical operations require boolean types
        if left_type != 'bool' or right_type != 'bool':
            raise TypeError(f"Logical {operation} requires boolean operands "
                            f"at line {line_number}")
        
        return 'bool'
    
    @staticmethod
    def check_relational_operation(left_type, right_type, operation, line_number):
        # Relational operations work for numeric types
        valid_numeric_types = ['int', 'float']
        
        if left_type not in valid_numeric_types or right_type not in valid_numeric_types:
            raise TypeError(f"Relational operation {operation} requires numeric types "
                            f"at line {line_number}")
        
        return 'bool'