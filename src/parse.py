# File: parse.py
# Info: IPP Project 1
# Author: Patrik Prochazka
# Login: xprochp00

import sys, re
from lark import (
    Lark, LarkError, Transformer,
    UnexpectedToken, UnexpectedCharacters, UnexpectedEOF,
)
import xml.etree.ElementTree as ET

# Constant error codes values
SUCCESS_EXIT            =   0
ARGUMENTS_ERROR         =  10
INPUT_ERROR             =  11
LEXICAL_ERROR           =  21
SYNTACTIC_ERROR         =  22
NO_MAIN_OR_RUN_ERROR    =  31
NO_DEFINITION_ERROR     =  32
BAD_ARRITY_ERROR        =  33
COLLISION_ERROR         =  34
OTHER_SEMANTIC_ERROR    =  35
INTERNAL_ERROR          =  99

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
        block_parameters = []
        for dct in args:
            param = dct.get("param")
            if param is not None:
                block_parameters.append(param)
        return {"block": {"block_parameters": block_parameters, "assignments": args[len(block_parameters):]}}
    
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
        value = args[0].value[1:-1]
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

# List of keywords
keywords = ["class", "self", "super", "nil", "true", "false"]

# List of builtin classes
builtins_classes = ["Object", "Nil", "True", "False", "Integer", "String", "Block"]

# List of class methods
class_methods = ["new", "from:"]

# List of global objects
global_objects = ["nil", "true", "false"]

# List of pseudo variables
pseudo_variables = ["self", "super"]

# List of user classes
user_classes = {}

# Function checking for method redefinition
def check_method_redefined(selector: str, methods: list[str]):
    if selector in methods:
        sys.stderr.write(f"Semantic Error: Method '{selector}' redefined\n")
        sys.exit(OTHER_SEMANTIC_ERROR)

# Function checking for class redefinition
def check_class_redefined(class_id: str):
    if (class_id in builtins_classes) or (class_id in user_classes):
        sys.stderr.write(f"Semantic Error: Class '{class_id}' redefined\n")
        sys.exit(OTHER_SEMANTIC_ERROR)

# Function checking for class definition
def check_class_defined(class_id: str):    
    if (class_id not in builtins_classes) and (class_id not in user_classes) :
        sys.stderr.write(f"Semantic Error: Class '{class_id}' not defined\n")
        sys.exit(NO_DEFINITION_ERROR)

# Function checking for cyclic class inheritance
def check_cyclic_inheritance(class_id: str, parent_id: str):
    child = class_id
    while child:
        parent = user_classes[child]
        
        if parent in builtins_classes:
            parent = None
        
        elif parent == class_id:
            sys.stderr.write(f"Semantic Error: Cyclic inheritance between classes '{class_id}' and '{parent_id}'\n")
            sys.exit(OTHER_SEMANTIC_ERROR)
            
        child = parent
    
# Function checking if class is subclass of base class
def is_subclass(class_id: str, base_class_id: str) -> bool:
    if class_id == base_class_id:
        return True
    
    if base_class_id == "Object":
        return True
    
    if class_id in builtins_classes:
        return base_class_id == "Object"
    
    child = class_id
    while True:
        parent = user_classes[child]
        
        if parent in builtins_classes:
            if parent == base_class_id:
                return True
            else:
                return False
        
        child = parent
        
# Function checking for class method message
def check_class_message(class_id: str, selector: str):
    if selector == "read":
        if (not is_subclass(class_id, "String")):
            sys.stderr.write(f"Semantic Error: Class '{class_id}' have no class method '{selector}'\n")
            sys.exit(NO_DEFINITION_ERROR)
    
    elif selector not in class_methods:
        sys.stderr.write(f"Semantic Error: Class '{class_id}' have no class method '{selector}'\n")
        sys.exit(NO_DEFINITION_ERROR)
        
# Function checking for Main class definition
def check_main_class_defined():
    if "Main" not in user_classes:
        sys.stderr.write("Semantic Error: Main class not defined\n")
        sys.exit(NO_MAIN_OR_RUN_ERROR)

# Function checking for Main run method definition
def check_run_method_defined(methods: list[str]):
    if "run" not in methods:
        sys.stderr.write("Semantic Error: Main run method not defined\n")
        sys.exit(NO_MAIN_OR_RUN_ERROR)

# Function checking for no block_parameters in Main run method
def check_run_no_parameters(block_parameters: list[str]):
    if block_parameters:
        sys.stderr.write("Semantic Error: Main run method with specified block_parameters\n")
        sys.exit(BAD_ARRITY_ERROR)

# Function for checking for block_parameters count equal to method arity
def check_parameters_arity(selector: str, block_parameters: list[str]):
    if selector.count(":") != len(block_parameters):
        sys.stderr.write(f"Semantic Error: Invalid block parameters arity in method '{selector}'\n")
        sys.exit(BAD_ARRITY_ERROR)
        
