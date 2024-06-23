import unittest
import sys, os
 
sys.path.append(os.path.abspath('utils'))

from backend_utils import (
    get_date_from_db,
    get_time_from_db,
    unix_to_postgres
)
class TestDateTimeFunctions(unittest.TestCase):

    def test_unix_to_postgres(self):
        # Test case 1: Unix timestamp for a specific date and time
        unix_timestamp = 1718971616
        expected_postgres_timestamp = '2024-06-21T20:06:56'
        self.assertEqual(unix_to_postgres(unix_timestamp), expected_postgres_timestamp)

        # Test case 2: Another Unix timestamp
        unix_timestamp = 1624370400
        expected_postgres_timestamp = '2021-06-22T22:00:00'
        self.assertEqual(unix_to_postgres(unix_timestamp), expected_postgres_timestamp)

        # Test case 3: Edge case with the Unix epoch (1970-01-01T00:00:00)
        unix_timestamp = 0
        expected_postgres_timestamp = '1970-01-01T08:00:00'
        self.assertEqual(unix_to_postgres(unix_timestamp), expected_postgres_timestamp)

        # Test case 4: Future Unix timestamp
        unix_timestamp = 2000000000
        expected_postgres_timestamp = '2033-05-18T11:33:20'
        self.assertEqual(unix_to_postgres(unix_timestamp), expected_postgres_timestamp)

        # Test case 5: Unix timestamp with milliseconds (truncate milliseconds)
        unix_timestamp = 1624370400.123456
        expected_postgres_timestamp = '2021-06-22T22:00:00'
        self.assertEqual(unix_to_postgres(unix_timestamp), expected_postgres_timestamp)
    
    def test_get_date_from_db(self):
        # Test case 1: Valid PostgreSQL timestamp
        postgres_timestamp = '2023-06-22T19:10:25'
        expected_date = '22 Jun 2023'
        self.assertEqual(get_date_from_db(postgres_timestamp), expected_date)

        # Test case 2: Another valid PostgreSQL timestamp
        postgres_timestamp = '2024-01-15T08:45:00'
        expected_date = '15 Jan 2024'
        self.assertEqual(get_date_from_db(postgres_timestamp), expected_date)

        # Test case 3: Edge case with minimal timestamp
        postgres_timestamp = '2000-01-01T00:00:00'
        expected_date = '01 Jan 2000'
        self.assertEqual(get_date_from_db(postgres_timestamp), expected_date)

        # Test case 4: Leap year timestamp
        postgres_timestamp = '2020-02-29T12:00:00'
        expected_date = '29 Feb 2020'
        self.assertEqual(get_date_from_db(postgres_timestamp), expected_date)

        # Test case 5: Future timestamp
        postgres_timestamp = '2050-12-31T23:59:59'
        expected_date = '31 Dec 2050'
        self.assertEqual(get_date_from_db(postgres_timestamp), expected_date)

    def test_get_time_from_db(self):
        # Test case 1: Valid PostgreSQL timestamp
        postgres_timestamp = '2023-06-22T19:10:25'
        expected_time = '19:10:25'
        self.assertEqual(get_time_from_db(postgres_timestamp), expected_time)

        # Test case 2: Another valid PostgreSQL timestamp
        postgres_timestamp = '2024-01-15T08:45:00'
        expected_time = '08:45:00'
        self.assertEqual(get_time_from_db(postgres_timestamp), expected_time)

        # Test case 3: Edge case with midnight timestamp
        postgres_timestamp = '2000-01-01T00:00:00'
        expected_time = '00:00:00'
        self.assertEqual(get_time_from_db(postgres_timestamp), expected_time)

        # Test case 4: Seconds only timestamp
        postgres_timestamp = '2021-12-31T23:59:59'
        expected_time = '23:59:59'
        self.assertEqual(get_time_from_db(postgres_timestamp), expected_time)

        # Test case 5: Time with leading zero in hours
        postgres_timestamp = '2025-05-10T08:30:45'
        expected_time = '08:30:45'
        self.assertEqual(get_time_from_db(postgres_timestamp), expected_time)

if __name__ == '__main__':
    unittest.main()

