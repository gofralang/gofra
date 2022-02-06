"""
    'Gofra' programming language module.
    Contains all submodules and stuff releated to 'Gofra'.
"""

__version__ = "0.1"
__license__ = "MIT"
__author__ = "Kirill Zhosul @kirillzhosul"

# Utils.
from . import stack
from . import errors

# Main.
from . import lexer
from . import cli
