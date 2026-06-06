import unittest
from novalang.lexer import Lexer, TokenType
from novalang.parser import Parser
from novalang.ast import LiteralNode, IdentifierNode, LetNode, AssignNode, BinaryOpNode
from novalang.interpreter import Interpreter, Environment

class TestLexer(unittest.TestCase):
    def test_basic_tokens(self):
        source = "let name = \"Manik\"\nage: Int = 21"
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        
        # Verify Token Stream
        self.assertEqual(tokens[0].type, TokenType.LET)
        self.assertEqual(tokens[1].type, TokenType.IDENTIFIER)
        self.assertEqual(tokens[1].value, "name")
        self.assertEqual(tokens[2].type, TokenType.ASSIGN)
        self.assertEqual(tokens[3].type, TokenType.STRING)
        self.assertEqual(tokens[3].value, "Manik")
        self.assertEqual(tokens[4].type, TokenType.IDENTIFIER)
        self.assertEqual(tokens[4].value, "age")
        self.assertEqual(tokens[5].type, TokenType.COLON)
        self.assertEqual(tokens[6].type, TokenType.IDENTIFIER)
        self.assertEqual(tokens[6].value, "Int")
        self.assertEqual(tokens[7].type, TokenType.ASSIGN)
        self.assertEqual(tokens[8].type, TokenType.INTEGER)
        self.assertEqual(tokens[8].value, "21")
        self.assertEqual(tokens[9].type, TokenType.EOF)

    def test_new_keywords_and_operators(self):
        source = """
        import math
        package main
        class Car extends Vehicle {
            init() {
                self.speed = 0
            }
        }
        /* This is a block comment
           spanning multiple lines */
        try {
            let x = 10
            x += 5
            x -= 2
            x *= 3
            x /= 4
            if (x != 0 && x <= 100 || !false) {
                print(x % 3)
            }
        } catch(e) {
            print(null)
        }
        while (true) { break; }
        for x in list { continue; }
        struct Point { x, y }
        enum Color { RED, GREEN }
        """
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        
        types = [t.type for t in tokens]
        self.assertIn(TokenType.IMPORT, types)
        self.assertIn(TokenType.PACKAGE, types)
        self.assertIn(TokenType.EXTENDS, types)
        self.assertIn(TokenType.SELF, types)
        self.assertIn(TokenType.TRY, types)
        self.assertIn(TokenType.CATCH, types)
        self.assertIn(TokenType.ADD_ASSIGN, types)
        self.assertIn(TokenType.SUB_ASSIGN, types)
        self.assertIn(TokenType.MUL_ASSIGN, types)
        self.assertIn(TokenType.DIV_ASSIGN, types)
        self.assertIn(TokenType.NE, types)
        self.assertIn(TokenType.LE, types)
        self.assertIn(TokenType.AND, types)
        self.assertIn(TokenType.OR, types)
        self.assertIn(TokenType.NOT, types)
        self.assertIn(TokenType.PERCENT, types)
        self.assertIn(TokenType.NULL, types)
        self.assertIn(TokenType.WHILE, types)
        self.assertIn(TokenType.BREAK, types)
        self.assertIn(TokenType.SEMICOLON, types)
        self.assertIn(TokenType.FOR, types)
        self.assertIn(TokenType.IN, types)
        self.assertIn(TokenType.CONTINUE, types)
        self.assertIn(TokenType.STRUCT, types)
        self.assertIn(TokenType.ENUM, types)
        self.assertIn(TokenType.DOT, types)

class TestParser(unittest.TestCase):
    def test_let_and_assign(self):
        source = "let name = \"Manik\"\nage: Int = 21\nvalue = 25"
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        
        self.assertEqual(len(parser.errors), 0)
        self.assertEqual(len(ast.statements), 3)
        self.assertIsInstance(ast.statements[0], LetNode)
        self.assertIsInstance(ast.statements[1], AssignNode)
        self.assertEqual(ast.statements[1].type_ann, "Int")
        self.assertIsInstance(ast.statements[2], AssignNode)
        self.assertEqual(ast.statements[2].type_ann, None)

