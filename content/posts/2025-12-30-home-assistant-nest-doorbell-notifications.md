---
title: Home Assistant - Nest Doorbell Notifications
date: 2025-12-30 06:08 -0500
categories: [Home Lab, Tutorial]
tags: [home assistant, nest]
image: /assets/img/banners/ha_nest.png
video: pCAHibCcpcA
description: I figured out how to embed a GIF from a Nest Doorbell into a Home Assistant notification, even though ChatGPT said it could not be done.
---
## TL;DR

I figured out how to embed a GIF from a Nest Doorbell into a Home Assistant notification, even though ChatGPT said it could not be done.

[Watch the video](https://www.youtube.com/watch?v=pCAHibCcpcA)

## Prerequisites

- A working **Home Assistant** installation
- A configured and functioning **Google Nest Doorbell** integrated into Home Assistant
- Basic understanding of **Home Assistant YAML** (automations, scripts, and notifications)
- Ability to run **shell commands** from Home Assistant (Shell Command integration or equivalent)
- An **Android device** or notification target that supports rich media notifications
- File system access to Home Assistant (SSH, Samba, or File Editor add-on)

## The Problem

I wanted a way to ditch the Google Home app and stop relying on it for notifications, so I decided to just replicate the experience in Home Assistant.

That turned out to be easier said than done.

Google (or rather, Nest) does not play very nicely with screenshots. Every time I tried to grab a snapshot from the doorbell, all I ended up with was a black image and a vague white blur where the video should have been.

Here’s the YAML I originally tried, which *should* have worked but absolutely did not:

```yaml
action:
  - service: camera.snapshot
    target:
      entity_id: camera.doorbell
    data:
      filename: /config/www/doorbell_snapshot.jpg
```

## How It Works

At a high level, the solution relies on stepping outside of Home Assistant’s built-in camera snapshot tools.

Instead of trying to grab a still image directly from the Nest Doorbell, Home Assistant runs a shell command that fetches the most recent Nest event video. That video is then processed with FFmpeg and converted into a GIF.

Because this involves writing and reading media files, a few external directories need to be explicitly allowed in `configuration.yaml` so Home Assistant can access them.

Once the GIF is created, the notification simply points to that file. Since the heavy lifting is already done, Home Assistant treats it like any other image attachment and sends it without issue.

## The Setup

### 1. Locate the Nest event media

First, locate your Nest media directory. Once inside the `nest` folder, navigate to the `event_media` directory. You should see one or more folders with long IDs.

Copy the ID of the folder that corresponds to your doorbell. You will use this in the configuration below.

### 2. Update `configuration.yaml`

Open your Home Assistant configuration file, usually located at:

```
/homeassistant/configuration.yaml
```

Add the following entries, replacing `<id>` with the folder ID you copied earlier.

```yaml
# Custom settings
shell_command:
  make_latest_nest_gif: 'cd "/config/nest/event_media/<id>" && ffmpeg -y -i "$(ls -t *.mp4 2>/dev/null | head -n 1)" -vf "fps=12,scale=640:-1:flags=lanczos" "/config/www/nest_events/latest_nest_event.gif"'

homeassistant:
  allowlist_external_dirs:
    - /config
    - /config/nest/event_media/<id>/
    - /config/www/nest_events/
```

Save the file and restart Home Assistant for the changes to take effect.

### 3. Test the shell command

Before wiring this into an automation, it’s a good idea to test it.

* Go to **Developer Tools**
* Open the **Actions** tab
* Search for `make_latest_nest_gif` (or whatever you named the command)
* Click **Perform action**

If everything worked, you should see a file named `latest_nest_event.gif` in:

```
/config/www/nest_events/
```

### 4. Create the notification script

When creating your notification, add an action to run the shell command first, followed by the notification itself.

Make sure the image path uses `/local` instead of `/config/www`, since Home Assistant exposes that directory via `/local`.

Here’s an example script:

```yaml
sequence:
  - action: shell_command.make_latest_nest_gif
    data: {}
  - action: notify.mobile_app_pixel_9_pro_fold
    data:
      title: 🚪🚶
      message: Someone is at the doorbell.
      data:
        image: /local/nest_events/latest_nest_event.gif
        notification_icon: mdi:doorbell-video
alias: Doorbell Notification (James's Pixel 9 Pro Fold)
description: ""
```

Once saved, your notification will generate a fresh GIF from the most recent Nest event and include it directly in the alert.

## Gotchas

There are a few quirks to be aware of when doing this:

- **Familiar Faces must be disabled**  
  If you have Familiar Faces enabled in the Google Home app, Nest won’t generate an event for people it recognizes. That means your own family or friends might not trigger an event. To make this work reliably, you need to turn off Familiar Faces for everyone in the library you want to capture.

- **Timing can be tricky**  
  The GIF is generated from the latest Nest event video, and sometimes the snapshot happens before the event is fully written. You can try adding a delay in the automation, but in my setup I skipped that and instead triggered the automation directly when:
  - A person is detected, **or**
  - The doorbell is pressed  

  This works most of the time without extra delays, but occasionally the GIF might be blank if the video isn’t ready yet.

- **File permissions / directories**  
  Make sure the directories you allow in `configuration.yaml` match where the GIF is written. Otherwise, Home Assistant can’t access it for notifications.

- **FFmpeg quirks**  
  FFmpeg sometimes complains if there are no MP4 files in the directory yet. It’s harmless, but worth noting if you see errors in your logs.

## Summary

With a bit of ingenuity, you can bypass the Google Home app and send Nest Doorbell notifications directly from Home Assistant with a GIF attached. The key steps involve:

1. Fetching the latest Nest event video using a shell command.
2. Converting the video into a GIF with FFmpeg.
3. Allowing Home Assistant access to the necessary directories.
4. Triggering notifications with the GIF attached, either when the doorbell is pressed or a person is detected.

Keep in mind a few quirks: disable Familiar Faces to ensure all people trigger events, handle timing carefully so the GIF is ready, and check file permissions for smooth operation. Once set up, you get live, rich notifications without relying on the Google Home app.

#### Links

1. [Google Nest Doorbell Integration with Vision LLM](https://www.youtube.com/watch?v=H5_Y1L9kmF8)