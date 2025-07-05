import llvmlite.ir as ir
import llvmlite.binding as llvm

class LLVMIRGenerator:
    def __init__(self):
        # Initialize LLVM
        llvm.initialize()
        llvm.initialize_native_target()
        llvm.initialize_native_asmprinter()
        self.fmt_globals = {}   # Cache for format string globals
        
        # Create module and builder
        self.module = ir.Module(name="main_module")
        self.builder = None
        
        # Variables to store function context
        self.function = None
        self.blocks = {}
        self.block_stack = []
        self.variables = {}
        self.functions = {}
        
        # Define types
        self.int_type = ir.IntType(32)
        self.float_type = ir.FloatType()
        self.void_type = ir.VoidType()
        self.bool_type = ir.IntType(1)
        self.char_ptr_type = ir.PointerType(ir.IntType(8))
        
        # Add built-in functions
        self._add_builtin_functions()
    
    def _add_builtin_functions(self):
        # Define printf function for print statements
        printf_ty = ir.FunctionType(self.int_type, [ir.PointerType(ir.IntType(8))], var_arg=True)
        self.printf = ir.Function(self.module, printf_ty, name="printf")
        
        # Define scanf function for read statements
        scanf_ty = ir.FunctionType(self.int_type, [ir.PointerType(ir.IntType(8))], var_arg=True)
        self.scanf = ir.Function(self.module, scanf_ty, name="scanf")
    
    def _get_llvm_type(self, type_name):
        if type_name == 'int':
            return self.int_type
        elif type_name == 'float':
            return self.float_type
        elif type_name == 'bool':
            return self.bool_type
        elif type_name == 'string':
            # In LLVM, strings are pointers to i8
            return self.char_ptr_type
        else:
            raise ValueError(f"Unsupported type: {type_name}")
    
    def generate(self, ast):
        """Generate LLVM IR code from the AST"""
        if ast is None:
            return "// No AST to generate code for"

        # Flag to check if the user defined their own main()
        user_defined_main = False

        # First pass: check for user-defined main
        if ast[0] == 'program':
            statements = ast[1]
            for stmt in statements:
                if isinstance(stmt, tuple) and stmt[0] == 'function_declaration' and stmt[1] == 'main':
                    user_defined_main = True
                    break

        # If no user-defined main, generate our own main() entry point
        if not user_defined_main:
            main_func_type = ir.FunctionType(self.int_type, [])
            main_func = ir.Function(self.module, main_func_type, name="main")
            entry_block = main_func.append_basic_block(name="entry")
            self.builder = ir.IRBuilder(entry_block)
            self.function = main_func

        # Process all statements
        if ast[0] == 'program':
            statements = ast[1]
            for stmt in statements:
                if stmt is not None:
                    self._generate_statement(stmt)

        # If we generated our own main(), add return 0 if needed
        if not user_defined_main and not self.builder.block.is_terminated:
            self.builder.ret(ir.Constant(self.int_type, 0))

        # Verify the module
        try:
            llvm_ir = str(self.module)
            llvm.parse_assembly(llvm_ir)
        except Exception as e:
            print(f"LLVM IR verification failed: {e}")
            return llvm_ir

        # Optimize the IR
        optimized_ir = self.optimize_ir(llvm_ir)

        # Return both versions
        return llvm_ir, optimized_ir

    
    def _generate_statement(self, stmt):
        """Generate code for a single statement"""
        if stmt is None:
            return
        
        stmt_type = stmt[0] if isinstance(stmt, tuple) else None
        
        if stmt_type == 'declaration':
            self._generate_declaration(stmt)
        elif stmt_type == 'declaration_init':
            self._generate_declaration_init(stmt)
        elif stmt_type == 'assignment':
            self._generate_assignment(stmt)
        elif stmt_type == 'function_declaration':
            self._generate_function_declaration(stmt)
        elif stmt_type == 'function_call':
            self._generate_function_call(stmt)
        elif stmt_type == 'if' or stmt_type == 'if_else':
            self._generate_conditional(stmt)
        elif stmt_type == 'while_loop':
            self._generate_while_loop(stmt)
        elif stmt_type == 'for_loop':
            self._generate_for_loop(stmt)
        elif stmt_type == 'return':
            self._generate_return(stmt)
        elif stmt_type == 'print':
            self._generate_print(stmt)
        elif stmt_type == 'read':
            self._generate_read(stmt)
    
    def _generate_declaration(self, stmt):
        """Generate code for variable declaration"""
        _, var_type, var_name = stmt
        
        # Allocate memory for the variable
        var_type_ir = self._get_llvm_type(var_type)
        alloca = self.builder.alloca(var_type_ir, name=var_name)
        
        # Store in our symbol table
        self.variables[var_name] = {'ptr': alloca, 'type': var_type}
    
    def _generate_declaration_init(self, stmt):
        """Generate code for variable declaration with initialization"""
        _, var_type, var_name, expr = stmt
        
        # Allocate memory for the variable
        var_type_ir = self._get_llvm_type(var_type)
        alloca = self.builder.alloca(var_type_ir, name=var_name)
        
        # Generate the expression and store the result
        expr_value, expr_type = self._generate_expression(expr)
        
        # Convert types if needed
        if var_type != expr_type:
            expr_value = self._convert_type(expr_value, expr_type, var_type)
        
        self.builder.store(expr_value, alloca)
        
        # Store in our symbol table
        self.variables[var_name] = {'ptr': alloca, 'type': var_type}
    
    def _generate_assignment(self, stmt):
        """Generate code for assignment"""
        _, var_name, expr = stmt
        
        # Generate the expression
        expr_value, expr_type = self._generate_expression(expr)
        
        # Store value in variable
        if var_name in self.variables:
            var_info = self.variables[var_name]
            var_type = var_info['type']
            
            # Convert types if needed
            if var_type != expr_type:
                expr_value = self._convert_type(expr_value, expr_type, var_type)
                
            self.builder.store(expr_value, var_info['ptr'])
        else:
            raise ValueError(f"Variable '{var_name}' not declared")
    
    def _generate_expression(self, expr):
        """Generate code for an expression, returns (value, type)"""
        if isinstance(expr, int):
            return ir.Constant(self.int_type, expr), 'int'
        elif isinstance(expr, float):
            return ir.Constant(self.float_type, expr), 'float'
        elif isinstance(expr, str):
            if expr == 'true':
                return ir.Constant(self.bool_type, 1), 'bool'
            elif expr == 'false':
                return ir.Constant(self.bool_type, 0), 'bool'
            elif expr in self.variables:
                # Load variable value
                var_info = self.variables[expr]
                return self.builder.load(var_info['ptr']), var_info['type']
            else:
                # Create a global string constant
                string_data = bytearray((expr + '\0').encode('utf8'))
                global_fmt = ir.GlobalVariable(self.module, 
                                             ir.ArrayType(ir.IntType(8), len(string_data)),
                                             name=f".str.{hash(expr) & 0xffffffff}")
                global_fmt.global_constant = True
                global_fmt.linkage = 'internal'
                global_fmt.initializer = ir.Constant(ir.ArrayType(ir.IntType(8), len(string_data)), 
                                                    bytearray(string_data))
                return self.builder.bitcast(global_fmt, self.char_ptr_type), 'string'
        elif isinstance(expr, tuple):
            if expr[0] == 'binop':
                return self._generate_binary_op(expr)
            elif expr[0] == 'unop':
                return self._generate_unary_op(expr)
            elif expr[0] == 'function_call':
                return self._generate_function_call(expr, is_expr=True)
            elif expr[0] == 'comparison':
                return self._generate_comparison(expr)
            
        # Default for any unhandled cases
        return ir.Constant(self.int_type, 0), 'int'
    
    def _convert_type(self, value, from_type, to_type):
        """Convert between different types"""
        if from_type == to_type:
            return value
        
        # Handle numeric conversions
        if from_type == 'int' and to_type == 'float':
            return self.builder.sitofp(value, self.float_type)
        elif from_type == 'float' and to_type == 'int':
            return self.builder.fptosi(value, self.int_type)
        elif from_type == 'bool' and to_type == 'int':
            return self.builder.zext(value, self.int_type)
        elif from_type == 'int' and to_type == 'bool':
            return self.builder.icmp_signed('!=', value, ir.Constant(self.int_type, 0))
        
        # If we can't convert (like string to int), just return the original value
        # In a real compiler, this would be a type error
        print(f"Warning: Cannot convert {from_type} to {to_type}")
        return value
    
    def _generate_binary_op(self, expr):
        """Generate code for binary operations"""
        _, op, left, right = expr
        
        # Generate code for left and right expressions
        left_val, left_type = self._generate_expression(left)
        right_val, right_type = self._generate_expression(right)
        
        # Special case for string concatenation
        if op == '+' and (left_type == 'string' or right_type == 'string'):
            # This is a placeholder - in a real implementation, you would need a runtime
            # function to concatenate strings
            print("Warning: String concatenation not fully implemented")
            if left_type == 'string':
                return left_val, 'string'
            else:
                return right_val, 'string'
        
        # For numeric operations, convert types if needed
        if left_type != right_type:
            # Promote int to float if one operand is float
            if left_type == 'float' and right_type == 'int':
                right_val = self.builder.sitofp(right_val, self.float_type)
                right_type = 'float'
            elif left_type == 'int' and right_type == 'float':
                left_val = self.builder.sitofp(left_val, self.float_type)
                left_type = 'float'
        
        # Now perform the operation
        result_type = left_type  # Result type is the same as operands
        
        if op == '+':
            if left_type == 'float':
                result = self.builder.fadd(left_val, right_val)
            else:
                result = self.builder.add(left_val, right_val)
        elif op == '-':
            if left_type == 'float':
                result = self.builder.fsub(left_val, right_val)
            else:
                result = self.builder.sub(left_val, right_val)
        elif op == '*':
            if left_type == 'float':
                result = self.builder.fmul(left_val, right_val)
            else:
                result = self.builder.mul(left_val, right_val)
        elif op == '/':
            if left_type == 'float':
                result = self.builder.fdiv(left_val, right_val)
            else:
                result = self.builder.sdiv(left_val, right_val)
        elif op == '%':
            if left_type == 'float':
                result = self.builder.frem(left_val, right_val)
            else:
                result = self.builder.srem(left_val, right_val)
        elif op == '&&':
            if left_type != 'bool':
                left_val = self.builder.icmp_signed('!=', left_val, ir.Constant(self.int_type, 0))
            if right_type != 'bool':
                right_val = self.builder.icmp_signed('!=', right_val, ir.Constant(self.int_type, 0))
            result = self.builder.and_(left_val, right_val)
            result_type = 'bool'
        elif op == '||':
            if left_type != 'bool':
                left_val = self.builder.icmp_signed('!=', left_val, ir.Constant(self.int_type, 0))
            if right_type != 'bool':
                right_val = self.builder.icmp_signed('!=', right_val, ir.Constant(self.int_type, 0))
            result = self.builder.or_(left_val, right_val)
            result_type = 'bool'
        else:
            print(f"Warning: Unsupported binary operator: {op}")
            result = left_val
        
        return result, result_type
    
    def _generate_unary_op(self, expr):
        """Generate code for unary operations"""
        _, op, operand = expr
        
        # Generate code for the operand
        val, val_type = self._generate_expression(operand)
        
        if op == '!':
            # Logical NOT - convert to boolean if needed
            if val_type != 'bool':
                if val_type == 'float':
                    cmp_val = self.builder.fcmp_ordered('==', val, ir.Constant(self.float_type, 0.0))
                else:
                    cmp_val = self.builder.icmp_signed('==', val, ir.Constant(self.int_type, 0))
                return cmp_val, 'bool'
            else:
                return self.builder.not_(val), 'bool'
        elif op == '-':
            # Negation for numeric values
            if val_type == 'float':
                return self.builder.fneg(val), val_type
            else:
                return self.builder.neg(val), val_type
        
        # Default case
        return val, val_type
    
    def _generate_comparison(self, expr):
        """Generate code for comparison operations"""
        _, op, left, right = expr
        
        # Generate code for left and right expressions
        left_val, left_type = self._generate_expression(left)
        right_val, right_type = self._generate_expression(right)
        
        # Convert types if needed
        if left_type != right_type:
            if left_type == 'float' and right_type == 'int':
                right_val = self.builder.sitofp(right_val, self.float_type)
                right_type = 'float'
            elif left_type == 'int' and right_type == 'float':
                left_val = self.builder.sitofp(left_val, self.float_type)
                left_type = 'float'
        
        # Generate appropriate comparison based on operator and types
        if left_type == 'float':
            if op == '<':
                result = self.builder.fcmp_ordered('<', left_val, right_val)
            elif op == '>':
                result = self.builder.fcmp_ordered('>', left_val, right_val)
            elif op == '<=':
                result = self.builder.fcmp_ordered('<=', left_val, right_val)
            elif op == '>=':
                result = self.builder.fcmp_ordered('>=', left_val, right_val)
            elif op == '==':
                result = self.builder.fcmp_ordered('==', left_val, right_val)
            elif op == '!=':
                result = self.builder.fcmp_ordered('!=', left_val, right_val)
            else:
                print(f"Warning: Unsupported comparison operator: {op}")
                result = ir.Constant(self.bool_type, 0)
        else:
            if op == '<':
                result = self.builder.icmp_signed('<', left_val, right_val)
            elif op == '>':
                result = self.builder.icmp_signed('>', left_val, right_val)
            elif op == '<=':
                result = self.builder.icmp_signed('<=', left_val, right_val)
            elif op == '>=':
                result = self.builder.icmp_signed('>=', left_val, right_val)
            elif op == '==':
                result = self.builder.icmp_signed('==', left_val, right_val)
            elif op == '!=':
                result = self.builder.icmp_signed('!=', left_val, right_val)
            else:
                print(f"Warning: Unsupported comparison operator: {op}")
                result = ir.Constant(self.bool_type, 0)
        
        return result, 'bool'
    
    def _generate_function_declaration(self, stmt):
        """Generate code for function declaration"""
        _, func_name, params, body = stmt
        
        # Define parameter types
        param_types = []
        param_names = []
        for param_type, param_name in params:
            param_types.append(self._get_llvm_type(param_type))
            param_names.append(param_name)
        
        # Create function type
        func_type = ir.FunctionType(self.int_type, param_types)
        
        # Create function
        func = ir.Function(self.module, func_type, name=func_name)
        
        # Set parameter names
        for i, arg in enumerate(func.args):
            arg.name = param_names[i]
        
        # Create entry block
        entry_block = func.append_basic_block(name="entry")
        
        # Save current builder state
        old_builder = self.builder
        old_function = self.function
        old_variables = self.variables.copy()
        
        # Set up new function context
        self.builder = ir.IRBuilder(entry_block)
        self.function = func
        self.variables = {}
        
        # Allocate memory for parameters and store argument values
        for i, (param_type, param_name) in enumerate(params):
            llvm_type = self._get_llvm_type(param_type)
            alloca = self.builder.alloca(llvm_type, name=param_name)
            self.builder.store(func.args[i], alloca)
            self.variables[param_name] = {'ptr': alloca, 'type': param_type}
        
        # Generate code for function body
        for stmt in body:
            if stmt is not None:
                self._generate_statement(stmt)
        
        # Add implicit return if needed
        if not self.builder.block.is_terminated:
            self.builder.ret(ir.Constant(self.int_type, 0))
        
        # Store function in our function table
        self.functions[func_name] = {
            'func': func,
            'return_type': 'int',  # Default return type
            'param_types': [param_type for param_type, _ in params]
        }
        
        # Restore previous builder state
        self.builder = old_builder
        self.function = old_function
        self.variables = old_variables
    
    def _generate_function_call(self, stmt, is_expr=False):
        """Generate code for function call"""
        _, func_name, args = stmt
        
        # Generate code for arguments
        arg_values = []
        for arg in args:
            value, _ = self._generate_expression(arg)
            arg_values.append(value)
        
        # Get the function
        if func_name in self.functions:
            func = self.functions[func_name]['func']
            return_type = self.functions[func_name]['return_type']
        elif func_name == 'printf':
            func = self.printf
            return_type = 'int'
        elif func_name == 'scanf':
            func = self.scanf
            return_type = 'int'
        else:
            # Try to find the function in the module
            func = self.module.get_global(func_name)
            if not func:
                raise ValueError(f"Function '{func_name}' not declared")
            return_type = 'int'  # Default return type
        
        # Call the function
        call = self.builder.call(func, arg_values)
        
        # Return the call value and type if used as an expression
        if is_expr:
            return call, return_type
        return None, None
    
    def _generate_conditional(self, stmt):
        """Generate code for conditional statements"""
        if stmt[0] == 'if':
            _, condition, then_body = stmt
            
            # Create blocks
            then_block = self.function.append_basic_block(name="then")
            end_block = self.function.append_basic_block(name="endif")
            
            # Generate condition code
            cond_val, cond_type = self._generate_expression(condition)
            
            # Ensure condition is a boolean
            if cond_type != 'bool':
                if cond_type == 'float':
                    cond_val = self.builder.fcmp_ordered('!=', cond_val, ir.Constant(self.float_type, 0.0))
                else:
                    cond_val = self.builder.icmp_signed('!=', cond_val, ir.Constant(self.int_type, 0))
            
            self.builder.cbranch(cond_val, then_block, end_block)
            
            # Generate code for then block
            self.builder.position_at_end(then_block)
            for s in then_body:
                if s is not None:
                    self._generate_statement(s)
            
            # Jump to end block if not already terminated
            if not self.builder.block.is_terminated:
                self.builder.branch(end_block)
            
            # Continue in end block
            self.builder.position_at_end(end_block)
            
        else:  # if_else
            _, condition, then_body, else_body = stmt
            
            # Create blocks
            then_block = self.function.append_basic_block(name="then")
            else_block = self.function.append_basic_block(name="else")
            end_block = self.function.append_basic_block(name="endif")
            
            # Generate condition code
            cond_val, cond_type = self._generate_expression(condition)
            
            # Ensure condition is a boolean
            if cond_type != 'bool':
                if cond_type == 'float':
                    cond_val = self.builder.fcmp_ordered('!=', cond_val, ir.Constant(self.float_type, 0.0))
                else:
                    cond_val = self.builder.icmp_signed('!=', cond_val, ir.Constant(self.int_type, 0))
            
            self.builder.cbranch(cond_val, then_block, else_block)
            
            # Generate code for then block
            self.builder.position_at_end(then_block)
            for s in then_body:
                if s is not None:
                    self._generate_statement(s)
            
            # Jump to end block if not already terminated
            if not self.builder.block.is_terminated:
                self.builder.branch(end_block)
            
            # Generate code for else block
            self.builder.position_at_end(else_block)
            for s in else_body:
                if s is not None:
                    self._generate_statement(s)
            
            # Jump to end block if not already terminated
            if not self.builder.block.is_terminated:
                self.builder.branch(end_block)
            
            # Continue in end block
            self.builder.position_at_end(end_block)
    
    def _generate_while_loop(self, stmt):
        """Generate code for while loops"""
        _, condition, body = stmt
        
        # Create blocks
        cond_block = self.function.append_basic_block(name="while_cond")
        body_block = self.function.append_basic_block(name="while_body")
        end_block = self.function.append_basic_block(name="while_end")
        
        # Jump to condition block
        self.builder.branch(cond_block)
        
        # Generate condition code
        self.builder.position_at_end(cond_block)
        cond_val, cond_type = self._generate_expression(condition)
        
        # Ensure condition is a boolean
        if cond_type != 'bool':
            if cond_type == 'float':
                cond_val = self.builder.fcmp_ordered('!=', cond_val, ir.Constant(self.float_type, 0.0))
            else:
                cond_val = self.builder.icmp_signed('!=', cond_val, ir.Constant(self.int_type, 0))
        
        self.builder.cbranch(cond_val, body_block, end_block)
        
        # Generate code for loop body
        self.builder.position_at_end(body_block)
        for s in body:
            if s is not None:
                self._generate_statement(s)
        
        # Jump back to condition block
        self.builder.branch(cond_block)
        
        # Continue in end block
        self.builder.position_at_end(end_block)
    
    def _generate_for_loop(self, stmt):
        """Generate code for for loops"""
        _, init, condition, increment, body = stmt
        
        # Generate initialization code
        if init is not None:
            self._generate_statement(init)
        
        # Create blocks
        cond_block = self.function.append_basic_block(name="for_cond")
        body_block = self.function.append_basic_block(name="for_body")
        incr_block = self.function.append_basic_block(name="for_incr")
        end_block = self.function.append_basic_block(name="for_end")
        
        # Jump to condition block
        self.builder.branch(cond_block)
        
        # Generate condition code
        self.builder.position_at_end(cond_block)
        cond_val, cond_type = self._generate_expression(condition)
        
        # Ensure condition is a boolean
        if cond_type != 'bool':
            if cond_type == 'float':
                cond_val = self.builder.fcmp_ordered('!=', cond_val, ir.Constant(self.float_type, 0.0))
            else:
                cond_val = self.builder.icmp_signed('!=', cond_val, ir.Constant(self.int_type, 0))
                
        self.builder.cbranch(cond_val, body_block, end_block)
        
        # Generate code for loop body
        self.builder.position_at_end(body_block)
        for s in body:
            if s is not None:
                self._generate_statement(s)
        
        # Jump to increment block
        self.builder.branch(incr_block)
        
        # Generate increment code
        self.builder.position_at_end(incr_block)
        if increment is not None:
            self._generate_statement(increment)
        
        # Jump back to condition block
        self.builder.branch(cond_block)
        
        # Continue in end block
        self.builder.position_at_end(end_block)
    
    def _generate_return(self, stmt):
        """Generate code for return statements"""
        _, expr = stmt
        
        # Generate expression code
        ret_val, ret_type = self._generate_expression(expr)
        
        # Convert to function return type if needed
        if ret_type != 'int':  # Assuming all functions return int for now
            if ret_type == 'float':
                ret_val = self.builder.fptosi(ret_val, self.int_type)
            elif ret_type == 'bool':
                ret_val = self.builder.zext(ret_val, self.int_type)
            # Strings can't be converted to int automatically
        
        # Return the value
        self.builder.ret(ret_val)
    
    def _generate_print(self, stmt):
        """Generate code for print statements"""
        _, expr = stmt

        # Generate expression code
        expr_val, expr_type = self._generate_expression(expr)

        # Determine the format string based on expression type
        if expr_type == 'int':
            fmt_str = "%d\n"
        elif expr_type == 'float':
            fmt_str = "%f\n"
        elif expr_type == 'string':
            fmt_str = "%s\n"
        elif expr_type == 'bool':
            fmt_str = "%d\n"  # booleans printed as integers
            # Convert bool to int if needed
            if expr_val.type != self.int_type:
                expr_val = self.builder.zext(expr_val, self.int_type)
        else:
            fmt_str = "%d\n"  # default

        # Check if the format string already exists in the cache
        if fmt_str in self.fmt_globals:
            fmt_const = self.fmt_globals[fmt_str]
        else:
            # Create format string global constant
            fmt_data = bytearray((fmt_str + '\0').encode('utf8'))
            fmt_name = f".str.fmt.{hash(fmt_str) & 0xffffffff}"
            fmt_const = ir.GlobalVariable(self.module, 
                                        ir.ArrayType(ir.IntType(8), len(fmt_data)),
                                        name=fmt_name)
            fmt_const.global_constant = True
            fmt_const.linkage = 'internal'
            fmt_const.initializer = ir.Constant(ir.ArrayType(ir.IntType(8), len(fmt_data)), 
                                                bytearray(fmt_data))
            self.fmt_globals[fmt_str] = fmt_const

        fmt_ptr = self.builder.bitcast(fmt_const, self.char_ptr_type)

        # Call printf with the format pointer and the expression value
        self.builder.call(self.printf, [fmt_ptr, expr_val])

    
    def _generate_read(self, stmt):
        """Generate code for read statements"""
        # Allocate a temporary int variable to store the input
        temp_var = self.builder.alloca(self.int_type, name="read_temp")
        
        # Create a format string for scanf (e.g., "%d\0")
        fmt_str = "%d"
        fmt_data = bytearray((fmt_str + '\0').encode('utf8'))
        fmt_const = ir.GlobalVariable(self.module, 
                                    ir.ArrayType(ir.IntType(8), len(fmt_data)),
                                    name=".str.scanf")
        fmt_const.global_constant = True
        fmt_const.linkage = 'internal'
        fmt_const.initializer = ir.Constant(ir.ArrayType(ir.IntType(8), len(fmt_data)), fmt_data)
        
        # Get a pointer to the format string
        fmt_ptr = self.builder.bitcast(fmt_const, self.char_ptr_type)
        
        # Call scanf with the format string and the address of temp_var
        self.builder.call(self.scanf, [fmt_ptr, temp_var])
        
        # Optionally, load the value read (if you need to use it later)
        read_value = self.builder.load(temp_var, name="read_value")
        # If the read value should be stored into a variable or used, handle that here.
        # For now, we simply generate the read without assigning it elsewhere.
    
    def optimize_ir(self, ir_code):
        """Optimize LLVM IR code using llvmlite's pass manager"""
        llvm_module = llvm.parse_assembly(ir_code)
        llvm_module.verify()
        output_filename = "unoptimized.ll"
        with open(output_filename, 'w') as f:
            f.write(str(ir_code))
        

        # Create a target machine representing the host
        target = llvm.Target.from_default_triple()
        target_machine = target.create_target_machine()

        # Create a pass manager and apply standard optimizations
        pass_manager = llvm.PassManagerBuilder()
        pass_manager.opt_level = 2  # Level 0 (none) to 3 (aggressive)
        pm = llvm.ModulePassManager()
        pass_manager.populate(pm)

        pm.run(llvm_module)
        # Save it to a .ll file
        output_filename = "program.ll"
        with open(output_filename, 'w') as f:
            f.write(str(llvm_module))
        return str(llvm_module)

