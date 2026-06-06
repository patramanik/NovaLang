import enum
import re
from typing import List, NamedTuple, Optional

class TokenType(enum.Enum):
    # Keywords
    LET = "let"
    FUN = "fun"
    CLASS = "class"
    INTERFACE = "interface"
    MATCH = "match"
    THREAD = "thread"
    ASYNC = "async"
    AWAIT = "await"
    UNSAFE = "unsafe"
    EXTERN = "extern"
    ASM = "asm"
    IF = "if"
    ELSE = "else"
    TRUE = "true"
    FALSE = "false"
    PRINT = "print"
    RETURN = "return"
    
    # New Keywords
    IMPORT = "import"
    PACKAGE = "package"
    EXTENDS = "extends"
    SELF = "self"
    TRY = "try"
    CATCH = "catch"
    WHILE = "while"
    FOR = "for"
    IN = "in"
    BREAK = "break"
    CONTINUE = "continue"
    STRUCT = "struct"
    ENUM = "enum"
    NULL = "null"

    # Literals & Identifiers
    IDENTIFIER = "IDENTIFIER"
    INTEGER = "INTEGER"
    FLOAT = "FLOAT"
    STRING = "STRING"

    # Operators
    ASSIGN = "="
    PLUS = "+"
    MINUS = "-"
    MUL = "*"
    DIV = "/"
    EQ = "=="
    LT = "<"
    GT = ">"
    ARROW = "=>"
    COLON = ":"
    
    # New Operators
    NE = "!="
    LE = "<="
    GE = ">="
    AND = "&&"
    OR = "||"
    NOT = "!"
    ADD_ASSIGN = "+="
    SUB_ASSIGN = "-="
    MUL_ASSIGN = "*="
    DIV_ASSIGN = "/="

    # Syntax delimiters
    LPAREN = "("
    RPAREN = ")"
    LBRACE = "{"
    RBRACE = "}"
    COMMA = ","
    
    # New Delimiters / Accessors
    DOT = "."
    SEMICOLON = ";"
    LBRACKET = "["
    RBRACKET = "]"
    PERCENT = "%"
    
    # Special
    EOF = "EOF"

class Token(NamedTuple):
    type: TokenType
    value: str
    line: int
    column: int

