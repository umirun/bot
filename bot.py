import telebot
import json
import random
import os
import time # Yangi qo'shilgan modul

# --- KONFIGURATSIYA ---
BOT_TOKEN = "8150817960:AAEGAh0EpQ7U_HpuZSQCWWf_Irn7shs5REE"
BOT_USERNAME = "@sitesotar_bot"
ADMIN_PASSWORD = "19781986"
# >>>>> O'ZINGIZNING TELEGRAM ID'INGIZNI SHU YERGA YOZING <<<<<
ADMIN_ID = 6407919120

bot = telebot.TeleBot(BOT_TOKEN)
DATA_FILE = 'data.json'

# --- VIKTORINA UCHUN HOLATNI SAQLASH ---
user_quiz_state = {}

# --- MA'LUMOTLAR BAZASI ---
def load_data():
    if not os.path.exists(DATA_FILE):
        return {"users": {}, "websites": [], "quiz_questions": [], "next_site_id": 1, "next_user_id": 1}
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

# --- YORDAMCHI FUNKSIYALAR ---
def get_user_balance(user_id):
    data = load_data()
    return data['users'].get(str(user_id), {}).get('balance', 0)

def update_user_balance(user_id, amount):
    data = load_data()
    user_id_str = str(user_id)
    if user_id_str not in data['users']:
        data['users'][user_id_str] = {'balance': 0, 'referrals': 0, 'username': ''}
    data['users'][user_id_str]['balance'] += amount
    save_data(data)

def register_user(user_id, username):
    data = load_data()
    user_id_str = str(user_id)
    if user_id_str not in data['users']:
        data['users'][user_id_str] = {'balance': 0, 'referrals': 0, 'username': username}
        save_data(data)

def get_main_menu():
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(telebot.types.KeyboardButton("📦 Saytlar ro'yxati"))
    markup.add(telebot.types.KeyboardButton("💰 Mening balansim"))
    markup.add(telebot.types.KeyboardButton("👥 Do'stni taklif qilish"))
    markup.add(telebot.types.KeyboardButton("🧠 Viktorina"))
    return markup

def get_admin_menu():
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(telebot.types.KeyboardButton("➕ Yangi sayt qo'shish"))
    markup.add(telebot.types.KeyboardButton("🗑️ Saytni o'chirish")) # YANGI
    markup.add(telebot.types.KeyboardButton("📁 Faylni yuklash (ZIP)"))
    markup.add(telebot.types.KeyboardButton("🎬 Media yuklash (Rasm/Video)"))
    markup.add(telebot.types.KeyboardButton("💸 Narxni o'zgartirish"))
    markup.add(telebot.types.KeyboardButton("💳 Balansni boshqarish"))
    markup.add(telebot.types.KeyboardButton("❓ Savol qo'shish (Viktorina)"))
    markup.add(telebot.types.KeyboardButton("📢 Barchaga xabar yuborish")) # YANGI
    markup.add(telebot.types.KeyboardButton("👤 Foydalanuvchilar ro'yxati"))
    markup.add(telebot.types.KeyboardButton("🔙 Chiqish"))
    return markup

# --- BOT HANDLER'LARI (avvalgidek) ---
@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.from_user.id
    username = message.from_user.username
    register_user(user_id, username)

    if message.text.startswith('/start '):
        try:
            referrer_id = int(message.text.split()[1])
            if referrer_id != user_id:
                update_user_balance(referrer_id, 500)
                bot.send_message(referrer_id, f"🎉 Tabriklaymiz! Siz do'stingizni taklif qildingiz va 500 so'm bonus oldingiz!")
                bot.send_message(user_id, f"Do'stingiz taklifi orqali botga qo'shildingiz. Xush kelibsiz!")
        except (ValueError, IndexError):
            pass

    referral_link = f"https://t.me/{BOT_USERNAME}?start={user_id}"
    welcome_text = (
        f"Assalomu alaykum, {message.from_user.first_name}! 👋\n\n"
        "Saytlar sotib olish va sotish bo'yicha botimizga xush kelibsiz!\n\n"
        "Do'stlaringizni taklif qiling va har bir do'stingiz uchun **500 so'm** bonus oling!\n"
        f"Sizning taklif linkingiz: {referral_link}"
    )
    bot.send_message(message.chat.id, welcome_text, reply_markup=get_main_menu())

