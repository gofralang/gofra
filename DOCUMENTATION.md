# MSPL Documentation

# Commands:
#### `show` - Pop one element from the stack and show it.
#### `copy` - Pop one element from the stack and push it 2 times (copy).
#### `free` - Pop one element from the stack (Just drop it, free stack from it).
#### `swap` - Pop two elements from the stack and swap them ([0, 1] => [1, 0]).
#### `+` - Pop two elements from the stack and push their sum.
#### `-` - Pop two elements from the stack and push their difference.
#### `/` - Pop two elements from the stack and push their div, int (%).
#### `*` - Pop two elements from the stack and push their multiply.
#### `==` - Pop two elements from the stack and push 1 if they is equal or 0 if not.
#### `!=` - Pop two elements from the stack and push 1 if they is not equal or 0 if yes.
#### `<` - Pop two elements from the stack and push 1 if A[1] less than B[2] or 0 if not.
#### `>` - Pop two elements from the stack and push 1 if A[1] greater than B[2] or 0 if not.
#### `<=` - Pop two elements from the stack and push 1 if A[1] less or equal than B[2] or 0 if not.
#### `>=` - Pop two elements from the stack and push 1 if A[1] greater or eqal than B[2] or 0 if not.
#### `if` - Pop one element from the stack, if there is 0, jumps to the endif or else block, otherwise jumps in the conditonal branch (Read more in block "Conditonal")(`0 if 1024 show endif`).
#### `else` - Other branch element of the if.
#### `endif` - Closing element of the if.

# Directives:
#### Directive starts with `#`, like: `#DIRECTIVE_NAME`,
#### List of the directives:
#### `#LINTER_SKIP` - *Unsafe* mode, disable linter check.
#### `#PYTHON_COMMENTS_SKIP` - Disable writing comments in the Python when generating it (Should don`t break anything), you may use this if you dont want system comments in your generated python scripts.
# Comments:
#### Comment starts with `//`, like: `// Comment`.
#### (There is one bug with comments, you should write comments without any at the start of the line (Spaces allowed))

# Conditional:
#### Supported: `IF`, `ELSE`, `ENDIF`
#### There is conditional in the language, to use it you may do something like:
```
0 if // Jump to else if 0 or jump in if !0

    // Do anything what you want in that block.
    1024 1023 == if
        1025 show
    else
        1023 show
    endif 
else

    512 show
endif

// This code will run anyway.
2048 show
```
