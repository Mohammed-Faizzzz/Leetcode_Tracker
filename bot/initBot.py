import threading
import time
import requests
import telebot
from dotenv import load_dotenv
import os
import schedule
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

from bot.backend import add_user, get_group_members, insert_reminder_timings, get_all_group_ids, get_reminder_timings

load_dotenv()
bot = telebot.TeleBot(os.environ.get('BOT_KEY'))

# API for leetcode
leet_api = 'https://alfa-leetcode-api.onrender.com/'


# --------------------------------- Call Init to Get the Group ID for Auto Reminders --------------------------------

@bot.message_handler(commands=['start'])
def init(message):
    group_id = message.chat.id
    bot_id = bot.get_me().id

    print(f'group_id : {group_id} bot_id : {bot_id}')

    # Once done, send a welcome message
    bot.reply_to(message, "Hello everyone! I'm your LeetCode tracker bot, and I'm here to help you track your progress.\n \nTo get started, please register by sending a message in this format:\n '/add your_leetcode_username'.\n \n Looking forward to assisting you on your coding journey!")


# ------------------------------------------ Add Leetcode Username to DB --------------------------------------------

@bot.message_handler(commands=['add'])
def register_lc_username(message):
    if message.chat.type == 'private':
        bot.reply_to(message, 'Please add me to a group !')
    else:
        username = message.from_user.username
        tele_id = message.from_user.id
        group_id = message.chat.id

        command_lc_username = message.text.split()

        if len(command_lc_username) > 1:
            leetcode_username = command_lc_username[1].lower()
            print(f'User : {tele_id}, Group: {group_id}, lc_username: {leetcode_username}')

            # Here need to verify if the username is accurate
            try:
                res = requests.get(leet_api + leetcode_username)

                if res.status_code == 200:
                    res_json = res.json()
                    print(res_json)
                    if 'errors' in res_json:
                        bot.reply_to(message, 'User does not exist !')
                    else:
                        # Here we will add the lc username to the user if not and link this user to the current group
                        add_user(username=username, leetcode_username=leetcode_username, group_id=group_id, tele_id=tele_id)
                        bot.reply_to(message, "Success")
                else:
                    bot.reply_to(message, "Error has occured")
            except requests.RequestException as e:
                print(f'Error : {e}')
                bot.reply_to(message, "Error has occured")

# ---------------------------------------------- Reminder Timing Form ------------------------------------------------


form_states = {}


# Builds the inline keyboard for user to select the timings
def build_keyboard(timings, chosen_timings, columns=3):
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
    group_id = message.chat.id

    # set the state of the current group to be form active
    if group_id not in form_states:
        form_states[group_id] = {
            'form_active': False,
            'message_id': None,
            'chosen_timings': []
        }

    if not form_states[group_id]['form_active'] and message.chat.type == 'group':
        form_states[group_id]['form_active'] = True
        timings = [f"{i:02d}:00" for i in range(24)]

        keyboard = build_keyboard(timings, form_states[group_id]['chosen_timings'])
        msg = bot.send_message(message.chat.id, 'Choose the timings for me to remind you all !', reply_markup=keyboard)
        form_states[group_id]['message_id'] = msg.message_id
    else:
        bot.send_message(message.chat.id, 'Reminder timing selection is already active.')


@bot.callback_query_handler(func=lambda call: call.data.startswith("reminder_timing_entry_"))
def handle_reminder_time_selection(call):
    group_id = call.message.chat.id
    res = call.data.split("_")[-1]

    chosen_timings = form_states[group_id]['chosen_timings']

    if not form_states[group_id]['form_active']:
        return

    if res == 'confirm':
        form_states[group_id]['form_active'] = False
        bot.send_message(call.message.chat.id, f'Confirmed timings: {chosen_timings}')

        if len(chosen_timings) == 0:
            bot.send_message(call.message.chat.id, f'You have not chosen any reminder timeslots !')
            return

        # Upsert into the DB
        insert_reminder_timings(group_id, chosen_timings)

        # Clear chosen timings after confirmation
        form_states[group_id]['chosen_timings'].clear()

        # Delete message
        bot.delete_message(group_id, form_states[group_id]['message_id'])

        bot.answer_callback_query(call.id, "Form closed")
    else:
        if res in chosen_timings:
            form_states[group_id]['chosen_timings'].remove(res)
        else:
            form_states[group_id]['chosen_timings'].append(res)

        # Update inline keyboard with updated selection
        timings = [f"{i:02d}:00" for i in range(24)]
        keyboard = build_keyboard(timings, form_states[group_id]['chosen_timings'])
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=keyboard)
        bot.answer_callback_query(call.id, f"Selected {res}")


# ---------------------------------------------- Auto Reminders -------------------------------------------------------

# First we get all the group_ids and their respective time slots
# After which, iterate through each group and set their reminders

group_reminder_dict = {}


def fetch_timings_of_groups():
    # Clear the current dict
    group_reminder_dict.clear()

    # Get all group ids
    all_group_ids = get_all_group_ids()

    for gid in all_group_ids:
        timings = get_reminder_timings(gid)
        group_reminder_dict[gid] = timings


def update_schedule_reminders():
    # Schedule reminders to run at chosen timings & call this function at every 20 minutes
    fetch_timings_of_groups()
    for group_id in group_reminder_dict:
        timings = group_reminder_dict[group_id]

        for timing in timings:
            schedule.every().day.at(timing).do(remind_members, group_id=group_id)


# Schedule the update to run every 45 minutes past the hour
def schedule_45_minutes_past_hour():
    # Define the time to run (e.g., '00:45', '01:45', '02:45', etc.)
    for hour in range(24):
        time_str = f"{hour:02d}:45"
        schedule.every().day.at(time_str).do(update_schedule_reminders)

def has_completed_daily_task(leetcode_username):
    # Based on leetcode_username -> fetch and verify they have completed at least 2 questions
    return True


def remind_members(group_id):
    members = get_group_members(group_id)

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


# Init calls
update_schedule_reminders()
schedule_45_minutes_past_hour()

# For testing scheduling -> hardcode the time and run the bot
schedule.every().day.at("20:14").do(remind_members, group_id=-4258400247)
schedule.every().day.at("20:15").do(remind_members, group_id=-4258400247)


def run_scheduler():
    while True:
        schedule.run_pending()
        time.sleep(1)


scheduler_thread = threading.Thread(target=run_scheduler)
scheduler_thread.start()

# --------------------------------------------------------- Infinity Polling -------------------------------------------

bot.infinity_polling()
