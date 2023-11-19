# ping
pingcount=120
date >> ping/ping_svalbard | ping -c $pingcount www.unis.no >> ping/ping_svalbard
date >> ping/ping_tsinghua | ping -c $pingcount www.tsinghua.edu.cn  >> ping/ping_tsinghua
date >> ping/ping_yellowknife | ping -c $pingcount www.yellowknife.ca  >> ping/ping_yellowknife
date >> ping/ping_wellington | ping -c $pingcount www.wellingtonairport.co.nz >> ping/ping_wellington
date >> ping/ping_falklands | ping -c $pingcount www.falklandislands.com  >> ping/ping_falklands

# traceroute
date >> traceroute/traceroute_svalbard | traceroute www.faroeislands.fo >> traceroute/traceroute_svalbard
date >> traceroute/traceroute_tsinghua | traceroute www.tsinghua.edu.cn >> traceroute/traceroute_tsinghua
date >> traceroute/traceroute_yellowknife | traceroute www.yellowknife.ca >> traceroute/traceroute_yellowknife
date >> traceroute/traceroute_wellington | traceroute www.wellingtonairport.co.nz >> traceroute/traceroute_wellington
date >> traceroute/traceroute_falklands | traceroute www.falklandislands.com >> traceroute/traceroute_falklands