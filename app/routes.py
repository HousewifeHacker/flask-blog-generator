from flask import render_template, request, redirect, url_for
from slugify import slugify

from app import app
from app.utils.posts_utils import load_posts, load_post, save_post

# list
@app.route("/admin")
def admin():
    """Admin dashboard showing list of markdown files."""
    posts = load_posts(app.config["POSTS_DIR"])
    return render_template("admin_list.html", posts=posts)

# read, update
@app.route("/posts/<slug>")
def post_detail(slug):
    post = load_post(app.config["POSTS_DIR"], slug)
    if post:
        if request.method == "POST":
            title = request.form.get("title")
            content = request.form.get("content")
            published = request.form.get("published") == "on"
            save_post(app.config["POSTS_DIR"], slug, title, content, published)
            return redirect(url_for("admin"))
        else:
            return render_template("post_editor.html", post=post)
    else:
        return render_template("404.html"), 404
    
# create
@app.route("/posts/new", methods=["GET", "POST"])
def new_post():
    if request.method == "POST":
        title = request.form.get("title")
        content = request.form.get("content")
        published = request.form.get("published") == "on"
        slug = slugify(title)
        save_post(app.config["POSTS_DIR"], slug, title, content, published)
        return redirect(url_for("admin"))
    else:
        return render_template("post_editor.html", post=None)