@bot.message_handler(func=lambda message: message.text == "📦 Saytlar ro'yxati")
def show_websites_menu(message):
    data = load_data()
    if not data['websites']:
        bot.send_message(message.chat.id, "Hozircha sotuvda saytlar yo'q.")
        return

    markup = telebot.types.InlineKeyboardMarkup(row_width=1)
    for site in data['websites']:
        btn_text = f"🌐 {site['name']}"
        callback_data = f"view_site_{site['id']}"
        markup.add(telebot.types.InlineKeyboardButton(btn_text, callback_data=callback_data))
    
    bot.send_message(message.chat.id, "Sotuvdagi saytlar ro'yxati:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('view_site_'))
def callback_view_site(call):
    site_id = int(call.data.split('_')[2])
    data = load_data()
    site = next((s for s in data['websites'] if s['id'] == site_id), None)

    if not site:
        bot.answer_callback_query(call.id, "Xatolik: Sayt topilmadi.", show_alert=True)
        return

    caption_text = f"**{site['name']}**\n\n{site['description']}\n\n💰 *Narxi: {site['price']} so'm*"
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(telebot.types.InlineKeyboardButton("🛒 Sotib olish", callback_data=f"buy_site_{site['id']}"))
    markup.add(telebot.types.InlineKeyboardButton("🔙 Orqaga", callback_data="back_to_sites"))

    try:
        if site.get('media_id') and site.get('media_type'):
            if site['media_type'] == 'photo':
                bot.send_photo(call.message.chat.id, site['media_id'], caption=caption_text, reply_markup=markup, parse_mode='Markdown')
            elif site['media_type'] == 'video':
                bot.send_video(call.message.chat.id, site['media_id'], caption=caption_text, reply_markup=markup, parse_mode='Markdown')
        else:
            bot.send_message(call.message.chat.id, caption_text, reply_markup=markup, parse_mode='Markdown')
        bot.delete_message(call.message.chat.id, call.message.message_id)
    except Exception as e:
        bot.send_message(call.message.chat.id, f"Median yuklashda xatolik: {e}\n\n{caption_text}", reply_markup=markup, parse_mode='Markdown')

@bot.callback_query_handler(func=lambda call: call.data == "back_to_sites")
def callback_back_to_sites(call):
    show_websites_menu(call.message)
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call: call.data.startswith('buy_site_'))
def callback_buy_site(call):
    user_id = call.from_user.id
    site_id = int(call.data.split('_')[2])
    data = load_data()
    
    site = next((s for s in data['websites'] if s['id'] == site_id), None)
    if not site:
        bot.answer_callback_query(call.id, "Xatolik: Sayt topilmadi.", show_alert=True)
        return

    user_balance = get_user_balance(user_id)
    if user_balance >= site['price']:
        update_user_balance(user_id, -site['price'])
        
        if site.get('file_id'):
            try:
                bot.send_document(user_id, site['file_id'], caption=f"🎉 {site['name']} sayti fayllari muvaffaqiyatli yuklandi!")
            except Exception as e:
                bot.send_message(user_id, f"Faylni yuborishda xatolik yuz berdi. Iltimos, adminga murojaat qiling. Xato: {e}")
        else:
            bot.send_message(user_id, f"🎉 Siz '{site['name']}' saytini muvaffaqiyatli sotib oldingiz!\n\nHozircha admin fayllarni yuklamagan. Fayllar yuklanganidan so'ng sizga yuboriladi.")
        
        bot.answer_callback_query(call.id, "✅ Sotib olindi!")
    else:
        needed = site['price'] - user_balance
        bot.answer_callback_query(call.id, f"❌ Balansingiz yetarli emas! Sizga yana {needed} so'm kerak.", show_alert=True)

@bot.message_handler(func=lambda message: message.text == "💰 Mening balansim")
def show_balance(message):
    balance = get_user_balance(message.from_user.id)
    bot.send_message(message.chat.id, f"Sizning balansingiz: {balance} so'm")

