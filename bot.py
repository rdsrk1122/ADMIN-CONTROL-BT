import logging
import json
import os
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler

# --- কনফিগারেশন ---
TOKEN = '7962381986:AAHSw32MC4IQPbHDaW-C550lZenz9fnCWHg' # এখানে আপনার বট টোকেন দিন
ADMIN_ID = 7159407533 # এখানে আপনার আইডি দিন (integer)
DATA_FILE = 'bot_data.json'

# ডাটা লোড ও সেভ করার ফাংশন
def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r') as f: return json.load(f)
        except: pass
    return {
        "password": "Rdsvai11", 
        "welcome_msg": "হ্যালো! আপনি যা লিখবেন তা অ্যাডমিনের কাছে পৌঁছে যাবে।", 
        "users": {}, 
        "blocked": []
    }

def save_data(data):
    with open(DATA_FILE, 'w') as f: json.dump(data, f)

db = load_data()

# কনভারসেশন স্টেটসমূহ
PASS, HOME, BCAST, S_ID, S_TXT, BLK, UNB, SETS, C_PASS, C_WEL = range(10)

# --- কিবোর্ডসমূহ ---
def main_kb():
    return ReplyKeyboardMarkup([
        ['👥 USER LIST', '💬 SENT MSG'],
        ['📢 BROADCAST', '🚫 BLOCK'],
        ['✅ UNBAN', '📑 BLOCK LIST'],
        ['⚙️ SETTINGS', '🚪 LOGOUT']
    ], resize_keyboard=True)

def sets_kb():
    return ReplyKeyboardMarkup([
        ['🔑 Change Password', '👋 Change Welcome Message'],
        ['⬅️ Back']
    ], resize_keyboard=True)

# --- সাধারণ ইউজার হ্যান্ডলার ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    uid = str(user.id)
    
    if uid in db['blocked']:
        return

    # ইউজার রেজিস্টার করা
    db['users'][uid] = {"name": user.full_name, "username": f"@{user.username}"}
    save_data(db)

    if user.id == ADMIN_ID:
        await update.message.reply_text(f"স্বাগতম বস! প্যানেলে ঢুকতে /admin লিখুন।")
    else:
        await update.message.reply_text(db['welcome_msg'])

async def handle_msg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    uid = str(user.id)
    
    if uid in db['blocked'] or user.id == ADMIN_ID:
        return
    
    # অ্যাডমিনকে মেসেজ পাঠানো
    await context.bot.send_message(
        chat_id=ADMIN_ID, 
        text=f"📩 *নতুন মেসেজ!*\n👤 নাম: {user.full_name}\n🆔 আইডি: `{user.id}`\n\nবার্তা: {update.message.text}",
        parse_mode='Markdown'
    )

# --- অ্যাডমিন প্যানেল লজিক ---
async def admin_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    await update.message.reply_text("🔐 প্যানেল পাসওয়ার্ড দিন:", reply_markup=ReplyKeyboardRemove())
    return PASS

