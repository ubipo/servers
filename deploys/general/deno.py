# https://deno.land/

import libdeploys.yay as yay

yay.packages(["deno-bin"], update=True, _sudo=True)
