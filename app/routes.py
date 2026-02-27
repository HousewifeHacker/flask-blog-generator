from flask import render_template, request, redirect, url_for

from app import app

# list
@app.route("/admin")
def admin():
    posts = [{
        "title": "My First Post",
        "slug": "my-first-post",
        "content": "This is the content of my first post.",
        "created_at": "2024-06-01",
        "modified_at": "2024-06-01",
        "published": True
    }]
    return render_template("admin_list.html", posts=posts)

# read, update
@app.route("/posts/<slug>")
def post_detail(slug):
    posts = [{
        "title": "My First Post",
        "slug": "my-first-post",
        "content": "This is the content of my first post.",
        "created_at": "2024-06-01",
        "modified_at": "2024-06-01",
        "published": True
    }]
    post = next((p for p in posts if p["slug"] == slug), None)
    if post:
        if request.method == "POST":
            #TODO: Save post changes
            return redirect(url_for("admin"))
        else:
            return render_template("post_editor.html", post=post)
    else:
        return render_template("404.html"), 404
    
# create
@app.route("/posts/new", methods=["GET", "POST"])
def new_post():
    if request.method == "POST":
        #TODO: Save new post
        return redirect(url_for("admin"))
    else:
        return render_template("post_editor.html", post=None)