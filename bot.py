#نویسنده :@Cyber_Blade
#کانال ما : @Cyber43
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import subprocess
import threading
import os
import zipfile
import random
import shutil
import sqlite3

api_id = 31465942 # اپی ایدی
api_hash = "e7b43af4e6ea21dfcbfe9462eb5e6a8b" # اپی هش
bot_token = "8586435834:AAF3494SL5UM3HVZPlCKMY2vihu6vetJN30" # توکن

OWNER_ID = 8048066572 # ایدی عددی مالک

app = Client("my_bot", api_id=api_id, api_hash=api_hash, bot_token=bot_token)
running_processes = {}
files_store = {}
user_state = {}
ui_state = {}

conn = sqlite3.connect("bot.db", check_same_thread=False)
cur = conn.cursor()
cur.execute("""
CREATE TABLE IF NOT EXISTS files (
    code_id TEXT PRIMARY KEY,
    file_path TEXT,
    folder_path TEXT
)
""")
conn.commit()

def generate_code_id():
    return str(random.randint(1000, 9999))

def save_file(code_id, file_path, folder):
    cur.execute("INSERT OR REPLACE INTO files VALUES (?, ?, ?)", (code_id, file_path, folder))
    conn.commit()

def load_files():
    cur.execute("SELECT code_id, file_path, folder_path FROM files")
    return cur.fetchall()

def main_menu():
    return InlineKeyboardMarkup(
        [[InlineKeyboardButton("دادن کد شخصی و ارسال فایل ✅", callback_data="run")],
         [InlineKeyboardButton("نصب کتابخانه ✅", callback_data="install")],
         [InlineKeyboardButton("لغو اجرا ❌", callback_data="cancel")],
         [InlineKeyboardButton("اجرای کد ▶️", callback_data="rerun")],
         [InlineKeyboardButton("دیدن خروجی 📄", callback_data="output")]]
    )

def back_menu():
    return InlineKeyboardMarkup([[InlineKeyboardButton("بازگشت ⬅️", callback_data="back")]])

def execute_code(file_path, code_id, chat_id):
    folder = str(code_id)
    os.makedirs(folder, exist_ok=True)
    file_name = os.path.basename(file_path)
    new_path = os.path.join(folder, file_name)
    if file_path != new_path:
        os.replace(file_path, new_path)
    output_file = os.path.join(folder, "output.txt")
    with open(output_file, "w", encoding="utf-8") as f:
        proc = subprocess.Popen(["python", new_path], stdout=f, stderr=subprocess.STDOUT)
        running_processes[code_id] = proc
        files_store[code_id] = new_path
        save_file(code_id, new_path, folder)
    def monitor_process():
        proc.wait()
        if code_id in running_processes:
            del running_processes[code_id]
    threading.Thread(target=monitor_process, daemon=True).start()

