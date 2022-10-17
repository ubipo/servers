from datetime import timedelta, datetime, timezone
import dateparser
from getpass import getpass
from io import StringIO
from pyinfra import host
from pyinfra.operations import files, systemd, server, python
import pyinfra.facts.files as files_facts
from util.ini import create_ini_file
from util.multiline import single_line, unindent

from nginx_http.tls_pfiers_wildcard.consts import *


def setup_renewal():
    credentials_file_exists = host.get_fact(files_facts.File, str(AWS_CREDENTIALS_PATH))

    if not credentials_file_exists:
        aws_credentials_file = create_ini_file(
            {
                "default": {
                    "aws_access_key_id": input("AWS Access Key ID: "),
                    "aws_secret_access_key": getpass("AWS Secret Access Key: "),
                }
            }
        )
        files.put(aws_credentials_file, str(AWS_CREDENTIALS_PATH), mode=700)

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
    """
    )
    files.put(StringIO(renewal_script), str(RENEW_SCRIPT_PATH), mode=755)

    unit_file = create_ini_file(
        {
            "Unit": {
                "Description": f"Renew {CERT_NAME} certificate using certbot",
            },
            "Service": {
                "Type": "oneshot",
                "ExecStart": RENEW_SCRIPT_PATH,
            },
        }
    )
    unit_path = SYSTEMD_FILE_BASE.with_suffix(".service")
    files.put(
        unit_file,
        str(unit_path),
        mode=644,
    )

    timer_file = create_ini_file(
        {
            "Unit": {
                "Description": "Run certbot-pfiers-wildcard on a schedule",
            },
            "Timer": {
                "OnCalendar": "*-*-* 5:00:00",
                "Persistent": "true",
                "RandomizedDelaySec": timedelta(hours=1).seconds,
            },
            "Install": {
                "WantedBy": "timers.target",
            },
        }
    )
    timer_path = SYSTEMD_FILE_BASE.with_suffix(".timer")
    files.put(
        timer_file,
        str(timer_path),
        mode=644,
    )

    systemd.service(timer_path.name, running=True, enabled=True, daemon_reload=True)

    def run_service_if_necessary():
        service_active_state: str = server.shell(
            f"systemctl show -P ActiveState {unit_path.name}"
        ).stdout
        print(f"{service_active_state=}")
        if service_active_state.strip() != "inactive":
            return
        service_exit_timestamp: str = server.shell(
            f"systemctl show -P ExecMainExitTimestamp {unit_path.name}"
        ).stdout
        service_exit_datetime = dateparser.parse(service_exit_timestamp).astimezone(
            timezone.utc
        )
        current_datetime = datetime.now(timezone.utc)
        if service_exit_datetime < (current_datetime - timedelta(days=1)):
            systemd.service(unit_path.name, running=True)

    python.call(function=run_service_if_necessary)
