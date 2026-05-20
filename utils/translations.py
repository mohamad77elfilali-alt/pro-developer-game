# utils/translations.py

# قاموس الترجمات الشامل للنظام
# مقسم بناءً على المفاتيح (Keys) وكل مفتاح يحتوي على اللغات المدعومة
translations = {
    # ================= [ واجهة الإعداد - Setup Wizard ] =================
    "setup_title": {
        "ar": "⚙️ نظام الإعداد الذكي - NetPulse",
        "en": "⚙️ Smart Setup System - NetPulse",
        "ru": "⚙️ Умная система настройки - NetPulse"
    },
    "lang_select_desc": {
        "ar": "يرجى اختيار لغة واجهة البوت الأساسية.",
        "en": "Please select the primary language for the bot interface.",
        "ru": "Пожалуйста, выберите основной язык интерфейса бота."
    },
    "aternos_session_prompt": {
        "ar": "🔑 يرجى إدخال `ATERNOS_SESSION` الخاص بك للربط:",
        "en": "🔑 Please enter your `ATERNOS_SESSION` to connect:",
        "ru": "🔑 Пожалуйста, введите ваш `ATERNOS_SESSION` для подключения:"
    },
    
    # ================= [ الرتب - Roles ] =================
    "setup_roles_start": {
        "ar": "🟢 اختر الرتب المسموح لها **بتشغيل** السيرفر:",
        "en": "🟢 Select roles allowed to **START** the server:",
        "ru": "🟢 Выберите роли, которым разрешено **ЗАПУСКАТЬ** сервер:"
    },
    "setup_roles_restart": {
        "ar": "🔄 اختر الرتب المسموح لها **بإعادة تشغيل** السيرفر:",
        "en": "🔄 Select roles allowed to **RESTART** the server:",
        "ru": "🔄 Выберите роли, которым разрешено **ПЕРЕЗАПУСКАТЬ** сервер:"
    },
    "setup_roles_stop": {
        "ar": "🔴 اختر الرتب المسموح لها **بإطفاء** السيرفر:",
        "en": "🔴 Select roles allowed to **STOP** the server:",
        "ru": "🔴 Выберите роли, которым разрешено **ОСТАНАВЛИВАТЬ** сервер:"
    },
    "setup_bot_send_roles": {
        "ar": "🤖 اختر الرتب التي تستطيع إرسال البوتات الإضافية:",
        "en": "🤖 Select roles allowed to send additional bots:",
        "ru": "🤖 Выберите роли, которым разрешено отправлять дополнительных ботов:"
    },

    # ================= [ القنوات - Channels ] =================
    "setup_channels_start": {
        "ar": "📺 اختر القناة المخصصة **لتشغيل** السيرفر:",
        "en": "📺 Select the channel for **STARTING** the server:",
        "ru": "📺 Выберите канал для **ЗАПУСКА** сервера:"
    },
    "setup_channels_power": {
        "ar": "⚡ اختر قناة **الإطفاء وإعادة التشغيل** (يمكن أن تكون نفس القناة السابقة):",
        "en": "⚡ Select the channel for **STOP & RESTART** (can be the same as above):",
        "ru": "⚡ Выберите канал для **ОСТАНОВКИ И ПЕРЕЗАПУСКА** (может быть тем же):"
    },
    "setup_bot_channel": {
        "ar": "💬 اختر غرفة إرسال البوت (أو ادمجها مع غرفة المشرف):",
        "en": "💬 Select the bot sending room (or merge with admin room):",
        "ru": "💬 Выберите комнату для отправки бота (или объедините с комнатой администратора):"
    },

    # ================= [ بيانات السيرفر - Server Data ] =================
    "setup_server_ip": {
        "ar": "🌐 أدخل آي بي السيرفر (IP):",
        "en": "🌐 Enter Server IP:",
        "ru": "🌐 Введите IP сервера:"
    },
    "setup_server_port": {
        "ar": "🔌 أدخل البورت (Port):",
        "en": "🔌 Enter Server Port:",
        "ru": "🔌 Введите порт сервера:"
    },
    "setup_server_version": {
        "ar": "📦 أدخل إصدار السيرفر (مثل 1.20.1):",
        "en": "📦 Enter Server Version (e.g. 1.20.1):",
        "ru": "📦 Введите версию сервера (например, 1.20.1):"
    },
    "setup_is_owner": {
        "ar": "👑 هل أنت مالك السيرفر أم متعاون؟ (اختر من القائمة)",
        "en": "👑 Are you the Owner or Collaborator? (Select from list)",
        "ru": "👑 Вы владелец или соавтор? (Выберите из списка)"
    },
    "setup_bot247_name": {
        "ar": "⏰ أدخل اسم بوت الـ 24 ساعة (إن وجد):",
        "en": "⏰ Enter 24/7 Bot name (if any):",
        "ru": "⏰ Введите имя бота 24/7 (если есть):"
    },

    # ================= [ الأزرار والواجهة - Buttons & UI ] =================
    "btn_save": {
        "ar": "💾 حفظ الإعدادات",
        "en": "💾 Save Settings",
        "ru": "💾 Сохранить настройки"
    },
    "btn_restore": {
        "ar": "↩️ استرجاع آخر إعدادات",
        "en": "↩️ Restore Previous Settings",
        "ru": "↩️ Восстановить настройки"
    },
    "btn_finish": {
        "ar": "✅ إنهاء الإعداد",
        "en": "✅ Finish Setup",
        "ru": "✅ Завершить настройку"
    },
    "btn_next": {
        "ar": "التالي ➡️",
        "en": "Next ➡️",
        "ru": "Далее ➡️"
    },
    "btn_back": {
        "ar": "⬅️ السابق",
        "en": "⬅️ Back",
        "ru": "⬅️ Назад"
    },

    # ================= [ رسائل النظام - System Messages ] =================
    "setup_completed": {
        "ar": "🎉 **تم إعداد النظام بنجاح!** جميع الإعدادات محفوظة وجاهزة للعمل بخاصية NetPulse الخارقة.",
        "en": "🎉 **Setup Completed Successfully!** All settings are saved and ready to operate with NetPulse power.",
        "ru": "🎉 **Настройка успешно завершена!** Все настройки сохранены и готовы к работе."
    },
    "permission_denied": {
        "ar": "❌ عذراً، لا تملك الصلاحية لاستخدام هذا الأمر.",
        "en": "❌ Sorry, you do not have permission to use this command.",
        "ru": "❌ Извините, у вас нет прав на использование этой команды."
    }
}

def get_text(key: str, lang: str = 'ar') -> str:
    """
    دالة لجلب النص المترجم بناءً على المفتاح واللغة المطلوبة.
    في حال لم يتم العثور على اللغة، تعود للغة العربية كافتراضي.
    """
    if key not in translations:
        return f"[{key}]" # يظهر هكذا لتنبيه المطور بنقص الترجمة
    
    # التحقق من وجود اللغة، وإلا يتم استخدام العربية
    available_langs = translations[key]
    return available_langs.get(lang, available_langs.get('ar', f"[{key}]"))
