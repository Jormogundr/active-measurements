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
            datetimes = []
            destinations = []
            losses = []

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

                # match packet loss
                loss = re.findall(r"\d*\.?\d*\%", line)
                if loss:
                    losses.append(float(loss[0].strip("%")))

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
                    dt = pd.to_datetime(dt[0], format="%a %d %b %Y %I:%M:%S %p %Z")
                    datetimes.append(dt)

                # match destination
                if line.startswith("PING "):
                    dst = line.strip("PING ").split(" ", 1)[0]
                    destinations.append(dst)

            num_measurements = int(len(delays) / PINGS_PER_DST)

            # handle plots on per file basis
            avg_delay = []
            window = 10

            # calculate average window
            for ind in range(len(delays) - window + 1):
                avg_delay.append(np.mean(delays[ind : ind + window]))

            plt_datetimes = np.arange(0, len(delays), PINGS_PER_DST)

            # left hand axis for delays
            ax = plt.gca()
            ax.set_ylim(0, max(delays) + 5)
            ax.set_xlim(min(plt_datetimes) - 5, max(plt_datetimes) + PINGS_PER_DST)
            ax.set_title(f"Delay for {f.decode('UTF-8')}")
            ax.plot(
                np.arange(0, len(delays), 1),
                delays,
                ".",
                marker="o",
                markersize=2,
                label="Delay",
            )
            ax.plot(np.arange(0, len(avg_delay), 1), avg_delay, "r-", linewidth=2, label="Average")
            ax.vlines(
                plt_datetimes,
                ymin=0,
                ymax=max(delays),
                color="g",
                linestyles="dashed",
                linewidth=1,
            )
            ax.set_xlabel("Measurement")
            ax.set_xticks(plt_datetimes)
            ax.set_xticklabels(datetimes)
            ax.set_ylabel("Delay (ms)")

            # right hand axis for packet loss
            x_axis_losses = np.arange(PINGS_PER_DST, len(delays) + PINGS_PER_DST, PINGS_PER_DST)
            ax2 = ax.twinx()  # instantiate a second axes that shares the same x-axis
            color = "tab:orange"
            ax2.set_ylabel(
                "Packet Loss (%)", color=color
            )  # we already handled the x-label with ax1
            ax2.plot(
                x_axis_losses, losses, color=color, linewidth=3, label="Packet loss"
            )
            ax2.tick_params(axis="y", labelcolor=color)
            ax2.set_ylim(0, 100)
            ax2.legend(loc="upper right")

            # shared y axis components
            ax.legend(loc="upper left", fancybox=True, shadow=True)
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

            # initialize geolocated ips with source coord
            locations = [(41.91864795195216, -83.39556671135584)]
            avg_hop_times = []
            hops = []

            # counter for tracking unique tr blocks and max latency
            hopCount = 0
            max_latency = 0

            # iterate over lines in file
            for j, line in enumerate(lines):
                print(f, line)
                # match end of block
                end = re.findall(r"^30  ", line)
                if end:
                    hopCount = 0
                    continue

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
                    hop_avg = sum / len(hop_latency)
                    avg_hop_times.append(hop_avg)
                    hopCount += 1
                    if hop_avg > max_latency:
                        max_latency = hop_avg

                # match hop destination ip and geolocate
                ip = re.findall(
                    r"([0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3})", line
                )
                if ip:
                    ips.append(ip[0])

                    # geolocation from ip
                    match = geolite2.lookup(ip[0])
                    if match and match.location != "192.168.1.1":
                        locations.append(match.location)

                # match dropped packet
                drop = re.findall(r"\* \* \*", line)
                if drop and hopCount > 0:
                    hops.append(hopCount)

            # plot geolocated ip addresses (for each hop in traceroute)
            df = pd.DataFrame()
            df["Latitude"] = list(zip(*locations))[0]
            df["Longitude"] = list(zip(*locations))[1]
            geometry = [Point(xy) for xy in zip(df["Longitude"], df["Latitude"])]
            gdf = GeoDataFrame(df, geometry=geometry)

            world = gpd.read_file(gpd.datasets.get_path("naturalearth_lowres"))
            gdf.plot(
                ax=world.plot(figsize=(10, 6)), marker="o", color="red", markersize=10
            )
            plt.title(f"Routing for {f.decode('UTF-8')}")
            plt.savefig(f"{BASE_PATH}/plots/{f.decode('UTF-8')}-hops.pdf", format="pdf")
            plt.show()

            # bin the average hop times list by number of hops in a given traceroute command
            hop_avg_binned_by_num_hops = []
            x_axis = []
            days = []
            k = 0
            x = 0
            d = 0

            for i in range(0, len(datetimes)):
                h = []
                t = []
                days.append(d)
                for j in range(0, hops[i]):
                    h.append(avg_hop_times[k])
                    t.append(x)
                    k += 1
                    x += 1
                hop_avg_binned_by_num_hops.append(h)
                x_axis.append(t)
                d += len(t)

                k = hops[i]

            # plot average hoptimes
            ax = plt.gca()
            for i, hop in enumerate(hop_avg_binned_by_num_hops):
                ax.plot(x_axis[i], hop, color="tab:blue")
            ax.set_xlabel("Hop Number")
            ax.vlines(
                days,
                ymin=0,
                ymax=max_latency,
                color="g",
                linestyles="dashed",
                linewidth=1,
                label="Datetimes",
            )
            ax.set_ylabel("Avg Hop Delay (ms)")
            ax.legend(loc="upper left", fancybox=True, shadow=True)
            plt.title(f"Average Hop Delays for {f.decode('UTF-8')}")
            ax.tick_params(axis="x", rotation=70)
            plt.tight_layout()
            plt.savefig(
                f"{BASE_PATH}/plots/{f.decode('UTF-8')}-avg-hop-delay.pdf", format="pdf"
            )
            plt.gcf().autofmt_xdate()
            plt.show()

    plot_ping_data()
    plot_traceroute_data()


if __name__ == "__main__":
    main()
    exit(0)
