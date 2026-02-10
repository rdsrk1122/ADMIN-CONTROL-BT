import logging
import json
import os
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler

# --- কনফিগারেশন ---
TOKEN = '7962381986:AAHSw32MC4IQPbHDaW-C550lZenz9fnCWHg'
ADMIN_ID = 7767589524  # আপনার আইডি দিন

# ডাটা ফাইল (রেলওয়েতে সাময়িকভাবে ডাটা রাখবে)
DATA_FILE = 'bot_data.json'

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    return {"password": "Rdsvai11", "welcome_msg": "হ্যালো! আপনি যা লিখবেন তা অ্যাডমিনের কাছে পৌঁছে যাবে।", "users": {}, "blocked": []}

def save_data(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f)

db = load_data()

# স্টেটসমূহ
WAITING_FOR_PASS, ADMIN_HOME, BCAST, SEND_MSG_ID, SEND_MSG_TXT, BLOCK_ID, UNBAN_ID, SETTINGS_MENU, CHANGE_PASS, CHANGE_WELCOME = range(10)

# --- কিবোর্ডস ---
def admin_keyboard():
    return ReplyKeyboardMarkup([
        ['👥 USER LIST', '💬 SENT MSG'],
        ['📢 BROADCAST', '🚫 BLOCK'],
        ['✅ UNBAN', '📑 BLOCK LIST'],
        ['⚙️ SETTINGS']
    ], resize_keyboard=True)

def settings_keyboard():
    return ReplyKeyboardMarkup([
        ['🔑 Change Password', '👋 Change Welcome Message'],
        ['⬅️ Back to Panel']
    ], resize_keyboard=True)

# --- হ্যান্ডলারস ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    uid = str(user.id)
    
    if uid in db['blocked']:
        return

    # ইউজার সেভ করা
    db['users'][uid] = {"name": user.full_name, "username": f"@{user.username}"}
    save_data(db)

    if user.id == ADMIN_ID:
        await update.message.reply_text(f"স্বাগতম বস! প্যানেলে ঢুকতে /admin লিখুন।")
    else:
        await update.message.reply_text(db['welcome_msg'])

async def handle_user_msg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if str(user.id) in db['blocked'] or user.id == ADMIN_ID:
        return
    
    text = f"📩 *নতুন মেসেজ!*\n👤 নাম: {user.full_name}\n🆔 আইডি: `{user.id}`\n\nবার্তা: {update.message.text}"
    await context.bot.send_message(chat_id=ADMIN_ID, text=text, parse_mode='Markdown')

# --- অ্যাডমিন কনভারসেশন ---
async def admin_entry(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    await update.message.reply_text("🔐 পাসওয়ার্ড দিন:", reply_markup=ReplyKeyboardRemove())
    return WAITING_FOR_PASS

async def check_pass(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == db['password']:
        await update.message.reply_text("✅ অ্যাডমিন প্যানেলে স্বাগতম!", reply_markup=admin_keyboard())
        return ADMIN_HOME
    else:
        await update.message.reply_text("❌ ভুল পাসওয়ার্ড! আবার চেষ্টা করুন /admin")
        return ConversationHandler.END

async def admin_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    if text == "👥 USER LIST":
        msg = "📊 *ইউজার লিস্ট:*\n\n"
        for uid, info in db['users'].items():
            msg += f"🔹 {info['name']} - `{uid}`\n"
        await update.message.reply_text(msg or "কোনো ইউজার নেই।", parse_mode='Markdown')

    elif text == "📢 BROADCAST":
        await update.message.reply_text("সবাইকে পাঠানোর জন্য মেসেজটি লিখুন:")
        return BCAST

    elif text == "⚙️ SETTINGS":
        await update.message.reply_text("⚙️ সেটিংস মেনু:", reply_markup=settings_keyboard())
        return SETTINGS_MENU
    
    # এখানে Block/Sent Msg এর লজিক একইভাবে যোগ করা যাবে...

async def settings_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text == '🔑 Change Password':
        await update.message.reply_text("নতুন পাসওয়ার্ডটি লিখুন:")
        return CHANGE_PASS
    elif text == '👋 Change Welcome Message':
        await update.message.reply_text("নতুন Welcome Message টি লিখুন:")
        return CHANGE_WELCOME
    elif text == '⬅️ Back to Panel':
        await update.message.reply_text("মেনু:", reply_markup=admin_keyboard())
        return ADMIN_HOME

async def update_welcome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db['welcome_msg'] = update.message.text
    save_data(db)
    await update.message.reply_text("✅ Welcome Message আপডেট হয়েছে!", reply_markup=settings_keyboard())
    return SETTINGS_MENU

# --- মেইন ফাংশন ---
def main():
    app = Application.builder().token(TOKEN).build()
    
    admin_conv = ConversationHandler(
        entry_points=[CommandHandler('admin', admin_entry)],
        states={
            WAITING_FOR_PASS: [MessageHandler(filters.TEXT & ~filters.COMMAND, check_pass)],
            ADMIN_HOME: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_main_menu)],
            SETTINGS_MENU: [MessageHandler(filters.TEXT & ~filters.COMMAND, settings_handler)],
            CHANGE_WELCOME: [MessageHandler(filters.TEXT & ~filters.COMMAND, update_welcome)],
            BCAST: [MessageHandler(filters.TEXT & ~filters.COMMAND, lambda u, c: start(u, c))] # Placeholder
        },
        fallbacks=[CommandHandler('start', start)]
    )

    app.add_handler(admin_conv)
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_user_msg))
    
    app.run_polling()

if __name__ == '__main__':
    main()
