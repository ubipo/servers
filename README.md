# Personal Server Infrastructure 🏗️

Infrastructure-as-code configuration for my personal servers using the excellent
[pyinfra](https://pyinfra.com/). 

My hardware setup consists of an [Odroid H2](https://www.odroid.co.uk/ODroid-H2)
at home (named *Cannelloni*) and a cpx11 VPS at
[Hetzner](https://www.hetzner.com/) called *Linguine*. Cannelloni runs all my
self-hosted services (and is accessible from the LAN or VPN) while Linguine just
acts as a reverse proxy to Cannelloni. This means I could theoretically run my
home server off public library WiFi and still have access to it from anywhere.
Conversely, if the internet goes down I can still access my services
locally. It's a win-win :).

This repo is mostly for my own reference, though I hope you might find it useful
as well.

## Setup

```sh
# Create a virtualenv and install dependencies
python3 -m venv env-pyinfra
source env-pyinfra/bin/activate
pip install -r requirements.txt
```

## Provisioning

To provision all hosts with my [*Tijmid* identity server](https://github.com/ubipo/tijmid):
```sh
pyinfra inventory.py deploys/tijmid.py
```

## Structure

### Libdeploys

`libdeploys` contains a collection of reusable deploy operations and facts, 
organized by service. For example, `libdeploys/docker` contains `operations.py`
for installing Docker and `facts.py` for detecting the Docker version.

### Deploys

`deploys` contains deploy scripts, such as `deploys/hostnames.py` which sets
the hostname and FQDN of hosts in the inventory.

While only loosely categorized, `deploys/apps` contains deploys for self-hosted
apps such as [Zabbix](https://www.zabbix.com/) and
[Baserow](https://baserow.io/), while more general deploys like docker and ssh
configuration are stored in `deploys/general`. Configurable data and constants
used during deployment are stored in `deploys/data`.

### Util

Utilities for use by both `libdeploys` and `deploys`. `util/ini.py` is a .ini
file parser and generator.
