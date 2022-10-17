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
