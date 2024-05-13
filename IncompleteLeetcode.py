import requests 
import json
import telegram
import asyncio
from datetime import datetime, date
from dotenv import load_dotenv
import os

load_dotenv()

bot = telegram.Bot(token=os.getenv('TELEBOT_TOKEN'))
bbcgrpID = os.getenv('BBC_GRP_ID')
testgrpID = os.getenv('TEST_GRP_ID')

users = os.getenv('USERS')

current_date = date.today()
str_current_date = str(current_date)
formatted_date = current_date.strftime("%d/%m/%Y")

async def updateTeleChannel(text):
    await bot.send_message(chat_id=bbcgrpID, text = text)

tele_incomplete_message = formatted_date + '\n' + 'Reminder to complete atleast 2 questions before the day ends!'+ '\n\n'; 

for user in users : 
    completedQuestions = []
    # print(len(completedQuestions))

    acceptedSubmissions = requests.get(f"https://alfa-leetcode-api.onrender.com/{user['leetcode']}/acSubmission") # should be in .env
    data_dict = json.loads(acceptedSubmissions.text)

    for submission in data_dict['submission']:

        timestamp = int(submission['timestamp'])
        date_time_accepted = datetime.fromtimestamp(timestamp)
        date_accepted = str(date_time_accepted.date())

        if date_accepted == str_current_date:
            # print(submission['title'])
            completedQuestions.append(submission['title'])

    # print(len(completedQuestions))
    if len(completedQuestions) < 2:
        
        tele_incomplete_message += user['tele'] + '\n'

    completedQuestions = []

asyncio.run(updateTeleChannel(tele_incomplete_message))
