from typing import Annotated

from fastapi import Path

RucPathParam = Annotated[
    str,
    Path(
        pattern=r"^[0-9]{11}$",
        description="RUC de 11 dígitos.",
        examples=["20607524476"],
    ),
]
