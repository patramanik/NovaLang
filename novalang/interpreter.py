from typing import Dict, Any, Optional, List
from novalang.ast import (
    ASTNode, Program, LetNode, AssignNode, BinaryOpNode, LiteralNode,
    IdentifierNode, PrintNode, BlockNode, FunctionDeclNode, CallNode, IfNode, MatchNode, ReturnNode,
    UnaryOpNode
)

class ReturnException(Exception):
    """Exception used to unwind call stacks for function returns."""
    def __init__(self, value: Any):
        self.value = value

class Environment:
    def __init__(self, parent: Optional['Environment'] = None):
        self.values: Dict[str, Any] = {}
        self.immutables: set[str] = set()
        self.types: Dict[str, Optional[str]] = {}
        self.parent = parent

    def has(self, name: str) -> bool:
        if name in self.values:
            return True
        if self.parent:
            return self.parent.has(name)
        return False

    def define(self, name: str, value: Any, is_const: bool = False, type_ann: Optional[str] = None):
        if name in self.values:
            raise RuntimeError(f"Redeclaration of variable '{name}' in the same scope")
        
        if type_ann:
            self._validate_type(name, value, type_ann)
            
        self.values[name] = value
        self.types[name] = type_ann
        if is_const:
            self.immutables.add(name)

    def assign(self, name: str, value: Any):
        if name in self.values:
            if name in self.immutables:
                raise RuntimeError(f"Cannot reassign read-only variable '{name}'")
            
            type_ann = self.types.get(name)
            if type_ann:
                self._validate_type(name, value, type_ann)
                
            self.values[name] = value
            return
            
        if self.parent:
            self.parent.assign(name, value)
            return
            
        # Implicit declaration in global/local scope via automatic type detection
        self.define(name, value, is_const=False, type_ann=None)

    def get(self, name: str) -> Any:
        if name in self.values:
            return self.values[name]
        if self.parent:
            return self.parent.get(name)
        raise RuntimeError(f"Undefined variable reference: '{name}'")

    def _validate_type(self, name: str, value: Any, type_ann: str):
        # Maps NovaLang type strings to Python types
        type_mapping = {
            "Int": int,
            "Float": float,
            "String": str,
            "Bool": bool
        }
        expected_type = type_mapping.get(type_ann)
        if expected_type is None:
            # Custom types/classes (unvalidated in simple script, passes checks)
            return
            
        if not isinstance(value, expected_type):
            raise TypeError(
                f"Type error for '{name}': Expected {type_ann}, but got value of type {type(value).__name__}"
            )

class Function:
    def __init__(self, decl: FunctionDeclNode, closure: Environment):
        self.decl = decl
        self.closure = closure

    def call(self, interpreter: 'Interpreter', args: List[Any]) -> Any:
        env = Environment(self.closure)
        if len(args) != len(self.decl.params):
            raise RuntimeError(
                f"Argument count mismatch for '{self.decl.name}': Expected {len(self.decl.params)}, got {len(args)}"
            )
            
        for (param_name, param_type), arg_val in zip(self.decl.params, args):
            env.define(param_name, arg_val, is_const=False, type_ann=param_type)
            
        try:
            interpreter.execute_block(self.decl.body, env)
        except ReturnException as ret:
            # Validate return type if specified
            if self.decl.return_type:
                # Basic check
                type_mapping = {"Int": int, "Float": float, "String": str, "Bool": bool}
                expected = type_mapping.get(self.decl.return_type)
                if expected and not isinstance(ret.value, expected):
                    raise TypeError(
                        f"Return type mismatch for '{self.decl.name}': Expected {self.decl.return_type}, got {type(ret.value).__name__}"
                    )
            return ret.value
            
        return None

