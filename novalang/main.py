import sys
import os
import subprocess
import shutil
import json
from typing import Optional
from novalang.lexer import Lexer
from novalang.parser import Parser
from novalang.interpreter import Interpreter
from novalang.repl import run_repl
from novalang.compiler import LLVMCompiler
from novalang.codegen_vm import VMBytecodeGenerator
from novalang.vm import VirtualMachine
from novalang.lsp import start_lsp_server

import tomllib

def debug_file(path: str) -> bool:
    if not os.path.exists(path):
        print(f"Error: File '{path}' not found.", file=sys.stderr)
        return False
        
    if path.endswith(".novac"):
        try:
            with open(path, "r", encoding="utf-8") as f:
                bytecode = json.load(f)
        except Exception as e:
            print(f"Error loading bytecode: {e}", file=sys.stderr)
            return False
    else:
        try:
            with open(path, "r", encoding="utf-8") as f:
                source = f.read()
            lexer = Lexer(source)
            tokens = lexer.tokenize()
            parser = Parser(tokens)
            ast = parser.parse()
            if parser.errors:
                for err in parser.errors:
                    print(err, file=sys.stderr)
                return False
            codegen = VMBytecodeGenerator()
            bytecode = codegen.generate(ast)
        except Exception as e:
            print(f"Compilation Error: {e}", file=sys.stderr)
            return False
            
    from novalang.debug import VMDebugger
    debugger = VMDebugger(bytecode)
    debugger.run()
    return True

def run_file(path: str, use_vm: bool = False) -> bool:
    if not os.path.exists(path):
        print(f"Error: File '{path}' not found.", file=sys.stderr)
        return False
        
    if path.endswith(".novac"):
        try:
            with open(path, "r", encoding="utf-8") as f:
                bytecode = json.load(f)
            vm = VirtualMachine()
            vm.run(bytecode)
            return True
        except Exception as e:
            print(f"VM Execution Error: {e}", file=sys.stderr)
            return False
            
    with open(path, "r", encoding="utf-8") as f:
        source = f.read()
        
    try:
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        
        parser = Parser(tokens)
        ast = parser.parse()
        
        if parser.errors:
            for err in parser.errors:
                print(err, file=sys.stderr)
            return False
            
        if use_vm:
            codegen = VMBytecodeGenerator()
            bytecode = codegen.generate(ast)
            vm = VirtualMachine()
            vm.run(bytecode)
        else:
            interpreter = Interpreter()
            interpreter.interpret(ast)
        return True
        
    except Exception as e:
        print(f"Runtime Error: {e}", file=sys.stderr)
        return False

def build_file(path: str, use_vm: bool = False) -> bool:
    if not os.path.exists(path):
        print(f"Error: File '{path}' not found.", file=sys.stderr)
        return False
        
    with open(path, "r", encoding="utf-8") as f:
        source = f.read()
        
    try:
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        
        parser = Parser(tokens)
        ast = parser.parse()
        
        if parser.errors:
            for err in parser.errors:
                print(err, file=sys.stderr)
            return False
            
        toml_dir = find_toml_dir(os.path.dirname(path))
        
        if use_vm:
            codegen = VMBytecodeGenerator()
            bytecode = codegen.generate(ast)
            
            if toml_dir and os.path.abspath(path).startswith(os.path.abspath(toml_dir)):
                manifest = load_manifest(toml_dir)
                pkg_name = manifest.get("package", {}).get("name", "app")
                build_dir = os.path.join(toml_dir, "build")
                os.makedirs(build_dir, exist_ok=True)
                output_path = os.path.join(build_dir, f"{pkg_name}.novac")
            else:
                output_path = os.path.splitext(path)[0] + ".novac"
                
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(bytecode, f, indent=2)
            print(f"Bytecode generated successfully: {output_path}")
            return True
            
        else:
            compiler = LLVMCompiler()
            llvm_ir = compiler.compile(ast)
            
            if toml_dir and os.path.abspath(path).startswith(os.path.abspath(toml_dir)):
                manifest = load_manifest(toml_dir)
                pkg_name = manifest.get("package", {}).get("name", "app")
                build_dir = os.path.join(toml_dir, "build")
                os.makedirs(build_dir, exist_ok=True)
                output_path = os.path.join(build_dir, f"{pkg_name}.ll")
            else:
                output_path = os.path.splitext(path)[0] + ".ll"
                
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(llvm_ir)
            print(f"LLVM IR generated: {output_path}")
            
            clang_bin = shutil.which("clang")
            if not clang_bin and os.name == "nt":
                # Check common Windows LLVM installation paths
                for candidate in [
                    r"C:\Program Files\LLVM\bin\clang.exe",
                    r"C:\Program Files (x86)\LLVM\bin\clang.exe"
                ]:
                    if os.path.exists(candidate):
                        clang_bin = candidate
                        break
        
            if clang_bin:
                exe_ext = ".exe" if os.name == "nt" else ""
                exe_path = os.path.splitext(output_path)[0] + exe_ext
                try:
                    subprocess.run([clang_bin, output_path, "-o", exe_path], check=True)
                    print(f"Native binary generated successfully: {exe_path}")
                except Exception as ex:
                    print(f"Warning: Failed to compile LLVM IR to native binary via Clang: {ex}", file=sys.stderr)
            else:
                print("Note: Clang compiler not found. Native executable code generation skipped.")
                print("Install Clang (or add it to your PATH) to automatically generate native binaries from LLVM IR.")
                
            return True
        
    except Exception as e:
        print(f"Build Error: {e}", file=sys.stderr)
        return False

