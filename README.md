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
###### (For now, language is mostly bare-metal so in this example there is raw `write` syscall and file descriptor usage)
```
include "std.gof"
FD_STD_OUT "Hello, World!\n" write
```


### Compatibility
Language currently have codegen only for MacOS ARM64

### Features
- Native (codegen assembly for ARM64)
- Type safe (at least somehow, validates stack usage and tries to infer types so you wont mess up)
- Mostly self explanation errors (Tries to help you and correct your intentions)
- Optimizer (Helps optimize resulting assembly for codegen so your default usage will not be overwhelmed by language)
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


### Command Line Interface (CLI)
After installation, your way to call `python -m gofra` for this block will be folded into just `gofra`!

For getting help with CLI just use `gofra --help`

CLI accepts single file name with Gofra source code
And then accepts action (for now, there is only `compile` action (`-c`, `--compile`))

So task for compiling given file is: `gofra ./path_to_your_file -c`

By default toolkit will left cache in `./.build` directory but you may redefine that behavior via `--delete-cache` (`--dc`) and `--cache-dir` (`--cd`)

There is some system that may be disable via `--no-typecheck` (`-nt`) and `--no-optimizations` (`-no`) for current development process they can be disable

For debugging and testing you have flags:
- `--execute` (`-e`) for running after compilation and do not have scripts
- `--fall-into-debugger` (`-dbg`) will fall into `lldb` after run

For some import management you may want to add some search directories via `--include-search-dir` (`-isd`) for example `gofra ./src.gof -c -isd ./my_path_for_search/ -isd ./another/path`

### Milestones and planned features

- Memory management support
- Function calls and hooking up with native libraries (.dylib, .dll, .so) with calling extern symbols
- Standard library with not only syscall mapping
- Support for x86_64 Windows and x86_64 Linux
- More examples 