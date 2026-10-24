import sqlite3
import uuid
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, ContextTypes, filters

TOKEN = "8814146319:AAHIftzavL08p0A4801MOVz96p5gIOJUu-I"
ADMIN_ID = 1833467870
REFERRAL_BONUS = 50

# ================= DATABASE SETUP =================
def init_db():
    conn = sqlite3.connect("master_bot.db")
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY, first_name TEXT, 
                    is_premium INTEGER DEFAULT 0, balance INTEGER DEFAULT 0, 
                    is_banned INTEGER DEFAULT 0, referred_by INTEGER DEFAULT 0)''')
    c.execute('''CREATE TABLE IF NOT EXISTS files (
                    code TEXT PRIMARY KEY, file_id TEXT, file_type TEXT)''')
    conn.commit()
    conn.close()

def db_query(query, args=(), fetchone=False, fetchall=False, commit=False):
    conn = sqlite3.connect("master_bot.db")
    c = conn.cursor()
    c.execute(query, args)
    res = None
    if fetchone: res = c.fetchone()
    if fetchall: res = c.fetchall()
    if commit: conn.commit()
    conn.close()
    return res

def add_user(user_id, first_name, referred_by=0):
    user = db_query("SELECT user_id FROM users WHERE user_id = ?", (user_id,), fetchone=True)
    if not user:
        db_query("INSERT INTO users (user_id, first_name, referred_by) VALUES (?, ?, ?)", 
                 (user_id, first_name, referred_by), commit=True)
        if referred_by != 0 and referred_by != user_id:
            db_query("UPDATE users SET balance = balance + ? WHERE user_id = ?", (REFERRAL_BONUS, referred_by), commit=True)
        return True
    return False

def check_ban(user_id):
    user = db_query("SELECT is_banned FROM users WHERE user_id = ?", (user_id,), fetchone=True)
    return user[0] == 1 if user else False

# ================= MAIN MENU KEYBOARD =================
def get_main_menu(user_id):
    btn1 = InlineKeyboardButton("👤 My Profile", callback_data='profile')
    btn2 = InlineKeyboardButton("💎 Premium", callback_data='premium')
    btn3 = InlineKeyboardButton("💰 Earn Money", callback_data='refer')
    btn4 = InlineKeyboardButton("📥 File Info", callback_data='fileinfo')
    
    keyboard = [
        [btn1, btn2],
        [btn3],
        [btn4]
    ]
    
    if user_id == ADMIN_ID:
        admin_btn = InlineKeyboardButton("⚙️ Admin Panel", callback_data='admin')
        keyboard.append([admin_btn])
        
    return InlineKeyboardMarkup(keyboard)

# ================= START COMMAND =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if check_ban(user.id):
        return await update.message.reply_text("❌ Aapko is bot se ban kar diya gaya hai.")

    args = context.args
    referred_by = 0
    if args:
        if args[0].startswith("ref_"):
            try: referred_by = int(args[0].split("_")[1])
            except: pass
        elif args[0].startswith("file_"):
            file_code = args[0].split("_")[1]
            f_data = db_query("SELECT file_id, file_type FROM files WHERE code = ?", (file_code,), fetchone=True)
            if f_data:
                add_user(user.id, user.first_name, 0)
                if f_data[1] == "doc": await update.message.reply_document(f_data[0])
                elif f_data[1] == "photo": await update.message.reply_photo(f_data[0])
                elif f_data[1] == "video": await update.message.reply_video(f_data[0])
                return
            else:
                return await update.message.reply_text("❌ File link expire ho gaya hai.")

    is_new = add_user(user.id, user.first_name, referred_by)
    if is_new and referred_by != 0:
        try: await context.bot.send_message(chat_id=referred_by, text=f"🎉 **New Referral!**\n{user.first_name} ne aapke link se join kiya. Aapko {REFERRAL_BONUS} points mile!", parse_mode="Markdown")
        except: pass

    await update.message.reply_text(
        f"Welcome to Master Bot, {user.first_name}! 👑\nSelect an option below:", 
        reply_markup=get_main_menu(user.id)
    )

# ================= BUTTON HANDLERS =================
async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    first_name = query.from_user.first_name
    
    if check_ban(user_id): return await query.answer("Aap banned hain!", show_alert=True)
    await query.answer()

    back_btn = InlineKeyboardButton("🔙 Back to Menu", callback_data='back')
    back_markup = InlineKeyboardMarkup([[back_btn]])

    if query.data == 'back':
        text = f"Welcome to Master Bot, {first_name}! 👑\nSelect an option below:"
        await query.edit_message_text(text, reply_markup=get_main_menu(user_id))
        return

    elif query.data == 'profile':
        user_data = db_query("SELECT balance, is_premium FROM users WHERE user_id = ?", (user_id,), fetchone=True)
        status = "💎 Premium" if user_data[1] else "🆓 Free User"
        text = f"👤 **Your Profile**\n\n🆔 ID: `{user_id}`\n💰 Balance: `{user_data[0]}` Points\n🔰 Status: {status}"
        await query.edit_message_text(text, reply_markup=back_markup, parse_mode="Markdown")
        
    elif query.data == 'refer':
        bot_usr = (await context.bot.get_me()).username
        ref_link = f"https://t.me/{bot_usr}?start=ref_{user_id}"
        text = f"💰 **Refer & Earn**\n\nShare this link. Get {REFERRAL_BONUS} points per join!\n\n🔗 Your Link:\n`{ref_link}`"
        await query.edit_message_text(text, reply_markup=back_markup, parse_mode="Markdown")
        
    elif query.data == 'premium':
        text = "💎 **Premium Plans**\n\nBenefits: No ads, unlimited downloads.\nContact Admin to buy."
        await query.edit_message_text(text, reply_markup=back_markup, parse_mode="Markdown")
        
    elif query.data == 'fileinfo':
        text = "📥 **File Sharing System**\n\n- Bot me stored files aap direct link se download kar sakte hain.\n- Admin yahan files upload kar sakta hai."
        await query.edit_message_text(text, reply_markup=back_markup, parse_mode="Markdown")
        
    elif query.data == 'admin' and user_id == ADMIN_ID:
        users = db_query("SELECT COUNT(*) FROM users", fetchone=True)[0]
        text = f"⚙️ **Admin Panel**\n\n👥 Total Users: `{users}`\n\n**Commands:**\n`/broadcast msg`\n`/ban user_id`\n`/unban user_id`\n`/addcoins user_id amount`\n`/stats`"
        await query.edit_message_text(text, reply_markup=back_markup, parse_mode="Markdown")

# ================= ADMIN COMMANDS & FILES =================
async def admin_commands(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != ADMIN_ID: return
    cmd = update.message.text.split()[0].lower()
    args = context.args

    if cmd == "/stats":
        total = db_query("SELECT COUNT(*) FROM users", fetchone=True)[0]
        await update.message.reply_text(f"📊 **Stats:** Total Users: {total}")
    elif cmd == "/broadcast" and args:
        msg = " ".join(args)
        users = db_query("SELECT user_id FROM users", fetchall=True)
        sent = 0
        m = await update.message.reply_text("Broadcasting...")
        for u in users:
            try:
                await context.bot.send_message(chat_id=u[0], text=f"📢 **Admin Message:**\n\n{msg}", parse_mode="Markdown")
                sent += 1
            except: pass
        await m.edit_text(f"✅ Broadcast done: {sent}/{len(users)}")
    elif cmd == "/ban" and args:
        db_query("UPDATE users SET is_banned = 1 WHERE user_id = ?", (int(args[0]),), commit=True)
        await update.message.reply_text(f"✅ User {args[0]} banned.")
    elif cmd == "/unban" and args:
        db_query("UPDATE users SET is_banned = 0 WHERE user_id = ?", (int(args[0]),), commit=True)
        await update.message.reply_text(f"✅ User {args[0]} unbanned.")
    elif cmd == "/addcoins" and len(args) == 2:
        db_query("UPDATE users SET balance = balance + ? WHERE user_id = ?", (int(args[1]), int(args[0])), commit=True)
        await update.message.reply_text(f"✅ Added {args[1]} coins to {args[0]}.")

async def file_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    
    code = str(uuid.uuid4())[:6]
    if update.message.document: f_type, f_id = "doc", update.message.document.file_id
    elif update.message.photo: f_type, f_id = "photo", update.message.photo[-1].file_id
    elif update.message.video: f_type, f_id = "video", update.message.video.file_id
    else: return

    db_query("INSERT INTO files (code, file_id, file_type) VALUES (?, ?, ?)", (code, f_id, f_type), commit=True)
    bot_usr = (await context.bot.get_me()).username
    await update.message.reply_text(f"✅ **File Uploaded!**\n🔗 Link: `https://t.me/{bot_usr}?start=file_{code}`", parse_mode="Markdown")

if __name__ == '__main__':
    init_db()
    app = ApplicationBuilder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(buttons))
    app.add_handler(MessageHandler(filters.COMMAND & filters.User(ADMIN_ID), admin_commands))
    app.add_handler(MessageHandler((filters.Document.ALL | filters.PHOTO | filters.VIDEO) & filters.User(ADMIN_ID), file_handler))
    
    print("Master Bot Started...")
    app.run_polling()
