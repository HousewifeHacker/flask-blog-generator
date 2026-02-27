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
