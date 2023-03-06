import libdeploys.syncthing as syncthing

syncthing.install()
syncthing.enable(username="syncthing", create_user=True)
