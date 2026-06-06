INTERPRETER_METHODS = {
    "upper": lambda s: s.upper(),
    "lower": lambda s: s.lower(),
    "split": lambda s, sep: s.split(sep),
    "join": lambda items, sep: sep.join(items)
}

def vm_upper(vm, args):
    obj = vm.heap.allocate("String", str(args[0].value).upper(), vm)
    vm.operand_stack.append(obj)

def vm_lower(vm, args):
    obj = vm.heap.allocate("String", str(args[0].value).lower(), vm)
    vm.operand_stack.append(obj)

def vm_split(vm, args):
    parts = str(args[0].value).split(str(args[1].value))
    wrapped = [vm.heap.allocate("String", p, vm) for p in parts]
    obj = vm.heap.allocate("List", wrapped, vm)
    vm.operand_stack.append(obj)

def vm_join(vm, args):
    items = [str(x.value) for x in args[0].value]
    sep = str(args[1].value)
    obj = vm.heap.allocate("String", sep.join(items), vm)
    vm.operand_stack.append(obj)

VM_METHODS = {
    "upper": vm_upper,
    "lower": vm_lower,
    "split": vm_split,
    "join": vm_join
}

def compile_upper(compiler, args):
    arg_reg, _ = compiler.compile_expression(args[0])
    return arg_reg, "String"

def compile_lower(compiler, args):
    arg_reg, _ = compiler.compile_expression(args[0])
    return arg_reg, "String"

def compile_split(compiler, args):
    arg_reg, _ = compiler.compile_expression(args[0])
    return arg_reg, "String"

def compile_join(compiler, args):
    arg_reg, _ = compiler.compile_expression(args[1])
    return arg_reg, "String"

COMPILER_METHODS = {
    "upper": compile_upper,
    "lower": compile_lower,
    "split": compile_split,
    "join": compile_join
}

TYPE_SIGNATURES = {
    "upper": "String",
    "lower": "String",
    "split": "String",
    "join": "String"
}
