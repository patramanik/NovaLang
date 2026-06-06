import sqlite3

def db_query(conn, sql):
    cursor = conn.cursor()
    cursor.execute(sql)
    conn.commit()
    return cursor.fetchall()

INTERPRETER_METHODS = {
    "connect": lambda url: sqlite3.connect(url),
    "query": db_query
}

def vm_connect(vm, args):
    conn = sqlite3.connect(str(args[0].value))
    obj = vm.heap.allocate("DbConnection", conn, vm)
    vm.operand_stack.append(obj)

def vm_query(vm, args):
    conn = args[0].value
    sql = str(args[1].value)
    cursor = conn.cursor()
    cursor.execute(sql)
    conn.commit()
    rows = cursor.fetchall()
    wrapped_rows = []
    for row in rows:
        wrapped_row = [vm.heap.allocate("String", str(val), vm) for val in row]
        wrapped_rows.append(vm.heap.allocate("List", wrapped_row, vm))
    obj = vm.heap.allocate("List", wrapped_rows, vm)
    vm.operand_stack.append(obj)

VM_METHODS = {
    "connect": vm_connect,
    "query": vm_query
}

def compile_connect(compiler, args):
    res_reg = compiler.next_register()
    compiler.current_fun_body.append(f"{res_reg} = add i32 1, 0")
    return res_reg, "Int"

def compile_query(compiler, args):
    res_reg = compiler.next_register()
    compiler.current_fun_body.append(f"{res_reg} = add i32 0, 0")
    return res_reg, "Int"

COMPILER_METHODS = {
    "connect": compile_connect,
    "query": compile_query
}

TYPE_SIGNATURES = {
    "connect": "Int",
    "query": "Int"
}
