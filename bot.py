import sqlite3
import uuid
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, ContextTypes, filters

TOKEN = "8814146319:AAHIftzavL08p0A4801MOVz96p5gIOJUu-I"
ADMIN_ID = 1833467870

SUPPORT_USERNAME = "itsokbroitok"  
CHANNEL_LINK = "https://t.me/MYSYQHUB" 

# Yahan hum GitHub link ki jagah apna Telegram ka file_id daalenge
QR_IMAGE_ID = "YAHAN_APNA_FILE_ID_DALNA_HAI" 
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

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if check_ban(user.id):
        return await update.message.reply_text("❌ Aapko is bot se ban kar diya gaya hai.")
    add_user(user.id, user.first_name)
    await update.message.reply_text(f"Welcome to Master Bot, {user.first_name}! 👑\nSelect an option below:", reply_markup=get_main_menu(user.id))

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
        keyboard = [[InlineKeyboardButton("🔙 Back to Plans", callback_data='back_from_photo')]]
        
        # Agar file_id set nahi hai toh error na aaye isliye check lagaya hai
        try:
            await context.bot.send_photo(
                chat_id=user_id,
                photo=QR_IMAGE_ID,
                caption=text,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="Markdown"
            )
            await query.message.delete()
        except:
            await query.edit_message_text(text=text + "\n\n*(QR Code image ID set nahi hai!)*", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
        
    elif query.data == 'back_from_photo':
        await query.message.delete()
        text = f"Welcome to Master Bot, {first_name}! 👑\nSelect an option below:"
        await context.bot.send_message(chat_id=user_id, text=text, reply_markup=get_main_menu(user_id))
    elif query.data == 'download_file':
        text = f"📥 **Download File**\n\n{DOWNLOAD_FILE_LINK}"
        keyboard = [[InlineKeyboardButton("🔙 Back", callback_data='back')]]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
    elif query.data == 'admin' and user_id == ADMIN_ID:
        users = db_query("SELECT COUNT(*) FROM users", fetchone=True)[0]
        text = f"⚙️ **Admin Panel**\n\n👥 Total Users: `{users}`\n\n**Commands:**\n`/broadcast msg`\n`/ban user_id`\n`/unban user_id`"
        keyboard = [[InlineKeyboardButton("🔙 Back", callback_data='back')]]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

async def handle_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id
    
    # AGAR ADMIN NE PHOTO BHEJI HAI, TOH BOT USKA FILE_ID BHI DEGA
    if user_id == ADMIN_ID and update.message.photo:
        photo_id = update.message.photo[-1].file_id
        await update.message.reply_text(f"📸 **Aapka File ID yeh hai:**\n`{photo_id}`\n\nIse copy karke code mein `QR_IMAGE_ID` ki jagah daal dein!", parse_mode="Markdown")
        return

    if user_id == ADMIN_ID and update.message.text:
        text = update.message.text
        if text.startswith("/broadcast") and context.args:
            msg = " ".join(context.args)
            users = db_query("SELECT user_id FROM users", fetchall=True)
            for u in users:
                try: await context.bot.send_message(chat_id=u[0], text=f"📢 **Admin Message:**\n\n{msg}", parse_mode="Markdown")
                except: pass
            await update.message.reply_text("✅ Broadcast done.")
            return
        elif text.startswith("/ban") and context.args:
            db_query("UPDATE users SET is_banned = 1 WHERE user_id = ?", (int(context.args[0]),), commit=True)
            await update.message.reply_text(f"✅ User banned.")
            return
        elif text.startswith("/unban") and context.args:
            db_query("UPDATE users SET is_banned = 0 WHERE user_id = ?", (int(context.args[0]),), commit=True)
            await update.message.reply_text(f"✅ User unbanned.")
            return

    if user_id != ADMIN_ID and update.message.text:
        text = update.message.text
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=f"🔔 **New Payment Verification Request!**\n\n👤 User: {user.first_name} (`{user_id}`)\n💳 UTR / Details: `{text}`",
            parse_mode="Markdown"
        )
        await update.message.reply_text("✅ **Aapka UTR admin ko bhej diya gaya hai!**", reply_markup=get_main_menu(user_id))

if __name__ == '__main__':
    init_db()
    app = ApplicationBuilder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(buttons))
    app.add_handler(MessageHandler(filters.PHOTO | filters.TEXT & ~filters.COMMAND, handle_messages))
    
    print("Master_Bot Started...")
    app.run_polling()
