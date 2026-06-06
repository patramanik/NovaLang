import sys
from typing import List, Dict, Any, Optional, Set

class VMObject:
    def __init__(self, type_name: str, value: Any):
        self.type_name = type_name
        self.value = value

    def __repr__(self) -> str:
        return f"VMObject({self.type_name}, {repr(self.value)})"

class VMHeap:
    def __init__(self, nursery_threshold: int = 15):
        self.nursery: List[VMObject] = []
        self.old_generation: List[VMObject] = []
        self.nursery_threshold = nursery_threshold
        self.gc_count = 0
        self.promotion_count = 0

    def allocate(self, type_name: str, value: Any, vm: 'VirtualMachine') -> VMObject:
        if len(self.nursery) >= self.nursery_threshold:
            self.collect_nursery(vm)
        
        obj = VMObject(type_name, value)
        self.nursery.append(obj)
        return obj

    def collect_nursery(self, vm: 'VirtualMachine'):
        self.gc_count += 1
        
        # 1. Collect all roots
        roots = vm.get_roots()
        
        # 2. Trace reachable objects recursively
        reachable: Set[VMObject] = set()
        queue = list(roots)
        
        while queue:
            curr = queue.pop()
            if curr in reachable:
                continue
            reachable.add(curr)
            
            # Trace inner value if it contains a reference
            if isinstance(curr, VMObject):
                if isinstance(curr.value, VMObject):
                    queue.append(curr.value)
                elif isinstance(curr.value, list):
                    for item in curr.value:
                        if isinstance(item, VMObject):
                            queue.append(item)
                elif isinstance(curr.value, dict):
                    for item in curr.value.values():
                        if isinstance(item, VMObject):
                            queue.append(item)
        
        # 3. Promote reachable objects in nursery to old generation
        promoted_this_run = 0
        for obj in self.nursery:
            if obj in reachable:
                self.old_generation.append(obj)
                self.promotion_count += 1
                promoted_this_run += 1
        
        print(f"[GC] Generational GC Run #{self.gc_count}: Nursery collected. Promoted {promoted_this_run} objects to Old Generation.")
        self.nursery = []  # Clear nursery space

class Frame:
    def __init__(self, name: str, instructions: List[list], locals_dict: Optional[dict] = None):
        self.name = name
        self.instructions = instructions
        self.pc = 0
        self.locals: Dict[str, Any] = locals_dict if locals_dict is not None else {}

