import threading
import time

import requests
import telebot
from dotenv import load_dotenv
import os
import schedule

from tb_forms import TelebotForms, BaseForm, fields

load_dotenv()
bot = telebot.TeleBot(os.environ.get('BOT_KEY'))
tbf = TelebotForms(bot)

# Fetch group id from database for current bot id if present else None
group_id = None

# Fetch group members based on current group_id
members = []

# API for leetcode
leet_api = 'https://alfa-leetcode-api.onrender.com/'


# -------------------------------------- ADD LEETCODE USERNAME TO THE DATABASE --------------------------------------

class LeetcodeRegisterForm(BaseForm):
    update_name = 'leetcode_register_form'
    form_title = 'Leetcode Register Form'
    freeze_mode = True
    close_form_but = False
    default_step_by_step = True
    submit_button_text = 'Confirm'
    canceled_text = 'Cancel'

    leetcode_username = fields.StrField("Leetcode username", "Enter your leetcode username")


@bot.message_handler(commands=['register_leetcode_username'])
def register_leetcode_username(message):
    if message.chat.type == 'group':
        bot.reply_to(message, "Please PM me to add your leetcode profile !!")
    else:
        form = LeetcodeRegisterForm()
        tbf.send_form(message.chat.id, form)


@tbf.form_submit_event('leetcode_register_form')
def register_leetcode_username(call, form_data):

    user_id = call.from_user.id
    leetcode_username = form_data.leetcode_username

    print(f'User {user_id} : {leetcode_username}')

    # Here need to verify if the username is accurate
    try:
        res = requests.get(leet_api + leetcode_username.lower())

        if res.status_code == 200:
            res_json = res.json()
            print(res_json)
            if res_json['errors']:
                bot.send_message(call.message.chat.id, 'User does not exist !')
            else:
                bot.send_message(call.message.chat.id, "Success")
        else:
            bot.send_message(call.message.chat.id, "Error has occured")
    except requests.RequestException as e:
        print(f'Error : {e}')
        bot.send_message(call.message.chat.id, "Error has occured")


@bot.message_handler(commands=['add_me'])
def add_me(message):
    if message.chat.type == 'private':
        bot.reply_to(message, 'Please call this command in a group to add yourself in our tracker for that group !!')
    else:
        user_id = message.from_user.id
        # Take note that chat id will be negative for groups !
        print(f'user : {user_id} wants to be added to group {message.chat.id}')


# ---------------------------------------------- Auto Reminders -------------------------------------------------------


def has_completed_daily_task(leetcode_username):
    # Based on leetcode_username -> fetch and verify they have completed at least 2 questions
    return False


def remind_members():
    global group_id

    if group_id and members:
        reminder_message = "Reminder to complete at least 2 questions before the day ends! "

        for member in members:
            try:
                if has_completed_daily_task(member.leetcode_username):
                    reminder_message += '\n' + f'@{member.username}'
            except telebot.apihelper.ApiTelegramException as e:
                print(f"Failed to mention user {member.name}: {e}")

        bot.send_message(group_id, reminder_message)
    else:
        print('Group ID not set or no members to mention')


# Schedule reminders to run at 09:00, 18:00, 23:00
schedule.every().day.at("09:00").do(remind_members)
schedule.every().day.at("18:00").do(remind_members)
schedule.every().day.at("23:00").do(remind_members)


def run_scheduler():
    while True:
        schedule.run_pending()
        time.sleep(1)


scheduler_thread = threading.Thread(target=run_scheduler)
scheduler_thread.start()

# --------------------------------------------------------- Infinity Polling -------------------------------------------

bot.infinity_polling()
