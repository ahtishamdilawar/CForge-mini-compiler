import sys
import os
from lexer import Lexer
from parser import Parser
from ir_generator import IRGenerator
from llvm_ir_generator import LLVMIRGenerator
import subprocess

def main():
    if len(sys.argv) < 2:
        print("Usage: python main.py <source_file.c>")
        sys.exit(1)

    filename = sys.argv[1]

    try:
        with open(filename, "r") as f:
            source_code = f.read()
    except Exception as e:
        print(f"Error reading file {filename}: {e}")
        sys.exit(1)

    # Create analysis folder if not exists
    os.makedirs("analysis", exist_ok=True)

    # --- Lexical Analysis ---
    lexer = Lexer()
    tokens = lexer.test(source_code)

    with open("analysis/lexical_analysis.txt", "w") as lex_file:
        lex_file.write("=== Lexical Analysis ===\n")
        for token in tokens:
            lex_file.write(f"Type: {token[0]:<15} Value: {token[1]:<15} Line: {token[2]}\n")

    print("Lexical analysis saved to analysis/lexical_analysis.txt")

    # --- Parsing & Symbol Table ---
    parser = Parser()
    ast, symbol_table = parser.parse(source_code)

    with open("analysis/symbol_table.txt", "w") as sym_file:
        sym_file.write("=== Symbol Table ===\n")
        for name, info in symbol_table.items():
            sym_file.write(f"Name: {name:<15} Type: {info['type']}\n")

    print("Symbol table saved to analysis/symbol_table.txt")

    # --- LLVM IR Generation ---
    generator = LLVMIRGenerator()
    ir_unoptimized, ir_optimized = generator.generate(ast)

    with open("analysis/ir_unoptimized.ll", "w") as ir_file:
        ir_file.write(ir_unoptimized)

    with open("analysis/ir_optimized.ll", "w") as ir_file:
        ir_file.write(ir_optimized)

    print("LLVM IR saved to analysis/ir_unoptimized.ll and analysis/ir_optimized.ll")

    # --- Run NASM Generator ---
    print("Running nasmgenerator.py...")
    result = subprocess.run(["python3", "nasmgenerator.py"], capture_output=True, text=True)

    print(result.stdout)
    if result.stderr:
        print("Errors in nasmgenerator.py:\n", result.stderr)

if __name__ == "__main__":
    main()
