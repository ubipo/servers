# Code server https://hub.docker.com/r/codercom/code-server

from operations import yay

yay.packages(["code-server"], update=True, _sudo=True)
