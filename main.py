import os
import asyncio
import logging
from pyrogram import Client, filters
from pymongo import MongoClient
from pyrogram.errors import (
    ChatWriteForbidden,
    ChatAdminRequired,
    UserIsBlocked,
    PeerIdInvalid,
    RPCError,
    FloodWait
)
from aiohttp import web

# ==========================
# CONFIG
# ==========================
BOT_TOKEN = os.getenv("BOT_TOKEN")
API_ID = 29568441
API_HASH = "b32ec0fb66d22da6f77d355fbace4f2a"
OWNER_ID = 5268762773

# MongoDB setup
mongo_uri = os.environ.get(
    "MONGO_URI",
    "mongodb+srv://frozenbotss:noobop0011@cluster0.s0tak.mongodb.net/?retryWrites=true&w=majority"
)
mongo_client = MongoClient(mongo_uri)
db = mongo_client["music_bot"]
broadcast_collection = db["broadcast"]

# ==========================
# LOGGING
# ==========================
logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

# ==========================
# BOT
# ==========================
bot = Client(
    name="broad112cast-bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)


@bot.on_message(filters.command("br") & filters.user(OWNER_ID))
async def broadcast_handler(_, message):
    if not message.reply_to_message:
        await message.reply("❌ Please reply to the message you want to broadcast.")
        return

    broadcast_message = message.reply_to_message
    all_chats = list(broadcast_collection.find({}))

    total = len(all_chats)
    success = 0
    failed = 0
    processed = 0

    logging.info(f"🚀 Starting broadcast to {total} chats...")

    for chat in all_chats:
        processed += 1
        try:
            target_chat_id = int(chat.get("chat_id"))
        except Exception as e:
            logging.warning(f"❌ Invalid chat_id: {chat.get('chat_id')} - {e}")
            failed += 1
            continue

        try:
            sent_msg = await bot.forward_messages(
                chat_id=target_chat_id,
                from_chat_id=broadcast_message.chat.id,
                message_ids=broadcast_message.id
            )
            success += 1
            logging.info(f"✅ Forwarded to {target_chat_id}")

            try:
                await bot.pin_chat_message(
                    chat_id=target_chat_id,
                    message_id=sent_msg.id,
                    disable_notification=False
                )
                logging.info(f"📌 Pinned in {target_chat_id}")
            except Exception as e:
                logging.debug(f"⚠️ Could not pin in {target_chat_id}: {e}")

        except FloodWait as e:
            logging.warning(f"⏳ FloodWait detected: Sleeping for {e.value}s...")
            await asyncio.sleep(e.value)
            logging.info("🔄 Resuming broadcast after FloodWait")
            continue

        except (ChatWriteForbidden, UserIsBlocked,
                ChatAdminRequired, PeerIdInvalid, ValueError) as e:
            logging.warning(f"❌ Removing {target_chat_id} (reason: {e})")
            failed += 1
            broadcast_collection.delete_one({"chat_id": chat.get("chat_id")})

        except RPCError as e:
            logging.error(f"❌ Failed to forward to {target_chat_id}: {e}")
            failed += 1

        if processed % 50 == 0:
            logging.info(f"📊 Progress: {processed}/{total} | ✅ {success} | ❌ {failed}")

        await asyncio.sleep(0.5)

    logging.info(f"✅ Broadcast finished! Total: {total} | Success: {success} | Failed: {failed}")
    await message.reply(f"📢 Broadcast complete!\n✅ Success: {success}\n❌ Failed & removed: {failed}")


# ==========================
# HTTP SERVER
# ==========================
async def handle_root(request):
    return web.Response(text="bot is alive baby")

async def start_web_server():
    app = web.Application()
    app.add_routes([web.get("/", handle_root)])
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", int(os.environ.get("PORT", 8080)))
    await site.start()
    logging.info("🌐 HTTP server running on port 8080")

# ==========================
# MAIN
# ==========================
async def main():
    await asyncio.gather(
        bot.start(),
        start_web_server()
    )
    logging.info("✅ Broadcast bot is running...")
    await bot.idle()  # Keep bot alive

asyncio.run(main())
