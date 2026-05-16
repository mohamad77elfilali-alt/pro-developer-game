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

# تحميل المتغيرات البيئية
load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))

if not DISCORD_TOKEN or not DATABASE_URL:
    raise ValueError("Missing DISCORD_TOKEN or DATABASE_URL in environment variables")

class ColoredFormatter(logging.Formatter):
    """منسق مخصص لتلوين السجلات في شاشة الكونسول بشكل احترافي"""
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
    """إعداد بنية تسجيل الأخطاء والبيانات (Logging) وتصحيح أسماء الدوال"""
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    logger = logging.getLogger("GamingBot")
    logger.setLevel(logging.INFO)
    
    # التسجيل في الكونسول ملون
    console_handler = logging.StreamHandler(sys.stdout)
    console_formatter = ColoredFormatter('%(asctime)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    
    # تصحيح الخطأ هنا: استخدام setFormatter بدلاً من set_formatter
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # الحفظ في ملف مستدار
    file_handler = RotatingFileHandler(log_dir / "bot.log", maxBytes=5*1024*1024, backupCount=3, encoding="utf-8")
    file_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(name)s - %(message)s')
    
    # تصحيح الخطأ هنا أيضاً لحماية بقية الكود
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)
    
    return logger

logger = setup_logging()

class GamingBot(commands.Bot):
    """كلاس البوت الرئيسي المطور لإدارة الألعاب بشكل مستقر وأبدي"""
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.guilds = True
        intents.members = True
        intents.voice_states = True # مهم جداً لتتبع خروج الأعضاء من قنوات السلو واللوبي
        
        super().__init__(
            command_prefix="!",
            intents=intents,
            application_id=None,
            help_command=None
        )
        self.db_pool = None

    async def initialize_database(self):
        """إنشاء الاتصال بقاعدة البيانات وبناء الجداول الأساسية إن لم تكن موجودة"""
        logger.info("📡 جاري الاتصال بقاعدة البيانات واختبار الجداول...")
        try:
            self.db_pool = await asyncpg.create_pool(
                DATABASE_URL,
                min_size=2,
                max_size=10,
                command_timeout=60.0
            )
            
            async with self.db_pool.acquire() as conn:
                # جدول تتبع قنوات السلو النشطة والحذف التلقائي
                await conn.execute('''
                    CREATE TABLE IF NOT EXISTS game_channels (
                        channel_id BIGINT PRIMARY KEY,
                        guild_id BIGINT,
                        host_id BIGINT,
                        lobby_type VARCHAR(20),
                        last_activity TIMESTAMP DEFAULT NOW()
                    );
                ''')
                # جدول تتبع اللوبي الجماعي النشط والخصوصية والعدد
                await conn.execute('''
                    CREATE TABLE IF NOT EXISTS active_lobbies (
                        channel_id BIGINT PRIMARY KEY,
                        guild_id BIGINT,
                        host_id BIGINT,
                        max_players INT DEFAULT 4,
                        is_private BOOLEAN DEFAULT FALSE,
                        last_activity TIMESTAMP DEFAULT NOW()
                    );
                ''')
            logger.info("✅ تم فحص وإعداد جداول قاعدة البيانات بنجاح.")
        except Exception as e:
            logger.critical(f"❌ فشل الاتصال بقاعدة البيانات: {e}", exc_info=True)
            sys.exit(1)

    async def load_cogs(self):
        """تحميل ملفات الـ Cogs بشكل ديناميكي وآمن"""
        cogs_to_load = ['cogs.solo_manager', 'cogs.multi_manager']
        for cog in cogs_to_load:
            try:
                await self.load_extension(cog)
                logger.info(f"📦 تم تحميل الموديل بنجاح: {cog}")
            except Exception as e:
                logger.error(f"❌ فشل تحميل الموديل {cog}: {e}", exc_info=True)

    async def setup_hook(self):
        """إعداد المزامنة وتسجيل الأزرار الثابتة لكي لا تتعطل أبداً عند الريستارت"""
        await self.initialize_database()
        await self.load_cogs()
        
        # استدعاء وتسجيل الـ Views الثابتة المحدثة لحل مشكلة عدم استجابة الأزرار
        from cogs.solo_manager import SoloGamePage1View
        from cogs.multi_manager import LobbyDashboardView, LobbySession
        
        # تسجيل أزرار السلو الدائمة
        self.add_view(SoloGamePage1View(user_id=0, channel_id=0, bot=self))
        
        # تسجيل أزرار اللوبي الجماعي الثابتة بشكل افتراضي لحفظ الـ custom_id
        dummy_lobby = LobbySession(host_id=0, channel_id=0, guild_id=0)
        self.add_view(LobbyDashboardView(dummy_lobby, self))
        
        # بدء مهمة تنظيف قنوات الخمول في الخلفية لتوفير الذاكرة
        self.clean_inactive_channels.start()
        logger.info("⚙️ تم تسجيل الـ Views الثابتة بنجاح وتشغيل مهام التنظيف التلقائي في الخلفية.")

    async def on_ready(self):
        logger.info(f"🟢 تم تشغيل البوت بنجاح باسم: {self.user}")
        logger.info(f"🛡️ معرف المسؤول المحمي: {ADMIN_ID}")
        
        # ضبط حالة البوت بشكل احترافي نيون
        await self.change_presence(
            activity=discord.Activity(type=discord.ActivityType.playing, name="🎮 Arcade Hub | /setup_gaming_hub")
        )

    @tasks.loop(minutes=2)
    async def clean_inactive_channels(self):
        """مهمة دورية لحذف قنوات الألعاب المهجورة تلقائياً بعد خمول طويل لمنع امتلاء السيرفر"""
        logger.info("🧹 جاري فحص وتنظيف قنوات الألعاب الخاملة...")
        try:
            if self.db_pool:
                async with self.db_pool.acquire() as conn:
                    # تدمير قنوات السلو الخاملة لأكثر من 15 دقيقة
                    records = await conn.fetch(
                        "SELECT channel_id FROM game_channels WHERE last_activity < NOW() - INTERVAL '15 minutes'"
                    )
                    for rec in records:
                        channel = self.get_channel(rec['channel_id'])
                        if channel:
                            await channel.delete(reason="تدمير ذاتي: انتهاء صلاحية الجلسة بسبب الخمول")
                        await conn.execute("DELETE FROM game_channels WHERE channel_id = $1", rec['channel_id'])
        except Exception as e:
            logger.error(f"Error in clean_inactive_channels task: {e}")

    async def close(self):
        """إغلاق آمن للاتصالات عند إطفاء البوت"""
        if self.db_pool:
            await self.db_pool.close()
            logger.info("📡 تم إغلاق اتصال قاعدة البيانات بنجاح.")
        await super().close()

