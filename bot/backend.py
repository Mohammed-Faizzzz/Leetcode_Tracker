import os
from supabase import create_client, Client

url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)

# add try catch statements
def insert_user(tele_id, username, leetcode_username):
    user_data = check_user_tele_exists(tele_id)

    if len(user_data) > 0:
        raise ValueError(f"User with tele id '{tele_id}' already exists")
    
    data, count = supabase.table('User').insert({"tele_id":tele_id, "username":username,"leetcode_username":leetcode_username}).execute()
    return data

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
        

