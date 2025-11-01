import json
import os
import logging
from datetime import datetime, timezone
from copy import deepcopy
from typing import Dict, Any
import threading

logger = logging.getLogger('tooly_bot.database')

# Use persistent disk path on Render, fallback to local for development
DATA_DIR = os.getenv('RENDER_DISK_PATH', 'data')

class BotData:
    def __init__(self):
        self.data = {
            'levels': {},
            'economy': {},
            'warnings': {},
            'lastVideoId': {},
            'leaderboard_messages': {},
            'shop_items': {},
            'inventory': {}
        }
        self.filename = os.path.join(DATA_DIR, 'bot_data.json')
        self.lock = threading.Lock()  # Thread-safe saving
        os.makedirs(DATA_DIR, exist_ok=True)
        self.load()
    
    def load(self):
        """Load data from JSON file"""
        if os.path.exists(self.filename):
            try:
                with open(self.filename, 'r') as f:
                    self.data = json.load(f)
                logger.info(f'✅ Loaded data from {self.filename}')
            except Exception as e:
                logger.error(f'❌ Failed to load {self.filename}: {e}')
                self.data = {
                    'levels': {},
                    'economy': {},
                    'warnings': {},
                    'lastVideoId': {},
                    'leaderboard_messages': {},
                    'shop_items': {},
                    'inventory': {}
                }
        else:
            logger.info(f'📝 Creating new {self.filename}')
            self.save()
    
    def save(self):
        """Save data to JSON file with thread safety"""
        with self.lock:
            try:
                # Write to temp file first, then rename (atomic operation)
                temp_file = self.filename + '.tmp'
                with open(temp_file, 'w') as f:
                    json.dump(self.data, f, indent=2)
                os.replace(temp_file, self.filename)
                logger.debug(f'💾 Saved data to {self.filename}')
            except Exception as e:
                logger.error(f'❌ Failed to save {self.filename}: {e}')
    
    def get_user_level(self, guild_id: str, user_id: str) -> Dict[str, Any]:
        """Get user level data - RETURNS A COPY"""
        if 'levels' not in self.data:
            self.data['levels'] = {}
        if guild_id not in self.data['levels']:
            self.data['levels'][guild_id] = {}
        
        if user_id not in self.data['levels'][guild_id]:
            default_data = {
                'level': 1,
                'xp': 0,
                'lastMessage': 0
            }
            self.data['levels'][guild_id][user_id] = default_data
            self.save()
            logger.debug(f'Created new level entry for user {user_id} in guild {guild_id}')
        
        return deepcopy(self.data['levels'][guild_id][user_id])
    
    def set_user_level(self, guild_id: str, user_id: str, data: Dict[str, Any]):
        """Set user level data"""
        if 'levels' not in self.data:
            self.data['levels'] = {}
        if guild_id not in self.data['levels']:
            self.data['levels'][guild_id] = {}
        
        self.data['levels'][guild_id][user_id] = data
        self.save()
        logger.debug(f'Updated level for user {user_id} in guild {guild_id}')
    
    def get_user_economy(self, guild_id: str, user_id: str) -> Dict[str, Any]:
        """Get user economy data - RETURNS A COPY"""
        if 'economy' not in self.data:
            self.data['economy'] = {}
        if guild_id not in self.data['economy']:
            self.data['economy'][guild_id] = {}
        
        if user_id not in self.data['economy'][guild_id]:
            default_data = {
                'coins': 0,
                'bank': 0,
                'lastDaily': 0,
                'lastWork': 0
            }
            self.data['economy'][guild_id][user_id] = default_data
            self.save()
            logger.debug(f'Created new economy entry for user {user_id} in guild {guild_id}')
        
        return deepcopy(self.data['economy'][guild_id][user_id])
    
    def set_user_economy(self, guild_id: str, user_id: str, data: Dict[str, Any]):
        """Set user economy data"""
        if 'economy' not in self.data:
            self.data['economy'] = {}
        if guild_id not in self.data['economy']:
            self.data['economy'][guild_id] = {}
        
        self.data['economy'][guild_id][user_id] = data
        self.save()
        logger.debug(f'Updated economy for user {user_id} in guild {guild_id}: {data}')
    
    def get_user_inventory(self, guild_id: str, user_id: str) -> Dict[str, Any]:
        """Get user inventory - RETURNS A COPY"""
        if 'inventory' not in self.data:
            self.data['inventory'] = {}
        if guild_id not in self.data['inventory']:
            self.data['inventory'][guild_id] = {}
        if user_id not in self.data['inventory'][guild_id]:
            self.data['inventory'][guild_id][user_id] = {}
        
        return deepcopy(self.data['inventory'][guild_id][user_id])
    
    def add_to_inventory(self, guild_id: str, user_id: str, item_id: str):
        """Add item to user inventory"""
        if 'inventory' not in self.data:
            self.data['inventory'] = {}
        if guild_id not in self.data['inventory']:
            self.data['inventory'][guild_id] = {}
        if user_id not in self.data['inventory'][guild_id]:
            self.data['inventory'][guild_id][user_id] = {}
        
        if item_id in self.data['inventory'][guild_id][user_id]:
            self.data['inventory'][guild_id][user_id][item_id]['quantity'] += 1
        else:
            self.data['inventory'][guild_id][user_id][item_id] = {
                'purchased': datetime.utcnow().timestamp(),
                'quantity': 1
            }
        self.save()
        logger.info(f'Added item {item_id} to user {user_id} in guild {guild_id}')
    
    def get_shop_items(self, guild_id: str) -> Dict[str, Any]:
        """Get shop items for a guild - RETURNS A COPY"""
        if 'shop_items' not in self.data:
            self.data['shop_items'] = {}
        if guild_id not in self.data['shop_items']:
            self.data['shop_items'][guild_id] = {}
        
        return deepcopy(self.data['shop_items'][guild_id])
    
    def set_shop_items(self, guild_id: str, items: Dict[str, Any]):
        """Set shop items for a guild"""
        if 'shop_items' not in self.data:
            self.data['shop_items'] = {}
        
        self.data['shop_items'][guild_id] = items
        self.save()
    
    def get_warnings(self, guild_id: str, user_id: str) -> list:
        """Get user warnings"""
        if 'warnings' not in self.data:
            self.data['warnings'] = {}
        if guild_id not in self.data['warnings']:
            self.data['warnings'][guild_id] = {}
        if user_id not in self.data['warnings'][guild_id]:
            self.data['warnings'][guild_id][user_id] = []
        
        return deepcopy(self.data['warnings'][guild_id][user_id])
    
    def add_warning(self, guild_id: str, user_id: str, reason: str, moderator_id: str):
        """Add warning to user"""
        if 'warnings' not in self.data:
            self.data['warnings'] = {}
        if guild_id not in self.data['warnings']:
            self.data['warnings'][guild_id] = {}
        if user_id not in self.data['warnings'][guild_id]:
            self.data['warnings'][guild_id][user_id] = []
        
        warning = {
            'reason': reason,
            'moderator_id': moderator_id,
            'timestamp': datetime.utcnow().timestamp()
        }
        self.data['warnings'][guild_id][user_id].append(warning)
        self.save()
    
    def clear_warnings(self, guild_id: str, user_id: str):
        """Clear all warnings for a user"""
        if 'warnings' not in self.data:
            self.data['warnings'] = {}
        if guild_id not in self.data['warnings']:
            self.data['warnings'][guild_id] = {}
        
        self.data['warnings'][guild_id][user_id] = []
        self.save()
    
    def get_last_video_id(self, guild_id: str) -> str:
        """Get last video ID for YouTube notifications"""
        if 'lastVideoId' not in self.data:
            self.data['lastVideoId'] = {}
        
        return self.data['lastVideoId'].get(guild_id)
    
    def set_last_video_id(self, guild_id: str, video_id: str):
        """Set last video ID for YouTube notifications"""
        if 'lastVideoId' not in self.data:
            self.data['lastVideoId'] = {}
        
        self.data['lastVideoId'][guild_id] = video_id
        self.save()
    
    def get_leaderboard_message(self, guild_id: str) -> Dict[str, Any]:
        """Get leaderboard message info"""
        if 'leaderboard_messages' not in self.data:
            self.data['leaderboard_messages'] = {}
        
        return self.data['leaderboard_messages'].get(guild_id, {})
    
    def set_leaderboard_message(self, guild_id: str, channel_id: str, message_id: str):
        """Set leaderboard message info"""
        if 'leaderboard_messages' not in self.data:
            self.data['leaderboard_messages'] = {}
        
        self.data['leaderboard_messages'][guild_id] = {
            'channel_id': channel_id,
            'message_id': message_id
        }
        self.save()


