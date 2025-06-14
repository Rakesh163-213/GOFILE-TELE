import os
import subprocess
import math
from pyrogram import Client, filters
from pyrogram.types import Message

# 🔐 Replace these
API_ID = int(os.getenv("API_ID")  # Replace with your API ID
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")

# 📁 Directory for downloads
DOWNLOAD_DIR = "./downloader"
SPLIT_SIZE = 1.90 * 1024 * 1024 * 1024  # 1.9 GB in bytes

app = Client("gofile_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

def split_large_file(file_path):
    """Split large video files using ffmpeg by size."""
    output_files = []
    file_size = os.path.getsize(file_path)

    if file_size <= SPLIT_SIZE:
        return [file_path]

    duration_cmd = [
        "ffprobe", "-v", "error", "-show_entries",
        "format=duration", "-of",
        "default=noprint_wrappers=1:nokey=1", file_path
    ]
    total_duration = float(subprocess.check_output(duration_cmd).decode().strip())
    parts = math.ceil(file_size / SPLIT_SIZE)
    duration_per_part = total_duration / parts

    filename_wo_ext = os.path.splitext(os.path.basename(file_path))[0]
    ext = os.path.splitext(file_path)[1]

    for i in range(parts):
        out_file = os.path.join(DOWNLOAD_DIR, f"{filename_wo_ext}_part{i+1}{ext}")
        start_time = i * duration_per_part

        ffmpeg_cmd = [
            "ffmpeg", "-ss", str(start_time), "-i", file_path,
            "-t", str(duration_per_part), "-c", "copy", out_file, "-y"
        ]

        subprocess.run(ffmpeg_cmd)
        output_files.append(out_file)

    os.remove(file_path)
    return output_files

@app.on_message(filters.private & filters.regex(r"https://gofile\.io/d/\w+"))
async def handle_url(client: Client, message: Message):
    url = message.text.strip()
    await message.reply_text(f"🔄 Processing your URL...\n{url}")

    try:
        # 📥 Download from Gofile
        subprocess.run(
            ["python", "gofile_downloader.py", url],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        files = os.listdir(DOWNLOAD_DIR)
        if not files:
            await message.reply_text("⚠️ No files downloaded.")
            return

        for fname in files:
            full_path = os.path.join(DOWNLOAD_DIR, fname)

            if os.path.getsize(full_path) > SPLIT_SIZE:
                await message.reply_text(f"📦 Splitting large file: {fname}")
                split_files = split_large_file(full_path)
            else:
                split_files = [full_path]

            for part in split_files:
                await message.reply_document(part, caption=os.path.basename(part))
                os.remove(part)  # clean after send

    except Exception as e:
        await message.reply_text(f"❌ Error: {str(e)}")

@app.on_message(filters.command("start"))
async def start(client, message):
    await message.reply_text("👋 Send me a Gofile URL, and I’ll download and send you the files. Large files will be split automatically!")

app.run()
