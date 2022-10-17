from io import StringIO
from pyinfra.operations import apt, files, server


apt.packages(packages=["ssh", "libpam-oath"], update=True, _sudo=True)

directives = [
    ("Port", 22),
    ("PubkeyAuthentication", "yes"),
    ("ChallengeResponseAuthentication", "yes"),
    ("PasswordAuthentication", "no"),
]
config = StringIO("\n".join(f"{key} {value}" for key, value in directives))
files.put(config, dest="/etc/ssh/sshd_config.d/00_pyinfra.conf", _sudo=True)

# oauth_seed = 
