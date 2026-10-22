---
title: FileCloud - MongoDB connection failed
date: 2023-07-31 15:01 -0500
categories: [Home Lab, Errors]
tags: [proxmox, filecloud, mongodb, avx]
image: /assets/img/banners/filecloud.png
description: Fix the 'Incompatible CPU' error during FileCloud installation. A step-by-step guide to configuring your environment for older CPUs or virtualized setups.
---

## Issue
MongoDB fails to connect because of incompatible CPU.

## Why?
The most likely reason for this error is actually on the installation guide.

![MongoDB AVX Warning](/assets/img/posts/20230731/mongo-avx.png)

Generally, CPUs with the commercial denomination "Core i3/i5/i7" support AVX, whereas "Pentium" and "Celeron" CPUs don't. AMD: Jaguar-based processors and newer. The supported CPUs are listed [here](https://en.wikipedia.org/wiki/Advanced_Vector_Extensions#CPUs_with_AVX).

## Fixes

### Change to host CPU
- SSH into your Proxmox node
- Run the below command to see if your CPU has the AVX instruction set

```bash
lscpu | grep -i avx
```

If the output is like below then your CPU supports AVX. If not, don't fret, I'll explain another solution later.

![AVX Command on Proxmox node](/assets/img/posts/20230731/node-command.gif)

- Go back to your Proxmox web console
- Click on your VM, navigate to `Hardware`, click on `Processors`, and `Edit` the type to `host`

![Change Processors Type](/assets/img/posts/20230731/processors-change-type.gif)

- Shutdown VM and reboot

After that you should be good to go! Go ahead and try to install again.

### Change to a compatible CPU
Instead of changing the processor to `host`, scroll through the list and find a compatible CPU. Shutdown and reboot.
