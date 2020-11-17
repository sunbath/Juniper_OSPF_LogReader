# Author: Eric Leung
# Last Modified: 1-Feb-2019
# Function:
# To analyze the ospf log collected from "show log | in ospf"
# Output:
# A list of downtime will be shown based on the ospf neighbor IP
# downtime will be shown for each incident

import re
import datetime
import pytz
import os
from pprint import pprint

def logfile_reader(filename, bad_word_list):
    log_list = []
    with open(filename) as f:
        for line in f:
            log_list.append(line.lower())
    f.close()
    log_list = log_cleaner(log_list, bad_word_list)
    return log_list

def log_cleaner(log_lines, bad_word_list):
    clean_log_lines = []
    dirty_log_lines = []
    bad_word_list = [x.lower() for x in bad_word_list]

    for line in log_lines:
        if not any(bad_word in line for bad_word in bad_word_list):
            if len(line.strip()) > 0:
                clean_log_lines.append(line.strip())
        else:
            dirty_log_lines.append(line)
    return clean_log_lines

def junos_ospf_log_reader(log_lines):
    #   Convert the log lines into easier managable data structure.
    #   E.g.
    #   'jan  5 11:48:14.571  jkf-mayb-switch1 rpd[1307]: rpd_ospf_nbrdown: ospf neighbor 10.132.43.105 (realm ospf-v2 vlan.514 area 0.0.0.0) state changed from full to init due to 1wayrcvd (event reason: neighbor is in one-way mode)'
    #
    #   Useful Information:
    #   Timestamp:  jan  5 11:48:14.571
    #   Hostname:   jkf-mayb-switch1
    #   Status:     full to init
    #   NeighborIP: 10.132.43.105 (key)
    #   Interface   vlan.514

    #   log_item: [timestamp,status,hostname,interface]
    #   Data Structure:
    #   {NeighborIP1 : [log_item_1,log_item_2....], NeighborIP2: [log_item_1,log_item_2....] ... }

    log_dict = {}
    for line in log_lines:
        neighborIP = ""
        timestamp = ""
        status = ""
        hostname = ""
        interface = ""

        # print(line)

        neighborIP = (line.split("nbr")[1]).split(" on")[0].strip()
        #print(neighborIP)

        timestamp_regex = r'[a-z][a-z][a-z]\s.\d\s[0-2][0-9]:[0-5][0-9]:[0-5][0-9].[0-9]{3}'
        raw_timestamp = re.findall(timestamp_regex, line)[0]
        #print(raw_timestamp)

        hostname = "fnlr-sg1-bursa2"
        #print(hostname)

        timestamp = raw_timestamp[4:6].strip()+"-"+raw_timestamp[0:3].capitalize()+" "+raw_timestamp[7:]

        location = 'sg'

        time_object = str_to_time(timestamp, location)
        #print(time_object)

        interface = (line.split("on ")[1]).split("from")[0].strip()
        #print(interface)

        statusword = line.split("from ")
        # print(statusword)
        if re.search(r'\bfull to \b', statusword[1]):
            status = "DOWN"
        elif re.search(r'\bto full\b', statusword[1]):
            status = "UP"
        else:
            continue
        #print(status)

        log_item = [time_object, status, hostname, interface]
        log_dict.setdefault(neighborIP, []).append(log_item)
    # pprint.pprint(log_dict)
    return log_dict

def neighbor_date_stat(log_dict):

    neighbor_date_stat_dict = {}

    for log_entries in log_dict.items():

        date_dict = {}
        #print(log_entries[0])

        for event in log_entries[1]:
            date = event[0].date()
            date_dict.setdefault(date,0)
            status = event[1]
            if status == "DOWN":
                date_dict[date] += 1
        #print(date_dict)
        neighbor_date_stat_dict[log_entries[0]] = date_dict
    #print(neighbor_date_stat_dict)
    return neighbor_date_stat_dict

