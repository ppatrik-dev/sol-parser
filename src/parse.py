# File: parse.py
# Author: Patrik Prochazka
# Login: xprochp00

import sys
from lark import Lark, LarkError, UnexpectedToken, UnexpectedCharacters, UnexpectedInput

try:
    input_program = sys.stdin.read()
    
except IOError as e:
    sys.stderr.write(f"IOError: {e}")
    sys.exit(11)
except Exception as e:
    sys.stderr.write(f"Error: {e}")
    sys.exit(11)

grammar = """
start: program

program: class program |     
class: "class" CID ":" CID "{" method "}"
method: selector block method |

selector: ID | ID_COL selector_tail
selector_tail: ID_COL selector_tail |

block: "[" block_par "|" block_stat "]"
block_par: COL_ID block_par | 
block_stat: ID ":" "=" expr "." block_stat | 

expr: expr_base expr_tail
expr_tail: ID
expr_tail: expr_sel
expr_sel: ID_COL expr_base expr_sel |
expr_base: INT | STR | ID | CID
expr_base: block
expr_base: "(" expr ")"

CID: /[A-Z][a-zA-Z0-9]*/

ID: /[a-z|_][a-zA-Z0-9_]*/
ID_COL: /[a-z|_][a-zA-Z0-9_]*:/
COL_ID: /:[a-z|_][a-zA-Z0-9_]*/

INT: /[+|-]*[1-9][0-9]*/
STR:/'[^'^\]*'/

COMMENT: /"[^"]*"/

%import common.WS
%ignore WS
%ignore COMMENT

"""

parser = Lark(grammar)

try:
    tree = parser.parse(input_program)
    print(tree.pretty())
    
except UnexpectedCharacters as e:
    sys.stderr.write(f"Lexical error: {e}")
    sys.exit(21)
    
except UnexpectedToken as e:
    sys.stderr.write(f"Syntactic error: {e}")
    sys.exit(22)
    
except LarkError as e:
    sys.stderr.write(f"Lark Error: {e}")
    sys.exit(99)
    
    
