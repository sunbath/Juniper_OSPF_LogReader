# Author: Eric Leung
# Last Modified: 23-Jan-2019
import re

def ospf_log_read(logfile):

    ospf_log_dict ={}
    f = open(logfile, 'r+')
    # Extract the last (-1) string in each command is subnet in each prefix-list and convert them to network address object
    with open(logfile) as f:
        for line in f:
            word = line.split(" ")
            statusword = line.split("state changed from ")
            timestamp = (word[1]+"-"+word[0]+" "+word[2]).strip()
            date = (word[1]+"-"+word[0]).strip()
            time = (word[2]).strip()

            #print(statusword[1])
            if re.search(r'\bFull to \b',statusword[1]):
                status = "DOWN"
            elif re.search(r'\bExchange to Full \b',statusword[1]):
                status = "UP"
            else:
                continue

            nbrip = word[9].strip()
            interface = word[10]
            #print(timestamp," ",status," ",nbrip," ",interface)
            new_info = [status,date,time]
            #print(new_info)
            ospf_log_dict.setdefault(nbrip,[]).append(new_info)
            #print(ospf_log_dict)
    f.close()
    return ospf_log_dict

def main():

    # Clean-up the log file
    bad_words = ['UI_CMDLINE_READ_LINE', '---(more', 'master:0' , '@' , 'PuTTY']
    with open('logfile.txt') as oldfile, open('newfile.txt', 'w') as newfile:
        for line in oldfile:
            if not any(bad_word in line for bad_word in bad_words):
                if len(line.strip()) > 0:
                    newfile.write(line)

    ospf_log_dict = ospf_log_read("newfile.txt")

    for key,value in ospf_log_dict.items():
        print(f"OSPF Neighbor IP: \t{key}")

        date_dict = {}
        for item in value:
            date_dict.setdefault(item[1],0)
        #print(date_dict)

        for item in value:
            if item[0] == "DOWN":
                date_dict[item[1]] +=1
        #print(date_dict)

        print(f"="*40)
        downtime = 0
        for item in value:
            if item[0] == "DOWN":
                downtime += 1
            print(f"{item[1]} {item[2]} \t {item[0]}")
        print(f"="*40)

        for key,value in date_dict.items():
            print(f"# of Downtime on {key} : \t{value}")
        print(f"Total: {downtime}")
        print("\n")

if __name__ == '__main__':
    main()