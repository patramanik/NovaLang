# 📖 NovaLang Complete Language Documentation & Reference Manual

Welcome to the complete language reference manual for **NovaLang**—the universal, multi-paradigm programming language ecosystem. This guide covers installation, the command-line interface, language grammar rules, the standard library API, execution targets (Virtual Machine & AOT Compiler), and developer tooling.

---

## 1. Introduction

NovaLang is designed to bridge the gap between high-performance systems languages (e.g., C++, Rust) and rapid-development scripting languages (e.g., Python, JavaScript).

### Core Highlights
* **Optional Gradual Typing**: Prototype quickly with dynamic, untyped variables, or specify static types to enforce safety and optimize native builds.
* **Dual-Backend Runtime**: Execute instant bytecode scripts or REPL shells via the stack-based Virtual Machine, or compile directly to target-optimized native executables (`.exe`) via LLVM.
* **Hybrid Memory Safety**: Default allocations utilize nursery-based, thread-local Generational Copying Garbage Collection (<5ms pause times). Low-level hardware operations can bypass the GC inside explicit `unsafe` blocks.

---

## 2. Installation & Setup

You can install NovaLang using the pre-compiled Standalone SDK or directly from the Python source code.

### Option A: Standalone Windows SDK installation
1. Download **`nova-sdk-windows.zip`** from the release page.
2. Extract the folder to your preferred location.
3. Open PowerShell inside the extracted directory and run the automated installer:
   ```powershell
   .\install.ps1
   ```
4. Restart your terminal. The `nova` command is now globally registered in your User `PATH`.

### Option B: Running from Python Source
Ensure you have **Python 3.10+** (Python 3.13 recommended) installed:
1. Clone the repository and navigate to the directory.
2. Install the package in editable mode:
   ```bash
   pip install -e .
   ```

