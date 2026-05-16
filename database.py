import asyncpg
import os
import logging
import asyncio
from typing import Optional

logger = logging.getLogger("DatabaseEngine")

class DatabaseManager:
    def __init__(self):
        # سحب رابط الاتصال الخاص بـ PostgreSQL من متغيرات Railway البيئية
        self.db_url: Optional[str] = os.getenv("DATABASE_URL")
        self.pool: Optional[asyncpg.Pool] = None
        self._lock = asyncio.Lock() # قفل أمان لمنع التداخل أثناء إعادة الاتصال

    async def initialize(self) -> bool:
        """إنشاء حوض الاتصالات والتأكد من سلامة الجلسة"""
        if not self.db_url:
            logger.critical("🛑 [Database] لم يتم العثور على المتغير البيئي DATABASE_URL!")
            return False

        async with self._lock:
            if self.pool is not None:
                return True # الحوض يعمل بالفعل

            try:
                logger.info("⚡ [Database] جاري إنشاء حوض اتصالات PostgreSQL جديد...")
                # إعداد الحوض بمعايير أداء عالية تناسب العمليات المكثفة للألعاب
                self.pool = await asyncpg.create_pool(
                    self.db_url,
                    min_size=2,       # الحد الأدنى للاتصالات الجاهزة دائماً
                    max_size=10,      # الحد الأقصى لتفادي استهلاك موارد الخطة المجانية
                    max_queries=1000, # إعادة تدوير الاتصال بعد 1000 استعلام لمنع تسريب الذاكرة
                    timeout=30.0      # مهلة زمنية قصوى للاستجابة قبل إلغاء الاستعلام
                )
                
                # اختبار الحوض باستعلام وهمي سريع للتأكد من فاعليته
                async with self.pool.acquire() as conn:
                    await conn.execute("SELECT 1;")
                
                logger.info("✅ [Database] تم الاتصال بقاعدة البيانات بنجاح وإنشاء الحوض المطور!")
                
                # إنشاء الجداول الأساسية تلقائياً إذا لم تكن موجودة
                await self._create_tables()
                return True

            except Exception as e:
                logger.error(f"❌ [Database] فشل ذريع في الاتصال بقاعدة البيانات: {e}")
                self.pool = None
                return False

    async def _create_tables(self):
        """إنشاء جداول النظام الأساسية بنية نظيفة متوافقة مع الـ Cogs"""
        async with self.pool.acquire() as conn:
            # جدول قنوات الألعاب واللوحات الدائمة لضمان عدم ضياع الأزرار بعد الريستارت
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS game_channels (
                    guild_id BIGINT PRIMARY KEY,
                    channel_id BIGINT NOT NULL,
                    message_id BIGINT NOT NULL
                );
            """)
            
            # جدول اقتصاد الألعاب (العملات والنقاط) لحفظ رصيد اللاعبين
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS users_economy (
                    user_id BIGINT PRIMARY KEY,
                    coins BIGINT DEFAULT 1000,
                    xp INT DEFAULT 0,
                    wins INT DEFAULT 0
                );
            """)
            logger.info("📦 [Database] تم التحقق من سلامة الجداول الهيكلية بنجاح.")

    async def ensure_connection(self) -> bool:
        """دالة حماية ذاتية تستدعيها الاستعلامات للتأكد من أن الحوض لم يمت"""
        if self.pool is None:
            logger.warning("⚠️ [Database] الحوض ميت! جاري محاولة إعادة البناء تلقائياً...")
            return await self.initialize()
        return True

    # --- أمثلة للاستعلامات الذكية والمحمية التي سيستخدمها البوت الجديد ---

    async def set_game_channel(self, guild_id: int, channel_id: int, message_id: int) -> bool:
        """حفظ أو تحديث قناة التحكم بالألعاب للأزرار الدائمة"""
        if not await self.ensure_connection():
            return False
        
        try:
            async with self.pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO game_channels (guild_id, channel_id, message_id)
                    VALUES ($1, $2, $3)
                    ON CONFLICT (guild_id) 
                    DO UPDATE SET channel_id = EXCLUDED.channel_id, message_id = EXCLUDED.message_id;
                """, guild_id, channel_id, message_id)
                return True
        except Exception as e:
            logger.error(f"❌ [Database] خطأ أثناء حفظ قناة الألعاب: {e}")
            return False

    async def close(self):
        """إغلاق الحوض بأمان عند انطفاء البوت من الاستضافة"""
        if self.pool:
            logger.info("🔒 [Database] جاري إغلاق حوض اتصالات قاعدة البيانات بأمان...")
            await self.pool.close()
            self.pool = None
