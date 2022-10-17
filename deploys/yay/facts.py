from pyinfra.api import FactBase

from pyinfra.facts.util.packaging import parse_packages

YAY_REGEX = r"^([0-9a-zA-Z\-]+)\s([0-9\._+a-z\-]+)"


class YayUnpackGroup(FactBase):
    """
    Returns a list of actual packages belonging to the provided package name,
    expanding groups or virtual packages.

    .. code:: python

        [
            "package_name",
        ]
    """

    requires_command = "yay"

    default = list

    def command(self, name):
        # Accept failure here (|| true) for invalid/unknown packages
        return 'yay -S --print-format "%n" {0} || true'.format(name)

    def process(self, output):
        return output


class YayPackages(FactBase):
    """
    Returns a dict of installed yay packages:

    .. code:: python

        {
            "package_name": ["version"],
        }
    """

    command = "yay -Q"
    requires_command = "yay"

    default = dict

    def process(self, output):
        return parse_packages(YAY_REGEX, output)