### AOT Compilation Prerequisites
Ahead-of-Time (AOT) native builds (`nova build <file>`) compile into LLVM assembly and require **LLVM Clang** installed on your system's path:
* **Windows**: Install *Desktop development with C++* via Visual Studio Installer, or download from the [LLVM Releases](https://github.com/llvm/llvm-project/releases).
* **Linux**: `sudo apt install clang`
* **macOS**: `xcode-select --install`

---

## 3. Command-Line Interface (CLI)

The `nova` command orchestrates execution, project bootstrapping, compilation, debugging, and IDE services.

### `nova init <project_name>`
Creates a standard, modular NovaLang project workspace.
```text
my_project/
├── src/
│   └── main.nova  # Entrypoint code
└── nova.toml       # Manifest and dependency config
```

### `nova run [file]`
Executes a source script (`.nova`) or compiled bytecode (`.novac`).
* **Walking Interpreter Mode** (Default): `nova run script.nova`
* **Virtual Machine Mode**: `nova run script.nova --vm`
* **Direct Bytecode Execution**: `nova run build/script.novac`

### `nova build [file]`
Compiles source files.
* **LLVM AOT Native Build** (Default): `nova build script.nova`  
  Generates target-optimized assembly `build/script.ll` and native executable `build/script.exe` (using Clang).
* **Bytecode VM Build**: `nova build script.nova --vm`  
  Generates JSON bytecode representation `build/script.novac`.

### `nova repl`
Launches the interactive Read-Eval-Print Loop.

### `nova debug [file]`
Launches the interactive step-by-step console-based bytecode debugger for the Virtual Machine.

### `nova lsp`
Starts the JSON-RPC Language Server daemon for IDEs.

---

## 4. Syntax & Language Guide

### 4.1 Variables & Typing

NovaLang supports both static typing and dynamic typing side-by-side:

```typescript
// 1. Statically-typed Read-only Bindings
let pi = 3.14159
let greeting: String = "Hello, Nova!"

// 2. Statically-typed Mutable Variables (no keyword required)
age: Int = 21
age = 22 // OK
// age = "twenty-two" -> Raises a compilation/interpreter type error

// 3. Dynamically-typed Variables
// Declared implicitly (without 'let' or type prefix)
value = 42
value = "Now I am a String" // OK, type checked dynamically
```

### 4.2 Built-in Primitive Types
* **`Int`**: 32-bit signed integers (e.g., `100`, `-5`).
* **`Float`**: 64-bit double-precision floating-point numbers (e.g., `3.14`).
* **`String`**: Unicode string literals (e.g., `"NovaLang"`, `"Line\nbreak"`).
* **`Bool`**: Boolean values (`true`, `false`).
* **`Null`**: Represents the absence of a value (`null`).

---

### 4.3 Control Flow & Loops

#### Conditional Branches
Condition checks do not require parentheses. Code blocks must be wrapped in curly braces `{}`.
```typescript
let score = 85

if score >= 90 {
    print("Grade A")
} else if score >= 80 {
    print("Grade B")
} else {
    print("Grade C")
}
```

#### Pattern Matching
Pattern matching evaluates expressions against specific branches. The fallback match is denoted by `_`.
```rust
let choice = 2

match choice {
    1 => { print("First option") }
    2 => { print("Second option") }
    _ => { print("Unknown selection") }
}
```

---

### 4.4 Functions

Functions are defined with the `fun` keyword, typed parameter sets, and an optional return type annotation (defaults to `Int` if omitted).

```typescript
fun calculate(x: Int, y: Int): Int {
    let factor = 2
    return (x + y) * factor
}

let result = calculate(10, 5) // result is 30
```

---

### 4.5 Object-Oriented Programming (OOP)

NovaLang supports clean OOP structures utilizing single inheritance and interface behavior contracts.

#### Interfaces
Interfaces declare behavior contracts containing function signatures without implementations.
```typescript
interface Animal {
    fun speak()
    fun get_legs(): Int
}
```

#### Classes & Inheritance
Classes declare properties, constructors (`init`), and methods. Inheritance is designated using `extends`. Use `self` to refer to class properties and methods.
```typescript
class Dog extends Animal {
    name: String
    legs: Int

    init(name: String) {
        self.name = name
        self.legs = 4
    }

    fun speak() {
        print(self.name + " says: Woof!")
    }

    fun get_legs(): Int {
        return self.legs
    }
}

// Instantiate and invoke
let buddy = Dog("Buddy")
buddy.speak() // Prints: Buddy says: Woof!
```

---

### 4.6 Exception Handling

NovaLang supports robust exception handling using the standard `try`, `catch`, `finally`, `throw`, and `throws` keywords.

#### Exception Keywords
* **`try`**: Wraps a block of code where runtime errors or explicit exceptions might be thrown.
* **`catch`**: Handles exceptions thrown inside the corresponding `try` block. Can specify an optional variable name and exception type annotation: `catch(e: ExceptionType) { ... }` or just `catch(e) { ... }`.
* **`finally`**: Optional. Defines a cleanup block that is guaranteed to run after the `try` (and any matching `catch`) blocks exit, regardless of whether an exception was thrown or caught.
* **`throw`**: Explicitly throws an exception object or value. Example: `throw "Something went wrong"`.
* **`throws`**: Declares in a function signature that the function may propagate specified exceptions to its caller.

#### Quick Example
```typescript
fun checkAge(age: Int) throws UnderageError {
    if age < 18 {
        throw "UnderageError: Access denied."
    }
    print("Access granted.")
}

try {
    checkAge(16)
} catch(err) {
    print("Caught error: " + err)
} finally {
    print("Execution checklist finished.")
}
```

---

## 5. Standard Library Reference

Standard libraries are organized under modular packages in `novalang/stdlib/` and imported using the scripting-style `import <name>` syntax.

### 5.1 `import math`
Provides core math operations:

| Signature | Returns | Description |
| :--- | :--- | :--- |
| `math.sqrt(x: Float)` | `Float` | Returns the square root of `x`. |
| `math.sin(x: Float)` | `Float` | Returns the sine of `x` (in radians). |
| `math.cos(x: Float)` | `Float` | Returns the cosine of `x` (in radians). |
| `math.abs(x: Float)` | `Float` | Returns the absolute value of `x`. |
| `math.min(a: Float, b: Float)` | `Float` | Returns the smaller value of `a` and `b`. |
| `math.max(a: Float, b: Float)` | `Float` | Returns the larger value of `a` and `b`. |

---

### 5.2 `import string`
Provides string manipulation operations:

| Signature | Returns | Description |
| :--- | :--- | :--- |
| `string.upper(s: String)` | `String` | Returns `s` in uppercase. |
| `string.lower(s: String)` | `String` | Returns `s` in lowercase. |
| `string.split(s: String, sep: String)` | `List` | Splits `s` into a list using delimiter `sep`. |
| `string.join(items: List, sep: String)` | `String` | Joins a list of items into a string separated by `sep`. |

---

### 5.3 `import io`
Provides standard console input/output and file system access:

| Signature | Returns | Description |
| :--- | :--- | :--- |
| `io.readline()` | `String` | Reads a line of input from standard input (stdin). |
| `io.readfile(path: String)` | `String` | Reads the entire content of file at `path`. |
| `io.writefile(path: String, content: String)` | `Int` | Writes `content` string to file at `path` (returns 1 on success). |

---

### 5.4 `import collection`
Provides dynamic data structures (Lists and Maps):

| Signature | Returns | Description |
| :--- | :--- | :--- |
| `collection.list()` | `List` | Creates and returns a new empty dynamic list. |
| `collection.list_add(l: List, val)` | `List` | Appends `val` to list `l` and returns the list. |
| `collection.list_get(l: List, idx: Int)` | `Any` | Retrieves the element at index `idx`. |
| `collection.list_len(l: List)` | `Int` | Returns the number of elements in list `l`. |
| `collection.map()` | `Map` | Creates and returns a new empty key-value map. |
| `collection.map_set(m: Map, k, v)` | `Map` | Binds key `k` to value `v` in map `m` and returns the map. |
| `collection.map_get(m: Map, k)` | `Any` | Retrieves value associated with key `k`, or returns `Null`. |
| `collection.map_has(m: Map, k)` | `Bool` | Returns `true` if key `k` exists in map `m`, else `false`. |

```typescript
import collection

// Working with Lists
let fruits = collection.list()
collection.list_add(fruits, "Apple")
collection.list_add(fruits, "Banana")
print(collection.list_get(fruits, 1)) // "Banana"
print(collection.list_len(fruits))    // 2

// Working with Maps
let user = collection.map()
collection.map_set(user, "name", "Manik")
collection.map_set(user, "age", 21)
if collection.map_has(user, "name") {
    print(collection.map_get(user, "name")) // "Manik"
}
```

---

### 5.5 `import net`
Provides mock socket operations and networking bindings:

| Signature | Returns | Description |
| :--- | :--- | :--- |
| `net.request(url: String)` | `String` | Performs a simulated HTTP GET request to `url`. |
| `net.listen(port: Int)` | `Int` | Binds a mock TCP socket to `port` (returns 1 on success). |

---

### 5.6 `import crypto`
Provides hashing utilities:

| Signature | Returns | Description |
| :--- | :--- | :--- |
| `crypto.sha256(s: String)` | `String` | Generates the SHA-256 hash string for input `s`. |
| `crypto.md5(s: String)` | `String` | Generates the MD5 hash string for input `s`. |

---

### 5.7 `import db`
Provides structured database query drivers:

| Signature | Returns | Description |
| :--- | :--- | :--- |
| `db.connect(url: String)` | `String` | Connects to database at `url` (returns connection string). |
| `db.query(conn: String, sql: String)` | `List` | Executes mock `sql` query on database connection `conn`. |

---

### 5.8 `import ai`
Provides vector math helpers for model building:

| Signature | Returns | Description |
| :--- | :--- | :--- |
| `ai.dot_product(v1: List, v2: List)` | `Float` | Computes the dot product of float lists `v1` and `v2`. |
| `ai.sigmoid(x: Float)` | `Float` | Computes the sigmoid activation value for `x`. |

---

## 6. Execution Backends & Runtimes

NovaLang supports dual execution models: AOT LLVM Compilation and Stack-based Bytecode Virtual Machine.

### 6.1 Ahead-of-Time (AOT) LLVM Compiler
* Translates source instructions directly into **LLVM IR assembly** (`.ll`).
* Performs optimization passes, resolving global variable scopes, type layouts, and function definitions.
* Standard `print` commands map to dynamic native bindings referencing C's `printf`.
* Native mathematical libraries map directly to CPU vectors or system C libraries.
* Compiles output assembly into standalone binaries (`.exe` / ELF) via **Clang**.

### 6.2 Virtual Machine (VM) & Generational Garbage Collector
* The VM compiles source code into JSON-serialized custom instructions (`.novac`).
* Features an execution engine processing registers, call frames, and operand stacks.
* **Nursery Generational GC**:
  * Allocations begin in a thread-local nursery heap.
  * When nursery size reaches capacity, the GC pauses execution to scan root registers (call frame variables, globals, active stacks).
  * Reachable referenced objects are promoted to the `old_generation` heap space. Unreferenced nursery variables are immediately recycled.

---

## 7. Developer Tooling

### 7.1 Interactive CLI Debugger (`nova debug <file>`)
Step through compiled VM bytecode command by command:

| Command | Shortcut | Description |
| :--- | :--- | :--- |
| `step` | `s` | Executes the next single instruction. |
| `continue` | `c` | Resumes execution until a breakpoint or exit. |
| `break <line>` | `b <line>`| Registers a breakpoint at the given bytecode offset. |
| `stack` | `p` | Prints the current operand stack. |
| `locals` | `l` | Prints local variables in the current call frame. |
| `globals` | `g` | Prints all global variables. |
| `list` | `v` | Lists all bytecode instructions. |
| `help` | `h` | Lists all debugger utility commands. |

### 7.2 Language Server Protocol (LSP)
The LSP daemon (`nova lsp`) integrates with IDEs to publish real-time feedback:
* **Diagnostics**: Live parser and lexer syntax checking.
* **Completions**: Autocompletes standard libraries, types, and keywords.
* **Hover tooltips**: Renders documentation popups for functions and signatures.
