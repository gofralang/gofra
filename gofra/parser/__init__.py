"""Parser package that used to parse source tokens into operators."""

from .operators import Operator, OperatorType
from .parser import parse_file

__all__ = ["Operator", "OperatorType", "parse_file"]
