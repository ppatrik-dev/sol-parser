# IPP Project 1 - SOL25 Parser

## 📌 Overview

This project includes the `parse.py` script, which serves as a **parser and XML generator** for the **SOL25** programming language. It reads a program written in SOL25 from standard input, parses it, and outputs an **Abstract Syntax Tree (AST)** in **XML format** to standard output.

When run with `-h` or `--help`, the script displays a brief help message describing its functionality.

---

## 🔍 Functionality

### 🧠 Lexical & Syntactic Analysis

- Utilizes the [`Lark`](https://github.com/lark-parser/lark) parsing library.
- Grammar is written in **EBNF**.
- Parsing is performed via Lark’s `parse()` method.
- Lexical errors are detected using regular expressions.
- Designed to avoid unnecessary recursive nesting.

### 🌲 Abstract Syntax Tree (AST)

- The parse tree from `Lark` is transformed into a simplified **AST** using a custom `Transformer` class.
- The AST structure resembles a **JSON-like tree** for easier processing.

### 💡 Semantic Analysis

Before generating XML, the script performs semantic checks:

- **Class message validation** (`check_class_message`)
  - Ensures, for example, that methods like `read` are called on appropriate subclasses (e.g., `String`)
- **Cyclic inheritance detection** (`check_cyclic_inheritance`)
- Verification using internal lists for:
  - Reserved keywords
  - Built-in classes
  - Global objects
  - Pseudovariables

---

## </> XML Generation

- Handled using Python’s [`xml.etree.ElementTree`](https://docs.python.org/3/library/xml.etree.elementtree.html).
- Main functions:
  - `generate_xml`: Creates the root `<program>` element
  - `generate_class`: Recursively builds class and method structures
  - `format_xml`: Ensures proper indentation, XML declaration header and UTF-8 encoding
- XML output is structured from **top to bottom**

---

## 🧾 Usage

```bash
python3 parse.py < input.sol > output.xml
