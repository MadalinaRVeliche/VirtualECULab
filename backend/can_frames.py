from typing import Annotated

from pydantic import BaseModel, Field

# Validate each payload element as an integer byte without coercing input.
CanByte = Annotated[int, Field(strict=True, ge=0, le=255)]


class StandardCanFrame(BaseModel):
    # The simulator models Classical CAN standard data frames:
    # an 11-bit identifier and zero to eight payload bytes.
    identifier: int = Field(strict=True, ge=0, le=0x7FF)
    data: list[CanByte] = Field(max_length=8)

    def preview(self):
        # Use the payload length as the DLC for this frame format.
        # Keep numeric values for decoding and comparisons, and add
        # hexadecimal strings for display.
        return {
            "format": "Classical CAN standard data frame",
            "identifier": self.identifier,
            "identifier_hex": f"0x{self.identifier:03X}",
            "dlc": len(self.data),
            "data": self.data,
            "data_hex": " ".join(f"{byte:02X}" for byte in self.data),
        }