import discord
from discord.ext import commands, tasks
from discord import option
from datetime import datetime
from typing import Optional
import random
import logging
from utils.database import bot_data
from utils.config import Config


logger = logging.getLogger('tooly_bot.leveling')

class Leveling(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.autosave.start()
        self.update_leaderboard.start()
    
    def cog_unload(self):
        self.autosave.cancel()
        self.update_leaderboard.cancel()
    
    @commands.Cog.listener()
    async def on_message(self, message):
        """Handle XP gain from messages"""
        if message.author.bot or isinstance(message.channel, discord.DMChannel):
            return
        
        guild_id = str(message.guild.id)
        user_id = str(message.author.id)
        
        # FIX: Added guild_id parameter
        user_data = bot_data.get_user_level(guild_id, user_id)
        now = datetime.utcnow().timestamp()
        
        if now - user_data['lastMessage'] >= Config.XP_COOLDOWN:
            user_data['lastMessage'] = now
            xp_gain = random.randint(Config.XP_MIN, Config.XP_MAX)
            user_data['xp'] += xp_gain
            xp_needed = user_data['level'] * Config.XP_PER_LEVEL
            
            if user_data['xp'] >= xp_needed:
                user_data['level'] += 1
                user_data['xp'] = 0
                
                messages = [
                    f'🎉 GG {message.author.mention}! You leveled up to **Level {user_data["level"]}**!',
                    f'⭐ Congrats {message.author.mention}! You\'re now **Level {user_data["level"]}**!',
                    f'🚀 Level up! {message.author.mention} reached **Level {user_data["level"]}**!',
                    f'💫 Awesome! {message.author.mention} is now **Level {user_data["level"]}**!'
                ]
                
                coin_reward = user_data['level'] * Config.LEVEL_UP_MULTIPLIER
                economy_data = bot_data.get_user_economy(guild_id, user_id)
                economy_data['coins'] += coin_reward
                bot_data.set_user_economy(guild_id, user_id, economy_data)
                
                await message.channel.send(
                    f'{random.choice(messages)} You earned **{coin_reward:,} coins**! 💰'
                )
            
            bot_data.set_user_level(guild_id, user_id, user_data)
    
    @discord.slash_command(name='rank', description='Check your rank and level')
    @option("user", discord.Member, description="User to check (optional)", required=False)
    async def rank(self, ctx, user: Optional[discord.Member] = None):
        target = user or ctx.author
        guild_id = str(ctx.guild.id)
        user_id = str(target.id)
        
        user_data = bot_data.get_user_level(guild_id, user_id)
        economy_data = bot_data.get_user_economy(guild_id, user_id)
        xp_needed = user_data['level'] * Config.XP_PER_LEVEL
        
        # FIX: Get all users for this guild
        all_users = list(bot_data.levels_col.find({'guild_id': guild_id}))
        all_users.sort(key=lambda x: (x.get('level', 1), x.get('xp', 0)), reverse=True)
        
        rank = next((i + 1 for i, u in enumerate(all_users) if u.get('user_id') == user_id), 'Unranked')
        
        progress_percent = int((user_data['xp'] / xp_needed) * 100) if xp_needed > 0 else 0
        progress_bar = self.create_progress_bar(user_data['xp'], xp_needed, length=20)
        
        if user_data['level'] >= 50:
            color = 0xFF6B6B
        elif user_data['level'] >= 30:
            color = 0xFFD93D
        elif user_data['level'] >= 15:
            color = 0x6BCB77
        else:
            color = 0x4D96FF
        
        embed = discord.Embed(color=color)
        embed.set_author(name=f"{target.display_name}'s Profile", icon_url=target.display_avatar.url)
        embed.set_thumbnail(url=target.display_avatar.url)
        
        embed.description = f"""
**RANK** • #{rank} / {len(all_users)}
**LEVEL** • {user_data['level']}
**XP** • {user_data['xp']:,} / {xp_needed:,} ({progress_percent}%)

{progress_bar}

**💰 BALANCE** • {economy_data['coins']:,} coins
        """
        
        if economy_data.get('fishCaught', 0) > 0:
            embed.add_field(name='🎣 Fish Caught', value=f"{economy_data['fishCaught']:,}", inline=True)
        
        if economy_data.get('gamblingWins', 0) > 0:
            total_games = economy_data.get('gamblingWins', 0) + economy_data.get('gamblingLosses', 0)
            win_rate = (economy_data['gamblingWins'] / total_games * 100) if total_games > 0 else 0
            embed.add_field(name='🎰 Win Rate', value=f"{win_rate:.1f}%", inline=True)
        
        embed.set_footer(text=f"Requested by {ctx.author.name}")
        embed.timestamp = datetime.utcnow()
        
        await ctx.respond(embed=embed)
    
    @discord.slash_command(name='leaderboard', description='View the server leaderboard')
    async def leaderboard(self, ctx):
        guild_id = str(ctx.guild.id)
        embed = self.generate_leaderboard_embed(guild_id)
        await ctx.respond(embed=embed)
    
    @discord.slash_command(name='setleaderboard', description='[ADMIN] Set auto-updating leaderboard in this channel')
    @discord.default_permissions(administrator=True)
    async def setleaderboard(self, ctx):
        await ctx.defer()
        
        guild_id = str(ctx.guild.id)
        embed = self.generate_leaderboard_embed(guild_id)
        message = await ctx.channel.send(embed=embed)
        
        # FIX: Use proper method to store leaderboard messages
        bot_data.set_leaderboard_message(
            guild_id,
            str(ctx.channel.id),
            str(message.id)
        )
        
        await ctx.followup.send('✅ Auto-updating leaderboard created! It will update every hour.')
    
    def create_progress_bar(self, current: int, total: int, length: int = 20) -> str:
        if total == 0:
            return '░' * length + ' 0%'
        
        filled = int((current / total) * length)
        bar = '█' * filled + '░' * (length - filled)
        percentage = int((current / total) * 100)
        return f'`{bar}` {percentage}%'
    
    def generate_leaderboard_embed(self, guild_id: str):
        # FIX: Query MongoDB directly for guild-specific leaderboard
        all_users = list(bot_data.levels_col.find({'guild_id': guild_id}))
        all_users.sort(key=lambda x: (x.get('level', 1), x.get('xp', 0)), reverse=True)
        all_users = all_users[:10]
        
        description = []
        for i, user_doc in enumerate(all_users):
            medal = '🥇' if i == 0 else '🥈' if i == 1 else '🥉' if i == 2 else f'**{i+1}.**'
            
            user_id = user_doc.get('user_id')
            level = user_doc.get('level', 1)
            xp = user_doc.get('xp', 0)
            
            economy_data = bot_data.get_user_economy(guild_id, user_id)
            total_coins = economy_data.get('coins', 0) + economy_data.get('bank', 0)
            
            description.append(
                f'{medal} <@{user_id}>\n'
                f'└ Level {level} ({xp:,} XP) • {total_coins:,} coins'
            )
        
        embed = discord.Embed(
            title='🏆 Server Leaderboard',
            description='\n'.join(description) if description else 'No users yet!',
            color=0x9B59B6,
            timestamp=datetime.utcnow()
        )
        embed.set_footer(text='Updates every hour • Showing Level & Total Coins')
        return embed
    
    @tasks.loop(seconds=Config.AUTOSAVE_INTERVAL)
    async def autosave(self):
        # MongoDB auto-saves, but keep for compatibility
        bot_data.save()
        logger.info('💾 Data autosaved')
    
    @tasks.loop(seconds=Config.LEADERBOARD_UPDATE_INTERVAL)
    async def update_leaderboard(self):
        try:
            # FIX: Query all guilds with leaderboard messages
            leaderboard_docs = bot_data.leaderboards_col.find({})
            
            for doc in leaderboard_docs:
                guild_id = doc.get('guild_id')
                channel_id = doc.get('channel_id')
                message_id = doc.get('message_id')
                
                if not all([guild_id, channel_id, message_id]):
                    continue
                
                channel = self.bot.get_channel(int(channel_id))
                if not channel:
                    continue
                    
                try:
                    message = await channel.fetch_message(int(message_id))
                    embed = self.generate_leaderboard_embed(guild_id)
                    await message.edit(embed=embed)
                    logger.info(f'📊 Updated leaderboard for guild {guild_id}')
                except discord.NotFound:
                    # Delete invalid leaderboard message
                    bot_data.leaderboards_col.delete_one({'guild_id': guild_id})
                    logger.info(f'🗑️ Removed invalid leaderboard for guild {guild_id}')
                except Exception as e:
                    logger.error(f'❌ Error updating leaderboard for guild {guild_id}: {e}')
        except Exception as e:
            logger.error(f'❌ Leaderboard update error: {e}')
    
    @autosave.before_loop
    async def before_autosave(self):
        await self.bot.wait_until_ready()
    
    @update_leaderboard.before_loop
    async def before_update_leaderboard(self):
        await self.bot.wait_until_ready()

def setup(bot):
    bot.add_cog(Leveling(bot))