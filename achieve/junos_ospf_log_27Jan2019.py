# Author: Eric Leung
# Last Modified: 23-Jan-2019

import re
import datetime
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

        neighborIP = (line.split("ospf neighbor ")[1]).split(" (realm")[0]
        # print(neighborIP)

        timestamp_regex = r'[a-z][a-z][a-z]\s.\d\s[0-2][0-9]:[0-5][0-9]:[0-5][0-9].[0-9]{3}'
        raw_timestamp = re.findall(timestamp_regex, line)[0]
        timestamp = raw_timestamp[4:6].strip()+"-"+raw_timestamp[0:3].capitalize()+" "+raw_timestamp[7:]
        #print(timestamp)

        hostname = line.split(raw_timestamp)[1].split("rpd[")[0].strip()
        # print(hostname)

        interface = (line.split("ospf-v2 ")[1]).split("area")[0].strip()
        # print(interface)

        statusword = line.split("state changed from ")
        # print(statusword)
        if re.search(r'\bfull to \b', statusword[1]):
            status = "DOWN"
        elif re.search(r'\bto full \b', statusword[1]):
            status = "UP"
        else:
            continue
        # print(status)

        log_item = [timestamp, status, hostname, interface]
        log_dict.setdefault(neighborIP, []).append(log_item)
    # pprint.pprint(log_dict)
    return log_dict

def neighbor_date_stat(log_dict):

    neighbor_date_stat_dict = {}

    for log_entries in log_dict.items():

        date_dict = {}
        #print(log_entries[0])

        for event in log_entries[1]:
            date = event[0].split(" ")[0]
            date_dict.setdefault(date,0)
            status = event[1]
            if status == "DOWN":
                date_dict[date] += 1
        #print(date_dict)
        neighbor_date_stat_dict[log_entries[0]] = date_dict
    #print(neighbor_date_stat_dict)
    return neighbor_date_stat_dict

def neighbor_total_stat(neighbor_date_stat_dict):

    neighbor_total_stat_dict = {}

    for key in neighbor_date_stat_dict:
        neighbor_total_stat_dict[key] = sum(neighbor_date_stat_dict[key].values())

    return neighbor_total_stat_dict

def main():
    bad_word_list = ['UI_CMDLINE_READ_LINE', '---(more', 'master:', '@', 'PuTTY']
    log_lines = logfile_reader("logfile.txt", bad_word_list)
    # for item in log_lines:
    #    print(item)

    ospf_log_dict = junos_ospf_log_reader(log_lines)
    #print(ospf_log_dict)

    neighbor_date_stat_dict = {}
    neighbor_date_stat_dict = neighbor_date_stat(ospf_log_dict)

    #pprint(neighbor_date_stat_dict)
    neighbor_total_stat_dict = {}
    neighbor_total_stat_dict = neighbor_total_stat(neighbor_date_stat_dict)
    #print(neighbor_total_stat_dict)

    for neighborIP, log_lines in ospf_log_dict.items():
        interface = log_lines[0][3]
        print(f"OSPF Neighbor IP: {neighborIP} \tInterface: {interface}")
        print(f"=" * 60)

        for log in log_lines:
            timestamp   = log[0]
            status      = log[1]
            hotname     = log[2]
            interface   = log[3]

            print(f"{timestamp} \t\t\t {status}")

        print(f"=" *60)


        for date, downtime in neighbor_date_stat_dict[neighborIP].items():
            print(f"{date}: {downtime}")

        print(f"Total: {neighbor_total_stat_dict[neighborIP]}")
        print(f"\n")


    # for key, value in ospf_log_dict.items():
    #
    #     # print(value)
    #     neighborIP = key
    #     interface = value[0][3]
    #
    #     print(f"OSPF Neighbor IP: {neighborIP} \tInterface: {interface}")
    #     print(f"=" * 60)
    #
    #     for log in value:
    #
    #         timestamp = log[0]
    #         status = log[1]
    #         hostname = log[2]
    #         interface = log[3]
    #
    #         print(f'{timestamp} \t\t\t {status}')
    #
    #         if status == 'DOWN':
    #             downtime_counter += 1
    #
    #
    #     print(f"=" * 60)
    #     for key, value in date_dict.items():
    #         print(f"# of Downtime on {key} : \t{value}")
    #     print(f"Total: {downtime}")
    #     print("\n")

if __name__ == '__main__':
    main()
