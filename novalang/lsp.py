import sys
import json
import re
import traceback
from typing import List, Dict, Optional, Set
from novalang.lexer import Lexer
from novalang.parser import Parser

def write_message(msg: dict):
    body = json.dumps(msg)
    sys.stdout.write(f"Content-Length: {len(body)}\r\n\r\n{body}")
    sys.stdout.flush()

def log(msg: str):
    sys.stderr.write(f"[LSP Log] {msg}\n")
    sys.stderr.flush()

# In-memory document storage
documents: Dict[str, str] = {}

def handle_request(req: dict):
    method = req.get("method")
    params = req.get("params", {})
    req_id = req.get("id")
    
    if method == "initialize":
        response = {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "capabilities": {
                    "textDocumentSync": 1,  # Full sync
                    "hoverProvider": True,
                    "completionProvider": {
                        "resolveProvider": False,
                        "triggerCharacters": ["."]
                    }
                }
            }
        }
        write_message(response)
        
    elif method == "initialized":
        pass
        
    elif method in ("textDocument/didOpen", "textDocument/didChange", "textDocument/didSave"):
        doc = params.get("textDocument", {})
        uri = doc.get("uri")
        text = doc.get("text")
        
        if "contentChanges" in params:
            text = params["contentChanges"][0].get("text")
            
        if uri and text is not None:
            publish_diagnostics(uri, text)
            
    elif method == "textDocument/hover":
        doc = params.get("textDocument", {})
        uri = doc.get("uri")
        pos = params.get("position", {})
        line = pos.get("line", 0)
        char = pos.get("character", 0)
        
        hover_result = get_hover_result(uri, line, char)
        response = {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": hover_result
        }
        write_message(response)
        
    elif method == "textDocument/completion":
        response = {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": get_completions()
        }
        write_message(response)
        
    elif req_id is not None:
        response = {
            "jsonrpc": "2.0",
            "id": req_id,
            "error": {
                "code": -32601,
                "message": f"Method not found: {method}"
            }
        }
        write_message(response)

def publish_diagnostics(uri: str, text: str):
    documents[uri] = text
    diagnostics = []
    
    try:
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        parser.parse()
        
        if parser.errors:
            for err in parser.errors:
                diag = parse_error_string(err)
                if diag:
                    diagnostics.append(diag)
    except SyntaxError as e:
        diag = parse_error_string(str(e))
        if diag:
            diagnostics.append(diag)
    except Exception as e:
        diagnostics.append({
            "range": {
                "start": {"line": 0, "character": 0},
                "end": {"line": 0, "character": 100}
            },
            "severity": 1,
            "message": str(e)
        })
        
    notification = {
        "jsonrpc": "2.0",
        "method": "textDocument/publishDiagnostics",
        "params": {
            "uri": uri,
            "diagnostics": diagnostics
        }
    }
    write_message(notification)

def parse_error_string(err_str: str) -> Optional[dict]:
    pat = re.compile(r".*Error at line (\d+), column (\d+): (.*)")
    m = pat.match(err_str)
    if m:
        line_str, col_str, msg = m.groups()
        line = max(0, int(line_str) - 1)
        col = max(0, int(col_str) - 1)
        return {
            "range": {
                "start": {"line": line, "character": col},
                "end": {"line": line, "character": col + 5}
            },
            "severity": 1,
            "message": err_str
        }
    return None

def get_hover_result(uri: str, line: int, char: int) -> Optional[dict]:
    text = documents.get(uri, "")
    lines = text.splitlines()
    if line >= len(lines):
        return None
        
    line_text = lines[line]
    word = get_word_at(line_text, char)
    if not word:
        return None
        
    docs = {
        "print": "**print(value)**\n\nPrints the string representation of a value to standard output.",
        "str": "**str(value)**\n\nConverts a value to its string representation.",
        "int": "**int(value)**\n\nConverts a string or float value to an integer.",
        "float": "**float(value)**\n\nConverts a string or integer value to a float.",
        "len": "**len(value)**\n\nReturns the length of a string value.",
        "let": "**let** keyword\n\nBinds a read-only (immutable) constant to a value in the current scope.",
        "fun": "**fun** keyword\n\nDeclares a reusable named function with static parameter types and return type.",
        "match": "**match** keyword\n\nIntroduces structural pattern matching block.",
        "class": "**class** keyword\n\nDeclares a custom object class.",
        "extends": "**extends** keyword\n\nSpecifies a parent class for inheritance.",
        "interface": "**interface** keyword\n\nDeclares a behavioral interface contract.",
        "Int": "Built-in integer type.",
        "Float": "Built-in double-precision floating-point type.",
        "Bool": "Built-in boolean type.",
        "String": "Built-in string type."
    }
    
    if word in docs:
        return {
            "contents": {
                "kind": "markdown",
                "value": docs[word]
            }
        }
    return None

def get_word_at(text: str, index: int) -> str:
    if index >= len(text):
        return ""
    start = index
    while start > 0 and (text[start-1].isalnum() or text[start-1] == '_'):
        start -= 1
    end = index
    while end < len(text) and (text[end].isalnum() or text[end] == '_'):
        end += 1
    return text[start:end]

def get_completions() -> List[dict]:
    keywords = ["let", "fun", "class", "interface", "match", "if", "else", "true", "false", "return", "import", "package", "extends", "self", "try", "catch", "while", "for", "in", "break", "continue", "struct", "enum", "null"]
    builtins = ["print", "str", "int", "float", "len"]
    types = ["Int", "Float", "Bool", "String"]
    
    items = []
    for kw in keywords:
        items.append({
            "label": kw,
            "kind": 14,
            "detail": "NovaLang Keyword"
        })
    for bi in builtins:
        items.append({
            "label": bi,
            "kind": 3,
            "detail": "Built-in Function"
        })
    for t in types:
        items.append({
            "label": t,
            "kind": 7,
            "detail": "Built-in Type"
        })
    return items

def start_lsp_server():
    log("NovaLang LSP Server started")
    stdin_buffer = ""
    while True:
        try:
            line = sys.stdin.readline()
            if not line:
                break
            stdin_buffer += line
            
            if "Content-Length:" in stdin_buffer and "\r\n\r\n" in stdin_buffer:
                parts = stdin_buffer.split("\r\n\r\n", 1)
                header_part = parts[0]
                remaining = parts[1]
                
                m = re.search(r"Content-Length:\s*(\d+)", header_part)
                if m:
                    content_length = int(m.group(1))
                    
                    while len(remaining) < content_length:
                        chunk = sys.stdin.read(content_length - len(remaining))
                        if not chunk:
                            break
                        remaining += chunk
                        
                    body = remaining[:content_length]
                    stdin_buffer = remaining[content_length:]
                    
                    try:
                        req = json.loads(body)
                        handle_request(req)
                    except Exception as parse_ex:
                        log(f"Error parsing request: {parse_ex}")
                else:
                    stdin_buffer = remaining
        except KeyboardInterrupt:
            break
        except Exception as e:
            log(f"LSP Global Loop Error: {e}\n{traceback.format_exc()}")
            break
