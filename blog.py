#!/usr/bin/env python3
"""Turns the Markdown posts in content/posts/ into the blog's HTML pages.

    python3 blog.py new "My post title"   start a new post (content/posts/YYYY-MM-DD-my-post-title.md)
    python3 blog.py add path/to/post.md   copy a finished post in, then build
    python3 blog.py build                 rebuild every post page, the blog page and the home page's latest post

Posts are Markdown with the same front matter as before (title, date, categories, tags, image,
description; `published: false` keeps one hidden; `video: <YouTube id>` shows that video at the
top of the post instead of the banner image). These work too, as they did on Jekyll:

    > A note.
    {: .prompt-info }                       (or .prompt-tip, .prompt-warning, .prompt-danger)
    `/etc/hosts`{: .filepath}
    ```text ... ```  then  {: file='name.txt'}   on the line after the closing fence
    {% include embed/youtube.html id='VIDEO_ID' %}
    Footnotes: [^1] in the text and [^1]: ... at the bottom.

Needs: pip install markdown-it-py mdit-py-plugins pygments   (see requirements.txt)
"""
import datetime as dt
import html
import json
import math
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SOURCES = ROOT / 'content' / 'posts'
SITE_URL = 'https://jflores.io'
AUTHOR = 'James Flores'
GITHUB = 'jamesfloresjr'

try:
    from markdown_it import MarkdownIt
    from mdit_py_plugins.anchors import anchors_plugin
    from mdit_py_plugins.footnote import footnote_plugin
    from pygments import highlight
    from pygments.formatters import HtmlFormatter
    from pygments.lexers import TextLexer, get_lexer_by_name
    from pygments.util import ClassNotFound
except ImportError:
    sys.exit('blog.py needs a few packages first:  pip install -r requirements.txt')


# ─── Reading posts ──────────────────────────────────────────────────────────

class Post:
    def __init__(self, path, meta, body):
        self.path = path
        self.meta = meta
        self.body = body
        self.title = meta.get('title') or path.stem
        self.date = parse_date(meta.get('date'), path)
        self.slug = re.sub(r'^\d{4}-\d{2}-\d{2}-', '', path.stem)
        self.url = f'/posts/{self.slug}/'
        self.description = meta.get('description', '')
        self.image = meta.get('image') or ''
        self.video = meta.get('video') or ''  # a YouTube video id, shown at the top instead of the banner
        self.tags = as_list(meta.get('tags'))
        self.categories = as_list(meta.get('categories'))
        self.published = str(meta.get('published', 'true')).lower() != 'false'


def as_list(value):
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value] if value else []


def parse_front_matter(text, path):
    """The YAML block at the top: simple `key: value` lines and `[a, b]` lists."""
    if not text.startswith('---'):
        sys.exit(f'{path.name}: missing front matter (a --- block with title, date and so on)')
    end = text.find('\n---', 3)
    if end < 0:
        sys.exit(f'{path.name}: the front matter is never closed with ---')
    meta = {}
    for line in text[3:end].splitlines():
        line = line.split(' #')[0].rstrip()
        if not line.strip() or ':' not in line:
            continue
        key, value = line.split(':', 1)
        value = value.strip()
        if value.startswith('[') and value.endswith(']'):
            meta[key.strip()] = [v.strip().strip('"\'') for v in value[1:-1].split(',') if v.strip()]
        else:
            meta[key.strip()] = value.strip('"\'')
    return meta, text[end + 4:].lstrip('\n')


def parse_date(value, path):
    m = re.match(r'(\d{4}-\d{2}-\d{2})', path.stem)
    if not value and m:
        value = m.group(1)
    for fmt in ('%Y-%m-%d %H:%M %z', '%Y-%m-%d %H:%M:%S %z', '%Y-%m-%d %H:%M', '%Y-%m-%d'):
        try:
            return dt.datetime.strptime(str(value).strip(), fmt)
        except ValueError:
            pass
    sys.exit(f'{path.name}: can\'t read the date "{value}" (use 2025-12-30 or 2025-12-30 06:08 -0500)')


