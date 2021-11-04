# MSPL Documentation

# Operations
## Simple
#### `+`, `-`, `*`, `/`, `==`, `!=`, `<`, `>`,`<=`, `>=`.
### (This is base operations, so it shouldn`t be documented)
## Other
#### `show` - Pop one element from the stack and show it.
#### `copy` - Pop one element from the stack and push it 2 times (copy).
#### `free` - Pop one element from the stack (Just drop it, free stack from it).
#### `swap` - Pop two elements from the stack and swap them ([0, 1] => [1, 0]).

# Keywords*
#### `if` - Pop one element from the stack, if there is 0, jumps to the endif or else block, otherwise jumps in the conditonal branch (Read more in block "Conditonal")(`0 if 1024 show endif`).
#### `while ... then` - `then` pops one element from the stack and jumps to the endif if there is 0, otherwise jump in the loop body, and after executing body, jump back to the while.
#### `else` - Other branch element of the if.
#### `endif` - Closing element of the if or then (while-then).

# Directives
#### Directive starts with `#`, like: `#DIRECTIVE_NAME`,
#### List of the directives:
#### `#LINTER_SKIP` - *Unsafe* mode, disable linter check.
#### `#MEM_BUF_BYTE_SIZE=N` - Says that there is only `N` bytes in the memory buffer.
#### `#PYTHON_COMMENTS_SKIP` - Disable writing comments in the Python when generating it (Should don`t break anything), you may use this if you dont want system comments in your generated python scripts.

# Comments
#### Comment starts with `//`, like: `// Comment`.
#### (There is one bug with comments, you should write comments without any at the start of the line (Spaces allowed))

# Conditional
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

# While Loops
#### Supported: `WHILE`, `THEN`, `ENDIF`
#### There is while loops in the language, to use it you may do something like:
```
0 while copy 10 < then
    // Push 0, copy it and compare to 10, if less, jump in the body (here).
    
    // Here we have our 0 before the while.
    
    // Copy counter and show it.
    copy show
    
    // Increment counter.
    inc
endif
```

# Memory
#### Supported: `MBWRITE`, `MBREAD`, `MBSHOW`, `MBPTR`
#### There is memory* support in the language, to use it you may do something like:
```
// Write 9 to memory pointer 0.
0 9 mbwrite

// Same as above.
mbptr 9 mbwrite

// Read that 9 from memory and push onto the stack.
mbptr mbread // Do not forgot to call `free` after, so there is no unused data in the stack.

// Write AB (97, 98 codes) to the memory.
mbptr 0 + 97 write
mbptr 1 + 98 write

// Show 2 chars from the memory.
mbptr 2 mbshowc
```