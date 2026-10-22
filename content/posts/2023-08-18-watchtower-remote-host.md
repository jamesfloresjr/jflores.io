---
title: Watchtower - Monitor remote hosts
date: 2023-08-18 15:08 -0500
categories: [Home Lab, Tutorial]
tags: [portainer, docker, watchtower, ubuntu server]
image: /assets/img/banners/watchtower.png
description: To have watchtower monitor a remote Docker endpoint you first need to enable TCP port 2375 for external connection.
---

## TL;DR
To have watchtower monitor a remote Docker endpoint you first need to enable TCP port 2375 for external connection.

## Remote Host
On the remote host, follow these steps:

- Run `vi /etc/docker/daemon.json` and paste:

```json
{"hosts": ["tcp://0.0.0.0:2375", "unix:///var/run/docker.sock"]}
```

- Run `systemctl edit docker.service` and paste lines 4-6:

```bash
### Editing /etc/systemd/system/docker.service.d/override.conf
### Anything between here and the comment below will become the new contents of the file

[Service]
 ExecStart=
 ExecStart=/usr/bin/dockerd

### Lines below this comment will be discarded
```

- Reload the systemd daemon and restart docker:

```bash
systemctl daemon-reload
systemctl restart docker.service
```

## Local Host
On the local host, simply run the watchtower container and specify the remote host:

```bash
docker run -d \
  --name watchtower \
  -e DOCKER_HOST="tcp://10.0.1.2:2375" \
  containrrr/watchtower
```

## Summary
I had to dig for this on my own as the watchtower documentation just shows the last command. On their page it doesn't mention at all about enabling the port. In hindsight, I guess it does make sense.

#### Links

1. [Enable TCP port 2375 for external connection to Docker](https://gist.github.com/styblope/dc55e0ad2a9848f2cc3307d4819d819f)
2. [Watchtower - Remote hosts](https://containrrr.dev/watchtower/remote-hosts/)