bot = GamingBot()

# --- تعريف أزرار لوحة التحكم الرئيسية (Persistent Views) ---

class GamingHubControlView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🕹️ إنشاء غرفة لعب فردي (سولو)", style=discord.ButtonStyle.blurple, custom_id="hub_create_solo")
    async def create_solo(self, interaction: discord.Interaction, button: discord.ui.Button):
        """إنشاء قناة نصية خاصة وخفية فوراً للاعب سولو"""
        await interaction.response.defer(ephemeral=True)
        
        guild = interaction.guild
        user = interaction.user
        
        # صلاحيات القناة: العضو والبوت فقط يرونها
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            user: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True),
            guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True)
        }
        
        try:
            # البحث عن تصنيف الألعاب
            category = discord.utils.get(guild.categories, name="🎮 GAMING HUB")
            channel = await guild.create_text_channel(
                name=f"👤-سولو-{user.name}",
                category=category,
                overwrites=overwrites,
                reason="جلسة لعب سلو جديدة"
            )
            
            # تسجيل القناة في قاعدة البيانات للتتبع
            async with interaction.client.db_pool.acquire() as conn:
                await conn.execute(
                    "INSERT INTO game_channels (channel_id, guild_id, host_id, lobby_type) VALUES ($1, $2, $3, 'solo')",
                    channel.id, guild.id, user.id
                )
            
            # إرسال لوحة ألعاب السولو المحدثة داخل القناة الجديدة
            from cogs.solo_manager import SoloGamePage1View
            embed = discord.Embed(
                title="🕹️ أهلاً بك في صالة الألعاب الفردية النيون",
                description="صالة ألعاب ترفيهية خاصة بك بالكامل! اضغط على أي زر بالأسفل لتشغيل اللعبة فوراً دون انتظار.",
                color=0x00D9FF
            )
            embed.set_footer(text="سيتم تدمير هذه القناة تلقائياً فور خروجك من اللعب أو عند الخمول لميكانيكية أمن السيرفر.")
            
            await channel.send(embed=embed, view=SoloGamePage1View(user.id, channel.id, interaction.client))
            await interaction.followup.send(f"✅ تم فتح صالتك الفردية بنجاح! توجه إلى هنا: {channel.mention}", ephemeral=True)
            
        except Exception as e:
            logger.error(f"Failed to create solo channel: {e}")
            await interaction.followup.send("❌ حدث خطأ أثناء إنشاء صالة الألعاب الفردية الخاصة بك.", ephemeral=True)

    @discord.ui.button(label="⚔️ إنشاء لوبي مواجهة جماعية", style=discord.ButtonStyle.green, custom_id="hub_create_multi")
    async def create_multi(self, interaction: discord.Interaction, button: discord.ui.Button):
        """إنشاء لوبي مواجهة جماعي مخصص والتحكم به"""
        await interaction.response.defer(ephemeral=True)
        
        guild = interaction.guild
        user = interaction.user
        
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            user: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True),
            guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True)
        }
        
        try:
            category = discord.utils.get(guild.categories, name="🎮 GAMING HUB")
            channel = await guild.create_text_channel(
                name=f"👥-لوبي-{user.name}",
                category=category,
                overwrites=overwrites,
                reason="غرفة مواجهة جماعية جديدة"
            )
            
            from cogs.multi_manager import LobbySession, LobbyDashboardView
            lobby = LobbySession(host_id=user.id, channel_id=channel.id, guild_id=guild.id)
            
            # تسجيل اللوبي الجماعي في قاعدة البيانات للتحديثات
            async with interaction.client.db_pool.acquire() as conn:
                await conn.execute(
                    "INSERT INTO active_lobbies (channel_id, guild_id, host_id) VALUES ($1, $2, $3)",
                    channel.id, guild.id, user.id
                )
            
            # حفظ الجلسة في ذاكرة الـ Cog المشغل
            multi_cog = interaction.client.get_cog("MultiManager")
            if multi_cog:
                multi_cog.active_lobbies[channel.id] = lobby

            embed = discord.Embed(
                title="🛡️ لوحة التحكم في اللوبي الجماعي المطور",
                description="بصفتك منظم هذه المواجهة، يمكنك التحكم في الخصوصية وسعة اللاعبين الفردية عن طريق الأزرار المحدثة أدناه:",
                color=0xFF1493
            )
            embed.add_field(name="📊 الإعدادات الافتراضية", value="• **الحالة:** 🔒 خاصة (Invite Only)\n• **الحد الأقصى:** 4 لاعبين", inline=False)
            
            await channel.send(embed=embed, view=LobbyDashboardView(lobby, interaction.client))
            await interaction.followup.send(f"⚔️ تم إنشاء اللوبي الجماعي بنجاح! ادخل هنا لضبطه واللعب: {channel.mention}", ephemeral=True)
            
        except Exception as e:
            logger.error(f"Failed to create multiplayer channel: {e}")
            await interaction.followup.send("❌ حدث خطأ أثناء إطلاق غرفتك الجماعية.", ephemeral=True)