class ReactionRoles:
    """Manages reaction role mappings"""
    def __init__(self):
        self.data = {}
        self.filename = os.path.join(DATA_DIR, 'reaction_roles.json')
        self.lock = threading.Lock()
        os.makedirs(DATA_DIR, exist_ok=True)
        self.load()
    
    def load(self):
        """Load reaction roles from JSON"""
        if os.path.exists(self.filename):
            try:
                with open(self.filename, 'r') as f:
                    self.data = json.load(f)
                logger.info(f'✅ Loaded reaction roles from {self.filename}')
            except Exception as e:
                logger.error(f'❌ Failed to load {self.filename}: {e}')
                self.data = {}
        else:
            logger.info(f'📝 Creating new {self.filename}')
            self.save()
    
    def save(self):
        """Save reaction roles to JSON"""
        with self.lock:
            try:
                temp_file = self.filename + '.tmp'
                with open(temp_file, 'w') as f:
                    json.dump(self.data, f, indent=2)
                os.replace(temp_file, self.filename)
                logger.debug(f'💾 Saved reaction roles to {self.filename}')
            except Exception as e:
                logger.error(f'❌ Failed to save {self.filename}: {e}')
    
    def add_reaction_role(self, guild_id: str, message_id: str, emoji: str, role_id: str):
        """Add a reaction role mapping"""
        if guild_id not in self.data:
            self.data[guild_id] = {}
        if message_id not in self.data[guild_id]:
            self.data[guild_id][message_id] = {}
        
        self.data[guild_id][message_id][emoji] = role_id
        self.save()
    
    def remove_reaction_role(self, guild_id: str, message_id: str, emoji: str = None):
        """Remove a reaction role mapping"""
        if guild_id not in self.data or message_id not in self.data[guild_id]:
            return
        
        if emoji:
            if emoji in self.data[guild_id][message_id]:
                del self.data[guild_id][message_id][emoji]
        else:
            del self.data[guild_id][message_id]
        
        self.save()
    
    def get_role_for_reaction(self, guild_id: str, message_id: str, emoji: str) -> str:
        """Get role ID for a reaction"""
        return self.data.get(guild_id, {}).get(message_id, {}).get(emoji)


