# CForge-mini-compiler

# A Simple Compiler for XD Language

## Overview

**CForge** is a compiler for a custom C-like language called XD, developed as part of a university course project. The compiler performs lexical analysis, parsing, semantic analysis, and generates both LLVM IR and NASM assembly code. It also provides analysis outputs and AST visualization.

## Features

- **Lexical Analysis:** Tokenizes XD source code using PLY.
- **Parsing:** Builds an Abstract Syntax Tree (AST) and checks for syntax errors.
- **Semantic Analysis:** Type checking and symbol table management.
- **LLVM IR Generation:** Produces both unoptimized and optimized LLVM IR.
- **NASM Assembly Generation:** Converts IR to NASM assembly.
- **AST Visualization:** Generates a graphical representation of the AST.
- **Error Reporting:** Detects and reports syntax and semantic errors.
- **Support for:** Variables, functions, control flow (if, else, while, for), arithmetic and logical operations, I/O (print, read).


## Getting Started

### Prerequisites

- Python 3.7+
- [PLY](https://www.dabeaz.com/ply/) (`pip install ply`)
- [llvmlite](https://llvmlite.readthedocs.io/en/latest/) (`pip install llvmlite`)
- Graphviz (for AST visualization, install both the Python package and system binaries)
- NASM (for assembling output, optional)

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/yourusername/CC_Project.git
   cd CC_Project
   ```

2. **Install dependencies:**
   ```bash
   pip install ply llvmlite graphviz
   ```

3. **(Optional) Install Graphviz system binaries:**
   - [Download Graphviz](https://graphviz.gitlab.io/download/)

### Usage

1. **Compile an XD source file:**
   ```bash
   python main.py <source_file.xd>
   ```

2. **Outputs:**
   - `analysis/lexical_analysis.txt` — Lexical tokens
   - `analysis/symbol_table.txt` — Symbol table
   - `analysis/ir_unoptimized.ll` — Unoptimized LLVM IR
   - `analysis/ir_optimized.ll` — Optimized LLVM IR
   - `ast_visualization.png` — AST image
   - `output.asm` — NASM assembly (if NASM generator is run)

3. **Example:**
   ```bash
   python main.py basic.xd
   ```

### Example XD Program

```c
def factorial(int n) {
    if (n <= 1) {
        return 1;
    }
    int result = 1;
    for (int i = 2; i <= n; i = i + 1) {
        result = result * i;
    }
    return result;
}

int num = 4;
int fact = factorial(num);
print("Factorial of ");
print(num);
print("is");
print(fact);
```

## Development
- Example source files: `basic.xd`, `arithmetic.xd`, `function.xd`, `controlflow.xd`.

## Credits

- Developed by: Muhammad Ahtisham
- For: Compiler Construction Course (22F-3331)

## License

This project is for educational purposes. See LICENSE file if provided.
