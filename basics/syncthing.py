import deploys.syncthing.operations as syncthing

syncthing.install()
syncthing.enable(username="syncthing", create_user=True)
