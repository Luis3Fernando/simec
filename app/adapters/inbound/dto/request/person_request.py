from typing import Annotated

from fastapi import Path

DniPathParam = Annotated[
    str,
    Path(
        pattern=r"^[0-9]{8}$",
        description="DNI de 8 dígitos.",
        examples=["44900952"],
    ),
]
