# Code server https://hub.docker.com/r/codercom/code-server

import libdeploys.yay as yay

yay.packages(["code-server"], update=True, _sudo=True)
