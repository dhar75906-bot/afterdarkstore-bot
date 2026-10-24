import sqlite3
import random
import string
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, ContextTypes, filters

TOKEN = "8814146319:AAHIftzavL08p0A4801MOVz96p5gIOJUu-I"
ADMIN_ID = 1833467870

SUPPORT_USERNAME = "itsokbroitok"  
CHANNEL_LINK = "https://t.me/MYSYQHUB" 
CHANNEL_USERNAME = "@MYSYQHUB" 
QR_IMAGE_ID = "YAHAN_APNA_FILE_ID_DALNA_HAI" # Agar aapne file_id di thi toh wo yahan dalein, ya neeche fallback link hai
DOWNLOAD_FILE_LINK = "File ka link abhi add nahi kiya gaya hai. Kripya baad mein check karein." 

# ================= DATABASE SETUP =================
def init_db():
    conn = sqlite3.connect("master_bot.db")
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY, first_name TEXT, 
                    is_premium INTEGER DEFAULT 0, balance INTEGER DEFAULT 0, 
                    is_banned INTEGER DEFAULT 0, referred_by INTEGER DEFAULT 0)''')
    c.execute('''CREATE TABLE IF NOT EXISTS keys (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, license_key TEXT, is_used INTEGER DEFAULT 0)''')
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
        if referred_by and referred_by != user_id:
            db_query("UPDATE users SET balance = balance + 10 WHERE user_id = ?", (referred_by,), commit=True)
        return True
    return False

def check_ban(user_id):
    user = db_query("SELECT is_banned FROM users WHERE user_id = ?", (user_id,), fetchone=True)
    return user[0] == 1 if user else False

async def check_subscription(user_id, context):
    try:
        member = await context.bot.get_chat_member(chat_id=CHANNEL_USERNAME, user_id=user_id)
        if member.status in ['member', 'administrator', 'creator']:
            return True
    except:
        pass
    return False

# ================= MENUS =================
def get_main_menu(user_id):
    keyboard = [
        [InlineKeyboardButton("🤖 Jarvis engine", callback_data='jarvis')],
        [InlineKeyboardButton("📥 Download file", callback_data='download_file')],
        [InlineKeyboardButton("👥 Referral Link", callback_data='referral'),
         InlineKeyboardButton("⭐ Feedback", callback_data='feedback')],
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

    ref_id = 0
    if context.args:
        try:
            ref_id = int(context.args[0])
        except:
            pass

    add_user(user.id, user.first_name, ref_id)

    is_joined = await check_subscription(user.id, context)
    if not is_joined:
        keyboard = [
            [InlineKeyboardButton("📢 Join Channel", url=CHANNEL_LINK)],
            [InlineKeyboardButton("🔄 Joined, Verify Now", callback_data='check_sub')]
        ]
        await update.message.reply_text(
            f"⚠️ **Pehle Hamara Channel Join Karein!**\n\nBot ko use karne ke liye hamare channel {CHANNEL_USERNAME} ko join karna anivary hai.",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
        return

    await update.message.reply_text(
        f"Welcome to After Dark Store, {user.first_name}! 👑\nSelect an option below:", 
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

    if query.data == 'check_sub':
        is_joined = await check_subscription(user_id, context)
        if is_joined:
            text = f"Welcome to After Dark Store, {first_name}! 👑\nSelect an option below:"
            await query.edit_message_text(text, reply_markup=get_main_menu(user_id))
        else:
            await query.answer("❌ Aapne abhi tak channel join nahi kiya hai!", show_alert=True)

    elif query.data == 'back':
        text = f"Welcome to After Dark Store, {first_name}! 👑\nSelect an option below:"
        await query.edit_message_text(text, reply_markup=get_main_menu(user_id))
        
    elif query.data == 'jarvis':
        text = "🔑 **KEY PLAN LIST**\n\nApna plan select karein:"
        await query.edit_message_text(text, reply_markup=get_plans_menu(), parse_mode="Markdown")
        
    elif query.data.startswith('plan_'):
        amount = query.data.split('_')[1]
        text = f"🛒 **Plan Selected:** ₹{amount}\n\n📷 **Payment Instructions:**\nNeeche diye gaye QR Code ko scan karein aur ₹{amount} pay karein.\n\nPayment ke baad apna **12-digit UPI Transaction ID (UTR)** yahan bhej dein."
        keyboard = [[InlineKeyboardButton("🔙 Back to Plans", callback_data='back_from_photo')]]
        
        try:
            await context.bot.send_photo(
                chat_id=user_id,
                photo=QR_IMAGE_ID,
                caption=text,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="Markdown"
            )
            await query.message.delete()
        except Exception as e:
            # Agar file_id mein koi error ho toh text format mein bhej dega taaki app crash na ho
            await query.edit_message_text(
                text=text + f"\n\n*(QR image load nahi ho paayi. Kripya support par contact karein)*", 
                reply_markup=InlineKeyboardMarkup(keyboard), 
                parse_mode="Markdown"
            )
        
    elif query.data == 'back_from_photo':
        await query.message.delete()
        text = f"Welcome to After Dark Store, {first_name}! 👑\nSelect an option below:"
        await context.bot.send_message(chat_id=user_id, text=text, reply_markup=get_main_menu(user_id))
        
    elif query.data == 'download_file':
        text = f"📥 **Download File**\n\n{DOWNLOAD_FILE_LINK}"
        keyboard = [[InlineKeyboardButton("🔙 Back", callback_data='back')]]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data == 'referral':
        bot_username = (await context.bot.get_me()).username
        ref_link = f"https://t.me/{bot_username}?start={user_id}"
        user_data = db_query("SELECT balance FROM users WHERE user_id = ?", (user_id,), fetchone=True)
        balance = user_data[0] if user_data else 0
        text = f"👥 **Referral & Wallet System**\n\nApne doston ko yeh link share karein aur har join par rewards payein!\n\n🔗 Your Link:\n`{ref_link}`\n\n💰 Wallet Balance: `₹{balance}`"
        keyboard = [[InlineKeyboardButton("🔙 Back", callback_data='back')]]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

    elif query.data == 'feedback':
        text = "⭐ **Feedback System**\n\nKripya apne anubhav ke baare mein apna feedback yahan chat mein type karke bhejein."
        keyboard = [[InlineKeyboardButton("🔙 Back", callback_data='back')]]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
        
    elif query.data == 'admin' and user_id == ADMIN_ID:
        users = db_query("SELECT COUNT(*) FROM users", fetchone=True)[0]
        text = f"⚙️ **Admin Panel**\n\n👥 Total Users: `{users}`\n\n**Commands:**\n`/broadcast msg`\n`/addkey KEY`\n`/ban user_id`\n`/unban user_id`"
        keyboard = [[InlineKeyboardButton("🔙 Back", callback_data='back')]]
        await query.edit_message_text(text, reply_markup=Get_keyboard_back := InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

    elif query.data.startswith('approve_'):
        target_user_id = int(query.data.split('_')[1])
        key_str = "JARVIS-" + ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
        db_query("UPDATE users SET is_premium = 1 WHERE user_id = ?", (target_user_id,), commit=True)
        
        try:
            await context.bot.send_message(
                chat_id=target_user_id,
                text=f"🎉 **Payment Verified Successfully!**\n\nAapka plan activate ho gaya hai. Aapki License Key yeh rahi:\n\n`{key_str}`",
                parse_mode="Markdown"
            )
        except:
            pass
        await query.edit_message_caption(caption=query.message.caption + "\n\n✅ **Approved & Key Sent!**", reply_markup=None)

# ================= MESSAGE & ADMIN HANDLERS =================
async def handle_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id
    
    if user_id == ADMIN_ID and update.message.photo:
        photo_id = update.message.photo[-1].file_id
        await update.message.reply_text(f"📸 **File ID:**\n`{photo_id}`\n\nIse copy karke code mein `QR_IMAGE_ID` ki jagah daal dein!", parse_mode="Markdown")
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
        elif text.startswith("/addkey") and context.args:
            new_key = context.args[0]
            db_query("INSERT INTO keys (license_key) VALUES (?)", (new_key,), commit=True)
            await update.message.reply_text(f"✅ Key added: {new_key}")
            return
        elif text.startswith("/ban") and context.args:
            db_query("UPDATE users SET is_banned = 1 WHERE user_id = ?", (int(context.args[0]),), commit=True)
            await update.message.reply_text("✅ User banned.")
            return
        elif text.startswith("/unban") and context.args:
            db_query("UPDATE users SET is_banned = 0 WHERE user_id = ?", (int(context.args[0]),), commit=True)
            await update.message.reply_text("✅ User unbanned.")
            return

    if user_id != ADMIN_ID and update.message.text:
        text = update.message.text
        keyboard = [[InlineKeyboardButton("✅ Approve & Send Key", callback_data=f'approve_{user_id}')]]
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=f"🔔 **New Payment Verification!**\n\n👤 User: {user.first_name} (`{user_id}`)\n💳 UTR / Details: `{text}`",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
        await update.message.reply_text("✅ **Aapka UTR admin ko bhej diya gaya hai!** Verification ke baad key mil jayegi.", reply_markup=get_main_menu(user_id))

if __name__ == '__main__':
    init_db()
    app = ApplicationBuilder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(buttons))
    app.add_handler(MessageHandler(filters.PHOTO | filters.TEXT & ~filters.COMMAND, handle_messages))
    
    print("After Dark Store Bot Started...")
    app.run_polling()
