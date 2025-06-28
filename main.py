import json
import requests
from telegram import Update, ReplyKeyboardRemove
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    ContextTypes, filters, ConversationHandler
)

# التوكن الخاص بالبوت
TOKEN = '7766419265:AAH0kqMNNSftg0WHUHxfR-dm4nCMZvptokQ'

# معرفات الإداريين
ADMIN_IDS = [2114059145, 825988821]

# عدد المستخدمين (بدون حفظ دائم)
user_count = 0

# حالات المحادثة
NUMBER, PASSWORD = range(2)

# دالة الترحيب وإرسال التوقيع مع ID و يوزر المستخدم
async def send_welcome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global user_count
    user_count += 1

    user = update.effective_user
    username = user.username or "مستخدم غير مسجل"
    user_id = user.id

    # إرسال إشعار للإداريين
    for admin_id in ADMIN_IDS:
        try:
            await context.bot.send_message(
                chat_id=admin_id,
                text=f"👤 مستخدم جديد دخل البوت:\nID: `{user_id}`\nUsername: @{username}",
                parse_mode="Markdown"
            )
        except:
            pass

    welcome_text = (
        "⌯ تم تفعيل الخدمة بواسطة:✪ 『 تيم @Mabowaged 』\n"
        "══════════════✪\n"
        "مؤسس البوت: @CR7_705\n"
        "══════════════🔰\n"
        "لمزيد من الثغرات والشروحات الحصرية:\n"
        "📢 https://t.me/mabowaged_eg\n"
        "══════════════❗\n"
        "لا تستخدم البوت فيما يغضب الله ❤️\n\n"
        f"مرحبًا بك يا {username}!\n"
        f"🆔 ID: {user_id}\n"
        f"📲 Username: @{username}"
    )

    await update.message.reply_text(welcome_text)
    await update.message.reply_text("📱 من فضلك أرسل رقم فودافون الخاص بك:")
    return NUMBER

# الحصول على الرقم
async def get_number(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['number'] = update.message.text.strip()
    await update.message.reply_text("🔐 أرسل كلمة السر:")
    return PASSWORD

# الحصول على كلمة السر وتنفيذ العملية
async def get_password(update: Update, context: ContextTypes.DEFAULT_TYPE):
    number = context.user_data.get('number')
    password = update.message.text.strip()

    await update.message.reply_text("⏳ جارٍ تسجيل الدخول...")

    login_url = "https://mobile.vodafone.com.eg/auth/realms/vf-realm/protocol/openid-connect/token"
    login_payload = {
        'username': number,
        'password': password,
        'grant_type': "password",
        'client_secret': "95fd95fb-7489-4958-8ae6-d31a525cd20a",
        'client_id': "ana-vodafone-app"
    }
    login_headers = {
        'User-Agent': "okhttp/4.11.0",
        'Accept': "application/json",
    }

    try:
        res = requests.post(login_url, data=login_payload, headers=login_headers)
        token = res.json().get('access_token')
    except:
        token = None

    if not token:
        await update.message.reply_text("❌ الرقم أو كلمة المرور غير صحيحة.")
        return ConversationHandler.END

    # العملية الخاصة بالهدية
    url = f"https://web.vodafone.com.eg/services/dxl/promo/promotion?@type=Promo&$.context.type=5G_Promo&$.characteristics%5B@name%3DcustomerNumber%5D.value={number}"
    headers = {
        'Authorization': f"Bearer {token}",
        'msisdn': number,
        'clientId': "WebsiteConsumer",
        'channel': "APP_PORTAL",
        'Content-Type': "application/json",
        'X-Requested-With': "com.emeint.android.myservices",
    }

    try:
        data = requests.get(url, headers=headers).json()
        current_level = "1"
        scores = []

        for item in data:
            for characteristic in item.get("characteristics", []):
                if characteristic.get("name") == "currentLevel":
                    current_level = characteristic.get("value")
                if characteristic.get("name") == "scores":
                    scores = list(map(int, characteristic.get("value").split(",")))

        level = current_level
        score = max(scores) if scores else 50

        # إرسال الطلب
        send_url = "https://web.vodafone.com.eg/services/dxl/promo/promotion"
        payload = {
            "@type": "Promo",
            "channel": {"id": "APP_PORTAL"},
            "context": {"type": "5G_Promo"},
            "pattern": [
                {
                    "characteristics": [
                        {"name": "level", "value": level},
                        {"name": "score", "value": str(score)},
                        {"name": "customerNumber", "value": number}
                    ]
                }
            ]
        }

        res = requests.post(send_url, data=json.dumps(payload), headers=headers)
        promo_id = res.json().get("id")
        mg = res.json()["characteristics"][0]["value"]

        confirm_url = f"https://web.vodafone.com.eg/services/dxl/promo/promotion/{promo_id}"
        confirm_payload = {
            "@type": "Promo",
            "channel": {"id": "APP_PORTAL"},
            "context": {"type": "5G_Promo"},
            "pattern": [
                {
                    "characteristics": [
                        {"name": "customerNumber", "value": number}
                    ]
                }
            ]
        }

        final_res = requests.patch(confirm_url, data=json.dumps(confirm_payload), headers=headers)
        if final_res.status_code == 204:
            await update.message.reply_text(f"✅ تم إضافة {mg} ميجا بنجاح 🔥")
        else:
            await update.message.reply_text("⚠️ حدث خطأ أثناء تفعيل الهدية.")
    except:
        await update.message.reply_text("❗ يبدو أنك أخذت الهدية بالفعل اليوم.")
    return ConversationHandler.END

# دالة إلغاء
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ تم إلغاء العملية.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

# أمر معرفة عدد المستخدمين
async def users_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id in ADMIN_IDS:
        await update.message.reply_text(f"📊 عدد من استخدم البوت: {user_count}")

# تشغيل البوت
if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", send_welcome)],
        states={
            NUMBER: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_number)],
            PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_password)],
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )

    app.add_handler(conv_handler)
    app.add_handler(CommandHandler("users", users_command))

    print("✅ Bot is running...")
    app.run_polling()