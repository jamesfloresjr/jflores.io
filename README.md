# jflores.io

Personal portfolio and blog of James Flores. Plain HTML, CSS and a little JavaScript, with no build step on the server: GitHub Pages serves the files as they are.

Preview it with `python3 -m http.server 8000` in this folder, then open http://localhost:8000.

## Blog posts

Posts are written in Markdown in `content/posts/`, and `blog.py` turns them into the HTML pages in `posts/`. It also rebuilds `blog/index.html`, the "Older"/"Newer" links between posts, and the latest post on the home page.

One-time setup:

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
```

Then:

```bash
.venv/bin/python blog.py new "My post title"     # starts content/posts/YYYY-MM-DD-my-post-title.md as a draft
.venv/bin/python blog.py add ~/Downloads/post.md # copies a finished post in and builds
.venv/bin/python blog.py build                   # rebuilds everything after editing a post
```

Commit the generated files along with the Markdown and push.

### Front matter

```yaml
---
title: Proxmox - Creating a Ubuntu Server template
date: 2023-08-02 08:44 -0500
categories: [Home Lab, Tutorial]
tags: [proxmox, linux]
image: /assets/img/banners/proxmox.png   # optional, 1200 × 630
video: pCAHibCcpcA                       # optional YouTube id: shown at the top instead of the image
description: One or two sentences, shown on the blog page and in search results.
published: false                         # optional; leave it out to publish
---
```

The file name sets the address: `2023-08-02-proxmox-template.md` is published at `/posts/proxmox-template/`. Images go in `assets/img/`; `blog.py` warns about any a post uses that aren't there yet.

### Extras that work in posts

- Callouts: `{: .prompt-info }` (or `.prompt-tip`, `.prompt-warning`, `.prompt-danger`) on the line after a `>` quote.
- File paths: `` `/etc/hosts`{: .filepath} ``
- A file name above a code block: `{: file='diceware.txt'}` on the line after the closing fence.
- YouTube: `{% include embed/youtube.html id='VIDEO_ID' %}`
- Footnotes: `[^1]` in the text and `[^1]: …` at the bottom.
- Tables, and code highlighting for any language name after the opening fence.
