import discord
from discord.ext import commands
import random
import asyncio

class SoloGames(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def trigger_dice(self, channel: discord.TextChannel, user: discord.User):
        """تشغيل لعبة النرد السريع فوراً بدون رهانات مالية"""
        player_roll = random.randint(1, 6)
        bot_roll = random.randint(1, 6)
        
        if player_roll > bot_roll:
            result = f"🎉 **انتصار رائع يا {user.mention}!**\nرميت النرد وحصلت على الرقم `{player_roll}`، بينما حصل البوت على `{bot_roll}`."
            color = discord.Color.from_rgb(0, 255, 100) # أخضر نيون
        elif player_roll < bot_roll:
            result = f"📉 **حظاً أوفر في المرة القادمة!**\nرميت النرد وحصلت على الرقم `{player_roll}`، بينما غلبك البوت بـ `{bot_roll}`."
            color = discord.Color.from_rgb(255, 50, 50) # أحمر نيون
        else:
            result = f"🤝 **جولة متعادلة!**\nكلاككما رمى النرد واستقر على الرقم `{player_roll}`."
            color = discord.Color.from_rgb(255, 200, 0) # أصفر

        embed = discord.Embed(title="🎲 صراع النرد الترفيهي", description=result, color=color)
        await channel.send(embed=embed)
        
        # تشغيل مؤقت الحذف الذاتي للغرفة فور انتهاء اللعبة
        await self.auto_delete_tracker(channel)

    async def trigger_slots(self, channel: discord.TextChannel, user: discord.User):
        """تشغيل آلة الحظ (Slots) فوراً للاستمتاع بتطابق الرموز"""
        emojis = ["🍒", "💎", "🪙", "🔥", "👑"]
        s1, s2, s3 = random.choice(emojis), random.choice(emojis), random.choice(emojis)
        
        if s1 == s2 == s3:
            result = f"🪐 **تطابق ثلاثي أسطوري!!! (JACKPOT)**\n⚡ النتيجة الحالية: [ {s1} | {s2} | {s3} ]\n\nلقد حققت أعلى نتيجة في اللعبة يا {user.mention}!"
            color = discord.Color.from_rgb(255, 215, 0) # ذهبي
        elif s1 == s2 or s2 == s3 or s1 == s3:
            result = f"✨ **تطابق ثنائي ممتاز!**\n⚡ النتيجة الحالية: [ {s1} | {s2} | {s3} ]\n\nجولة قوية وممتعة!"
            color = discord.Color.from_rgb(0, 255, 150)
        else:
            result = f"❌ **لم تتماثل الرموز هذه المرة!**\n⚡ النتيجة الحالية: [ {s1} | {s2} | {s3} ]\n\nجرّب حظك مرة أخرى في الجولة القادمة."
            color = discord.Color.from_rgb(255, 0, 50)

        embed = discord.Embed(title="🎰 آلة الحظ الأيونية", description=result, color=color)
        await channel.send(embed=embed)
        
        # تشغيل مؤقت الحذف الذاتي للغرفة فور انتهاء اللعبة
        await self.auto_delete_tracker(channel)

    async def auto_delete_tracker(self, channel: discord.TextChannel):
        """نظام تتبع ذكي يقوم بتدمير الغرفة المؤقتة تلقائياً بعد 45 ثانية لتوفير موارد السيرفر"""
        await asyncio.sleep(45)
        try:
            await channel.send("🔒 *انتهت الجولة الترفيهية. جاري تدمير هذه الغرفة المؤقتة ذاتياً بعد 5 ثوانٍ...*")
            await asyncio.sleep(5)
            await channel.delete()
        except Exception:
            pass

async def setup(bot):
    await bot.add_extension(SoloGames(bot))