# Function checking for block parameter collision
def check_parameters_collide(block_parameters: list[str]):
    if len(block_parameters) != len(set(block_parameters)):
        sys.stderr.write("Semantic Error: Block paramaters with same identifier\n")
        sys.exit(OTHER_SEMANTIC_ERROR)
        
# Function checking for block parameter assignment
def check_parameter_assign(var_id: str, block_parameters: list[str]):
    if var_id in block_parameters:
        sys.stderr.write(f"Semantic Error: Assignment to block parameter\n")
        sys.exit(COLLISION_ERROR)

# Function checking for indetifier definition
def check_variable_definied(var_id: str, parameters: list[str], variables: list[str]):
    if (var_id not in parameters) and (var_id not in variables) and (var_id not in pseudo_variables):
        sys.stderr.write(f"Semantic Error: Indetifier '{var_id}' not defined\n")
        sys.exit(NO_DEFINITION_ERROR)

# Function checking for keyword used as identifier
def check_keyword_used(id: str):
    if id in keywords:
        sys.stderr.write(f"Syntactic Error: Keyword '{id}' used as indetifier\n")
        sys.exit(SYNTACTIC_ERROR)

# Function searching for first program comment
def get_first_comment(source_code) -> str | None:
    match = re.search(r'\"(.*?)\"', source_code, re.DOTALL)
    
    if match is None:
        return None
    else:
        return match.group(0)[1:-1]

# Function formating final XML output using 'dom.minidom' module
def format_xml(root_elem: ET.Element) -> str:
    ET.indent(root_elem)
    xml_string = ET.tostring(root_elem, encoding="UTF-8", xml_declaration=True).decode("UTF-8")
    
    return xml_string

# Function generating final XML representation of program AST
def generate_xml(ast: dict, cmt: str) -> ET.Element:
    if cmt == None:
        program_elem = ET.Element("program", language="SOL25")
    else:
        program_elem = ET.Element("program", language="SOL25", description=cmt)
        
    classes = ast["program"]
    for cls in classes:
        check_class_redefined(cls["name"])
        user_classes[cls["name"]] = cls["parent"]
    
    for cls in classes:
        generate_class(program_elem, cls)
        
    check_main_class_defined()
    
    return program_elem

# Function generating class elements
def generate_class(parent_elem: ET.Element, class_node: dict):
    instance_methods = []
    
    check_class_defined(class_node["parent"])
    check_cyclic_inheritance(class_node["name"], class_node["parent"])
    
    class_elem = ET.SubElement(parent_elem, class_node["type"], name=class_node["name"], parent=class_node["parent"])
        
    methods = class_node["body"]
    for mth in methods:
        check_method_redefined(mth["selector"], instance_methods)
        generate_method(class_elem, mth)
        instance_methods.append(mth["selector"])
        
    if class_node["name"] == "Main":
        check_run_method_defined(instance_methods)

# Function generating method elements
def generate_method(parent_elem: ET.Element, method_node: dict):
    check_keyword_used(method_node["selector"])
    
    method_elem = ET.SubElement(parent_elem, method_node["type"], selector=method_node["selector"])
    
    if parent_elem.attrib["name"] == "Main":
        if method_node["selector"] == "run":
            check_run_no_parameters(method_node["block"]["block_parameters"])
            
    check_parameters_arity(method_node["selector"], method_node["block"]["block_parameters"])
    
    generate_block(method_elem, method_node["block"])

# Function generating block elements  
def generate_block(parent_elem: ET.Element, block_node: dict):
    block_parameters = block_node["block_parameters"]
    block_variables = []
    
    arity = len(block_parameters)
    block_elem = ET.SubElement(parent_elem, "block", arity=str(arity))
    
    check_parameters_collide(block_parameters)
    
    for i in range(0, arity):
        generate_parameter(block_elem, block_parameters[i], i+1)
    
    assignments = block_node["assignments"]
    for i in range(0, len(assignments)):
        check_parameter_assign(assignments[i]["var"], block_parameters)

        generate_assignment(block_elem, assignments[i], i+1, block_parameters, block_variables)
        
# Function generating parameter elements
def generate_parameter(parent_elem: ET.Element, name: str, order: int):
    check_keyword_used(name)
    
    ET.SubElement(parent_elem, "parameter", name=name, order=str(order))

# Function generating assignment elements
def generate_assignment(parent_elem: ET.Element, assign_node, order: int, parameters: list[str], variables: list[str]):
    assign_elem = ET.SubElement(parent_elem, "assign", order=str(order))
    
    var_id = assign_node["var"]
    check_keyword_used(var_id)
    variables.append(var_id)
    
    ET.SubElement(assign_elem, "var", name=var_id)
    generate_expression(assign_elem, assign_node["expr"], parameters, variables)

