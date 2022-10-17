from io import StringIO
from pyinfra import host
from pyinfra.operations import pacman, server, files
from pyinfra.api import operation
from pyinfra.facts import files as files_facts
from pyinfra.operations.util.packaging import ensure_packages

from facts.yay import YayPackages, YayUnpackGroup


@operation
def install():
    """Installs yay itself"""

    # sudo_kwargs = {"_sudo": True} if kwargs.get("_sudo") else {}
    yield from pacman.packages(["git", "base-devel", "go"], update=True)

    yield from server.user("makepkg", system=True)

    yield from files.directory("/tmp/yay", present=False)

    if host.get_fact(files_facts.File, "/tmp/yay"):
        yield f"cd /tmp/yay && sudo -u makepkg git pull"
    else:
        yield f"sudo -u makepkg git clone https://aur.archlinux.org/yay.git /tmp/yay"

    yield f"cd /tmp/yay && sudo -u makepkg makepkg -s --noconfirm"

    yield f"pacman -U --noconfirm /tmp/yay/yay-*.pkg.tar.*"

    yield from server.user("yay", system=True)

    yield from files.put(
        StringIO("yay ALL = NOPASSWD: /usr/bin/pacman"), "/etc/sudoers.d/yay"
    )


@operation(is_idempotent=False)
def upgrade():
    """
    Upgrades all pacman packages.
    """

    yield "pacman --noconfirm -Su"


@operation(is_idempotent=False)
def update():
    """
    Updates pacman repositories.
    """

    yield "pacman -Sy"


@operation
def packages(
    packages=[],
    present=True,
    update=False,
    upgrade=False,
):
    """
    Add/remove yay packages.

    + packages: list of packages to ensure
    + present: whether the packages should be installed
    + update: run ``yay -Sy`` before installing packages
    + upgrade: run ``yay -Su`` before installing packages

    Versions:
        Package versions can be pinned like yay: ``<pkg>=<version>``.

    **Example:**

    .. code:: python

        yay.packages(
            name="Install deno",
            packages=["deno"],
            update=True,
        )
    """

    if update:
        yield from pacman.update()

    if upgrade:
        yield from pacman.upgrade()

    yield from ensure_packages(
        host,
        packages,
        host.get_fact(YayPackages),
        present,
        install_command="sudo -u yay yay --noconfirm -S",
        uninstall_command="sudo -u yay yay --noconfirm -R",
        expand_package_fact=lambda package: host.get_fact(
            YayUnpackGroup,
            name=package,
        ),
    )
