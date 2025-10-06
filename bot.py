import discord
from discord.ext import commands, tasks
from discord import app_commands
import json
import os
import asyncio
import aiohttp
import feedparser
from datetime import datetime, timedelta
import re
from typing import Optional, Tuple, List
import logging
import random
from duckduckgo_search import DDGS
from bs4 import BeautifulSoup

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('discord_bot')

# Constants
class Config:
    XP_COOLDOWN = 60
    DAILY_COOLDOWN = 86400
    WORK_COOLDOWN = 900
    FISH_COOLDOWN = 120
    GAMBLE_MIN = 10
    GAMBLE_MAX_PERCENT = 0.5
    NAME_MENTION_COOLDOWN = 30
    
    XP_MIN, XP_MAX = 10, 25
    XP_PER_LEVEL = 100
    DAILY_MIN, DAILY_MAX = 500, 1000
    WORK_MIN, WORK_MAX = 100, 300
    LEVEL_UP_MULTIPLIER = 50
    
    WARN_THRESHOLD = 3
    TIMEOUT_DURATION = 60
    
    DATA_FILE = 'botdata.json'
    AUTOSAVE_INTERVAL = 300
    VIDEO_CHECK_INTERVAL = 300
    LEADERBOARD_UPDATE_INTERVAL = 3600
    SETTINGS_FILE = 'server_settings.json'

class BotData:
    def __init__(self):
        self.data = {
            'levels': {},
            'economy': {},
            'warnings': {},
            'lastVideoId': '',
            'leaderboard_messages': {}
        }
        self.load()
    
    def load(self):
        try:
            if os.path.exists(Config.DATA_FILE):
                with open(Config.DATA_FILE, 'r') as f:
                    loaded = json.load(f)
                    self.data.update(loaded)
                logger.info('Data loaded successfully')
        except Exception as e:
            logger.error(f'Error loading data: {e}')
    
    def save(self):
        try:
            with open(Config.DATA_FILE, 'w') as f:
                json.dump(self.data, f, indent=2)
        except Exception as e:
            logger.error(f'Error saving data: {e}')
    
    def get_user_level(self, user_id: str):
        return self.data['levels'].get(user_id, {'xp': 0, 'level': 1, 'lastMessage': 0})
    
    def set_user_level(self, user_id: str, data: dict):
        self.data['levels'][user_id] = data
    
    def get_user_economy(self, user_id: str):
        return self.data['economy'].get(user_id, {
            'coins': 0, 
            'bank': 0, 
            'lastDaily': 0, 
            'lastWork': 0,
            'lastFish': 0,
            'fishCaught': 0,
            'totalGambled': 0,
            'gamblingWins': 0
        })
    
    def set_user_economy(self, user_id: str, data: dict):
        self.data['economy'][user_id] = data
    
    def get_warnings(self, user_id: str):
        return self.data['warnings'].get(user_id, [])
    
    def add_warning(self, user_id: str, warning: dict):
        if user_id not in self.data['warnings']:
            self.data['warnings'][user_id] = []
        self.data['warnings'][user_id].append(warning)

def load_server_settings():
    if os.path.exists(Config.SETTINGS_FILE):
        with open(Config.SETTINGS_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_server_settings(settings):
    with open(Config.SETTINGS_FILE, 'w') as f:
        json.dump(settings, f, indent=2)

def get_shop_items(bot_data):
    if 'shop_items' not in bot_data.data:
        bot_data.data['shop_items'] = {}
    return bot_data.data['shop_items']

def get_user_inventory(bot_data, user_id: str):
    if 'inventory' not in bot_data.data:
        bot_data.data['inventory'] = {}
    return bot_data.data['inventory'].get(user_id, {})

def add_to_inventory(bot_data, user_id: str, item_id: str):
    if 'inventory' not in bot_data.data:
        bot_data.data['inventory'] = {}
    if user_id not in bot_data.data['inventory']:
        bot_data.data['inventory'][user_id] = {}
    
    bot_data.data['inventory'][user_id][item_id] = {
        'purchased': datetime.utcnow().timestamp()
    }

class AutoMod:
    @staticmethod
    def normalize_text(text: str) -> str:
        normalized = text.lower()
        normalized = re.sub(r'\s+', '', normalized)
        normalized = re.sub(r'[^a-z0-9]', '', normalized)
        replacements = {'0': 'o', '1': 'i', '3': 'e', '4': 'a', '5': 's', '7': 't', '8': 'b'}
        for old, new in replacements.items():
            normalized = normalized.replace(old, new)
        return normalized
    
    @staticmethod
    def check_inappropriate(content: str) -> bool:
        normalized = AutoMod.normalize_text(content)
        blocked_patterns = [
            r'n[il]+[gq]+[ea]+r',
            r'n[il]+[gq]+[a]+',
            r'f[a]+[gq]+[gq]?[o]+[t]',
            r'r[e]+[t]+[a]+r?d',
            r'k[il]+k[e]+',
        ]
        for pattern in blocked_patterns:
            if re.search(pattern, normalized, re.IGNORECASE):
                return True
        return False

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents)
bot_data = BotData()
server_settings = load_server_settings()
name_mention_cooldowns = {}

