# This file is auto-generated by MSPL python subcommand! 

# Allocate stack (As is MSPL is Stack-Oriented Language): 
stack = list()

# Work with stack functions: 
def push(v):
	stack.append(v)
def pop():
	return stack.pop()


# Source (stack_example.mspl): 
push(2)  # Text: 2 [Line 5, Row 1]

push(2)  # Text: 2 [Line 5, Row 3]

push(pop() + pop())  # Text: + [Line 5, Row 5]

push(4)  # Text: 4 [Line 8, Row 1]

push(4)  # Text: 4 [Line 8, Row 3]

push(pop() + pop())  # Text: + [Line 8, Row 5]

push(pop() * pop())  # Text: * [Line 13, Row 1]

print(pop())  # Text: show [Line 16, Row 1]
push(32)  # Text: 32 [Line 18, Row 1]

pop()  # Text: free [Line 18, Row 4]
