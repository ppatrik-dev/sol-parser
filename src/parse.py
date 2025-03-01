# File: parse.py
# Author: Patrik Prochazka
# Login: xprochp00

import sys
from lark import (
    Lark, LarkError, Transformer,
    UnexpectedToken, UnexpectedCharacters, UnexpectedEOF,
)

def check_arguments():
    help_message = """
    The script (filter), reads the source code in SOL25 from the standard input, 
    checks the lexical, syntactic and static semantic correctness of the code and writes 
    XML representation of the program abstract syntactic tree to the standard output.
    
    usage:  python parse.py [--help]
    """
    
    argc = len(sys.argv)
    
    if argc == 2 and sys.argv[1] == "--help":
        print(help_message)
        sys.exit(0)
    elif argc > 2:
        print("Invalid arguments, use --help for usage information")
        sys.exit(10)
    
try:
    check_arguments()
    input_program = sys.stdin.read()
    
except IOError as e:
    sys.stderr.write(f"IOError: {e}")
    sys.exit(11)
except Exception as e:
    sys.stderr.write(f"Error: {e}")
    sys.exit(11)

grammar = """
start: program

program: class*
class: "class" CID ":" CID "{" method* "}"
method: selector block

selector: ID | ID_COL+

block: "[" block_par* "|" block_stat* "]"
block_par: COL_ID -> param
block_stat: ID ":" "=" expr "." -> assign

expr: expr_base expr_tail
expr_tail: ID -> no_param_sel
        | expr_sel+ -> message
expr_sel: ID_COL expr_base -> param_sel
expr_base: INT -> integer 
        | STR -> string
        | ID -> var_id
        | CID -> class_id
        | block -> block_expr
        | "(" expr ")" -> nested_expr

CID: /[A-Z][a-zA-Z0-9]*/

ID: /[a-z|_][a-zA-Z0-9_]*/
ID_COL: /[a-z|_][a-zA-Z0-9_]*:/
COL_ID: /:[a-z|_][a-zA-Z0-9_]*/

INT: /0|([+-]?[1-9][0-9]*)/
STR: /'([^'\\]|\\[\'\\n])*'/x   # TODO

COMMENT: /"[^"]*"/

%import common.WS
%ignore WS
%ignore COMMENT
"""

parser = Lark(grammar, lexer='contextual', parser='lalr', start='start')

try:
    parse_tree = parser.parse(input_program)
    print(parse_tree.pretty())
    
except UnexpectedCharacters as e:
    sys.stderr.write(f"Lexical Error: {e}")
    sys.exit(21)
    
except (UnexpectedToken, UnexpectedEOF) as e:
    sys.stderr.write(f"Syntactic Error: {e}")
    sys.exit(22)
    
except LarkError as e:
    sys.stderr.write(f"Lark Error: {e}")
    sys.exit(99)
    