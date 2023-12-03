# ping
pingcount=120
date >> ping/ping_svalbard | ping -c $pingcount 34.247.153.46 >> ping/ping_svalbard
date >> ping/ping_tsinghua | ping -c $pingcount 166.111.4.100  >> ping/ping_tsinghua
date >> ping/ping_yellowknife | ping -c $pingcount 20.104.44.154  >> ping/ping_yellowknife
date >> ping/ping_wellington | ping -c $pingcount 52.84.18.97 >> ping/ping_wellington
date >> ping/ping_falklands | ping -c $pingcount 51.145.110.210  >> ping/ping_falklands

# traceroute
date >> traceroute/traceroute_svalbard | traceroute www.unis.no >> traceroute/traceroute_svalbard
date >> traceroute/traceroute_tsinghua | traceroute www.tsinghua.edu.cn >> traceroute/traceroute_tsinghua
date >> traceroute/traceroute_yellowknife | traceroute www.yellowknife.ca >> traceroute/traceroute_yellowknife
date >> traceroute/traceroute_wellington | traceroute www.wellingtonairport.co.nz >> traceroute/traceroute_wellington
date >> traceroute/traceroute_falklands | traceroute www.falklandislands.com >> traceroute/traceroute_falklands