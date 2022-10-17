from dataclasses import dataclass, field
import json
from pyinfra.api import DeployError


@dataclass(frozen=True)
class SyncthingConfig:
    raw: dict
    api_key: str = field(init=False)
    base_url: str = field(init=False)

    def __post_init__(self):
        object.__setattr__(self, "api_key", self.raw["gui"]["apiKey"])
        object.__setattr__(self, "base_url", f"http://{self.raw['gui']['address']}")

    def __repr__(self):
        return f"SyncthingConfig(<data omitted>)"


def create_request_curl_command(
    endpoint: str,
    method: str = "GET",
    data: dict = None,
    config: SyncthingConfig = None,
    base_url: str | None = None,
    api_key: str | None = None,
    non_error_status_codes: list[int] | None = None,
):
    if base_url is None:
        if config is None:
            raise DeployError("Must provide either config or base_url and api_key")

        api_key = config.api_key
        base_url = config.base_url
    elif api_key is None:
        raise DeployError("Must provide either both base_url and api_key or neither")

    curl_command = (
        f"output=$(curl -s -i -X {method}"
        f" -H 'X-API-Key: {api_key}'"
        f" -H 'Accept: application/json'"
    )

    if data is not None:
        data_str = json.dumps(data)
        curl_command += f" -d '{data_str}'"

    curl_command += f" {base_url}/rest/{endpoint}"
    curl_command += ")"

    print_output_command = f'echo "$output"'

    status_command = f'status_code=$(echo "$output" | head -n 1 | cut -d " " -f 2)'

    if non_error_status_codes is None:
        non_error_status_codes = [200]

    expressions = [
        f"$status_code -eq {status_code}" for status_code in non_error_status_codes
    ]
    error_command = f"[ {' -o '.join(expressions)} ]"

    return "; ".join(
        [curl_command, print_output_command, status_command, error_command]
    )
