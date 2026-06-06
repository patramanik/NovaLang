import urllib.request

def http_request(url):
    try:
        with urllib.request.urlopen(url, timeout=5) as response:
            return response.read().decode('utf-8')
    except Exception as e:
        return f"Error: {e}"

INTERPRETER_METHODS = {
    "request": http_request,
    "listen": lambda port: f"Server listening on port {port}"
}

def vm_request(vm, args):
    try:
        with urllib.request.urlopen(str(args[0].value), timeout=5) as response:
            res_val = response.read().decode('utf-8')
    except Exception as e:
        res_val = f"Error: {e}"
    obj = vm.heap.allocate("String", res_val, vm)
    vm.operand_stack.append(obj)

def vm_listen(vm, args):
    res_val = f"Server listening on port {args[0].value}"
    obj = vm.heap.allocate("String", res_val, vm)
    vm.operand_stack.append(obj)

VM_METHODS = {
    "request": vm_request,
    "listen": vm_listen
}

def compile_request(compiler, args):
    hash_lbl = compiler.get_global_string("mock response")
    ptr_reg = compiler.next_register()
    compiler.current_fun_body.append(f"{ptr_reg} = getelementptr inbounds [14 x i8], ptr {hash_lbl}, i64 0, i64 0")
    return ptr_reg, "String"

def compile_listen(compiler, args):
    hash_lbl = compiler.get_global_string("Server listening on port...")
    ptr_reg = compiler.next_register()
    compiler.current_fun_body.append(f"{ptr_reg} = getelementptr inbounds [27 x i8], ptr {hash_lbl}, i64 0, i64 0")
    return ptr_reg, "String"

COMPILER_METHODS = {
    "request": compile_request,
    "listen": compile_listen
}

TYPE_SIGNATURES = {
    "request": "String",
    "listen": "String"
}
