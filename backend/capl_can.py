import re

from backend.can_frames import StandardCanFrame

# This small CAPL subset accepts hexadecimal and decimal integer literals.
NUMBER = r"(?:0[xX][0-9a-fA-F]+|[0-9]+)"


def parse_number(value):
    return int(value, 16 if value.lower().startswith("0x") else 10)


def simulate_can_program(code, event="start", key=None):
    # Match the entire source so the program has one message declaration
    # followed by one supported event handler.
    program = re.fullmatch(
        rf"\s*variables\s*\{{\s*"
        rf"message\s+(?P<identifier>{NUMBER})\s+"
        rf"(?P<name>[A-Za-z_][A-Za-z0-9_]*)\s*;"
        rf"\s*\}}\s*"
        rf"on\s+(?P<event>start|key\s+'(?P<key>[^'\\\r\n])')"
        rf"\s*\{{(?P<body>.*)\}}\s*",
        code,
        flags=re.DOTALL,
    )

    if program is None:
        raise ValueError(
            "Expected one message declaration in variables "
            "followed by one on start or on key event."
        )

    identifier = parse_number(program.group("identifier"))

    if identifier > 0x7FF:
        raise ValueError("Standard CAN identifiers cannot exceed 0x7FF.")

    # Build the statement patterns around the declared name so assignments
    # and output() refer to the message defined by this program.
    name = re.escape(program.group("name"))
    body = program.group("body")

    patterns = {
        "dlc": re.compile(rf"{name}\.dlc\s*=\s*({NUMBER})\s*;"),
        "byte": re.compile(
            rf"{name}\.byte\s*\(\s*({NUMBER})\s*\)"
            rf"\s*=\s*({NUMBER})\s*;"
        ),
        "output": re.compile(rf"output\s*\(\s*{name}\s*\)\s*;"),
        "write": re.compile(r'write\s*\(\s*"([^"\\\r\n]*)"\s*\)\s*;'),
    }

    # The message buffer has eight slots. DLC determines how many bytes
    # from that buffer are included when the program transmits a frame.
    dlc = None
    data = [0] * 8
    output = []
    frames = []
    position = 0

    # Parse from the current position so unsupported text cannot be
    # silently skipped between valid statements.
    while position < len(body):
        if body[position].isspace():
            position += 1
            continue

        for operation, pattern in patterns.items():
            instruction = pattern.match(body, position)

            if instruction is None:
                continue

            if operation == "dlc":
                dlc = parse_number(instruction.group(1))
                if dlc > 8:
                    raise ValueError("Classical CAN DLC must be between 0 and 8.")

            elif operation == "byte":
                index = parse_number(instruction.group(1))
                value = parse_number(instruction.group(2))

                if index > 7:
                    raise ValueError("Byte index must be between 0 and 7.")
                if value > 255:
                    raise ValueError("Byte value must be between 0 and 255.")

                data[index] = value

            elif operation == "write":
                output.append(instruction.group(1))

            elif operation == "output":
                if dlc is None:
                    raise ValueError(
                        "Our simulator requires an explicit DLC before output()."
                    )

                # Slice the current buffer to capture a snapshot.
                # Later assignments cannot modify an earlier transmission.
                frame = StandardCanFrame(
                    identifier=identifier,
                    data=data[:dlc],
                )
                frames.append(frame.preview())

            position = instruction.end()
            break
        else:
            raise ValueError(
                "Unsupported statement. Use the declared message's "
                'dlc, byte(index), output(message), or write("text").'
            )

    # Validate the handler body for every request. Return its logs and
    # frames only if the requested event matches, including the exact key.
    declared_event = "start" if program.group("event") == "start" else "key"
    triggered = declared_event == event and (
        declared_event == "start" or program.group("key") == key
    )

    return {
        "output": output if triggered else [],
        "frames": frames if triggered else [],
    }