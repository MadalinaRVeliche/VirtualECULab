from typing import Annotated

from pydantic import BaseModel, Field

CanByte = Annotated[int, Field(strict=True, ge=0, le=255)]


class StandardCanFrame(BaseModel):
    identifier: int = Field(strict=True, ge=0, le=0x7FF)
    data: list[CanByte] = Field(max_length=8)

    def preview(self):
        return {
            "format": "Classical CAN standard data frame",
            "identifier": self.identifier,
            "identifier_hex": f"0x{self.identifier:03X}",
            "dlc": len(self.data),
            "data": self.data,
            "data_hex": " ".join(f"{byte:02X}" for byte in self.data),
        }
