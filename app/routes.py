import os
from flask import render_template, request, redirect, url_for, send_from_directory
from slugify import slugify

from app import app
from app.utils.posts_utils import load_posts, load_post, save_post
from app.generator import generate_site


@app.route("/preview/<slug>")
def preview(slug):
    output_dir = os.path.abspath(os.path.join(app.root_path, "..", app.config["OUTPUT_DIR"], "generated_posts"))
    return send_from_directory(output_dir, f"{slug}.html")


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