def load_posts():
    posts = []
    for path in sorted(SOURCES.glob('*.md')):
        meta, body = parse_front_matter(path.read_text(encoding='utf-8'), path)
        post = Post(path, meta, body)
        if post.published:
            posts.append(post)
    posts.sort(key=lambda p: p.date.timestamp(), reverse=True)  # newest first
    slugs = [p.slug for p in posts]
    for slug in set(slugs):
        if slugs.count(slug) > 1:
            sys.exit(f'Two posts would both live at /posts/{slug}/; rename one of the files.')
    return posts


# ─── Markdown to HTML ───────────────────────────────────────────────────────

FORMATTER = HtmlFormatter(nowrap=True)


def render_fence(self, tokens, idx, options, env):
    token = tokens[idx]
    info = token.info.strip().split()
    file = next((i[5:] for i in info if i.startswith('file=')), '')
    lang = next((i for i in info if not i.startswith('file=')), '')
    try:
        lexer = get_lexer_by_name(lang) if lang else TextLexer()
    except ClassNotFound:
        lexer = TextLexer()
    code = highlight(token.content, lexer, FORMATTER)
    file_attr = f' file="{html.escape(file)}"' if file else ''
    return (f'<div class="language-{html.escape(lang or "plaintext")} highlighter-rouge"{file_attr}>'
            f'<div class="highlight"><pre class="highlight"><code>{code}</code></pre></div></div>\n')


def markdown_renderer():
    md = (MarkdownIt('commonmark', {'html': True, 'typographer': True})
          .enable(['table', 'strikethrough', 'replacements', 'smartquotes'])
          .use(footnote_plugin)
          .use(anchors_plugin, min_level=2, max_level=4))
    md.add_render_rule('fence', render_fence)
    return md


PROMPT = re.compile(r'^\{:\s*\.(prompt-(?:info|tip|warning|danger))\s*\}\s*$')
FILE_IAL = re.compile(r'^\{:\s*file=["\']([^"\']+)["\']\s*\}\s*$')
INLINE_IAL = re.compile(r'`([^`\n]+)`\{:\s*\.([\w-]+)\s*\}')
YOUTUBE = re.compile(r"^\{%\s*include\s+embed/youtube\.html\s+id=['\"]([\w-]+)['\"]\s*%\}\s*$")


def youtube(video_id, css_class='embed'):
    return (f'<div class="{css_class}"><iframe src="https://www.youtube-nocookie.com/embed/{esc(video_id)}" '
            'title="YouTube video" loading="lazy" allow="accelerometer; clipboard-write; encrypted-media; '
            'gyroscope; picture-in-picture; web-share" referrerpolicy="strict-origin-when-cross-origin" '
            'allowfullscreen></iframe></div>')


def preprocess(body):
    """Turns the Jekyll (kramdown and Liquid) extras into plain Markdown and HTML."""
    out = []
    fence = None        # the open code block's marker (``` or ~~~) and where it starts in out
    last_closed = None  # (where the last code block starts, where it ends) in out
    for line in body.split('\n'):
        stripped = line.strip()
        if fence:
            out.append(line)
            if stripped.startswith(fence[0]) and not stripped.strip(fence[0][0]):
                last_closed, fence = (fence[1], len(out) - 1), None
            continue
        if (m := re.match(r'^\s*(`{3,}|~{3,})', line)):
            fence = (m.group(1), len(out))
            out.append(line)
            continue
        if (m := FILE_IAL.match(stripped)) and last_closed and last_closed[1] == len(out) - 1:
            out[last_closed[0]] = out[last_closed[0]].rstrip() + f' file={m.group(1)}'
            continue
        if (m := PROMPT.match(stripped)):
            # Mark the quote just above, from its first line.
            i = len(out)
            while i > 0 and out[i - 1].lstrip().startswith('>'):
                i -= 1
            out.insert(i, f'<!--{m.group(1)}-->')
            continue
        if (m := YOUTUBE.match(stripped)):
            out += ['', youtube(m.group(1)), '']
            continue
        out.append(INLINE_IAL.sub(lambda m: f'<code class="{m.group(2)}">{html.escape(m.group(1))}</code>', line))
    return '\n'.join(out)


