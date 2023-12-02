import os
import re
import datetime
import subprocess as sp

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

BASE_PATH = "/".join([os.getenv("HOME"), "active-measurements"])
PING_PATH = "/".join([BASE_PATH, "ping"])
TRACEROUTE_PATH = "/".join([BASE_PATH, "traceroute"])
PINGS_PER_DST = 120


def main():
    
    def convert_ping_raw_to_dataframe():
        cols = ["ICMP_SEQ", "TTL", "DELAY", "DATETIME", "UNIX_TIME", "DESTINATION"]
        

        if not os.path.exists(PING_PATH):
            print("{} does not exist".format(PING_PATH))

        directory = os.fsencode(PING_PATH)

        icmp_sequences = []
        ttls = []
        delays = []
        datetimes, unix_times = [], []
        destinations = []

        # iterate over files in dir
        for f in os.listdir(directory):
            fname = "/".join([PING_PATH, os.fsdecode(f)])
            if not os.path.exists(fname):
                print("{} does not exist".format(fname))
            fcontents = open(fname, "r")
            lines = fcontents.read().splitlines()

            

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
                delay = re.findall(r"(?i)time=([0-9]*)", line)
                if delay:
                    delays.append(delay[0])
                
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

            # rows in dataframe must be equal length
            num_measurements = int(len(delays)/PINGS_PER_DST)
            df_datetimes = []
            df_unix_times = []
            df_destinations = []
            for m in range(0, num_measurements):
                for n in range(0, PINGS_PER_DST):
                    df_datetimes.append(datetimes[m])
                    df_unix_times.append(unix_times[m])
                    df_destinations.append(destinations[m])

        # build dataframe after iterating through all files
        # "ICMP_SEQ", "TTL", "DELAY", "DATETIME", "UNIX_TIME", "DESTINATION"
        # ping_df = pd.DataFrame(columns=cols)
        # ping_df['ICMP_SEQ'] = icmp_sequences
        # ping_df['TTL'] = icmp_sequences
        # ping_df['DELAY'] = delays
        # ping_df['DATETIME'] = df_datetimes
        # ping_df['UNIX_TIME'] = df_unix_times
        # ping_df['DESTINATION'] = df_destinations
        
        # plot
        plt.plot(delays)
        plt.show()
            
            

    def convert_tr_raw_to_dataframe():
        pass

    convert_ping_raw_to_dataframe()


if __name__ == "__main__":
    main()
