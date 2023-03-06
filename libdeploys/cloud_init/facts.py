from pyinfra.api import FactBase
from enum import Enum


class StatusValue(Enum):
    NOT_INSTALLED = 0
    DONE = 1
    DISABLED = 2
    UNKNOWN = 3


class Status(FactBase):
    def command(self):
        return "command -v cloud-init; cloud-init status || true"

    def process(self, output: list[str]):
        if len(output) == 0:
            return StatusValue.NOT_INSTALLED
        status_str = output[1].split(":", 1)[1].strip()
        if status_str == "done":
            return StatusValue.DONE
        if status_str == "disabled":
            return StatusValue.DISABLED
        return StatusValue.UNKNOWN
