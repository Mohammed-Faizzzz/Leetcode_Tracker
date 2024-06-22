import threading
import time
import telebot
from dotenv import load_dotenv
import os
import schedule

load_dotenv()
bot = telebot.TeleBot(os.environ.get('BOT_KEY'))

# Fetch group id from database for current bot id if present else None
group_id = None

# Fetch group members based on current group_id
members = []

# --------------------------------------------------------- Initialise -------------------------------------------------

reply_text = "Hello! Reply to this message with your LeetCode username"


@bot.message_handler(commands=['init'])
def initialize(message):
    global group_id

    if message.chat.type == 'private':
        bot.reply_to(message, "Self tracker coming soon, for now add me to a group!")
    else:

        if group_id is None:
            # Store group id of current bot id instance in the database
            group_id = message.chat.id

        sent_message = bot.send_message(message.chat.id, reply_text)
        try:
            bot.pin_chat_message(message.chat.id, sent_message.message_id)
        except telebot.apihelper.ApiTelegramException as e:
            bot.send_message(message.chat.id, "I don't have permission to pin messages. Please ensure I have the 'Pin Messages' permission.")


@bot.message_handler(func=lambda message: message.reply_to_message and reply_text in message.reply_to_message.text)
def get_leetcode_username(message):
    user = message.from_user

    # To be stored in DB : tele id, leetcode username, group id
    telegram_id = user.id
    leetcode_username = message.text
    global group_id

    # Verify if leetcode username exists through api
    print('Verifying username in leetcode')

    # Add to database
    print('Add user to database')

    bot.send_message(message.chat.id,f"Thank you, {user.first_name}! Your LeetCode username {leetcode_username} has been registered.")
    print(f"User {user.id} - {user.username} registered with LeetCode username: {leetcode_username}")


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
