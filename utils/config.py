"""Configuration constants for Tooly Bot"""

class Config:
    # Cooldowns (in seconds)
    XP_COOLDOWN = 60
    DAILY_COOLDOWN = 86400
    WORK_COOLDOWN = 900
    FISH_COOLDOWN = 120
    GAMBLE_COOLDOWN = 0
    NAME_MENTION_COOLDOWN = 30
    
    # XP & Leveling
    XP_MIN, XP_MAX = 10, 25
    XP_PER_LEVEL = 100
    LEVEL_UP_MULTIPLIER = 50
    
    # Economy
    DAILY_MIN, DAILY_MAX = 500, 1000
    WORK_MIN, WORK_MAX = 100, 300
    GAMBLE_MIN = 10
    GAMBLE_MAX_PERCENT = 0.5
    
    # Moderation
    WARN_THRESHOLD = 3
    TIMEOUT_DURATION = 60
    
    # Files & Intervals
    DATA_FILE = 'data/botdata.json'
    SETTINGS_FILE = 'data/server_settings.json'
    REACTIONS_FILE = 'data/reaction_roles.json'
    AUTOSAVE_INTERVAL = 300
    VIDEO_CHECK_INTERVAL = 300
    LEADERBOARD_UPDATE_INTERVAL = 3600

# Fish Types
FISH_TYPES = [
    {'emoji': '🐟', 'name': 'Common Fish', 'value': 50, 'weight': 50},
    {'emoji': '🐠', 'name': 'Tropical Fish', 'value': 100, 'weight': 30},
    {'emoji': '🦈', 'name': 'Shark', 'value': 300, 'weight': 10},
    {'emoji': '🐙', 'name': 'Octopus', 'value': 200, 'weight': 15},
    {'emoji': '🦀', 'name': 'Crab', 'value': 75, 'weight': 25},
    {'emoji': '🐢', 'name': 'Turtle', 'value': 150, 'weight': 20},
    {'emoji': '🦞', 'name': 'Lobster', 'value': 180, 'weight': 18},
    {'emoji': '🐡', 'name': 'Pufferfish', 'value': 220, 'weight': 12},
    {'emoji': '🦑', 'name': 'Squid', 'value': 140, 'weight': 22},
    {'emoji': '🐋', 'name': 'Whale', 'value': 500, 'weight': 5},
    {'emoji': '🐬', 'name': 'Dolphin', 'value': 350, 'weight': 8},
    {'emoji': '🦭', 'name': 'Seal', 'value': 280, 'weight': 9},
    {'emoji': '🐚', 'name': 'Pearl', 'value': 400, 'weight': 6},
    {'emoji': '⚓', 'name': 'Old Anchor', 'value': 250, 'weight': 8},
    {'emoji': '💎', 'name': 'Diamond', 'value': 1000, 'weight': 2},
    {'emoji': '🏆', 'name': 'Golden Trophy', 'value': 1500, 'weight': 1},
    {'emoji': '👢', 'name': 'Old Boot', 'value': 10, 'weight': 40},
    {'emoji': '🥫', 'name': 'Tin Can', 'value': 5, 'weight': 35},
]

# Gambling Games
GAMBLE_GAMES = {
    'slots': {
        'name': '🎰 Slot Machine',
        'symbols': ['🍒', '🍋', '🍊', '🍇', '💎', '7️⃣'],
        'payouts': {3: 5.0, 2: 2.0}
    },
    'dice': {
        'name': '🎲 Dice Roll',
        'win_rate': 0.48,
        'multiplier_range': (1.5, 2.8)
    },
    'coinflip': {
        'name': '🪙 Coin Flip',
        'win_rate': 0.49,
        'multiplier': 2.0
    },
    'roulette': {
        'name': '🎡 Roulette',
        'colors': ['🔴', '⚫', '🟢'],
        'payouts': {'color': 2.0, 'green': 14.0}
    }
}