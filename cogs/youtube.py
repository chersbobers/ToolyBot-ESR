import discord
from discord.ext import commands, tasks
from datetime import datetime
import asyncio
import feedparser
import os
import logging
from utils.database import bot_data, server_settings
from utils.config import Config

logger = logging.getLogger('tooly_bot.youtube')

class YouTube(commands.Cog):
    """YouTube notification system"""
    
    def __init__(self, bot):
        self.bot = bot
        self.check_videos.start()
    
    def cog_unload(self):
        self.check_videos.cancel()
    
    @discord.slash_command(name='toggle_notifications', description='[ADMIN] Toggle YouTube video notifications')
    @discord.default_permissions(manage_guild=True)
    async def toggle_notifications(self, ctx):
        guild_id = str(ctx.guild.id)
        
        current = server_settings.get(guild_id, 'notifications_enabled', True)
        server_settings.set(guild_id, 'notifications_enabled', not current)
        
        status = "enabled ✅" if not current else "disabled ❌"
        
        embed = discord.Embed(
            title='🔔 Notification Settings',
            description=f'YouTube notifications are now **{status}**',
            color=0xFF69B4 if not current else 0x808080,
            timestamp=datetime.utcnow()
        )
        
        await ctx.respond(embed=embed)
    
    @discord.slash_command(name='notification_status', description='Check if notifications are enabled')
    async def notification_status(self, ctx):
        guild_id = str(ctx.guild.id)
        enabled = server_settings.get(guild_id, 'notifications_enabled', True)
        
        status = "enabled ✅" if enabled else "disabled ❌"
        
        embed = discord.Embed(
            title='🔔 Notification Status',
            description=f'YouTube notifications are currently **{status}**',
            color=0xFF69B4 if enabled else 0x808080,
            timestamp=datetime.utcnow()
        )
        
        await ctx.respond(embed=embed)
    
    @tasks.loop(seconds=Config.VIDEO_CHECK_INTERVAL)
    async def check_videos(self):
        """Check for new YouTube videos"""
        channel_id = os.getenv('YOUTUBE_CHANNEL_ID')
        notif_channel_id = os.getenv('NOTIFICATION_CHANNEL_ID')
        
        if not channel_id or not notif_channel_id:
            return
        
        try:
            feed_url = f'https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}'
            feed = await asyncio.to_thread(feedparser.parse, feed_url)
            
            if feed.entries:
                latest = feed.entries[0]
                video_id = latest.id
                
                if video_id != bot_data.data['lastVideoId'] and bot_data.data['lastVideoId']:
                    channel = self.bot.get_channel(int(notif_channel_id))
                    if channel:
                        guild_id = str(channel.guild.id)
                        
                        # Check if notifications are enabled
                        if not server_settings.get(guild_id, 'notifications_enabled', True):
                            logger.info(f'🔕 Notifications disabled for guild {guild_id}')
                            bot_data.data['lastVideoId'] = video_id
                            bot_data.save()
                            return

                        embed = discord.Embed(
                            title='🎬 New YouTube Video!',
                            description=f'**{latest.title}**',
                            url=latest.link,
                            color=0xFF0000,
                            timestamp=datetime.utcnow()
                        )
                        
                        if hasattr(latest, 'media_thumbnail'):
                            embed.set_thumbnail(url=latest.media_thumbnail[0]['url'])
                        
                        embed.add_field(name='Channel', value=latest.author, inline=True)
                        pub_date = datetime.strptime(latest.published, '%Y-%m-%dT%H:%M:%S%z')
                        embed.add_field(name='Published', value=pub_date.strftime('%Y-%m-%d %H:%M'), inline=True)
                        
                        await channel.send('📺 New video alert! @everyone', embed=embed)
                        logger.info(f'📺 New video notification sent: {latest.title}')
                
                bot_data.data['lastVideoId'] = video_id
                bot_data.save()
        
        except Exception as e:
            logger.error(f'❌ Error checking videos: {e}')
    
    @check_videos.before_loop
    async def before_check_videos(self):
        await self.bot.wait_until_ready()

def setup(bot):
    bot.add_cog(YouTube(bot))