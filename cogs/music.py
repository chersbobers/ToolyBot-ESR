import discord
from discord.ext import commands
from discord import option
from datetime import datetime
import aiohttp
import re
import os
import logging

logger = logging.getLogger('tooly_bot.music')

class Music(commands.Cog):
    """Music search functionality"""
    
    def __init__(self, bot):
        self.bot = bot
    
    @discord.slash_command(name='image', description='Search for an image using Pexels')
    @option("query", description="What to search for")
    async def image(self, ctx, query: str):
        await ctx.defer()
        try:
            PEXELS_API_KEY = os.getenv('PEXELS_API_KEY')
            if not PEXELS_API_KEY:
                await ctx.followup.send('❌ Pexels API key not configured!')
                return

            url = f'https://api.pexels.com/v1/search?query={query}&per_page=1'
            headers = {'Authorization': PEXELS_API_KEY}

            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as response:
                    if response.status != 200:
                        await ctx.followup.send('❌ Failed to contact Pexels API.')
                        return
                    data = await response.json()
                    if not data.get('photos'):
                        await ctx.followup.send(f'❌ No images found for "{query}".')
                        return
                    
                    photo = data['photos'][0]
                    image_url = photo['src']['large']
                    photographer = photo.get('photographer', 'Unknown')
                    photographer_url = photo.get('photographer_url', '')

            embed = discord.Embed(
                title=f'🔍 {query}',
                color=0xFF69B4,
                timestamp=datetime.utcnow(),
                description=f'Photo by [{photographer}]({photographer_url}) on Pexels'
            )
            embed.set_image(url=image_url)
            embed.set_footer(text=f'Requested by {ctx.author.name}')

            await ctx.followup.send(embed=embed)
        except Exception as e:
            logger.error(f'Image search error: {e}')
            await ctx.followup.send('❌ Failed to search for images')
    
    @discord.slash_command(name='music', description='Search for a song')
    @option("song", description="Song name")
    @option("artist", description="Artist name")
    async def music(self, ctx, song: str, artist: str):
        await ctx.defer()
        try:
            async with aiohttp.ClientSession() as session:
                youtube_query = f'{artist} {song} official music video'.replace(' ', '+')
                youtube_search_url = f'https://www.youtube.com/results?search_query={youtube_query}'

                song_clean = re.sub(r'[^a-z0-9]', '', song.lower())
                artist_clean = re.sub(r'[^a-z0-9]', '', artist.lower())
                lyrics_url = f'https://www.azlyrics.com/lyrics/{artist_clean}/{song_clean}.html'

                itunes_url = f'https://itunes.apple.com/search?term={artist}+{song}&entity=song&limit=1'
                async with session.get(itunes_url) as resp:
                    itunes_data = await resp.json()

                embed = discord.Embed(
                    title=f'🎵 {song}',
                    description=f'by **{artist}**',
                    color=0xFF69B4,
                    timestamp=datetime.utcnow()
                )

                if itunes_data.get('results') and len(itunes_data['results']) > 0:
                    result = itunes_data['results'][0]
                    album_art = result.get('artworkUrl100', '').replace('100x100', '600x600')
                    if album_art:
                        embed.set_thumbnail(url=album_art)
                    if result.get('collectionName'):
                        embed.add_field(name='💿 Album', value=result['collectionName'], inline=True)
                    if result.get('releaseDate'):
                        year = result['releaseDate'][:4]
                        embed.add_field(name='📅 Year', value=year, inline=True)
                    if result.get('trackTimeMillis'):
                        duration = result['trackTimeMillis'] // 1000
                        minutes = duration // 60
                        seconds = duration % 60
                        embed.add_field(name='⏱️ Duration', value=f'{minutes}:{seconds:02d}', inline=True)
                    if result.get('trackViewUrl'):
                        embed.add_field(name='🎧 Listen on Apple Music', value=f'[Open in iTunes]({result["trackViewUrl"]})', inline=False)

                embed.add_field(name='📺 Watch on YouTube', value=f'[Search for music video]({youtube_search_url})', inline=False)
                embed.add_field(name='📝 Read Lyrics', value=f'[View on AZLyrics]({lyrics_url})', inline=False)
                embed.set_footer(text=f'Requested by {ctx.author.display_name}')

                await ctx.followup.send(embed=embed)

        except Exception as e:
            logger.error(f'Music search error: {e}')
            await ctx.followup.send('❌ Failed to find song info')

def setup(bot):
    bot.add_cog(Music(bot))