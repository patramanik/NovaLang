def list_add(lst, val):
    lst.append(val)
    return lst

def map_set(m, k, v):
    m[k] = v
    return m

INTERPRETER_METHODS = {
    "list": lambda: [],
    "list_add": list_add,
    "list_get": lambda lst, idx: lst[idx],
    "list_len": lambda lst: len(lst),
    "map": lambda: {},
    "map_set": map_set,
    "map_get": lambda m, k: m.get(k),
    "map_has": lambda m, k: k in m
}

def vm_list(vm, args):
    obj = vm.heap.allocate("List", [], vm)
    vm.operand_stack.append(obj)

def vm_list_add(vm, args):
    lst_obj = args[0]
    val_obj = args[1]
    lst_obj.value.append(val_obj)
    vm.operand_stack.append(lst_obj)

def vm_list_get(vm, args):
    lst_obj = args[0]
    idx = int(args[1].value)
    vm.operand_stack.append(lst_obj.value[idx])

def vm_list_len(vm, args):
    lst_obj = args[0]
    obj = vm.heap.allocate("Int", len(lst_obj.value), vm)
    vm.operand_stack.append(obj)

def vm_map(vm, args):
    obj = vm.heap.allocate("Map", {}, vm)
    vm.operand_stack.append(obj)

def vm_map_set(vm, args):
    map_obj = args[0]
    key_val = args[1].value
    val_obj = args[2]
    map_obj.value[key_val] = val_obj
    vm.operand_stack.append(map_obj)

def vm_map_get(vm, args):
    map_obj = args[0]
    key_val = args[1].value
    res = map_obj.value.get(key_val, vm.heap.allocate("Null", None, vm))
    vm.operand_stack.append(res)

def vm_map_has(vm, args):
    map_obj = args[0]
    key_val = args[1].value
    res = key_val in map_obj.value
    obj = vm.heap.allocate("Bool", res, vm)
    vm.operand_stack.append(obj)

VM_METHODS = {
    "list": vm_list,
    "list_add": vm_list_add,
    "list_get": vm_list_get,
    "list_len": vm_list_len,
    "map": vm_map,
    "map_set": vm_map_set,
    "map_get": vm_map_get,
    "map_has": vm_map_has
}

def compile_list(compiler, args):
    hash_lbl = compiler.get_global_string("mock list")
    ptr_reg = compiler.next_register()
    compiler.current_fun_body.append(f"{ptr_reg} = getelementptr inbounds [10 x i8], ptr {hash_lbl}, i64 0, i64 0")
    return ptr_reg, "String"

def compile_list_add(compiler, args):
    arg_reg, _ = compiler.compile_expression(args[0])
    return arg_reg, "String"

def compile_list_get(compiler, args):
    res_reg = compiler.next_register()
    compiler.current_fun_body.append(f"{res_reg} = add i32 0, 0")
    return res_reg, "Int"

def compile_list_len(compiler, args):
    res_reg = compiler.next_register()
    compiler.current_fun_body.append(f"{res_reg} = add i32 0, 0")
    return res_reg, "Int"

def compile_map(compiler, args):
    hash_lbl = compiler.get_global_string("mock map")
    ptr_reg = compiler.next_register()
    compiler.current_fun_body.append(f"{ptr_reg} = getelementptr inbounds [9 x i8], ptr {hash_lbl}, i64 0, i64 0")
    return ptr_reg, "String"

def compile_map_set(compiler, args):
    arg_reg, _ = compiler.compile_expression(args[0])
    return arg_reg, "String"

def compile_map_get(compiler, args):
    res_reg = compiler.next_register()
    compiler.current_fun_body.append(f"{res_reg} = add i32 0, 0")
    return res_reg, "Int"

def compile_map_has(compiler, args):
    res_reg = compiler.next_register()
    compiler.current_fun_body.append(f"{res_reg} = xor i1 0, 0")
    return res_reg, "Bool"

COMPILER_METHODS = {
    "list": compile_list,
    "list_add": compile_list_add,
    "list_get": compile_list_get,
    "list_len": compile_list_len,
    "map": compile_map,
    "map_set": compile_map_set,
    "map_get": compile_map_get,
    "map_has": compile_map_has
}

TYPE_SIGNATURES = {
    "list": "String",
    "list_add": "String",
    "list_get": "Int",
    "list_len": "Int",
    "map": "String",
    "map_set": "String",
    "map_get": "Int",
    "map_has": "Bool"
}
