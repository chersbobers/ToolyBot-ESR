import discord
from discord.ext import commands
from discord import option
from datetime import datetime
import re
import random
import logging
from utils.database import bot_data, server_settings
from utils.config import Config

logger = logging.getLogger('tooly_bot.moderation')

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

class Moderation(commands.Cog):
    """Moderation commands and auto-mod"""
    
    def __init__(self, bot):
        self.bot = bot
        self.name_mention_cooldowns = {}
    
    @commands.Cog.listener()
    async def on_message(self, message):
        """Auto-moderation and easter eggs"""
        if message.author.bot or isinstance(message.channel, discord.DMChannel):
            return
        
        # Auto-moderation
        is_blocked = AutoMod.check_inappropriate(message.content)
        if is_blocked:
            try:
                await message.delete()
                await message.channel.send(
                    f'⚠️ {message.author.mention}, your message was removed for inappropriate content',
                    delete_after=5
                )
                logger.info(f'🛡️ Blocked message from {message.author}')
            except discord.Forbidden:
                logger.warning('⚠️ Missing permissions to delete message')
            return
        
        # Easter egg responses
        content_lower = message.content.lower()
        if any(name.lower() in content_lower for name in ['clanka', 'clanker', 'tinskin']):
            cooldown_key = f'{message.author.id}-{message.channel.id}'
            now = datetime.utcnow().timestamp()
            
            if cooldown_key in self.name_mention_cooldowns:
                if now - self.name_mention_cooldowns[cooldown_key] < Config.NAME_MENTION_COOLDOWN:
                    return
            
            self.name_mention_cooldowns[cooldown_key] = now
            responses = [
                'Robophobia in the big 25', 'Woah you cant say that', 'DONT SLUR AT ME!',
                'ROBOPHOBIA wow real cool dude', 'how would you like it if i called you a human?',
                'beep boop', 'BEEP BOOP', 'BEEP BOOP BEEP BOOP', 'DING DONG', 'DING DONG DING DONG',
                'DOO WOP A DOO WOP A DOO WOP', 'BOP A DOO WOP A BOP A DOO WOP'
            ]
            await message.reply(random.choice(responses))
    
    @commands.Cog.listener()
    async def on_member_join(self, member):
        """Welcome new members"""
        if member.bot:
            return
        
        welcome_msg = f"""👋 Welcome to **{member.guild.name}**, {member.name}!

I'm Tooly Bot! Here's what I can do:
• 📊 Earn XP and level up by chatting
• 💰 Economy system with daily rewards & work
• 🎣 Go fishing and sell your catch (18 fish types!)
• 🎰 Play 4 gambling games: Slots, Dice, Coinflip, Roulette
• 🎭 Reaction roles for self-assignable roles
• 🎮 Fun commands and games
• 🛡️ Moderation tools

Use `/botinfo` to learn more about all features!"""
        
        try:
            await member.send(welcome_msg)
            logger.info(f'✅ Sent welcome DM to {member.name}')
        except discord.Forbidden:
            logger.info(f'❌ Could not send DM to {member.name}')
    
    @discord.slash_command(name='purge', description='[MOD] Delete multiple messages')
    @option("amount", description="Number of messages to delete (1-100)", min_value=1, max_value=100)
    @discord.default_permissions(manage_messages=True)
    async def purge(self, ctx, amount: int):
        await ctx.defer(ephemeral=True)
        
        try:
            deleted = await ctx.channel.purge(limit=amount)
            
            embed = discord.Embed(
                title='🗑️ Messages Purged',
                description=f'Successfully deleted **{len(deleted)}** messages!',
                color=0x00FF00,
                timestamp=datetime.utcnow()
            )
            embed.add_field(name='Channel', value=ctx.channel.mention, inline=True)
            embed.add_field(name='Moderator', value=ctx.author.mention, inline=True)
            
            await ctx.followup.send(embed=embed, ephemeral=True)
            logger.info(f'🗑️ {ctx.author} purged {len(deleted)} messages in {ctx.channel}')
            
        except discord.Forbidden:
            await ctx.followup.send('❌ I don\'t have permission to delete messages in this channel!', ephemeral=True)
        except discord.HTTPException as e:
            await ctx.followup.send(f'❌ Failed to delete messages: {str(e)}', ephemeral=True)
            logger.error(f'Purge error: {e}')
    
    @discord.slash_command(name='createitem', description='[ADMIN] Create a new shop item')
    @option("item_id", description="Unique ID for the item")
    @option("name", description="Display name")
    @option("price", description="Price in coins", min_value=1)
    @option("description", description="Item description")
    @option("emoji", description="Emoji for the item")
    @option("item_type", description="Type of item", choices=["role", "badge", "consumable"])
    @option("role_id", description="Role ID (only for role type items)", required=False)
    @discord.default_permissions(administrator=True)
    async def createitem(self, ctx, item_id: str, name: str, price: int, description: str, emoji: str, item_type: str, role_id: str = None):
        if item_type == 'role' and not role_id:
            await ctx.respond('❌ Role items require a role_id!', ephemeral=True)
            return
        
        shop_items = bot_data.get_shop_items()
        if item_id in shop_items:
            await ctx.respond(f'❌ Item with ID `{item_id}` already exists!', ephemeral=True)
            return
        
        shop_items[item_id] = {
            'name': name[:100],
            'description': description[:200],
            'price': price,
            'emoji': emoji[:10],
            'type': item_type,
            'role_id': role_id,
            'created': datetime.utcnow().timestamp(),
            'creator': str(ctx.author.id)
        }
        
        bot_data.data['shop_items'] = shop_items
        bot_data.save()
        
        embed = discord.Embed(
            title='✅ Item Created Successfully',
            color=0x00FF00,
            timestamp=datetime.utcnow()
        )
        embed.add_field(name='ID', value=f'`{item_id}`', inline=True)
        embed.add_field(name='Name', value=name, inline=True)
        embed.add_field(name='Price', value=f'{price:,} coins', inline=True)
        embed.add_field(name='Type', value=item_type, inline=True)
        embed.add_field(name='Emoji', value=emoji, inline=True)
        if role_id:
            embed.add_field(name='Role ID', value=role_id, inline=True)
        embed.add_field(name='Description', value=description, inline=False)
        
        await ctx.respond(embed=embed)
    
    @discord.slash_command(name='deleteitem', description='[ADMIN] Delete a shop item')
    @option("item_id", description="ID of item to delete")
    @discord.default_permissions(administrator=True)
    async def deleteitem(self, ctx, item_id: str):
        shop_items = bot_data.get_shop_items()
        
        if item_id not in shop_items:
            await ctx.respond(f'❌ Item `{item_id}` not found!', ephemeral=True)
            return
        
        item = shop_items[item_id]
        del shop_items[item_id]
        bot_data.data['shop_items'] = shop_items
        bot_data.save()
        
        await ctx.respond(f'✅ Deleted item: **{item["name"]}** (`{item_id}`)')
    
    @discord.slash_command(name='listitems', description='[ADMIN] List all shop items with IDs')
    @discord.default_permissions(administrator=True)
    async def listitems(self, ctx):
        shop_items = bot_data.get_shop_items()
        
        if not shop_items:
            await ctx.respond('📦 No items in shop yet. Use `/createitem` to add some!', ephemeral=True)
            return
        
        embed = discord.Embed(
            title='📋 All Shop Items (Admin View)',
            color=0x9B59B6,
            timestamp=datetime.utcnow()
        )
        
        for item_id, item in shop_items.items():
            field_value = f"**Price:** {item['price']:,} coins\n**Type:** {item['type']}\n**Description:** {item['description']}"
            if item.get('role_id'):
                field_value += f"\n**Role ID:** {item['role_id']}"
            
            embed.add_field(
                name=f"{item['emoji']} {item['name']} (`{item_id}`)",
                value=field_value,
                inline=False
            )
        
        await ctx.respond(embed=embed, ephemeral=True)

def setup(bot):
    bot.add_cog(Moderation(bot))