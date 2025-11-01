from aiohttp import web
import aiohttp_session
import aiohttp
from .utils import get_guild_config, update_guild_config, get_guild_stats, check_user_permissions

async def handle_api_guilds(request):
    """Get user's guilds where they have admin permissions"""
    session = await aiohttp_session.get_session(request)
    if 'user' not in session:
        return web.json_response({'error': 'Not authenticated'}, status=401)
    
    # Get user's guilds from Discord
    async with aiohttp.ClientSession() as http_session:
        headers = {'Authorization': f"Bearer {session['access_token']}"}
        async with http_session.get('https://discord.com/api/users/@me/guilds', headers=headers) as resp:
            if resp.status != 200:
                return web.json_response({'error': 'Failed to fetch guilds'}, status=500)
            user_guilds = await resp.json()
    
    # Filter guilds where user has admin permissions (0x8)
    admin_guilds = [g for g in user_guilds if (int(g['permissions']) & 0x8) == 0x8]
    
    # Check which guilds have the bot
    bot = request.app['bot']
    for guild in admin_guilds:
        guild['bot_in_guild'] = bot.get_guild(int(guild['id'])) is not None
    
    return web.json_response(admin_guilds)

async def handle_api_guild(request):
    """Get guild information"""
    session = await aiohttp_session.get_session(request)
    if 'user' not in session:
        return web.json_response({'error': 'Not authenticated'}, status=401)
    
    guild_id = request.match_info['guild_id']
    
    # Check permissions
    has_permission = await check_user_permissions(session, guild_id, session['access_token'])
    if not has_permission:
        return web.json_response({'error': 'No permission'}, status=403)
    
    bot = request.app['bot']
    guild = bot.get_guild(int(guild_id))
    
    if not guild:
        return web.json_response({'error': 'Guild not found or bot not in guild'}, status=404)
    
    return web.json_response({
        'id': str(guild.id),
        'name': guild.name,
        'member_count': guild.member_count,
        'icon': guild.icon.url if guild.icon else None,
        'owner_id': str(guild.owner_id)
    })

async def handle_api_guild_stats(request):
    """Get guild statistics"""
    session = await aiohttp_session.get_session(request)
    if 'user' not in session:
        return web.json_response({'error': 'Not authenticated'}, status=401)
    
    guild_id = request.match_info['guild_id']
    
    # Check permissions
    has_permission = await check_user_permissions(session, guild_id, session['access_token'])
    if not has_permission:
        return web.json_response({'error': 'No permission'}, status=403)
    
    db = request.app['db']
    bot = request.app['bot']
    
    stats = await get_guild_stats(db, bot, guild_id)
    return web.json_response(stats)

async def handle_api_get_config(request):
    """Get guild configuration"""
    session = await aiohttp_session.get_session(request)
    if 'user' not in session:
        return web.json_response({'error': 'Not authenticated'}, status=401)
    
    guild_id = request.match_info['guild_id']
    
    # Check permissions
    has_permission = await check_user_permissions(session, guild_id, session['access_token'])
    if not has_permission:
        return web.json_response({'error': 'No permission'}, status=403)
    
    db = request.app['db']
    config = await get_guild_config(db, guild_id)
    
    # Remove MongoDB _id field
    config.pop('_id', None)
    
    return web.json_response(config)

async def handle_api_update_config(request):
    """Update guild configuration"""
    session = await aiohttp_session.get_session(request)
    if 'user' not in session:
        return web.json_response({'error': 'Not authenticated'}, status=401)
    
    guild_id = request.match_info['guild_id']
    
    # Check permissions
    has_permission = await check_user_permissions(session, guild_id, session['access_token'])
    if not has_permission:
        return web.json_response({'error': 'No permission'}, status=403)
    
    try:
        data = await request.json()
    except:
        return web.json_response({'error': 'Invalid JSON'}, status=400)
    
    db = request.app['db']
    
    # Ensure guild_id is set
    data['guild_id'] = str(guild_id)
    
    await update_guild_config(db, guild_id, data)
    
    return web.json_response({'success': True})

async def handle_api_leaderboard(request):
    """Get guild leaderboard"""
    session = await aiohttp_session.get_session(request)
    if 'user' not in session:
        return web.json_response({'error': 'Not authenticated'}, status=401)
    
    guild_id = request.match_info['guild_id']
    
    # Check permissions
    has_permission = await check_user_permissions(session, guild_id, session['access_token'])
    if not has_permission:
        return web.json_response({'error': 'No permission'}, status=403)
    
    db = request.app['db']
    bot = request.app['bot']
    
    # Get top users by XP
    users = await db.users.find(
        {'guild_id': str(guild_id)},
        {'user_id': 1, 'xp': 1, 'level': 1, 'balance': 1}
    ).sort('xp', -1).limit(50).to_list(50)
    
    # Try to get usernames from Discord
    guild = bot.get_guild(int(guild_id))
    if guild:
        for user in users:
            member = guild.get_member(int(user['user_id']))
            if member:
                user['username'] = member.display_name
    
    return web.json_response(users)