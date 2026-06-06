import sys

def readfile(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

def writefile(path, content):
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

INTERPRETER_METHODS = {
    "readline": lambda: sys.stdin.readline().rstrip("\r\n"),
    "readfile": readfile,
    "writefile": writefile
}

def vm_readline(vm, args):
    val = sys.stdin.readline().rstrip("\r\n")
    obj = vm.heap.allocate("String", val, vm)
    vm.operand_stack.append(obj)

def vm_readfile(vm, args):
    with open(args[0].value, "r", encoding="utf-8") as f:
        content = f.read()
    obj = vm.heap.allocate("String", content, vm)
    vm.operand_stack.append(obj)

def vm_writefile(vm, args):
    with open(args[0].value, "w", encoding="utf-8") as f:
        f.write(str(args[1].value))
    obj = vm.heap.allocate("Null", None, vm)
    vm.operand_stack.append(obj)

VM_METHODS = {
    "readline": vm_readline,
    "readfile": vm_readfile,
    "writefile": vm_writefile
}

def compile_readline(compiler, args):
    hash_lbl = compiler.get_global_string("mock input")
    ptr_reg = compiler.next_register()
    compiler.current_fun_body.append(f"{ptr_reg} = getelementptr inbounds [11 x i8], ptr {hash_lbl}, i64 0, i64 0")
    return ptr_reg, "String"

def compile_readfile(compiler, args):
    hash_lbl = compiler.get_global_string("mock file content")
    ptr_reg = compiler.next_register()
    compiler.current_fun_body.append(f"{ptr_reg} = getelementptr inbounds [18 x i8], ptr {hash_lbl}, i64 0, i64 0")
    return ptr_reg, "String"

def compile_writefile(compiler, args):
    res_reg = compiler.next_register()
    compiler.current_fun_body.append(f"{res_reg} = add i32 0, 0")
    return res_reg, "Int"

COMPILER_METHODS = {
    "readline": compile_readline,
    "readfile": compile_readfile,
    "writefile": compile_writefile
}

TYPE_SIGNATURES = {
    "readline": "String",
    "readfile": "String",
    "writefile": "Int"
}
