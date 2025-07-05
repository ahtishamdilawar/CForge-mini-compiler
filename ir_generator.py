class IRGenerator:
    def __init__(self):
        self.instructions = []
        self.temp_count = 0
        self.label_count = 0

    def new_temp(self):
        temp = f"t{self.temp_count}"
        self.temp_count += 1
        return temp

    def new_label(self):
        label = f"L{self.label_count}"
        self.label_count += 1
        return label

    def emit(self, *args):
        self.instructions.append(args)

    def generate(self, node):
        if node is None:
            return

        if isinstance(node, list):
            for stmt in node:
                self.generate(stmt)
            return

        node_type = node[0] if isinstance(node, tuple) else None

        if node_type == 'program':
            self.generate(node[1])

        elif node_type == 'declaration_init':
            _, var_type, name, expr = node
            temp = self.generate(expr)
            self.emit('assign', name, temp)

        elif node_type == 'declaration':
            _, var_type, name = node
            pass  # No-op for IR

        elif node_type == 'assignment':
            _, name, expr = node
            temp = self.generate(expr)
            self.emit('assign', name, temp)

        elif node_type == 'binop':
            _, op, left, right = node
            ltemp = self.generate(left)
            rtemp = self.generate(right)
            temp = self.new_temp()
            self.emit('binop', op, temp, ltemp, rtemp)
            return temp

        elif node_type == 'unop':
            _, op, operand = node
            otemp = self.generate(operand)
            temp = self.new_temp()
            self.emit('unop', op, temp, otemp)
            return temp

        elif node_type == 'print':
            val = self.generate(node[1])
            self.emit('print', val)

        elif node_type == 'return':
            retval = self.generate(node[1])
            self.emit('return', retval)

        elif node_type == 'if':
            _, cond, if_body = node
            cond_temp = self.generate(cond)
            else_label = self.new_label()
            end_label = self.new_label()
            self.emit('if_false_goto', cond_temp, else_label)
            self.generate(if_body)
            self.emit('goto', end_label)
            self.emit('label', else_label)
            self.emit('label', end_label)

        elif node_type == 'if_else':
            _, cond, if_body, else_body = node
            cond_temp = self.generate(cond)
            else_label = self.new_label()
            end_label = self.new_label()
            self.emit('if_false_goto', cond_temp, else_label)
            self.generate(if_body)
            self.emit('goto', end_label)
            self.emit('label', else_label)
            self.generate(else_body)
            self.emit('label', end_label)

        elif node_type == 'while_loop':
            _, cond, body = node
            start_label = self.new_label()
            end_label = self.new_label()
            self.emit('label', start_label)
            cond_temp = self.generate(cond)
            self.emit('if_false_goto', cond_temp, end_label)
            self.generate(body)
            self.emit('goto', start_label)
            self.emit('label', end_label)

        elif node_type == 'for_loop':
            _, init, cond, increment, body = node
            self.generate(init)
            start_label = self.new_label()
            end_label = self.new_label()
            self.emit('label', start_label)
            cond_temp = self.generate(cond)
            self.emit('if_false_goto', cond_temp, end_label)
            self.generate(body)
            self.generate(increment)
            self.emit('goto', start_label)
            self.emit('label', end_label)

        elif node_type == 'function_declaration':
            _, name, params, body = node
            self.emit('function', name, params)
            self.generate(body)
            self.emit('end_function', name)

        elif isinstance(node, int) or isinstance(node, float) or isinstance(node, str):
            temp = self.new_temp()
            self.emit('literal', temp, node)
            return temp

        elif isinstance(node, tuple) and node[0] == 'function_call':
            func_name = node[1]
            args = [self.generate(arg) for arg in node[2]]
            result = self.new_temp()
            self.emit('call', result, func_name, args)
            return result

        elif isinstance(node, str):
            return node  # variable name

    def get_ir(self):
        return self.instructions

    def print_ir(self):
        print("\n--- Intermediate Representation ---")
        for instr in self.instructions:
            print(instr)
