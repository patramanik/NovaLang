# 🚀 NovaLang Developer User Guide

Welcome to the **NovaLang User Guide**! This manual is designed for developers who want to write, compile, and run programs in NovaLang. It details environment setup, syntax standards, data structures, standard libraries, and application development workflows.

---

## 1. Getting Started

### 1.1 Installation
To install the NovaLang SDK on Windows:
1. Extract the **`nova-sdk-windows.zip`** bundle.
2. Open PowerShell inside the folder and run:
   ```powershell
   .\install.ps1
   ```
3. Restart your terminal window. The `nova` command is now available globally.
4. Verify your installation by running:
   ```cmd
   nova repl
   ```

### 1.2 VS Code Syntax Highlighting
To enable syntax highlighting in Visual Studio Code:
1. Copy the `editors/vscode` directory from your extracted SDK folder.
2. Paste it into your local VS Code extensions directory:
   * **Windows**: `%USERPROFILE%\.vscode\extensions\novalang-extension`
   * **Linux/macOS**: `~/.vscode/extensions/novalang-extension`
3. Restart VS Code. `.nova` files will now render with full color formatting.

---

## 2. Managing Projects & Files

NovaLang supports both quick one-file scripts and structured multi-module projects.

### 2.1 Starting a Project
To create a new standard project workspace, run:
```bash
nova init my_app
```
This sets up a standard folder structure containing:
* `nova.toml` — The project manifest configuration.
* `src/main.nova` — The main application code entrypoint.

### 2.2 Executing Code
You can execute files in three ways depending on your requirements:

1. **Instant Run** (AST Walking Interpreter):
   ```bash
   nova run src/main.nova
   ```
2. **Virtual Machine Execution** (High-Performance Bytecode):
   ```bash
   nova run src/main.nova --vm
   ```
3. **Ahead-of-Time Native Compilation** (Compiles to a standalone machine executable):
   ```bash
   nova build src/main.nova
   ```
   This compiles your script to a native binary (`build/main.exe` on Windows). *Note: Requires Clang compiler installed on your system PATH.*

---

## 3. Language Basics

### 3.1 Variables & Scoping
NovaLang features a gradual, optional typing system. Variables can be declared with static types or implicit dynamic scopes.

```typescript
// 1. Constants (Read-only bindings)
let pi = 3.14159
let appName = "NovaApp"

// 2. Statically-typed Variables
// Type-safety is enforced at compile time.
age: Int = 21
age = 22 // OK
// age = "twenty-two" -> Compilation Error

// 3. Dynamically-typed Variables
// Declared implicitly. Can shift types during runtime.
userValue = 100
userValue = "Now I am a String!" // OK
```

### 3.2 Basic Types
* **`Int`**: Integers (e.g., `42`, `-7`).
* **`Float`**: Floating-point decimals (e.g., `9.81`, `-0.01`).
* **`String`**: Text wrapped in double quotes (e.g., `"Hello"`).
* **`Bool`**: Booleans (`true` or `false`).
* **`Null`**: Null value reference (`null`).

---

## 4. Control Flow & Patterns

### 4.1 Conditionals
Conditions do not require surrounding parentheses. Code blocks must be wrapped in curly braces `{}`.
```typescript
let threshold = 10

if threshold > 15 {
    print("Greater than 15")
} else if threshold == 10 {
    print("Exactly 10")
} else {
    print("Lesser than 10")
}
```

### 4.2 Pattern Matching (`match`)
Check values structurally against multiple code branches:
```rust
let status_code = 404

match status_code {
    200 => { print("Success") }
    404 => { print("Page Not Found") }
    500 => { print("Server Error") }
    _   => { print("Unknown Status") }
}
```

---

## 5. Functions & Methods

Functions are declared using the `fun` keyword. Stating parameter types and return type is recommended:

```typescript
fun greet(name: String, count: Int): String {
    print("Greeting user: " + name)
    return "Hello " + name
}

let message = greet("Manik", 1)
```

---

## 6. Object-Oriented Programming (OOP)

NovaLang supports structural classes, single inheritance, and interfaces.

### 6.1 Classes
Constructors are defined under the name `init`. Always use `self` to reference class members.

```typescript
class Account {
    owner: String
    balance: Float

    init(owner: String, initial_deposit: Float) {
        self.owner = owner
        self.balance = initial_deposit
    }

    fun deposit(amount: Float) {
        self.balance = self.balance + amount
        print("Deposited: " + amount)
    }

    fun show_balance() {
        print("Balance is: " + self.balance)
    }
}

let myAcc = Account("Manik", 500.0)
myAcc.deposit(150.0)
myAcc.show_balance() // Prints: Balance is: 650.0
```

### 6.2 Interfaces & Inheritance
Use `interface` to enforce contracts and `extends` for inheritance.
```typescript
interface Shape {
    fun area(): Float
}

class Square extends Shape {
    side: Float

    init(side: Float) {
        self.side = side
    }

    fun area(): Float {
        return self.side * self.side
    }
}

let sq = Square(5.0)
print(sq.area()) // 25.0
```

---

## 7. Exception Handling

NovaLang provides standard try-catch-finally constructs and exception throwing to safely recover from runtime errors.

### 7.1 Try-Catch-Finally Blocks
Wrap risky code in a `try` block. If an exception occurs, execution immediately jumps to the matching `catch` block. The optional `finally` block is guaranteed to run after both blocks complete.

```typescript
try {
    let result = 10 / 0 // VM division-by-zero error
} catch(err) {
    print("Handled error: " + err)
} finally {
    print("This runs no matter what!")
}
```

### 7.2 Custom Throws & Signatures
Functions that can propagate exceptions must declare them in their signature using the `throws` keyword:

```typescript
fun load_config(path: String) throws FileNotFoundError {
    if path == "" {
        throw "FileNotFoundError: Path is empty"
    }
    return "config"
}
```

---

## 8. Working with Collections

Import `collection` to manage dynamic arrays (Lists) and key-value dictionaries (Maps).

```typescript
import collection

// --- 1. LISTS ---
let list = collection.list()
collection.list_add(list, "Red")
collection.list_add(list, "Green")
collection.list_add(list, "Blue")

print(collection.list_len(list))     // Prints: 3
print(collection.list_get(list, 1))  // Prints: Green

// --- 2. MAPS ---
let settings = collection.map()
collection.map_set(settings, "theme", "dark")
collection.map_set(settings, "fontSize", 14)

if collection.map_has(settings, "theme") {
    let activeTheme = collection.map_get(settings, "theme")
    print("Active theme: " + activeTheme) // Active theme: dark
}
```

---

## 9. Standard Library API Checklist

Import standard library utilities directly using `import <module_name>`:

| Module | Core Functionality | Quick Example |
| :--- | :--- | :--- |
| **`math`** | Basic trig & algebra | `import math`<br>`let root = math.sqrt(16.0)` |
| **`string`** | Text casing and separation | `import string`<br>`let shout = string.upper("hi")` |
| **`io`** | Stdin/Stdout & File read/write | `import io`<br>`let content = io.readfile("data.txt")` |
| **`collection`** | Lists & Maps | `import collection`<br>`let list = collection.list()` |
| **`net`** | HTTP requests & sockets | `import net`<br>`let response = net.request("url")` |
| **`crypto`** | SHA-256 and MD5 hashing | `import crypto`<br>`let hash = crypto.sha256("passwd")` |
| **`db`** | SQL Database query execution | `import db`<br>`let conn = db.connect("sqlite://")` |
| **`ai`** | Vector dot-products & sigmoid | `import ai`<br>`let active = ai.sigmoid(0.5)` |
