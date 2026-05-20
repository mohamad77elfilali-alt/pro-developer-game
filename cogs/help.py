import discord
from discord.ext import commands
from discord.app_commands import command

class HelpCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @command(name="help", description="عرض دليل المساعدة الرسمي للنظام واكتشاف قدرات NetPulse")
    async def help_command(self, interaction: discord.Interaction):
        # رابط المقال والصورة المباشرة
        article_url = "https://hamzadeveloper1.blogspot.com/2026/05/i-can-help-you.html"
        image_url = "https://blogger.googleusercontent.com/img/b/R29vZ2xl/AVvXsEj.../s1600/help_banner.jpg" # استبدلها برابط الصورة الفعلي من مدونتك

        # تصميم الـ Embed بستايل NetPulse (Glassmorphism & Neon)
        embed = discord.Embed(
            title="🌐 NetPulse Aternos System | Help Center",
            description=(
                "أهلاً بك في مركز التحكم. أنت تستخدم أقوى معمارية بوتات لإدارة سيرفرات Aternos.\n\n"
                "**الأوامر المتاحة:**\n"
                "🚀 `/start` - تشغيل السيرفر بأمان.\n"
                "🔴 `/stop` - إطفاء السيرفر.\n"
                "🔄 `/restart` - إعادة تشغيل السيرفر.\n"
                "📊 `/status` - مراقبة حالة السيرفر واللاعبين.\n"
                "⚙️ `/setup` - إعادة تهيئة إعدادات النظام (للمشرفين)."
            ),
            color=discord.Color.from_str("#b026ff") # بنفسجي نيون
        )
        
        embed.set_image(url=image_url)
        embed.set_footer(text="Developed by Mohammed El Filali | NetPulse Project", icon_url=self.bot.user.avatar.url)
        embed.add_url = article_url # إضافة الرابط كمرجع

        # إضافة زر توجيه للمقال
        view = discord.ui.View()
        view.add_item(discord.ui.Button(label="📖 اقرأ المقال الكامل", url=article_url, style=discord.ButtonStyle.link))

        await interaction.response.send_message(embed=embed, view=view)

async def setup(bot):
    await bot.add_cog(HelpCog(bot))
