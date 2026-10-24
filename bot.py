import sqlite3
import uuid
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, ContextTypes, filters

TOKEN = "8814146319:AAHIftzavL08p0A4801MOVz96p5gIOJUu-I"
ADMIN_ID = 1833467870

SUPPORT_USERNAME = "itsokbroitok"  
CHANNEL_LINK = "https://t.me/MYSYQHUB" 
QR_IMAGE_URL = "https://raw.githubusercontent.com/dhar75906-bot/afterdarkstore-bot/main/qr.jpg"
DOWNLOAD_FILE_LINK = "File ka link abhi add nahi kiya gaya hai. Kripya baad mein check karein." 

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
        return True
    return False

def check_ban(user_id):
    user = db_query("SELECT is_banned FROM users WHERE user_id = ?", (user_id,), fetchone=True)
    return user[0] == 1 if user else False

# ================= MENUS =================
def get_main_menu(user_id):
    keyboard = [
        [InlineKeyboardButton("🤖 Jarvis engine", callback_data='jarvis')],
        [InlineKeyboardButton("📥 Download file", callback_data='download_file')],
        [
            InlineKeyboardButton("🎧 Support", url=f"https://t.me/{SUPPORT_USERNAME}"),
            InlineKeyboardButton("📢 Channel", url=CHANNEL_LINK)
        ]
    ]
    if user_id == ADMIN_ID:
        keyboard.append([InlineKeyboardButton("⚙️ Admin Panel", callback_data='admin')])
    return InlineKeyboardMarkup(keyboard)

def get_plans_menu():
    keyboard = [
        [InlineKeyboardButton("1 DAY · ₹70", callback_data='plan_70'),
         InlineKeyboardButton("3 DAYS · ₹140", callback_data='plan_140')],
        [InlineKeyboardButton("7 DAYS · ₹300", callback_data='plan_300'),
         InlineKeyboardButton("15 DAYS · ₹450", callback_data='plan_450')],
        [InlineKeyboardButton("30 DAYS · ₹750", callback_data='plan_750'),
         InlineKeyboardButton("90 DAYS · ₹1700", callback_data='plan_1700')],
        [InlineKeyboardButton("🔙 Back", callback_data='back')]
    ]
    return InlineKeyboardMarkup(keyboard)

# ================= START COMMAND =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if check_ban(user.id):
        return await update.message.reply_text("❌ Aapko is bot se ban kar diya gaya hai.")

    add_user(user.id, user.first_name)
    await update.message.reply_text(
        f"Welcome to Master Bot, {user.first_name}! 👑\nSelect an option below:", 
        reply_markup=get_main_menu(user.id)
    )

# ================= BUTTON HANDLERS =================
async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    first_name = query.from_user.first_name
    
    add_user(user_id, first_name)
    if check_ban(user_id): return await query.answer("Aap banned hain!", show_alert=True)
    await query.answer()

    if query.data == 'back':
        text = f"Welcome to Master Bot, {first_name}! 👑\nSelect an option below:"
        await query.edit_message_text(text, reply_markup=get_main_menu(user_id))
        
    elif query.data == 'jarvis':
        text = "🔑 **KEY PLAN LIST**\n\nApna plan select karein:"
        await query.edit_message_text(text, reply_markup=get_plans_menu(), parse_mode="Markdown")
        
    elif query.data.startswith('plan_'):
        amount = query.data.split('_')[1]
        text = f"🛒 **Plan Selected:** ₹{amount}\n\n📷 **Payment Instructions:**\nNeeche diye gaye QR Code ko scan karein aur ₹{amount} pay karein.\n\nPayment ke baad apna **12-digit UPI Transaction ID (UTR)** yahan bhej dein."
        keyboard = [
            [InlineKeyboardButton("🔙 Back to Plans", callback_data='back_from_photo')]
        ]
        try:
            await context.bot.send_photo(
                chat_id=user_id,
                photo=QR_IMAGE_URL,
                caption=text,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="Markdown"
            )
            await query.message.delete()
        except Exception as e:
            # Agar QR image load hone mein koi error aaye toh text bhej dega taaki bot crash na ho
            await query.edit_message_text(
                text=text + f"\n\n*(QR Image Link Error: {e})*", 
                reply_markup=InlineKeyboardMarkup(keyboard), 
                parse_mode="Markdown"
            )
        
    elif query.data == 'back_from_photo':
        await query.message.delete()
        text = f"Welcome to Master Bot, {first_name}! 👑\nSelect an option below:"
        await context.bot.send_message(chat_id=user_id, text=text, reply_markup=get_main_menu(user_id))
        
    elif query.data == 'download_file':
        text = f"📥 **Download File**\n\n{DOWNLOAD_FILE_LINK}"
        keyboard = [[InlineKeyboardButton("🔙 Back", callback_data='back')]]
        await query.edit_message_text(text, reply_markup=get_keyboard_back := InlineKeyboardMarkup(keyboard))
        
    elif query.data == 'admin' and user_id == ADMIN_ID:
        users = db_query("SELECT COUNT(*) FROM users", fetchone=True)[0]
        text = f"⚙️ **Admin Panel**\n\n👥 Total Users: `{users}`\n\n**Commands:**\n`/broadcast msg`\n`/ban user_id`\n`/unban user_id`"
        keyboard = [[InlineKeyboardButton("🔙 Back", callback_data='back')]]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

# ================= MESSAGE & ADMIN HANDLERS =================
async def handle_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id
    text = update.message.text

    if user_id == ADMIN_ID:
        # Admin commands check
        if text.startswith("/broadcast") and context.args:
            msg = " ".join(context.args)
            users = db_query("SELECT user_id FROM users", fetchall=True)
            sent = 0
            m = await update.message.reply_text("Broadcasting...")
            for u in users:
                try:
                    await context.bot.send_message(chat_id=u[0], text=f"📢 **Admin Message:**\n\n{msg}", parse_mode="Markdown")
                    sent += 1
                except: pass
            await m.edit_text(f"✅ Broadcast done: {sent}/{len(users)}")
            return
        elif text.startswith("/ban") and context.args:
            db_query("UPDATE users SET is_banned = 1 WHERE user_id = ?", (int(context.args[0]),), commit=True)
            await update.message.reply_text(f"✅ User {context.args[0]} banned.")
            return
        elif text.startswith("/unban") and context.args:
            db_query("UPDATE users SET is_banned = 0 WHERE user_id = ?", (int(context.args[0]),), commit=True)
            await update.message.reply_text(f"✅ User {context.args[0]} unbanned.")
            return

    # Normal user ne agar payment ke baad UTR (Transaction ID) bheja hai
    if user_id != ADMIN_ID:
        # Forward UTR to Admin for instant verification
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=f"🔔 **New Payment Verification Request!**\n\n👤 User: {user.first_name} (`{user_id}`)\n💳 UTR / Details: `{text}`",
            parse_mode="Markdown"
        )
        await update.message.reply_text(
            "✅ **Aapka UTR / Payment detail admin ko bhej diya gaya hai!**\nVerify hote hi aapko key mil jayegi.",
            reply_markup=get_main_menu(user_id)
        )

if __name__ == '__main__':
    init_db()
    app = ApplicationBuilder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(buttons))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_messages))
    
    print("Master Bot Started...")
    app.run_polling()
