import discord
from discord.ext import commands, tasks
import asyncpg
import os
from dotenv import load_dotenv
import logging
from logging.handlers import RotatingFileHandler
import sys
from datetime import datetime
from pathlib import Path

load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))

if not DISCORD_TOKEN or not DATABASE_URL:
    raise ValueError("Missing DISCORD_TOKEN or DATABASE_URL in environment variables")

class ColoredFormatter(logging.Formatter):
    """Custom formatter with color codes for console output"""
    
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[35m',   # Magenta
    }
    RESET = '\033[0m'
    
    def format(self, record):
        log_color = self.COLORS.get(record.levelname, self.RESET)
        record.levelname = f"{log_color}{record.levelname}{self.RESET}"
        return super().format(record)

def setup_logging():
    """Configure color-coded logging infrastructure"""
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    logger = logging.getLogger("GamingBot")
    logger.setLevel(logging.DEBUG)
    
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_formatter = ColoredFormatter(
        '[%(asctime)s] %(levelname)s | %(name)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(console_formatter)
    
    file_handler = RotatingFileHandler(
        log_dir / "gaming_bot.log",
        maxBytes=10_000_000,
        backupCount=5
    )
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(
        '[%(asctime)s] %(levelname)s | %(name)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(file_formatter)
    
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    
    return logger

logger = setup_logging()

class GamingBot(commands.Bot):
    """Elite Discord Gaming Bot with PostgreSQL persistence"""
    
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        
        super().__init__(
            command_prefix="!",
            intents=intents,
            help_command=None
        )
        
        self.db_pool: asyncpg.Pool = None
        self.active_channels: dict = {}
    
    async def setup_hook(self):
        """Initialize database and load cogs"""
        logger.info("🚀 Initializing GamingBot setup hook...")
        
        await self.initialize_database()
        await self.load_cogs()
        
        self.cleanup_inactive_channels.start()
        logger.info("✅ Setup hook complete - Database initialized, Cogs loaded, Cleanup task started")
    
    async def initialize_database(self):
        """Create PostgreSQL connection pool and initialize schema"""
        try:
            logger.info("🗄️  Connecting to PostgreSQL database...")
            self.db_pool = await asyncpg.create_pool(
                DATABASE_URL,
                min_size=5,
                max_size=20,
                command_timeout=60
            )
            logger.info("✅ PostgreSQL connection pool established (5-20 connections)")
            
            async with self.db_pool.acquire() as conn:
                await conn.execute("""
                    CREATE TABLE IF NOT EXISTS game_channels (
                        id SERIAL PRIMARY KEY,
                        guild_id BIGINT NOT NULL,
                        channel_id BIGINT NOT NULL UNIQUE,
                        host_id BIGINT NOT NULL,
                        lobby_type TEXT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        metadata JSONB DEFAULT '{}'::jsonb
                    );
                """)
                
                await conn.execute("""
                    CREATE TABLE IF NOT EXISTS active_lobbies (
                        id SERIAL PRIMARY KEY,
                        guild_id BIGINT NOT NULL,
                        channel_id BIGINT NOT NULL UNIQUE,
                        host_id BIGINT NOT NULL,
                        max_players INT DEFAULT 4,
                        is_private BOOLEAN DEFAULT FALSE,
                        invited_users BIGINT[] DEFAULT ARRAY[]::BIGINT[],
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                """)
                
                await conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_game_channels_guild ON game_channels(guild_id);
                """)
                
                await conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_active_lobbies_guild ON active_lobbies(guild_id);
                """)
            
            logger.info("✅ Database schema initialized successfully")
        
        except Exception as e:
            logger.error(f"❌ Database initialization failed: {e}", exc_info=True)
            raise
    
    async def load_cogs(self):
        """Dynamically load all cogs from cogs directory"""
        try:
            cogs_dir = Path("cogs")
            cogs_dir.mkdir(exist_ok=True)
            
            cog_files = list(cogs_dir.glob("*.py"))
            
            if not cog_files:
                logger.warning("⚠️  No cog files found in cogs/ directory")
                return
            
            for cog_file in cog_files:
                cog_name = cog_file.stem
                if cog_name.startswith("_"):
                    continue
                
                try:
                    await self.load_extension(f"cogs.{cog_name}")
                    logger.info(f"✅ Loaded cog: {cog_name}")
                except Exception as e:
                    logger.error(f"❌ Failed to load cog {cog_name}: {e}", exc_info=True)
        
        except Exception as e:
            logger.error(f"❌ Cog loading failed: {e}", exc_info=True)
    
    @tasks.loop(minutes=5)
    async def cleanup_inactive_channels(self):
        """Automatically clean up inactive game channels every 5 minutes"""
        try:
            if not self.db_pool:
                return
            
            async with self.db_pool.acquire() as conn:
                inactive_channels = await conn.fetch("""
                    SELECT channel_id, guild_id FROM game_channels 
                    WHERE EXTRACT(EPOCH FROM (NOW() - last_activity)) > 900;
                """)
            
            for record in inactive_channels:
                channel_id = record["channel_id"]
                guild_id = record["guild_id"]
                
                try:
                    channel = self.get_channel(channel_id)
                    if channel:
                        await channel.delete(reason="Inactivity cleanup (15 minutes)")
                        logger.info(f"🗑️  Deleted inactive channel {channel_id} from guild {guild_id}")
                    
                    async with self.db_pool.acquire() as conn:
                        await conn.execute(
                            "DELETE FROM game_channels WHERE channel_id = $1",
                            channel_id
                        )
                
                except discord.NotFound:
                    async with self.db_pool.acquire() as conn:
                        await conn.execute(
                            "DELETE FROM game_channels WHERE channel_id = $1",
                            channel_id
                        )
                    logger.info(f"🗑️  Cleaned up database record for deleted channel {channel_id}")
                
                except Exception as e:
                    logger.error(f"❌ Error cleaning up channel {channel_id}: {e}", exc_info=True)
        
        except Exception as e:
            logger.error(f"❌ Cleanup task failed: {e}", exc_info=True)
    
    @cleanup_inactive_channels.before_loop
    async def before_cleanup(self):
        """Wait for bot to be ready before starting cleanup task"""
        await self.wait_until_ready()
    
    async def on_ready(self):
        """Log successful bot connection"""
        logger.info(f"🎮 Bot connected as {self.user} (ID: {self.user.id})")
        logger.info(f"📊 Connected to {len(self.guilds)} guild(s)")
        logger.info(f"👥 Total members cached: {sum(g.member_count or 0 for g in self.guilds)}")
        
        try:
            synced = await self.tree.sync()
            logger.info(f"✅ Synced {len(synced)} command(s)")
        except Exception as e:
            logger.error(f"❌ Failed to sync commands: {e}", exc_info=True)

bot = GamingBot()

@bot.tree.command(name="setup_gaming_hub", description="Set up the Gaming Hub (Admin Only)")
@discord.app_commands.checks.has_permissions(administrator=True)
async def setup_gaming_hub(interaction: discord.Interaction):
    """Create the Gaming Hub Category with Solo and Multiplayer channels"""
    
    logger.info(f"🎮 /setup_gaming_hub invoked by {interaction.user} in guild {interaction.guild.id}")
    
    try:
        await interaction.response.defer(ephemeral=True)
        
        guild = interaction.guild
        category_name = "🎮 Gaming Hub"
        
        existing_category = discord.utils.get(guild.categories, name=category_name)
        if existing_category:
            logger.info(f"⚠️  Gaming Hub category already exists in guild {guild.id}")
            await interaction.followup.send(
                "✅ Gaming Hub already exists! Category found.",
                ephemeral=True
            )
            return
        
        logger.info(f"📁 Creating Gaming Hub category in guild {guild.id}")
        category = await guild.create_category(category_name)
        
        logger.info(f"📝 Creating solo-arcade channel in guild {guild.id}")
        solo_channel = await guild.create_text_channel(
            "👤-solo-arcade",
            category=category,
            topic="Create your private solo gaming session"
        )
        
        logger.info(f"📝 Creating multiplayer-lobbies channel in guild {guild.id}")
        multi_channel = await guild.create_text_channel(
            "👥-multiplayer-lobbies",
            category=category,
            topic="Host and join multiplayer gaming lobbies"
        )
        
        solo_embed = discord.Embed(
            title="🕹️ SOLO ARCADE ENGINE",
            description="Welcome to your private gaming sanctuary. Click the button below to spin up your exclusive solo session and dive into 50+ mini-games!",
            color=0x9D00FF
        )
        solo_embed.add_field(
            name="🎮 What You Get",
            value="• **50+ Unique Games** - Arcade, Trivia, Simulations, and more\n• **Private Channel** - Your exclusive gaming space\n• **Instant Deletion** - Auto-cleanup when you're done\n• **Pure Gameplay** - No economy, just pure fun",
            inline=False
        )
        solo_embed.add_field(
            name="⚡ How It Works",
            value="1. Click the button below\n2. Get your private channel instantly\n3. Pick any game from the arcade grid\n4. Play as much as you want\n5. Channel auto-deletes after inactivity",
            inline=False
        )
        solo_embed.set_footer(text="🔮 Powered by Elite Gaming Bot | Made with ❤️")
        solo_embed.color = 0x00D9FF
        
        from cogs.solo_manager import SoloCreationView
        await solo_channel.send(embed=solo_embed, view=SoloCreationView())
        logger.info(f"✅ Solo arcade interface deployed to {solo_channel.id}")
        
        multi_embed = discord.Embed(
            title="⚔️ MULTIPLAYER MATCHMAKING HUB",
            description="Gather your squad and host epic multiplayer showdowns! Configure your lobby and challenge other players to unforgettable party games.",
            color=0xFF00FF
        )
        multi_embed.add_field(
            name="🎯 Game Modes",
            value="• **Truth or Dare** - Classic party chaos\n• **Would You Rather** - Hilarious decisions\n• **Word Wars** - Linguistic combat\n• **King of the Hill** - Last player standing\n• **And 6 More Epic Multiplayer Experiences**",
            inline=False
        )
        multi_embed.add_field(
            name="⚙️ Advanced Controls",
            value="• 👥 Set max player limits\n• 🔓 Toggle between Public & Private\n• ➕ Invite specific friends\n• 🎮 Launch your custom lobby",
            inline=False
        )
        multi_embed.set_footer(text="🔮 Powered by Elite Gaming Bot | Made with ❤️")
        multi_embed.color = 0xFF1493
        
        from cogs.multi_manager import MultiCreationView
        await multi_channel.send(embed=multi_embed, view=MultiCreationView())
        logger.info(f"✅ Multiplayer interface deployed to {multi_channel.id}")
        
        await interaction.followup.send(
            f"✅ **Gaming Hub Created Successfully!**\n\n"
            f"📁 Category: {category.mention}\n"
            f"👤 Solo Channel: {solo_channel.mention}\n"
            f"👥 Multi Channel: {multi_channel.mention}\n\n"
            f"🎮 Your gaming infrastructure is ready!",
            ephemeral=True
        )
        
        logger.info(f"✅ Setup complete for guild {guild.id}")
    
    except Exception as e:
        logger.error(f"❌ setup_gaming_hub failed: {e}", exc_info=True)
        await interaction.followup.send(
            f"❌ Failed to set up Gaming Hub: {str(e)}",
            ephemeral=True
        )

@setup_gaming_hub.error
async def setup_gaming_hub_error(interaction: discord.Interaction, error: discord.app_commands.AppCommandError):
    """Error handler for setup_gaming_hub"""
    if isinstance(error, discord.app_commands.MissingPermissions):
        logger.warning(f"❌ {interaction.user} attempted setup_gaming_hub without admin permissions")
        await interaction.response.send_message(
            "❌ You need Administrator permissions to set up the Gaming Hub!",
            ephemeral=True
        )
    else:
        logger.error(f"❌ Unexpected error in setup_gaming_hub: {error}", exc_info=True)
        await interaction.response.send_message(
            "❌ An unexpected error occurred!",
            ephemeral=True
        )

async def main():
    """Start the bot"""
    async with bot:
        try:
            await bot.start(DISCORD_TOKEN)
        except Exception as e:
            logger.critical(f"❌ Failed to start bot: {e}", exc_info=True)
            raise

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
