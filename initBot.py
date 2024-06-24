import threading
import time
import requests
import telebot
from dotenv import load_dotenv
import os
import schedule
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from supabase import create_client, Client

load_dotenv()
bot = telebot.TeleBot(os.environ.get('BOT_KEY'))

url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)

# API for leetcode
leet_api = 'https://alfa-leetcode-api.onrender.com/'

# Timings for reminders to be sent at
chosen_timings = []

# ---------------------------------- Misc API Fetches ---------------------------------------------------------------


def get_group_id():
    try:
        bot_id = bot.get_me().id
        res = supabase.table('Group').select('*').eq('bot_id', bot_id).execute()
        if len(res.data) == 0:
            # Group not added
            return None
        else:
            return res.data[0]['group_id']
    except requests.RequestException as e:
        print(f'Error : {e}')


# Fetch group id from database for current bot id if present else None
group_id = get_group_id()


def get_group_members(group_id):
    # Get all the user_ids of current group
    users = []
    try:
        res = supabase.table('Group_Users').select('User!inner(tele_id, username, leetcode_username)').eq('group_id', group_id).execute()

        if len(res.data) == 0:
            return []
        else:
            for user_data in res.data:
                users.append(user_data["User"])

            return users

    except requests.RequestException as e:
        print(f'Error : {e}')


# Fetch group members based on current group_id
members = get_group_members(group_id)
print(f'Members of the group : {members}')
get_group_members(group_id)


# --------------------------------- Call Init to Get the Group ID for Auto Reminders --------------------------------

@bot.message_handler(commands=['start'])
def init(message):

    if message.chat.type == 'private':
        bot.reply_to(message, 'Please call this command in a group !!')
        return

    global group_id
    group_id = message.chat.id
    bot_id = bot.get_me().id

    print(f'group_id : {group_id} bot_id : {bot_id}')

    # API POST to DB
    create_group(group_id, bot_id)

    # Once done, send a welcome message
    bot.reply_to(message, "Hello everyone! I'm your LeetCode tracker bot, and I'm here to help you track your progress.\n \nTo get started, please register by sending a message in this format:\n '/add your_leetcode_username'.\n \n Looking forward to assisting you on your coding journey!")


def create_group(group_id, bot_id):
    try:
        data, count = supabase.table('Group').upsert({
            "group_id": group_id,
            "bot_id": bot_id
        }).execute()

        print(data)
    except requests.RequestException as e:
        print(f'Error : {e}')

# ------------------------------------------ Add Leetcode Username to DB --------------------------------------------


@bot.message_handler(commands=['add'])
def register_lc_username(message):
    if message.chat.type == 'private':
        bot.reply_to(message, 'Please add me to a group !')
    else:
        user_id = message.from_user.id
        username = message.from_user.username
        group_id = message.chat.id

        command_lc_username = message.text.split()

        if len(command_lc_username) > 1:
            leetcode_username = command_lc_username[1].lower()

            # Here need to verify if the username is accurate
            try:
                res = requests.get(leet_api + leetcode_username)

                if res.status_code == 200:
                    res_json = res.json()
                    if 'errors' in res_json:
                        bot.reply_to(message, 'User does not exist !')
                    else:
                        # Here we will add the lc username to the user if not and link this user to the current group

                        create_user(username=username, user_id=user_id, leetcode_username=leetcode_username, group_id=group_id)

                        bot.reply_to(message, "Success")
                else:
                    bot.reply_to(message, "Error has occured")
            except requests.RequestException as e:
                print(f'Error : {e}')
                bot.reply_to(message, "Error has occured")


def create_user(leetcode_username, user_id, username, group_id):
    print(f'User : {user_id}, Tele User: {username}, Group: {group_id}, lc_username: {leetcode_username}')
    # First we create the user if not exists
    try:
        supabase.table('User').upsert({
            "tele_id": user_id,
            "username": username,
            'leetcode_username': leetcode_username
        }).execute()
    except requests.RequestException as e:
        print(f'Error : {e}')

    # Now we link the user to the group
    try:
        supabase.table('Group_Users').upsert({
            "user_tele_id": user_id,
            "group_id": group_id
        }).execute()
    except requests.RequestException as e:
        print(f'Error : {e}')

# ---------------------------------------------- Reminder Timing Form ------------------------------------------------


form_active = False


# Builds the inline keyboard for user to select the timings
def build_keyboard(timings, chosen_timings, columns=4):
    keyboard = InlineKeyboardMarkup()
    row = []
    for index, timing in enumerate(timings):
        button_text = f'✅ {timing}' if timing in chosen_timings else timing
        row.append(InlineKeyboardButton(text=button_text, callback_data=f'reminder_timing_entry_{timing}'))
        if (index + 1) % columns == 0:
            keyboard.row(*row)
            row = []
    if row:
        # For any excess buttons we might have
        keyboard.row(*row)
    keyboard.add(InlineKeyboardButton(text='CONFIRM', callback_data='reminder_timing_entry_confirm'))
    return keyboard


@bot.message_handler(commands=['reminder_timings'])
def send_reminder_timing_form(message):
    global form_active
    if not form_active and message.chat.type == 'group':
        form_active = True
        timings = [f"{i:02d}:00" for i in range(24)]

        keyboard = build_keyboard(timings, chosen_timings)
        bot.send_message(message.chat.id, 'Choose the timings for me to remind you all !', reply_markup=keyboard)
    else:
        bot.send_message(message.chat.id, 'Reminder timing selection is already active.')


@bot.callback_query_handler(func=lambda call: call.data.startswith("reminder_timing_entry_"))
def handle_reminder_time_selection(call):
    global form_active
    res = call.data.split("_")[-1]

    if res == 'confirm':
        form_active = False
        bot.send_message(call.message.chat.id, f'Confirmed timings: {chosen_timings}')
        chosen_timings.clear()  # Clear chosen timings after confirmation
        bot.answer_callback_query(call.id, "Form closed")
    else:
        if res in chosen_timings:
            chosen_timings.remove(res)
        else:
            chosen_timings.append(res)

        # Update inline keyboard with updated selection
        timings = [f"{i:02d}:00" for i in range(24)]
        keyboard = build_keyboard(timings, chosen_timings)
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=keyboard)
        bot.answer_callback_query(call.id, f"Selected {res}")

# ---------------------------------------------- Auto Reminders -------------------------------------------------------


def has_completed_daily_task(leetcode_username):
    # Based on leetcode_username -> fetch and verify they have completed at least 2 questions
    return True


def remind_members():
    global group_id
    global members

    if group_id and members:
        reminder_message = "Reminder to complete at least 2 questions before the day ends! "

        for member in members:
            try:
                if has_completed_daily_task(member["leetcode_username"]):
                    reminder_message += '\n' + f'@{member["username"]}'
            except telebot.apihelper.ApiTelegramException as e:
                username = member["username"]
                print(f"Failed to mention user {username}: {e}")

        bot.send_message(group_id, reminder_message)
    else:
        print('Group ID not set or no members to mention')


# Schedule reminders to run at chosen timings
for timing in chosen_timings:
    schedule.every().day.at(timing).do(remind_members)

# For testing scheduling -> hardcode the time and run the bot
schedule.every().day.at("14:01").do(remind_members)


def run_scheduler():
    while True:
        schedule.run_pending()
        time.sleep(1)


scheduler_thread = threading.Thread(target=run_scheduler)
scheduler_thread.start()

# --------------------------------------------------------- Infinity Polling -------------------------------------------

bot.infinity_polling()
