# Gofra Language Documentation

# Operations

## Simple

#### `+`, `-`, `*`, `/`, `%`, `==`, `!=`, `<`, `>`,`<=`, `>=`.

### (This is base operations, so it shouldn`t be documented)

## Other

#### `show` - Pop one element from the stack and show it. (`[0, 1] => [0]`)

#### `copy` - Pop one element from the stack and push it 2 times (copy). (`[0, 1] => [0, 1, 1]`)

#### `copy2` - Pop two elements from the stack and push it 4 times (copy) (`[0, 1] => [0, 1, 0, 1]`).

#### `free` - Pop one element from the stack (Just drop it, free stack from it). (`[0, 1] => [0]`)

#### `swap` - Pop two elements from the stack and swap them (`[0, 1] => [1, 0]`).

# Keywords\*

#### `if` - Pop one element from the stack, if there is 0, jumps to the end or else block, otherwise jumps in the conditonal branch (Read more in block "Conditonal")(`0 if 1024 show end`).

#### `while ... do` - `do` pops one element from the stack and jumps to the end if there is 0, otherwise jump in the loop body, and after executing body, jump back to the while.

#### `else` - Other branch element of the if.

#### `end` - Closing element of the if or do (while-do).

# Directives

#### Directive starts with `#`, like: `#DIRECTIVE_NAME`,

#### List of the directives:

#### `#MEM_BUF_BYTE_SIZE=N` - Says that there is only `N` bytes in the memory buffer.

# Comments

#### Comment starts with `//`, like: `// Comment`.

#### (There is one bug with comments, you should write comments without any at the start of the line (Spaces allowed))

# Definitions

#### Supported: `DEFINE`, `END`

#### There is definitions in the language, to use it you may do something like:

```
define NAME ... end // You may change name.
NAME // Will expand.
```

# Characters

#### `'a'` - Pushes 97 (Code) of the character into the stack.

# Strings

#### `"Hello world"` - Pushes string pointer into the stack, and also size.

#### After defining string you may use data to show the string, using `mshowc`,

#### Or do some checks, based on string size.

#### You also may grab strings from I/O using io_read_str (Same as defining string, but string is from I/O instead of source).

# Input / Output (I/O)

#### `io_read_str` - Pushes string, that user is input at the stack. (Pointer, Size)

#### `io_read_int` - Pushes integer, or -1 if incorrect value, that user is input.

# Constants

#### `NULL` - Returns 0.

#### `MPTR` - Returns null-pointer (Should be 0 for non-compiled (even if python)).

# Conditional

#### Supported: `IF`, `ELSE`, `END`

#### There is conditional in the language, to use it you may do something like:

```
0 if // Jump to else if 0 or jump in if !0

    // Do anything what you want in that block.
    1024 1023 == if
        1025 show
    else
        1023 show
    end
else
    512 show
end

// This code will run anyway.
2048 show
```

# While Loops

#### Supported: `WHILE`, `DO`, `END`

#### There is while loops in the language, to use it you may do something like:

```
0 while copy 10 < do
    // Push 0, copy it and compare to 10, if less, jump in the body (here).

    // Here we have our 0 before the while.

    // Copy counter and show it.
    copy show

    // Increment counter.
    inc
end
```

# Memory

#### Supported:

#### `mwrite` - Pop two elements from the stack (`[pointer], [value] => []`), and writes value at the pointer to memory(1 byte | 8 bits cell)

#### `mread` - Pop one element from the stack (`[pointer] => [])`, and pushes back value at the pointer from memory (1 byte | 8 bits cell),

#### `mshowc` - Pop two elements from the stack (`[pointer], [length] => []`), and shows every character in memory `[pointer]...[pointer+length-1]`,

#### `MPTR` - Push *null_pointer\*\* to the stack (By default *0\*\*) to write memory at

#### `mwrite4b` - Same as `mwrite`, but writes 4 bytes | 32 bits (Remember that you should write next value at `[pointer] 4 +` as there is 4 bytes taken by that value)

#### `mread4b` - Same as `mread`, but reads 4 bytes | 32 bits

#### There is memory\* support in the language, to use it you may do something like:

```
// Write 9 to memory pointer 0.
0 9 mwrite

// Same as above.
MPTR 9 mwrite

// Read that 9 from memory and push onto the stack.
MPTR mread // Do not forgot to call `free` after, so there is no unused data in the stack.

// Write AB (97, 98 codes) to the memory.
MPTR 0 + 97 write
MPTR 1 + 98 write

// Show 2 chars from the memory.
MPTR 2 mshowc
```
