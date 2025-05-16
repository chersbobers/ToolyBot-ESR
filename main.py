import discord
from discord.ext import commands
from aiohttp import web
import os
from supabase import create_client, Client

# ===============================
# CONFIGURATION - use env vars!
# ===============================
DISCORD_BOT_TOKEN = os.getenv("05fea0fd6d1380a2377fcf870bb019979400e987c658ddc47a22d344c230c739")
SUPABASE_URL = os.getenv("https://hpozhvkrlckwybrjasjn.supabase.co")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imhwb3podmtybGNrd3licmphc2puIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDczNzI2NDEsImV4cCI6MjA2Mjk0ODY0MX0.2bbU0qD1zGmJjAQpSPjub5De4ZCD5NqRd9SEhzptI28")
PORT = int(os.getenv("PORT", 8080))

# Allowed channels — fix duplicate keys, use unique channel IDs
ALLOWED_CHANNELS = {
    1328561469410775134: 'general',
    1328561469410775135: 'updates',        # changed to a unique ID for example
    1329596448127451156: 'announcements',
}

# ===============================

# Setup discord bot with intents
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# Setup Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

@bot.event
async def on_ready():
    print(f'✅ Logged in as {bot.user}!')
    bot.loop.create_task(start_webserver())

async def handle_post(request):
    try:
        data = await request.json()
        message = data.get("message")
        channel_id = int(data.get("channel_id"))

        # Validate input
        if not message or not channel_id:
            return web.Response(status=400, text="Missing message or channel_id.")
        if channel_id not in ALLOWED_CHANNELS:
            return web.Response(status=403, text="Channel not allowed.")

        # Insert message into Supabase
        res = supabase.from_("messages").insert([
            {"message": message, "channel_id": str(channel_id)}
        ]).execute()

        if res.error:
            return web.Response(status=500, text=f"Supabase error: {res.error.message}")

        # Send message to Discord channel
        channel = bot.get_channel(channel_id)
        if not channel:
            return web.Response(status=404, text="Channel not found.")

        await channel.send(f"[From Website] {message}")
        return web.Response(text="✅ Message sent!")

    except Exception as e:
        print("❌ Error:", e)
        return web.Response(status=500, text="Server error.")

async def start_webserver():
    app = web.Application()
    app.router.add_post('/send', handle_post)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', PORT)
    await site.start()
    print(f"🌐 Webhook server running at http://0.0.0.0:{PORT}/send")

if __name__ == "__main__":
    if not DISCORD_BOT_TOKEN or not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
        print("❌ ERROR: Please set DISCORD_BOT_TOKEN, SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY env vars!")
        exit(1)
    bot.run(DISCORD_BOT_TOKEN)
