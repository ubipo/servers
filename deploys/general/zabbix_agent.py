from libdeploys import zabbix
from pyinfra import host
from libdeploys import zabbix
from deploys.data.zabbix import *

zabbix.install_agent()
zabbix.configure_agent(
    hostname=host.name,
    server_address_passive=None,
    nbro_passive_agents=0,
    server_address_active=PUBLIC_SERVER_ADDRESS,
)
