# File: parse.py
# Author: Patrik Prochazka
# Login: xprochp00

import sys, re
from lark import (
    Lark, LarkError, Transformer,
    UnexpectedToken, UnexpectedCharacters, UnexpectedEOF,
)
import xml.etree.ElementTree as ET
import xml.dom.minidom

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
        return {"block": {"parameters": parameters, "assignments": args[len(parameters):]}}
    
    def param(self, args):
        name = (args[0].value)[1:]
        return {"param": name}    
        
    def assign(self, args):
        var = args[0].value
        return {"type": "assign", "var": var} | args[1]
    
    def expr(self, args):
        return {"expr": {"object": args[0], "message": args[1]}}
    
    def no_param_sel(self, args):
        name = args[0].value
        return {"type": "no_param_sel", "name": name}
    
    def expr_tail(self, args):
        return args
    
    def param_sel(self, args):
        name = args[0].value
        return {"type": "param_sel", "name": name, "arg": args[1]}
    
    def integer(self, args):
        value = args[0].value
        return {"type": "integer", "value": value}
    
    def string(self, args):
        value = args[0].value
        return {"type": "string", "value": value}
    
    def var_id(self, args):
        name = args[0].value
        return {"type": "var", "name": name}
    
    def class_id(self, args):
        name = args[0].value
        return {"type": "class", "name": name}
    
    def block_expr(self, args):
        return ({"type": "block_expr"} | args[0])
    
    def nested_expr(self, args):
        return ({"type": "nested_expr"} | args[0])

# Function searching for first program comment
def get_first_comment(source_code):
    match = re.search(r'\"(.*?)\"', source_code)
    comment = match.group(0)
    
    if comment != None:
        return comment[1:-1]
    else:
        return None

# Function formating final XML output using 'dom.minidom' module
def format_xml(root_elem: ET.Element):
    xml_string = ET.tostring(root_elem, encoding="utf-8")
    parsed_dom = xml.dom.minidom.parseString(xml_string)
    xml_output = parsed_dom.toprettyxml(indent="  ", encoding="UTF-8").decode("utf-8")
    
    return xml_output.strip()

# Function generating final XML representation of program AST
def generate_xml(ast: dict):
    global comment
    
    program_elem = ET.Element("program", language="SOL25", description=comment)
    
    classes = ast["program"]
    for cls in classes:
        generate_class(program_elem, cls)
    
    return program_elem

# Function generating class elements
def generate_class(parent_elem: ET.Element, class_node: dict):
    class_elem = ET.SubElement(parent_elem, class_node["type"], name=class_node["name"], parent=class_node["parent"])
    
    methods = class_node["body"]
    for mth in methods:
        generate_method(class_elem, mth)

# Function generating method elements
def generate_method(parent_elem: ET.Element, method_node: dict):
    method_elem = ET.SubElement(parent_elem, method_node["type"], selector=method_node["selector"])
    
    generate_block(method_elem, method_node["block"])

# Function generating block elements  
def generate_block(parent_elem: ET.Element, block_node: dict):
    parameters = block_node["parameters"]
    arity = len(parameters)
    
    block_elem = ET.SubElement(parent_elem, "block", arity=str(arity))
    
    for i in range(0, arity):
        generate_parameter(block_elem, parameters[i], i+1)
    
    assignments = block_node["assignments"]
    for i in range(0, len(assignments)):
        generate_assignment(block_elem, assignments[i], i+1)
        
# Function generating parameter elements
def generate_parameter(parent_elem: ET.Element, name: str, order: int):
    ET.SubElement(parent_elem, "parameter", name=name, order=str(order))

# Function generating assignment elements
def generate_assignment(parent_elem: ET.Element, assign_node, order: int):
    assign_elem = ET.SubElement(parent_elem, "assign", order=str(order))
    
    lvalue_elem = ET.SubElement(assign_elem, "var", name=assign_node["var"])
    rvalue_elem = ET.SubElement(assign_elem, "expr")
    generate_expression(rvalue_elem, assign_node["expr"])

# Function generating expression elements
def generate_expression(parent_elem: ET.Element, expression_node: dict):    
    selector = ""
    messages = expression_node["message"]
    for msg in messages:
        selector += msg["name"]
    
    selector_elem = ET.SubElement(parent_elem, "send", selector=selector)
    expr_elem = ET.SubElement(selector_elem, "expr")
    
    object_node = expression_node["object"]
    message_node = expression_node["message"]

    nested_expr = object_node.get("expr")
    if nested_expr == None:
        ET.SubElement(expr_elem, object_node["type"], name=object_node["name"])
    else:
        generate_expression(expr_elem, nested_expr)
    
    if message_node[0]["type"] == "param_sel":
        for i in range(0, len(message_node)):
            generate_argument(selector_elem, message_node[i]["arg"], i+1)

# Function generating argument elements   
def generate_argument(parent_elem: ET.Element, arg_node: dict, order: int):
    arg_elem = ET.SubElement(parent_elem, "arg", order=str(order))
    expr_elem = ET.SubElement(arg_elem, "expr")
    
    arg_type = arg_node["type"]

    if arg_type == "integer":
        ET.SubElement(expr_elem, "literal", attrib={"class": "Integer", "value": arg_node["value"]})

    elif arg_type == "string":
        ET.SubElement(expr_elem, "literal", attrib={"class": "String", "value": arg_node["value"]})
    
    elif arg_type == "var":
        ET.SubElement(expr_elem, "var", name=arg_node["name"])
    
    elif arg_type == "nested_expr":
        generate_expression(expr_elem, arg_node["expr"])
        
    elif arg_type == "block_expr":
        generate_block(expr_elem, arg_node["block"])
    
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
    comment = get_first_comment(input_program)

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
expr_tail: no_param_sel
        | param_sel+
no_param_sel: ID
param_sel: ID_COL expr_base
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

# Generating and printing final XML
xml_root = generate_xml(ast)
print(format_xml(xml_root))