def to_html(md, body):
    out = md.render(preprocess(body))
    out = re.sub(r'<!--(prompt-\w+)-->\s*<blockquote>', r'<blockquote class="\1">', out)
    out = re.sub(r'(<sup class="footnote-ref"><a [^>]*>)\[(\d+)\](</a></sup>)', r'\1\2\3', out)  # 1, not [1]
    out = out.replace('<img ', '<img loading="lazy" ')
    return out


# ─── Pages ──────────────────────────────────────────────────────────────────

def esc(text):
    return html.escape(str(text), quote=True)


def head(title, description, url, image='', kind='website', published=None, schema=None):
    full = f'{SITE_URL}{url}'
    image_url = f'{SITE_URL}{image}' if image.startswith('/') else image
    tags = [
        f'<title>{esc(title)}</title>',
        f'<meta name="description" content="{esc(description)}" />',
        f'<meta name="author" content="{AUTHOR}" />',
        f'<link rel="canonical" href="{full}" />',
        f'<meta property="og:title" content="{esc(title)}" />',
        f'<meta property="og:description" content="{esc(description)}" />',
        f'<meta property="og:url" content="{full}" />',
        f'<meta property="og:site_name" content="{AUTHOR}" />',
        f'<meta property="og:type" content="{kind}" />',
    ]
    if published:
        tags.append(f'<meta property="article:published_time" content="{published}" />')
    if image_url:
        tags += [f'<meta property="og:image" content="{esc(image_url)}" />',
                 '<meta name="twitter:card" content="summary_large_image" />']
    else:
        tags.append('<meta name="twitter:card" content="summary" />')
    if schema:
        tags.append(f'<script type="application/ld+json">{json.dumps(schema)}</script>')
    return '\n  '.join(tags)


def page(title, description, url, body, current_blog=False, **head_args):
    icons = (ROOT / 'index.html').read_text(encoding='utf-8')
    icons = icons[icons.index('<svg width="0" height="0"'):icons.index('</svg>', icons.index('<svg width="0" height="0"')) + 6]
    blog_current = ' aria-current="page"' if current_blog else ''
    return f'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  {head(title, description, url, **head_args)}
  <meta name="theme-color" content="#0e0f11" media="(prefers-color-scheme: dark)">
  <meta name="theme-color" content="#f7f5f0" media="(prefers-color-scheme: light)">
  <link rel="icon" href="/favicon.svg" type="image/svg+xml">

  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600&family=IBM+Plex+Sans:ital,wght@0,400;0,500;0,600;1,400&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="/style.css">
  <script>
    // Before first paint: the theme you picked last time, if any.
    (function () {{
      var root = document.documentElement;
      root.classList.add('js');
      try {{
        var saved = localStorage.getItem('theme');
        if (saved === 'light' || saved === 'dark') root.dataset.theme = saved;
      }} catch (e) {{}}
    }})();
  </script>
</head>
<body>
  {icons}

  <header class="site-header">
    <div class="wrap">
      <a class="monogram" href="/" aria-label="James Flores, home">jf</a>
      <nav class="nav" aria-label="Main">
        <a href="/#projects">Projects</a>
        <a href="/blog/"{blog_current}>Blog</a>
        <a class="hide-sm" href="https://github.com/{GITHUB}" rel="noopener">GitHub</a>
        <button class="theme-toggle" type="button" aria-label="Switch between light and dark">
          <svg class="moon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8z"/></svg>
          <svg class="sun" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/></svg>
        </button>
      </nav>
    </div>
  </header>

  <main id="top">
{body}
  </main>

  <footer class="site-footer">
    <div class="wrap">
      <p>© <span data-year>{dt.date.today().year}</span> {AUTHOR}</p>
      <nav aria-label="Elsewhere">
        <a href="https://github.com/{GITHUB}" rel="noopener">GitHub</a>
        <a href="/blog/">Blog</a>
        <a href="https://www.credly.com/users/james-flores.373c9444/badges" rel="noopener">Credly</a>
      </nav>
    </div>
  </footer>

  <script src="/script.js" defer></script>