def init_project(name: str):
    if os.path.exists(name):
        if os.path.isdir(name) and os.listdir(name):
            print(f"Error: Directory '{name}' already exists and is not empty.", file=sys.stderr)
            sys.exit(1)
    else:
        os.makedirs(name, exist_ok=True)
        
    src_dir = os.path.join(name, "src")
    os.makedirs(src_dir, exist_ok=True)
    
    pkg_name = os.path.basename(os.path.normpath(name))
    
    # 1. Create nova.toml
    toml_content = f"""[package]
name = "{pkg_name}"
version = "0.1.0"
authors = ["Manik Patra <manikpatra409@gmail.com>"]
edition = "2026"

[dependencies]
# Add dependencies here
"""
    with open(os.path.join(name, "nova.toml"), "w", encoding="utf-8") as f:
        f.write(toml_content)
        
    # 2. Create src/main.nova
    main_nova_content = """// NovaLang Starter Project
// This file showcases the key features of NovaLang: gradual typing, custom functions, and pattern matching.

// 1. Statically-typed constant binding
let welcomeMessage = "Hello from NovaLang!"
print(welcomeMessage)

// 2. Mutable variable using static type annotation
count: Int = 10

// 3. Reusable function with static types
fun calculateSquare(n: Int): Int {
    return n * n
}

// 4. Cooperative control flow with if-else
let inputVal = 5
let squareResult = calculateSquare(inputVal)

if (squareResult > 20) {
    print("Square is greater than 20")
} else {
    print("Square is less than or equal to 20")
}

// 5. Pattern matching
print("Pattern matching example:")
match inputVal {
    1 => { print("One") }
    5 => { print("Five - Match found!") }
    _ => { print("Other value") }
}

print("Starter project execution complete!")
"""
    with open(os.path.join(src_dir, "main.nova"), "w", encoding="utf-8") as f:
        f.write(main_nova_content)
        
    # 3. Create README.md
    readme_content = f"""# {name}

A standard NovaLang project generated by `nova init`.

## Getting Started

To run the application:
```bash
nova run
```

To validate and build the application:
```bash
nova build
```

## Project Structure
* `nova.toml` - Package manifest and dependencies.
* `src/main.nova` - Entry point code file.
"""
    with open(os.path.join(name, "README.md"), "w", encoding="utf-8") as f:
        f.write(readme_content)
        
    # 4. Create .gitignore
    gitignore_content = """# NovaLang Build Artifacts
*.novac
__pycache__/
"""
    with open(os.path.join(name, ".gitignore"), "w", encoding="utf-8") as f:
        f.write(gitignore_content)
        
    print(f"Initialized standard NovaLang project in '{name}' successfully.")

def find_toml_dir(start_path: Optional[str] = None) -> Optional[str]:
    curr = os.path.abspath(start_path) if start_path else os.getcwd()
    while True:
        toml_path = os.path.join(curr, "nova.toml")
        if os.path.isfile(toml_path):
            return curr
        parent = os.path.dirname(curr)
        if parent == curr:
            break
        curr = parent
    return None

def load_manifest(toml_dir: str) -> dict:
    toml_path = os.path.join(toml_dir, "nova.toml")
    try:
        with open(toml_path, "rb") as f:
            return tomllib.load(f)
    except Exception as e:
        print(f"Error: Failed to parse '{toml_path}': {e}", file=sys.stderr)
        sys.exit(1)

