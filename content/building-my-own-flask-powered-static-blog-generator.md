---
created_at: '2026-02-28T15:38:58.784998'
modified_at: '2026-02-28T17:08:29.495593'
published: true
title: Building My Own Flask-Powered Static Blog Generator
---

I’ve hosted a blog on GitHub Pages for many years, which is awesome in that it’s free, fast, and handles static HTML. But I started wanting a better way to write blog posts locally, without manually editing HTML or copying and pasting Markdown files into the repo.  

So I built a small Flask app to serve as an admin interface for writing, editing, and generating blog content, something like a lightweight CMS, that eventually provides static HTML that can be deployed to GitHub Pages.

### Project Goals

Here were my core goals for this project:

* Run a local web server for writing posts.
* Use a WYSIWYG-style Markdown editor.
* Save drafts without publishing them.
* Generate static HTML pages for GitHub Pages.
* Automatically generate the blog index with pagination.
* Use templates for consistent styling.
* Keep dependencies clean.

I also decided I wasn’t going to host this web app publicly. It only runs on my machine. That meant no containers or cloud hosting were necessary. Poetry was my choice for dependency management instead of a virtual environment + requirements.txt.

### Flask 

While developing my solution, I realized that I didn't need auth. It is my GitHub repo and my local code on my computer, so I still have control over what gets published to my blog. I also realized that I didn't need a database, though I did decide to maintain a json file for more efficient loading and updating on the index pages. Flask is lightweight and flexible by design, yet gives you:

* Routing
* Templates (Jinja2)
* Request handling
* Static file serving

### Handling markdown files

I found the JavaScript Markdown editor EasyMDE for adding WYSIWYG to Markdown. Then I combined that with the Python library python-frontmatter for adding metadata. The resulting markdown file was written to disk with just Python. Remember I was also using index.json as an efficient lookup object. These are the helpers to load and modify the markdown files:

```python

import os
import json
import frontmatter
from datetime import datetime

_INDEX_FILE = "index.json"


def _index_path(posts_dir):
    return os.path.join(posts_dir, _INDEX_FILE)


def _read_index(posts_dir):
    path = _index_path(posts_dir)
    if not os.path.exists(path):
        return {}
    with open(path) as f:
        return json.load(f)
				

def _write_index(posts_dir, index):
    with open(_index_path(posts_dir), "w") as f:
        json.dump(index, f, indent=2, default=str)
				
				
def load_posts(posts_dir):
    """Returns all post metadata from the index, sorted by modified_at descending."""
    index = _read_index(posts_dir)
    posts = [{"slug": slug, **meta} for slug, meta in index.items()]
    posts.sort(key=lambda p: p["modified_at"], reverse=True)
    return posts


def load_post(posts_dir, slug):
    path = os.path.join(posts_dir, f"{slug}.md")
    return frontmatter.load(path)


def save_post(posts_dir, slug, title, content, published):
    """Saves a post to a markdown file and updates the metadata index."""
    now = datetime.now().isoformat()
    path = os.path.join(posts_dir, f"{slug}.md")

    if os.path.exists(path):
        post = frontmatter.load(path)
        created_at = post.get("created_at")
    else:
        created_at = now

    post = frontmatter.Post(content)
    post["title"] = title
    post["published"] = published
    post["created_at"] = created_at
    post["modified_at"] = now

    with open(path, "w") as f:
        f.write(frontmatter.dumps(post))

    index = _read_index(posts_dir)
    index[slug] = {
        "title": title,
        "published": published,
        "created_at": created_at,
        "modified_at": now,
    }
    _write_index(posts_dir, index)
	
```

### Generating HTML

My templates are not pretty yet. They don't have to be because it's just to be useful to me. But you need Jinja2 templates for the different types of pages you want to include. I'm probably going to change my templates and page structure but you can get the idea of how to leverage Flask to generate the HTML from a Jinja2 template. Note that if there's a link between pages, you can't use url_for. url_for generates URLs by looking up registered routes on a live Flask server but we are generating static files that will not have an active Flask server. I decided to generate the entire site because I wanted to make sure all the static pages were updated to use the same templates and template versions: 

