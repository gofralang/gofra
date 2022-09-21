from enum import Enum, auto
from dataclasses import dataclass


class VMRuntimeError(Exception):
    pass


class BytecodeInstructionType(Enum):
    #
    STACK_PUSH_INTEGER = auto()
    STACK_DROP = auto()
    STACK_SWAP = auto()
    STACK_COPY = auto()
    STACK_COPY2 = auto()
    STACK_COPY_OVER = auto()
    #
    CONDITIONAL_END = auto()
    CONDITIONAL_IF = auto()
    CONDITIONAL_ELSE = auto()
    CONDITIONAL_DO = auto()
    CONDITIONAL_WHILE = auto()
    #
    LOCAL_STORE_INTEGER = auto()
    LOCAL_LOAD_INTEGER = auto()
    #
    MATH_ADD = auto()
    MATH_DIVIDE = auto()
    MATH_MODULUS = auto()
    MATH_MINUS = auto()
    MATH_MULTIPLY = auto()
    MATH_DECREMENT = auto()
    MATH_INCREMENT = auto()
    #
    LOGIC_EQUAL = auto()
    LOGIC_NOT_EQUAL = auto()
    LOGIC_LESS = auto()
    LOGIC_GREATER = auto()
    LOGIC_LESS_EQUAL_ = auto()
    LOGIC_GREATER_EQUAL = auto()
    #
    VM_ECHO_INTEGER = auto()


@dataclass
class BytecodeInstruction:
    type: BytecodeInstructionType
    operand: int | None = None


class Bytecode:
    def __init__(self, instructions: list[BytecodeInstruction]) -> None:
        self._instructions = instructions

    def get_instructions(self):
        return self._instructions

    def get_instruction(self, index: int):
        return self._instructions[index]

    def out_of_bounds(self, index: int):
        return index >= len(self._instructions)


