class SymbolTable:
    def __init__(self):
        # Multi-level symbol table to support scopes
        self.tables = [{}]
    
    def enter_scope(self):
        # Create a new scope
        self.tables.append({})
    
    def exit_scope(self):
        # Remove the current scope
        if len(self.tables) > 1:
            self.tables.pop()
    
    def declare(self, name, type, line_number):
        # Check for redeclaration in current scope
        current_scope = self.tables[-1]
        if name in current_scope:
            raise ValueError(f"Variable '{name}' already declared in current scope at line {line_number}")
        
        current_scope[name] = {
            'type': type,
            'initialized': False
        }
    
    def assign(self, name, value_type, line_number):
        # Find variable in nested scopes
        for scope in reversed(self.tables):
            if name in scope:
                # Type checking
                if scope[name]['type'] != value_type:
                    raise TypeError(f"Type mismatch for variable '{name}' at line {line_number}. "
                                    f"Expected {scope[name]['type']}, got {value_type}")
                
                scope[name]['initialized'] = True
                return
        
        # Variable not found in any scope
        raise NameError(f"Undeclared variable '{name}' at line {line_number}")
    
    def lookup(self, name, line_number):
        # Find variable in nested scopes
        for scope in reversed(self.tables):
            if name in scope:
                if not scope[name]['initialized']:
                    raise ValueError(f"Variable '{name}' used before initialization at line {line_number}")
                return scope[name]['type']
        
        raise NameError(f"Undeclared variable '{name}' at line {line_number}")
    
    def __str__(self):
        # Pretty print symbol table for debugging
        result = []
        for i, scope in enumerate(self.tables):
            result.append(f"Scope {i}:")
            for name, info in scope.items():
                result.append(f"  {name}: {info}")
        return "\n".join(result)