class Lexer:
    def __init__(self, source: str):
        self.source = source
        self.pos = 0
        self.line = 1
        self.column = 1
        self.length = len(source)

    def error(self, message: str):
        raise SyntaxError(f"Lexer Error at line {self.line}, column {self.column}: {message}")

    def peek(self) -> str:
        if self.pos >= self.length:
            return ""
        return self.source[self.pos]

    def advance(self) -> str:
        char = self.peek()
        self.pos += 1
        if char == "\n":
            self.line += 1
            self.column = 1
        else:
            self.column += 1
        return char

    def skip_whitespace_and_comments(self):
        while self.pos < self.length:
            char = self.peek()
            if char.isspace():
                self.advance()
            elif char == "/" and self.pos + 1 < self.length and self.source[self.pos + 1] == "/":
                # Line comment
                while self.pos < self.length and self.peek() != "\n":
                    self.advance()
            elif char == "/" and self.pos + 1 < self.length and self.source[self.pos + 1] == "*":
                # Block comment
                self.advance()  # Skip '/'
                self.advance()  # Skip '*'
                while self.pos < self.length:
                    if self.peek() == "*" and self.pos + 1 < self.length and self.source[self.pos + 1] == "/":
                        self.advance()  # Skip '*'
                        self.advance()  # Skip '/'
                        break
                    self.advance()
            else:
                break

    def read_string(self) -> Token:
        start_line = self.line
        start_column = self.column
        self.advance()  # Skip the opening quote
        result = []
        while self.pos < self.length and self.peek() != '"':
            char = self.advance()
            if char == '\\':  # Escape sequence
                if self.pos < self.length:
                    escaped = self.advance()
                    if escaped == 'n':
                        result.append('\n')
                    elif escaped == 't':
                        result.append('\t')
                    elif escaped == '"':
                        result.append('"')
                    elif escaped == '\\':
                        result.append('\\')
                    else:
                        result.append(escaped)
            else:
                result.append(char)
        if self.pos >= self.length:
            self.error("Unterminated string literal")
        self.advance()  # Skip closing quote
        return Token(TokenType.STRING, "".join(result), start_line, start_column)

    def read_number(self) -> Token:
        start_line = self.line
        start_column = self.column
        result = []
        while self.pos < self.length and (self.peek().isdigit() or self.peek() == '.'):
            result.append(self.advance())
        
        num_str = "".join(result)
        if num_str.count('.') > 1:
            self.error(f"Malformed float literal: {num_str}")
        
        if '.' in num_str:
            return Token(TokenType.FLOAT, num_str, start_line, start_column)
        return Token(TokenType.INTEGER, num_str, start_line, start_column)

    def read_identifier(self) -> Token:
        start_line = self.line
        start_column = self.column
        result = []
        while self.pos < self.length and (self.peek().isalnum() or self.peek() == '_'):
            result.append(self.advance())
        
        ident = "".join(result)
        # Check if it is a keyword
        try:
            token_type = TokenType(ident)
            return Token(token_type, ident, start_line, start_column)
        except ValueError:
            return Token(TokenType.IDENTIFIER, ident, start_line, start_column)

    def next_token(self) -> Token:
        self.skip_whitespace_and_comments()

        if self.pos >= self.length:
            return Token(TokenType.EOF, "", self.line, self.column)

        char = self.peek()

        # Strings
        if char == '"':
            return self.read_string()

        # Numbers
        if char.isdigit():
            return self.read_number()

        # Identifiers / Keywords
        if char.isalpha() or char == '_':
            return self.read_identifier()

        # Double-char operators
        # Double/compound and logic operators
        if char == "=":
            start_line, start_col = self.line, self.column
            self.advance()
            if self.peek() == "=":
                self.advance()
                return Token(TokenType.EQ, "==", start_line, start_col)
            elif self.peek() == ">":
                self.advance()
                return Token(TokenType.ARROW, "=>", start_line, start_col)
            return Token(TokenType.ASSIGN, "=", start_line, start_col)

        if char == "!":
            start_line, start_col = self.line, self.column
            self.advance()
            if self.peek() == "=":
                self.advance()
                return Token(TokenType.NE, "!=", start_line, start_col)
            return Token(TokenType.NOT, "!", start_line, start_col)

        if char == "<":
            start_line, start_col = self.line, self.column
            self.advance()
            if self.peek() == "=":
                self.advance()
                return Token(TokenType.LE, "<=", start_line, start_col)
            return Token(TokenType.LT, "<", start_line, start_col)

        if char == ">":
            start_line, start_col = self.line, self.column
            self.advance()
            if self.peek() == "=":
                self.advance()
                return Token(TokenType.GE, ">=", start_line, start_col)
            return Token(TokenType.GT, ">", start_line, start_col)

        if char == "+":
            start_line, start_col = self.line, self.column
            self.advance()
            if self.peek() == "=":
                self.advance()
                return Token(TokenType.ADD_ASSIGN, "+=", start_line, start_col)
            return Token(TokenType.PLUS, "+", start_line, start_col)

        if char == "-":
            start_line, start_col = self.line, self.column
            self.advance()
            if self.peek() == "=":
                self.advance()
                return Token(TokenType.SUB_ASSIGN, "-=", start_line, start_col)
            return Token(TokenType.MINUS, "-", start_line, start_col)

        if char == "*":
            start_line, start_col = self.line, self.column
            self.advance()
            if self.peek() == "=":
                self.advance()
                return Token(TokenType.MUL_ASSIGN, "*=", start_line, start_col)
            return Token(TokenType.MUL, "*", start_line, start_col)

        if char == "/":
            start_line, start_col = self.line, self.column
            self.advance()
            if self.peek() == "=":
                self.advance()
                return Token(TokenType.DIV_ASSIGN, "/=", start_line, start_col)
            return Token(TokenType.DIV, "/", start_line, start_col)

        if char == "&":
            start_line, start_col = self.line, self.column
            self.advance()
            if self.peek() == "&":
                self.advance()
                return Token(TokenType.AND, "&&", start_line, start_col)
            self.error("Expected '&' to form '&&' operator")

        if char == "|":
            start_line, start_col = self.line, self.column
            self.advance()
            if self.peek() == "|":
                self.advance()
                return Token(TokenType.OR, "||", start_line, start_col)
            self.error("Expected '|' to form '||' operator")

        # Single-char operators/delimiters
        char_tokens = {
            ":": TokenType.COLON,
            "(": TokenType.LPAREN,
            ")": TokenType.RPAREN,
            "{": TokenType.LBRACE,
            "}": TokenType.RBRACE,
            ",": TokenType.COMMA,
            ".": TokenType.DOT,
            ";": TokenType.SEMICOLON,
            "[": TokenType.LBRACKET,
            "]": TokenType.RBRACKET,
            "%": TokenType.PERCENT,
        }

        if char in char_tokens:
            start_line, start_col = self.line, self.column
            self.advance()
            return Token(char_tokens[char], char, start_line, start_col)

        self.error(f"Unexpected character: '{char}'")

    def tokenize(self) -> List[Token]:
        tokens = []
        while True:
            tok = self.next_token()
            tokens.append(tok)
            if tok.type == TokenType.EOF:
                break
        return tokens
