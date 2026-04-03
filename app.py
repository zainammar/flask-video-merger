import os
from flask import Flask, render_template, request, jsonify, send_file
from werkzeug.utils import secure_filename
from moviepy.editor import VideoFileClip, concatenate_videoclips

app = Flask(__name__)

UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'output'

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

progress = {"percent": 0, "status": "idle", "filename": ""}


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/upload', methods=['POST'])
def upload():
    global progress

    files = request.files.getlist('videos')

    if not files:
        return jsonify({"error": "No files uploaded"}), 400

    clips = []
    progress = {"percent": 0, "status": "processing", "filename": ""}

    total = len(files)

    for i, file in enumerate(files):
        filename = secure_filename(file.filename)
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)

        # Trim values
        start = float(request.form.get(f'start_{i}', 0))
        end = float(request.form.get(f'end_{i}', 0))

        clip = VideoFileClip(filepath)

        if end <= 0 or end > clip.duration:
            end = clip.duration

        if start < 0:
            start = 0

        if start >= end:
            start = 0
            end = clip.duration

        trimmed_clip = clip.subclip(start, end)
        clips.append(trimmed_clip)

        progress["filename"] = filename
        progress["percent"] = int((i + 1) / total * 50)

    # Merge
    final_clip = concatenate_videoclips(clips, method="compose")

    output_path = os.path.join(OUTPUT_FOLDER, 'merged_video.mp4')

    final_clip.write_videofile(
        output_path,
        codec='libx264',
        audio_codec='aac'
    )

    for clip in clips:
        clip.close()

    final_clip.close()

    progress["percent"] = 100
    progress["status"] = "done"

    return jsonify({"download": "/download"})


@app.route('/progress')
def get_progress():
    return jsonify(progress)


@app.route('/download')
def download():
    return send_file(os.path.join(OUTPUT_FOLDER, 'merged_video.mp4'), as_attachment=True)


if __name__ == '__main__':
    app.run(debug=True)