def install_library(lib_name, chat_id):
    proc = subprocess.Popen(["pip", "install", lib_name], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    output, _ = proc.communicate()
    app.send_message(chat_id, "نتیجه نصب:\n" + (output[-3500:] if output else "تمام شد"), reply_markup=back_menu())

@app.on_message(filters.command("start"))
def start(client, message):
    if message.from_user.id != OWNER_ID:
        return
    sent = message.reply_text("ربات آماده است:", reply_markup=main_menu())
    ui_state[message.from_user.id] = sent.id

@app.on_callback_query()
def callback_query(client, cq):
    if cq.from_user.id != OWNER_ID:
        return
    user_id = cq.from_user.id
    ui_state[user_id] = cq.message.id
    if cq.data == "run":
        user_state[user_id] = "await_code"
        cq.message.edit_text("فایل یا کد خود را بفرستید (.py یا .zip)", reply_markup=back_menu())
    elif cq.data == "install":
        user_state[user_id] = "await_library"
        cq.message.edit_text("نام کتابخانه را بفرستید:", reply_markup=back_menu())
    elif cq.data == "cancel":
        user_state[user_id] = "await_cancel"
        cq.message.edit_text("کد شخصی فایل را بفرستید:", reply_markup=back_menu())
    elif cq.data == "rerun":
        user_state[user_id] = "await_rerun"
        cq.message.edit_text("کد شخصی فایل را بفرستید برای اجرا:", reply_markup=back_menu())
    elif cq.data == "output":
        user_state[user_id] = "await_output"
        cq.message.edit_text("کد شخصی فایل را بفرستید برای دیدن خروجی:", reply_markup=back_menu())
    elif cq.data == "back":
        if user_id in user_state:
            user_state.pop(user_id)
        cq.message.edit_text("بازگشت به منو:", reply_markup=main_menu())

@app.on_message(filters.private)
def handle_message(client, message):
    if message.from_user.id != OWNER_ID:
        return
    user_id = message.from_user.id
    state = user_state.get(user_id)
    menu_msg_id = ui_state.get(user_id)
    if state == "await_code":
        if message.document:
            file_name = message.document.file_name
            file_path = message.download(file_name)
            if file_name.endswith(".zip"):
                with zipfile.ZipFile(file_path, 'r') as zip_ref:
                    zip_ref.extractall("extracted")
                files = [f for f in os.listdir("extracted") if f.endswith(".py")]
                codes = []
                for f_name in files:
                    code_id = generate_code_id()
                    abs_path = os.path.join("extracted", f_name)
                    threading.Thread(target=execute_code, args=(abs_path, code_id, message.chat.id)).start()
                    codes.append(code_id)
                if codes:
                    message.reply_text("کدها در حال اجرا هستند: " + ", ".join(codes), reply_markup=back_menu())
                else:
                    message.reply_text("فایل zip شامل کد پایتون نبود", reply_markup=back_menu())
            else:
                code_id = generate_code_id()
                threading.Thread(target=execute_code, args=(file_path, code_id, message.chat.id)).start()
                message.reply_text(f"کد شما در حال اجراست. کد شخصی: {code_id}", reply_markup=back_menu())
        elif message.text:
            code_id = generate_code_id()
            folder = str(code_id)
            os.makedirs(folder, exist_ok=True)
            code_name = os.path.join(folder, f"temp_code_{code_id}.py")
            with open(code_name, "w", encoding="utf-8") as f:
                f.write(message.text)
            threading.Thread(target=execute_code, args=(code_name, code_id, message.chat.id)).start()
            message.reply_text(f"کد شما در حال اجراست. کد شخصی: {code_id}", reply_markup=back_menu())
        if user_id in user_state:
            user_state.pop(user_id)
    elif state == "await_library":
        lib_name = message.text.strip()
        threading.Thread(target=install_library, args=(lib_name, message.chat.id)).start()
        if user_id in user_state:
            user_state.pop(user_id)
    elif state == "await_cancel":
        code_id = message.text.strip()
        cur.execute("SELECT file_path, folder_path FROM files WHERE code_id = ?", (code_id,))
        row = cur.fetchone()
        if row:
            file_path, folder = row
            if code_id in running_processes:
                try:
                    running_processes[code_id].kill()
                except Exception:
                    pass
                try:
                    subprocess.run(["pkill", "-f", file_path], check=False)
                except Exception:
                    pass
                if code_id in running_processes:
                    del running_processes[code_id]
            if code_id in files_store:
                del files_store[code_id]
            message.reply_text("اجرای کد متوقف شد و فایل برای استفاده بعدی باقی ماند", reply_markup=back_menu())
        else:
            message.reply_text("کد پیدا نشد", reply_markup=back_menu())
        if user_id in user_state:
            user_state.pop(user_id)
    elif state == "await_rerun":
        code_id = message.text.strip()
        cur.execute("SELECT file_path FROM files WHERE code_id = ?", (code_id,))
        row = cur.fetchone()
        if row:
            file_path = row[0]
            threading.Thread(target=execute_code, args=(file_path, code_id, message.chat.id)).start()
            message.reply_text("کد دوباره اجرا شد", reply_markup=back_menu())
        else:
            message.reply_text("کد پیدا نشد", reply_markup=back_menu())
        if user_id in user_state:
            user_state.pop(user_id)
    elif state == "await_output":
        code_id = message.text.strip()
        cur.execute("SELECT folder_path FROM files WHERE code_id = ?", (code_id,))
        row = cur.fetchone()
        if row:
            folder = row[0]
            output_file = os.path.join(folder, "output.txt")
            if os.path.exists(output_file):
                app.send_document(message.chat.id, output_file)
                message.reply_text("خروجی ارسال شد", reply_markup=back_menu())
            else:
                message.reply_text("خروجی یافت نشد", reply_markup=back_menu())
        else:
            message.reply_text("کد پیدا نشد", reply_markup=back_menu())
        if user_id in user_state:
            user_state.pop(user_id)
    else:
        sent = message.reply_text("ربات آماده است:", reply_markup=main_menu())
        ui_state[user_id] = sent.id

for code_id, file_path, folder in load_files():
    files_store[code_id] = file_path

app.run()
