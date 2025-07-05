import re
import subprocess

class LLVMToNasmConverter:
    def __init__(self):
        self.nasm_code = []
        self.data_section = []
        self.text_section = []
        self.external_functions = []

    def parse_ir(self, llvm_ir):
        lines = llvm_ir.split('\n')
        for line in lines:
            line = line.strip()
            if line.startswith('@'):
                self.parse_global_constant(line)
            elif line.startswith('declare'):
                self.parse_declare(line)
            elif line.startswith('define'):
                self.parse_function(line)
            elif line.startswith(';') or not line:
                continue
            else:
                self.text_section.append(line)
        self.generate_nasm_code()

    def parse_global_constant(self, line):
        match = re.match(r'@([\w\.]+) = internal constant \[\d+ x i8\] c"(.*)\\00"', line)
        if match:
            var_name = match.group(1)
            string_value = match.group(2).replace('\\0A', '\\n').replace('\\\\', '\\')
            self.data_section.append(f'{var_name} db "{string_value}", 0')

    def parse_declare(self, line):
        match = re.match(r'declare .* @([\w]+)\(.*\)', line)
        if match:
            self.external_functions.append(match.group(1))

    def parse_function(self, line):
        if re.match(r'define i32 @main\(\)', line):
            self.text_section.append('global _start\n\n_start:')
            self.text_section.append('  ; Translated code will be inserted here')

    def generate_nasm_code(self):
        self.nasm_code.append('section .data')
        for line in self.data_section:
            self.nasm_code.append(f'    {line}')
        
        self.nasm_code.append('\nsection .text')
        for ext in self.external_functions:
            self.nasm_code.append(f'    extern {ext}')
        
        for line in self.text_section:
            self.nasm_code.append(f'    {line}')
        
        self.nasm_code.append('    mov rax, 60')
        self.nasm_code.append('    xor rdi, rdi')
        self.nasm_code.append('    syscall')

    def get_nasm_code(self):
        return '\n'.join(self.nasm_code)

    def save_to_file(self, filename):
        with open(filename, 'w') as file:
            file.write(self.get_nasm_code())
        print(f"NASM code saved to {filename}")

def compile_and_run():
    
    compile_result = subprocess.run(["clang", "-o", "program.o", "-c", "program.ll"], capture_output=True, text=True)
    if compile_result.returncode != 0:
        print("❌ Compile error:\n", compile_result.stderr)
        return

    link_result = subprocess.run(["clang", "-o", "program", "program.o", "-lc"], capture_output=True, text=True)
    if link_result.returncode != 0:
        print("❌ Link error:\n", link_result.stderr)
        return

    print("Running program:")
    run_result = subprocess.run(["./program"], capture_output=True, text=True)
    print(run_result.stdout)

if __name__ == "__main__":
    try:
        with open("program.ll", "r") as file:
            llvm_ir = file.read()
    except FileNotFoundError:
        print("❌ Error: 'program.ll' file not found.")
        exit(1)

    # Convert and save NASM
    converter = LLVMToNasmConverter()
    converter.parse_ir(llvm_ir)
    converter.save_to_file("output.asm")

    # Compile and run the LLVM IR
    compile_and_run()
