"""Deterministic, bounded interpreter for an explicitly documented CAPL subset.

No eval/exec, host functions, I/O, loops or arbitrary Python are exposed.
Each request replays an action history from time zero, avoiding server sessions.
"""

import ast
import operator
import re

from backend.can_frames import StandardCanFrame


class SimulationError(ValueError):
    pass


LEX = re.compile(
    r"(?P<space>\s+|//[^\n]*|/\*[\s\S]*?\*/)"
    r"|(?P<number>0[xX][0-9a-fA-F]+|\d+)"
    r'|(?P<string>"[^"\\\r\n]*"|\x27[^\x27\\\r\n]\x27)'
    r"|(?P<name>[A-Za-z_][A-Za-z_0-9]*)"
    r"|(?P<symbol>==|!=|<=|>=|&&|\|\||\+\+|--|[{}();.,=+*/%<>!\-])"
)
PRECEDENCE = {
    "||": 1,
    "&&": 2,
    "==": 3,
    "!=": 3,
    "<": 4,
    ">": 4,
    "<=": 4,
    ">=": 4,
    "+": 5,
    "-": 5,
    "*": 6,
    "/": 6,
    "%": 6,
}
OPERATORS = {
    "+": operator.add,
    "-": operator.sub,
    "*": operator.mul,
    "==": operator.eq,
    "!=": operator.ne,
    "<": operator.lt,
    ">": operator.gt,
    "<=": operator.le,
    ">=": operator.ge,
}


