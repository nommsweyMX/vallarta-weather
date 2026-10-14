#!/bin/bash
# GFS 18Z 13 Oct 2026, 0-384 h every 3 h, region 0-36N 125-75W: MSLP, 10-m wind, precipitation rate
D=$1; cd $D/grib
for h in $(seq 0 3 384); do
  f=$(printf "f%03d" $h); [ -s $f.grb2 ] && continue
  for i in 1 2 3 4; do
    curl -sS -m 90 -f -o $f.grb2 "https://nomads.ncep.noaa.gov/cgi-bin/filter_gfs_0p25.pl?dir=%2Fgfs.20261013%2F18%2Fatmos&file=gfs.t18z.pgrb2.0p25.$f&var_PRMSL=on&var_UGRD=on&var_VGRD=on&var_PRATE=on&lev_mean_sea_level=on&lev_10_m_above_ground=on&lev_surface=on&subregion=&toplat=36&leftlon=235&rightlon=285&bottomlat=0" && break
    rm -f $f.grb2; sleep $((3*i))
  done
  sleep 0.6
done
ls $D/grib/f*.grb2 | wc -l
