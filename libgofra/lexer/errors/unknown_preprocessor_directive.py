from libgofra.exceptions import GofraError
from libgofra.lexer.tokens import TokenLocation


class UnknownPreprocessorDirectiveError(GofraError):
    def __init__(self, at: TokenLocation, directive: str) -> None:
        self.at = at
        self.directive = directive

    def __repr__(self) -> str:
        return f"""Unknown preprocessor directive at {self.at}!

Encountered unknown directive: '{self.directive}'

Known directives are: #define #undef #include #ifdef #ifndef #endif

{self.generic_error_name}"""