</body>
</html>
'''


def tag_list(tags):
    if not tags:
        return ''
    return '<ul class="tags">' + ''.join(f'<li>{esc(t)}</li>' for t in tags) + '</ul>'


def post_page(md, post, older, newer):
    content = to_html(md, post.body)
    words = len(re.sub(r'<[^>]+>', ' ', content).split())
    minutes = max(1, math.ceil(words / 200))
    when = post.date.isoformat()
    meta = [f'<time datetime="{when}">{post.date:%B} {post.date.day}, {post.date:%Y}</time>',
            '<span aria-hidden="true">·</span>', f'<span>{minutes} min read</span>']
    if post.categories:
        meta += ['<span aria-hidden="true">·</span>', f'<span>{esc(", ".join(post.categories))}</span>']
    if post.video:
        banner = '\n    ' + youtube(post.video, 'embed post-banner')
    elif post.image:
        banner = f'\n    <img class="post-banner" src="{esc(post.image)}" alt="" width="1200" height="630">'
    else:
        banner = ''
    nav_older = (f'<a class="prev" href="{older.url}"><span>← Older</span><strong>{esc(older.title)}</strong></a>'
                 if older else '<span></span>')
    nav_newer = (f'<a class="next" href="{newer.url}"><span>Newer →</span><strong>{esc(newer.title)}</strong></a>'
                 if newer else '')
    body = f'''<article class="post">
  <header class="post-head">
    <div class="backdrop" aria-hidden="true"></div>
    <div class="wrap narrow">
      <a class="back" href="/blog/">← All posts</a>
      <h1>{esc(post.title)}</h1>
      <p class="post-meta">
        {' '.join(meta)}
      </p>
      {tag_list(post.tags)}
    </div>
  </header>

  <div class="wrap narrow">{banner}
    <div class="prose">
{content}
    </div>

    <nav class="post-nav" aria-label="More posts">
      {nav_older}
      {nav_newer}
    </nav>
  </div>
</article>'''
    image = post.image if post.image.startswith(('/', 'http')) else ''
    schema = {'@context': 'https://schema.org', '@type': 'BlogPosting', 'headline': post.title,
              'description': post.description, 'datePublished': when, 'url': f'{SITE_URL}{post.url}',
              'author': {'@type': 'Person', 'name': AUTHOR}}
    if image:
        schema['image'] = f'{SITE_URL}{image}' if image.startswith('/') else image
    return page(f'{post.title} | {AUTHOR}', post.description, post.url, body, current_blog=True,
                image=image, kind='article', published=when, schema=schema)


def card(post):
    image = (f'\n          <img src="{esc(post.image)}" alt="" loading="lazy" width="1200" height="630">'
             if post.image else '')
    return f'''      <li class="reveal">
        <a class="post-card" href="{post.url}">{image}
          <div class="post-card-body">
            <time datetime="{post.date.isoformat()}">{post.date:%b} {post.date.day}, {post.date:%Y}</time>
            <h2>{esc(post.title)}</h2>
            <p>{esc(post.description)}</p>
            {tag_list(post.tags)}
          </div>
        </a>
      </li>'''


def blog_page(posts):
    description = 'Guides and fixes from my homelab, for my future self (and you).'
    cards = '\n'.join(card(p) for p in posts)
    body = f'''<section class="blog-head">
  <div class="backdrop" aria-hidden="true"></div>
  <div class="wrap">
    <p class="prompt" aria-hidden="true">~$ ls posts/</p>
    <h1>Blog</h1>
    <p class="lead">Guides and fixes from my homelab: Proxmox, Docker, Home Assistant and the scripts that tie them together. Written for my future self, and for you.</p>
  </div>
</section>

<section class="blog-list">
  <div class="wrap">
    <ol class="cards">
{cards}
    </ol>
  </div>
