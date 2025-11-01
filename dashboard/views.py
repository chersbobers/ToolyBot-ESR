from aiohttp import web
import aiohttp_session

async def handle_home(request):
    """Home page"""
    session = await aiohttp_session.get_session(request)
    logged_in = 'user' in session
    
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Tooly Bot Dashboard</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                display: flex;
                align-items: center;
                justify-content: center;
                padding: 1rem;
            }
            .container {
                background: white;
                padding: 3rem;
                border-radius: 20px;
                box-shadow: 0 20px 60px rgba(0,0,0,0.3);
                text-align: center;
                max-width: 500px;
                width: 100%;
            }
            h1 { color: #333; margin-bottom: 1rem; font-size: 2.5rem; }
            p { color: #666; margin-bottom: 2rem; font-size: 1.1rem; }
            .btn {
                display: inline-block;
                padding: 1rem 2rem;
                background: #5865F2;
                color: white;
                text-decoration: none;
                border-radius: 8px;
                font-weight: bold;
                transition: all 0.3s;
            }
            .btn:hover {
                background: #4752C4;
                transform: translateY(-2px);
                box-shadow: 0 5px 15px rgba(88,101,242,0.4);
            }
            .features {
                margin-top: 2rem;
                text-align: left;
            }
            .feature {
                padding: 0.5rem 0;
                color: #555;
            }
            .feature::before {
                content: "✓ ";
                color: #5865F2;
                font-weight: bold;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🛠️ Tooly Bot</h1>
            <p>Powerful Discord bot management dashboard</p>
            """ + (
        "<a href='/dashboard' class='btn'>Go to Dashboard</a>" if logged_in 
        else "<a href='/login' class='btn'>Login with Discord</a>"
    ) + """
            <div class="features">
                <div class="feature">Leveling System Configuration</div>
                <div class="feature">Economy Settings</div>
                <div class="feature">Moderation Tools</div>
                <div class="feature">Real-time Statistics</div>
                <div class="feature">Member Leaderboards</div>
            </div>
        </div>
    </body>
    </html>
    """
    return web.Response(text=html, content_type='text/html')

async def handle_dashboard(request):
    """Server selection page"""
    session = await aiohttp_session.get_session(request)
    if 'user' not in session:
        return web.Response(status=302, headers={'Location': '/login'})
    
    user = session['user']
    avatar_url = f"https://cdn.discordapp.com/avatars/{user['id']}/{user['avatar']}.png" if user.get('avatar') else "https://cdn.discordapp.com/embed/avatars/0.png"
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Tooly Bot - Dashboard</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: #f5f5f5;
                min-height: 100vh;
            }}
            .navbar {{
                background: #5865F2;
                color: white;
                padding: 1rem 2rem;
                display: flex;
                justify-content: space-between;
                align-items: center;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }}
            .navbar h1 {{ font-size: 1.5rem; }}
            .user-info {{
                display: flex;
                align-items: center;
                gap: 1rem;
            }}
            .user-avatar {{
                width: 40px;
                height: 40px;
                border-radius: 50%;
            }}
            .btn {{
                padding: 0.5rem 1rem;
                background: white;
                color: #5865F2;
                text-decoration: none;
                border-radius: 5px;
                font-weight: bold;
                cursor: pointer;
                border: none;
            }}
            .container {{
                max-width: 1200px;
                margin: 2rem auto;
                padding: 0 2rem;
            }}
            .guilds-grid {{
                display: grid;
                grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
                gap: 1.5rem;
                margin-top: 2rem;
            }}
            .guild-card {{
                background: white;
                padding: 1.5rem;
                border-radius: 10px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                transition: transform 0.2s;
            }}
            .guild-card:hover {{
                transform: translateY(-5px);
                box-shadow: 0 5px 20px rgba(0,0,0,0.15);
            }}
            .guild-icon {{
                width: 60px;
                height: 60px;
                border-radius: 50%;
                margin-bottom: 1rem;
            }}
            .guild-name {{
                font-size: 1.2rem;
                font-weight: bold;
                margin-bottom: 0.5rem;
                color: #333;
            }}
            .guild-info {{
                color: #666;
                font-size: 0.9rem;
                margin-bottom: 1rem;
            }}
            .guild-btn {{
                display: block;
                padding: 0.75rem;
                background: #5865F2;
                color: white;
                text-decoration: none;
                border-radius: 5px;
                text-align: center;
                font-weight: bold;
                transition: background 0.2s;
            }}
            .guild-btn:hover {{
                background: #4752C4;
            }}
            .guild-btn.add {{
                background: #43b581;
            }}
            .guild-btn.add:hover {{
                background: #3ca374;
            }}
            .loading {{
                text-align: center;
                padding: 3rem;
                color: #666;
            }}
        </style>
    </head>
    <body>
        <div class="navbar">
            <h1>🛠️ Tooly Bot Dashboard</h1>
            <div class="user-info">
                <img class="user-avatar" src="{avatar_url}" alt="Avatar">
                <span>{user['username']}</span>
                <a href="/logout" class="btn">Logout</a>
            </div>
        </div>
        
        <div class="container">
            <h2>Select a Server</h2>
            <div class="guilds-grid" id="guilds">
                <div class="loading">Loading your servers...</div>
            </div>
        </div>
        
        <script>
            async function loadGuilds() {{
                const response = await fetch('/api/guilds');
                const guilds = await response.json();
                
                const container = document.getElementById('guilds');
                container.innerHTML = '';
                
                if (guilds.length === 0) {{
                    container.innerHTML = '<div class="loading">No servers found with admin permissions.</div>';
                    return;
                }}
                
                guilds.forEach(guild => {{
                    const card = document.createElement('div');
                    card.className = 'guild-card';
                    
                    const iconUrl = guild.icon 
                        ? `https://cdn.discordapp.com/icons/${{guild.id}}/${{guild.icon}}.png`
                        : 'https://cdn.discordapp.com/embed/avatars/0.png';
                    
                    card.innerHTML = `
                        <img class="guild-icon" src="${{iconUrl}}" alt="${{guild.name}}">
                        <div class="guild-name">${{guild.name}}</div>
                        <div class="guild-info">${{guild.approximate_member_count || 'Unknown'}} members</div>
                        ${{guild.bot_in_guild 
                            ? `<a href="/dashboard/${{guild.id}}" class="guild-btn">Manage Server</a>`
                            : `<a href="https://discord.com/api/oauth2/authorize?client_id={request.app['config']['CLIENT_ID']}&permissions=8&scope=bot%20applications.commands&guild_id=${{guild.id}}" class="guild-btn add">Add Bot</a>`
                        }}
                    `;
                    
                    container.appendChild(card);
                }});
            }}
            
            loadGuilds();
        </script>
    </body>
    </html>
    """
    return web.Response(text=html, content_type='text/html')

async def handle_guild_dashboard(request):
    """Individual guild management page"""
    session = await aiohttp_session.get_session(request)
    if 'user' not in session:
        return web.Response(status=302, headers={'Location': '/login'})
    
    guild_id = request.match_info['guild_id']
    
    # Check permissions
    from .utils import check_user_permissions
    has_permission = await check_user_permissions(session, guild_id, session['access_token'])
    if not has_permission:
        return web.Response(text="You don't have permission to manage this server", status=403)
    
    user = session['user']
    avatar_url = f"https://cdn.discordapp.com/avatars/{user['id']}/{user['avatar']}.png" if user.get('avatar') else "https://cdn.discordapp.com/embed/avatars/0.png"
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Tooly Bot - Server Management</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: #f5f5f5;
                min-height: 100vh;
            }}
            .navbar {{
                background: #5865F2;
                color: white;
                padding: 1rem 2rem;
                display: flex;
                justify-content: space-between;
                align-items: center;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }}
            .navbar h1 {{ font-size: 1.5rem; }}
            .user-info {{
                display: flex;
                align-items: center;
                gap: 1rem;
            }}
            .user-avatar {{
                width: 40px;
                height: 40px;
                border-radius: 50%;
            }}
            .btn {{
                padding: 0.5rem 1rem;
                background: white;
                color: #5865F2;
                text-decoration: none;
                border-radius: 5px;
                font-weight: bold;
                cursor: pointer;
                border: none;
            }}
            .container {{
                max-width: 1400px;
                margin: 2rem auto;
                padding: 0 2rem;
                display: grid;
                grid-template-columns: 250px 1fr;
                gap: 2rem;
            }}
            .sidebar {{
                background: white;
                padding: 1.5rem;
                border-radius: 10px;
                height: fit-content;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }}
            .sidebar h3 {{
                margin-bottom: 1rem;
                color: #333;
            }}
            .nav-item {{
                padding: 0.75rem 1rem;
                margin-bottom: 0.5rem;
                border-radius: 5px;
                cursor: pointer;
                transition: background 0.2s;
                color: #666;
            }}
            .nav-item:hover {{
                background: #f0f0f0;
            }}
            .nav-item.active {{
                background: #5865F2;
                color: white;
            }}
            .main-content {{
                background: white;
                padding: 2rem;
                border-radius: 10px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }}
            .stats-grid {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 1.5rem;
                margin-bottom: 2rem;
            }}
            .stat-card {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 1.5rem;
                border-radius: 10px;
                box-shadow: 0 4px 15px rgba(0,0,0,0.1);
            }}
            .stat-value {{
                font-size: 2rem;
                font-weight: bold;
                margin-bottom: 0.5rem;
            }}
            .stat-label {{
                font-size: 0.9rem;
                opacity: 0.9;
            }}
            .section {{
                display: none;
            }}
            .section.active {{
                display: block;
            }}
            .form-group {{
                margin-bottom: 1.5rem;
            }}
            .form-group label {{
                display: block;
                margin-bottom: 0.5rem;
                font-weight: bold;
                color: #333;
            }}
            .form-group input, .form-group textarea, .form-group select {{
                width: 100%;
                padding: 0.75rem;
                border: 1px solid #ddd;
                border-radius: 5px;
                font-size: 1rem;
            }}
            .form-group input[type="checkbox"] {{
                width: auto;
                margin-right: 0.5rem;
            }}
            .save-btn {{
                background: #43b581;
                color: white;
                padding: 0.75rem 2rem;
                border: none;
                border-radius: 5px;
                font-weight: bold;
                cursor: pointer;
                font-size: 1rem;
            }}
            .save-btn:hover {{
                background: #3ca374;
            }}
            .alert {{
                padding: 1rem;
                border-radius: 5px;
                margin-bottom: 1rem;
                display: none;
            }}
            .alert.success {{
                background: #43b581;
                color: white;
            }}
            .alert.error {{
                background: #f04747;
                color: white;
            }}
            .leaderboard-table {{
                width: 100%;
                border-collapse: collapse;
            }}
            .leaderboard-table th {{
                background: #5865F2;
                color: white;
                padding: 1rem;
                text-align: left;
            }}
            .leaderboard-table td {{
                padding: 1rem;
                border-bottom: 1px solid #eee;
            }}
            .leaderboard-table tr:hover {{
                background: #f9f9f9;
            }}
        </style>
    </head>
    <body>
        <div class="navbar">
            <h1>🛠️ <span id="guild-name">Loading...</span></h1>
            <div class="user-info">
                <a href="/dashboard" class="btn" style="margin-right: 1rem;">← Back to Servers</a>
                <img class="user-avatar" src="{avatar_url}" alt="Avatar">
                <span>{user['username']}</span>
                <a href="/logout" class="btn">Logout</a>
            </div>
        </div>
        
        <div class="container">
            <div class="sidebar">
                <h3>Settings</h3>
                <div class="nav-item active" data-section="overview">📊 Overview</div>
                <div class="nav-item" data-section="leveling">📈 Leveling</div>
                <div class="nav-item" data-section="economy">💰 Economy</div>
                <div class="nav-item" data-section="moderation">🛡️ Moderation</div>
                <div class="nav-item" data-section="leaderboard">🏆 Leaderboard</div>
            </div>
            
            <div class="main-content">
                <div id="alert" class="alert"></div>
                
                <!-- Overview Section -->
                <div class="section active" id="overview">
                    <h2>Server Overview</h2>
                    <div class="stats-grid">
                        <div class="stat-card">
                            <div class="stat-value" id="stat-members">-</div>
                            <div class="stat-label">Total Members</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-value" id="stat-active">-</div>
                            <div class="stat-label">Active Users</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-value" id="stat-xp">-</div>
                            <div class="stat-label">Total XP Earned</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-value" id="stat-economy">-</div>
                            <div class="stat-label">Total Economy</div>
                        </div>
                    </div>
                </div>
                
                <!-- Leveling Section -->
                <div class="section" id="leveling">
                    <h2>Leveling Configuration</h2>
                    <form id="leveling-form">
                        <div class="form-group">
                            <label>
                                <input type="checkbox" id="leveling-enabled"> Enable Leveling System
                            </label>
                        </div>
                        <div class="form-group">
                            <label>XP Rate Multiplier</label>
                            <input type="number" id="xp-rate" step="0.1" min="0.1" max="10">
                        </div>
                        <div class="form-group">
                            <label>Minimum XP per Message</label>
                            <input type="number" id="xp-min" min="1" max="100">
                        </div>
                        <div class="form-group">
                            <label>Maximum XP per Message</label>
                            <input type="number" id="xp-max" min="1" max="100">
                        </div>
                        <div class="form-group">
                            <label>Level Up Message</label>
                            <input type="text" id="level-up-message" placeholder="{{user}} reached level {{level}}!">
                            <small style="color: #666;">Use {{user}} for mention and {{level}} for level number</small>
                        </div>
                        <button type="submit" class="save-btn">Save Changes</button>
                    </form>
                </div>
                
                <!-- Economy Section -->
                <div class="section" id="economy">
                    <h2>Economy Configuration</h2>
                    <form id="economy-form">
                        <div class="form-group">
                            <label>
                                <input type="checkbox" id="economy-enabled"> Enable Economy System
                            </label>
                        </div>
                        <div class="form-group">
                            <label>Daily Reward Amount</label>
                            <input type="number" id="daily-amount" min="0">
                        </div>
                        <div class="form-group">
                            <label>Weekly Reward Amount</label>
                            <input type="number" id="weekly-amount" min="0">
                        </div>
                        <div class="form-group">
                            <label>Currency Name</label>
                            <input type="text" id="currency-name" placeholder="coins">
                        </div>
                        <div class="form-group">
                            <label>Currency Symbol</label>
                            <input type="text" id="currency-symbol" placeholder="🪙" maxlength="5">
                        </div>
                        <div class="form-group">
                            <label>Starting Balance</label>
                            <input type="number" id="starting-balance" min="0">
                        </div>
                        <button type="submit" class="save-btn">Save Changes</button>
                    </form>
                </div>
                
                <!-- Moderation Section -->
                <div class="section" id="moderation">
                    <h2>Moderation Configuration</h2>
                    <form id="moderation-form">
                        <div class="form-group">
                            <label>
                                <input type="checkbox" id="auto-mod"> Enable Auto-Moderation
                            </label>
                        </div>
                        <div class="form-group">
                            <label>Warn Threshold (before action)</label>
                            <input type="number" id="warn-threshold" min="1" max="10">
                        </div>
                        <button type="submit" class="save-btn">Save Changes</button>
                    </form>
                </div>
                
                <!-- Leaderboard Section -->
                <div class="section" id="leaderboard">
                    <h2>Server Leaderboard</h2>
                    <table class="leaderboard-table">
                        <thead>
                            <tr>
                                <th>Rank</th>
                                <th>User</th>
                                <th>Level</th>
                                <th>XP</th>
                                <th>Balance</th>
                            </tr>
                        </thead>
                        <tbody id="leaderboard-body">
                            <tr><td colspan="5" style="text-align: center; padding: 2rem;">Loading...</td></tr>
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
        
        <script>
            const guildId = '{guild_id}';
            let config = {{}};
            
            // Navigation
            document.querySelectorAll('.nav-item').forEach(item => {{
                item.addEventListener('click', () => {{
                    document.querySelectorAll('.nav-item').forEach(i => i.classList.remove('active'));
                    document.querySelectorAll('.section').forEach(s => s.classList.remove('active'));
                    item.classList.add('active');
                    document.getElementById(item.dataset.section).classList.add('active');
                }});
            }});
            
            // Load guild data
            async function loadGuildData() {{
                try {{
                    const [guildRes, statsRes, configRes] = await Promise.all([
                        fetch(`/api/guild/${{guildId}}`),
                        fetch(`/api/guild/${{guildId}}/stats`),
                        fetch(`/api/guild/${{guildId}}/config`)
                    ]);
                    
                    const guild = await guildRes.json();
                    const stats = await statsRes.json();
                    config = await configRes.json();
                    
                    document.getElementById('guild-name').textContent = guild.name;
                    document.getElementById('stat-members').textContent = stats.total_members.toLocaleString();
                    document.getElementById('stat-active').textContent = stats.active_users.toLocaleString();
                    document.getElementById('stat-xp').textContent = stats.total_xp_earned.toLocaleString();
                    document.getElementById('stat-economy').textContent = stats.total_economy.toLocaleString();
                    
                    // Populate forms
                    document.getElementById('leveling-enabled').checked = config.leveling.enabled;
                    document.getElementById('xp-rate').value = config.leveling.xp_rate;
                    document.getElementById('xp-min').value = config.leveling.xp_min;
                    document.getElementById('xp-max').value = config.leveling.xp_max;
                    document.getElementById('level-up-message').value = config.leveling.level_up_message;
                    
                    document.getElementById('economy-enabled').checked = config.economy.enabled;
                    document.getElementById('daily-amount').value = config.economy.daily_amount;
                    document.getElementById('weekly-amount').value = config.economy.weekly_amount;
                    document.getElementById('currency-name').value = config.economy.currency_name;
                    document.getElementById('currency-symbol').value = config.economy.currency_symbol;
                    document.getElementById('starting-balance').value = config.economy.starting_balance;
                    
                    document.getElementById('auto-mod').checked = config.moderation.auto_mod;
                    document.getElementById('warn-threshold').value = config.moderation.warn_threshold;
                }} catch (error) {{
                    showAlert('Failed to load guild data', 'error');
                }}
            }}
            
            // Load leaderboard
            async function loadLeaderboard() {{
                try {{
                    const res = await fetch(`/api/guild/${{guildId}}/leaderboard`);
                    const users = await res.json();
                    
                    const tbody = document.getElementById('leaderboard-body');
                    if (users.length === 0) {{
                        tbody.innerHTML = '<tr><td colspan="5" style="text-align: center; padding: 2rem;">No data yet</td></tr>';
                        return;
                    }}
                    
                    tbody.innerHTML = users.map((user, i) => `
                        <tr>
                            <td>${{i + 1}}</td>
                            <td>${{user.username || user.user_id}}</td>
                            <td>${{user.level}}</td>
                            <td>${{user.xp.toLocaleString()}}</td>
                            <td>${{(user.balance || 0).toLocaleString()}}</td>
                        </tr>
                    `).join('');
                }} catch (error) {{
                    document.getElementById('leaderboard-body').innerHTML = '<tr><td colspan="5" style="text-align: center; padding: 2rem;">Failed to load</td></tr>';
                }}
            }}
            
            // Save forms
            document.getElementById('leveling-form').addEventListener('submit', async (e) => {{
                e.preventDefault();
                config.leveling = {{
                    enabled: document.getElementById('leveling-enabled').checked,
                    xp_rate: parseFloat(document.getElementById('xp-rate').value),
                    xp_min: parseInt(document.getElementById('xp-min').value),
                    xp_max: parseInt(document.getElementById('xp-max').value),
                    level_up_message: document.getElementById('level-up-message').value,
                    level_up_channel: config.leveling.level_up_channel,
                    ignored_channels: config.leveling.ignored_channels,
                    ignored_roles: config.leveling.ignored_roles
                }};
                await saveConfig();
            }});
            
            document.getElementById('economy-form').addEventListener('submit', async (e) => {{
                e.preventDefault();
                config.economy = {{
                    enabled: document.getElementById('economy-enabled').checked,
                    daily_amount: parseInt(document.getElementById('daily-amount').value),
                    weekly_amount: parseInt(document.getElementById('weekly-amount').value),
                    currency_name: document.getElementById('currency-name').value,
                    currency_symbol: document.getElementById('currency-symbol').value,
                    starting_balance: parseInt(document.getElementById('starting-balance').value)
                }};
                await saveConfig();
            }});
            
            document.getElementById('moderation-form').addEventListener('submit', async (e) => {{
                e.preventDefault();
                config.moderation = {{
                    ...config.moderation,
                    auto_mod: document.getElementById('auto-mod').checked,
                    warn_threshold: parseInt(document.getElementById('warn-threshold').value)
                }};
                await saveConfig();
            }});
            
            async function saveConfig() {{
                try {{
                    const res = await fetch(`/api/guild/${{guildId}}/config`, {{
                        method: 'POST',
                        headers: {{ 'Content-Type': 'application/json' }},
                        body: JSON.stringify(config)
                    }});
                    
                    if (res.ok) {{
                        showAlert('Settings saved successfully!', 'success');
                    }} else {{
                        showAlert('Failed to save settings', 'error');
                    }}
                }} catch (error) {{
                    showAlert('Failed to save settings', 'error');
                }}
            }}
            
            function showAlert(message, type) {{
                const alert = document.getElementById('alert');
                alert.textContent = message;
                alert.className = `alert ${{type}}`;
                alert.style.display = 'block';
                setTimeout(() => {{ alert.style.display = 'none'; }}, 3000);
            }}
            
            // Initialize
            loadGuildData();
            loadLeaderboard();
        </script>
    </body>
    </html>
    """
    return web.Response(text=html, content_type='text/html')