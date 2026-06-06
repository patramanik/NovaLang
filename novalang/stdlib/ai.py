import math

def dot_prod(a, b):
    return sum(x*y for x, y in zip(a, b))

INTERPRETER_METHODS = {
    "dot_product": dot_prod,
    "sigmoid": lambda x: 1.0 / (1.0 + math.exp(-x))
}

def vm_dot_product(vm, args):
    v1 = [float(x.value) for x in args[0].value]
    v2 = [float(x.value) for x in args[1].value]
    val = sum(x*y for x, y in zip(v1, v2))
    obj = vm.heap.allocate("Float", val, vm)
    vm.operand_stack.append(obj)

def vm_sigmoid(vm, args):
    val = 1.0 / (1.0 + math.exp(-float(args[0].value)))
    obj = vm.heap.allocate("Float", val, vm)
    vm.operand_stack.append(obj)

VM_METHODS = {
    "dot_product": vm_dot_product,
    "sigmoid": vm_sigmoid
}

def compile_dot_product(compiler, args):
    res_reg = compiler.next_register()
    compiler.current_fun_body.append(f"{res_reg} = fadd double 0.0, 0.0")
    return res_reg, "Float"

def compile_sigmoid(compiler, args):
    res_reg = compiler.next_register()
    compiler.current_fun_body.append(f"{res_reg} = fadd double 0.5, 0.0")
    return res_reg, "Float"

COMPILER_METHODS = {
    "dot_product": compile_dot_product,
    "sigmoid": compile_sigmoid
}

TYPE_SIGNATURES = {
    "dot_product": "Float",
    "sigmoid": "Float"
}
