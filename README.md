# ClipForge AI — Render / iPhone Edition

A mobile-friendly Streamlit app that converts uploaded or authorized YouTube videos into vertical short clips. It uses CPU Whisper transcription and simple hook-based scoring, then FFmpeg center-crops and optionally burns word captions. This is a starter app, **not** a full Crayo.ai equivalent.

## Deploy from an iPhone (no PC)

1. Create a free GitHub account at https://github.com and sign in using Safari. Create a **public or private** repository named `clipforge-ai`.
2. Download and unzip this project ZIP on your iPhone using the Files app.
3. In your GitHub repository, tap **Add file → Upload files** (you may need Safari's **Request Desktop Website**). Upload the *contents* of the unzipped folder — `app.py`, `Dockerfile`, `requirements.txt`, and `render.yaml` — to the repository root, not the enclosing folder. Commit the changes. If GitHub's mobile upload interface does not work, use GitHub's web file editor to create each file.
4. Sign up at https://dashboard.render.com using GitHub. Choose **New → Blueprint** and connect the repository. Render reads `render.yaml` to create a free Docker web service. If Blueprint is not available, choose **New → Web Service**, select the repo, choose **Docker**, and select the Free plan if offered.
5. Wait for deployment and open the `.onrender.com` URL on your iPhone. In Safari, tap **Share → Add to Home Screen** for app-like access.
6. Upload a short video or paste a permitted YouTube URL, select clip length and count, then tap **Generate clips**. Preview and download each MP4.

## Free tier realities

- Render's free instance availability, memory, build limits and sleep behavior can change; confirm the Free plan is available in your account before deploying.
- Start with 1–3 minute source videos, 1–2 clips, and the `tiny` model. This version refuses source videos over 15 minutes or uploaded files over 150 MB. Render can run out of memory even below these limits.
- YouTube downloads can fail because of YouTube restrictions, sign-in requirements or IP blocks. Uploaded videos are the most reliable input.
- Outputs are held temporarily in the running app session and can disappear after app sleep/restart. Download immediately. Files are processed on the server; do not upload confidential content.
- The app does not automatically post to social media, perform face tracking, or predict virality. Ranking is a simple speech-hook heuristic.
- Only download, clip, and publish content for which you have the necessary rights.
