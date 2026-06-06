from novalang.stdlib import (
    math, string, io, net, crypto, db, ai, collection
)

STDLIB_MODULES = {
    "math": math,
    "string": string,
    "io": io,
    "net": net,
    "crypto": crypto,
    "db": db,
    "ai": ai,
    "collection": collection
}

def load_interpreter_module(name: str) -> dict:
    if name in STDLIB_MODULES:
        return STDLIB_MODULES[name].INTERPRETER_METHODS
    raise RuntimeError(f"Standard library module '{name}' not found")

def execute_vm_call(vm, func_name: str, args: list) -> bool:
    if "." not in func_name:
        return False
    mod_name, func_key = func_name.split(".", 1)
    if mod_name in STDLIB_MODULES:
        module = STDLIB_MODULES[mod_name]
        if func_key in module.VM_METHODS:
            module.VM_METHODS[func_key](vm, args)
            return True
    return False

def compile_stdlib_call(compiler, func_name: str, args: list):
    if "." not in func_name:
        raise RuntimeError(f"Standard library function '{func_name}' is not in a package namespace")
    mod_name, func_key = func_name.split(".", 1)
    if mod_name in STDLIB_MODULES:
        module = STDLIB_MODULES[mod_name]
        if func_key in module.COMPILER_METHODS:
            return module.COMPILER_METHODS[func_key](compiler, args)
    raise RuntimeError(f"Standard library function '{func_name}' not supported in compiler")

def infer_stdlib_type(compiler, func_name: str, args: list) -> str:
    if "." not in func_name:
        return "Int"
    mod_name, func_key = func_name.split(".", 1)
    if mod_name in STDLIB_MODULES:
        module = STDLIB_MODULES[mod_name]
        if func_key in module.TYPE_SIGNATURES:
            sig = module.TYPE_SIGNATURES[func_key]
            if callable(sig):
                return sig(args, compiler)
            return sig
    return "Int"
