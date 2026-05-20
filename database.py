import aiosqlite
import asyncio

# اسم قاعدة البيانات - مصممة لتكون مستقلة وسهلة النقل
DB_NAME = "netpulse_aternos.db"

async def init_db():
    """
    تهيئة قاعدة البيانات وإنشاء الجداول إذا لم تكن موجودة.
    يتم استدعاء هذه الدالة عند تشغيل البوت لأول مرة.
    """
    async with aiosqlite.connect(DB_NAME) as db:
        # إنشاء جدول إعدادات السيرفر (Guild Settings)
        # قمنا بدمج جميع الخيارات التي طلبتها في أعمدة منظمة
        await db.execute('''
            CREATE TABLE IF NOT EXISTS guild_settings (
                guild_id INTEGER PRIMARY KEY,
                language TEXT DEFAULT 'ar',
                aternos_session TEXT,
                start_role INTEGER,
                restart_role INTEGER,
                stop_role INTEGER,
                start_channel INTEGER,
                power_channel INTEGER, -- قناة الإطفاء وإعادة التشغيل (يمكن أن تكون نفس القناة السابقة)
                server_ip TEXT,
                is_owner BOOLEAN,      -- هل هو المالك (True) أم متعاون (False)
                server_port TEXT,
                server_version TEXT,
                bot_247_name TEXT,
                bot_send_roles TEXT,   -- سيتم حفظ الرتب كـ String مفصول بفواصل
                bot_channel INTEGER    -- غرفة إرسال البوت (مستقلة أو مدمجة)
            )
        ''')
        await db.commit()
        print("[DB] Database Initialized Successfully. All schemas are ready.")

async def get_settings(guild_id: int):
    """
    جلب إعدادات السيرفر باستخدام الـ ID الخاص به.
    ترجع البيانات على شكل قاموس (Dictionary) يسهل التعامل معه برمجياً.
    """
    async with aiosqlite.connect(DB_NAME) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute('SELECT * FROM guild_settings WHERE guild_id = ?', (guild_id,))
        row = await cursor.fetchone()
        return dict(row) if row else None

async def save_settings(guild_id: int, **kwargs):
    """
    حفظ أو تحديث إعدادات السيرفر بشكل ديناميكي.
    يسمح بتحديث حقل واحد أو عدة حقول في نفس الوقت.
    """
    async with aiosqlite.connect(DB_NAME) as db:
        # التحقق مما إذا كان السيرفر مسجلاً مسبقاً في قاعدة البيانات
        cursor = await db.execute('SELECT guild_id FROM guild_settings WHERE guild_id = ?', (guild_id,))
        exists = await cursor.fetchone()

        if not exists:
            # إذا لم يكن موجوداً، نقوم بإنشاء سجل جديد له
            await db.execute('INSERT INTO guild_settings (guild_id) VALUES (?)', (guild_id,))
        
        # تحديث الحقول الديناميكية بناءً على المدخلات (kwargs)
        for key, value in kwargs.items():
            query = f"UPDATE guild_settings SET {key} = ? WHERE guild_id = ?"
            await db.execute(query, (value, guild_id))
            
        await db.commit()

# دالة مساعدة لتجربة قاعدة البيانات عند تشغيل هذا الملف بشكل منفصل
if __name__ == "__main__":
    asyncio.run(init_db())
