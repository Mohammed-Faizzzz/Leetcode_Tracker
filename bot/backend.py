import os
from dotenv import load_dotenv
import requests
from supabase import create_client, Client

load_dotenv()
url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)


# add try catch statements
def insert_user(tele_id, username, leetcode_username):
    # Upsert will insert if entry does not exist
    try:
        data, count = supabase.table('User').upsert(
            {"tele_id": tele_id, "username": username, "leetcode_username": leetcode_username}).execute()
        return data
    except requests.RequestException as e:
        print(f'Error : {e}')


def insert_user_submission(leetcode_username, question_title, submission_timestamp):
    
    user_data = check_user_leetcode_exists(leetcode_username)

    if len(user_data) == 0:
        raise ValueError(f"User with leetcode username '{leetcode_username}' does not exist")

    data, count = supabase.table('User_Submissions').insert({
        "leetcode_username": leetcode_username,
        "question_title": question_title,
        # need to check/change the timezone of the submission
        "submission_timestamp": submission_timestamp
    }).execute()

    return data

def insert_user_group(tele_id, group_id):

    user_data = check_user_tele_exists(tele_id)

    if len(user_data) == 0:
        raise ValueError(f"User with tele id '{tele_id}' does not exist")
    
    data, count = supabase.table('Group_Users').insert({"user_tele_id":tele_id, "group_id":group_id}).execute()
    return data

def check_user_leetcode_exists(leetcode_username):
# Check if the leetcode_username exists in the User table
    response = supabase.table('User').select('*').eq('leetcode_username', leetcode_username).execute()
    return response.data

def check_user_tele_exists(tele_id):
# Check if the leetcode_username exists in the User table
    response= supabase.table('User').select('*').eq('tele_id', tele_id).execute()
    return response.data


def insert_group(group_id, bot_id):
    try:
        supabase.table('Group').upsert({
            "group_id": group_id,
            "bot_id": bot_id
        }).execute()
    except requests.RequestException as e:
        print(f'Error : {e}')


def add_user(username, tele_id, leetcode_username, group_id):
    try:
        insert_user(tele_id, username, leetcode_username)
        insert_user_group(tele_id, group_id)
    except requests.RequestException as e:
        print(f'Error : {e}')


def get_group_id(bot_id):
    try:
        res = supabase.table('Group').select('*').eq('bot_id', bot_id).execute()
        if len(res.data) == 0:
            # Group not added
            return None
        else:
            return res.data[0]['group_id']
    except requests.RequestException as e:
        print(f'Error : {e}')


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