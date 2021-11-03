# MSPL Documentation

# Commands:
#### `show` - Pop one element from the stack and show it.
#### `copy` - Pop one element from the stack and push it 2 times (copy).
#### `free` - Pop one element from the stack (Just drop it, free stack from it).
#### `+` - Pop two elements from the stack and push their sum.
#### `-` - Pop two elements from the stack and push their difference.
#### `/` - Pop two elements from the stack and push their div, int (%).
#### `*` - Pop two elements from the stack and push their multiply.
#### `==` - Pop two elements from the stack and push 1 if they is equal or 0 if not.
#### `!=` - Pop two elements from the stack and push 1 if they is not equal or 0 if yes.
#### `if` - Pop one element from the stack, if there is 0, jumps to the endif block, otherwise jumps in the conditonal branch (Read more in block "Conditonal")(`0 if 1024 show endif`).
#### `endif` - Closing element of the endif.

# Directives:
#### Directives starts with `#`, like: `#DIRECTIVE_NAME`,
#### List of the directives:
#### `#LINTER_SKIP` - *Unsafe* mode, disable linter check.

# Comments:
#### Comments starts with `//`, like: `// Comment`.
#### (There is one bug with comments, you should write comments without any at the start of the line (Spaces allowed))

# Conditional:
#### There is conditional in the language, to use it you may do something like:
```
0 // Push zero as value to check.

if // Call if so we jump to the next endif if there is 0 in stack.

// DO ANY WHAT YOU WANT IN THAT BLOCK.
1024 show // Show 1024.

endif // Endif.

// This code will run anyway.
2048 show // Show 2048
```