class ServerSettings:
    """Manages per-server settings"""
    def __init__(self):
        self.data = {}
        self.filename = os.path.join(DATA_DIR, 'server_settings.json')
        self.lock = threading.Lock()
        os.makedirs(DATA_DIR, exist_ok=True)
        self.load()
    
    def load(self):
        """Load server settings from JSON"""
        if os.path.exists(self.filename):
            try:
                with open(self.filename, 'r') as f:
                    self.data = json.load(f)
                logger.info(f'✅ Loaded server settings from {self.filename}')
            except Exception as e:
                logger.error(f'❌ Failed to load {self.filename}: {e}')
                self.data = {}
        else:
            logger.info(f'📝 Creating new {self.filename}')
            self.save()
    
    def save(self):
        """Save server settings to JSON"""
        with self.lock:
            try:
                temp_file = self.filename + '.tmp'
                with open(temp_file, 'w') as f:
                    json.dump(self.data, f, indent=2)
                os.replace(temp_file, self.filename)
                logger.debug(f'💾 Saved server settings to {self.filename}')
            except Exception as e:
                logger.error(f'❌ Failed to save {self.filename}: {e}')
    
    def get(self, guild_id: str, key: str, default=None):
        """Get a setting for a guild"""
        return self.data.get(guild_id, {}).get(key, default)
    
    def set(self, guild_id: str, key: str, value):
        """Set a setting for a guild"""
        if guild_id not in self.data:
            self.data[guild_id] = {}
        
        self.data[guild_id][key] = value
        self.save()
    
    def get_all(self, guild_id: str) -> Dict[str, Any]:
        """Get all settings for a guild"""
        return deepcopy(self.data.get(guild_id, {}))


# Global instances
bot_data = BotData()
reaction_roles = ReactionRoles()
server_settings = ServerSettings()