async def auth(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == db['password']:
        await update.message.reply_text("✅ অ্যাক্সেস মঞ্জুর! মেনু সিলেক্ট করুন:", reply_markup=main_kb())
        return HOME
    else:
        await update.message.reply_text("❌ ভুল পাসওয়ার্ড! আবার চেষ্টা করতে /admin লিখুন।")
        return ConversationHandler.END

async def admin_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    
    if text == "👥 USER LIST":
        msg = "📊 *ইউজার লিস্ট:*\n\n"
        for uid, info in db['users'].items():
            msg += f"🔹 {info['name']} - `{uid}`\n"
        await update.message.reply_text(msg if len(db['users']) > 0 else "কোনো ইউজার নেই।", parse_mode='Markdown')
        return HOME

    elif text == "📢 BROADCAST":
        await update.message.reply_text("প্রচারের জন্য মেসেজটি লিখুন (বাতিল করতে /cancel):")
        return BCAST

    elif text == "💬 SENT MSG":
        await update.message.reply_text("যাকে মেসেজ পাঠাবেন তার ID দিন:")
        return S_ID

    elif text == "🚫 BLOCK":
        await update.message.reply_text("ব্লক করতে ইউজার ID দিন:")
        return BLK

    elif text == "✅ UNBAN":
        await update.message.reply_text("আনব্যান করতে ইউজার ID দিন:")
        return UNB

    elif text == "📑 BLOCK LIST":
        await update.message.reply_text(f"🚫 ব্লকড আইডিগুলো: {db['blocked'] or 'কেউ নেই'}")
        return HOME

    elif text == "⚙️ SETTINGS":
        await update.message.reply_text("⚙️ সেটিংস মেনু:", reply_markup=sets_kb())
        return SETS

    elif text == "🚪 LOGOUT":
        await update.message.reply_text("অ্যাডমিন প্যানেল থেকে লগআউট করা হয়েছে।", reply_markup=ReplyKeyboardRemove())
        return ConversationHandler.END
    
    return HOME

# --- অ্যাকশন হ্যান্ডলারস ---
async def do_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message.text
    count = 0
    for uid in db['users']:
        try:
            await context.bot.send_message(chat_id=int(uid), text=f"📢 *ঘোষণা:*\n\n{msg}", parse_mode='Markdown')
            count += 1
        except: pass
    await update.message.reply_text(f"✅ {count} জনের কাছে পাঠানো হয়েছে।", reply_markup=main_kb())
    return HOME

async def get_send_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['target_id'] = update.message.text
    await update.message.reply_text("মেসেজটি লিখুন:")
    return S_TXT

async def do_send_msg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        target = context.user_data['target_id']
        await context.bot.send_message(chat_id=target, text=f"💬 *অ্যাডমিনের বার্তা:*\n\n{update.message.text}", parse_mode='Markdown')
        await update.message.reply_text("✅ মেসেজ পাঠানো হয়েছে!", reply_markup=main_kb())
    except:
        await update.message.reply_text("❌ পাঠানো যায়নি। আইডি সঠিক তো?", reply_markup=main_kb())
    return HOME

async def do_block(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.message.text
    if uid not in db['blocked']:
        db['blocked'].append(uid)
        save_data(db)
    await update.message.reply_text(f"🚫 আইডি {uid} ব্লক করা হয়েছে।", reply_markup=main_kb())
    return HOME

async def do_unban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.message.text
    if uid in db['blocked']:
        db['blocked'].remove(uid)
        save_data(db)
    await update.message.reply_text(f"✅ আইডি {uid} আনব্যান করা হয়েছে।", reply_markup=main_kb())
    return HOME

# --- সেটিংস লজিক ---
async def settings_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    t = update.message.text
    if t == '🔑 Change Password':
        await update.message.reply_text("নতুন পাসওয়ার্ডটি লিখুন:")
        return C_PASS
    if t == '👋 Change Welcome Message':
        await update.message.reply_text("নতুন Welcome Message টি লিখুন:")
        return C_WEL
    if t == '⬅️ Back':
        await update.message.reply_text("প্রধান মেনু:", reply_markup=main_kb())
        return HOME
    return SETS

async def update_pass(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db['password'] = update.message.text
    save_data(db)
    await update.message.reply_text("✅ পাসওয়ার্ড সফলভাবে পরিবর্তন হয়েছে!", reply_markup=sets_kb())
    return SETS

async def update_wel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db['welcome_msg'] = update.message.text
    save_data(db)
    await update.message.reply_text("✅ Welcome Message আপডেট হয়েছে!", reply_markup=sets_kb())
    return SETS

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("অপারেশন বাতিল।", reply_markup=main_kb())
    return HOME

# --- মেইন রানার ---
def main():
    app = Application.builder().token(TOKEN).build()
    
    admin_handler = ConversationHandler(
        entry_points=[CommandHandler('admin', admin_start)],
        states={
            PASS: [MessageHandler(filters.TEXT & ~filters.COMMAND, auth)],
            HOME: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_buttons)],
            BCAST: [MessageHandler(filters.TEXT & ~filters.COMMAND, do_broadcast)],
            S_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_send_id)],
            S_TXT: [MessageHandler(filters.TEXT & ~filters.COMMAND, do_send_msg)],
            BLK: [MessageHandler(filters.TEXT & ~filters.COMMAND, do_block)],
            UNB: [MessageHandler(filters.TEXT & ~filters.COMMAND, do_unban)],
            SETS: [MessageHandler(filters.TEXT & ~filters.COMMAND, settings_choice)],
            C_PASS: [MessageHandler(filters.TEXT & ~filters.COMMAND, update_pass)],
            C_WEL: [MessageHandler(filters.TEXT & ~filters.COMMAND, update_wel)],
        },
        fallbacks=[CommandHandler('cancel', cancel), CommandHandler('start', start)],
        allow_reentry=True
    )

    app.add_handler(admin_handler)
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_msg))
    
    print("Bot is starting...")
    app.run_polling()

if __name__ == '__main__':
    main()
