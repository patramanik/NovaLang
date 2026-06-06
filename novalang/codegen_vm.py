from typing import List, Dict, Any
from novalang.ast import (
    ASTNode, Program, LetNode, AssignNode, BinaryOpNode, LiteralNode,
    IdentifierNode, PrintNode, BlockNode, FunctionDeclNode, CallNode, IfNode, MatchNode, ReturnNode,
    UnaryOpNode
)

class VMBytecodeGenerator:
    def __init__(self):
        self.instructions: List[list] = []
        self.functions: Dict[str, dict] = {}
        self.label_counter = 0

    def next_label(self, prefix: str) -> str:
        self.label_counter += 1
        return f"{prefix}_{self.label_counter}"

    def generate(self, program: Program) -> dict:
        self.instructions = []
        self.functions = {}
        
        # Split functions from top-level instructions
        functions_nodes = []
        toplevel_nodes = []
        for stmt in program.statements:
            if isinstance(stmt, FunctionDeclNode):
                functions_nodes.append(stmt)
            else:
                toplevel_nodes.append(stmt)
                
        # Compile functions first
        for fn in functions_nodes:
            self.compile_function(fn)
            
        # Compile main instructions
        for stmt in toplevel_nodes:
            self.compile_node(stmt, self.instructions)
            
        # Append HALT to main instructions if not empty
        self.instructions.append(["HALT"])
        
        # Resolve labels for main
        resolved_main = self.resolve_labels(self.instructions)
        
        # Resolve labels for all compiled functions
        resolved_functions = {}
        for fn_name, fn_info in self.functions.items():
            resolved_functions[fn_name] = {
                "params": fn_info["params"],
                "body": self.resolve_labels(fn_info["body"])
            }
            
        return {
            "functions": resolved_functions,
            "main": resolved_main
        }

    def compile_function(self, node: FunctionDeclNode):
        func_body = []
        
        for stmt in node.body.statements:
            self.compile_node(stmt, func_body)
            
        # Check if the last instruction terminates. If not, load null/None and return
        has_return = False
        if func_body:
            last = func_body[-1]
            if last[0] == "RETURN":
                has_return = True
        
        if not has_return:
            func_body.append(["LOAD_CONST", None])
            func_body.append(["RETURN"])
            
        self.functions[node.name] = {
            "params": [p[0] for p in node.params],
            "body": func_body
        }

    def compile_node(self, node: ASTNode, body: List[list]):
        if isinstance(node, LiteralNode):
            body.append(["LOAD_CONST", node.value])
            
        elif isinstance(node, IdentifierNode):
            body.append(["LOAD_VAR", node.name])
            
        elif isinstance(node, LetNode):
            self.compile_node(node.value, body)
            body.append(["STORE_VAR", node.name])
            
        elif isinstance(node, AssignNode):
            self.compile_node(node.value, body)
            body.append(["STORE_VAR", node.name])
            
        elif isinstance(node, PrintNode):
            self.compile_node(node.value, body)
            body.append(["PRINT"])
            
        elif isinstance(node, BlockNode):
            for stmt in node.statements:
                self.compile_node(stmt, body)
                
        elif isinstance(node, CallNode):
            for arg in node.args:
                self.compile_node(arg, body)
            if isinstance(node.func, IdentifierNode):
                body.append(["CALL", node.func.name, len(node.args)])
            else:
                raise RuntimeError("VM codegen requires function call target to be an Identifier")
                
        elif isinstance(node, IfNode):
            self.compile_node(node.condition, body)
            lbl_else = self.next_label("if_else")
            lbl_end = self.next_label("if_end")
            
            if node.else_branch:
                body.append(["JUMP_IF_FALSE", lbl_else])
                self.compile_node(node.then_branch, body)
                body.append(["JUMP", lbl_end])
                body.append(["LABEL", lbl_else])
                self.compile_node(node.else_branch, body)
                body.append(["LABEL", lbl_end])
            else:
                body.append(["JUMP_IF_FALSE", lbl_end])
                self.compile_node(node.then_branch, body)
                body.append(["LABEL", lbl_end])
                
        elif isinstance(node, MatchNode):
            self.compile_node(node.value, body)
            lbl_end = self.next_label("match_end")
            
            for pattern, case_body in node.cases:
                lbl_next = self.next_label("match_next")
                
                if isinstance(pattern, IdentifierNode) and pattern.name == "_":
                    body.append(["POP"])  # Pop the matched value
                    self.compile_node(case_body, body)
                    body.append(["JUMP", lbl_end])
                    break
                else:
                    body.append(["DUP"])
                    self.compile_node(pattern, body)
                    body.append(["EQ"])
                    body.append(["JUMP_IF_FALSE", lbl_next])
                    body.append(["POP"])  # Pop matched value duplicate
                    self.compile_node(case_body, body)
                    body.append(["JUMP", lbl_end])
                    body.append(["LABEL", lbl_next])
            else:
                body.append(["POP"])  # Pop original matched value if no case matched
                
            body.append(["LABEL", lbl_end])
            
        elif isinstance(node, ReturnNode):
            if node.value:
                self.compile_node(node.value, body)
            else:
                body.append(["LOAD_CONST", None])
            body.append(["RETURN"])
            
        elif isinstance(node, BinaryOpNode):
            if node.op == "&&":
                lbl_eval_false = self.next_label("and_eval_false")
                lbl_end = self.next_label("and_end")
                self.compile_node(node.left, body)
                body.append(["JUMP_IF_FALSE", lbl_eval_false])
                self.compile_node(node.right, body)
                body.append(["JUMP", lbl_end])
                body.append(["LABEL", lbl_eval_false])
                body.append(["LOAD_CONST", False])
                body.append(["LABEL", lbl_end])
            elif node.op == "||":
                lbl_eval_right = self.next_label("or_eval_right")
                lbl_end = self.next_label("or_end")
                self.compile_node(node.left, body)
                body.append(["JUMP_IF_FALSE", lbl_eval_right])
                body.append(["LOAD_CONST", True])
                body.append(["JUMP", lbl_end])
                body.append(["LABEL", lbl_eval_right])
                self.compile_node(node.right, body)
                body.append(["LABEL", lbl_end])
            else:
                self.compile_node(node.left, body)
                self.compile_node(node.right, body)
                op_map = {
                    "+": "ADD", "-": "SUB", "*": "MUL", "/": "DIV", "%": "MOD",
                    "==": "EQ", "!=": "NE", "<": "LT", ">": "GT", "<=": "LE", ">=": "GE"
                }
                if node.op in op_map:
                    body.append([op_map[node.op]])
                else:
                    raise RuntimeError(f"VM codegen doesn't support binary operator '{node.op}'")
                    
        elif isinstance(node, UnaryOpNode):
            self.compile_node(node.right, body)
            if node.op == "-":
                body.append(["NEG"])
            elif node.op == "!":
                body.append(["NOT"])
            elif node.op == "+":
                pass  # Unary + is a no-op
            else:
                raise RuntimeError(f"VM codegen doesn't support unary operator '{node.op}'")
                
        else:
            raise RuntimeError(f"VM codegen doesn't support AST node type: {type(node).__name__}")

    def resolve_labels(self, instrs: List[list]) -> List[list]:
        label_map = {}
        idx = 0
        for instr in instrs:
            if instr[0] == "LABEL":
                label_map[instr[1]] = idx
            else:
                idx += 1
                
        resolved = []
        for instr in instrs:
            if instr[0] == "LABEL":
                continue
            elif instr[0] in ("JUMP", "JUMP_IF_FALSE"):
                target = instr[1]
                if target in label_map:
                    resolved.append([instr[0], label_map[target]])
                else:
                    raise RuntimeError(f"Jump to undefined label target: '{target}'")
            else:
                resolved.append(instr)
                
        return resolved