class TestInterpreter(unittest.TestCase):
    def test_evaluation(self):
        # 1. Test basic calculations and variable lookup
        source = "x = 10\ny = 20\nlet z = x + y * 2\nprint(z)"
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        
        interpreter = Interpreter()
        interpreter.interpret(ast)
        self.assertEqual(interpreter.environment.get("z"), 50)

    def test_static_type_checking(self):
        # Statically typed Int assigned to String value should raise TypeError
        source = "age: Int = \"twenty\""
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        
        interpreter = Interpreter()
        with self.assertRaises(TypeError):
            interpreter.interpret(ast)

    def test_functions(self):
        source = """
        fun add(a: Int, b: Int): Int {
            return a + b
        }
        let result = add(5, 15)
        """
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        
        interpreter = Interpreter()
        interpreter.interpret(ast)
        self.assertEqual(interpreter.environment.get("result"), 20)

    def test_match_statement(self):
        source = """
        x = 2
        y = "other"
        match x {
            1 => { y = "one" }
            2 => { y = "two" }
            _ => { y = "wildcard" }
        }
        """
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        
        interpreter = Interpreter()
        interpreter.interpret(ast)
        self.assertEqual(interpreter.environment.get("y"), "two")

    def test_improved_features(self):
        source = """
        // 1. Compound assignment
        x = 10
        x += 5
        x -= 3
        x *= 2
        x /= 4
        
        // 2. Modulo operator
        mod_val = 17 % 5
        
        // 3. Comparison / Relational operators
        is_le = 5 <= 10
        is_ge = 10 >= 10
        is_ne = 5 != 10
        
        // 4. Logical operators with short-circuiting
        t = true
        f = false
        and_val = t && f
        or_val = f || t
        
        // 5. Unary operators
        neg = -10
        pos = +5
        not_val = !false
        
        // 6. Built-ins call
        msg = "Hello"
        msg_len = len(msg)
        s_val = str(123)
        i_val = int("456")
        """
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        
        interpreter = Interpreter()
        interpreter.interpret(ast)
        
        self.assertEqual(interpreter.environment.get("x"), 6.0)
        self.assertEqual(interpreter.environment.get("mod_val"), 2)
        self.assertEqual(interpreter.environment.get("is_le"), True)
        self.assertEqual(interpreter.environment.get("is_ge"), True)
        self.assertEqual(interpreter.environment.get("is_ne"), True)
        self.assertEqual(interpreter.environment.get("and_val"), False)
        self.assertEqual(interpreter.environment.get("or_val"), True)
        self.assertEqual(interpreter.environment.get("neg"), -10)
        self.assertEqual(interpreter.environment.get("pos"), 5)
        self.assertEqual(interpreter.environment.get("not_val"), True)
        self.assertEqual(interpreter.environment.get("msg_len"), 5)
        self.assertEqual(interpreter.environment.get("s_val"), "123")
        self.assertEqual(interpreter.environment.get("i_val"), 456)

import os
import shutil

class TestPackageManager(unittest.TestCase):
    def setUp(self):
        # Create a temp dir inside the workspace (temporary directories must be inside workspace)
        self.test_dir_parent = os.path.abspath("test_temp")
        os.makedirs(self.test_dir_parent, exist_ok=True)
        self.project_name = "test_project"
        self.project_path = os.path.join(self.test_dir_parent, self.project_name)

    def tearDown(self):
        if os.path.exists(self.test_dir_parent):
            shutil.rmtree(self.test_dir_parent)

    def test_init_project(self):
        from novalang.main import init_project
        
        # Run init
        init_project(self.project_path)
        
        # Verify files were created
        self.assertTrue(os.path.isdir(self.project_path))
        self.assertTrue(os.path.isfile(os.path.join(self.project_path, "nova.toml")))
        self.assertTrue(os.path.isfile(os.path.join(self.project_path, "README.md")))
        self.assertTrue(os.path.isfile(os.path.join(self.project_path, ".gitignore")))
        self.assertTrue(os.path.isdir(os.path.join(self.project_path, "src")))
        self.assertTrue(os.path.isfile(os.path.join(self.project_path, "src", "main.nova")))

        # Verify content of toml
        from novalang.main import load_manifest
        manifest = load_manifest(self.project_path)
        self.assertEqual(manifest["package"]["name"], self.project_name)

    def test_build_and_run_project(self):
        from novalang.main import init_project, build_file, run_file
        
        init_project(self.project_path)
        entry_point = os.path.join(self.project_path, "src", "main.nova")
        
        # Test build
        build_ok = build_file(entry_point)
        self.assertTrue(build_ok)
        
        # Test run
        run_ok = run_file(entry_point)
        self.assertTrue(run_ok)