@bot.message_handler(func=lambda message: message.text == "👥 Do'stni taklif qilish")
def send_referral_link(message):
    user_id = message.from_user.id
    referral_link = f"https://t.me/{BOT_USERNAME}?start={user_id}"
    bot.send_message(message.chat.id, f"Do'stlaringizni ushbu link orqali taklif qiling va har bir do'stingiz uchun **500 so'm** bonus oling!\n\n{referral_link}")

# --- VIKTORINA LOGIKASI (avvalgidek) ---
@bot.message_handler(func=lambda message: message.text == "🧠 Viktorina")
def start_quiz(message):
    data = load_data()
    if len(data['quiz_questions']) < 5:
        bot.send_message(message.chat.id, "Hozircha viktorina uchun savollar yetarli emas. Iltimos, keyinroq urinib ko'ring.")
        return
    
    user_id = message.from_user.id
    quiz_questions = random.sample(data['quiz_questions'], 5)
    user_quiz_state[user_id] = {
        'questions': quiz_questions,
        'current_index': 0,
        'correct_answers': 0
    }
    
    ask_next_question(user_id)

def ask_next_question(user_id):
    if user_id not in user_quiz_state:
        return

    state = user_quiz_state[user_id]
    if state['current_index'] < len(state['questions']):
        question_data = state['questions'][state['current_index']]
        question_text = f"🧠 Savol {state['current_index'] + 1}/5:\n\n{question_data['question']}"
        
        markup = telebot.types.InlineKeyboardMarkup(row_width=2)
        for i, option in enumerate(question_data['options']):
            letter = chr(65 + i) 
            callback_data = f"quiz_answer_{user_id}_{letter}"
            markup.add(telebot.types.InlineKeyboardButton(f"{letter}. {option}", callback_data=callback_data))
        
        bot.send_message(user_id, question_text, reply_markup=markup)
    else:
        if state['correct_answers'] == 5:
            update_user_balance(user_id, 100)
            bot.send_message(user_id, "🎉 Tabriklayman! Siz barcha 5 savolga to'g'ri javob berdingiz va 100 so'm bonus oldingiz!")
        else:
            bot.send_message(user_id, f"Viktorina tugadi. Siz {state['correct_answers']}/5 ta to'g'ri javob berdingiz. Barchasini to'g'ri javoblasangiz, bonus olasiz.")
        
        del user_quiz_state[user_id]
        bot.send_message(user_id, "Yana bir marotaba urinib ko'rish uchun '🧠 Viktorina' tugmasini bosing.", reply_markup=get_main_menu())

@bot.callback_query_handler(func=lambda call: call.data.startswith('quiz_answer_'))
def callback_quiz_answer(call):
    try:
        _, _, user_id_str, answer_letter = call.data.split('_')
        user_id = int(user_id_str)
    except (ValueError, IndexError):
        bot.answer_callback_query(call.id, "Xatolik!", show_alert=True)
        return

    if user_id not in user_quiz_state or call.from_user.id != user_id:
        bot.answer_callback_query(call.id, "Bu sizning viktorinangiz emas!", show_alert=True)
        return

    state = user_quiz_state[user_id]
    current_question = state['questions'][state['current_index']]
    
    if answer_letter == current_question['correct_answer']:
        state['correct_answers'] += 1
        bot.answer_callback_query(call.id, "✅ To'g'ri!")
    else:
        bot.answer_callback_query(call.id, f"❌ Noto'g'ri. To'g'ri javob: {current_question['correct_answer']}", show_alert=True)

    state['current_index'] += 1
    ask_next_question(user_id)

# --- ADMIN PANELI ---
@bot.message_handler(commands=['admin'])
def admin_login(message):
    if message.from_user.id != ADMIN_ID:
        bot.send_message(message.chat.id, "Bu buyruq faqat admin uchun!")
        return
    msg = bot.send_message(message.chat.id, "Admin paneliga kirish uchun parolni kiriting:")
    bot.register_next_step_handler(msg, check_admin_password)