def neighbor_date_total_stat(neighbor_date_stat_dict):

    neighbor_date_total_stat_dict = {}

    for key in neighbor_date_stat_dict:
        neighbor_date_total_stat_dict[key] = sum(neighbor_date_stat_dict[key].values())

    return neighbor_date_total_stat_dict

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

def utc_to_localtime(timeobject,timezone_str):
    hk = pytz.timezone('Asia/Hong_Kong')
    sg = pytz.timezone('Asia/Singapore')
    bk = pytz.timezone('Asia/Bangkok')
    jk = pytz.timezone('Asia/Jakarta')
    mu = pytz.timezone('Etc/GMT+10')
    utc = pytz.utc

    timezone_dict = {'hk': hk, 'sg': sg, 'bk': bk, 'jk': jk, "mu": mu, 'utc': utc}

    sourcetimezone = [value for (key, value) in timezone_dict.items() if key == timezone_str.lower()][0]

    date_time_obj = timeobject.astimezone(sourcetimezone)

    return date_time_obj

def neighbor_downtime_stat(log_dict):
    # This function is to calculate the downtime of each incident

    # Initialize a dictionary object to store the calculation result
    # {"neighborIP" : {"timestamp" : downtime }
    neighbor_downtime_stat_dict = {}

    # Iterate the log entries from the given input log_dict
    for log_entries in log_dict.items():

        downtime_dict = {}
        #print(log_entries[0])

        first_event = True
        previous_event_status = ""
        for event in log_entries[1]:
            timestamp = event[0]
            downtime_dict.setdefault(timestamp,0)
            status = event[1]

            # if the event is a down event, the timestamp is the incident start time
            if status == "DOWN":
                downtime_dict[timestamp] = 0
                start_time = timestamp
                previous_event_status = status
            # if the event is a up event, the timestamp is the incident end time
            # downtime = end time - start time
            elif status == "UP" and not first_event and previous_event_status == "DOWN":
                downtime_dict[timestamp] = timestamp - start_time
                previous_event_status = status
            first_event = False
            print(previous_event_status)
        #print(date_dict)
        neighbor_downtime_stat_dict[log_entries[0]] = downtime_dict
    #pprint(neighbor_downtime_stat_dict)
    return neighbor_downtime_stat_dict

def location_determinator(hostname):
    # To determine the location of the log based on the device hostname
    # A two-character location abbreviation will be returned.
    if "hk" in hostname:
        location = "hk"
    elif "jk" in hostname:
        location = "jk"
    elif ("bk" in hostname) or ("-bk" in hostname):
        location = "bk"
    elif ("sg" in hostname) or ("-sg" in hostname):
        location = "sg"
    elif "-mu" in hostname:
        location = "mu"
    elif ("au" in hostname) or ("-sy" in hostname):
        location = "sy"

    return location

def print_output(ospf_log_dict,neighbor_date_stat_dict,neighbor_date_total_stat_dict,neighbor_downtime_stat_dict):
    now = datetime.datetime.now()
    for neighborIP, log_lines in ospf_log_dict.items():
        hostname = log_lines[0][2]
        continue

    print(f"OSPF Log Analysis for {hostname} \n")
    print(f"Creation time: {now}\n")

    for neighborIP, log_lines in ospf_log_dict.items():
        interface = log_lines[0][3]
        print(f"OSPF Neighbor IP: {neighborIP} \tInterface: {interface}")
        print(f"=" * 90)
        print(f"Timestamp \t\t\t\t\t\t\t\t\t Status \t\t Downtime")
        print(f"=" * 90)

        for log in log_lines:
            timestamp   = log[0]
            status      = log[1]
            hostname     = log[2]
            location    = location_determinator(hostname)
            interface   = log[3]
            downtime    = neighbor_downtime_stat_dict[neighborIP][timestamp]

            formatted_timestamp = utc_to_localtime(timestamp,location).strftime('%Y-%m-%d %H:%M:%S.%f %z')

            if downtime == 0:
                print(f"{formatted_timestamp} \t\t\t {status}")
            else:
                print(f"{formatted_timestamp} \t\t\t {status}  \t\t\t ({downtime})")

        print(f"=" *90)

        print(f"Number of Downtime Incidents")
        print(f"=" * 90)
        for date, downtime in neighbor_date_stat_dict[neighborIP].items():
            print(f"{date}: {downtime}")
        print(f"-" * 90)
        print(f"Total: {neighbor_date_total_stat_dict[neighborIP]}")
        print(f"\n")

