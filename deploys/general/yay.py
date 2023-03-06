import sys
from pathlib import Path

sys.path.append(Path(__file__).absolute().parent)
sys.path.append(Path(__file__).absolute().parent.parent)

from libdeploys import yay

yay.install(_sudo=True)
