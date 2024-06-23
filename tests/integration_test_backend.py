import unittest
import uuid
import os,sys

sys.path.append(os.path.abspath('bot'))

from backend import (
    insert_user,
    insert_user_submission,
    insert_user_group,
    check_user_leetcode_exists,
    check_user_tele_exists,
    supabase
)

class TestSupabaseFunctionsIntegration(unittest.TestCase):
    def setUp(self):
        # Clear the test data before each test
        supabase.table('User').delete().neq('tele_id', str(uuid.uuid4())).execute()
        supabase.table('User_Submissions').delete().neq('leetcode_username', 'dummy').execute()
        supabase.table('Group_Users').delete().neq('user_tele_id', str(uuid.uuid4())).execute()

    def test_insert_new_user(self):
        tele_id = str(uuid.uuid4())
        username = "testuser"
        leetcode_username = "leetcodeuser"

        result = insert_user(tele_id, username, leetcode_username)

        # Check if the user was inserted correctly
        user_data = supabase.table('User').select('*').eq('tele_id', tele_id).execute()
        self.assertEqual(len(user_data.data), 1)
        self.assertEqual(user_data.data[0]['tele_id'], tele_id)
        self.assertEqual(user_data.data[0]['username'], username)
        self.assertEqual(user_data.data[0]['leetcode_username'], leetcode_username)

    def test_insert_existing_user(self):
        tele_id = str(uuid.uuid4())
        username = "testuser"
        leetcode_username = "leetcodeuser"

        insert_user(tele_id, username, leetcode_username)

        with self.assertRaises(ValueError):
            insert_user(tele_id, username, leetcode_username)

    def test_insert_user_submission(self):
        # First, insert a user
        tele_id = str(uuid.uuid4())
        username = "testuser"
        leetcode_username = "leetcodeuser"
        insert_user(tele_id, username, leetcode_username)

        question_title = "Test Question"
        submission_timestamp = "2023-06-23T12:00:00"

        result = insert_user_submission(leetcode_username, question_title, submission_timestamp)

        # Check if the submission was inserted correctly
        submission_data = supabase.table('User_Submissions').select('*').eq('leetcode_username', leetcode_username).execute()
        self.assertEqual(len(submission_data.data), 1)
        self.assertEqual(submission_data.data[0]['leetcode_username'], leetcode_username)
        self.assertEqual(submission_data.data[0]['question_title'], question_title)
        self.assertEqual(submission_data.data[0]['submission_timestamp'], submission_timestamp)

    def test_insert_user_group(self):
        # First, insert a user
        tele_id = str(uuid.uuid4())
        username = "testuser"
        leetcode_username = "leetcodeuser"
        insert_user(tele_id, username, leetcode_username)

        group_id = str(uuid.uuid4())

        result = insert_user_group(tele_id, group_id)

        # Check if the user-group relation was inserted correctly
        group_data = supabase.table('Group_Users').select('*').eq('user_tele_id', tele_id).execute()
        self.assertEqual(len(group_data.data), 1)
        self.assertEqual(group_data.data[0]['user_tele_id'], tele_id)
        self.assertEqual(group_data.data[0]['group_id'], group_id)

    def test_check_user_leetcode_exists(self):
        # First, insert a user
        tele_id = str(uuid.uuid4())
        username = "testuser"
        leetcode_username = "leetcodeuser"
        insert_user(tele_id, username, leetcode_username)

        # Check if the user exists
        result = check_user_leetcode_exists(leetcode_username)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['leetcode_username'], leetcode_username)

    def test_check_user_tele_exists(self):
        # First, insert a user
        tele_id = str(uuid.uuid4())
        username = "testuser"
        leetcode_username = "leetcodeuser"
        insert_user(tele_id, username, leetcode_username)

        # Check if the user exists
        result = check_user_tele_exists(tele_id)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['tele_id'], tele_id)

    def test_insert_user_submission_non_existent_user(self):
        with self.assertRaises(ValueError):
            insert_user_submission(str(uuid.uuid4()), "Test Question", "2023-06-23T12:00:00+00:00")

    def test_insert_user_group_non_existent_user(self):
        with self.assertRaises(ValueError):
            insert_user_group(str(uuid.uuid4()), "testgroup123")

if __name__ == '__main__':
    unittest.main()