def file_output(ospf_log_dict,neighbor_date_stat_dict,neighbor_date_total_stat_dict,neighbor_downtime_stat_dict,filename):
    now = datetime.datetime.now()

    filename = filename.split(".txt")[0]+"-"+now.strftime("%Y%m%d-%H%M%S")+".txt"

    if not os.path.exists("log_result"):
        os.makedirs("log_result")

    output_path = "./log_result/"

    wholepath = os.path.join(output_path, filename)

    f = open(wholepath, "w+")

    for neighborIP, log_lines in ospf_log_dict.items():
        hostname = log_lines[0][2]
        continue

    f.write(f"OSPF Log Analysis for {hostname} \n")
    f.write(f"Creation time: {now}\n")
    f.write(f"\n")

    for neighborIP, log_lines in ospf_log_dict.items():
        interface = log_lines[0][3]
        f.write(f"OSPF Neighbor IP: {neighborIP} \tInterface: {interface}\n")
        f.write(f"=" * 90)
        f.write("\n")
        f.write(f"Timestamp \t\t\t\t\t\t\t\t\t Status \t\t Downtime\n")
        f.write(f"=" * 90)
        f.write("\n")

        for log in log_lines:
            timestamp   = log[0]
            status      = log[1]
            hostname     = log[2]
            location    = location_determinator(hostname)
            interface   = log[3]
            downtime    = neighbor_downtime_stat_dict[neighborIP][timestamp]

            formatted_timestamp = utc_to_localtime(timestamp,location).strftime('%Y-%m-%d %H:%M:%S.%f %z')

            if downtime == 0:
                f.write(f"{formatted_timestamp} \t\t\t {status}\n")
            else:
                f.write(f"{formatted_timestamp} \t\t\t {status}  \t\t\t ({downtime})\n")

        f.write(f"=" *90)
        f.write("\n")

        f.write(f"Number of Downtime Incidents\n")
        f.write(f"=" * 90)
        f.write("\n")
        for date, downtime in neighbor_date_stat_dict[neighborIP].items():
            f.write(f"{date}: {downtime}\n")
        f.write(f"-" * 90)
        f.write("\n")
        f.write(f"Total: {neighbor_date_total_stat_dict[neighborIP]}")
        f.write(f"\n")
        f.write(f"\n")
    f.close()

def main():
    bad_word_list = ['UI_CMDLINE_READ_LINE', '---(more', 'master:', '@', 'PuTTY']
    log_lines = logfile_reader("cisco_logfile.txt", bad_word_list)

    ospf_log_dict = junos_ospf_log_reader(log_lines)
    #print(ospf_log_dict)

    neighbor_date_stat_dict = {}
    neighbor_date_stat_dict = neighbor_date_stat(ospf_log_dict)

    #pprint(neighbor_date_stat_dict)
    neighbor_date_total_stat_dict = {}
    neighbor_date_total_stat_dict = neighbor_date_total_stat(neighbor_date_stat_dict)
    #print(neighbor_total_stat_dict)

    neighbor_downtime_stat_dict = neighbor_downtime_stat(ospf_log_dict)
    #pprint(neighbor_downtime_stat_dict)

    print_output(ospf_log_dict,neighbor_date_stat_dict,neighbor_date_total_stat_dict,neighbor_downtime_stat_dict)

    file_output(ospf_log_dict,neighbor_date_stat_dict,neighbor_date_total_stat_dict,neighbor_downtime_stat_dict,"ospf-log.txt")

if __name__ == '__main__':
    main()