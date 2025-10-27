import json
import os
import logging
from datetime import datetime, timezone
from copy import deepcopy
from utils.config import Config

logger = logging.getLogger('tooly_bot.database')

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
        os.makedirs('data', exist_ok=True)
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
                self.data = {}
        else:
            logger.info(f'📝 Creating new {self.filename}')
            self.data = {}
            self.save()
    
    def save(self):
        """Save data to JSON file"""
        try:
            with open(self.filename, 'w') as f:
                json.dump(self.data, f, indent=2)
            logger.debug(f'💾 Saved data to {self.filename}')
        except Exception as e:
            logger.error(f'❌ Failed to save {self.filename}: {e}')
    
    def get_user_economy(self, guild_id: str, user_id: str) -> Dict[str, Any]:
        """Get user economy data - RETURNS A COPY to avoid reference issues"""
        if 'economy' not in self.data:
            self.data['economy'] = {}
        if guild_id not in self.data['economy']:
            self.data['economy'][guild_id] = {}
        
        if user_id not in self.data['economy'][guild_id]:
            # Create new user with default values
            default_data = {
                'coins': 0,
                'bank': 0,
                'lastDaily': 0,
                'lastWork': 0
            }
            self.data['economy'][guild_id][user_id] = default_data
            logger.debug(f'Created new economy entry for user {user_id} in guild {guild_id}')
        
        # Return a COPY to prevent reference issues
        return deepcopy(self.data['economy'][guild_id][user_id])
    
    def set_user_economy(self, guild_id: str, user_id: str, data: Dict[str, Any]):
        """Set user economy data - properly updates without overwriting others"""
        if 'economy' not in self.data:
            self.data['economy'] = {}
        if guild_id not in self.data['economy']:
            self.data['economy'][guild_id] = {}
        
        # Update only this user's data, preserving others
        self.data['economy'][guild_id][user_id] = data
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
        
        from datetime import datetime
        self.data['inventory'][guild_id][user_id][item_id] = {
            'purchased': datetime.utcnow().timestamp(),
            'quantity': self.data['inventory'][guild_id][user_id].get(item_id, {}).get('quantity', 0) + 1
        }
        logger.info(f'Added item {item_id} to user {user_id} in guild {guild_id}')
    
    def get_shop_items(self, guild_id: str) -> Dict[str, Any]:
        """Get shop items for a guild - RETURNS A COPY"""
        if 'shop_items' not in self.data:
            self.data['shop_items'] = {}
        if guild_id not in self.data['shop_items']:
            self.data['shop_items'][guild_id] = {}
        
        return deepcopy(self.data['shop_items'][guild_id])

# Global instance
bot_data = BotData()