# app/generator.py
# This module generates static HTML files from markdown posts.

import os
import markdown
import frontmatter
from flask import render_template

PER_PAGE = 10


def generate_post(post):
    """Renders a single post to HTML using a template."""
    html_content = markdown.markdown(post.content)
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
