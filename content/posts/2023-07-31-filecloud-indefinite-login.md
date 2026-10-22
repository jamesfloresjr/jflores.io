---
title: FileCloud - Login loads indefinitely
date: 2023-07-31 21:04 -0500
categories: [Home Lab, Errors]
tags: [filecloud, login, https]
image: /assets/img/banners/filecloud.png
description: Fix the FileCloud admin login hang by disabling the SECURE_COOKIE setting in cloudconfig.php when HTTPS is not yet configured.
---

## Issue
When logging into the admin console for the first time, the login loads indefinitely.

## Why?
This `TONIDOCLOUD_SECURE_COOKIE` setting is turned on by default without ever being configured for HTTPS. You might've seen this error on your `Extended Checks` page and brushed it off as nothing like I did.

## Fix
Edit the `cloudconfig.php` file located at `/var/www/html/config/`{: .filepath}.

```bash
sudo vi /var/www/html/config/cloudconfig.php
```

Once in the file, press `/` to search, type `SECURE_COOKIE` to find the line, then press the `Enter` key. Press `i` to edit and scroll over to change the `1` to a `0`. Press the `Esc` key and type `:wq` to write to the file. Reload the admin console and try to login again.