class Parser:
    def __init__(self, source):
        self.tokens = []
        position = 0
        while position < len(source):
            match = LEX.match(source, position)
            if not match:
                line = source.count("\n", 0, position) + 1
                raise SimulationError(
                    f"Unsupported syntax near line {line}: {source[position : position + 24]!r}"
                )
            if match.lastgroup != "space":
                self.tokens.append((match.lastgroup, match.group()))
            position = match.end()
        self.tokens.append(("end", "<end>"))
        self.position = 0

    def peek(self):
        return self.tokens[self.position][1]

    def take(self, expected=None):
        value = self.peek()
        if expected is not None and value != expected:
            raise SimulationError(f"Expected {expected!r}, found {value!r}.")
        if value == "<end>":
            raise SimulationError("Unexpected end of program.")
        self.position += 1
        return value

    def name(self):
        if self.tokens[self.position][0] != "name":
            raise SimulationError("Expected a variable name.")
        name = self.take()
        if name in {"this", "on", "variables", "if", "else"}:
            raise SimulationError(f"Reserved name: {name}.")
        return name

    def number(self):
        if self.tokens[self.position][0] != "number":
            raise SimulationError("Expected a decimal or hexadecimal integer.")
        raw = self.take()
        return int(raw, 16 if raw.lower().startswith("0x") else 10)

    def reference(self):
        name = self.take()
        field, index = None, None
        if self.peek() == ".":
            self.take(".")
            field = self.take()
            if field == "byte":
                self.take("(")
                index = self.expression()
                self.take(")")
            elif field not in {"dlc", "id"}:
                raise SimulationError(f"Unsupported message field: {field}.")
        return ("ref", name, field, index)

    def expression(self, minimum=0):
        kind, value = self.tokens[self.position]
        if value in {"-", "!", "+"}:
            self.take()
            left = ("unary", value, self.expression(7))
        elif value == "(":
            self.take()
            left = self.expression()
            self.take(")")
        elif kind == "number":
            left = ("literal", self.number())
        elif kind == "string":
            left = ("literal", ast.literal_eval(self.take()))
        elif kind == "name":
            left = self.reference()
        else:
            raise SimulationError(f"Expected an expression, found {value!r}.")
        while self.peek() in PRECEDENCE and PRECEDENCE[self.peek()] >= minimum:
            operation = self.take()
            right = self.expression(PRECEDENCE[operation] + 1)
            left = ("binary", operation, left, right)
        return left

    def block(self):
        self.take("{")
        statements = []
        while self.peek() != "}":
            statements.append(self.statement())
        self.take("}")
        return statements

    def statement(self):
        if self.peek() == "if":
            self.take()
            self.take("(")
            condition = self.expression()
            self.take(")")
            yes = self.block() if self.peek() == "{" else [self.statement()]
            no = []
            if self.peek() == "else":
                self.take()
                no = self.block() if self.peek() == "{" else [self.statement()]
            return ("if", condition, yes, no)
        if self.tokens[self.position][0] != "name":
            raise SimulationError(
                f"Unsupported statement beginning with {self.peek()!r}."
            )
        if self.tokens[self.position + 1][1] == "(":
            name = self.take()
            self.take("(")
            arguments = []
            if self.peek() != ")":
                arguments.append(self.expression())
                while self.peek() == ",":
                    self.take()
                    arguments.append(self.expression())
            self.take(")")
            self.take(";")
            return ("call", name, arguments)
        target = self.reference()
        operation = self.take()
        if operation == "=":
            value = self.expression()
        elif operation in {"++", "--"}:
            value = (
                "binary",
                "+" if operation == "++" else "-",
                target,
                ("literal", 1),
            )
        else:
            raise SimulationError("Expected assignment, increment, or decrement.")
        self.take(";")
        return ("assign", target, value)

    def program(self):
        declarations, handlers = [], {}
        if self.peek() == "variables":
            self.take()
            self.take("{")
            names = set()
            while self.peek() != "}":
                kind = self.take()
                if kind not in {"int", "byte", "msTimer", "message"}:
                    raise SimulationError(f"Unsupported declaration type: {kind}.")
                identifier = self.number() if kind == "message" else None
                name = self.name()
                if name in names:
                    raise SimulationError(f"Duplicate declaration: {name}.")
                names.add(name)
                initial = ("literal", 0)
                if self.peek() == "=":
                    if kind not in {"int", "byte"}:
                        raise SimulationError("Only scalar initializers are supported.")
                    self.take()
                    initial = self.expression()
                self.take(";")
                declarations.append((kind, name, identifier, initial))
            self.take("}")
        while self.peek() != "<end>":
            self.take("on")
            event = self.take()
            if event == "start":
                selector = None
            elif event == "key":
                token = self.take()
                if not re.fullmatch(r"'[^'\\\r\n]'", token):
                    raise SimulationError("on key requires one quoted character.")
                selector = token[1:-1]
            elif event == "message":
                selector = self.number()
                if selector > 0x7FF:
                    raise SimulationError(
                        "Only standard 11-bit receive identifiers are supported."
                    )
            elif event == "timer":
                selector = self.name()
            else:
                raise SimulationError(f"Unsupported event: {event}.")
            handler = (event, selector)
            if handler in handlers:
                raise SimulationError(f"Duplicate handler: {handler}.")
            handlers[handler] = self.block()
        if not handlers:
            raise SimulationError("At least one event handler is required.")
        return declarations, handlers


