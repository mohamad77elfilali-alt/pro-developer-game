import discord
from discord.ext import commands
import os
import asyncio
# استدعاء دالة التهيئة لقاعدة البيانات
        import database
        await database.init_db()

# إعداد النوايا (Intents) بصلاحيات كاملة للتعامل مع القنوات والرتب والأعضاء
intents = discord.Intents.all()

class AternosManagerBot(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix='/', 
            intents=intents,
            help_command=None # قمنا بتعطيل المساعدة الافتراضية لأننا سنصنع واحدة مخصصة واحترافية
        )
        
        # إعداد الألوان الهوية البصرية (Cyberpunk/Neon Aesthetic) لاستخدامها في واجهات البوت
        self.color_blue = discord.Color.from_str("#00f0ff")   # نيون أزرق
        self.color_purple = discord.Color.from_str("#b026ff") # نيون بنفسجي

    async def setup_hook(self):
        # قائمة بالملفات (Cogs) التي سيتم تحميلها لاحقاً
        cogs = [
            'cogs.setup_wizard',
            'cogs.aternos_commands',
            'cogs.help'
        ]
        
        # تحميل الملفات بشكل آمن مع طباعة حالة التحميل
        for cog in cogs:
            try:
                # نستخدم مسار وهمي الآن، سنقوم بإنشاء هذه الملفات في الخطوات القادمة
                await self.load_extension(cog)
                print(f"[*] Module {cog} loaded successfully.")
            except Exception as e:
                print(f"[!] Warning: {cog} is not loaded yet or failed: {e}")
        
        # مزامنة أوامر السلاش
        await self.tree.sync()
        print("[*] Core System Sync Complete.")

    async def on_ready(self):
        print(f"=== SYSTEM ONLINE ===")
        print(f"Logged in professionally as {self.user.name}")
        print(f"Ready to initialize Setup Protocol.")

if __name__ == '__main__':
    TOKEN = os.getenv('DISCORD_TOKEN')
    
    if not TOKEN:
        print("❌ Error: DISCORD_TOKEN is missing!")
    else:
        bot = AternosManagerBot()
        bot.run(TOKEN)
