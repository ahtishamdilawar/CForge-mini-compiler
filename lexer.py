import ply.lex as lex
import re

class Lexer:
    # List of token names, including new tokens for modulus and logical operations.
    tokens = [
        'IDENTIFIER',
        'INTEGER',
        'FLOAT',
        'STRING',
        'PLUS',
        'MINUS',
        'MULTIPLY',
        'DIVIDE',
        'MOD',            # modulus operator
        'EQUALS',         # assignment operator
        'EQ',             # equality operator (==)
        'LESS_THAN',
        'GREATER_THAN',
        'LESS_EQUAL',
        'GREATER_EQUAL',
        'NOT_EQUAL',
        'AND',            # logical AND (&&)
        'OR',             # logical OR (||)
        'NOT',            # logical NOT (!)
        'LPAREN',
        'RPAREN',
        'LBRACE',
        'RBRACE',
        'SEMICOLON',
        'COMMA',
    ]

    # Reserved keywords including bool type and I/O operations.
    reserved = {
        'if': 'IF',
        'else': 'ELSE',
        'while': 'WHILE',
        'for': 'FOR',
        'int': 'INT_TYPE',
        'float': 'FLOAT_TYPE',
        'string': 'STRING_TYPE',
        'bool': 'BOOL_TYPE',
        'true': 'TRUE',
        'false': 'FALSE',
        'return': 'RETURN',
        'def': 'FUNCTION',
        'print': 'PRINT',
        'read': 'READ'
    }

    # Add reserved words to tokens
    tokens += list(reserved.values())

    # Regular expression rules for simple tokens
    t_PLUS          = r'\+'
    t_MINUS         = r'-'
    t_MULTIPLY      = r'\*'
    t_DIVIDE        = r'/'
    t_MOD           = r'%'
    # Note: For equality vs assignment, ensure the longer match is first.
    t_EQ            = r'=='
    t_NOT_EQUAL     = r'!='
    t_EQUALS        = r'='
    t_LESS_EQUAL    = r'<='
    t_GREATER_EQUAL = r'>='
    t_LESS_THAN     = r'<'
    t_GREATER_THAN  = r'>'
    t_AND           = r'&&'
    t_OR            = r'\|\|'
    # Logical NOT must come after != so that "!=" is recognized first.
    t_NOT           = r'!'
    t_LPAREN        = r'\('
    t_RPAREN        = r'\)'
    t_LBRACE        = r'\{'
    t_RBRACE        = r'\}'
    t_SEMICOLON     = r';'
    t_COMMA         = r','

    # More complex token rules using functions
    def t_FLOAT(self, t):
        r'\d+\.\d+'
        t.value = float(t.value)
        return t

    def t_INTEGER(self, t):
        r'\d+'
        t.value = int(t.value)
        return t

    def t_STRING(self, t):
        r'"[^"]*"|\'[^\']*\''
        # Remove quotes
        t.value = t.value[1:-1]
        return t

    def t_IDENTIFIER(self, t):
        r'[a-zA-Z_][a-zA-Z0-9_]*'
        # Check for reserved words
        t.type = self.reserved.get(t.value, 'IDENTIFIER')
        return t

    # Define a rule so we can track line numbers
    def t_newline(self, t):
        r'\n+'
        t.lexer.lineno += len(t.value)

    # Completely ignore whitespace
    t_ignore = ' \t'

    # Ignore single-line comments
    def t_COMMENT(self, t):
        r'//.*'
        pass

    # Multi-line comments
    def t_MULTILINE_COMMENT(self, t):
        r'/\*(.|\n)*?\*/'
        t.lexer.lineno += t.value.count('\n')
        pass

    # Error handling rule
    def t_error(self, t):
        print(f"Illegal character '{t.value[0]}' at line {t.lineno}")
        t.lexer.skip(1)

    def __init__(self):
        # Build the lexer during initialization
        self.lexer = lex.lex(module=self)

    # Test the lexer
    def test(self, data):
        # Ensure lexer is built
        if not hasattr(self, 'lexer'):
            self.lexer = lex.lex(module=self)
        
        # Reset line number
        self.lexer.lineno = 1
        
        # Input the data
        self.lexer.input(data)
        
        # Collect tokens
        tokens = []
        while True:
            tok = self.lexer.token()
            if not tok:
                break
            tokens.append((tok.type, tok.value, tok.lineno))
        return tokens