def print_help():
    help_text = """NovaLang Package Manager and Interpreter CLI (v1.3.0)

Usage:
  nova <command> [arguments]

Commands:
  init <name>     Initialize a standard NovaLang project structure in a new folder
  run [file]      Run the project entry point (src/main.nova) or a specific file
                  Use --vm flag to execute using the stack Virtual Machine
  build [file]    Parse and validate the project entry point or a specific file
                  Use --vm flag to compile to a .novac bytecode file
  repl            Launch the interactive Read-Eval-Print Loop
  lsp             Launch the Language Server Protocol (LSP) daemon on stdio
  debug [file]    Launch the interactive bytecode debugger on a file
  help            Show this help documentation
  version         Show the version of NovaLang

Alternative:
  nova <path>     Directly executes a single .nova or .novac source file (backwards compatible)
"""
    print(help_text)

def main():
    if len(sys.argv) < 2:
        run_repl()
        return

    use_vm = False
    if "--vm" in sys.argv:
        use_vm = True
        sys.argv.remove("--vm")

    cmd = sys.argv[1]

    if cmd in ("init", "run", "build", "repl", "help", "version", "-h", "--help", "-v", "--version", "lsp", "debug"):
        if cmd == "init":
            if len(sys.argv) < 3:
                print("Error: Missing project name. Usage: nova init <name>", file=sys.stderr)
                sys.exit(1)
            init_project(sys.argv[2])
            
        elif cmd == "run":
            if len(sys.argv) >= 3:
                target = sys.argv[2]
                if os.path.isdir(target):
                    target = os.path.join(target, "src", "main.nova")
                if not run_file(target, use_vm=use_vm):
                    sys.exit(1)
            else:
                toml_dir = find_toml_dir()
                if not toml_dir:
                    print("Error: Could not find a 'nova.toml' in this directory or any parent directories.", file=sys.stderr)
                    sys.exit(1)
                load_manifest(toml_dir)
                entry_point = os.path.join(toml_dir, "src", "main.nova")
                if not run_file(entry_point, use_vm=use_vm):
                    sys.exit(1)
                    
        elif cmd == "build":
            if len(sys.argv) >= 3:
                target = sys.argv[2]
                if os.path.isdir(target):
                    target = os.path.join(target, "src", "main.nova")
                if not build_file(target, use_vm=use_vm):
                    sys.exit(1)
                else:
                    print("Build successful!")
            else:
                toml_dir = find_toml_dir()
                if not toml_dir:
                    print("Error: Could not find a 'nova.toml' in this directory or any parent directories.", file=sys.stderr)
                    sys.exit(1)
                manifest = load_manifest(toml_dir)
                entry_point = os.path.join(toml_dir, "src", "main.nova")
                if not build_file(entry_point, use_vm=use_vm):
                    sys.exit(1)
                else:
                    if use_vm:
                        print(f"Build successful for package '{manifest.get('package', {}).get('name', 'unknown')}' (Bytecode format)!")
                    else:
                        print(f"Build successful for package '{manifest.get('package', {}).get('name', 'unknown')}'!")
                    
        elif cmd == "repl":
            run_repl()
            
        elif cmd == "lsp":
            start_lsp_server()
            
        elif cmd == "debug":
            if len(sys.argv) >= 3:
                target = sys.argv[2]
                if os.path.isdir(target):
                    target = os.path.join(target, "src", "main.nova")
                if not debug_file(target):
                    sys.exit(1)
            else:
                toml_dir = find_toml_dir()
                if not toml_dir:
                    print("Error: Could not find a 'nova.toml' in this directory or any parent directories.", file=sys.stderr)
                    sys.exit(1)
                load_manifest(toml_dir)
                entry_point = os.path.join(toml_dir, "src", "main.nova")
                if not debug_file(entry_point):
                    sys.exit(1)
            
        elif cmd in ("help", "-h", "--help"):
            print_help()
            
        elif cmd in ("version", "-v", "--version"):
            print("NovaLang CLI v1.3.0")
            
    else:
        # Backwards compatible: run file directly if it exists
        if os.path.exists(cmd):
            if not run_file(cmd, use_vm=use_vm):
                sys.exit(1)
        else:
            print(f"Error: Unknown command or file '{cmd}'", file=sys.stderr)
            print("Run 'nova help' for usage instructions.", file=sys.stderr)
            sys.exit(1)

if __name__ == "__main__":
    main()
