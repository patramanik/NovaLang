from typing import List, Optional, Tuple
from novalang.lexer import Token, TokenType
from novalang.ast import (
    ASTNode, Program, LetNode, AssignNode, BinaryOpNode, LiteralNode,
    IdentifierNode, PrintNode, BlockNode, FunctionDeclNode, CallNode, IfNode, MatchNode, ReturnNode,
    UnaryOpNode, ImportNode, PackageNode, MemberAccessNode
)

class Parser:
    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.pos = 0
        self.errors = []

    def error(self, message: str, token: Optional[Token] = None):
        tok = token if token else self.current_token()
        err_msg = f"Parser Error at line {tok.line}, column {tok.column}: {message} (got '{tok.value}')"
        self.errors.append(err_msg)
        raise SyntaxError(err_msg)

    def current_token(self) -> Token:
        if self.pos >= len(self.tokens):
            return self.tokens[-1]
        return self.tokens[self.pos]

    def peek_token(self, offset: int = 1) -> Token:
        idx = self.pos + offset
        if idx >= len(self.tokens):
            return self.tokens[-1]
        return self.tokens[idx]

    def check(self, token_type: TokenType) -> bool:
        return self.current_token().type == token_type

    def match(self, token_type: TokenType) -> bool:
        if self.check(token_type):
            self.advance()
            return True
        return False

    def consume(self, token_type: TokenType, message: str) -> Token:
        if self.check(token_type):
            return self.advance()
        self.error(message)

    def advance(self) -> Token:
        tok = self.current_token()
        if tok.type != TokenType.EOF:
            self.pos += 1
        return tok

    def synchronize(self):
        """Skip tokens until we reach a statement boundary to recover from errors."""
        self.advance()
        while not self.check(TokenType.EOF):
            # Synchronize on braces or key declaration keywords
            if self.current_token().value == '\n':
                self.advance()
                return
            if self.current_token().type in (
                TokenType.LET, TokenType.FUN, TokenType.CLASS,
                TokenType.INTERFACE, TokenType.MATCH, TokenType.IF,
                TokenType.RBRACE, TokenType.LBRACE
            ):
                return
            self.advance()

    def parse(self) -> Program:
        statements = []
        while not self.check(TokenType.EOF):
            try:
                # Filter out raw newlines separating statements
                while self.check(TokenType.EOF) is not True and self.current_token().value == '\n':
                    self.advance()
                
                if self.check(TokenType.EOF):
                    break
                    
                stmt = self.parse_statement()
                if stmt:
                    statements.append(stmt)
            except SyntaxError:
                self.synchronize()
        return Program(statements)

    def parse_statement(self) -> Optional[ASTNode]:
        if self.match(TokenType.LET):
            return self.parse_let_declaration()
        elif self.check(TokenType.FUN):
            return self.parse_function_declaration()
        elif self.check(TokenType.IF):
            return self.parse_if_statement()
        elif self.check(TokenType.MATCH):
            return self.parse_match_statement()
        elif self.match(TokenType.PRINT):
            return self.parse_print_statement()
        elif self.check(TokenType.RETURN):
            return self.parse_return_statement()
        elif self.match(TokenType.IMPORT):
            return self.parse_import_statement()
        elif self.match(TokenType.PACKAGE):
            return self.parse_package_statement()
        elif self.check(TokenType.LBRACE):
            return self.parse_block()
        else:
            return self.parse_assignment_or_expression()

    def parse_import_statement(self) -> ASTNode:
        name_parts = [self.consume(TokenType.IDENTIFIER, "Expected module name after 'import'").value]
        while self.match(TokenType.DOT):
            name_parts.append(self.consume(TokenType.IDENTIFIER, "Expected identifier after '.'").value)
        module_name = ".".join(name_parts)
        return ImportNode(module_name)

    def parse_package_statement(self) -> ASTNode:
        name_parts = [self.consume(TokenType.IDENTIFIER, "Expected package name after 'package'").value]
        while self.match(TokenType.DOT):
            name_parts.append(self.consume(TokenType.IDENTIFIER, "Expected identifier after '.'").value)
        package_name = ".".join(name_parts)
        return PackageNode(package_name)

    def parse_return_statement(self) -> ASTNode:
        self.consume(TokenType.RETURN, "Expected 'return'")
        expr = None
        # Check if there is an expression following return
        if not self.check(TokenType.RBRACE) and not self.check(TokenType.EOF) and self.current_token().value != '\n':
            expr = self.parse_expression()
        return ReturnNode(expr)

    def parse_let_declaration(self) -> ASTNode:
        ident_tok = self.consume(TokenType.IDENTIFIER, "Expected identifier after 'let'")
        self.consume(TokenType.ASSIGN, "Expected '=' after identifier in let declaration")
        expr = self.parse_expression()
        return LetNode(ident_tok.value, expr)

    def parse_function_declaration(self) -> ASTNode:
        self.consume(TokenType.FUN, "Expected 'fun'")
        ident_tok = self.consume(TokenType.IDENTIFIER, "Expected function name")
        
        self.consume(TokenType.LPAREN, "Expected '(' after function name")
        params = []
        if not self.check(TokenType.RPAREN):
            while True:
                param_name_tok = self.consume(TokenType.IDENTIFIER, "Expected parameter name")
                param_type = None
                if self.match(TokenType.COLON):
                    type_tok = self.consume(TokenType.IDENTIFIER, "Expected parameter type name")
                    param_type = type_tok.value
                params.append((param_name_tok.value, param_type))
                if not self.match(TokenType.COMMA):
                    break
        self.consume(TokenType.RPAREN, "Expected ')' after parameter list")
        
        return_type = None
        if self.match(TokenType.COLON):
            ret_type_tok = self.consume(TokenType.IDENTIFIER, "Expected return type name")
            return_type = ret_type_tok.value
            
        body = self.parse_block()
        return FunctionDeclNode(ident_tok.value, params, return_type, body)

    def parse_if_statement(self) -> ASTNode:
        self.consume(TokenType.IF, "Expected 'if'")
        self.consume(TokenType.LPAREN, "Expected '(' before condition")
        condition = self.parse_expression()
        self.consume(TokenType.RPAREN, "Expected ')' after condition")
        
        then_branch = self.parse_block()
        else_branch = None
        if self.match(TokenType.ELSE):
            if self.check(TokenType.IF):
                else_branch = self.parse_if_statement()
            else:
                else_branch = self.parse_block()
                
        return IfNode(condition, then_branch, else_branch)

    def parse_match_statement(self) -> ASTNode:
        self.consume(TokenType.MATCH, "Expected 'match'")
        val = self.parse_expression()
        self.consume(TokenType.LBRACE, "Expected '{' after match value")
        
        cases = []
        while not self.check(TokenType.RBRACE) and not self.check(TokenType.EOF):
            # Read pattern
            # Support wildcard '_' or literals
            pattern = None
            if self.current_token().value == "_":
                pattern = IdentifierNode(self.advance().value)
            else:
                pattern = self.parse_expression()
                
            self.consume(TokenType.ARROW, "Expected '=>' after pattern")
            
            # Case body can be a block or a single statement
            body = self.parse_block()
            cases.append((pattern, body))
            
            # Strip newlines separating cases
            while self.current_token().value == '\n':
                self.advance()
                
        self.consume(TokenType.RBRACE, "Expected '}' to close match cases")
        return MatchNode(val, cases)

    def parse_print_statement(self) -> ASTNode:
        self.consume(TokenType.LPAREN, "Expected '(' after print")
        expr = self.parse_expression()
        self.consume(TokenType.RPAREN, "Expected ')' after expression")
        return PrintNode(expr)

    def parse_block(self) -> BlockNode:
        self.consume(TokenType.LBRACE, "Expected '{'")
        statements = []
        while not self.check(TokenType.RBRACE) and not self.check(TokenType.EOF):
            while self.current_token().value == '\n':
                self.advance()
            if self.check(TokenType.RBRACE):
                break
            stmt = self.parse_statement()
            if stmt:
                statements.append(stmt)
            while self.current_token().value == '\n':
                self.advance()
        self.consume(TokenType.RBRACE, "Expected '}'")
        return BlockNode(statements)

    def parse_assignment_or_expression(self) -> ASTNode:
        # Check if it's assignment or declaration:
        # x = expression
        # x: Type = expression
        if self.check(TokenType.IDENTIFIER):
            next_t = self.peek_token(1)
            if next_t.type == TokenType.ASSIGN:
                ident = self.advance()  # consume identifier
                self.advance()  # consume '='
                val = self.parse_expression()
                return AssignNode(ident.value, val)
            elif next_t.type == TokenType.COLON:
                # name: Type = expr
                ident = self.advance()  # consume identifier
                self.advance()  # consume ':'
                type_tok = self.consume(TokenType.IDENTIFIER, "Expected type name after ':'")
                self.consume(TokenType.ASSIGN, "Expected '=' after type annotation")
                val = self.parse_expression()
                return AssignNode(ident.value, val, type_tok.value)
            elif next_t.type in (TokenType.ADD_ASSIGN, TokenType.SUB_ASSIGN, TokenType.MUL_ASSIGN, TokenType.DIV_ASSIGN):
                ident = self.advance()  # consume identifier
                op_tok = self.advance()  # consume compound assign token
                val = self.parse_expression()
                op_map = {
                    TokenType.ADD_ASSIGN: "+",
                    TokenType.SUB_ASSIGN: "-",
                    TokenType.MUL_ASSIGN: "*",
                    TokenType.DIV_ASSIGN: "/"
                }
                op = op_map[op_tok.type]
                rhs = BinaryOpNode(IdentifierNode(ident.value), op, val)
                return AssignNode(ident.value, rhs)
                
        return self.parse_expression()

    def parse_expression(self) -> ASTNode:
        return self.parse_logical_or()

    def parse_logical_or(self) -> ASTNode:
        expr = self.parse_logical_and()
        while self.check(TokenType.OR):
            op = self.advance().value
            right = self.parse_logical_and()
            expr = BinaryOpNode(expr, op, right)
        return expr

    def parse_logical_and(self) -> ASTNode:
        expr = self.parse_equality()
        while self.check(TokenType.AND):
            op = self.advance().value
            right = self.parse_equality()
            expr = BinaryOpNode(expr, op, right)
        return expr

    def parse_equality(self) -> ASTNode:
        expr = self.parse_comparison()
        while self.check(TokenType.EQ) or self.check(TokenType.NE):
            op = self.advance().value
            right = self.parse_comparison()
            expr = BinaryOpNode(expr, op, right)
        return expr

    def parse_comparison(self) -> ASTNode:
        expr = self.parse_addition()
        while self.check(TokenType.LT) or self.check(TokenType.GT) or self.check(TokenType.LE) or self.check(TokenType.GE):
            op = self.advance().value
            right = self.parse_addition()
            expr = BinaryOpNode(expr, op, right)
        return expr

    def parse_addition(self) -> ASTNode:
        expr = self.parse_multiplication()
        while self.check(TokenType.PLUS) or self.check(TokenType.MINUS):
            op = self.advance().value
            right = self.parse_multiplication()
            expr = BinaryOpNode(expr, op, right)
        return expr

    def parse_multiplication(self) -> ASTNode:
        expr = self.parse_unary()
        while self.check(TokenType.MUL) or self.check(TokenType.DIV) or self.check(TokenType.PERCENT):
            op = self.advance().value
            right = self.parse_unary()
            expr = BinaryOpNode(expr, op, right)
        return expr

    def parse_unary(self) -> ASTNode:
        if self.check(TokenType.NOT) or self.check(TokenType.MINUS) or self.check(TokenType.PLUS):
            op_tok = self.advance()
            right = self.parse_unary()
            return UnaryOpNode(op_tok.value, right)
        return self.parse_postfix()

    def parse_postfix(self) -> ASTNode:
        expr = self.parse_primary_value()
        while True:
            if self.match(TokenType.DOT):
                member_tok = self.consume(TokenType.IDENTIFIER, "Expected identifier after '.'")
                expr = MemberAccessNode(expr, member_tok.value)
            elif self.match(TokenType.LPAREN):
                args = []
                if not self.check(TokenType.RPAREN):
                    while True:
                        args.append(self.parse_expression())
                        if not self.match(TokenType.COMMA):
                            break
                self.consume(TokenType.RPAREN, "Expected ')' after arguments list")
                expr = CallNode(expr, args)
            else:
                break
        return expr

    def parse_primary_value(self) -> ASTNode:
        tok = self.current_token()
        
        if self.match(TokenType.INTEGER):
            return LiteralNode(int(tok.value))
        elif self.match(TokenType.FLOAT):
            return LiteralNode(float(tok.value))
        elif self.match(TokenType.STRING):
            return LiteralNode(tok.value)
        elif self.match(TokenType.TRUE):
            return LiteralNode(True)
        elif self.match(TokenType.FALSE):
            return LiteralNode(False)
        elif self.match(TokenType.NULL):
            return LiteralNode(None)
        elif self.check(TokenType.IDENTIFIER):
            ident = self.advance()
            return IdentifierNode(ident.value)
        elif self.match(TokenType.LPAREN):
            expr = self.parse_expression()
            self.consume(TokenType.RPAREN, "Expected ')' after expression")
            return expr
            
        self.error("Expected expression")
