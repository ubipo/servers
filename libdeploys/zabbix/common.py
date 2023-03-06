from dataclasses import dataclass
from inspect import cleandoc
import pprint


@dataclass
class ApiCredentials:
    username: str
    password: str

    def DEFAULT():
        return ApiCredentials("Admin", "zabbix")


def create_api_call_command(
    credentials: ApiCredentials, endpoint: str, parameters: dict
):
    parameters_str = pprint.pformat(parameters, indent=0)
    single_line_parameters = parameters_str.strip().replace("\n", "\\n")
    python_code = f"""
        from zabbix_api import ZabbixAPI
        import json

        zapi = ZabbixAPI("http://localhost:50158")
        zapi.login("{credentials.username}", "{credentials.password}")
        response = zapi.do_request(zapi.json_obj(
            "{endpoint}",
            {single_line_parameters}
        ))
        print(json.dumps(response["result"]))
    """
    single_line_code = (
        cleandoc(python_code).strip().replace("\n", "\\n").replace("'", "'\\''")
    )
    return f"printf '{single_line_code}' | python3"