```python
import os
import markdown
import frontmatter
from flask import render_template

PER_PAGE = 10


def generate_post(post):
    """Renders a single post to HTML using a template."""
    html_content = markdown.markdown(post.content, extensions=["fenced_code", "codehilite"])
    return render_template(
        "post.html",
        content=html_content,
        title=post.get("title"),
        created_at=post.get("created_at"),
        modified_at=post.get("modified_at")
    )


def generate_site(app):
    """Generates static HTML files for all published posts and paginated index pages."""
    posts_dir = app.config["POSTS_DIR"]
    output_dir = app.config["OUTPUT_DIR"]
    posts_output = os.path.join(output_dir, "generated_posts")

    os.makedirs(posts_output, exist_ok=True)

    with app.app_context():
        published_posts = []

        for filename in os.listdir(posts_dir):
            if filename.endswith(".md"):
                path = os.path.join(posts_dir, filename)
                post = frontmatter.load(path)

                if not post.get("published"):
                    continue

                rendered = generate_post(post)
                slug = filename.replace(".md", "")

                with open(os.path.join(posts_output, f"{slug}.html"), "w") as f:
                    f.write(rendered)

                published_posts.append({
                    "slug": slug,
                    "title": post.get("title"),
                    "created_at": post.get("created_at"),
                    "modified_at": post.get("modified_at"),
                })

        published_posts.sort(key=lambda p: p["modified_at"], reverse=True)

        total_pages = max(1, -(-len(published_posts) // PER_PAGE))

        for page in range(1, total_pages + 1):
            start = (page - 1) * PER_PAGE
            page_posts = published_posts[start:start + PER_PAGE]

            prev_url = None if page == 1 else ("index.html" if page == 2 else f"page-{page - 1}.html")
            next_url = None if page == total_pages else f"page-{page + 1}.html"

            page_html = render_template(
                "index.html",
                posts=page_posts,
                page=page,
                total_pages=total_pages,
                prev_url=prev_url,
                next_url=next_url,
            )

            out_filename = "index.html" if page == 1 else f"page-{page}.html"
            with open(os.path.join(output_dir, out_filename), "w") as f:
                f.write(page_html)

        with open(os.path.join(output_dir, "about.html"), "w") as f:
            f.write(render_template("about.html"))
```

### My admin routes

Then putting those all together to control from my browser with a Flask web application, my routes:

```python
import os
from flask import render_template, request, redirect, url_for, send_from_directory
from slugify import slugify

from app import app
from app.utils.posts_utils import load_posts, load_post, save_post
from app.generator import generate_site


@app.route("/admin")
def admin():
    posts = load_posts(app.config["POSTS_DIR"])
    return render_template("admin_list.html", posts=posts)


@app.route("/posts/<slug>", methods=["GET", "POST"])
def post_detail(slug):
    post = load_post(app.config["POSTS_DIR"], slug)
    if post:
        if request.method == "POST":
            title = request.form.get("title")
            content = request.form.get("content")
            published = request.form.get("published") == "on"
            save_post(app.config["POSTS_DIR"], slug, title, content, published)
            if published:
                generate_site(app)
            return redirect(url_for("admin"))
        else:
            return render_template("post_editor.html", post=post)
    else:
        return render_template("404.html"), 404


@app.route("/posts/new", methods=["GET", "POST"])
def new_post():
    if request.method == "POST":
        title = request.form.get("title")
        content = request.form.get("content")
        published = request.form.get("published") == "on"
        slug = slugify(title)
        save_post(app.config["POSTS_DIR"], slug, title, content, published)
        if published:
            generate_site(app)
        return redirect(url_for("admin"))
    else:
        return render_template("post_editor.html", post=None)
```

### GitHub Pages

GitHub Pages allows two main options for user/organization sites: 

* Serve from / (root)
* Serve from /docs

I chose to generate into docs/, which keeps source files separate from output.


### My Repo

The code is going to be changing but you can find it [on Github](https://github.com/HousewifeHacker/housewifehacker.github.com/tree/master).