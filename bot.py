import os
import subprocess
from pyrogram import Client, filters
from pyrogram.types import Message

# 🔐 Credentials#
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")
# 📁 Download directory
DOWNLOAD_DIR = "/downloader"

# 🚀 Bot setup
app = Client("gofile_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# 🧠 Filter messages with Gofile URLs
@app.on_message(filters.private & filters.regex(r"https://gofile\.io/d/\w+"))
async def handle_gofile(client: Client, message: Message):
    url = message.text.strip()
    await message.reply_text(f"🔄 Downloading from Gofile...\n📥 URL: {url}")

    try:
        # ✅ Run the external downloader
        result = subprocess.run(
            ["python", "gofile_downloader.py", url],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        if result.returncode != 0:
            await message.reply_text(f"❌ Error downloading:\n{result.stderr}")
            return

        # 📤 Upload all files from /downloader
        files = os.listdir(DOWNLOAD_DIR)
        if not files:
            await message.reply_text("⚠️ No files found in /downloader.")
            return

        for filename in files:
            file_path = os.path.join(DOWNLOAD_DIR, filename)
            await message.reply_document(file_path, caption=f"📁 {filename}")
            os.remove(file_path)  # Clean up after sending

    except Exception as e:
        await message.reply_text(f"🚨 Unexpected error:\n{str(e)}")

print("# ▶️ Start bot")
app.run()
