import os
import re
import subprocess as sp
import urllib.request

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

from shapely.geometry import Point
import geopandas as gpd
from geopandas import GeoDataFrame
from geoip import geolite2

BASE_PATH = "/".join([os.getenv("HOME"), "active-measurements"])
PING_PATH = "/".join([BASE_PATH, "ping"])
TRACEROUTE_PATH = "/".join([BASE_PATH, "traceroute"])
PINGS_PER_DST = 120


def main():
    def plot_ping_data():
        cols = ["ICMP_SEQ", "TTL", "DELAY", "DATETIME", "UNIX_TIME", "DESTINATION"]

        if not os.path.exists(PING_PATH):
            print("{} does not exist".format(PING_PATH))

        directory = os.fsencode(PING_PATH)

        # iterate over files in dir
        for i, f in enumerate(os.listdir(directory)):
            fname = "/".join([PING_PATH, os.fsdecode(f)])
            if not os.path.exists(fname):
                print("{} does not exist".format(fname))
                exit(1)
            fcontents = open(fname, "r")
            lines = fcontents.read().splitlines()

            icmp_sequences = []
            ttls = []
            delays = []
            datetimes, unix_times = [], []
            destinations = []

            # iterate over lines in file
            for j, line in enumerate(lines):
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
                    delays.append(float(delay[0]))

                # match datetime
                dt = re.findall(
                    r"^[A-Z][a-z]{2}\ \d*\ [A-Z][a-z]{2}\ [\d]{4}\ [\d:]*\ [A-Z]{2}\ EST",
                    line,
                )
                if dt:
                    unix_time = int(
                        sp.getoutput(f"date --date='{dt[0]}' +FORMAT='%s'").strip(
                            "FORMAT="
                        )
                    )
                    dt = pd.to_datetime(unix_time, unit="s")
                    unix_times.append(unix_time)
                    datetimes.append(dt)

                # match destination
                if line.startswith("PING "):
                    dst = line.strip("PING ").split(" ", 1)[0]
                    destinations.append(dst)

            num_measurements = int(len(delays) / PINGS_PER_DST)

            # handle plots on per file basis
            avg = []
            window = 10

            # calculate average window
            for ind in range(len(delays) - window + 1):
                avg.append(np.mean(delays[ind : ind + window]))

            plt_datetimes = np.arange(0, len(delays), PINGS_PER_DST)

            # plot
            plt.vlines(3, ymin=0, ymax=1)
            ax = plt.gca()
            ax.set_ylim([min(delays) - 5, max(delays) + 5])
            ax.set_title(f"Delay for {f.decode('UTF-8')}")
            ax.plot(delays, ".", label="Raw data")
            ax.plot(avg, "r-", label="Average")
            ax.vlines(
                plt_datetimes,
                ymin=min(delays),
                ymax=max(delays),
                color="g",
                linestyles="dashed",
                label="Datetimes",
                linewidth=1,
            )
            ax.set_xlabel("Measurement")
            ax.set_xticks(plt_datetimes)
            ax.set_xticklabels(datetimes)
            ax.set_ylabel("Delay (ms)")
            ax.legend(loc="upper right", fancybox=True, shadow=True)
            ax.tick_params(axis="x", rotation=70)
            plt.tight_layout()
            plt.savefig(
                f"{BASE_PATH}/plots/{f.decode('UTF-8')}-delays.pdf", format="pdf"
            )
            plt.gcf().autofmt_xdate()
            plt.show()

    def plot_traceroute_data():

        if not os.path.exists(TRACEROUTE_PATH):
            print("{} does not exist".format(TRACEROUTE_PATH))

        directory = os.fsencode(TRACEROUTE_PATH)
        # iterate over files in dir
        for f in os.listdir(directory):
            fname = "/".join([TRACEROUTE_PATH, os.fsdecode(f)])
            if not os.path.exists(fname):
                print("{} does not exist".format(fname))
                exit(1)
            fcontents = open(fname, "r")
            lines = fcontents.read().splitlines()

            datetimes, unix_times = [], []
            ips = []
            locations = []
            avg_hop_times = []
            
            # traceroute blocks are separated by several newlines
            # keep track of those so we can match contiguous lines
            linecount = 3

            # iterate over lines in file
            for j, line in enumerate(lines):
                # match datetime
                dt = re.findall(
                    r"^[A-Z][a-z]{2}\ \d*\ [A-Z][a-z]{2}\ [\d]{4}\ [\d:]*\ [A-Z]{2}\ EST",
                    line,
                )
                if dt:
                    unix_time = int(
                        sp.getoutput(f"date --date='{dt[0]}' +FORMAT='%s'").strip(
                            "FORMAT="
                        )
                    )
                    dt = pd.to_datetime(unix_time, unit="s")
                    unix_times.append(unix_time)
                    datetimes.append(dt)

                # match hop times and find average
                hop_latency = re.findall(r"([0-9]*\.[0-9]*) ms", line)
                if hop_latency:
                    sum = 0
                    for h in hop_latency:
                        sum += float(h)
                    hop_avg = sum/len(hop_latency)
                    avg_hop_times.append(hop_avg)

                # match hop destination ip and geolocate
                ip = re.findall(r"([0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3})", line)
                if ip and linecount > 3:
                    ips.append(ip[0])
                    linecount = 0
                    

                    # geolocation from ip
                    match = geolite2.lookup(ip[0])
                    if match.location:
                        locations.append(match.location)
                    else:
                        locations.append("Unknown location")

                linecount += 1
        
            # handle data on per file basis

            # plot geolocated ip addresses (for each hop in traceroute)
            df = pd.DataFrame()
            df['Latitude'] = list(zip(*locations))[0]
            df['Longitude'] = list(zip(*locations))[1]
            geometry = [Point(xy) for xy in zip(df['Longitude'], df['Latitude'])]
            gdf = GeoDataFrame(df, geometry=geometry)   

            world = gpd.read_file(gpd.datasets.get_path('naturalearth_lowres'))
            gdf.plot(ax=world.plot(figsize=(10, 6)), marker='o', color='red', markersize=10)
            plt.title(f"Routing for {f.decode('UTF-8')}")
            plt.show()
        
    plot_traceroute_data()
    #plot_ping_data()


if __name__ == "__main__":
    main()
    exit(0)