class VM:
    _runtime_emulated_stack = []
    _runtime_emulated_locals = dict()
    _runtime_current_execution_index = 0

    def __init__(self):
        self._runtime_clear()

    def execute_bytecode(self, bytecode: Bytecode):
        self._runtime_clear()
        while not bytecode.out_of_bounds(self._runtime_current_execution_index):
            instruction = bytecode.get_instruction(
                self._runtime_current_execution_index
            )
            self.execute_bytecode_instruction(
                bytecode=bytecode, instruction=instruction
            )

    def execute_bytecode_instruction(
        self, bytecode: Bytecode, instruction: BytecodeInstruction
    ):
        # print(">>>", instruction.type.name, self._runtime_current_execution_index)
        if instruction.type == BytecodeInstructionType.STACK_PUSH_INTEGER:
            self._stack_push(instruction.operand)
            self._runtime_current_execution_index += 1
        elif instruction.type == BytecodeInstructionType.LOCAL_STORE_INTEGER:
            self._local_store(instruction.operand, self._stack_pop())
            self._runtime_current_execution_index += 1
        elif instruction.type == BytecodeInstructionType.LOCAL_LOAD_INTEGER:
            self._stack_push(self._local_load(instruction.operand))
            self._runtime_current_execution_index += 1
        elif instruction.type == BytecodeInstructionType.MATH_ADD:
            operand_a = self._stack_pop()
            operand_b = self._stack_pop()
            self._stack_push(operand_a + operand_b)
            self._runtime_current_execution_index += 1
        elif instruction.type == BytecodeInstructionType.MATH_INCREMENT:
            operand_a = self._stack_pop()
            self._stack_push(operand_a + 1)
            self._runtime_current_execution_index += 1
        elif instruction.type == BytecodeInstructionType.STACK_COPY:
            operand_a = self._stack_pop()
            self._stack_push(operand_a)
            self._stack_push(operand_a)
            self._runtime_current_execution_index += 1
        elif instruction.type == BytecodeInstructionType.STACK_DROP:
            self._stack_pop()
            self._runtime_current_execution_index += 1
        elif instruction.type == BytecodeInstructionType.LOGIC_LESS:
            operand_a = self._stack_pop()
            operand_b = self._stack_pop()
            self._stack_push(operand_b < operand_a)
            self._runtime_current_execution_index += 1
        elif instruction.type == BytecodeInstructionType.MATH_MULTIPLY:
            operand_a = self._stack_pop()
            operand_b = self._stack_pop()
            self._stack_push(operand_a * operand_b)
            self._runtime_current_execution_index += 1
        elif instruction.type == BytecodeInstructionType.VM_ECHO_INTEGER:
            print(self._stack_pop())
            self._runtime_current_execution_index += 1
        elif instruction.type == BytecodeInstructionType.CONDITIONAL_IF:
            operand_a = self._stack_pop()
            if operand_a == 0:
                # Jump to the operator operand.
                # As this is IF, so we should jump to the END.
                self._runtime_current_execution_index = instruction.operand
            else:
                self._runtime_current_execution_index += 1
        elif instruction.type == BytecodeInstructionType.CONDITIONAL_END:
            # Jump to the operator operand.
            # As this is END operator, we should have index + 1, index!
            self._runtime_current_execution_index = instruction.operand
        elif instruction.type == BytecodeInstructionType.CONDITIONAL_ELSE:
            # Jump to the operator operand.
            # As this is ELSE operator, we should have index + 1, index!
            self._runtime_current_execution_index = instruction.operand
        elif instruction.type == BytecodeInstructionType.CONDITIONAL_DO:
            operand_a = self._stack_pop()
            if operand_a == 0:
                end_jump_operator_index = bytecode.get_instruction(
                    instruction.operand
                ).operand

                # Jump to the operator operand.
                # As this is DO, so we should jump to the END.
                self._runtime_current_execution_index = int(end_jump_operator_index)
            else:
                # If this is true.

                # Increment operator index.
                # This is makes jump into the if body.
                self._runtime_current_execution_index += 1
        elif instruction.type == BytecodeInstructionType.CONDITIONAL_WHILE:
            # Increment operator index.
            # This is makes jump into the if statement (expression).
            self._runtime_current_execution_index += 1
        else:
            raise VMRuntimeError(
                "Got unexpected bytecode instruction: %s" % instruction
            )
        # print(self._runtime_emulated_stack, self._runtime_emulated_locals)

    def _local_store(self, index: int, value: int):
        if not isinstance(value, int):
            raise VMRuntimeError(
                "Virtual machine got invalid value to store in locals!"
            )
        self._runtime_emulated_locals[index] = value

    def _local_load(self, index: int) -> int:
        return self._runtime_emulated_locals[index]

    def _stack_push(self, value: int):
        if not isinstance(value, int):
            raise VMRuntimeError(
                "Virtual machine got invalid value to push on to the stack!"
            )
        self._runtime_emulated_stack.append(int(value))

    def _stack_pop(self) -> int:
        if len(self._runtime_emulated_stack) == 0:
            raise VMRuntimeError("Virtual machine unable to pop from empty stack!")
        return self._runtime_emulated_stack.pop()

    def _runtime_clear(self):
        self._stack_clear()
        self._runtime_current_execution_index = 0

    def _stack_clear(self):
        self._runtime_emulated_stack = []


if __name__ == "__main__":
    VM().execute_bytecode(
        Bytecode(
            instructions=[
                BytecodeInstruction(BytecodeInstructionType.STACK_PUSH_INTEGER, 32),
                BytecodeInstruction(BytecodeInstructionType.LOCAL_STORE_INTEGER, 1),
                BytecodeInstruction(BytecodeInstructionType.LOCAL_LOAD_INTEGER, 1),
                BytecodeInstruction(BytecodeInstructionType.STACK_PUSH_INTEGER, 32),
                BytecodeInstruction(BytecodeInstructionType.MATH_ADD_INTEGER),
                BytecodeInstruction(BytecodeInstructionType.LOCAL_STORE_INTEGER, 2),
            ]
        )
    )