# Function generating expression elements
def generate_expression(parent_elem: ET.Element, expression_node: dict, parameters: list[str], variables: list[str]):    
    messages = expression_node["message"]
    selector = ""
    for msg in messages:
        selector += msg["name"]
     
    object_node = expression_node["object"]
    message_node = expression_node["message"]
    
    if object_node["type"] == "class":
        check_class_message(object_node["name"], selector)
    
    if selector == "":
        generate_literal(parent_elem, object_node, parameters, variables)
        
    else:
        check_keyword_used(selector)
        
        if parent_elem.tag == "assign":
            expr_elem = ET.SubElement(parent_elem, "expr")
            selector_elem = ET.SubElement(expr_elem, "send", selector=selector)
        else:
            selector_elem = ET.SubElement(parent_elem, "send", selector=selector)
        
        generate_literal(selector_elem, object_node, parameters, variables)        

        if message_node and message_node[0]["type"] == "param_sel":
            for i in range(0, len(message_node)):
                generate_argument(selector_elem, message_node[i]["arg"], i+1, parameters, variables)

# Function generating argument elements   
def generate_argument(parent_elem: ET.Element, arg_node: dict, order: int, parameters: list[str], variables: list[str]):
    arg_elem = ET.SubElement(parent_elem, "arg", order=str(order))
    
    generate_literal(arg_elem, arg_node, parameters, variables)

# Function generating literal element
def generate_literal(parent_elem: ET.Element, node: dict, parameters: list[str], variables: list[str]):
    if parent_elem.tag == "expr":
        expr_elem = parent_elem
    else:
        expr_elem = ET.SubElement(parent_elem, "expr")
    
    node_type = node["type"]
    
    if node_type == "nested_expr":
        generate_expression(expr_elem, node["expr"], parameters, variables)
        
    elif node_type == "block_expr":
        generate_block(expr_elem, node["block"])
        
    elif node_type == "var":
        if node["name"] in global_objects:
            ET.SubElement(expr_elem, "literal", attrib={"class": node["name"].capitalize(), "value": node["name"]})
        else:
            check_variable_definied(node["name"], parameters, variables)
            ET.SubElement(expr_elem, "var", name=node["name"])
        
    elif node_type == "class":
        check_class_defined(node["name"])
        ET.SubElement(expr_elem, "literal", attrib={"class": "class", "value": node["name"]})
        
    elif node_type == "integer":
        ET.SubElement(expr_elem, "literal", attrib={"class": "Integer", "value": node["value"]})

    elif node_type == "string":  
        ET.SubElement(expr_elem, "literal", attrib={"class": "String", "value": node["value"]})
    
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
        sys.exit(SUCCESS_EXIT)
    elif argc > 1:
        sys.stderr.write("Invalid arguments, use --help for usage information\n")
        sys.exit(ARGUMENTS_ERROR)

try:
    check_arguments()
    input_program = sys.stdin.read()

# Handle IO error while reading input
except IOError as e:
    sys.stderr.write(f"IOError: {e}\n")
    sys.exit(INPUT_ERROR)

# Handle other exceptions
except Exception as e:
    sys.stderr.write(f"Error: {e}\n")
    sys.exit(INPUT_ERROR)

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
        | param_sel*
no_param_sel: ID
param_sel: ID_COL expr_base
expr_base: "(" expr ")" -> nested_expr
        | block -> block_expr
        | ID -> var_id
        | CID -> class_id
        | INT -> integer
        | STR -> string

CID: /[A-Z][a-zA-Z0-9]*/

ID: /[a-z|_][a-zA-Z0-9_]*/
ID_COL: /[a-z|_][a-zA-Z0-9_]*:/
COL_ID: /:[a-z|_][a-zA-Z0-9_]*/

INT: /0|([+-]?[1-9][0-9]*)/
STR: /'([^'\\\n]|\\['\\n])*'/

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
    sys.stderr.write(f"Lexical Error: {e}\n")
    sys.exit(LEXICAL_ERROR)

# Handle Syntactic errors with exit code 22
except (UnexpectedToken, UnexpectedEOF) as e:
    sys.stderr.write(f"Syntactic Error: {e}\n")
    sys.exit(SYNTACTIC_ERROR)

# Handle other Lark errors with exit code 99
except LarkError as e:
    sys.stderr.write(f"Lark Error: {e}\n")
    sys.exit(INTERNAL_ERROR)

# Using custom defined transformer for AST
transformer = AST_Transformer()
ast = transformer.transform(parse_tree)

comment = get_first_comment(input_program)

# Generating and printing final XML
xml_root = generate_xml(ast, comment)
print(format_xml(xml_root))
