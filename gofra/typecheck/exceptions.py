from collections.abc import Sequence

from gofra.exceptions import GofraError
from gofra.parser.operators import Operator

from .types import GofraType


class TypecheckInvalidArgumentTypeError(GofraError):
    def __init__(
        self,
        *args: object,
        expected_type: GofraType,
        actual_type: GofraType,
        operator: Operator,
    ) -> None:
        super().__init__(*args)
        self.expected_type = expected_type
        self.actual_type = actual_type
        self.operator = operator

    def __repr__(self) -> str:
        return f"""Type safety check failed!

Expected {self.expected_type.name} but got {self.actual_type.name}
 for '{self.operator.token.text}' at {self.operator.token.location}

Did you miss the types?"""


class TypecheckInvalidBinaryMathArithmeticsError(GofraError):
    def __init__(
        self,
        *args: object,
        actual_lhs_type: GofraType,
        actual_rhs_type: GofraType,
        operator: Operator,
    ) -> None:
        super().__init__(*args)
        self.actual_lhs_type = actual_lhs_type
        self.actual_rhs_type = actual_rhs_type
        self.operator = operator

    def __repr__(self) -> str:
        return f"""Type safety check failed!

Binary math operator '{self.operator.token.text}' at {self.operator.token.location} expected both {GofraType.INTEGER.name} operands, 
but got {self.actual_lhs_type.name} on the left and {self.actual_rhs_type.name} on the right.

Expected contract: [{GofraType.INTEGER.name}, {GofraType.INTEGER.name}]
Actual contract: [{self.actual_lhs_type.name}, {self.actual_rhs_type.name}]

Pointer arithmetics disallowed within binary math operators!
Please use desired pointer-arithmetics safe operators!

Did you miss the types?"""


class TypecheckInvalidPointerArithmeticsError(GofraError):
    def __init__(
        self,
        *args: object,
        actual_lhs_type: GofraType,
        actual_rhs_type: GofraType,
        operator: Operator,
    ) -> None:
        super().__init__(*args)
        self.actual_lhs_type = actual_lhs_type
        self.actual_rhs_type = actual_rhs_type
        self.operator = operator

    def __repr__(self) -> str:
        return f"""Type safety check failed!

Invalid pointer arithmetics for operator '{self.operator.token.text}' at {self.operator.token.location}

Expected contract: [{GofraType.POINTER.name}, {GofraType.INTEGER.name}]
Actual contract: [{self.actual_lhs_type.name}, {self.actual_rhs_type.name}]

Did you miss the types?"""


class TypecheckNonEmptyStackAtEndError(GofraError):
    def __init__(
        self,
        *args: object,
        stack_size: int,
    ) -> None:
        super().__init__(*args)
        self.stack_size = stack_size

    def __repr__(self) -> str:
        return f"""Type safety check error!
Got {self.stack_size} stack elements at the end.
Expected NO elements at the end.

Did you forgot to drop those elements?"""


class TypecheckNotEnoughArgumentsError(GofraError):
    def __init__(
        self,
        *args: object,
        types_on_stack: Sequence[GofraType],
        required_args: int,
        operator: Operator,
    ) -> None:
        super().__init__(*args)
        self.types_on_stack = types_on_stack
        self.required_args = required_args
        self.operator = operator

    def __repr__(self) -> str:
        return f"""Type safety check failed!

Expected {self.required_args} arguments on stack but got {len(self.types_on_stack)}
 for '{self.operator.token.text}' at {self.operator.token.location}

Did you miss some arguments?"""
