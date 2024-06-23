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


# --------------------------------- Call Init to Get the Group ID for Auto Reminders --------------------------------

@bot.message_handler(commands=['start'])
def init(message):
    global group_id
    group_id = message.chat.id
    bot_id = bot.get_me().id

    print(f'group_id : {group_id} bot_id : {bot_id}')

    # API POST to DB

    # Once done, send a welcome message
    bot.reply_to(message, "Hello everyone! I'm your LeetCode tracker bot, and I'm here to help you track your progress.\n \nTo get started, please register by sending a message in this format:\n '/add your_leetcode_username'.\n \n Looking forward to assisting you on your coding journey!")


# ------------------------------------------ Add Leetcode Username to DB --------------------------------------------

@bot.message_handler(commands=['add'])
def register_lc_username(message):
    if message.chat.type == 'private':
        bot.reply_to(message, 'Please add me to a group !')
    else:
        user_id = message.from_user.id
        group_id = message.chat.id

        command_lc_username = message.text.split()

        if len(command_lc_username) > 1:
            leetcode_username = command_lc_username[1].lower()
            print(f'User : {user_id}, Group: {group_id}, lc_username: {leetcode_username}')

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
                        bot.reply_to(message, "Success")
                else:
                    bot.reply_to(message, "Error has occured")
            except requests.RequestException as e:
                print(f'Error : {e}')
                bot.reply_to(message, "Error has occured")

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
