import requests 
import json
import telegram
import asyncio
from datetime import datetime, date, timedelta
from dotenv import load_dotenv
from pytz import timezone
import os

load_dotenv()

bot = telegram.Bot(token=os.getenv('TELEBOT_TOKEN'))
bbcgrpID_json = os.getenv('BBC_GRP_ID')
testgrpID_json = os.getenv('TEST_GRP_ID')
bbcgrpID = json.loads(bbcgrpID_json)
testgrpID = json.loads(testgrpID_json)

users_json = os.getenv('USERS')
users = json.loads(users_json)

sgt = timezone('Asia/Singapore')

# Get the current date and time in your timezone
now = datetime.now(sgt)

current_date = now.date() - timedelta(days=1)
str_current_date = str(current_date)
formatted_date = current_date.strftime("%d/%m/%Y")

async def updateTeleChannel(text):
    print("running inside")
    await bot.send_message(chat_id=bbcgrpID, text = text)

# def updateGoogleSheet(str_current_date, completedQuestions):
#     # You can implement the logic to update the Google Sheet here
#     print("Updating Google Sheet for date:", str_current_date)
#     for question in completedQuestions:
#         print("Adding question to Google Sheet:", question)

tele_completed_message = formatted_date + '\n' + 'Congrats on completing atleast 2 questions today!' + '\n\n';

print("running")
for user in users : 
    # print (user['leetcode'])
    completedQuestions = []

    acceptedSubmissions = requests.get(f"https://alfa-leetcode-api.onrender.com/{user['leetcode']}/acSubmission")
    data_dict = json.loads(acceptedSubmissions.text)

    for submission in data_dict['submission']:
        
        timestamp = int(submission['timestamp'])
        date_time_accepted = datetime.fromtimestamp(timestamp)
        date_accepted = str(date_time_accepted.date())

        if date_accepted == str_current_date:
            # print(submission)
            completedQuestions.append(submission['title'])

    if len(completedQuestions) >=2 :
        # print(len(completedQuestions))
        joined_questions = "\n".join(completedQuestions)
        tele_completed_message += user['tele'] + '\n' + joined_questions+ '\n\n'

    completedQuestions = []

asyncio.run(updateTeleChannel(tele_completed_message))
# updateGoogleSheet(str_current_date, completedQuestions)
