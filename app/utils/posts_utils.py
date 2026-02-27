import os
import frontmatter
from datetime import datetime

def load_posts(posts_dir):
    """Loads all posts markdown files from the given directory, returning a list of post metadata."""
    posts = []

    for filename in os.listdir(posts_dir):
        if filename.endswith(".md"):
            path = os.path.join(posts_dir, filename)
            post = frontmatter.load(path)

            posts.append({
                "slug": filename.replace(".md", ""),
                "title": post.get("title"),
                "created_at": post.get("created_at"),
                "modified_at": post.get("modified_at"),
                "published": post.get("published", False),
                #"path": path
            })

    posts.sort(key=lambda x: x["created_at"], reverse=True)
    return posts


def load_post(posts_dir, slug):
    path = os.path.join(posts_dir, f"{slug}.md")
    return frontmatter.load(path)


def save_post(posts_dir, slug, title, content, published):
    """Saves a post to a markdown file in the given directory, including metadata."""
    now = datetime.now().isoformat()
    path = os.path.join(posts_dir, f"{slug}.md")

    # If the file already exists, preserve the original created_at date
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

    # write the markdown file with slug as filename and frontmatter metadata
    with open(path, "w") as f:
        f.write(frontmatter.dumps(post))