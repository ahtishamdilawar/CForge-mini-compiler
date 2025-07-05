import ply.yacc as yacc
import graphviz
import sys
from lexer import Lexer

class Parser:
    def __init__(self):
        # Build the lexer and parser.
        self.lexer = Lexer()
        self.tokens = self.lexer.tokens
        self.parser = yacc.yacc(module=self)
        
        # Symbol table to track variables and functions.
        self.symbol_table = {}
        self.current_scope = 'global'

    ##########################
    # Grammar Rules
    ##########################
    def p_program(self, p):
        '''program : statement_list'''
        p[0] = ('program', p[1])

    def p_statement_list(self, p):
        '''statement_list : statement
                          | statement_list statement'''
        if len(p) == 2:
            p[0] = [p[1]]
        else:
            p[0] = p[1] + [p[2]]

    def p_statement(self, p):
        '''statement : declaration
                     | assignment
                     | function_declaration
                     | function_call_statement
                     | conditional
                     | loop
                     | return_statement
                     | print_statement
                     | read_statement
                     | empty'''
        p[0] = p[1]

    def p_empty(self, p):
        '''empty :'''
        pass
    
    def p_function_call_statement(self, p):
        '''function_call_statement : function_call SEMICOLON'''
        p[0] = p[1]

    # (Other rules remain unchanged...)
    def p_function_call(self, p):
        '''function_call : IDENTIFIER LPAREN argument_list RPAREN'''
        if not self.symbol_exists(p[1]) or self.symbol_table[p[1]]['type'] != 'function':
            print(f"Error: Function '{p[1]}' not declared")
        else:
            expected_params = self.symbol_table[p[1]].get('params', [])
            if len(expected_params) != len(p[3]):
                print(f"Error: Function '{p[1]}' expects {len(expected_params)} arguments but got {len(p[3])}")
        p[0] = ('function_call', p[1], p[3])

    # When declaring a function, also add its parameters to the symbol table.
    def p_function_declaration(self, p):
        '''function_declaration : FUNCTION IDENTIFIER LPAREN parameter_list RPAREN LBRACE statement_list RBRACE'''
        if self.symbol_already_declared(p[2]):
            print(f"Error: Function '{p[2]}' already declared")
        else:
            self.symbol_table[p[2]] = {
                'type': 'function',
                'params': p[4],
                'scope': self.current_scope
            }
            # Temporarily add parameters into the symbol table for type checking the function body.
        for param in p[4]:
            param_type, param_name = param
            if self.symbol_already_declared(param_name):
                print(f"Error: Parameter '{param_name}' already declared")
            else:
                self.add_symbol(param_name, param_type)
        p[0] = ('function_declaration', p[2], p[4], p[7])
        # In a full implementation, you would now exit the function scope and remove parameters.

    
    # Declaration with optional initialization and type-checking.
    def p_declaration(self, p):
        '''declaration : type IDENTIFIER SEMICOLON
                       | type IDENTIFIER EQUALS expression SEMICOLON'''
        if self.symbol_already_declared(p[2]):
            print(f"Error: Symbol '{p[2]}' already declared in current scope")
        else:
            self.add_symbol(p[2], p[1])
        if len(p) == 4:
            p[0] = ('declaration', p[1], p[2])
        else:
            expr_type = self.get_expr_type(p[4])
            if expr_type != p[1]:
                print(f"Type Error: Cannot assign {expr_type} to variable of type {p[1]}")
            p[0] = ('declaration_init', p[1], p[2], p[4])

    def p_type(self, p):
        '''type : INT_TYPE
                | FLOAT_TYPE
                | STRING_TYPE
                | BOOL_TYPE'''
        p[0] = p[1]

    def p_assignment(self, p):
        '''assignment : IDENTIFIER EQUALS expression SEMICOLON'''
        if not self.symbol_exists(p[1]):
            print(f"Error: Variable '{p[1]}' not declared")
        else:
            var_type = self.symbol_table[p[1]]['type']
            expr_type = self.get_expr_type(p[3])
            if var_type != expr_type:
                print(f"Type Error: Cannot assign {expr_type} to variable '{p[1]}' of type {var_type}")
        p[0] = ('assignment', p[1], p[3])

    def p_expression(self, p):
        '''expression : logical_expr
                      | function_call'''
        p[0] = p[1]

    # Logical expressions including &&, ||, and NOT.
    def p_logical_expr(self, p):
        '''logical_expr : comparison_expr
                        | logical_expr AND comparison_expr
                        | logical_expr OR comparison_expr
                        | NOT comparison_expr'''
        if len(p) == 2:
            p[0] = p[1]
        elif p[1] == '!':
            expr_type = self.get_expr_type(p[2])
            if expr_type != 'bool':
                print("Type Error: '!' operator requires a boolean operand")
            p[0] = ('unop', p[1], p[2])
        else:
            left_type = self.get_expr_type(p[1])
            right_type = self.get_expr_type(p[3])
            if left_type != 'bool' or right_type != 'bool':
                print("Type Error: Logical operators require boolean operands")
            p[0] = ('binop', p[2], p[1], p[3])

    def p_comparison_expr(self, p):
        '''comparison_expr : arithmetic_expr
                           | arithmetic_expr comparison_op arithmetic_expr'''
        if len(p) == 2:
            p[0] = p[1]
        else:
            left_type = self.get_expr_type(p[1])
            right_type = self.get_expr_type(p[3])
            if left_type != right_type:
                print(f"Type Error: Cannot compare {left_type} with {right_type}")
            p[0] = ('comparison', p[2], p[1], p[3])

    def p_comparison_op(self, p):
        '''comparison_op : LESS_THAN
                         | GREATER_THAN
                         | LESS_EQUAL
                         | GREATER_EQUAL
                         | EQ
                         | NOT_EQUAL'''
        p[0] = p[1]

    # Arithmetic expressions now support string concatenation.
    def p_arithmetic_expr(self, p):
        '''arithmetic_expr : term
                           | arithmetic_expr PLUS term
                           | arithmetic_expr MINUS term
                           | arithmetic_expr MOD term'''
        if len(p) == 2:
            p[0] = p[1]
        else:
            op = p[2]
            left_type = self.get_expr_type(p[1])
            right_type = self.get_expr_type(p[3])
            if op == '+':
                if left_type == 'string' and right_type == 'string':
                    p[0] = ('binop', '+', p[1], p[3])
                elif left_type == right_type and left_type != 'string':
                    p[0] = ('binop', '+', p[1], p[3])
                elif 'string' in (left_type, right_type):
                    print(f"Type Error: Cannot use '+' between string and {right_type if left_type == 'string' else left_type}")
                    p[0] = ('error',)
                else:
                    print(f"Type Error: Cannot operate on {left_type} and {right_type} with '+'")
                    p[0] = ('binop', '+', p[1], p[3])

            else:
                if left_type != right_type:
                    print(f"Type Error: Cannot operate on {left_type} and {right_type} with '{op}'")
                p[0] = ('binop', op, p[1], p[3])

    def p_term(self, p):
        '''term : factor
                | term MULTIPLY factor
                | term DIVIDE factor'''
        if len(p) == 2:
            p[0] = p[1]
        else:
            left_type = self.get_expr_type(p[1])
            right_type = self.get_expr_type(p[3])
            if left_type != right_type:
                print(f"Type Error: Cannot operate on {left_type} and {right_type} with '{p[2]}'")
            p[0] = ('binop', p[2], p[1], p[3])

    def p_factor(self, p):
        '''factor : INTEGER
                  | FLOAT
                  | STRING
                  | TRUE
                  | FALSE
                  | IDENTIFIER
                  | LPAREN expression RPAREN'''
        if len(p) == 2:
            p[0] = p[1]
        else:
            p[0] = p[2]

    def p_function_declaration(self, p):
        '''function_declaration : FUNCTION IDENTIFIER LPAREN parameter_list RPAREN LBRACE statement_list RBRACE'''
        if self.symbol_already_declared(p[2]):
            print(f"Error: Function '{p[2]}' already declared")
        else:
            self.symbol_table[p[2]] = {
                'type': 'function',
                'params': p[4],
                'scope': self.current_scope
            }
        p[0] = ('function_declaration', p[2], p[4], p[7])

    def p_parameter_list(self, p):
        '''parameter_list : 
                          | type IDENTIFIER
                          | parameter_list COMMA type IDENTIFIER'''
        if len(p) == 1:
            p[0] = []
        elif len(p) == 3:
            p[0] = [(p[1], p[2])]
        else:
            p[0] = p[1] + [(p[3], p[4])]

    def p_function_call(self, p):
        '''function_call : IDENTIFIER LPAREN argument_list RPAREN'''
        if not self.symbol_exists(p[1]) or self.symbol_table[p[1]]['type'] != 'function':
            print(f"Error: Function '{p[1]}' not declared")
        else:
            expected_params = self.symbol_table[p[1]].get('params', [])
            if len(expected_params) != len(p[3]):
                print(f"Error: Function '{p[1]}' expects {len(expected_params)} arguments but got {len(p[3])}")
        p[0] = ('function_call', p[1], p[3])

    def p_argument_list(self, p):
        '''argument_list : 
                         | expression
                         | argument_list COMMA expression'''
        if len(p) == 1:
            p[0] = []
        elif len(p) == 2:
            p[0] = [p[1]]
        else:
            p[0] = p[1] + [p[3]]

    def p_conditional(self, p):
        '''conditional : IF LPAREN expression RPAREN LBRACE statement_list RBRACE
                       | IF LPAREN expression RPAREN LBRACE statement_list RBRACE ELSE LBRACE statement_list RBRACE'''
        if len(p) == 8:
            p[0] = ('if', p[3], p[6])
        else:
            p[0] = ('if_else', p[3], p[6], p[10])

    # Modified for-loop rule using for_increment nonterminal.
    def p_loop(self, p):
        '''loop : WHILE LPAREN expression RPAREN LBRACE statement_list RBRACE
                | FOR LPAREN declaration expression SEMICOLON for_increment RPAREN LBRACE statement_list RBRACE'''
        if p[1] == 'while':
            p[0] = ('while_loop', p[3], p[6])
        else:
            p[0] = ('for_loop', p[3], p[4], p[6], p[9])

    # New nonterminal for for-loop increment allowing assignments.
    def p_for_increment_assignment(self, p):
        '''for_increment : IDENTIFIER EQUALS expression'''
        if not self.symbol_exists(p[1]):
            print(f"Error: Variable '{p[1]}' not declared")
        else:
            var_type = self.symbol_table[p[1]]['type']
            expr_type = self.get_expr_type(p[3])
            if var_type != expr_type:
                print(f"Type Error: Cannot assign {expr_type} to variable '{p[1]}' of type {var_type}")
        p[0] = ('assignment', p[1], p[3])

    def p_for_increment_expr(self, p):
        '''for_increment : expression'''
        p[0] = p[1]

    def p_return_statement(self, p):
        '''return_statement : RETURN expression SEMICOLON'''
        p[0] = ('return', p[2])

    def p_print_statement(self, p):
        '''print_statement : PRINT LPAREN expression RPAREN SEMICOLON'''
        p[0] = ('print', p[3])

    def p_read_statement(self, p):
        '''read_statement : READ LPAREN RPAREN SEMICOLON'''
        p[0] = ('read',)

    ##########################
    # Symbol Table Management
    ##########################
    def add_symbol(self, name, symbol_type):
        self.symbol_table[name] = {
            'type': symbol_type,
            'scope': self.current_scope
        }

    def symbol_already_declared(self, name):
        return name in self.symbol_table

    def symbol_exists(self, name):
        return name in self.symbol_table

    ##########################
    # Enhanced Type Checking Helper
    ##########################
    def get_expr_type(self, expr):
        # For literals, determine the type.
        if isinstance(expr, int):
            return 'int'
        elif isinstance(expr, float):
            return 'float'
        elif isinstance(expr, str):
            # Explicitly recognize boolean literals.
            if expr == 'true' or expr == 'false':
                return 'bool'
            # Could be an identifier or a string literal.
            if expr in self.symbol_table:
                return self.symbol_table[expr]['type']
            else:
                return 'string'
        elif isinstance(expr, tuple):
            if expr[0] == 'binop':
                op = expr[1]
                left_type = self.get_expr_type(expr[2])
                right_type = self.get_expr_type(expr[3])
                if op == '+':
                    if left_type == 'string' or right_type == 'string':
                        return 'string'
                    elif left_type == right_type:
                        return left_type
                    else:
                        return 'error'
                else:
                    if left_type == right_type:
                        return left_type
                    else:
                        return 'error'
            elif expr[0] == 'unop':
                return self.get_expr_type(expr[2])
            elif expr[0] == 'function_call':
                return 'int'
            return 'unknown'
        else:
            return 'unknown'


    ##########################
    # Error Handling
    ##########################
    def p_error(self, p):
        if p:
            print(f"\n!!! Syntax Error !!!")
            print(f"Unexpected token: '{p.value}' of type {p.type}")
            print(f"Line number: {p.lineno}")
        else:
            print("\n!!! Syntax Error at EOF !!!")

    ##########################
    # AST Visualization (Prettified)
    ##########################
    def visualize_ast(self, ast):
        if ast is None:
            print("No AST to visualize")
            return None

        print("\n--- Full AST Debug Print ---")
        def print_ast(node, indent=''):
            if isinstance(node, tuple):
                print(f"{indent}{node[0]}")
                for child in node[1:]:
                    print_ast(child, indent + '  ')
            elif isinstance(node, list):
                print(f"{indent}List:")
                for item in node:
                    print_ast(item, indent + '  ')
            else:
                print(f"{indent}{repr(node)}")
        
        #print_ast(ast)

        dot = graphviz.Digraph(comment='Abstract Syntax Tree', 
                               node_attr={'shape': 'box', 'style': 'filled', 'fillcolor': 'lightblue', 'fontname': 'Helvetica'},
                               graph_attr={'rankdir': 'TB', 'splines': 'ortho', 'fontsize': '10'})
        
        def add_nodes(node, parent_id=None):
            try:
                current_id = str(id(node))
                if isinstance(node, tuple):
                    label = str(node[0])
                    dot.node(current_id, label)
                    if parent_id:
                        dot.edge(parent_id, current_id)
                    for child in node[1:]:
                        add_nodes(child, current_id)
                elif isinstance(node, list):
                    list_id = current_id + '_list'
                    dot.node(list_id, 'List')
                    if parent_id:
                        dot.edge(parent_id, list_id)
                    for item in node:
                        add_nodes(item, list_id)
                elif node is not None:
                    leaf_id = current_id + '_leaf'
                    dot.node(leaf_id, str(node), shape='ellipse', fillcolor='lightyellow')
                    if parent_id:
                        dot.edge(parent_id, leaf_id)
            except Exception as e:
                print(f"Error adding node: {e}")
                print(f"Problematic node: {node}")
        
        try:
            add_nodes(ast)
            dot.render('ast_visualization', format='png', cleanup=True)
            print("AST visualization saved as 'ast_visualization.png'")
        except Exception as e:
            print(f"Error generating AST visualization: {e}")
        
        return dot

    ##########################
    # Parse and Analyze Input
    ##########################
    def parse(self, data):
        print("\n--- Parsing Started ---")
        print(f"Input data:\n{data}")
        
        self.symbol_table = {}
        self.current_scope = 'global'
        
        try:
            ast = self.parser.parse(data, lexer=self.lexer.lexer, debug=False)
            print("\n--- Parsing Completed Successfully ---")
            self.visualize_ast(ast)
            return ast, self.symbol_table
        except Exception as e:
            print("\n--- Parsing Failed ---")
            print(f"Error: {e}")
            print(f"Exception details: {sys.exc_info()}")
            raise
