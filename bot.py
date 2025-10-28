import telebot
from telebot import types
import random

# --- KONFIGURATSIYA ---
# Bot tokeningizni shu yerga kiriting. Uni @BotFather dan olishingiz mumkin.
BOT_TOKEN = "7710717172:AAHSpMqnhXqV55KWd9VSY2Il8qPVTeThMSA"  # <-- BU YERGA O'Z TOKENINGIZNI QO'YING

# Bot obyektini yaratish
bot = telebot.TeleBot(BOT_TOKEN)

# Foydalanuvchilar ballarini saqlash uchun lug'at
user_scores = {}

# HTML savollari va javoblari
html_questions = [
    {
        "question": "HTML da <h1> tegi nima uchun ishlatiladi?",
        "options": ["a) Rasmlar uchun", "b) Sarlavhalar uchun", "c) Havolalar uchun", "d) Paragraflar uchun"],
        "correct": "b"
    },
    {
        "question": "HTML da qaysi element web sahifaga rasm qo'shish uchun ishlatiladi?",
        "options": ["a) <image>", "b) <img>", "c) <src>", "d) <picture>"],
        "correct": "b"
    },
    {
        "question": "HTML da hyperlink (havola) qanday yaratiladi?",
        "options": ["a) <a href='url'>link</a>", "b) <link>url</link>", "c) <href>url</href>", "d) <url>link</url>"],
        "correct": "a"
    },
    {
        "question": "HTML da ro'yxat (list) yaratish uchun qaysi teg ishlatiladi?",
        "options": ["a) <list>", "b) <ul>", "c) <ol>", "d) b va c to'g'ri"],
        "correct": "d"
    },
    {
        "question": "HTML da jadval qanday yaratiladi?",
        "options": ["a) <table>", "b) <tab>", "c) <grid>", "d) <rows>"],
        "correct": "a"
    },
    {
        "question": "HTML da CSS qanday ulanadi?",
        "options": ["a) <style>", "b) <link>", "c) <script>", "d) a va b to'g'ri"],
        "correct": "d"
    },
    {
        "question": "HTML5 da yangi qo'shilgan semantik teglar qaysilar?",
        "options": ["a) <header>, <footer>, <nav>", "b) <div>, <span>", "c) <b>, <i>", "d) <table>, <tr>"],
        "correct": "a"
    },
    {
        "question": "HTML da form elementi qanday yaratiladi?",
        "options": ["a) <form>", "b) <input>", "c) <fieldset>", "d) Barchasi to'g'ri"],
        "correct": "d"
    },
    {
        "question": "HTML da kommentariya qanday yoziladi?",
        "options": ["a) <!-- Kommentariya -->", "b) // Kommentariya", "c) /* Kommentariya */", "d) # Kommentariya"],
        "correct": "a"
    },
    {
        "question": "HTML da <br> tegi nima uchun ishlatiladi?",
        "options": ["a) Qatorni tugatish uchun", "b) Qatorni ajratish uchun", "c) Bo'sh joy qo'shish uchun", "d) Matnni qalin qilish uchun"],
        "correct": "b"
    }
]

# --- TUGMALARNI YARATISH FUNKSIYALARI ---

def create_main_keyboard():
    """
    Asosiy menyu tugmalarini (ReplyKeyboard) yaratuvchi funksiya.
    Bu tugmalar foydalanuvchi interfeysining past doimiy turadi.
    """
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    # Tugmalarni yaratish
    btn_info = types.KeyboardButton("📚 Ma'lumot")
    btn_inline = types.KeyboardButton("🎯 Inline Tugmalar")
    btn_quiz = types.KeyboardButton("📝 Savol-Javob")
    btn_profile = types.KeyboardButton("👤 Profil")
    btn_settings = types.KeyboardButton("⚙️ Sozlamalar")
    # Tugmalarni klaviaturaga qo'shish
    keyboard.add(btn_info, btn_inline, btn_quiz, btn_profile, btn_settings)
    return keyboard

def create_inline_keyboard():
    """
    Xabarga biriktiriladigan tugmalarni (InlineKeyboard) yaratuvchi funksiya.
    """
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    # Tugmalarni yaratish
    btn_like = types.InlineKeyboardButton(text="👍 Yoqdi", callback_data="like_pressed")
    btn_dislike = types.InlineKeyboardButton(text="👎 Yoqmadi", callback_data="dislike_pressed")
    btn_refresh = types.InlineKeyboardButton(text="🔄 Yangilash", callback_data="refresh_data")
    btn_website = types.InlineKeyboardButton(text="🌐 portfoliom", url="https://pp.runstax.uz")
    # Tugmalarni klaviaturaga qo'shish
    keyboard.add(btn_like, btn_dislike)
    keyboard.add(btn_refresh, btn_website)
    return keyboard

def create_quiz_keyboard(question_index):
    """
    Savol-javob o'yini uchun inline tugmalar yaratish.
    Endi faqat javob variantlari mavjud.
    """
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    
    # Har bir variant uchun tugma yaratish
    for option in html_questions[question_index]["options"]:
        callback_data = f"quiz_answer_{question_index}_{option[0]}"  # a, b, c, d
        keyboard.add(types.InlineKeyboardButton(text=option, callback_data=callback_data))
    
    # "Keyingi savol" tugmasi olib tashlandi, chunki o'tish avtomatik.
    return keyboard

