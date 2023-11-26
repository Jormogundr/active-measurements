import os
import re
import datetime
import subprocess as sp

import pandas as pd

BASE_PATH = "/".join([os.getenv("HOME"), "active-measurements"])
PING_PATH = "/".join([BASE_PATH, "ping"])
TRACEROUTE_PATH = "/".join([BASE_PATH, "traceroute"])


def main():
    
    def convert_ping_raw_to_dataframe():
        cols = ["ICMP_SEQ", "TTL", "TIME", "DATETIME", "DESTINATION"]
        ping_df = pd.DataFrame(columns=cols)

        if not os.path.exists(PING_PATH):
            print("{} does not exist".format(PING_PATH))

        directory = os.fsencode(PING_PATH)

        # iterate over files in dir
        for f in os.listdir(directory):
            fname = "/".join([PING_PATH, os.fsdecode(f)])
            if not os.path.exists(fname):
                print("{} does not exist".format(fname))
            fcontents = open(fname, "r")
            lines = fcontents.read().splitlines()

            # initialize pandas series lists on per file basis
            icmp_sequences = []
            ttls = []
            times = []
            datetimes, unix_times = [], []
            destinations = []

            # iterate over lines in file
            for line in lines:
                # match icmp_seq
                icmp_seq = re.findall(r"(?i)icmp_seq=([0-9]*)", line)
                if icmp_seq:
                    icmp_sequences.append(icmp_seq[0])

                # match ttl
                ttl = re.findall(r"(?i)ttl=([0-9]*)", line)
                if ttl:
                    ttls.append(ttl[0])

                # match time
                time = re.findall(r"(?i)time=([0-9]*)", line)
                if time:
                    times.append(ttl[0])
                
                # match datetime
                dt = re.findall(r"^[A-Z][a-z]{2}\ \d*\ [A-Z][a-z]{2}\ [\d]{4}\ [\d:]*\ [A-Z]{2}\ EST", line)
                if dt:
                    unix_time = int(sp.getoutput(f"date --date='{dt[0]}' +FORMAT='%s'").strip("FORMAT="))
                    dt = pd.to_datetime(unix_time, unit='s')
                    unix_times.append(unix_time)
                    datetimes.append(dt)

                # match destination
                if line.startswith("PING "):
                    dst = line.strip("PING ").split(" ", 1)[0]
                    destinations.append(dst)


            # convert python lists to pandas series
            icmp_sequence_series = pd.Series(icmp_sequences, dtype=int)
            ttl_series = pd.Series(ttls, dtype=int)
            time_series = pd.Series(times, dtype=int)
            datetime_series = pd.Series(datetimes)
            unix_time_series = pd.Series(unix_times, dtype=int)
            print(datetime_series)

            # add pandas series to pandas dataframe
            
            

    def convert_tr_raw_to_dataframe():
        pass

    convert_ping_raw_to_dataframe()


if __name__ == "__main__":
    main()
