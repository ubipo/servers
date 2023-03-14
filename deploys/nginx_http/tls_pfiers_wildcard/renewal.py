from datetime import timedelta, datetime, timezone
import dateparser
from getpass import getpass
from io import StringIO
from pyinfra import host
from pyinfra.operations import files, systemd, server, python, npm
import pyinfra.facts.files as files_facts
from pyinfra.api import DeployError
import libdeploys.command as command
from util.ini import IniConfig
from util.multiline import single_line, unindent

from libdeploys.syncthing.facts import Config
from nginx_http.tls_pfiers_wildcard.consts import *
from util.secrets import get_secrets


def setup_leader_renewal():
    secrets = get_secrets()
    docker_exists = host.get_fact(command.Exists, "docker")
    if not docker_exists:
        raise DeployError("docker is not installed")

    credentials_file_exists = host.get_fact(files_facts.File, str(AWS_CREDENTIALS_PATH))

    if not credentials_file_exists:
        key_id = secrets[KEY_ID_SECRET_KEY]
        access_key = secrets[ACCESS_KEY_SECRET_KEY]
        if len(str(key_id or "")) == 0:
            raise DeployError(f"Secret {KEY_ID_SECRET_KEY} is not set")
        if len(str(access_key or "")) == 0:
            raise DeployError(f"Secret {ACCESS_KEY_SECRET_KEY} is not set")
        aws_credentials_file = IniConfig.from_section_directives(
            (
                "default",
                [
                    ("aws_access_key_id", key_id),
                    ("aws_secret_access_key", access_key),
                ],
            )
        )
        files.put(
            aws_credentials_file.to_string_io(), str(AWS_CREDENTIALS_PATH), mode=700
        )

    certbot_out_dir = PosixPath(f"/tmp/{CERT_NAME}-certbot-out")
    certbot_docker_command = single_line(
        f"""
        docker run --rm --name certbot
        -v {str(AWS_CREDENTIALS_PATH)}:/root/.aws/credentials:ro
        -v {str(certbot_out_dir)}:/etc/letsencrypt
        certbot/dns-route53
        certonly --agree-tos -n --email pieter@pfiers.net
        -a dns-route53 --cert-name {CERT_NAME}
        --expand
        -d '*.pfiers.net'
        """
    )
    docker_host_certs_dir = certbot_out_dir / "live" / CERT_NAME
    cert_files = ["cert.pem", "chain.pem", "fullchain.pem", "privkey.pem"]
    cert_files_str = " ".join(
        str(docker_host_certs_dir / cert_file) for cert_file in cert_files
    )
    renewal_script = unindent(
        f"""
        #!/bin/bash
        set -euxo pipefail
        mkdir -p {certbot_out_dir}
        chmod 700 {certbot_out_dir}
        {certbot_docker_command}
        cp {cert_files_str} {str(KEYS_DIR).removesuffix("/")}/
        chmod -R 750 {str(KEYS_DIR)}
        chgrp -R syncthing {str(KEYS_DIR)}
        rm -r {certbot_out_dir}
        systemctl reload nginx
        """
    )
    files.put(StringIO(renewal_script), str(RENEW_SCRIPT_PATH), mode=755)

    unit_file = IniConfig.from_section_directives(
        ("Unit", [("Description", f"Renew {CERT_NAME} certificate using certbot")]),
        (
            "Service",
            [
                ("Type", "oneshot"),
                ("ExecStart", RENEW_SCRIPT_PATH),
            ],
        ),
    )
    unit_path = SYSTEMD_FILE_BASE.with_suffix(".service")
    files.put(
        unit_file.to_string_io(),
        str(unit_path),
        mode=644,
    )

    timer_file = IniConfig.from_section_directives(
        (
            "Unit",
            [
                ("Description", f"Renew {CERT_NAME} every week"),
            ],
        ),
        (
            "Timer",
            [
                (
                    "OnCalendar",
                    "Mon *-*-* 5:00:00",
                ),  # Max 5 requests per week (168 hours, https://letsencrypt.org/docs/rate-limits/)
                ("Persistent", "true"),
                ("RandomizedDelaySec", timedelta(hours=1).seconds),
            ],
        ),
        (
            "Install",
            [
                ("WantedBy", "timers.target"),
            ],
        ),
    )
    timer_path = SYSTEMD_FILE_BASE.with_suffix(".timer")
    files.put(
        timer_file.to_string_io(),
        str(timer_path),
        mode=644,
    )

    systemd.service(timer_path.name, running=True, enabled=True, daemon_reload=True)

    def run_service_if_necessary():
        service_active_state: str = server.shell(
            f"systemctl show -P ActiveState {unit_path.name}"
        ).stdout.strip()
        print(f"{service_active_state=}")
        if service_active_state == "inactive":
            service_exit_timestamp: str = server.shell(
                f"systemctl show -P ExecMainExitTimestamp {unit_path.name}"
            ).stdout
            service_exit_datetime = dateparser.parse(service_exit_timestamp)
            if service_exit_datetime is not None:
                service_exit_datetime = service_exit_datetime.astimezone(timezone.utc)
                current_datetime = datetime.now(timezone.utc)
                if service_exit_datetime > (current_datetime - timedelta(days=1)):
                    return
        elif service_active_state != "failed":
            return
        systemd.service(unit_path.name, running=True)

    python.call(function=run_service_if_necessary)


def setup_follower_renewal():
    # Follower nodes get the certs from the leader node over syncthing
    # => reload nginx when the certs change using
    # https://github.com/terminalnetwork/syncthing-hooks
    npm.packages(packages=["syncthing-hooks@~0.4"], latest=False, directory=None)

    syncthing_config = host.get_fact(Config, "syncthing")
    events_url = f"{syncthing_config.base_url}/rest/events"
    unit_file = IniConfig.from_section_directives(
        (
            "Unit",
            [
                (
                    "Description",
                    f"Watch {CERT_NAME} certificates for changes and reload nginx",
                ),
            ],
        ),
        (
            "Service",
            [
                ("Type", "simple"),
                ("Environment", f"API_KEY={syncthing_config.api_key}"),
                ("Environment", f"ST_URL={events_url}"),
                ("ExecStart", "syncthing-hooks"),
            ],
        ),
        ("Install", [("WantedBy", "multi-user.target")]),
    )
    unit_path = SYSTEMD_FILE_BASE.with_suffix(".service")
    files.put(
        unit_file.to_string_io(),
        str(unit_path),
        mode=644,
    )
    systemd.service(unit_path.name, running=True, enabled=True, daemon_reload=True)

    reload_script = unindent(
        f"""
        #!/bin/bash
        set -euxo pipefail
        systemctl reload nginx
        """
    )
    files.put(
        StringIO(reload_script),
        # Run 5 minutes after latest change (debounce)
        f"/root/.syncthing-hooks/{SYNCTHING_FOLDER_ID}-5m",
        mode=755,
    )