</section>'''
    return page(f'Blog | {AUTHOR}', description, '/blog/', body, current_blog=True)


def latest_card(post):
    image = (f'\n          <img src="{esc(post.image)}" alt="" loading="lazy" width="1200" height="630">'
             if post.image else '')
    return f'''        <a class="latest-post reveal" href="{post.url}">{image}
          <div class="latest-post-body">
            <time datetime="{post.date.isoformat()}">{post.date:%B} {post.date.day}, {post.date:%Y}</time>
            <h3>{esc(post.title)}</h3>
            <p>{esc(post.description)}</p>
            <span class="read">Read the post →</span>
          </div>
        </a>'''


def update_home(posts):
    path = ROOT / 'index.html'
    text = path.read_text(encoding='utf-8')
    start = re.search(r'<!-- latest-post[^>]*-->', text)
    end = text.find('<!-- /latest-post -->')
    if not start or end < 0:
        print('index.html has no <!-- latest-post --> … <!-- /latest-post --> markers; left it alone.')
        return
    inner = '\n' + latest_card(posts[0]) + '\n        ' if posts else '\n        '
    path.write_text(text[:start.end()] + inner + text[end:], encoding='utf-8')


# ─── Commands ───────────────────────────────────────────────────────────────

def build():
    posts = load_posts()
    md = markdown_renderer()
    for i, post in enumerate(posts):
        newer = posts[i - 1] if i > 0 else None
        older = posts[i + 1] if i + 1 < len(posts) else None
        out = ROOT / 'posts' / post.slug / 'index.html'
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(post_page(md, post, older, newer), encoding='utf-8')
        for src in re.findall(r'\]\((/assets/[^)\s]+)', post.body) + ([post.image] if post.image.startswith('/') else []):
            if not (ROOT / src.lstrip('/')).exists():
                print(f'  warning: {post.path.name} uses {src}, which isn\'t in the site yet')
    (ROOT / 'blog').mkdir(exist_ok=True)
    (ROOT / 'blog' / 'index.html').write_text(blog_page(posts), encoding='utf-8')
    update_home(posts)

    known = {p.slug for p in posts}
    for folder in sorted((ROOT / 'posts').iterdir()):
        if folder.is_dir() and folder.name not in known:
            print(f'  note: posts/{folder.name}/ has no Markdown in content/posts/ any more; delete it if it\'s gone')
    print(f'Built {len(posts)} posts, the blog page and the home page\'s latest post.')


def add(source):
    source = Path(source).expanduser()
    if not source.is_file():
        sys.exit(f'No such file: {source}')
    meta, _ = parse_front_matter(source.read_text(encoding='utf-8'), source)
    name = source.name
    if not re.match(r'^\d{4}-\d{2}-\d{2}-', name):
        date = parse_date(meta.get('date'), source)
        name = f'{date:%Y-%m-%d}-{slugify(source.stem)}.md'
    target = SOURCES / name
    SOURCES.mkdir(parents=True, exist_ok=True)
    if source.resolve() != target.resolve():
        shutil.copyfile(source, target)
        print(f'Added content/posts/{name}')
    build()
    slug = re.sub(r'^\d{4}-\d{2}-\d{2}-', '', target.stem)
    print(f'Your post: /posts/{slug}/')


def slugify(text):
    return re.sub(r'[^a-z0-9]+', '-', text.lower()).strip('-') or 'post'


def new(title):
    now = dt.datetime.now().astimezone()
    path = SOURCES / f'{now:%Y-%m-%d}-{slugify(title)}.md'
    if path.exists():
        sys.exit(f'{path.relative_to(ROOT)} already exists.')
    SOURCES.mkdir(parents=True, exist_ok=True)
    path.write_text(f'''---
title: {title}
date: {now:%Y-%m-%d %H:%M %z}
categories: []
tags: []
image:
description:
published: false
---

Write here. Remove `published: false` above when it's ready, then run `python3 blog.py build`.
''', encoding='utf-8')
    print(f'Started {path.relative_to(ROOT)}')


def main(argv):
    if len(argv) >= 2 and argv[0] == 'add':
        add(argv[1])
    elif len(argv) >= 2 and argv[0] == 'new':
        new(' '.join(argv[1:]))
    elif argv == ['build'] or not argv:
        build()
    else:
        sys.exit(__doc__)


if __name__ == '__main__':
    main(sys.argv[1:])