class Interpreter:
    def __init__(self):
        self.globals = Environment()
        self.environment = self.globals
        
        # Add standard built-ins
        self.globals.define("print", print, is_const=True)
        self.globals.define("str", str, is_const=True)
        self.globals.define("int", int, is_const=True)
        self.globals.define("float", float, is_const=True)
        self.globals.define("len", len, is_const=True)

    def interpret(self, program: Program) -> Any:
        last_val = None
        for stmt in program.statements:
            last_val = self.evaluate(stmt)
        return last_val

    def execute_block(self, block: BlockNode, env: Environment):
        previous = self.environment
        try:
            self.environment = env
            for stmt in block.statements:
                self.evaluate(stmt)
        finally:
            self.environment = previous

    def evaluate(self, node: ASTNode) -> Any:
        if isinstance(node, LiteralNode):
            return node.value
            
        elif isinstance(node, IdentifierNode):
            return self.environment.get(node.name)
            
        elif isinstance(node, LetNode):
            val = self.evaluate(node.value)
            self.environment.define(node.name, val, is_const=True)
            return val
            
        elif isinstance(node, AssignNode):
            val = self.evaluate(node.value)
            if node.type_ann is not None:
                self.environment.define(node.name, val, is_const=False, type_ann=node.type_ann)
            elif self.environment.has(node.name):
                self.environment.assign(node.name, val)
            else:
                self.environment.define(node.name, val, is_const=False, type_ann=None)
            return val
            
        elif isinstance(node, BinaryOpNode):
            if node.op == "&&":
                left_val = self.evaluate(node.left)
                if not left_val:
                    return left_val
                return self.evaluate(node.right)
            elif node.op == "||":
                left_val = self.evaluate(node.left)
                if left_val:
                    return left_val
                return self.evaluate(node.right)
                
            left_val = self.evaluate(node.left)
            right_val = self.evaluate(node.right)
            
            if node.op == "+":
                return left_val + right_val
            elif node.op == "-":
                return left_val - right_val
            elif node.op == "*":
                return left_val * right_val
            elif node.op == "/":
                return left_val / right_val
            elif node.op == "%":
                return left_val % right_val
            elif node.op == "==":
                return left_val == right_val
            elif node.op == "!=":
                return left_val != right_val
            elif node.op == "<":
                return left_val < right_val
            elif node.op == ">":
                return left_val > right_val
            elif node.op == "<=":
                return left_val <= right_val
            elif node.op == ">=":
                return left_val >= right_val
            else:
                raise RuntimeError(f"Unknown operator: {node.op}")
                
        elif isinstance(node, UnaryOpNode):
            right_val = self.evaluate(node.right)
            if node.op == "-":
                return -right_val
            elif node.op == "+":
                return +right_val
            elif node.op == "!":
                return not right_val
            else:
                raise RuntimeError(f"Unknown unary operator: {node.op}")
                
        elif isinstance(node, PrintNode):
            val = self.evaluate(node.value)
            print(val)
            return val
            
        elif isinstance(node, BlockNode):
            env = Environment(self.environment)
            self.execute_block(node, env)
            return None
            
        elif isinstance(node, FunctionDeclNode):
            func = Function(node, self.environment)
            self.environment.define(node.name, func, is_const=True)
            return func
            
        elif isinstance(node, CallNode):
            func_val = self.evaluate(node.func)
            args = [self.evaluate(arg) for arg in node.args]
            
            if isinstance(func_val, Function):
                return func_val.call(self, args)
            elif callable(func_val):
                return func_val(*args)
            else:
                raise RuntimeError(f"Value '{node.func}' is not callable")
            
        elif isinstance(node, IfNode):
            cond_val = self.evaluate(node.condition)
            if cond_val:
                self.evaluate(node.then_branch)
            elif node.else_branch:
                self.evaluate(node.else_branch)
            return None
            
        elif isinstance(node, MatchNode):
            val_to_match = self.evaluate(node.value)
            for pattern, body in node.cases:
                # Match wildcard '_' or identical values
                if isinstance(pattern, IdentifierNode) and pattern.name == "_":
                    # Wildcard match
                    self.evaluate(body)
                    break
                
                pat_val = self.evaluate(pattern)
                if pat_val == val_to_match:
                    self.evaluate(body)
                    break
            return None
            
        elif isinstance(node, ReturnNode):
            val = self.evaluate(node.value) if node.value else None
            raise ReturnException(val)
            
        raise RuntimeError(f"Unknown AST node type: {type(node).__name__}")