def check_admin_password(message):
    if message.text == ADMIN_PASSWORD:
        bot.send_message(message.chat.id, "✅ Admin paneliga xush kelibsiz!", reply_markup=get_admin_menu())
    else:
        bot.send_message(message.chat.id, "❌ Noto'g'ri parol!", reply_markup=get_main_menu())

# --- YANGI: SAYTNI O'CHIRISH ---
@bot.message_handler(func=lambda message: message.text == "🗑️ Saytni o'chirish")
def admin_delete_site_step1(message):
    data = load_data()
    if not data['websites']:
        bot.send_message(message.chat.id, "O'chirish uchun sayt yo'q.")
        return

    markup = telebot.types.InlineKeyboardMarkup(row_width=1)
    for site in data['websites']:
        btn_text = f"🗑️ {site['name']}"
        callback_data = f"delete_site_{site['id']}"
        markup.add(telebot.types.InlineKeyboardButton(btn_text, callback_data=callback_data))
    
    bot.send_message(message.chat.id, "O'chirmoqchi bo'lgan saytni tanlang:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('delete_site_'))
def callback_delete_site(call):
    site_id = int(call.data.split('_')[2])
    data = load_data()
    
    site_to_delete = next((s for s in data['websites'] if s['id'] == site_id), None)
    if not site_to_delete:
        bot.answer_callback_query(call.id, "Xatolik: Sayt topilmadi.", show_alert=True)
        return

    # Saytni ro'yxatdan o'chirish
    data['websites'] = [s for s in data['websites'] if s['id'] != site_id]
    save_data(data)
    
    bot.answer_callback_query(call.id, f"'{site_to_delete['name']}' sayti o'chirildi.")
    # O'chirilgan sayt xabarini yangilash uchun eski xabarni o'chirib, yangisini yuboramiz
    bot.delete_message(call.message.chat.id, call.message.message_id)
    admin_delete_site_step1(call.message) # O'chirilgandan so'ng yangi ro'yxatni ko'rsatish

# --- YANGI: BARCHAGA XABAR YUBORISH ---
@bot.message_handler(func=lambda message: message.text == "📢 Barchaga xabar yuborish")
def admin_broadcast_step1(message):
    msg = bot.send_message(message.chat.id, "Barcha foydalanuvchilarga yuboriladigan xabar matnini, rasmini yoki videosini yuboring:")
    bot.register_next_step_handler(msg, process_broadcast)

def process_broadcast(message):
    data = load_data()
    user_ids = [int(uid) for uid in data['users'].keys()]
    if not user_ids:
        bot.send_message(message.chat.id, "Botda hozircha foydalanuvchilar yo'q.")
        return

    sent_count = 0
    failed_count = 0
    
    status_message = bot.send_message(message.chat.id, f"Xabar {len(user_ids)} ta foydalanuvchiga yuborilmoqda... Biroz kutib turing.")

    for user_id in user_ids:
        try:
            if message.content_type == 'text':
                bot.send_message(user_id, message.text)
            elif message.content_type == 'photo':
                bot.send_photo(user_id, message.photo[-1].file_id, caption=message.caption)
            elif message.content_type == 'video':
                bot.send_video(user_id, message.video.file_id, caption=message.caption)
            elif message.content_type == 'document':
                bot.send_document(user_id, message.document.file_id, caption=message.caption)
            
            sent_count += 1
            time.sleep(0.05) # Telegram limitlaridan saqlanish uchun kichik pauza
        except Exception as e:
            failed_count += 1
            print(f"Failed to send to {user_id}: {e}") # Xatoliklarni konsolga chiqarish

    bot.edit_message_text(
        chat_id=message.chat.id,
        message_id=status_message.message_id,
        text=f"✅ Yuborish tugadi!\n\n"
             f"👤 Jami foydalanuvchilar: {len(user_ids)}\n"
             f"✅ Muvaffaqiyatli yuborildi: {sent_count}\n"
             f"❌ Yuborilmadi: {failed_count}"
    )

# --- QOLGAN ADMIN FUNKSIYALARI (avvalgidek) ---
@bot.message_handler(func=lambda message: message.text == "💳 Balansni boshqarish")
def admin_manage_balance_menu(message):
    markup = telebot.types.InlineKeyboardMarkup(row_width=2)
    markup.add(telebot.types.InlineKeyboardButton("➕ Pul qo'shish", callback_data="manage_balance_add"))
    markup.add(telebot.types.InlineKeyboardButton("➖ Pul yechish", callback_data="manage_balance_remove"))
    bot.send_message(message.chat.id, "Foydalanuvchi balansini boshqarish:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('manage_balance_'))
def callback_manage_balance(call):
    action = call.data.split('_')[2]
    msg = bot.send_message(call.message.chat.id, "Balansini boshqarmoqchi bo'lgan foydalanuvchining Telegram ID'sini kiriting:")
    bot.register_next_step_handler(msg, process_balance_user_id, action)
    bot.answer_callback_query(call.id)

def process_balance_user_id(message, action):
    try:
        user_id_to_manage = int(message.text)
        data = load_data()
        if str(user_id_to_manage) not in data['users']:
            bot.send_message(message.chat.id, "❌ Bunday ID li foydalanuvchi topilmadi. Qaytadan urinib ko'ring:")
            bot.register_next_step_handler(message, process_balance_user_id, action)
            return
        msg = bot.send_message(message.chat.id, "Qancha summani kiritmoqchisiz? (faqat raqamlarda)")
        bot.register_next_step_handler(msg, process_balance_amount, user_id_to_manage, action)
    except ValueError:
        bot.send_message(message.chat.id, "❌ Noto'g'ri ID formati. Faqat raqamlardan foydalaning. Qaytadan urinib ko'ring:")
        bot.register_next_step_handler(message, process_balance_user_id, action)

def process_balance_amount(message, user_id_to_manage, action):
    try:
        amount = int(message.text)
        if action == 'add':
            update_user_balance(user_id_to_manage, amount)
            bot.send_message(message.chat.id, f"✅ Foydalanuvchi (ID: {user_id_to_manage}) balansi {amount} so'mga to'ldirildi.", reply_markup=get_admin_menu())
            bot.send_message(user_id_to_manage, f"🎉 Sizning balansingiz {amount} so'mga to'ldirildi. Joriy balans: {get_user_balance(user_id_to_manage)} so'm")
        elif action == 'remove':
            current_balance = get_user_balance(user_id_to_manage)
            if current_balance >= amount:
                update_user_balance(user_id_to_manage, -amount)
                bot.send_message(message.chat.id, f"✅ Foydalanuvchi (ID: {user_id_to_manage}) balansidan {amount} so'm yechildi.", reply_markup=get_admin_menu())
                bot.send_message(user_id_to_manage, f"⚠️ Sizning balansingizdan {amount} so'm yechildi. Joriy balans: {get_user_balance(user_id_to_manage)} so'm")
            else:
                bot.send_message(message.chat.id, f"❌ Foydalanuvchining balansi yetarli emas. Uning balansi: {current_balance} so'm.", reply_markup=get_admin_menu())
    except ValueError:
        bot.send_message(message.chat.id, "❌ Summani noto'g'ri kiritdingiz. Faqat raqamlardan foydalaning. Qaytadan urinib ko'ring:")
        bot.register_next_step_handler(message, process_balance_amount, user_id_to_manage, action)

@bot.message_handler(func=lambda message: message.text == "❓ Savol qo'shish (Viktorina)")
def admin_add_question_step1(message):
    msg = bot.send_message(message.chat.id, "Viktorina uchun yangi savolni kiriting:")
    bot.register_next_step_handler(msg, admin_add_question_step2)

def admin_add_question_step2(message):
    question_text = message.text
    msg = bot.send_message(message.chat.id, "Endi A variantini kiriting:")
    bot.register_next_step_handler(msg, admin_add_question_step3, question_text, {})

def admin_add_question_step3(message, question_text, options):
    options['A'] = message.text
    msg = bot.send_message(message.chat.id, "Endi B variantini kiriting:")
    bot.register_next_step_handler(msg, admin_add_question_step4, question_text, options)

def admin_add_question_step4(message, question_text, options):
    options['B'] = message.text
    msg = bot.send_message(message.chat.id, "Endi C variantini kiriting:")
    bot.register_next_step_handler(msg, admin_add_question_step5, question_text, options)

def admin_add_question_step5(message, question_text, options):
    options['C'] = message.text
    msg = bot.send_message(message.chat.id, "Endi D variantini kiriting:")
    bot.register_next_step_handler(msg, admin_add_question_step6, question_text, options)

def admin_add_question_step6(message, question_text, options):
    options['D'] = message.text
    msg = bot.send_message(message.chat.id, "Endi to'g'ri javobni kiriting (faqat A, B, C yoki D harfini):")
    bot.register_next_step_handler(msg, admin_add_question_final, question_text, options)

def admin_add_question_final(message, question_text, options):
    correct_answer = message.text.upper()
    if correct_answer in ['A', 'B', 'C', 'D']:
        data = load_data()
        new_question = {
            "question": question_text,
            "options": [options['A'], options['B'], options['C'], options['D']],
            "correct_answer": correct_answer
        }
        data['quiz_questions'].append(new_question)
        save_data(data)
        bot.send_message(message.chat.id, "✅ Yangi savol muvaffaqiyatli qo'shildi.", reply_markup=get_admin_menu())
    else:
        bot.send_message(message.chat.id, "❌ Noto'g'ri javob. Faqat A, B, C yoki D harflaridan birini kiriting. Qaytadan urinib ko'ring:")
        bot.register_next_step_handler(message, admin_add_question_final, question_text, options)

@bot.message_handler(func=lambda message: message.text == "➕ Yangi sayt qo'shish")
def admin_add_site_step1(message):
    msg = bot.send_message(message.chat.id, "Yangi saytning nomini kiriting:")
    bot.register_next_step_handler(msg, admin_add_site_step2)

def admin_add_site_step2(message):
    site_name = message.text
    msg = bot.send_message(message.chat.id, "Endi sayt uchun qisqa tavsif yozing:")
    bot.register_next_step_handler(msg, admin_add_site_step3, site_name)

def admin_add_site_step3(message, site_name):
    site_description = message.text
    msg = bot.send_message(message.chat.id, "Sayt narxini so'mda kiriting (masalan: 50000):")
    bot.register_next_step_handler(msg, admin_add_site_step4, site_name, site_description)

def admin_add_site_step4(message, site_name, site_description):
    try:
        price = int(message.text)
        msg = bot.send_message(message.chat.id, "Endi sayt uchun rasm yoki video yuboring (jpg, png, mp4):")
        bot.register_next_step_handler(msg, admin_add_site_media_step, site_name, site_description, price)
    except ValueError:
        bot.send_message(message.chat.id, "❌ Narxni faqat raqamlarda kiriting! Qaytadan urinib ko'ring:")
        bot.register_next_step_handler(message, admin_add_site_step4, site_name, site_description)

def admin_add_site_media_step(message, site_name, site_description, price):
    data = load_data()
    new_site = {
        "id": data['next_site_id'],
        "name": site_name,
        "description": site_description,
        "price": price,
        "file_id": None,
        "media_id": None,
        "media_type": None
    }
    data['websites'].append(new_site)
    data['next_site_id'] += 1
    save_data(data)

    if message.content_type == 'photo':
        new_site['media_id'] = message.photo[-1].file_id
        new_site['media_type'] = 'photo'
        save_data(data)
        bot.send_message(message.chat.id, "✅ Rasm saqlandi. Endi saytning ZIP faylini yuboring (yoki 'O'tkaz yuborish' deb yozing):")
    elif message.content_type == 'video':
        new_site['media_id'] = message.video.file_id
        new_site['media_type'] = 'video'
        save_data(data)
        bot.send_message(message.chat.id, "✅ Video saqlandi. Endi saytning ZIP faylini yuboring (yoki 'O'tkaz yuborish' deb yozing):")
    else:
        bot.send_message(message.chat.id, "❌ Rasm yoki video yuborilmadi. Keyinroq '🎬 Media yuklash' orqali qo'shishingiz mumkin. Hozircha ZIP faylni yuboring (yoki 'O'tkaz yuborish' deb yozing):")
    
    bot.register_next_step_handler(message, admin_add_site_zip_step, new_site['id'])

def admin_add_site_zip_step(message, site_id):
    if message.text and message.text.lower() == 'o\'tkaz yuborish':
        bot.send_message(message.chat.id, f"✅ '{site_id}' ID li sayt muvaffaqiyatli qo'shildi, lekin fayli yuklanmadi.", reply_markup=get_admin_menu())
        return

    if message.content_type == 'document':
        file_id = message.document.file_id
        data = load_data()
        for site in data['websites']:
            if site['id'] == site_id:
                site['file_id'] = file_id
                save_data(data)
                bot.send_message(message.chat.id, f"✅ Sayt va uning fayli muvaffaqiyatli qo'shildi!", reply_markup=get_admin_menu())
                return
    else:
        bot.send_message(message.chat.id, "❌ Iltimos, ZIP faylini yuboring yoki 'O'tkaz yuborish' deb yozing.")
        bot.register_next_step_handler(message, admin_add_site_zip_step, site_id)

@bot.message_handler(func=lambda message: message.text == "🎬 Media yuklash (Rasm/Video)")
def admin_upload_media_step1(message):
    data = load_data()
    if not data['websites']:
        bot.send_message(message.chat.id, "Avval sayt qo'shing.")
        return
    
    markup = telebot.types.InlineKeyboardMarkup(row_width=1)
    for site in data['websites']:
        btn_text = f"{site['name']}"
        callback_data = f"upload_media_{site['id']}"
        markup.add(telebot.types.InlineKeyboardButton(btn_text, callback_data=callback_data))
    
    bot.send_message(message.chat.id, "Qaysi sayt uchun media yuklamoqchisiz?", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('upload_media_'))
def callback_upload_media(call):
    site_id = int(call.data.split('_')[2])
    msg = bot.send_message(call.message.chat.id, "Endi sayt uchun rasm yoki videoni yuboring:")
    bot.register_next_step_handler(msg, process_media_upload, site_id)
    bot.answer_callback_query(call.id)

def process_media_upload(message, site_id):
    data = load_data()
    site_to_update = next((s for s in data['websites'] if s['id'] == site_id), None)
    if not site_to_update:
        bot.send_message(message.chat.id, "Xatolik: Sayt topilmadi.", reply_markup=get_admin_menu())
        return

    if message.content_type == 'photo':
        site_to_update['media_id'] = message.photo[-1].file_id
        site_to_update['media_type'] = 'photo'
        save_data(data)
        bot.send_message(message.chat.id, f"✅ Rasm '{site_to_update['name']}' saytiga muvaffaqiyatli yuklandi.", reply_markup=get_admin_menu())
    elif message.content_type == 'video':
        site_to_update['media_id'] = message.video.file_id
        site_to_update['media_type'] = 'video'
        save_data(data)
        bot.send_message(message.chat.id, f"✅ Video '{site_to_update['name']}' saytiga muvaffaqiyatli yuklandi.", reply_markup=get_admin_menu())
    else:
        bot.send_message(message.chat.id, "Iltimos, faqat rasm yoki video yuboring. Qaytadan urinib ko'ring:")
        bot.register_next_step_handler(message, process_media_upload, site_id)

@bot.message_handler(func=lambda message: message.text == "📁 Faylni yuklash (ZIP)")
def admin_upload_file_step1(message):
    data = load_data()
    if not data['websites']:
        bot.send_message(message.chat.id, "Avval sayt qo'shing.")
        return
    
    markup = telebot.types.InlineKeyboardMarkup(row_width=1)
    for site in data['websites']:
        if not site.get('file_id'):
            btn_text = f"{site['name']}"
            callback_data = f"upload_file_{site['id']}"
            markup.add(telebot.types.InlineKeyboardButton(btn_text, callback_data=callback_data))
    
    if not markup.keyboard:
        bot.send_message(message.chat.id, "Barcha saytlar uchun fayllar yuklangan.")
        return

    bot.send_message(message.chat.id, "Qaysi sayt uchun fayl yuklamoqchisiz?", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('upload_file_'))
def callback_upload_file(call):
    site_id = int(call.data.split('_')[2])
    msg = bot.send_message(call.message.chat.id, "Endi saytning ZIP arxivini (faylini) yuboring:")
    bot.register_next_step_handler(msg, process_file_upload, site_id)
    bot.answer_callback_query(call.id)

def process_file_upload(message, site_id):
    if message.content_type != 'document':
        bot.send_message(message.chat.id, "Iltimos, faqat 'document' ko'rinishida fayl yuboring. Qaytadan urinib ko'ring:")
        bot.register_next_step_handler(message, process_file_upload, site_id)
        return
    
    file_id = message.document.file_id
    data = load_data()
    for site in data['websites']:
        if site['id'] == site_id:
            site['file_id'] = file_id
            save_data(data)
            bot.send_message(message.chat.id, f"✅ Fayl '{site['name']}' saytiga muvaffaqiyatli yuklandi.", reply_markup=get_admin_menu())
            return
    
    bot.send_message(message.chat.id, "Xatolik: Sayt topilmadi.", reply_markup=get_admin_menu())

@bot.message_handler(func=lambda message: message.text == "💸 Narxni o'zgartirish")
def admin_change_price_step1(message):
    data = load_data()
    if not data['websites']:
        bot.send_message(message.chat.id, "O'zgartirish uchun sayt yo'q.")
        return

    markup = telebot.types.InlineKeyboardMarkup(row_width=1)
    for site in data['websites']:
        btn_text = f"{site['name']} - {site['price']} so'm"
        callback_data = f"change_price_{site['id']}"
        markup.add(telebot.types.InlineKeyboardButton(btn_text, callback_data=callback_data))
    
    bot.send_message(message.chat.id, "Narxini o'zgartirmoqchi bo'lgan saytni tanlang:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('change_price_'))
def callback_change_price(call):
    site_id = int(call.data.split('_')[2])
    msg = bot.send_message(call.message.chat.id, "Yangi narxni so'mda kiriting (masalan: 75000):")
    bot.register_next_step_handler(msg, process_price_change, site_id)
    bot.answer_callback_query(call.id)

def process_price_change(message, site_id):
    try:
        new_price = int(message.text)
        data = load_data()
        for site in data['websites']:
            if site['id'] == site_id:
                site['price'] = new_price
                save_data(data)
                bot.send_message(message.chat.id, f"✅ '{site['name']}' saytining narxi {new_price} so'mga o'zgartirildi.", reply_markup=get_admin_menu())
                return
        bot.send_message(message.chat.id, "Xatolik: Sayt topilmadi.", reply_markup=get_admin_menu())
    except ValueError:
        bot.send_message(message.chat.id, "❌ Narxni faqat raqamlarda kiriting! Qaytadan urinib ko'ring:")
        bot.register_next_step_handler(message, process_price_change, site_id)

@bot.message_handler(func=lambda message: message.text == "👤 Foydalanuvchilar ro'yxati")
def admin_show_users(message):
    data = load_data()
    if not data['users']:
        bot.send_message(message.chat.id, "Hozircha foydalanuvchilar yo'q.")
        return
    
    users_list = "👥 Foydalanuvchilar ro'yxati:\n\n"
    for user_id_str, user_info in data['users'].items():
        username = user_info.get('username', 'Noma\'lum')
        balance = user_info.get('balance', 0)
        referrals = user_info.get('referrals', 0)
        users_list += f"ID: {user_id_str}\nUsername: @{username}\nBalans: {balance} so'm\nTakliflar: {referrals}\n---------------------\n"
    
    if len(users_list) > 4000:
        with open('users_list.txt', 'w', encoding='utf-8') as f:
            f.write(users_list)
        with open('users_list.txt', 'rb') as f:
            bot.send_document(message.chat.id, f)
        os.remove('users_list.txt')
    else:
        bot.send_message(message.chat.id, users_list, reply_markup=get_admin_menu())

@bot.message_handler(func=lambda message: message.text == "🔙 Chiqish")
def admin_logout(message):
    bot.send_message(message.chat.id, "Admin panelidan chiqdingiz.", reply_markup=get_main_menu())

# Botni ishga tushirish
print("Bot ishga tushdi...")
bot.infinity_polling()
