from typing import List, Dict, Optional, Tuple
from novalang.ast import (
    ASTNode, Program, LetNode, AssignNode, BinaryOpNode, LiteralNode,
    IdentifierNode, PrintNode, BlockNode, FunctionDeclNode, CallNode, IfNode, MatchNode, ReturnNode,
    UnaryOpNode, ImportNode, PackageNode, MemberAccessNode, AsmNode,
    TryCatchFinallyNode, ThrowNode
)

class LLVMCompiler:
    def __init__(self):
        self.globals_declarations: List[str] = [
            "declare i32 @printf(ptr, ...)",
            "declare void @exit(i32)",
            "@str_format_int = private unnamed_addr constant [4 x i8] c\"%d\\0A\\00\", align 1",
            "@str_format_float = private unnamed_addr constant [6 x i8] c\"%.6f\\0A\\00\", align 1",
            "@str_format_string = private unnamed_addr constant [4 x i8] c\"%s\\0A\\00\", align 1",
            "@str_format_bool_true = private unnamed_addr constant [6 x i8] c\"true\\0A\\00\", align 1",
            "@str_format_bool_false = private unnamed_addr constant [7 x i8] c\"false\\0A\\00\", align 1"
        ]
        self.current_fun_allocas: List[str] = []
        self.current_fun_body: List[str] = []
        self.register_count = 0
        self.label_count = 0
        self.var_types: Dict[str, str] = {}
        self.var_slots: Dict[str, str] = {}
        self.global_strings: Dict[str, str] = {}
        self.functions: Dict[str, Tuple[List[str], str]] = {}
        self.global_vars: Dict[str, str] = {}
        self.global_var_types: Dict[str, str] = {}
        self.is_in_main = False

    def next_register(self) -> str:
        self.register_count += 1
        return f"%reg_{self.register_count}"

    def next_label(self, prefix: str) -> str:
        self.label_count += 1
        return f"{prefix}_{self.label_count}"

    def get_llvm_type(self, t: str) -> str:
        mapping = {
            "Int": "i32",
            "Float": "double",
            "Bool": "i1",
            "String": "ptr"
        }
        return mapping.get(t, "i32")

    def get_global_string(self, text: str) -> str:
        if text in self.global_strings:
            return self.global_strings[text]
        
        lbl = f"@.str.{len(self.global_strings)}"
        self.global_strings[text] = lbl
        
        escaped_chars = []
        for char in text:
            o = ord(char)
            if char.isalnum() or char in ' _-+*/=<>!@#$^&*()[]{}|;:,./?~`':
                escaped_chars.append(char)
            else:
                escaped_chars.append(f"\\{o:02X}")
        escaped_str = "".join(escaped_chars) + "\\00"
        
        raw_bytes = text.encode("utf-8")
        size = len(raw_bytes) + 1
        self.globals_declarations.append(f"{lbl} = private unnamed_addr constant [{size} x i8] c\"{escaped_str}\", align 1")
        return lbl

    def last_instruction_is_terminator(self) -> bool:
        if not self.current_fun_body:
            return False
        last = self.current_fun_body[-1].strip()
        return last.startswith("br ") or last.startswith("ret ")

    def compile(self, program: Program) -> str:
        # Split function declarations from top-level statements
        functions_nodes = []
        toplevel_nodes = []
        for stmt in program.statements:
            if isinstance(stmt, FunctionDeclNode):
                functions_nodes.append(stmt)
            else:
                toplevel_nodes.append(stmt)
                
        # Register user function signatures first (for recursive call lookup)
        for fn in functions_nodes:
            param_types = [p[1] if p[1] else "Int" for p in fn.params]
            ret_type = fn.return_type if fn.return_type else "Int"
            self.functions[fn.name] = (param_types, ret_type)

        # Pre-scan globals to register top-level variables before functions compile
        self.pre_scan_globals(toplevel_nodes)

        # Compile user functions
        fun_ir = ""
        for fn in functions_nodes:
            fun_ir += self.compile_function(fn) + "\n"
            
        # Compile main function
        main_ir = self.compile_main(toplevel_nodes)
        
        globals_ir = "\n".join(self.globals_declarations)
        return f"; ModuleID = 'novalang'\nsource_filename = \"main.nova\"\n\n{globals_ir}\n\n{fun_ir}\n{main_ir}"

    def compile_main(self, statements: List[ASTNode]) -> str:
        self.is_in_main = True
        self.current_fun_allocas = []
        self.current_fun_body = []
        self.var_types = {}
        self.var_slots = {}
        
        self.current_fun_body.append("entry:")
        
        for stmt in statements:
            self.compile_statement(stmt)
            
        self.current_fun_body.append("ret i32 0")
        
        allocas_str = "\n".join([f"    {a}" for a in self.current_fun_allocas])
        body_lines = []
        for line in self.current_fun_body:
            line_strip = line.strip()
            if line_strip.endswith(":"):
                body_lines.append(line_strip)
            else:
                body_lines.append(f"    {line_strip}")
                
        full_body = "\n".join(["entry:"] + [f"    {a}" for a in self.current_fun_allocas] + body_lines[1:])
        return f"define i32 @main() {{\n{full_body}\n}}"

    def compile_function(self, node: FunctionDeclNode) -> str:
        old_allocas = self.current_fun_allocas
        old_body = self.current_fun_body
        old_var_slots = self.var_slots
        old_var_types = self.var_types
        old_is_in_main = self.is_in_main
        
        self.is_in_main = False
        self.current_fun_allocas = []
        self.current_fun_body = []
        self.var_slots = {}
        self.var_types = {}
        
        param_types, ret_type = self.functions[node.name]
        
        args_decl = []
        for (param_name, _), p_type in zip(node.params, param_types):
            llvm_type = self.get_llvm_type(p_type)
            args_decl.append(f"{llvm_type} %{param_name}_param")
            
        llvm_ret = self.get_llvm_type(ret_type)
        
        self.current_fun_body.append("entry:")
        
        for (param_name, _), p_type in zip(node.params, param_types):
            slot = f"%{param_name}_slot"
            self.var_slots[param_name] = slot
            self.var_types[param_name] = p_type
            
            llvm_type = self.get_llvm_type(p_type)
            self.current_fun_allocas.append(f"{slot} = alloca {llvm_type}, align 4")
            self.current_fun_body.append(f"store {llvm_type} %{param_name}_param, ptr {slot}, align 4")
            
        for stmt in node.body.statements:
            self.compile_statement(stmt)
            
        if not self.last_instruction_is_terminator():
            if ret_type == "Int" or ret_type == "Bool":
                self.current_fun_body.append("ret i32 0")
            elif ret_type == "Float":
                self.current_fun_body.append("ret double 0.0")
            elif ret_type == "String":
                self.current_fun_body.append("ret ptr null")
            else:
                self.current_fun_body.append("ret void")
                
        alloc_lines = [f"    {a.strip()}" for a in self.current_fun_allocas]
        body_lines = []
        for line in self.current_fun_body:
            line_strip = line.strip()
            if line_strip.endswith(":"):
                body_lines.append(line_strip)
            else:
                body_lines.append(f"    {line_strip}")
                
        full_body = "\n".join(["entry:"] + alloc_lines + body_lines[1:])
        
        args_str = ", ".join(args_decl)
        fun_ir = f"define {llvm_ret} @{node.name}({args_str}) {{\n{full_body}\n}}"
        
        self.current_fun_allocas = old_allocas
        self.current_fun_body = old_body
        self.var_slots = old_var_slots
        self.var_types = old_var_types
        self.is_in_main = old_is_in_main
        
        return fun_ir

    def compile_statement(self, node: ASTNode):
        if isinstance(node, PrintNode):
            self.compile_print(node)
        elif isinstance(node, LetNode):
            # Immutable let
            val_reg, val_type = self.compile_expression(node.value)
            if self.is_in_main:
                slot = self.global_vars[node.name]
                llvm_type = self.get_llvm_type(self.global_var_types[node.name])
                self.current_fun_body.append(f"store {llvm_type} {val_reg}, ptr {slot}, align 4")
            else:
                slot = f"%{node.name}_slot"
                self.var_slots[node.name] = slot
                self.var_types[node.name] = val_type
                llvm_type = self.get_llvm_type(val_type)
                self.current_fun_allocas.append(f"{slot} = alloca {llvm_type}, align 4")
                self.current_fun_body.append(f"store {llvm_type} {val_reg}, ptr {slot}, align 4")
        elif isinstance(node, AssignNode):
            self.compile_assignment(node)
        elif isinstance(node, BlockNode):
            self.compile_block(node)
        elif isinstance(node, IfNode):
            self.compile_if(node)
        elif isinstance(node, MatchNode):
            self.compile_match(node)
        elif isinstance(node, ReturnNode):
            self.compile_return(node)
        elif isinstance(node, AsmNode):
            for instr in node.instructions:
                # Escape double-quotes for LLVM assembly strings (\22 represents " in LLVM)
                escaped_instr = instr.replace('"', '\\22')
                self.current_fun_body.append(f"call void asm sideeffect \"{escaped_instr}\", \"\"()")
        elif isinstance(node, ThrowNode):
            val_reg, val_type = self.compile_expression(node.value)
            if val_type == "Int":
                self.current_fun_body.append(f"call i32 (ptr, ...) @printf(ptr @str_format_int, i32 {val_reg})")
            elif val_type == "Float":
                self.current_fun_body.append(f"call i32 (ptr, ...) @printf(ptr @str_format_float, double {val_reg})")
            elif val_type == "String":
                self.current_fun_body.append(f"call i32 (ptr, ...) @printf(ptr @str_format_string, ptr {val_reg})")
            else:
                self.current_fun_body.append(f"call i32 (ptr, ...) @printf(ptr @str_format_int, i32 0)")
            self.current_fun_body.append("call void @exit(i32 1)")
        elif isinstance(node, TryCatchFinallyNode):
            self.compile_block(node.try_block)
            if node.finally_block:
                self.compile_block(node.finally_block)
        elif isinstance(node, ImportNode) or isinstance(node, PackageNode):
            return
        else:
            # Standalone expression
            self.compile_expression(node)

    def compile_block(self, node: BlockNode):
        for stmt in node.statements:
            self.compile_statement(stmt)

    def compile_print(self, node: PrintNode):
        val_reg, val_type = self.compile_expression(node.value)
        if val_type == "Int":
            self.current_fun_body.append(f"call i32 (ptr, ...) @printf(ptr @str_format_int, i32 {val_reg})")
        elif val_type == "Float":
            self.current_fun_body.append(f"call i32 (ptr, ...) @printf(ptr @str_format_float, double {val_reg})")
        elif val_type == "String":
            self.current_fun_body.append(f"call i32 (ptr, ...) @printf(ptr @str_format_string, ptr {val_reg})")
        elif val_type == "Bool":
            label_true = self.next_label("print_bool_true")
            label_false = self.next_label("print_bool_false")
            label_end = self.next_label("print_bool_end")
            self.current_fun_body.append(f"br i1 {val_reg}, label %{label_true}, label %{label_false}")
            
            self.current_fun_body.append(f"{label_true}:")
            self.current_fun_body.append(f"call i32 (ptr, ...) @printf(ptr @str_format_bool_true)")
            self.current_fun_body.append(f"br label %{label_end}")
            
            self.current_fun_body.append(f"{label_false}:")
            self.current_fun_body.append(f"call i32 (ptr, ...) @printf(ptr @str_format_bool_false)")
            self.current_fun_body.append(f"br label %{label_end}")
            
            self.current_fun_body.append(f"{label_end}:")

    def compile_assignment(self, node: AssignNode):
        val_reg, val_type = self.compile_expression(node.value)
        var_type = node.type_ann if node.type_ann else val_type
        
        if node.name in self.var_slots:
            slot = self.var_slots[node.name]
            expected_type = self.var_types[node.name]
        elif node.name in self.global_vars:
            slot = self.global_vars[node.name]
            expected_type = self.global_var_types[node.name]
        else:
            if self.is_in_main:
                slot = f"@{node.name}"
                self.global_vars[node.name] = slot
                self.global_var_types[node.name] = var_type
                llvm_type = self.get_llvm_type(var_type)
                default_val = "0.0" if var_type == "Float" else "null" if var_type == "String" else "0"
                self.globals_declarations.append(f"{slot} = global {llvm_type} {default_val}, align 4")
                expected_type = var_type
            else:
                slot = f"%{node.name}_slot"
                self.var_slots[node.name] = slot
                self.var_types[node.name] = var_type
                llvm_type = self.get_llvm_type(var_type)
                self.current_fun_allocas.append(f"{slot} = alloca {llvm_type}, align 4")
                expected_type = var_type
                
        if expected_type != val_type:
            if expected_type == "Float" and val_type == "Int":
                conv_reg = self.next_register()
                self.current_fun_body.append(f"{conv_reg} = sitofp i32 {val_reg} to double")
                val_reg = conv_reg
                val_type = "Float"
            else:
                raise TypeError(f"Type error for '{node.name}': Expected {expected_type}, but got {val_type}")
                
        llvm_type = self.get_llvm_type(expected_type)
        self.current_fun_body.append(f"store {llvm_type} {val_reg}, ptr {slot}, align 4")

    def compile_if(self, node: IfNode):
        cond_reg, cond_type = self.compile_expression(node.condition)
        if cond_type != "Bool":
            if cond_type == "Int":
                conv_reg = self.next_register()
                self.current_fun_body.append(f"{conv_reg} = icmp ne i32 {cond_reg}, 0")
                cond_reg = conv_reg
            else:
                raise TypeError("Condition must be a boolean or integer")
                
        label_then = self.next_label("if_then")
        label_else = self.next_label("if_else") if node.else_branch else None
        label_end = self.next_label("if_end")
        
        if label_else:
            self.current_fun_body.append(f"br i1 {cond_reg}, label %{label_then}, label %{label_else}")
        else:
            self.current_fun_body.append(f"br i1 {cond_reg}, label %{label_then}, label %{label_end}")
            
        self.current_fun_body.append(f"{label_then}:")
        self.compile_block(node.then_branch)
        if not self.last_instruction_is_terminator():
            self.current_fun_body.append(f"br label %{label_end}")
            
        if label_else:
            self.current_fun_body.append(f"{label_else}:")
            if isinstance(node.else_branch, IfNode):
                self.compile_if(node.else_branch)
            else:
                self.compile_block(node.else_branch)
            if not self.last_instruction_is_terminator():
                self.current_fun_body.append(f"br label %{label_end}")
                
        self.current_fun_body.append(f"{label_end}:")

    def compile_match(self, node: MatchNode):
        val_reg, val_type = self.compile_expression(node.value)
        llvm_type = self.get_llvm_type(val_type)
        
        label_end = self.next_label("match_end")
        
        for i, (pattern, body) in enumerate(node.cases):
            is_wildcard = isinstance(pattern, IdentifierNode) and pattern.name == "_"
            
            if is_wildcard:
                self.compile_block(body)
                if not self.last_instruction_is_terminator():
                    self.current_fun_body.append(f"br label %{label_end}")
                break
            else:
                pat_reg, pat_type = self.compile_expression(pattern)
                if pat_type != val_type:
                    raise TypeError(f"Pattern match type mismatch: cannot match {val_type} with {pat_type}")
                    
                cond_reg = self.next_register()
                if val_type == "Int" or val_type == "Bool":
                    self.current_fun_body.append(f"{cond_reg} = icmp eq {llvm_type} {val_reg}, {pat_reg}")
                elif val_type == "Float":
                    self.current_fun_body.append(f"{cond_reg} = fcmp oeq double {val_reg}, {pat_reg}")
                elif val_type == "String":
                    self.current_fun_body.append(f"{cond_reg} = icmp eq ptr {val_reg}, {pat_reg}")
                    
                label_case = self.next_label(f"match_case_{i}")
                label_next = self.next_label(f"match_next_{i}")
                
                self.current_fun_body.append(f"br i1 {cond_reg}, label %{label_case}, label %{label_next}")
                
                self.current_fun_body.append(f"{label_case}:")
                self.compile_block(body)
                if not self.last_instruction_is_terminator():
                    self.current_fun_body.append(f"br label %{label_end}")
                    
                self.current_fun_body.append(f"{label_next}:")
                
        if not self.last_instruction_is_terminator():
            self.current_fun_body.append(f"br label %{label_end}")
            
        self.current_fun_body.append(f"{label_end}:")

    def compile_return(self, node: ReturnNode):
        if node.value:
            val_reg, val_type = self.compile_expression(node.value)
            llvm_type = self.get_llvm_type(val_type)
            self.current_fun_body.append(f"ret {llvm_type} {val_reg}")
        else:
            self.current_fun_body.append("ret void")

    def compile_expression(self, node: ASTNode) -> Tuple[str, str]:
        if isinstance(node, LiteralNode):
            return self.compile_literal(node)
        elif isinstance(node, IdentifierNode):
            return self.compile_identifier(node)
        elif isinstance(node, BinaryOpNode):
            return self.compile_binary_op(node)
        elif isinstance(node, UnaryOpNode):
            return self.compile_unary_op(node)
        elif isinstance(node, CallNode):
            return self.compile_call(node)
        elif isinstance(node, MemberAccessNode):
            name = self.get_member_access_path(node)
            return self.compile_identifier(IdentifierNode(name))
        else:
            raise RuntimeError(f"Expression type '{type(node).__name__}' not supported in compiler")

    def compile_literal(self, node: LiteralNode) -> Tuple[str, str]:
        val = node.value
        if isinstance(val, bool):
            return "1" if val else "0", "Bool"
        elif isinstance(val, int):
            return str(val), "Int"
        elif isinstance(val, float):
            return str(val), "Float"
        elif isinstance(val, str):
            lbl = self.get_global_string(val)
            raw_bytes = val.encode("utf-8")
            size = len(raw_bytes) + 1
            ptr_reg = self.next_register()
            self.current_fun_body.append(f"{ptr_reg} = getelementptr inbounds [{size} x i8], ptr {lbl}, i64 0, i64 0")
            return ptr_reg, "String"
        elif val is None:
            return "null", "String"
            
        raise RuntimeError(f"Unknown literal type: {type(val)}")

    def compile_identifier(self, node: IdentifierNode) -> Tuple[str, str]:
        if node.name in self.var_slots:
            slot = self.var_slots[node.name]
            var_type = self.var_types[node.name]
            llvm_type = self.get_llvm_type(var_type)
            reg = self.next_register()
            self.current_fun_body.append(f"{reg} = load {llvm_type}, ptr {slot}, align 4")
            return reg, var_type
        elif node.name in self.global_vars:
            slot = self.global_vars[node.name]
            var_type = self.global_var_types[node.name]
            llvm_type = self.get_llvm_type(var_type)
            reg = self.next_register()
            self.current_fun_body.append(f"{reg} = load {llvm_type}, ptr {slot}, align 4")
            return reg, var_type
            
        raise RuntimeError(f"Identifier '{node.name}' is undefined in this scope")

    def compile_binary_op(self, node: BinaryOpNode) -> Tuple[str, str]:
        if node.op == "&&":
            res_slot = self.next_register() + "_and"
            self.current_fun_allocas.append(f"{res_slot} = alloca i1, align 4")
            
            label_eval_right = self.next_label("and_eval_right")
            label_end = self.next_label("and_end")
            
            left_reg, left_type = self.compile_expression(node.left)
            if left_type != "Bool":
                raise TypeError("Logical operands must be Bool")
                
            self.current_fun_body.append(f"store i1 {left_reg}, ptr {res_slot}, align 4")
            self.current_fun_body.append(f"br i1 {left_reg}, label %{label_eval_right}, label %{label_end}")
            
            self.current_fun_body.append(f"{label_eval_right}:")
            right_reg, right_type = self.compile_expression(node.right)
            if right_type != "Bool":
                raise TypeError("Logical operands must be Bool")
            self.current_fun_body.append(f"store i1 {right_reg}, ptr {res_slot}, align 4")
            self.current_fun_body.append(f"br label %{label_end}")
            
            self.current_fun_body.append(f"{label_end}:")
            load_reg = self.next_register()
            self.current_fun_body.append(f"{load_reg} = load i1, ptr {res_slot}, align 4")
            return load_reg, "Bool"
            
        if node.op == "||":
            res_slot = self.next_register() + "_or"
            self.current_fun_allocas.append(f"{res_slot} = alloca i1, align 4")
            
            label_eval_right = self.next_label("or_eval_right")
            label_end = self.next_label("or_end")
            
            left_reg, left_type = self.compile_expression(node.left)
            if left_type != "Bool":
                raise TypeError("Logical operands must be Bool")
                
            self.current_fun_body.append(f"store i1 {left_reg}, ptr {res_slot}, align 4")
            self.current_fun_body.append(f"br i1 {left_reg}, label %{label_end}, label %{label_eval_right}")
            
            self.current_fun_body.append(f"{label_eval_right}:")
            right_reg, right_type = self.compile_expression(node.right)
            if right_type != "Bool":
                raise TypeError("Logical operands must be Bool")
            self.current_fun_body.append(f"store i1 {right_reg}, ptr {res_slot}, align 4")
            self.current_fun_body.append(f"br label %{label_end}")
            
            self.current_fun_body.append(f"{label_end}:")
            load_reg = self.next_register()
            self.current_fun_body.append(f"{load_reg} = load i1, ptr {res_slot}, align 4")
            return load_reg, "Bool"

        left_reg, left_type = self.compile_expression(node.left)
        right_reg, right_type = self.compile_expression(node.right)
        
        if left_type == "Int" and right_type == "Float":
            conv = self.next_register()
            self.current_fun_body.append(f"{conv} = sitofp i32 {left_reg} to double")
            left_reg = conv
            left_type = "Float"
        elif left_type == "Float" and right_type == "Int":
            conv = self.next_register()
            self.current_fun_body.append(f"{conv} = sitofp i32 {right_reg} to double")
            right_reg = conv
            right_type = "Float"
            
        res_reg = self.next_register()
        
        if left_type == "Int":
            if node.op == "+":
                self.current_fun_body.append(f"{res_reg} = add i32 {left_reg}, {right_reg}")
                return res_reg, "Int"
            elif node.op == "-":
                self.current_fun_body.append(f"{res_reg} = sub i32 {left_reg}, {right_reg}")
                return res_reg, "Int"
            elif node.op == "*":
                self.current_fun_body.append(f"{res_reg} = mul i32 {left_reg}, {right_reg}")
                return res_reg, "Int"
            elif node.op == "/":
                self.current_fun_body.append(f"{res_reg} = sdiv i32 {left_reg}, {right_reg}")
                return res_reg, "Int"
            elif node.op == "%":
                self.current_fun_body.append(f"{res_reg} = srem i32 {left_reg}, {right_reg}")
                return res_reg, "Int"
            elif node.op == "==":
                self.current_fun_body.append(f"{res_reg} = icmp eq i32 {left_reg}, {right_reg}")
                return res_reg, "Bool"
            elif node.op == "!=":
                self.current_fun_body.append(f"{res_reg} = icmp ne i32 {left_reg}, {right_reg}")
                return res_reg, "Bool"
            elif node.op == "<":
                self.current_fun_body.append(f"{res_reg} = icmp slt i32 {left_reg}, {right_reg}")
                return res_reg, "Bool"
            elif node.op == ">":
                self.current_fun_body.append(f"{res_reg} = icmp sgt i32 {left_reg}, {right_reg}")
                return res_reg, "Bool"
            elif node.op == "<=":
                self.current_fun_body.append(f"{res_reg} = icmp sle i32 {left_reg}, {right_reg}")
                return res_reg, "Bool"
            elif node.op == ">=":
                self.current_fun_body.append(f"{res_reg} = icmp sge i32 {left_reg}, {right_reg}")
                return res_reg, "Bool"
                
        elif left_type == "Float":
            if node.op == "+":
                self.current_fun_body.append(f"{res_reg} = fadd double {left_reg}, {right_reg}")
                return res_reg, "Float"
            elif node.op == "-":
                self.current_fun_body.append(f"{res_reg} = fsub double {left_reg}, {right_reg}")
                return res_reg, "Float"
            elif node.op == "*":
                self.current_fun_body.append(f"{res_reg} = fmul double {left_reg}, {right_reg}")
                return res_reg, "Float"
            elif node.op == "/":
                self.current_fun_body.append(f"{res_reg} = fdiv double {left_reg}, {right_reg}")
                return res_reg, "Float"
            elif node.op == "%":
                self.current_fun_body.append(f"{res_reg} = frem double {left_reg}, {right_reg}")
                return res_reg, "Float"
            elif node.op == "==":
                self.current_fun_body.append(f"{res_reg} = fcmp oeq double {left_reg}, {right_reg}")
                return res_reg, "Bool"
            elif node.op == "!=":
                self.current_fun_body.append(f"{res_reg} = fcmp one double {left_reg}, {right_reg}")
                return res_reg, "Bool"
            elif node.op == "<":
                self.current_fun_body.append(f"{res_reg} = fcmp olt double {left_reg}, {right_reg}")
                return res_reg, "Bool"
            elif node.op == ">":
                self.current_fun_body.append(f"{res_reg} = fcmp ogt double {left_reg}, {right_reg}")
                return res_reg, "Bool"
            elif node.op == "<=":
                self.current_fun_body.append(f"{res_reg} = fcmp ole double {left_reg}, {right_reg}")
                return res_reg, "Bool"
            elif node.op == ">=":
                self.current_fun_body.append(f"{res_reg} = fcmp oge double {left_reg}, {right_reg}")
                return res_reg, "Bool"
                
        elif left_type == "Bool":
            if node.op == "==":
                self.current_fun_body.append(f"{res_reg} = icmp eq i1 {left_reg}, {right_reg}")
                return res_reg, "Bool"
            elif node.op == "!=":
                self.current_fun_body.append(f"{res_reg} = icmp ne i1 {left_reg}, {right_reg}")
                return res_reg, "Bool"
                
        raise RuntimeError(f"Operation '{node.op}' not supported between {left_type} and {right_type}")

    def compile_unary_op(self, node: UnaryOpNode) -> Tuple[str, str]:
        right_reg, right_type = self.compile_expression(node.right)
        res_reg = self.next_register()
        
        if node.op == "-":
            if right_type == "Int":
                self.current_fun_body.append(f"{res_reg} = sub i32 0, {right_reg}")
                return res_reg, "Int"
            elif right_type == "Float":
                self.current_fun_body.append(f"{res_reg} = fsub double 0.0, {right_reg}")
                return res_reg, "Float"
        elif node.op == "+":
            return right_reg, right_type
        elif node.op == "!":
            if right_type == "Bool":
                self.current_fun_body.append(f"{res_reg} = xor i1 {right_reg}, 1")
                return res_reg, "Bool"
                
        raise RuntimeError(f"Unary operator '{node.op}' not supported for type {right_type}")

    def compile_call(self, node: CallNode) -> Tuple[str, str]:
        if isinstance(node.func, IdentifierNode):
            func_name = node.func.name
            if func_name in self.functions:
                param_types, ret_type = self.functions[func_name]
                if len(node.args) != len(param_types):
                    raise RuntimeError(f"Argument count mismatch calling '{func_name}'")
                    
                args_compiled = []
                for arg, expected_t in zip(node.args, param_types):
                    arg_reg, arg_type = self.compile_expression(arg)
                    if arg_type != expected_t:
                        if expected_t == "Float" and arg_type == "Int":
                            conv = self.next_register()
                            self.current_fun_body.append(f"{conv} = sitofp i32 {arg_reg} to double")
                            arg_reg = conv
                            arg_type = "Float"
                        else:
                            raise TypeError(f"Argument type mismatch calling '{func_name}': expected {expected_t}, got {arg_type}")
                    llvm_t = self.get_llvm_type(expected_t)
                    args_compiled.append(f"{llvm_t} {arg_reg}")
                    
                res_reg = self.next_register()
                llvm_ret = self.get_llvm_type(ret_type)
                args_str = ", ".join(args_compiled)
                self.current_fun_body.append(f"{res_reg} = call {llvm_ret} @{func_name}({args_str})")
                return res_reg, ret_type
                
        elif isinstance(node.func, MemberAccessNode):
            func_name = self.get_member_access_path(node.func)
            return self.compile_stdlib_call(func_name, node.args)
            
        raise RuntimeError(f"Function call target is not compileable AOT")

    def get_member_access_path(self, node: ASTNode) -> str:
        if isinstance(node, IdentifierNode):
            return node.name
        elif isinstance(node, MemberAccessNode):
            obj_path = self.get_member_access_path(node.object)
            return f"{obj_path}.{node.member}"
        raise RuntimeError("Invalid member access path")

    def compile_stdlib_call(self, func_name: str, args: List[ASTNode]) -> Tuple[str, str]:
        from novalang.stdlib import compile_stdlib_call
        try:
            return compile_stdlib_call(self, func_name, args)
        except Exception as e:
            res_reg = self.next_register()
            self.current_fun_body.append(f"{res_reg} = add i32 0, 0")
            return res_reg, "Int"

    def pre_scan_globals(self, statements: List[ASTNode]):
        for stmt in statements:
            if isinstance(stmt, LetNode):
                var_type = self.infer_type(stmt.value)
                slot = f"@{stmt.name}"
                self.global_vars[stmt.name] = slot
                self.global_var_types[stmt.name] = var_type
                llvm_type = self.get_llvm_type(var_type)
                default_val = "0.0" if var_type == "Float" else "null" if var_type == "String" else "0"
                self.globals_declarations.append(f"{slot} = global {llvm_type} {default_val}, align 4")
            elif isinstance(stmt, AssignNode):
                var_type = stmt.type_ann if stmt.type_ann else self.infer_type(stmt.value)
                slot = f"@{stmt.name}"
                self.global_vars[stmt.name] = slot
                self.global_var_types[stmt.name] = var_type
                llvm_type = self.get_llvm_type(var_type)
                default_val = "0.0" if var_type == "Float" else "null" if var_type == "String" else "0"
                self.globals_declarations.append(f"{slot} = global {llvm_type} {default_val}, align 4")

    def infer_type(self, node: ASTNode) -> str:
        if isinstance(node, LiteralNode):
            val = node.value
            if isinstance(val, bool):
                return "Bool"
            elif isinstance(val, int):
                return "Int"
            elif isinstance(val, float):
                return "Float"
            elif isinstance(val, str):
                return "String"
            return "Int"
        elif isinstance(node, IdentifierNode):
            if node.name in self.var_types:
                return self.var_types[node.name]
            if node.name in self.global_var_types:
                return self.global_var_types[node.name]
            return "Int"
        elif isinstance(node, BinaryOpNode):
            if node.op in ("==", "!=", "<", ">", "<=", ">=", "&&", "||"):
                return "Bool"
            t = self.infer_type(node.left)
            if t == "Float" or self.infer_type(node.right) == "Float":
                return "Float"
            return t
        elif isinstance(node, UnaryOpNode):
            if node.op == "!":
                return "Bool"
            return self.infer_type(node.right)
        elif isinstance(node, CallNode):
            if isinstance(node.func, IdentifierNode):
                func_name = node.func.name
                if func_name in self.functions:
                    return self.functions[func_name][1]
            elif isinstance(node.func, MemberAccessNode):
                func_name = self.get_member_access_path(node.func)
                from novalang.stdlib import infer_stdlib_type
                return infer_stdlib_type(self, func_name, node.args)
            return "Int"
        return "Int"
