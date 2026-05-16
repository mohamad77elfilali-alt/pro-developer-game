import asyncpg
import os
from dotenv import load_dotenv

# شحن المتغيرات البيئية
load_dotenv()

class DatabaseManager:
    """مدير قاعدة البيانات الذكي لبوت الألعاب والإدارة"""
    def __init__(self):
        self.pool = None

    async def initialize(self):
        # جلب رابط قاعدة البيانات من Railway
        database_url = os.getenv("DATABASE_URL")
        if not database_url:
            print("❌ [Database] خطأ: لم يتم العثور على DATABASE_URL في المتغيرات البيئية!")
            return False
        
        try:
            # إنشاء حوض الاتصالات (Connection Pool) لقاعدة البيانات
            self.pool = await asyncpg.create_pool(database_url)
            print("✅ [Database] تم الاتصال بقاعدة البيانات PostgreSQL بنجاح!")
            
            # إنشاء الجداول الأساسية للألعاب إن لم تكن موجودة
            await self.create_tables()
            return True
        except Exception as e:
            print(f"❌ [Database] فشل الاتصال بقاعدة البيانات: {e}")
            return False

    async def create_tables(self):
        """إنشاء جداول الاقتصاد ونقاط الألعاب"""
        async with self.pool.acquire() as conn:
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS users_economy (
                    user_id BIGINT PRIMARY KEY,
                    coins BIGINT DEFAULT 1000,
                    xp INT DEFAULT 0,
                    wins INT DEFAULT 0
                );
            ''')
            print("✅ [Database] تم التحقق من سلامة الجداول الهيكلية للألعاب.")

    async def close(self):
        """إغلاق الاتصال بأمان عند إطفاء السيرفر"""
        if self.pool:
            await self.pool.close()
            print("🔒 [Database] تم إغلاق اتصال قاعدة البيانات بأمان.")
