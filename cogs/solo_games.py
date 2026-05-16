import discord
from discord.ext import commands
import random

class SoloGames(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def trigger_dice(self, channel: discord.TextChannel, user: discord.User):
        """يتم استدعاؤها فوراً عند اختيار لعبة النرد من لوحة التحكم"""
        player_roll = random.randint(1, 6)
        bot_roll = random.randint(1, 6)
        
        if player_roll > bot_roll:
            result = f"🎉 لقد فزت يا {user.mention}! رميت `{player_roll}` والفرعون رمى `{bot_roll}`."
            color = discord.Color.green()
        elif player_roll < bot_roll:
            result = f"📉 خسرت! رميت `{player_roll}` والفرعون رمى `{bot_roll}`."
            color = discord.Color.red()
        else:
            result = f"🤝 تعادل! كلاككما رمى `{player_roll}`."
            color = discord.Color.gold()

        embed = discord.Embed(title="🎲 جولة النرد السريع", description=result, color=color)
        await channel.send(embed=embed)

    async def trigger_slots(self, channel: discord.TextChannel, user: discord.User):
        """يتم استدعاؤها فوراً عند اختيار لعبة آلة الحظ من لوحة التحكم"""
        emojis = ["🎰", "🍒", "💎", "🪙", "🔥"]
        slot1, slot2, slot3 = random.choice(emojis), random.choice(emojis), random.choice(emojis)

        if slot1 == slot2 == slot3:
            result = f"👑 {user.mention} **الربح الأكبر!!** ثلاثي متطابق: [ {slot1} | {slot2} | {slot3} ]"
            color = discord.Color.gold()
        elif slot1 == slot2 or slot2 == slot3 or slot1 == slot3:
            result = f"✨ **ربح متوسط!** تطابق ثنائي: [ {slot1} | {slot2} | {slot3} ]"
            color = discord.Color.green()
        else:
            result = f"❌ **حظاً أوفر!** لم تتماثل الرموز: [ {slot1} | {slot2} | {slot3} ]"
            color = discord.Color.red()

        embed = discord.Embed(title="🎰 آلة الحظ (Slots)", description=result, color=color)
        await channel.send(embed=embed)

async def setup(bot):
    await bot.add_extension(SoloGames(bot))
