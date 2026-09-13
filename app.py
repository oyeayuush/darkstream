import os
import secrets
import sqlite3
import uuid
from datetime import datetime
from pathlib import Path

from flask import Flask, abort, flash, redirect, render_template, request, send_from_directory, url_for
from werkzeug.utils import secure_filename


BASE_DIR = Path(__file__).resolve().parent
UPLOAD_FOLDER = BASE_DIR / "uploads"
DATABASE_PATH = BASE_DIR / "videos.db"
ALLOWED_EXTENSIONS = {"mp4", "webm", "mov", "avi", "mkv"}
MAX_FILE_SIZE = 500 * 1024 * 1024  # 500 MB
MAX_TITLE_LENGTH = 100

app = Flask(__name__)
app.config.update(
    SECRET_KEY=os.environ.get("SECRET_KEY", secrets.token_hex(32)),
    MAX_CONTENT_LENGTH=MAX_FILE_SIZE,
)


def get_connection():
    """Open the local database and return rows with named columns."""
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def initialise_app():
    """Create storage folders and the video table the first time the app runs."""
    UPLOAD_FOLDER.mkdir(exist_ok=True)
    with get_connection() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS videos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                filename TEXT NOT NULL UNIQUE,
                uploaded_at TEXT NOT NULL
            )
            """
        )


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route("/")
def home():
    with get_connection() as connection:
        videos = connection.execute(
            "SELECT id, title, filename, uploaded_at FROM videos ORDER BY id DESC"
        ).fetchall()
    return render_template("index.html", videos=videos)


@app.post("/upload")
def upload_video():
    file = request.files.get("video")
    title = request.form.get("title", "").strip()

    if not title:
        flash("Please give your video a title.")
        return redirect(url_for("home"))
    if len(title) > MAX_TITLE_LENGTH:
        flash(f"Titles must be {MAX_TITLE_LENGTH} characters or fewer.")
        return redirect(url_for("home"))
    if file is None or not file.filename:
        flash("Please choose a video file.")
        return redirect(url_for("home"))
    if not allowed_file(file.filename):
        flash("Only MP4, WebM, MOV, AVI and MKV files are allowed.")
        return redirect(url_for("home"))

    original_name = secure_filename(file.filename)
    extension = original_name.rsplit(".", 1)[1].lower()
    saved_name = f"{uuid.uuid4().hex}.{extension}"
    file.save(UPLOAD_FOLDER / saved_name)

    try:
        with get_connection() as connection:
            connection.execute(
                "INSERT INTO videos (title, filename, uploaded_at) VALUES (?, ?, ?)",
                (title, saved_name, datetime.now().strftime("%d %b %Y, %I:%M %p")),
            )
    except sqlite3.Error:
        (UPLOAD_FOLDER / saved_name).unlink(missing_ok=True)
        flash("The video could not be saved. Please try again.")
        return redirect(url_for("home"))

    flash("Video uploaded successfully.")
    return redirect(url_for("home"))


@app.route("/videos/<path:filename>")
def uploaded_video(filename):
    # Only serve a filename that is present in our database.
    with get_connection() as connection:
        video = connection.execute(
            "SELECT filename FROM videos WHERE filename = ?", (filename,)
        ).fetchone()
    if video is None:
        abort(404)
    return send_from_directory(UPLOAD_FOLDER, video["filename"])


@app.post("/videos/<int:video_id>/delete")
def delete_video(video_id):
    with get_connection() as connection:
        video = connection.execute(
            "SELECT filename FROM videos WHERE id = ?", (video_id,)
        ).fetchone()
        if video is None:
            abort(404)
        connection.execute("DELETE FROM videos WHERE id = ?", (video_id,))

    (UPLOAD_FOLDER / video["filename"]).unlink(missing_ok=True)
    flash("Video deleted.")
    return redirect(url_for("home"))


@app.errorhandler(413)
def file_too_large(_error):
    flash("That video is too large. The maximum upload size is 500 MB.")
    return redirect(url_for("home"))


initialise_app()

if __name__ == "__main__":
    # debug=True is useful while learning. Do not enable it on a public website.
    app.run(debug=True)
