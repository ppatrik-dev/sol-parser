# File: parse.py
# Author: Patrik Prochazka
# Login: xprochp00

import sys
from lark import (
    Lark, LarkError, Transformer,
    UnexpectedToken, UnexpectedCharacters, UnexpectedEOF,
)

# Creating AST trasformer using base class Transformer from Lark.
# Defining transform functions for grammar rules to transform
# Lark parse tree to AST representation similar to JSON
class AST_Transformer(Transformer):
    def program(self, args):
        return {"program": args}
    
    def class_def(self, args):
        name = args[0].value
        parent = args[1].value
        body = args[2:]
        return {"type": "class", "name": name, "parent": parent, "body": body}
        
    def method(self, args):
        return ({"type": "method"} | args[0] | args[1])
    
    def selector(self, args):
        name = ""
        for arg in args:
            name += arg.value
        return {"selector": name}
        
    def block(self, args):
        parameters = []
        for dct in args:
            param = dct.get("param")
            if param is not None:
                parameters.append(param)
        return {"block": {"parameters": parameters, "statements": args[len(parameters):]}}
    
    def param(self, args):
        name = args[0].value
        return {"param": name}    
        
    def assign(self, args):
        lvalue = args[0].value
        rvalue = args[1]
        return {"type": "assign", "lvalue": lvalue, "rvalue": rvalue}
    
    def expr(self, args):
        return ({"type": "expr"} | args[0] | args[1])
    
    def no_param_sel(self, args):
        name = args[0].value
        return {"type": "no_param_sel", "name": name}
    
    def message(self, args):
        return {"message": args}
    
    def param_sel(self, args):
        name = args[0].value
        return {"type": "param_sel", "name": name, "param": args[1]}
    
    def integer(self, args):
        value = args[0].value
        return {"type": "integer", "value": value}
    
    def string(self, args):
        value = args[0].value
        return {"type": "string", "value": value}
    
    def obj_id(self, args):
        name = args[0].value
        return {"type": "obj", "name": name}
    
    def class_id(self, args):
        name = args[0].value
        return {"type": "class", "name": name}
    
    def block_expr(self, args):
        return ({"type": "block_expr"} | args[0])
    
    def nested_expr(self, args):
        return {"nested_expr": args[0]}

# Function checking program arguments and printing help message
def check_arguments():
    help_message = """
    The script (filter), reads the source code in SOL25 from the standard input, 
    checks the lexical, syntactic and static semantic correctness of the code and writes 
    XML representation of the program abstract syntactic tree to the standard output.
    
    usage:  python parse.py [--help]
    """
    
    argc = len(sys.argv)
    
    if (argc == 2) and (sys.argv[1] == "--help" or sys.argv[1] == "-h"):
        sys.stdout.write(help_message)
        sys.exit(0)
    elif argc > 1:
        sys.stderr.write("Invalid arguments, use --help for usage information")
        sys.exit(10)

try:
    check_arguments()
    input_program = sys.stdin.read()

# Handle IO error while reading input
except IOError as e:
    sys.stderr.write(f"IOError: {e}")
    sys.exit(11)

# Handle other exceptions
except Exception as e:
    sys.stderr.write(f"Error: {e}")
    sys.exit(11)

# Define parsing grammar for Lark parser
grammar = r"""
program: class_def*
class_def: "class" CID ":" CID "{" method* "}"
method: selector block

selector: ID | ID_COL+

block: "[" block_par* "|" block_stat* "]"
block_par: COL_ID -> param
block_stat: ID ":=" expr "." -> assign

expr: expr_base expr_tail
expr_tail: ID -> no_param_sel
        | expr_sel+ -> message
expr_sel: ID_COL expr_base -> param_sel
expr_base: INT -> integer 
        | STR -> string
        | ID -> obj_id
        | CID -> class_id
        | block -> block_expr
        | "(" expr ")" -> nested_expr

CID: /[A-Z][a-zA-Z0-9]*/

ID: /[a-z|_][a-zA-Z0-9_]*/
ID_COL: /[a-z|_][a-zA-Z0-9_]*:/
COL_ID: /:[a-z|_][a-zA-Z0-9_]*/

INT: /0|([+-]?[1-9][0-9]*)/
STR: /'([^'\\]|\\['\\n])*'/

COMMENT: /"[^"]*"/

%import common.WS
%ignore WS
%ignore COMMENT
"""

# Create Lark parser, using 'contextual' lexer and 'lalr' parser starting from rule 'program'
parser = Lark(grammar, lexer='contextual', parser='lalr', start='program')

try:
    parse_tree = parser.parse(input_program)

# Handle Lexical errors with exit code 21
except UnexpectedCharacters as e:
    sys.stderr.write(f"Lexical Error: {e}")
    sys.exit(21)

# Handle Syntactic errors with exit code 22
except (UnexpectedToken, UnexpectedEOF) as e:
    sys.stderr.write(f"Syntactic Error: {e}")
    sys.exit(22)

# Handle other Lark errors with exit code 99    
except LarkError as e:
    sys.stderr.write(f"Lark Error: {e}")
    sys.exit(99)

# Using custom definied transformer for AST
transformer = AST_Transformer()
ast = transformer.transform(parse_tree)
print(ast)