import logging, asyncio, time, os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# --- [Settings] ---
# GitHub တင်မှာဖြစ်လို့ Token ကို Environment Variable အနေနဲ့ ဖတ်ခိုင်းထားပါတယ်
BOT_TOKEN = os.getenv('BOT_TOKEN', '8732244949:AAEa4sotDF8JTbWrfNl5CeEq676AL_RgM2U')

BANNED_WORDS = ["လိုး", "မအေလိုး", "နှမလိုး", "ဘအေလိုး", "မိအေးလိုး", "အမေလိုး", "လီး", "စောက်", "ဖာသည်", "ခွေးမသား", "ခွေးလိုး", "လီးပဲ", "လီးလား", "စောက်ဖုတ်", "စောက်ထိုး", "စောက်ခွက်", "စောက်ရူး", "စောက်ကောင်", "မအေဘေး", "သေနာ", "ငပိန်း", "fuck", "bitch", "မအလ"]

logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)

# Menu Button သတ်မှတ်ခြင်း
async def set_commands(application):
    commands = [
        ("start", "Bot ကို စတင်နှိုးရန်"),
        ("unban", "User ကို ပြန်လည်ခွင့်ပြုရန် (Admin သုံးရန်)"),
    ]
    await application.bot.set_my_commands(commands)

# လူသစ်ဝင်လာလျှင် Welcome စာနှင့် Admin List ပြခြင်း
async def welcome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.new_chat_members: return
    for member in update.message.new_chat_members:
        if member.id == context.bot.id:
            await update.message.reply_text(f"🛡 **{update.effective_chat.title}** မှာ Admin ပေးလို့ ကျေးဇူးတင်ပါတယ်!")
            return
        
        admins = await context.bot.get_chat_administrators(update.effective_chat.id)
        admin_list = ", ".join([f"@{a.user.username}" for a in admins if a.user.username])
        
        welcome_text = (
            f"🎊 **Group မှ ကြိုဆိုပါတယ် {member.first_name}!** 🎊\n🆔 သင်၏ ID: `{member.id}`\n\n"
            "🛡 **Safe Group MM Pro မှ သင့်ကို စောင့်ရှောက်ပေးပါမည်။**\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "🚫 **စည်းကမ်းချက်များ:**\n• ဆဲဆိုပါက (၇ ရက်) Ban ခံရမည်။\n• Link နှင့် Sticker မပို့ရ။\n"
            "• လာရောက်တောင်းပန်လိုပါက သင်၏ ID ကို အသုံးပြုပါ။\n\n"
            f"📢 **Admins:** {admin_list if admin_list else 'Username မရှိပါ'}"
        )
        await update.message.reply_text(welcome_text, parse_mode="Markdown")

# Unban Function (Admin သုံးရန်)
async def unban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    admins = await context.bot.get_chat_administrators(update.effective_chat.id)
    if user_id not in [a.user.id for a in admins]: return

    target_id = None
    if update.message.reply_to_message:
        target_id = update.message.reply_to_message.from_user.id
    elif context.args:
        target_id = context.args[0]

    if target_id:
        try:
            await context.bot.unban_chat_member(update.effective_chat.id, target_id, only_if_banned=True)
            await update.message.reply_text(f"✅ User `{target_id}` ကို Unban လုပ်ပြီးပါပြီ။")
        except: pass

# Monitor (ဆဲစာ Ban နှင့် Link/Sticker ဖျက်ခြင်း)
async def monitor(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message: return
    chat_id, user = update.effective_chat.id, update.effective_user
    
    if update.message.sticker or (update.message.text and ("http" in update.message.text or "t.me/" in update.message.text)):
        try: await update.message.delete()
        except: pass
        return

    if update.message.text:
        clean_text = update.message.text.lower().replace(" ", "")
        if any(w in clean_text for w in BANNED_WORDS):
            try:
                await update.message.delete()
                until = int(time.time() + (7 * 24 * 60 * 60))
                await context.bot.ban_chat_member(chat_id, user.id, until_date=until)
                await context.bot.send_message(chat_id, f"❌ @{user.username} ကို ဆဲဆိုမှုကြောင့် ၇ ရက် Ban လိုက်ပါပြီ။")
            except: pass

if __name__ == '__main__':
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    
    async def post_init(application):
        await set_commands(application)

    app.post_init = post_init
    app.add_handler(CommandHandler("start", lambda u,c: u.message.reply_text("🛡 Safe Group MM Pro အသက်ဝင်နေပါပြီ!")))
    app.add_handler(CommandHandler("unban", unban))
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome))
    app.add_handler(MessageHandler((filters.TEXT | filters.Sticker.ALL) & (~filters.COMMAND), monitor))
    
    print("Bot is starting...")
    app.run_polling(drop_pending_updates=True)
