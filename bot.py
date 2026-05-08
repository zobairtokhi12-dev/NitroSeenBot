from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import subprocess
import os
import random
import sqlite3

api_id = 31465942
api_hash = "e7b43af4e6ea21dfcbfe9462eb5e6a8b"
bot_token = "8586435834:AAF3494SL5UM3HVZPlCKMY2vihu6vetJN30"

OWNER_ID = 8048066572

app = Client(
"my_bot",
api_id=api_id,
api_hash=api_hash,
bot_token=bot_token
)

running_processes = {}
files_store = {}
user_state = {}

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
    pass
return str(random.randint(1000, 9999))

def save_file(code_id, file_path, folder):
cur.execute(
"INSERT OR REPLACE INTO files VALUES (?, ?, ?)",
(code_id, file_path, folder)
)
conn.commit()

def main_menu():
return InlineKeyboardMarkup([
[InlineKeyboardButton("ارسال فایل", callback_data="run")],
[InlineKeyboardButton("نصب کتابخانه", callback_data="install")]
])

def execute_code(file_path, code_id):

folder = str(code_id)

os.makedirs(folder, exist_ok=True)

file_name = os.path.basename(file_path)

new_path = os.path.join(folder, file_name)

if file_path != new_path:
    os.replace(file_path, new_path)

output_file = os.path.join(folder, "output.txt")

with open(output_file, "w", encoding="utf-8") as f:

    proc = subprocess.Popen(
        ["python", new_path],
        stdout=f,
        stderr=subprocess.STDOUT
    )

    running_processes[code_id] = proc
    files_store[code_id] = new_path

    save_file(code_id, new_path, folder)

    proc.wait()

def install_library(lib_name):
subprocess.run(["pip", "install", lib_name])

@app.on_message(filters.command("start"))
def start(client, message):

if message.from_user.id != OWNER_ID:
    return

message.reply_text(
    "ربات آماده است",
    reply_markup=main_menu()
)

@app.on_callback_query()
def callback_query(client, cq):

if cq.from_user.id != OWNER_ID:
    return

if cq.data == "run":

    user_state[cq.from_user.id] = "await_code"

    cq.message.edit_text("فایل بفرست")

elif cq.data == "install":

    user_state[cq.from_user.id] = "await_library"

    cq.message.edit_text("نام کتابخانه را بفرست")

@app.on_message(filters.private)
def handle_message(client, message):

if message.from_user.id != OWNER_ID:
    return

state = user_state.get(message.from_user.id)

if state == "await_code":

    if message.document:

        file_name = message.document.file_name

        file_path = message.download(file_name)

        code_id = generate_code_id()

        execute_code(file_path, code_id)

        message.reply_text(
            f"کد اجرا شد\nکد شخصی: {code_id}"
        )

    user_state.pop(message.from_user.id)

elif state == "await_library":

    install_library(message.text.strip())

    message.reply_text("کتابخانه نصب شد")

    user_state.pop(message.from_user.id)

app.run()
