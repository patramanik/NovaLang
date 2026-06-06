import sys
from novalang.lexer import Lexer
from novalang.parser import Parser
from novalang.interpreter import Interpreter

def run_repl():
    interpreter = Interpreter()
    print("NovaLang Interactive REPL (v1.3.0)")
    print("Press Ctrl+C to clear current line, Ctrl+D to exit.")
    
    while True:
        try:
            line = input("nova> ")
            if not line.strip():
                continue
                
            # Run compiler stages
            lexer = Lexer(line)
            tokens = lexer.tokenize()
            
            parser = Parser(tokens)
            ast = parser.parse()
            
            if parser.errors:
                for err in parser.errors:
                    print(err, file=sys.stderr)
                continue
                
            result = interpreter.interpret(ast)
            if result is not None:
                print(result)
                
        except KeyboardInterrupt:
            print("\nKeyboardInterrupt (line cleared)")
            continue
        except EOFError:
            print("\nExiting REPL. Goodbye!")
            break
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)

if __name__ == "__main__":
    run_repl()
