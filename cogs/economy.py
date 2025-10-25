import discord
from discord.ext import commands
from discord import option
from datetime import datetime
from typing import Optional
import random
import logging

from utils.database import bot_data
from utils.config import Config

logger = logging.getLogger('tooly_bot.economy')


class Economy(commands.Cog):
    """Economy system with daily rewards, work, and shop."""

    def __init__(self, bot):
        self.bot = bot

    # ==================================================
    # 🏪 SHOP MANAGEMENT COMMANDS (ADMIN)
    # ==================================================

    @discord.slash_command(name='createitem', description='[ADMIN] Create a new shop item')
    @option("item_id", description="Unique ID for the item")
    @option("name", description="Display name")
    @option("price", description="Price in coins", min_value=1)
    @option("description", description="Item description")
    @option("emoji", description="Emoji for the item")
    @option("item_type", description="Type of item", choices=["role", "badge", "consumable"])
    @option("role_id", description="Role ID (only for role type items)", required=False)
    @discord.default_permissions(administrator=True)
    async def createitem(
        self,
        ctx,
        item_id: str,
        name: str,
        price: int,
        description: str,
        emoji: str,
        item_type: str,
        role_id: str = None
    ):
        if item_type == 'role' and not role_id:
            await ctx.respond('❌ Role items require a role_id!', ephemeral=True)
            return

        shop_items = bot_data.get_shop_items()
        if item_id in shop_items:
            await ctx.respond(f'❌ Item with ID `{item_id}` already exists!', ephemeral=True)
            return

        shop_items[item_id] = {
            'name': name[:100],
            'description': description[:200],
            'price': price,
            'emoji': emoji[:10],
            'type': item_type,
            'role_id': role_id,
            'created': datetime.utcnow().timestamp(),
            'creator': str(ctx.author.id)
        }

        bot_data.data['shop_items'] = shop_items
        bot_data.save()

        embed = discord.Embed(
            title='✅ Item Created Successfully',
            color=0x00FF00,
            timestamp=datetime.utcnow()
        )
        embed.add_field(name='ID', value=f'`{item_id}`', inline=True)
        embed.add_field(name='Name', value=name, inline=True)
        embed.add_field(name='Price', value=f'{price:,} coins', inline=True)
        embed.add_field(name='Type', value=item_type, inline=True)
        embed.add_field(name='Emoji', value=emoji, inline=True)
        if role_id:
            embed.add_field(name='Role ID', value=role_id, inline=True)
        embed.add_field(name='Description', value=description, inline=False)

        await ctx.respond(embed=embed, ephemeral=True)

    @discord.slash_command(name='deleteitem', description='[ADMIN] Delete a shop item')
    @option("item_id", description="ID of item to delete")
    @discord.default_permissions(administrator=True)
    async def deleteitem(self, ctx, item_id: str):
        shop_items = bot_data.get_shop_items()

        if item_id not in shop_items:
            await ctx.respond(f'❌ Item `{item_id}` not found!', ephemeral=True)
            return

        item = shop_items[item_id]
        del shop_items[item_id]
        bot_data.data['shop_items'] = shop_items
        bot_data.save()

        await ctx.respond(f'✅ Deleted item: **{item["name"]}** (`{item_id}`)', ephemeral=True)

    @discord.slash_command(name='listitems', description='[ADMIN] List all shop items with IDs')
    @discord.default_permissions(administrator=True)
    async def listitems(self, ctx):
        shop_items = bot_data.get_shop_items()

        if not shop_items:
            await ctx.respond('📦 No items in shop yet. Use `/createitem` to add some!', ephemeral=True)
            return

        embed = discord.Embed(
            title='📋 All Shop Items (Admin View)',
            color=0x9B59B6,
            timestamp=datetime.utcnow()
        )

        for item_id, item in shop_items.items():
            field_value = f"**Price:** {item['price']:,} coins\n**Type:** {item['type']}\n**Description:** {item['description']}"
            if item.get('role_id'):
                field_value += f"\n**Role ID:** {item['role_id']}"

            embed.add_field(
                name=f"{item['emoji']} {item['name']} (`{item_id}`)",
                value=field_value,
                inline=False
            )

        await ctx.respond(embed=embed, ephemeral=True)

    # ==================================================
    # 🪙 ECONOMY COMMANDS
    # ==================================================

    @discord.slash_command(name='balance', description='Check your balance')
    @option("user", discord.Member, description="User to check (optional)", required=False)
    async def balance(self, ctx, user: Optional[discord.Member] = None):
        target = user or ctx.author
        user_id = str(target.id)
        economy_data = bot_data.get_user_economy(user_id)

        embed = discord.Embed(
            title=f'💰 {target.display_name}\'s Balance',
            color=0xFFD700,
            timestamp=datetime.utcnow()
        )
        embed.set_thumbnail(url=target.display_avatar.url)
        embed.add_field(name='💵 Wallet', value=f'{economy_data["coins"]:,} coins', inline=True)
        embed.add_field(name='🏦 Bank', value=f'{economy_data["bank"]:,} coins', inline=True)
        embed.add_field(
            name='💎 Total',
            value=f'{economy_data["coins"] + economy_data["bank"]:,} coins',
            inline=True
        )

        await ctx.respond(embed=embed)

    # ... (keep daily, work, shop, inventory, give as-is)

    @discord.slash_command(name='buy', description='Purchase an item from the shop')
    @option("item_id", str, description="Item ID to purchase (see /shop)")
    async def buy(self, ctx, item_id: str):
        shop_items = bot_data.get_shop_items()

        if item_id not in shop_items:
            await ctx.respond('❌ Invalid item ID! Use `/shop` to see available items.', ephemeral=True)
            return

        item = shop_items[item_id]
        user_id = str(ctx.author.id)

        inventory = bot_data.get_user_inventory(user_id)
        if item_id in inventory and item['type'] != 'consumable':
            await ctx.respond(f'❌ You already own **{item["name"]}**!', ephemeral=True)
            return

        economy_data = bot_data.get_user_economy(user_id)
        if economy_data['coins'] < item['price']:
            needed = item['price'] - economy_data['coins']
            await ctx.respond(
                f'❌ You need **{needed:,}** more coins to buy **{item["name"]}**!',
                ephemeral=True
            )
            return

        economy_data['coins'] -= item['price']
        bot_data.set_user_economy(user_id, economy_data)
        bot_data.add_to_inventory(user_id, item_id)
        bot_data.save()

        # 🧩 FIX: Check and handle missing permissions safely
        if item['type'] == 'role' and item.get('role_id'):
            role = ctx.guild.get_role(int(item['role_id']))
            if role:
                if ctx.guild.me.top_role.position > role.position:
                    try:
                        await ctx.author.add_roles(role, reason="Purchased from shop")
                    except discord.Forbidden:
                        logger.warning(f"❌ Missing permission to add role {role.name}")
                        await ctx.respond(
                            f'⚠️ I don’t have permission to add the role **{role.name}**. Please check my role position!',
                            ephemeral=True
                        )
                else:
                    await ctx.respond(
                        f'⚠️ My highest role is below **{role.name}**, so I can’t assign it!',
                        ephemeral=True
                    )

        embed = discord.Embed(
            title='✅ Purchase Successful!',
            description=f'You purchased **{item["name"]}**!',
            color=0x00FF00,
            timestamp=datetime.utcnow()
        )
        embed.add_field(name='Item', value=f"{item['emoji']} {item['name']}", inline=True)
        embed.add_field(name='Price', value=f'{item["price"]:,} coins', inline=True)
        embed.add_field(name='Remaining Balance', value=f'{economy_data["coins"]:,} coins', inline=True)

        if item['type'] == 'role':
            embed.add_field(name='Role Added', value='✅ (If I have permission)', inline=False)

        await ctx.respond(embed=embed)


def setup(bot):
    bot.add_cog(Economy(bot))
