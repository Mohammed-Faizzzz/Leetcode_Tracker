from datetime import datetime

#api call returns unix timestamp
#method to convert the api timestamp to a format accepted by postgresql
def unix_to_postgres(unix_timestamp):
    dt = datetime.fromtimestamp(unix_timestamp)

    postgres_timestamp = dt.strftime('%Y-%m-%dT%H:%M:%S')

    return postgres_timestamp

def get_date_from_db(date_time):
    dt = datetime.strptime(date_time, '%Y-%m-%dT%H:%M:%S')
    formatted_date = dt.strftime('%d %b %Y')

    return formatted_date

def get_time_from_db(date_time):
    dt = datetime.strptime(date_time, '%Y-%m-%dT%H:%M:%S')
    formatted_time = dt.strftime('%H:%M:%S')

    return formatted_time
