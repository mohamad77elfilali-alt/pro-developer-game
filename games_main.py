import discord
from discord.ext import commands
import os
import asyncio
from dotenv import load_dotenv
from utils.db import DatabaseManager # مدير قاعدة البيانات الذكي والمستقر

# شحن متغيرات البيئة من Railway
load_dotenv()

class UltraGamesBot(commands.Bot):
    def __init__(self):
        # تفعيل كافة الصلاحيات للبوت (Intents.all) كما في كودك الأصلي
        intents = discord.Intents.all()
        super().__init__(command_prefix="g!", intents=intents)
        self.db = DatabaseManager()

    async def setup_hook(self):
        # 1. الاتصال بقاعدة البيانات المشتركة لجلب أرصدة اللاعبين
        print("⚡ [System] جاري الاتصال بقاعدة البيانات...")
        await self.db.initialize()

        # 2. تحميل ملفات الألعاب ديناميكياً وبشكل آمن متوافق مع البيئة السحابية
        # قمنا بتحديد الأقسام الثلاثة المتواجدة لديك لضمان شحنها بدون مشاكل مسارات
        cogs_to_load = [
            "games_cogs.board_games",
            "games_cogs.casino",
            "games_cogs.party_games"
        ]

        print("🎮 [System] بدء شحن ملفات الألعاب التنافسية...")
        for cog in cogs_to_load:
            try:
                await self.load_extension(cog)
                print(f"✅ تم تحميل لعبة: {cog.split('.')[-1]}")
            except Exception as e:
                print(f"❌ فشل تحميل ملف الألعاب {cog}: {e}")
        
        # 3. مزامنة أوامر السلاش الخاصة بالألعاب عالمياً
        print("🔄 [System] جاري مزامنة أوامر ألعاب السلاش مع ديسكورد...")
        try:
            synced = await self.tree.sync()
            print(f"✨ تم مزامنة {len(synced)} من أوامر السلاش بنجاح.")
        except Exception as e:
            print(f"❌ فشل مزامنة أوامر السلاش: {e}")

    async def on_ready(self):
        print("=" * 50)
        print(f'🕹️ {self.user.name} (بوت الألعاب) جاهز ومستعد للتحدي!')
        print("=" * 50)
        await self.change_presence(
            activity=discord.Activity(type=discord.ActivityType.playing, name="with Server Economy!")
        )

# تعيين التوكن بشكل ذكي: يقرأ أولاً من GAMES_BOT_TOKEN أو BOT_TOKEN من إعدادات Railway
TOKEN = os.getenv("GAMES_BOT_TOKEN") or os.getenv("BOT_TOKEN")

if __name__ == "__main__":
    if not TOKEN:
        print("🛑 [Fatal Error] لم يتم العثور على التوكن! تأكد من إضافة متغير GAMES_BOT_TOKEN في لوحة تحكم Railway Variables.")
    else:
        bot = UltraGamesBot()
        try:
            asyncio.run(bot.start(TOKEN))
        except KeyboardInterrupt:
            print("🔒 [System] تم إيقاف البوت بأمان.")
