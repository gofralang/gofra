# Gofra Programming Language

Gofra is an native stack based programming language.

Language follows reverse polish notation (examples can be found below) \
**Language is in development stage and mostly made for fun and research so don't expect a lot and try to test or implement your own idea**

## Table of content

- [Hello world example](#hello-world-example)
- [Compatibility](#compatibility)
- [Features](#features)
- [Installation](#installation)
- [Examples](#examples)
- [Language overview](#language-overview)
- [Command Line Interface](#command-line-interface-cli)
- [Milestones and planned features](#milestones-and-planned-features)

---

### Hello world example
###### (For now, language is mostly bare-metal so in this example there is raw `sc_write` syscall and file descriptor usage)
```
include "std.gof"
func void main
    FD_STD_OUT "Hello, World!\n" sc_write drop
end
```


### Compatibility
Language currently have codegenS only for:
- AARCH64 MacOS (Darwin)
- x86_64 Linux

### Features
- Native (codegen assembly)
- Type safety (Validates stack usage and tries to infer types so you wont mess up)
- Mostly self explanation errors (Tries to help you and correct your intentions)
- Optimizer (DCE, CF, Helps optimize resulting assembly for codegen so your default usage will not be overwhelmed by language)
- FFI with `global`/`extern` function modifers (there is CLI flags to emit an library/object file)
- Simple CLI for working with language (simple toolkit)


### Installation
- Clone this repo
- Install latest Python version
- Navigate to root directory 
- Run `python -m gofra --help` (`python` depends on your installation of Python)

### Examples
Examples may be found inside `./examples` directory

### Language overview
As language is stack based so your basic action is to *put something on a stack*, like `2 2` will push 2 and then another 2 on stack so stack underneath will look like [2, 2]

If you want to operate on that numbers you may do something like `3 2 +` which is same as `3 + 2` in other language or default math. Underneath this will mean: push 3 on stack -> push 2 on stack -> take 2 elements from stack -> sum them -> push result back. Stack after that will become [5]

Conditionals is also a bit controversial:
```
1 2 == if
    ...
end
```
which is same as other languages:
```
if (1 == 2){
    ...
}
```
(You can follow previous math example for checking stack manipulation)

For writing a bit more complex programs you may want to use macros and includes:
Macros is an collection of tokens (like functions in other languages) but does not have an object-like system they just an way to not write same logic (for now)
So, this code:
```
macro multiply_by_2
    2 *
end

4 multiply_by_2
```
at compilation stage will be converted into simple `4 2 *` (tokens expanded)
For importing some file (same as macros system but for files) you can use `import "file.gof"`



### Milestones and planned features

- Standard library with not only syscall mapping
- Stability improvements
- Support for x86_64 Windows
- More examples