class TestCompiler(unittest.TestCase):
    def test_llvm_ir_generation(self):
        from novalang.compiler import LLVMCompiler
        source = """
        fun add(a: Int, b: Int): Int {
            return a + b
        }
        
        let msg = "Nova IR works"
        print(msg)
        
        val_int: Int = 10
        val_float: Float = 5.5
        val_bool: Bool = true
        
        x = add(val_int, 5)
        if (x > 10 && val_bool) {
            print("x is greater than 10")
        } else {
            print("x is small")
        }
        """
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        
        compiler = LLVMCompiler()
        ir = compiler.compile(ast)
        
        self.assertIn("@printf", ir)
        self.assertIn("define i32 @add(i32 %a_param, i32 %b_param)", ir)
        self.assertIn("define i32 @main()", ir)
        self.assertIn("alloca i32", ir)
        self.assertIn("global double", ir)
        self.assertIn("alloca i1", ir)
        self.assertIn("icmp sgt", ir)
        self.assertIn("br i1", ir)
        self.assertIn("call i32 @add", ir)

class TestVM(unittest.TestCase):
    def test_basic_arithmetic_and_variables(self):
        from novalang.codegen_vm import VMBytecodeGenerator
        from novalang.vm import VirtualMachine
        source = """
        x = 5
        y = 10
        z = x + y * 2.5
        """
        lexer = Lexer(source)
        ast = Parser(lexer.tokenize()).parse()
        bytecode = VMBytecodeGenerator().generate(ast)
        
        vm = VirtualMachine()
        res = vm.run(bytecode)
        self.assertEqual(res, 30.0)

    def test_conditionals_and_match(self):
        from novalang.codegen_vm import VMBytecodeGenerator
        from novalang.vm import VirtualMachine
        source = """
        let inputVal = 5
        res = 0
        match inputVal {
            1 => { res = 10 }
            5 => { res = 50 }
            _ => { res = 99 }
        }
        """
        lexer = Lexer(source)
        ast = Parser(lexer.tokenize()).parse()
        bytecode = VMBytecodeGenerator().generate(ast)
        
        vm = VirtualMachine()
        res = vm.run(bytecode)
        self.assertEqual(res, 50)

    def test_functions_and_recursion(self):
        from novalang.codegen_vm import VMBytecodeGenerator
        from novalang.vm import VirtualMachine
        source = """
        fun fib(n: Int): Int {
            if (n <= 1) {
                return n
            }
            return fib(n - 1) + fib(n - 2)
        }
        let ans = fib(6)
        """
        lexer = Lexer(source)
        ast = Parser(lexer.tokenize()).parse()
        bytecode = VMBytecodeGenerator().generate(ast)
        
        vm = VirtualMachine()
        res = vm.run(bytecode)
        self.assertEqual(res, 8)

    def test_generational_gc(self):
        from novalang.codegen_vm import VMBytecodeGenerator
        from novalang.vm import VirtualMachine
        source = """
        x = 0
        x = x + 1
        x = x + 2
        x = x + 3
        x = x + 4
        x = x + 5
        x = x + 6
        x = x + 7
        x = x + 8
        x = x + 9
        x = x + 10
        x = x + 11
        x = x + 12
        x = x + 13
        x = x + 14
        x = x + 15
        x = x + 16
        """
        lexer = Lexer(source)
        ast = Parser(lexer.tokenize()).parse()
        bytecode = VMBytecodeGenerator().generate(ast)
        
        vm = VirtualMachine(nursery_threshold=5)
        res = vm.run(bytecode)
        self.assertGreater(vm.heap.gc_count, 0)
        self.assertGreater(vm.heap.promotion_count, 0)
        self.assertEqual(res, 136)

if __name__ == "__main__":
    unittest.main()
