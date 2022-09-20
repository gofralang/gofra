# Gofra Programming Language

### **_Stack - Based programming language "written in Python"_**

## Features

- Interpretate code (Will removed with isolated VM/Bytecode interpretation).
- Generate graph for the code (`.dot` graphviz)(Maybe removed later because redundancy).
- Bytecode (Compile, Interpretate) [WIP] [Gorfa Bytecode Virtual Machine in C++](https://github.com/gofralang/vm)

## Language features

- Stack implementation (push, pop)
- Conditional IFs ([bool_from_stack] if [code] else [code] end).
- WHILE loops (while [expression] do [code] end)
- Bytearray Memory (mbwrite, mbread, mbshowc, mbptr etc...)
- Characters, Strings.
- Basic I/O.

## Simple example

```
35 // Push 35 in the stack.
5 // Push 5 in the stack.
+ // Pop both 35 and 5, and push their sum in the stack.
show // Pop value from the stack and show it on the screen.
```

## Hello World example

```
"Hello, World!" mshowc // Show string "Hello, World!" on the screen.
```

## Add syntax for your own PyCharm (or JetBrains IDE): [JB Docs](https://www.jetbrains.com/help/pycharm/creating-and-registering-file-types.html#create-new-file-type)

## Documentation: `DOCUMENTATION.MD`, Examples: `./examples/README.MD`.