def create_results_keyboard():
    """
    Natijalar uchun tugmalar yaratish
    """
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    keyboard.add(types.InlineKeyboardButton(text="🔄 Testni qayta boshlash", callback_data="quiz_restart"))
    keyboard.add(types.InlineKeyboardButton(text="🔙 Asosiy menyu", callback_data="back_to_menu"))
    return keyboard

# --- HANDLERLAR (BOTNI QANDAY JAVOB BERISHINI ANIQLAYDI) ---

@bot.message_handler(commands=['start'])
def send_welcome(message):
    """
    /start buyrug'i uchun handler. Foydalanuvchiga salom beradi va asosiy menyunini ko'rsatadi.
    """
    user_id = message.from_user.id
    user_scores[user_id] = {"current_question": 0, "correct_answers": 0, "answered": [False] * len(html_questions)}
    
    bot.send_message(
        message.chat.id,
        f"Assalomu alaykum, {message.from_user.full_name}! 👋\n\n"
        "Men `pyTelegr` yordamida yaratilgan chiroyli botman. "
        "Pastdagi menudan tanlang!\n\n"
        "🆕 Yangi funksiya: HTML bo'yicha savol-javob testi!",
        reply_markup=create_main_keyboard(),
        parse_mode="Markdown"
    )

@bot.message_handler(func=lambda message: message.text == "📚 Ma'lumot")
def send_info(message):
    """
    "📚 Ma'lumot" tugmasi bosilganda ishlaydi.
    """
    info_text = (
        "Bu - `pyTelegramBotAPI` yordamida yaratilgan Telegram bot misoli.\n\n"
        "🔹 *Asosiy funksiyalar:*\n"
        "• Interaktiv menyu\n"
        "• Inline tugmalar\n"
        "• Foydalanuvchi profili\n"
        "• HTML bo'yicha test\n\n"
        "Bot to'liq Python tilida yozilgan va tezkor javob berish uchun optimallashtirilgan."
    )
    bot.send_message(message.chat.id, info_text, parse_mode="Markdown")

@bot.message_handler(func=lambda message: message.text == "🎯 Inline Tugmalar")
def send_inline_buttons(message):
    """
    "🎯 Inline Tugmalar" tugmasi bosilganda foydalanuvchiga inline tugmalar bilan xabar yuboradi.
    """
    bot.send_message(message.chat.id, "Quyidagi tugmalardan birini bosing:", reply_markup=create_inline_keyboard())

@bot.message_handler(func=lambda message: message.text == "📝 Savol-Javob")
def start_quiz(message):
    """
    "📝 Savol-Javob" tugmasi bosilganda testni boshlaydi
    """
    user_id = message.from_user.id
    if user_id not in user_scores:
        user_scores[user_id] = {"current_question": 0, "correct_answers": 0, "answered": [False] * len(html_questions)}
    
    question_index = user_scores[user_id]["current_question"]
    send_question(message.chat.id, question_index)

def send_question(chat_id, question_index):
    """
    Foydalanuvchiga savol yuborish
    """
    question = html_questions[question_index]["question"]
    
    question_text = (
        f"📝 *HTML Testi*\n\n"
        f"Savol {question_index + 1}/{len(html_questions)}\n\n"
        f"*{question}*"
    )
    
    bot.send_message(
        chat_id, 
        question_text, 
        reply_markup=create_quiz_keyboard(question_index),
        parse_mode="Markdown"
    )

@bot.message_handler(func=lambda message: message.text == "👤 Profil")
def send_profile(message):
    """
    "👤 Profil" tugmasi bosilganda foydalanuvchi haqida ma'lumot ko'rsatadi.
    """
    user = message.from_user
    user_id = user.id
    
    # Foydalanuvchining test natijalarini olish
    test_info = ""
    if user_id in user_scores:
        correct = user_scores[user_id]["correct_answers"]
        total = len(html_questions)
        percentage = round((correct / total) * 100, 1) if total > 0 else 0
        test_info = f"\n\n📊 *Test natijalari:*\n"
        test_info += f"✅ To'g'ri javoblar: {correct}/{total}\n"
        test_info += f"📈 Foiz: {percentage}%"
    
    profile_text = (
        f"👤 *Sizning profilingiz*\n\n"
        f"🆔 ID: `{user.id}`\n"
        f"👤 Ism: {user.full_name}\n"
        f"👥 Username: @{user.username if user.username else 'mavjud emas'}"
        f"{test_info}"
    )
    bot.send_message(message.chat.id, profile_text, parse_mode="Markdown")

@bot.message_handler(func=lambda message: message.text == "⚙️ Sozlamalar")
def send_settings(message):
    """
    "⚙️ Sozlamalar" tugmasi bosilganda xabar yuboradi.
    """
    settings_text = (
        "⚙️ *Sozlamalar*\n\n"
        "Hozircha mavjud sozlamalar:\n"
        "• 🌐 Til: O'zbekcha\n"
        "• 📊 Statistika: Yoqilgan\n"
        "• 🔔 Bildirishnomalar: Yoqilgan\n\n"
        "Qo'shimcha sozlamalar tez orada qo'shiladi..."
    )
    bot.send_message(message.chat.id, settings_text, parse_mode="Markdown")

