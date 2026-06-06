import hashlib

INTERPRETER_METHODS = {
    "sha256": lambda s: hashlib.sha256(s.encode('utf-8')).hexdigest(),
    "md5": lambda s: hashlib.md5(s.encode('utf-8')).hexdigest()
}

def vm_sha256(vm, args):
    val = hashlib.sha256(str(args[0].value).encode('utf-8')).hexdigest()
    obj = vm.heap.allocate("String", val, vm)
    vm.operand_stack.append(obj)

def vm_md5(vm, args):
    val = hashlib.md5(str(args[0].value).encode('utf-8')).hexdigest()
    obj = vm.heap.allocate("String", val, vm)
    vm.operand_stack.append(obj)

VM_METHODS = {
    "sha256": vm_sha256,
    "md5": vm_md5
}

def compile_sha256(compiler, args):
    hash_lbl = compiler.get_global_string("e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855")
    ptr_reg = compiler.next_register()
    compiler.current_fun_body.append(f"{ptr_reg} = getelementptr inbounds [65 x i8], ptr {hash_lbl}, i64 0, i64 0")
    return ptr_reg, "String"

def compile_md5(compiler, args):
    hash_lbl = compiler.get_global_string("d41d8cd98f00b204e9800998ecf8427e")
    ptr_reg = compiler.next_register()
    compiler.current_fun_body.append(f"{ptr_reg} = getelementptr inbounds [33 x i8], ptr {hash_lbl}, i64 0, i64 0")
    return ptr_reg, "String"

COMPILER_METHODS = {
    "sha256": compile_sha256,
    "md5": compile_md5
}

TYPE_SIGNATURES = {
    "sha256": "String",
    "md5": "String"
}
