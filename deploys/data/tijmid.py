from pathlib import Path


TIJMID_DIR_RELATIVE = "tijmid"
TIJMID_INSTALL_DIR = Path("/opt/tijmid")
TIJMID_CLI_PATH = Path("/opt/tijmid/dist/cli.mts")
TIJMID_CLI = Path("node /opt/tijmid/dist/cli.mjs")
TIJMID_DATA_DIR = Path("/var/lib/tijmid")
TIJMID_DB_PATH = TIJMID_DATA_DIR / "db.sqlite3"
TIJMID_RUN_DIR = Path("/run") / TIJMID_DIR_RELATIVE
TIJMID_USERNAME = "tijmid"