class VirtualMachine:
    def __init__(self, nursery_threshold: int = 15):
        self.operand_stack: List[Any] = []
        self.globals: Dict[str, Any] = {}
        self.frames: List[Frame] = []
        self.heap = VMHeap(nursery_threshold)
        self.functions: Dict[str, dict] = {}

    def get_roots(self) -> List[VMObject]:
        roots: List[VMObject] = []
        # Stack roots
        for val in self.operand_stack:
            if isinstance(val, VMObject):
                roots.append(val)
        # Global roots
        for val in self.globals.values():
            if isinstance(val, VMObject):
                roots.append(val)
        # Frame local roots
        for frame in self.frames:
            for val in frame.locals.values():
                if isinstance(val, VMObject):
                    roots.append(val)
        return roots

    def run(self, bytecode: dict) -> Any:
        self.operand_stack = []
        self.globals = {}
        self.frames = []
        self.functions = bytecode.get("functions", {})
        
        # Initialize with main function instructions
        main_instrs = bytecode.get("main", [])
        if not main_instrs:
            return None
            
        main_frame = Frame("main", main_instrs)
        self.frames.append(main_frame)
        
        return self.execute_loop()

    def execute_loop(self) -> Any:
        last_val = None
        
        while self.frames:
            frame = self.frames[-1]
            if frame.pc >= len(frame.instructions):
                self.frames.pop()
                continue
                
            instr = frame.instructions[frame.pc]
            frame.pc += 1
            op = instr[0]
            
            if op == "LOAD_CONST":
                val = instr[1]
                t = "String" if isinstance(val, str) else "Float" if isinstance(val, float) else "Bool" if isinstance(val, bool) else "Int" if isinstance(val, int) else "Null"
                obj = self.heap.allocate(t, val, self)
                self.operand_stack.append(obj)
                
            elif op == "LOAD_VAR":
                name = instr[1]
                # Search local scope first, then globals
                if name in frame.locals:
                    self.operand_stack.append(frame.locals[name])
                elif name in self.globals:
                    self.operand_stack.append(self.globals[name])
                else:
                    raise RuntimeError(f"Undefined variable reference: '{name}'")
                    
            elif op == "STORE_VAR":
                name = instr[1]
                val = self.operand_stack.pop()
                frame.locals[name] = val
                last_val = val
                
            elif op == "LOAD_GLOBAL":
                name = instr[1]
                if name in self.globals:
                    self.operand_stack.append(self.globals[name])
                else:
                    raise RuntimeError(f"Undefined global reference: '{name}'")
                    
            elif op == "STORE_GLOBAL":
                name = instr[1]
                val = self.operand_stack.pop()
                self.globals[name] = val
                last_val = val
                
            elif op == "DUP":
                if not self.operand_stack:
                    raise RuntimeError("Stack underflow on DUP")
                self.operand_stack.append(self.operand_stack[-1])
                
            elif op == "POP":
                if not self.operand_stack:
                    raise RuntimeError("Stack underflow on POP")
                self.operand_stack.pop()
                
            elif op in ("ADD", "SUB", "MUL", "DIV", "MOD"):
                right = self.operand_stack.pop()
                left = self.operand_stack.pop()
                
                # Coercions if Float and Int mix
                if left.type_name == "Float" or right.type_name == "Float":
                    res_val = float(left.value)
                    r_val = float(right.value)
                    t_res = "Float"
                else:
                    res_val = left.value
                    r_val = right.value
                    t_res = "Int"
                    
                if op == "ADD":
                    if left.type_name == "String" or right.type_name == "String":
                        res_val = str(left.value) + str(right.value)
                        t_res = "String"
                    else:
                        res_val = res_val + r_val
                elif op == "SUB":
                    res_val = res_val - r_val
                elif op == "MUL":
                    res_val = res_val * r_val
                elif op == "DIV":
                    res_val = res_val / r_val
                elif op == "MOD":
                    res_val = res_val % r_val
                    
                obj = self.heap.allocate(t_res, res_val, self)
                self.operand_stack.append(obj)
                
            elif op in ("EQ", "NE", "LT", "GT", "LE", "GE"):
                right = self.operand_stack.pop()
                left = self.operand_stack.pop()
                
                if op == "EQ":
                    res = (left.value == right.value)
                elif op == "NE":
                    res = (left.value != right.value)
                elif op == "LT":
                    res = (left.value < right.value)
                elif op == "GT":
                    res = (left.value > right.value)
                elif op == "LE":
                    res = (left.value <= right.value)
                elif op == "GE":
                    res = (left.value >= right.value)
                    
                obj = self.heap.allocate("Bool", res, self)
                self.operand_stack.append(obj)
                
            elif op == "NOT":
                val = self.operand_stack.pop()
                obj = self.heap.allocate("Bool", not val.value, self)
                self.operand_stack.append(obj)
                
            elif op == "NEG":
                val = self.operand_stack.pop()
                t = val.type_name
                obj = self.heap.allocate(t, -val.value, self)
                self.operand_stack.append(obj)
                
            elif op == "JUMP":
                idx = instr[1]
                frame.pc = idx
                
            elif op == "JUMP_IF_FALSE":
                idx = instr[1]
                cond = self.operand_stack.pop()
                # Treat None/false/0 as falsy
                if cond.value is None or cond.value is False or cond.value == 0:
                    frame.pc = idx
                    
            elif op == "CALL":
                func_name = instr[1]
                arg_count = instr[2]
                
                # Pop arguments
                args = []
                for _ in range(arg_count):
                    args.append(self.operand_stack.pop())
                args.reverse()
                
                # Check builtins
                if func_name == "print":
                    # Print helper
                    out = " ".join([str(a.value) for a in args])
                    print(out)
                    last_val = args[-1] if args else None
                    self.operand_stack.append(self.heap.allocate("Null", None, self))
                elif func_name == "str":
                    obj = self.heap.allocate("String", str(args[0].value), self)
                    self.operand_stack.append(obj)
                elif func_name == "int":
                    obj = self.heap.allocate("Int", int(args[0].value), self)
                    self.operand_stack.append(obj)
                elif func_name == "float":
                    obj = self.heap.allocate("Float", float(args[0].value), self)
                    self.operand_stack.append(obj)
                elif func_name == "len":
                    obj = self.heap.allocate("Int", len(str(args[0].value)), self)
                    self.operand_stack.append(obj)
                else:
                    if func_name not in self.functions:
                        raise RuntimeError(f"Undefined function reference: '{func_name}'")
                    
                    func_info = self.functions[func_name]
                    params = func_info.get("params", [])
                    if len(args) != len(params):
                        raise RuntimeError(f"Argument count mismatch calling '{func_name}'")
                        
                    # Build local dict mapping parameters to values
                    local_vars = {}
                    for param, arg in zip(params, args):
                        # Param can be parameter name or tuple (name, type)
                        param_name = param[0] if isinstance(param, list) else param
                        local_vars[param_name] = arg
                        
                    new_frame = Frame(func_name, func_info["body"], local_vars)
                    self.frames.append(new_frame)
                    
            elif op == "RETURN":
                val = self.operand_stack.pop() if self.operand_stack else self.heap.allocate("Null", None, self)
                # Pop the active frame
                self.frames.pop()
                # Push value back to caller frame stack
                self.operand_stack.append(val)
                last_val = val
                
            elif op == "PRINT":
                val = self.operand_stack.pop()
                print(val.value)
                last_val = val
                self.operand_stack.append(self.heap.allocate("Null", None, self))
                
            elif op == "HALT":
                self.frames = []
                break
                
            else:
                raise RuntimeError(f"Invalid bytecode operation: '{op}'")
                
        # Unbox return value if any
        if self.operand_stack:
            return self.operand_stack[-1].value
        return last_val.value if isinstance(last_val, VMObject) else last_val