# --- أوامر السلاش (Slash Commands) ---

@bot.tree.command(name="setup_gaming_hub", description="🛠️ ينشئ البنية الأساسية لغرف الألعاب واللوحات التفاعلية الثابتة بالسيرفر")
@commands.has_permissions(administrator=True)
async def setup_gaming_hub(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    guild = interaction.guild
    
    try:
        # 1. إنشاء التصنيف الرئيسي
        category = discord.utils.get(guild.categories, name="🎮 GAMING HUB")
        if not category:
            category = await guild.create_category("🎮 GAMING HUB")
            logger.info("Category '🎮 GAMING HUB' created.")
            
        # 2. إنشاء قناة إطلاق الألعاب الفردية والجماعية المشتركة
        hub_channel = discord.utils.get(category.text_channels, name="🕹️-بوابة-الألعاب")
        if not hub_channel:
            hub_channel = await guild.create_text_channel(
                name="🕹️-بوابة-الألعاب",
                category=category,
                overwrites={guild.default_role: discord.PermissionOverwrite(send_messages=False)} 
            )
            
            embed = discord.Embed(
                title="⚡ منظومة ألعاب النيون التنافسية الترفيهية ⚡",
                description=(
                    "مرحباً بك في أضخم صالة ألعاب على ديسكورد! هنا يمكنك خوض تحديات فردية أو جماعية حماسية.\n\n"
                    "**[ 🕹️ ألعاب السولو الفردية ]**\n"
                    "عند الضغط على الزر، سيقوم البوت بتخصيص صالة مشفرة ومخفية لك تماماً لتلعب بداخلها بأزرار فخمة.\n\n"
                    "**[ ⚔️ ألعاب المواجهة الجماعية ]**\n"
                    "يتيح لك إنشاء لوبي مواجهة خاص، تحديد عدد اللاعبين (مثل لاعبين اثنين فقط)، وتوليد روابط دعوة لأصدقائك."
                ),
                color=0x5865F2
            )
            embed.set_footer(text="Sentinel Gaming System • تم تفعيل الأزرار الأبدية")
            
            await hub_channel.send(embed=embed, view=GamingHubControlView())
            
        await bot.tree.sync(guild=guild)
        await interaction.followup.send("✅ تم إعداد وتثبيت بنية غرف الألعاب ولوحة التحكم التفاعلية بنجاح وبأعلى كفاءة!", ephemeral=True)
        
    except Exception as e:
        logger.error(f"Error in setup_gaming_hub: {e}")
        await interaction.followup.send(f"❌ فشل الإعداد: {str(e)}", ephemeral=True)

async def main():
    async with bot:
        await bot.start(DISCORD_TOKEN)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