# Web server
from aiohttp import web

async def handle_health(request):
    return web.Response(text="Bot is running!")

async def start_web_server():
    app = web.Application()
    app.router.add_get('/', handle_health)
    app.router.add_get('/health', handle_health)
    port = int(os.getenv('PORT', 3000))
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    logger.info(f'Web server running on port {port}')

@bot.tree.command(name='flip', description='Flip a coin')
async def flip(interaction: discord.Interaction):
    result = random.choice(['Heads', 'Tails'])
    await interaction.response.send_message(f'🪙 The coin landed on **{result}**!')

@bot.tree.command(name='8ball', description='Ask the magic 8-ball')
@app_commands.describe(question='Your question')
async def eightball(interaction: discord.Interaction, question: str):
    responses = ['Yes, definitely!', 'No way!', 'Maybe...', 'Ask again later', 'Absolutely!', 'I doubt it', 'Signs point to yes', 'Very doubtful', 'Without a doubt', 'My sources say no', 'Outlook good', 'Cannot predict now']
    await interaction.response.send_message(f'🎱 **{question[:200]}**\n{random.choice(responses)}')

@bot.tree.command(name='kitty', description='Get a random cat picture')
async def kitty(interaction: discord.Interaction):
    await interaction.response.defer()
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get('https://api.thecatapi.com/v1/images/search', timeout=aiohttp.ClientTimeout(total=5)) as resp:
                data = await resp.json()
                embed = discord.Embed(title=f'💰 {target.name}\'s Balance', color=0xFFD700, timestamp=datetime.utcnow())
    embed.add_field(name='🪙 Wallet', value=f'{economy_data["coins"]} coins', inline=True)
    embed.add_field(name='🏦 Bank', value=f'{economy_data["bank"]} coins', inline=True)
    embed.add_field(name='💵 Total', value=f'{economy_data["coins"] + economy_data["bank"]} coins', inline=True)
    
    # Add stats if available
    if economy_data.get('fishCaught', 0) > 0:
        embed.add_field(name='🎣 Fish Caught', value=str(economy_data['fishCaught']), inline=True)
    if economy_data.get('gamblingWins', 0) > 0:
        embed.add_field(name='🎰 Gambling Wins', value=str(economy_data['gamblingWins']), inline=True)
    
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name='daily', description='Claim your daily coins')
async def daily(interaction: discord.Interaction):
    user_id = str(interaction.user.id)
    economy_data = bot_data.get_user_economy(user_id)
    now = datetime.utcnow().timestamp()
    if now - economy_data['lastDaily'] < Config.DAILY_COOLDOWN:
        time_left = Config.DAILY_COOLDOWN - (now - economy_data['lastDaily'])
        hours = int(time_left // 3600)
        minutes = int((time_left % 3600) // 60)
        await interaction.response.send_message(f'⏳ You already claimed your daily! Come back in {hours}h {minutes}m')
        return
    amount = random.randint(Config.DAILY_MIN, Config.DAILY_MAX)
    economy_data['coins'] += amount
    economy_data['lastDaily'] = now
    bot_data.set_user_economy(user_id, economy_data)
    bot_data.save()
    await interaction.response.send_message(f'✅ You claimed your daily reward of **{amount} coins**! 💰')

@bot.tree.command(name='work', description='Work for coins')
async def work(interaction: discord.Interaction):
    user_id = str(interaction.user.id)
    economy_data = bot_data.get_user_economy(user_id)
    now = datetime.utcnow().timestamp()
    if now - economy_data.get('lastWork', 0) < Config.WORK_COOLDOWN:
        time_left = Config.WORK_COOLDOWN - (now - economy_data.get('lastWork', 0))
        minutes = int(time_left // 60)
        await interaction.response.send_message(f'⏳ You need to wait {minutes} more minutes before working again!')
        return
    amount = random.randint(Config.WORK_MIN, Config.WORK_MAX)
    economy_data['coins'] += amount
    economy_data['lastWork'] = now
    bot_data.set_user_economy(user_id, economy_data)
    bot_data.save()
    jobs = ['worked at a cafe', 'delivered pizzas', 'coded a website', 'walked dogs', 'mowed lawns', 'streamed on Twitch']
    await interaction.response.send_message(f'💼 You {random.choice(jobs)} and earned **{amount} coins**!')

@bot.tree.command(name='deposit', description='Deposit coins to bank')
@app_commands.describe(amount='Amount to deposit')
async def deposit(interaction: discord.Interaction, amount: int):
    user_id = str(interaction.user.id)
    economy_data = bot_data.get_user_economy(user_id)
    if amount < 1:
        await interaction.response.send_message('❌ Amount must be positive!', ephemeral=True)
        return
    if amount > economy_data['coins']:
        await interaction.response.send_message('❌ You don\'t have enough coins!', ephemeral=True)
        return
    economy_data['coins'] -= amount
    economy_data['bank'] += amount
    bot_data.set_user_economy(user_id, economy_data)
    bot_data.save()
    await interaction.response.send_message(f'✅ Deposited **{amount} coins** to your bank!')

@bot.tree.command(name='withdraw', description='Withdraw coins from bank')
@app_commands.describe(amount='Amount to withdraw')
async def withdraw(interaction: discord.Interaction, amount: int):
    user_id = str(interaction.user.id)
    economy_data = bot_data.get_user_economy(user_id)
    if amount < 1:
        await interaction.response.send_message('❌ Amount must be positive!', ephemeral=True)
        return
    if amount > economy_data['bank']:
        await interaction.response.send_message('❌ You don\'t have enough coins in your bank!', ephemeral=True)
        return
    economy_data['bank'] -= amount
    economy_data['coins'] += amount
    bot_data.set_user_economy(user_id, economy_data)
    bot_data.save()
    await interaction.response.send_message(f'✅ Withdrew **{amount} coins** from your bank!')

@bot.tree.command(name='give', description='Give coins to someone')
@app_commands.describe(user='User to give coins', amount='Amount to give')
async def give(interaction: discord.Interaction, user: discord.Member, amount: int):
    if user.bot:
        await interaction.response.send_message('❌ You can\'t give coins to bots!', ephemeral=True)
        return
    if user.id == interaction.user.id:
        await interaction.response.send_message('❌ You can\'t give coins to yourself!', ephemeral=True)
        return
    if amount < 1:
        await interaction.response.send_message('❌ Amount must be positive!', ephemeral=True)
        return
    sender_id = str(interaction.user.id)
    sender_data = bot_data.get_user_economy(sender_id)
    if amount > sender_data['coins']:
        await interaction.response.send_message('❌ You don\'t have enough coins!', ephemeral=True)
        return
    recipient_id = str(user.id)
    recipient_data = bot_data.get_user_economy(recipient_id)
    sender_data['coins'] -= amount
    recipient_data['coins'] += amount
    bot_data.set_user_economy(sender_id, sender_data)
    bot_data.set_user_economy(recipient_id, recipient_data)
    bot_data.save()
    await interaction.response.send_message(f'✅ Gave **{amount} coins** to {user.mention}!')

# ============ MODERATION COMMANDS ============
@bot.tree.command(name='warn', description='Warn a user')
@app_commands.describe(user='User to warn', reason='Reason for warning')
@app_commands.default_permissions(moderate_members=True)
async def warn(interaction: discord.Interaction, user: discord.Member, reason: str):
    if user.bot:
        await interaction.response.send_message('❌ Cannot warn bots!', ephemeral=True)
        return
    warning = {'reason': reason[:500], 'mod': str(interaction.user.id), 'timestamp': datetime.utcnow().timestamp()}
    bot_data.add_warning(str(user.id), warning)
    bot_data.save()
    try:
        await user.send(f'⚠️ You have been warned in **{interaction.guild.name}**\n**Reason:** {reason}')
    except:
        pass
    await interaction.response.send_message(f'✅ Warned {user.mention} for: {reason}')

@bot.tree.command(name='warnings', description='Check warnings')
@app_commands.describe(user='User to check')
@app_commands.default_permissions(moderate_members=True)
async def warnings(interaction: discord.Interaction, user: Optional[discord.Member] = None):
    target = user or interaction.user
    warns = bot_data.get_warnings(str(target.id))
    if not warns:
        await interaction.response.send_message(f'{target.mention} has no warnings!')
        return
    description = []
    for i, w in enumerate(warns):
        date = datetime.fromtimestamp(w['timestamp']).strftime('%Y-%m-%d')
        description.append(f'**{i+1}.** {w["reason"]}\nBy: <@{w["mod"]}> on {date}')
    embed = discord.Embed(title=f'⚠️ {target.name}\'s Warnings ({len(warns)})', description='\n\n'.join(description), color=0xFF0000, timestamp=datetime.utcnow())
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name='kick', description='Kick a user')
@app_commands.describe(user='User to kick', reason='Reason')
@app_commands.default_permissions(kick_members=True)
async def kick(interaction: discord.Interaction, user: discord.Member, reason: Optional[str] = 'No reason provided'):
    if not user.guild_permissions < interaction.user.guild_permissions:
        await interaction.response.send_message('❌ Cannot kick this user!', ephemeral=True)
        return
    try:
        await user.kick(reason=reason)
        await interaction.response.send_message(f'✅ Kicked {user.mention} for: {reason}')
    except:
        await interaction.response.send_message('❌ Failed to kick user!', ephemeral=True)

@bot.tree.command(name='ban', description='Ban a user')
@app_commands.describe(user='User to ban', reason='Reason')
@app_commands.default_permissions(ban_members=True)
async def ban(interaction: discord.Interaction, user: discord.Member, reason: Optional[str] = 'No reason provided'):
    if not user.guild_permissions < interaction.user.guild_permissions:
        await interaction.response.send_message('❌ Cannot ban this user!', ephemeral=True)
        return
    try:
        await user.ban(reason=reason)
        await interaction.response.send_message(f'✅ Banned {user.mention} for: {reason}')
    except:
        await interaction.response.send_message('❌ Failed to ban user!', ephemeral=True)

@bot.tree.command(name='timeout', description='Timeout a user')
@app_commands.describe(user='User to timeout', duration='Duration in minutes', reason='Reason')
@app_commands.default_permissions(moderate_members=True)
async def timeout(interaction: discord.Interaction, user: discord.Member, duration: int, reason: Optional[str] = 'No reason provided'):
    if duration < 1 or duration > 40320:
        await interaction.response.send_message('❌ Duration must be between 1 and 40320 minutes!', ephemeral=True)
        return
    try:
        await user.timeout(timedelta(minutes=duration), reason=reason)
        await interaction.response.send_message(f'✅ Timed out {user.mention} for {duration} minutes. Reason: {reason}')
    except:
        await interaction.response.send_message('❌ Cannot timeout this user!', ephemeral=True)

@bot.tree.command(name='purge', description='Delete messages')
@app_commands.describe(amount='Number of messages (1-100)')
@app_commands.default_permissions(manage_messages=True)
async def purge(interaction: discord.Interaction, amount: int):
    if amount < 1 or amount > 100:
        await interaction.response.send_message('❌ Amount must be between 1 and 100!', ephemeral=True)
        return
    await interaction.response.defer(ephemeral=True)
    deleted = await interaction.channel.purge(limit=amount)
    await interaction.followup.send(f'✅ Deleted {len(deleted)} messages!', ephemeral=True)

# ============ ADMIN COMMANDS ============
@bot.tree.command(name='say', description='Make the bot say something')
@app_commands.describe(message='Message to send')
@app_commands.default_permissions(administrator=True)
async def say(interaction: discord.Interaction, message: str):
    await interaction.response.defer(ephemeral=True)
    await interaction.channel.send(message[:2000])
    await interaction.followup.send('✅ Message sent!', ephemeral=True)

@bot.tree.command(name='embed', description='Send an embed message')
@app_commands.describe(text='Embed text', image='Image URL', color='Hex color (e.g., #FF0000)')
@app_commands.default_permissions(administrator=True)
async def embed_cmd(interaction: discord.Interaction, text: str, image: Optional[str] = None, color: Optional[str] = '#9B59B6'):
    # Validate hex color
    if not re.match(r'^#[0-9A-Fa-f]{6}$', color):
        await interaction.response.send_message('❌ Invalid hex color!', ephemeral=True)
        return
    color_int = int(color.replace('#', ''), 16)
    embed = discord.Embed(description=text[:4096], color=color_int, timestamp=datetime.utcnow())
    if image:
        if not re.match(r'^https?://.+\.(jpg|jpeg|png|gif|webp)$', image, re.IGNORECASE):
            await interaction.response.send_message('❌ Invalid image URL!', ephemeral=True)
            return
        embed.set_image(url=image)
    await interaction.response.defer(ephemeral=True)
    await interaction.channel.send(embed=embed)
    await interaction.followup.send('✅ Embed sent!', ephemeral=True)

@bot.tree.command(name='dm', description='Send a DM to a user')
@app_commands.describe(user='User to message', message='Message content')
@app_commands.default_permissions(moderate_members=True)
async def dm(interaction: discord.Interaction, user: discord.Member, message: str):
    try:
        await user.send(f'📬 **Message from tooly**\n\n{message[:2000]}')
        await interaction.response.send_message(f'✅ Message sent to {user.mention}', ephemeral=True)
    except:
        await interaction.response.send_message('❌ Could not send DM. The user may have DMs off.', ephemeral=True)

# ============ YOUTUBE COMMANDS ============
@bot.tree.command(name='checkvideos', description='Check for new PippyOC videos')
@app_commands.default_permissions(manage_guild=True)
async def checkvideos(interaction: discord.Interaction):
    await interaction.response.send_message('Checking for new PippyOC videos... 🔍')
    await check_videos()

# ============ HELP COMMAND ============
@bot.tree.command(name='help', description='Show all commands')
async def help_command(interaction: discord.Interaction):
    embed = discord.Embed(
        title='📋 Tooly Bot Commands',
        description='Here are all my commands organized by category!',
        color=0x9B59B6,
        timestamp=datetime.utcnow()
    )
    embed.add_field(name='ℹ️ Info', value='`/hello` `/ping` `/serverinfo` `/userinfo` `/botinfo` `/help`', inline=False)
    embed.add_field(name='🎮 Fun', value='`/roll` `/flip` `/8ball` `/kitty` `/doggy` `/randompet` `/joke` `/yotsuba` `/image` `/music`', inline=False)
    embed.add_field(name='📊 Levels', value='`/rank` `/leaderboard` `/setleaderboard`\nEarn XP by chatting! (1 msg/min)', inline=False)
    embed.add_field(name='💰 Economy', value='`/balance` `/daily` `/work` `/deposit` `/withdraw` `/give` `/fish` `/gamble`', inline=False)
    embed.add_field(name='🛒 Shop', value='`/shop` `/buy` `/inventory`', inline=False)
    embed.add_field(name='🛡️ Moderation', value='`/warn` `/warnings` `/kick` `/ban` `/timeout` `/purge`', inline=False)
    embed.add_field(name='👑 Admin', value='`/say` `/embed` `/dm` `/createitem` `/deleteitem` `/listitems`', inline=False)
    embed.add_field(name='📺 YouTube', value='`/checkvideos` `/toggle-notifications` `/notification-status`', inline=False)
    embed.set_footer(text='Type / to see all commands!')
    await interaction.response.send_message(embed=embed)

if __name__ == '__main__':
    token = os.getenv('TOKEN')
    if not token:
        logger.error('❌ TOKEN environment variable not set!')
        exit(1)
    bot.run(token)