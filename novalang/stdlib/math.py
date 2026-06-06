import math

INTERPRETER_METHODS = {
    "sqrt": lambda x: float(math.sqrt(x)),
    "sin": lambda x: float(math.sin(x)),
    "cos": lambda x: float(math.cos(x)),
    "abs": lambda x: abs(x),
    "min": lambda a, b: min(a, b),
    "max": lambda a, b: max(a, b)
}

def vm_sqrt(vm, args):
    obj = vm.heap.allocate("Float", float(math.sqrt(args[0].value)), vm)
    vm.operand_stack.append(obj)

def vm_sin(vm, args):
    obj = vm.heap.allocate("Float", float(math.sin(args[0].value)), vm)
    vm.operand_stack.append(obj)

def vm_cos(vm, args):
    obj = vm.heap.allocate("Float", float(math.cos(args[0].value)), vm)
    vm.operand_stack.append(obj)

def vm_abs(vm, args):
    obj = vm.heap.allocate(args[0].type_name, abs(args[0].value), vm)
    vm.operand_stack.append(obj)

def vm_min(vm, args):
    v1, v2 = args[0].value, args[1].value
    t = "Float" if args[0].type_name == "Float" or args[1].type_name == "Float" else "Int"
    obj = vm.heap.allocate(t, min(v1, v2), vm)
    vm.operand_stack.append(obj)

def vm_max(vm, args):
    v1, v2 = args[0].value, args[1].value
    t = "Float" if args[0].type_name == "Float" or args[1].type_name == "Float" else "Int"
    obj = vm.heap.allocate(t, max(v1, v2), vm)
    vm.operand_stack.append(obj)

VM_METHODS = {
    "sqrt": vm_sqrt,
    "sin": vm_sin,
    "cos": vm_cos,
    "abs": vm_abs,
    "min": vm_min,
    "max": vm_max
}

def compile_sqrt(compiler, args):
    dec = "declare double @sqrt(double)"
    if dec not in compiler.globals_declarations:
        compiler.globals_declarations.append(dec)
    arg_reg, arg_type = compiler.compile_expression(args[0])
    if arg_type == "Int":
        conv = compiler.next_register()
        compiler.current_fun_body.append(f"{conv} = sitofp i32 {arg_reg} to double")
        arg_reg = conv
    res = compiler.next_register()
    compiler.current_fun_body.append(f"{res} = call double @sqrt(double {arg_reg})")
    return res, "Float"

def compile_sin(compiler, args):
    dec = "declare double @sin(double)"
    if dec not in compiler.globals_declarations:
        compiler.globals_declarations.append(dec)
    arg_reg, arg_type = compiler.compile_expression(args[0])
    if arg_type == "Int":
        conv = compiler.next_register()
        compiler.current_fun_body.append(f"{conv} = sitofp i32 {arg_reg} to double")
        arg_reg = conv
    res = compiler.next_register()
    compiler.current_fun_body.append(f"{res} = call double @sin(double {arg_reg})")
    return res, "Float"

def compile_cos(compiler, args):
    dec = "declare double @cos(double)"
    if dec not in compiler.globals_declarations:
        compiler.globals_declarations.append(dec)
    arg_reg, arg_type = compiler.compile_expression(args[0])
    if arg_type == "Int":
        conv = compiler.next_register()
        compiler.current_fun_body.append(f"{conv} = sitofp i32 {arg_reg} to double")
        arg_reg = conv
    res = compiler.next_register()
    compiler.current_fun_body.append(f"{res} = call double @cos(double {arg_reg})")
    return res, "Float"

def compile_abs(compiler, args):
    arg_reg, arg_type = compiler.compile_expression(args[0])
    res = compiler.next_register()
    if arg_type == "Float":
        dec = "declare double @fabs(double)"
        if dec not in compiler.globals_declarations:
            compiler.globals_declarations.append(dec)
        compiler.current_fun_body.append(f"{res} = call double @fabs(double {arg_reg})")
        return res, "Float"
    else:
        dec = "declare i32 @abs(i32)"
        if dec not in compiler.globals_declarations:
            compiler.globals_declarations.append(dec)
        compiler.current_fun_body.append(f"{res} = call i32 @abs(i32 {arg_reg})")
        return res, "Int"

def compile_min(compiler, args):
    arg0, type0 = compiler.compile_expression(args[0])
    arg1, type1 = compiler.compile_expression(args[1])
    res = compiler.next_register()
    if type0 == "Float" or type1 == "Float":
        if type0 == "Int":
            conv = compiler.next_register()
            compiler.current_fun_body.append(f"{conv} = sitofp i32 {arg0} to double")
            arg0 = conv
        if type1 == "Int":
            conv = compiler.next_register()
            compiler.current_fun_body.append(f"{conv} = sitofp i32 {arg1} to double")
            arg1 = conv
        cmp_reg = compiler.next_register()
        compiler.current_fun_body.append(f"{cmp_reg} = fcmp olt double {arg0}, {arg1}")
        compiler.current_fun_body.append(f"{res} = select i1 {cmp_reg}, double {arg0}, double {arg1}")
        return res, "Float"
    else:
        cmp_reg = compiler.next_register()
        compiler.current_fun_body.append(f"{cmp_reg} = icmp slt i32 {arg0}, {arg1}")
        compiler.current_fun_body.append(f"{res} = select i1 {cmp_reg}, i32 {arg0}, i32 {arg1}")
        return res, "Int"

def compile_max(compiler, args):
    arg0, type0 = compiler.compile_expression(args[0])
    arg1, type1 = compiler.compile_expression(args[1])
    res = compiler.next_register()
    if type0 == "Float" or type1 == "Float":
        if type0 == "Int":
            conv = compiler.next_register()
            compiler.current_fun_body.append(f"{conv} = sitofp i32 {arg0} to double")
            arg0 = conv
        if type1 == "Int":
            conv = compiler.next_register()
            compiler.current_fun_body.append(f"{conv} = sitofp i32 {arg1} to double")
            arg1 = conv
        cmp_reg = compiler.next_register()
        compiler.current_fun_body.append(f"{cmp_reg} = fcmp ogt double {arg0}, {arg1}")
        compiler.current_fun_body.append(f"{res} = select i1 {cmp_reg}, double {arg0}, double {arg1}")
        return res, "Float"
    else:
        cmp_reg = compiler.next_register()
        compiler.current_fun_body.append(f"{cmp_reg} = icmp sgt i32 {arg0}, {arg1}")
        compiler.current_fun_body.append(f"{res} = select i1 {cmp_reg}, i32 {arg0}, i32 {arg1}")
        return res, "Int"

COMPILER_METHODS = {
    "sqrt": compile_sqrt,
    "sin": compile_sin,
    "cos": compile_cos,
    "abs": compile_abs,
    "min": compile_min,
    "max": compile_max
}

def infer_abs(args, compiler):
    if args:
        return compiler.infer_type(args[0])
    return "Int"

def infer_minmax(args, compiler):
    if len(args) > 0 and compiler.infer_type(args[0]) == "Float":
        return "Float"
    if len(args) > 1 and compiler.infer_type(args[1]) == "Float":
        return "Float"
    return "Int"

TYPE_SIGNATURES = {
    "sqrt": "Float",
    "sin": "Float",
    "cos": "Float",
    "abs": infer_abs,
    "min": infer_minmax,
    "max": infer_minmax
}
