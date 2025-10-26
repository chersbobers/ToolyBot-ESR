from aiohttp import web
import json
from datetime import datetime
from utils.database import bot_data, server_settings, reaction_roles

def create_app(bot):
    app = web.Application()
    
    async def index(request):
        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Tooly Bot Status</title>
            <meta name="viewport" content="width=device-width, initial-scale=1">
        </head>
        <body>
            <h1>Tooly Bot Status</h1>
            <p><strong>Status:</strong> <span id="status">ONLINE</span></p>
            <p><strong>Servers:</strong> <span id="servers">Loading...</span></p>
            <p><strong>Users:</strong> <span id="users">Loading...</span></p>
            <p><strong>Total Coins:</strong> <span id="coins">Loading...</span></p>
            <p><strong>Total Fish Caught:</strong> <span id="fish">Loading...</span></p>
            <p><strong>Commands:</strong> <span id="commands">Loading...</span></p>
            <p><strong>Reaction Roles:</strong> <span id="reaction_roles">Loading...</span></p>
            
            <hr>
            
            <h2>Features</h2>
            <ul>
                <li>XP & Leveling</li>
                <li>Economy System</li>
                <li>Fishing (18 types)</li>
                <li>4 Gambling Games</li>
                <li>Reaction Roles</li>
                <li>Auto-Moderation</li>
                <li>YouTube Alerts</li>
                <li>Fun Commands</li>
            </ul>
            
            <hr>
            
            <h2>API Endpoints</h2>
            <ul>
                <li><strong>GET</strong> /api/stats - Get bot statistics</li>
                <li><strong>GET</strong> /api/leaderboard - Get top 10 users by level</li>
                <li><strong>GET</strong> /api/user/:id - Get user information</li>
            </ul>
            
            <script>
                async function loadStats() {
                    try {
                        const response = await fetch('/api/stats');
                        const data = await response.json();
                        
                        document.getElementById('servers').textContent = data.servers.toLocaleString();
                        document.getElementById('users').textContent = data.users.toLocaleString();
                        document.getElementById('coins').textContent = data.total_coins.toLocaleString();
                        document.getElementById('fish').textContent = data.total_fish.toLocaleString();
                        document.getElementById('commands').textContent = data.commands.toLocaleString();
                        document.getElementById('reaction_roles').textContent = data.reaction_roles.toLocaleString();
                        document.getElementById('status').textContent = 'ONLINE';
                    } catch (error) {
                        console.error('Failed to load stats:', error);
                        document.getElementById('status').textContent = 'ERROR';
                    }
                }
                
                loadStats();
                setInterval(loadStats, 30000); // Refresh every 30 seconds
            </script>
        </body>
        </html>
        """
        return web.Response(text=html, content_type='text/html')
    
    async def health(request):
        return web.Response(text="🤖 Tooly Bot is running!")
    
    async def api_stats(request):
        total_users = len(bot_data.data.get('levels', {}))
        total_coins = sum(
            e.get('coins', 0) + e.get('bank', 0) 
            for e in bot_data.data.get('economy', {}).values()
        )
        total_fish = sum(
            e.get('fishCaught', 0) 
            for e in bot_data.data.get('economy', {}).values()
        )
        
        stats = {
            'servers': len(bot.guilds),
            'users': total_users,
            'total_coins': total_coins,
            'total_fish': total_fish,
            'commands': len([cmd for cmd in bot.walk_application_commands()]),
            'reaction_roles': len(reaction_roles.data)
        }
        
        return web.json_response(stats)
    
    async def api_leaderboard(request):
        all_users = sorted(
            bot_data.data['levels'].items(),
            key=lambda x: (x[1]['level'], x[1]['xp']),
            reverse=True
        )[:10]
        
        leaderboard = []
        for user_id, data in all_users:
            economy_data = bot_data.get_user_economy(user_id)
            leaderboard.append({
                'user_id': user_id,
                'level': data['level'],
                'xp': data['xp'],
                'coins': economy_data.get('coins', 0) + economy_data.get('bank', 0)
            })
        
        return web.json_response(leaderboard)
    
    async def api_user(request):
        user_id = request.match_info.get('id')
        
        if not user_id or user_id not in bot_data.data['levels']:
            return web.json_response({'error': 'User not found'}, status=404)
        
        level_data = bot_data.get_user_level(user_id)
        economy_data = bot_data.get_user_economy(user_id)
        
        user_info = {
            'user_id': user_id,
            'level': level_data['level'],
            'xp': level_data['xp'],
            'coins': economy_data['coins'],
            'bank': economy_data['bank'],
            'fish_caught': economy_data.get('fishCaught', 0),
            'gambling_wins': economy_data.get('gamblingWins', 0),
            'gambling_losses': economy_data.get('gamblingLosses', 0)
        }
        
        return web.json_response(user_info)
    
    # Routes
    app.router.add_get('/', index)
    app.router.add_get('/health', health)
    app.router.add_get('/api/stats', api_stats)
    app.router.add_get('/api/leaderboard', api_leaderboard)
    app.router.add_get('/api/user/{id}', api_user)
    
    return app