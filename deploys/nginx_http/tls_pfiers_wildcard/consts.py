from pathlib import PosixPath


CERT_NAME = "pfiers-wildcard"
USER = CERT_NAME
SYNCTHING_FOLDER_ID = f"tls-keys-{CERT_NAME}"
KEYS_DIR = PosixPath(f"/var/tls-keys") / CERT_NAME
KEY_ID_SECRET_KEY = f"awsCertbotKeyId-{CERT_NAME}"
ACCESS_KEY_SECRET_KEY = f"awsCertbotAccessKey-{CERT_NAME}"
RENEW_SCRIPT_PATH = PosixPath(f"/usr/local/bin/renew-{CERT_NAME}.sh")
AWS_CREDENTIALS_PATH = PosixPath(f"/usr/local/etc/aws_credentials-{CERT_NAME}")
SYSTEMD_FILE_BASE = PosixPath(f"/etc/systemd/system/tls-{CERT_NAME}")
NGINX_DIR = PosixPath("/etc/nginx")
SITES_DIR = NGINX_DIR / "sites"
SNIPPETS_DIR = NGINX_DIR / "snippets"
TLS_SNIPPETS_DIR = SNIPPETS_DIR / f"tls-{CERT_NAME}"
SNIPPET_COMMON_PATH = TLS_SNIPPETS_DIR / "common.conf"
SNIPPET_VHOST_PATH = TLS_SNIPPETS_DIR / "vhost.conf"
SNIPPET_CATCHALL_PATH = TLS_SNIPPETS_DIR / "catchall.conf"
