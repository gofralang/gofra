from __future__ import annotations

from collections.abc import MutableSequence
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Sequence

    from gofra.lexer import Token
    from gofra.lexer.tokens import TokenLocation
    from gofra.parser.operators import Operator
    from gofra.typecheck.types import GofraType


@dataclass(frozen=False)
class Function:
    location: TokenLocation
    name: str

    inner_tokens: MutableSequence[Token]
    inner_body: MutableSequence[Operator]

    call_signature: Sequence[GofraType]
    return_type: GofraType | None

    is_inline: bool
    is_extern: bool

    def push_token(self, token: Token) -> Token:
        self.inner_tokens.append(token)
        return token
