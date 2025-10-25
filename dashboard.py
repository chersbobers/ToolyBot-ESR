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
            <title>Tooly Bot Dashboard</title>
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <style>
                * { margin: 0; padding: 0; box-sizing: border-box; }
                body {
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    min-height: 100vh;
                    padding: 20px;
                }
                .container {
                    max-width: 1200px;
                    margin: 0 auto;
                }
                .header {
                    background: rgba(255,255,255,0.95);
                    padding: 30px;
                    border-radius: 15px;
                    box-shadow: 0 10px 40px rgba(0,0,0,0.2);
                    margin-bottom: 30px;
                    text-align: center;
                }
                .header h1 {
                    color: #667eea;
                    font-size: 2.5em;
                    margin-bottom: 10px;
                }
                .header p {
                    color: #666;
                    font-size: 1.1em;
                }
                .stats-grid {
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                    gap: 20px;
                    margin-bottom: 30px;
                }
                .stat-card {
                    background: rgba(255,255,255,0.95);
                    padding: 25px;
                    border-radius: 15px;
                    box-shadow: 0 5px 20px rgba(0,0,0,0.1);
                    transition: transform 0.3s ease;
                }
                .stat-card:hover {
                    transform: translateY(-5px);
                }
                .stat-card h3 {
                    color: #667eea;
                    font-size: 0.9em;
                    text-transform: uppercase;
                    letter-spacing: 1px;
                    margin-bottom: 10px;
                }
                .stat-card .value {
                    font-size: 2.5em;
                    font-weight: bold;
                    color: #333;
                }
                .stat-card .label {
                    color: #999;
                    font-size: 0.9em;
                    margin-top: 5px;
                }
                .info-section {
                    background: rgba(255,255,255,0.95);
                    padding: 30px;
                    border-radius: 15px;
                    box-shadow: 0 5px 20px rgba(0,0,0,0.1);
                    margin-bottom: 20px;
                }
                .info-section h2 {
                    color: #667eea;
                    margin-bottom: 20px;
                    font-size: 1.8em;
                }
                .feature-list {
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                    gap: 15px;
                }
                .feature {
                    padding: 15px;
                    background: #f8f9fa;
                    border-radius: 10px;
                    border-left: 4px solid #667eea;
                }
                .feature-icon {
                    font-size: 1.5em;
                    margin-right: 10px;
                }
                .status {
                    display: inline-block;
                    padding: 8px 16px;
                    background: #28a745;
                    color: white;
                    border-radius: 20px;
                    font-weight: bold;
                    font-size: 0.9em;
                }
                .api-section {
                    background: rgba(255,255,255,0.95);
                    padding: 30px;
                    border-radius: 15px;
                    box-shadow: 0 5px 20px rgba(0,0,0,0.1);
                }
                .endpoint {
                    background: #f8f9fa;
                    padding: 15px;
                    border-radius: 8px;
                    margin-bottom: 15px;
                    font-family: 'Courier New', monospace;
                }
                .method {
                    display: inline-block;
                    padding: 4px 12px;
                    background: #667eea;
                    color: white;
                    border-radius: 5px;
                    font-weight: bold;
                    margin-right: 10px;
                    font-size: 0.8em;
                }
                @media (max-width: 768px) {
                    .header h1 { font-size: 1.8em; }
                    .stat-card .value { font-size: 2em; }
                    .stats-grid { grid-template-columns: 1fr; }
                }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🤖 Tooly Bot Dashboard</h1>
                    <p>Real-time Statistics & Information</p>
                    <div style="margin-top: 15px;">
                        <span class="status">● ONLINE</span>
                    </div>
                </div>
                
                <div class="stats-grid">
                    <div class="stat-card">
                        <h3>📊 Servers</h3>
                        <div class="value" id="servers">-</div>
                        <div class="label">Total Guilds</div>
                    </div>
                    <div class="stat-card">
                        <h3>👥 Users</h3>
                        <div class="value" id="users">-</div>
                        <div class="label">Registered Users</div>
                    </div>
                    <div class="stat-card">
                        <h3>💰 Economy</h3>
                        <div class="value" id="coins">-</div>
                        <div class="label">Total Coins</div>
                    </div>
                    <div class="stat-card">
                        <h3>🎣 Fish</h3>
                        <div class="value" id="fish">-</div>
                        <div class="label">Total Caught</div>
                    </div>
                </div>
                
                <div class="info-section">
                    <h2>✨ Features</h2>
                    <div class="feature-list">
                        <div class="feature">
                            <span class="feature-icon">⭐</span>
                            <strong>XP & Leveling</strong>
                        </div>
                        <div class="feature">
                            <span class="feature-icon">💵</span>
                            <strong>Economy System</strong>
                        </div>
                        <div class="feature">
                            <span class="feature-icon">🎣</span>
                            <strong>Fishing (18 types)</strong>
                        </div>
                        <div class="feature">
                            <span class="feature-icon">🎰</span>
                            <strong>4 Gambling Games</strong>
                        </div>
                        <div class="feature">
                            <span class="feature-icon">🎭</span>
                            <strong>Reaction Roles</strong>
                        </div>
                        <div class="feature">
                            <span class="feature-icon">🛡️</span>
                            <strong>Auto-Moderation</strong>
                        </div>
                        <div class="feature">
                            <span class="feature-icon">📺</span>
                            <strong>YouTube Alerts</strong>
                        </div>
                        <div class="feature">
                            <span class="feature-icon">🎮</span>
                            <strong>Fun Commands</strong>
                        </div>
                    </div>
                </div>
                
                <div class="api-section">
                    <h2>🔌 API Endpoints</h2>
                    <div class="endpoint">
                        <span class="method">GET</span>
                        <span>/api/stats</span>
                        <div style="color: #666; margin-top: 5px; font-size: 0.9em;">Get bot statistics</div>
                    </div>
                    <div class="endpoint">
                        <span class="method">GET</span>
                        <span>/api/leaderboard</span>
                        <div style="color: #666; margin-top: 5px; font-size: 0.9em;">Get top 10 users by level</div>
                    </div>
                    <div class="endpoint">
                        <span class="method">GET</span>
                        <span>/api/user/:id</span>
                        <div style="color: #666; margin-top: 5px; font-size: 0.9em;">Get user information</div>
                    </div>
                </div>
            </div>
            
            <script>
                async function loadStats() {
                    try {
                        const response = await fetch('/api/stats');
                        const data = await response.json();
                        
                        document.getElementById('servers').textContent = data.servers.toLocaleString();
                        document.getElementById('users').textContent = data.users.toLocaleString();
                        document.getElementById('coins').textContent = data.total_coins.toLocaleString();
                        document.getElementById('fish').textContent = data.total_fish.toLocaleString();
                    } catch (error) {
                        console.error('Failed to load stats:', error);
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