class Runtime:
    def __init__(self, code):
        try:
            declarations, self.handlers = Parser(code).program()
        except RecursionError as exc:
            raise SimulationError("Program nesting is too deep.") from exc
        self.values, self.types, self.messages, self.timers = {}, {}, {}, {}
        self.now = 0
        self.steps = 0
        self.sequence = 0
        self.output, self.frames, self.events, self.console = [], [], [], []
        self.received = None
        for kind, name, identifier, initial in declarations:
            self.types[name] = kind
            if kind == "message":
                if not 0 <= identifier <= 0x7FF:
                    raise SimulationError(
                        "Standard CAN identifiers must be 0x000–0x7FF."
                    )
                self.messages[name] = {
                    "identifier": identifier,
                    "dlc": None,
                    "data": [0] * 8,
                }
            elif kind == "msTimer":
                self.timers[name] = None
            else:
                self.values[name] = self.integer(self.evaluate(initial))
                self.assign(("ref", name, None, None), self.values[name])
        for event, selector in self.handlers:
            if event == "timer" and selector not in self.timers:
                raise SimulationError(f"Timer {selector} is not declared.")
        # Validate identifiers and function names in all handlers, even inactive ones.
        for (event, _), statements in self.handlers.items():
            self.validate(statements, event)

    def integer(self, value):
        if not isinstance(value, int) or isinstance(value, bool):
            raise SimulationError("Expected an integer value.")
        if abs(value) > 2**31 - 1:
            raise SimulationError("Integer exceeds the teaching simulator range.")
        return value

    def validate_expression(self, expr, event, target=False):
        if expr[0] == "ref":
            _, name, field, index = expr
            if name == "this":
                if event != "message" or target:
                    raise SimulationError(
                        "this is read-only and valid only in on message."
                    )
            elif name not in self.types:
                raise SimulationError(f"Undeclared name: {name}.")
            if field and name != "this" and name not in self.messages:
                raise SimulationError(f"{name} is not a message.")
            if target and (
                name in self.timers
                or name in self.messages
                and not field
                or field == "id"
            ):
                raise SimulationError("Invalid assignment target.")
            if index:
                self.validate_expression(index, event)
        elif expr[0] == "binary":
            self.validate_expression(expr[2], event)
            self.validate_expression(expr[3], event)
        elif expr[0] == "unary":
            self.validate_expression(expr[2], event)

    def validate(self, statements, event):
        arities = {"write": 1, "output": 1, "setTimer": 2, "cancelTimer": 1}
        for stmt in statements:
            if stmt[0] == "if":
                self.validate_expression(stmt[1], event)
                self.validate(stmt[2], event)
                self.validate(stmt[3], event)
            elif stmt[0] == "assign":
                self.validate_expression(stmt[1], event, target=True)
                self.validate_expression(stmt[2], event)
            else:
                _, name, args = stmt
                if name not in arities or len(args) != arities[name]:
                    raise SimulationError(
                        f"Unsupported function or argument count: {name}."
                    )
                for arg in args:
                    self.validate_expression(arg, event)
                if name in {"output", "setTimer", "cancelTimer"}:
                    ref = args[0]
                    expected = self.messages if name == "output" else self.timers
                    if ref[0] != "ref" or ref[2] is not None or ref[1] not in expected:
                        raise SimulationError(f"Invalid first argument to {name}.")

    def evaluate(self, expr):
        kind = expr[0]
        if kind == "literal":
            return expr[1]
        if kind == "ref":
            _, name, field, index = expr
            if field is None:
                if name not in self.values:
                    raise SimulationError(f"{name} is not an integer variable.")
                return self.values[name]
            message = self.received if name == "this" else self.messages.get(name)
            if message is None:
                raise SimulationError("No received message is available.")
            if field == "id":
                return message["identifier"]
            if field == "dlc":
                return message["dlc"] if message["dlc"] is not None else 0
            offset = self.integer(self.evaluate(index))
            if not 0 <= offset < 8:
                raise SimulationError("Byte index must be 0–7.")
            if name == "this" and offset >= message["dlc"]:
                raise SimulationError("Attempted to read beyond received DLC.")
            return message["data"][offset]
        if kind == "unary":
            value = self.integer(self.evaluate(expr[2]))
            return (
                int(not value)
                if expr[1] == "!"
                else -value
                if expr[1] == "-"
                else value
            )
        _, operation, left_expr, right_expr = expr
        left = self.integer(self.evaluate(left_expr))
        if operation == "&&":
            return int(bool(left) and bool(self.integer(self.evaluate(right_expr))))
        if operation == "||":
            return int(bool(left) or bool(self.integer(self.evaluate(right_expr))))
        right = self.integer(self.evaluate(right_expr))
        if operation in {"/", "%"}:
            if right == 0:
                raise SimulationError("Division by zero.")
            quotient = (abs(left) // abs(right)) * (
                -1 if (left < 0) != (right < 0) else 1
            )
            return quotient if operation == "/" else left - quotient * right
        return int(OPERATORS[operation](left, right))

    def assign(self, ref, value):
        _, name, field, index = ref
        value = self.integer(value)
        if field is None:
            if self.types.get(name) == "byte" and not 0 <= value <= 255:
                raise SimulationError(
                    "Byte variables must stay within 0–255; implicit wrapping is unsupported."
                )
            self.values[name] = value
        elif field == "dlc":
            if not 0 <= value <= 8:
                raise SimulationError("Classical CAN DLC must be 0–8.")
            self.messages[name]["dlc"] = value
        else:
            offset = self.integer(self.evaluate(index))
            if not 0 <= offset < 8 or not 0 <= value <= 255:
                raise SimulationError("Byte index must be 0–7 and value 0–255.")
            self.messages[name]["data"][offset] = value

    def execute(self, statements):
        for stmt in statements:
            self.steps += 1
            if self.steps > 10000:
                raise SimulationError("Simulation instruction budget exceeded.")
            if stmt[0] == "if":
                self.execute(
                    stmt[2] if self.integer(self.evaluate(stmt[1])) else stmt[3]
                )
            elif stmt[0] == "assign":
                self.assign(stmt[1], self.evaluate(stmt[2]))
            else:
                _, name, args = stmt
                if name == "write":
                    message = self.evaluate(args[0])
                    if not isinstance(message, str):
                        raise SimulationError(
                            "write() currently accepts one literal string."
                        )
                    self.output.append(message)
                    self.console.append({"time_ms": self.now, "text": message})
                elif name == "output":
                    message = self.messages[args[0][1]]
                    if message["dlc"] is None:
                        raise SimulationError("Set DLC explicitly before output().")
                    frame = StandardCanFrame(
                        identifier=message["identifier"],
                        data=message["data"][: message["dlc"]],
                    ).preview()
                    self.frames.append(
                        {**frame, "time_ms": self.now, "direction": "Tx"}
                    )
                elif name == "cancelTimer":
                    self.timers[args[0][1]] = None
                else:
                    delay = self.integer(self.evaluate(args[1]))
                    if not 1 <= delay <= 60000:
                        raise SimulationError("Timer delays must be 1–60000 ms.")
                    self.sequence += 1
                    self.timers[args[0][1]] = (self.now + delay, self.sequence)

    def dispatch(self, event, selector=None):
        self.events.append({"time_ms": self.now, "event": event, "selector": selector})
        self.execute(self.handlers.get((event, selector), []))

    def advance(self, milliseconds):
        target = self.now + milliseconds
        if target > 60000:
            raise SimulationError("A simulation can span at most 60000 ms.")
        while True:
            scheduled = [
                (due[0], due[1], name)
                for name, due in self.timers.items()
                if due is not None and due[0] <= target
            ]
            if not scheduled:
                break
            due, _, name = min(scheduled)
            self.now = due
            self.timers[name] = None  # one-shot; the handler must explicitly rearm
            self.dispatch("timer", name)
        self.now = target

    def replay(self, actions):
        self.dispatch("start")
        for action in actions:
            kind = action["type"]
            if kind == "advance":
                self.advance(action["ms"])
            elif kind == "key":
                self.dispatch("key", action["key"])
            else:
                frame = StandardCanFrame(
                    identifier=action["identifier"], data=action["data"]
                ).preview()
                self.frames.append({**frame, "time_ms": self.now, "direction": "Rx"})
                self.received = {
                    "identifier": frame["identifier"],
                    "dlc": frame["dlc"],
                    "data": frame["data"],
                }
                self.dispatch("message", frame["identifier"])
                self.received = None
        return {
            "time_ms": self.now,
            "output": self.output,
            "console": self.console,
            "frames": self.frames,
            "events": self.events,
            "variables": self.values,
            "timers": {
                name: due[0] if due else None for name, due in self.timers.items()
            },
        }
