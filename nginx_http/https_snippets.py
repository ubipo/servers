# From: https://ssl-config.mozilla.org/#server=nginx&config=intermediate

from io import StringIO
from pyinfra.operations import files
from nginx_http.tls_pfiers_wildcard.consts import *

from util.nginx import create_nginx_config

files.directory(str(KEYS_DIR), mode=700)

dhparam_path = KEYS_DIR / "ffdhe2048.pem"
files.download(
    "https://raw.githubusercontent.com/mozilla/ssl-config-generator/master/docs/ffdhe2048.txt",
    str(dhparam_path),
)

snippet_common = create_nginx_config(
    ("ssl_certificate", KEYS_DIR / "fullchain.pem"),
    ("ssl_certificate_key", KEYS_DIR / "privkey.pem"),
    ("ssl_dhparam", dhparam_path),
    # Session
    ("ssl_session_timeout", "1d"),
    ("ssl_session_cache", "shared:MozSSL:10m"),  # about 40000 sessions
    ("ssl_session_tickets", False),
    # Ciphers
    ("ssl_protocols", "TLSv1.2 TLSv1.3"),
    (
        "ssl_ciphers",
        "ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-CHACHA20-POLY1305:DHE-RSA-AES128-GCM-SHA256:DHE-RSA-AES256-GCM-SHA384",
    ),
    ("ssl_prefer_server_ciphers", False),
    # HSTS
    ("add_header", 'Strict-Transport-Security "max-age=63072000" always'),
    # OCSP stapling
    ("ssl_stapling", True),
    ("ssl_stapling_verify", True),
    # Verify chain of trust of OCSP response using Root CA and Intermediate certs
    ("ssl_trusted_certificate", KEYS_DIR / "chain.pem"),
)
files.put(StringIO(snippet_common), str(SNIPPET_COMMON_PATH))

snippet_vhost = create_nginx_config(
    ("listen", "[::]:443 ssl http2"),
    ("listen", "443 ssl http2"),
    ("include", SNIPPET_COMMON_PATH),
)
files.put(StringIO(snippet_vhost), str(SNIPPET_VHOST_PATH))

snippet_catchall = create_nginx_config(
    ("listen", "[::]:443 default_server ssl http2 ipv6only=on"),
    ("listen", "443 default_server ssl http2"),
    ("include", SNIPPET_COMMON_PATH),
)
files.put(StringIO(snippet_catchall), str(SNIPPET_CATCHALL_PATH))
