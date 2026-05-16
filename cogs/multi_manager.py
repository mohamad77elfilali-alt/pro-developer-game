import discord
from discord.ext import commands
import asyncpg
import random
import logging
from typing import Optional, Dict, Set
import asyncio
from datetime import datetime

logger = logging.getLogger("GamingBot")

class LobbySession:
    """بيانات جلسة اللعب الجماعي النشطة"""
    def __init__(self, host_id: int, channel_id: int, guild_id: int, max_players: int = 4, is_private: bool = False):
        self.host_id = host_id
        self.channel_id = channel_id
        self.guild_id = guild_id
        self.max_players = max_players
        self.is_private = is_private
        self.invited_users: Set[int] = set()
        self.active_players: Set[int] = set([host_id])
        self.created_at = datetime.now()
        self.last_activity = datetime.now()
        self.game_in_progress = False

class LobbyDashboardView(discord.ui.View):
    """لوحة التحكم الكاملة بالأزرار لإدارة اللوبي وحل مشاكل الصلاحيات والحد الأقصى للاعبين"""
    def __init__(self, lobby: LobbySession, bot):
        super().__init__(timeout=None)
        self.lobby = lobby
        self.bot = bot

    async def update_db(self):
        try:
            async with self.bot.db_pool.acquire() as conn:
                await conn.execute(
                    "UPDATE active_lobbies SET max_players = $1, is_private = $2 WHERE channel_id = $3",
                    self.lobby.max_players, self.lobby.is_private, self.lobby.channel_id
                )
        except Exception as e:
            logger.error(f"Error updating lobby DB: {e}")

    @discord.ui.button(label="🔓 تحويل عام (مرئي)", style=discord.ButtonStyle.success, custom_id="lobby_toggle_public")
    async def toggle_public(self, interaction: discord.Interaction, button: discord.ui.Button):
        """إصلاح مشكلة جعل القناة مرئية للجميع وتغيير الصلاحيات برمجياً فوراً"""
        if interaction.user.id != self.lobby.host_id:
            await interaction.response.send_message("❌ أنت لست منظم هذه الغرفة لتعديل الخصوصية!", ephemeral=True)
            return

        self.lobby.is_private = False
        await self.update_db()
        
        # تعديل صلاحيات القناة لتصبح مرئية لجميع السيرفر فوراً
        channel = interaction.channel
        overwrite = channel.overwrites_for(interaction.guild.default_role)
        overwrite.view_channel = True
        overwrite.send_messages = True
        await channel.set_permissions(interaction.guild.default_role, overwrite=overwrite, reason="تحديث اللوبي إلى عام")

        await interaction.response.send_message("🔓 تم تحويل القناة بنجاح لتصبح مرئية وعامة لجميع أعضاء السيرفر الآن!", ephemeral=False)

    @discord.ui.button(label="👥 تحديد لاعبين اثنين (2)", style=discord.ButtonStyle.primary, custom_id="lobby_set_2_players")
    async def set_two_players(self, interaction: discord.Interaction, button: discord.ui.Button):
        """إصلاح مشكلة تحديد سعة اللاعبين إلى 2 برمجياً"""
        if interaction.user.id != self.lobby.host_id:
            await interaction.response.send_message("❌ أنت لست منظم هذه الغرفة لتعديل السعة!", ephemeral=True)
            return

        self.lobby.max_players = 2
        await self.update_db()
        await interaction.response.send_message("👥 تم تحديث السعة القصوى للغرفة بنجاح لتستقبل [لاعبين اثنين فقط (2)]!", ephemeral=False)

    @discord.ui.button(label="➕ دعوة صديق (رابط فوري)", style=discord.ButtonStyle.secondary, custom_id="lobby_invite_friend_link")
    async def invite_friend(self, interaction: discord.Interaction, button: discord.ui.Button):
        """تعديل ميزة دعوة صديق لتوليد رابط دعوة فوري مرسل عبر رسالة مخفية بدلاً من كتابة الاسم"""
        if interaction.user.id != self.lobby.host_id:
            await interaction.response.send_message("❌ يمكنك فقط طلب رابط الدعوة إن كنت صاحب اللوبي!", ephemeral=True)
            return

        try:
            # إنشاء رابط دعوة مؤقت وخاص بهذه القناة ينتهي بعد ساعة وصالح لـ 5 استخدامات فقط لتسهيل اللعب
            invite_link = await interaction.channel.create_invite(max_age=3600, max_uses=5, unique=True, reason="رابط سريع لدعوة الأصدقاء للغرفة الجماعية")
            await interaction.response.send_message(f"🔗 **إليك رابط الدعوة الفوري الخاص بقناتك الجماعية:**\n{invite_link}\n قم بنسخه وإرساله لأصدقائك مباشرة ليدخلوا معك!", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ فشل إنشاء رابط الدعوة: {str(e)}", ephemeral=True)

    @discord.ui.button(label="⚔️ انضمام للعب الجماعي", style=discord.ButtonStyle.danger, custom_id="lobby_join_player")
    async def join_lobby(self, interaction: discord.Interaction, button: discord.ui.Button):
        """نظام التحكم برمجياً بحد اللاعبين ومنع تخطي العدد المطلوب"""
        user_id = interaction.user.id
        if user_id in self.lobby.active_players:
            await interaction.response.send_message("⚠️ أنت مشترك بالفعل في هذه القناة الجماعية!", ephemeral=True)
            return

        # التحقق برمجياً من السعة المحددة من قبل المنظم قبل السماح بالدخول
        if len(self.lobby.active_players) >= self.lobby.max_players:
            await interaction.response.send_message(f"❌ الغرفة ممتلئة تماماً! الحد الأقصى المسموح به هو **{self.lobby.max_players}** لاعبين فقط.", ephemeral=True)
            return

        self.lobby.active_players.add(user_id)
        
        # منح العضو المنضم صلاحية رؤية القناة فورياً إذا كانت خاصة
        overwrite = interaction.channel.overwrites_for(interaction.user)
        overwrite.view_channel = True
        overwrite.send_messages = True
        await interaction.channel.set_permissions(interaction.user, overwrite=overwrite)
        
        await interaction.response.send_message(f"🎉 انضم اللاعب {interaction.user.mention} إلى المواجهة! العدد الحالي: ({len(self.lobby.active_players)}/{self.lobby.max_players})", ephemeral=False)

class MultiManager(commands.Cog):
    """إدارة فعاليات اللوبي الجماعي للأعضاء"""
    def __init__(self, bot):
        self.bot = bot
        self.active_lobbies: Dict[int, LobbySession] = {}

    @commands.Cog.listener()
    async def cog_load(self):
        logger.info("✅ MultiManager loaded successfully and tracking persistent events")

async def setup(bot):
    await bot.add_cog(MultiManager(bot))