# --- INLINE TUGMALAR UCHUN CALLBACK HANDLERLARI ---

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    """
    Inline tugmalarga bosilganda ishlaydigan asosiy handler.
    """
    bot.answer_callback_query(call.id)
    user_id = call.from_user.id
    
    if call.data == "like_pressed":
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text="Siz ma'lumotga yoqdi deb belgiladingiz! 😊"
        )
    elif call.data == "dislike_pressed":
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text="Afsuski, sizga yoqmadi. Keyingi safar yaxshiroq bo'ladi! 🙏"
        )
    elif call.data == "refresh_data":
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text="Ma'lumot muvaffaqiyatli yangilandi! Quyidagi tugmalardan foydalaning:",
            reply_markup=create_inline_keyboard()
        )
    elif call.data.startswith("quiz_answer_"):
        # Test javobini tekshirish va avtomatik ravishda keyingisiga o'tish
        parts = call.data.split("_")
        question_index = int(parts[2])
        answer = parts[3]
        
        if user_id not in user_scores:
            # Agar foydalanuvchi ma'lumotlari yo'q bo'lsa, uni qayta boshlaymiz
            start_quiz(call.message)
            return

        # Agar bu savolga avval javob berilmagan bo'lsa
        if not user_scores[user_id]["answered"][question_index]:
            user_scores[user_id]["answered"][question_index] = True
            
            # To'g'ri javobni tekshirish
            if answer == html_questions[question_index]["correct"]:
                user_scores[user_id]["correct_answers"] += 1
                result_text = "✅ To'g'ri javob!"
            else:
                # To'g'ri javobning to'liq matnini topish
                correct_option_text = next(opt for opt in html_questions[question_index]["options"] if opt.startswith(html_questions[question_index]["correct"]))
                result_text = f"❌ Noto'g'ri javob! To'g'ri javobi: {correct_option_text}"

            # Keyingi savolga o'tish yoki natijalarni ko'rsatish
            next_question_index = question_index + 1
            
            if next_question_index < len(html_questions):
                # Agar keyingi savol bo'lsa, uni ko'rsatamiz
                user_scores[user_id]["current_question"] = next_question_index
                next_q_data = html_questions[next_question_index]
                
                combined_text = (
                    f"{result_text}\n\n" # Avvalgi savol natijasi
                    f"📝 *HTML Testi*\n\n"
                    f"Savol {next_question_index + 1}/{len(html_questions)}\n\n"
                    f"*{next_q_data['question']}*"
                )
                
                bot.edit_message_text(
                    chat_id=call.message.chat.id,
                    message_id=call.message.message_id,
                    text=combined_text,
                    reply_markup=create_quiz_keyboard(next_question_index),
                    parse_mode="Markdown"
                )
            else:
                # Agar bu oxirgi savol bo'lsa, natijalarni ko'rsatamiz
                correct = user_scores[user_id]["correct_answers"]
                total = len(html_questions)
                percentage = round((correct / total) * 100, 1) if total > 0 else 0
                
                final_result_text = (
                    f"🏆 *Test tugadi!*\n\n"
                    f"Oxirgi savolga javob: {result_text}\n\n"
                    f"Siz {total} ta savoldan {correct} tasiga to'g'ri javob berdingiz.\n"
                    f"📊 Foiz: {percentage}%\n\n"
                )
                
                if percentage >= 80:
                    final_result_text += "🥇 A'lo! HTML bo'yicha a'lo bilimga egasiz!"
                elif percentage >= 60:
                    final_result_text += "🥈 Yaxshi! HTML bo'yicha yaxshi bilimga egasiz."
                elif percentage >= 40:
                    final_result_text += "🥉 Qoniqarli. HTML bo'yicha ko'proq o'rganishingiz kerak."
                else:
                    final_result_text += "📚 Past. HTML bo'yicha ko'proq o'rganishni tavsiya etamiz."
                
                bot.edit_message_text(
                    chat_id=call.message.chat.id,
                    message_id=call.message.message_id,
                    text=final_result_text,
                    reply_markup=create_results_keyboard(),
                    parse_mode="Markdown"
                )
    elif call.data == "quiz_restart":
        # Testni qayta boshlash
        user_scores[user_id] = {"current_question": 0, "correct_answers": 0, "answered": [False] * len(html_questions)}
        
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text="Test qayta boshlanmoqda..."
        )
        
        send_question(call.message.chat.id, 0)
    elif call.data == "back_to_menu":
        # Asosiy menuga qaytish
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text="Asosiy menuga qaytdingiz. Pastdagi tugmalardan foydalaning!"
        )

# --- BOTNI ISHGA TUSHURISH ---
if __name__ == '__main__':
    print("Bot ishga tushirilmoqda...")
    bot.infinity_polling()
    print("Bot to'xtatildi.")
