import math
import operator
from typing import Any
from collections.abc import Callable

from pydantic import Field
import pydantic
from pyparsing import (Forward, Group, Literal, ParseResults, Regex, Suppress,
                       Word, alphanums, alphas, delimitedList)

from openglider.utils.dataclass import BaseModel
from openglider.vector.unit import Angle, Length, Percentage, Quantity

# parse arithmetic expressions similar to the pyparsing calculator example:
# https://github.com/pyparsing/pyparsing/blob/master/examples/fourFn.py


default_units: list[type[Quantity]] = [
    Length,
    Percentage,
    Angle,
]

AllUnits = Length | Percentage | Angle
#UnitAndFloat = Length | Percentage | Angle | float

def default_resolver(key: str) -> float:
    raise KeyError(f"unable to resolve '{key}' (no variable resolver)")


class Parser(BaseModel):
    units: list[type[Quantity]] = Field(default_factory=default_units.copy)
    variable_resolver: Callable[[str], float] = default_resolver

    _parser: Forward | None =  pydantic.PrivateAttr(default=None)
    _units: dict[str, type[Quantity]] | None = pydantic.PrivateAttr(default=None)

    stack: list[str | float | Quantity] = Field(default_factory=list)

    _operations = {
        "+": operator.add,
        "-": operator.sub,
        "*": operator.mul,
        "/": operator.truediv,
        "^": operator.pow,
    }

    _functions: dict[str, Callable[[Any], Any]] = {
        "sin": math.sin,
        "cos": math.cos,
        "tan": math.tan,
        "exp": math.exp,
        "sqrt": math.sqrt,
        "abs": abs,
        "trunc": int,
        "round": round,
        "sgn": lambda a: -1 if a < 0 else 1
    }

    _constants = {
        "PI": Angle(math.pi),
        #"E": math.e
    }

    def get_units(self) -> dict[str, type[Quantity]]:
        if self._units is None:
            result = {}
            for quantity_type in self.units:
                result[quantity_type.unit] = quantity_type
                for unit in quantity_type.unit_variants:
                    result[unit] = quantity_type
            
            self._units = result
        
        return self._units
    
    def get_parser(self) -> Forward:
        if self._parser is None:            
            regex_number = Regex(Quantity.re_number)
            units = regex_number + Regex(Quantity.re_unit)

            identifier = Word(alphas, alphanums + "_$")

            plus, minus, mult, div = map(Literal, "+-*/")
            left_par, right_par = map(Suppress, "()")
            addop = plus | minus
            multop = mult | div
            expop = Literal("^")

            expr = Forward()
            expr_list = delimitedList(Group(expr))

            # add parse action that replaces the function identifier with a (name, number of args) tuple
            def insert_fn_argcount_tuple(t: ParseResults) -> None:
                fn = t.pop(0)
                num_args = len(t[0])
                t.insert(0, (fn, num_args))

            fn_call = (identifier + left_par - Group(expr_list) + right_par).setParseAction(
                insert_fn_argcount_tuple
            )

            atom = (
                addop[...]
                + (
                    units.setParseAction(self.push_with_unit)
                    |(fn_call | regex_number | identifier).setParseAction(self.push_first)
                    | Group(left_par + expr + right_par)
                )
            ).setParseAction(self.push_unary_minus)

            # by defining exponentiation as "atom [ ^ factor ]..." instead of "atom [ ^ atom ]...", we get right-to-left
            # exponents, instead of left-to-right that is, 2^3^2 = 2^(3^2), not (2^3)^2.
            factor = Forward()
            factor <<= atom + (expop + factor).setParseAction(self.push_first)[...]
            term = factor + (multop + factor).setParseAction(self.push_first)[...]
            expr <<= term + (addop + term).setParseAction(self.push_first)[...]

            self._parser = expr

        return self._parser
    
    def push_with_unit(self, toks: ParseResults) -> None:
        _amount, unit = toks
        available_units = self.get_units()

        if unit not in available_units:
            raise ValueError(f"unknown unit '{unit}' available units: {list(available_units.keys())}")
        
        amount = available_units[unit](float(_amount), unit=unit)
        self.stack.append(amount)
    
    def push_first(self, toks: ParseResults) -> None:
        self.stack.append(toks[0])

    def push_unary_minus(self, toks: ParseResults) -> None:
        for t in toks:
            if t == "-":
                self.stack.append("unary -")
            else:
                break
    
    def parse(self, expression: str | float) -> Quantity | float:
        if isinstance(expression, (float, int)):
            return float(expression)
        
        self.stack.clear()

        # try parsing the input string
        parse_result = self.get_parser().parseString(expression, parseAll=True)

        if len(parse_result) == 0 or parse_result[0] != "Parse Failure":
            #for i, ob in enumerate(self.stack):
            #    if isinstance(ob, str) and ob[0].isalpha() and ob not in self._constants:
                    
            return self.evaluate_stack()
        
        raise Exception("")

    def evaluate_stack(self) -> Quantity | float:
        op, num_args = self.stack.pop(), 0

        if isinstance(op, (float, int, Quantity)):
            return op

        if isinstance(op, tuple):
            op, num_args = op

        if op == "unary -":
            return -self.evaluate_stack()
        if op in "+-*/^":
            # note: operands are pushed onto the stack in reverse order
            op2 = self.evaluate_stack()
            op1 = self.evaluate_stack()
            return self._operations[op](op1, op2)
        elif op[0].isalpha():
            if op in self._constants:
                return self._constants[op]
            elif op in self._functions:
                # note: args are pushed onto the stack in reverse order
                args = reversed([self.evaluate_stack() for _ in range(num_args)])
                return self._functions[op](*args)
            else:
                return self.variable_resolver(op)
        else:
            return float(op)


if __name__ == "__main__":
    parser = Parser()

    print(parser.parse("3 + 3cm"))