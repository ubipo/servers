from pyinfra.api import FactBase, DeployError
from util.ini import IniConfig


class Config(FactBase):
    def command(self, config_number: int, save_before_read: bool = True):
        command = ""
        if save_before_read:
            command += (
                f'live_conf="$(wg showconf wg{config_number})"; '
                + f'[ $? -eq 0 ] && echo "$live_conf" > /etc/wireguard/wg{config_number}.conf; '
            )

        command += f'cat /etc/wireguard/wg{config_number}.conf 2>&1; printf "\\n$?"'
        return command

    def process(self, output: list[str]):
        exit_code = int(output[-1])
        content = "\n".join(output[:-1])
        if exit_code != 0:
            if "No such file or directory" in content:
                return None
            raise DeployError(f"Error reading config: {content}")
        return IniConfig().from_string(content)


class PublicKey(FactBase):
    def command(self, config_number: int):
        return f"sed -n 's/^PrivateKey\s*=\s*\(\S*\)$/\\1/p' /etc/wireguard/wg{config_number}.conf | wg pubkey"


class NewPrivateKey(FactBase):
    def command(self):
        return "wg genkey"
