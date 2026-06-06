from dataclasses import dataclass
from typing import List, Optional, Any, Union

@dataclass
class ASTNode:
    pass

@dataclass
class Program(ASTNode):
    statements: List[ASTNode]

@dataclass
class LiteralNode(ASTNode):
    value: Any  # Can be int, float, str, bool, None

@dataclass
class IdentifierNode(ASTNode):
    name: str

@dataclass
class LetNode(ASTNode):
    """Immutable variable declaration: let x = val"""
    name: str
    value: ASTNode

@dataclass
class AssignNode(ASTNode):
    """Mutable/Dynamic assignment or declaration: x = val, or with type x: Type = val"""
    name: str
    value: ASTNode
    type_ann: Optional[str] = None  # Static type annotation if present

@dataclass
class BinaryOpNode(ASTNode):
    left: ASTNode
    op: str
    right: ASTNode

@dataclass
class PrintNode(ASTNode):
    value: ASTNode

@dataclass
class BlockNode(ASTNode):
    statements: List[ASTNode]

@dataclass
class FunctionDeclNode(ASTNode):
    name: str
    params: List[tuple[str, Optional[str]]]  # List of (param_name, param_type)
    return_type: Optional[str]
    body: BlockNode

@dataclass
class CallNode(ASTNode):
    func: ASTNode  # Usually IdentifierNode
    args: List[ASTNode]

@dataclass
class IfNode(ASTNode):
    condition: ASTNode
    then_branch: BlockNode
    else_branch: Optional[Union[BlockNode, 'IfNode']] = None

@dataclass
class MatchNode(ASTNode):
    value: ASTNode
    cases: List[tuple[ASTNode, BlockNode]]  # List of (pattern, body)

@dataclass
class ReturnNode(ASTNode):
    value: Optional[ASTNode] = None

@dataclass
class UnaryOpNode(ASTNode):
    op: str
    right: ASTNode
