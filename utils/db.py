import asyncpg
import os
from dotenv import load_dotenv

# شحن المتغيرات البيئية من Railway
load_dotenv()

class DatabaseManager:
    """مدير قاعدة البيانات المطور لدعم نظام قنوات الألعاب والأزرار الدائمة"""
    def __init__(self):
        self.pool = None

    async def initialize(self):
        # جلب رابط قاعدة البيانات من المتغيرات البيئية
        database_url = os.getenv("DATABASE_URL")
        if not database_url:
            print("❌ [Database] خطأ: لم يتم العثور على DATABASE_URL في المتغيرات البيئية!")
            return False
        
        try:
            # إنشاء حوض الاتصالات (Connection Pool) للطلبات المتزامنة
            self.pool = await asyncpg.create_pool(database_url)
            print("✅ [Database] تم الاتصال بقاعدة البيانات PostgreSQL بنجاح!")
            
            # تهيئة وإنشاء الجداول الهيكلية للنظام الجديد
            await self.create_tables()
            return True
        except Exception as e:
            print(f"❌ [Database] فشل الاتصال بقاعدة البيانات: {e}")
            return False

    async def create_tables(self):
        """إنشاء جداول الاقتصاد وجداول إعدادات قنوات الألعاب"""
        async with self.pool.acquire() as conn:
            # 1. جدول الاقتصاد والنقاط والانتصارات للاعبين
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS users_economy (
                    user_id BIGINT PRIMARY KEY,
                    coins BIGINT DEFAULT 1000,
                    xp INT DEFAULT 0,
                    wins INT DEFAULT 0,
                    losses INT DEFAULT 0
                );
            ''')
            
            # 2. جدول إعدادات السيرفر (لحفظ قناة الألعاب الرئيسية ورسالة التحكم)
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS guild_settings (
                    guild_id BIGINT PRIMARY KEY,
                    game_channel_id BIGINT,
                    panel_message_id BIGINT
                );
            ''')
            print("✅ [Database] تم التحقق وإنشاء جداول قنوات التحكم والاقتصاد بنجاح.")

    # --- دالات مساعدة خاصة بنظام التحكم الجديد ---

    async def set_game_channel(self, guild_id: int, channel_id: int, message_id: int):
        """حفظ أو تحديث قناة الألعاب الرئيسية ورسالة الأزرار"""
        async with self.pool.acquire() as conn:
            await conn.execute('''
                INSERT INTO guild_settings (guild_id, game_channel_id, panel_message_id)
                VALUES ($1, $2, $3)
                ON CONFLICT (guild_id) 
                DO UPDATE SET game_channel_id = $2, panel_message_id = $3;
            ''', guild_id, channel_id, message_id)

    async def get_game_settings(self, guild_id: int):
        """جلب إعدادات قناة الألعاب الخاصة بالسيرفر"""
        async with self.pool.acquire() as conn:
            return await conn.fetchrow('SELECT game_channel_id, panel_message_id FROM guild_settings WHERE guild_id = $1', guild_id)

    async def close(self):
        """إغلاق حوض الاتصال بأمان عند إطفاء البوت"""
        if self.pool:
            await self.pool.close()
            print("🔒 [Database] تم إغلاق اتصال قاعدة البيانات بأمان.")
