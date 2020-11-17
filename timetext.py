import datetime
import pytz

def str_to_time(timestamp_str,timezone_str):
    #timestamp_str example: 5-Jan 11:48:14.571

    hk = pytz.timezone('Asia/Hong_Kong')
    sg = pytz.timezone('Asia/Singapore')
    bk = pytz.timezone('Asia/Bangkok')
    jk = pytz.timezone('Asia/Jakarta')
    mu = pytz.timezone('Etc/GMT+10')
    utc = pytz.utc

    timezone_dict = {'hk': hk, 'sg': sg, 'bk': bk, 'jk': jk, "mu": mu, 'utc': utc}

    sourcetimezone = [value for (key, value) in timezone_dict.items() if key == timezone_str.lower()][0]
    #print(sourcetimezone)

    date_time_obj = datetime.datetime.strptime(timestamp_str, '%d-%b %H:%M:%S.%f')
    date_time_obj = date_time_obj.replace(year=datetime.datetime.now().year)

    # Create the timestamp with the local timezone.
    date_time_obj = sourcetimezone.localize(date_time_obj)

    # Convert the timestamp with UTC time.
    date_time_obj = date_time_obj.astimezone(utc)
    #print(date_time_obj)
    #print('Date:', date_time_obj.date())
    #print('Time:', date_time_obj.time())
    #print('Date-time:', date_time_obj)

    return date_time_obj

def main():
    a = str_to_time("5-Jan 11:48:14.571","UTC")
    b = str_to_time("5-Jan 11:48:27.014","UTC")
    print(f"{a}")
    print(f"{b}")
    print(f"{b-a}")

if __name__ == '__main__':
    main()

