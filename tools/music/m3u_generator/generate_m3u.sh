#!/bin/bash
directory=$1
artist_name=$2
album_name=$3
m3u_name="$artist_name - $album_name.m3u"
cd "$directory"
ls -1v *.mp3 > "$m3u_name"
while read f
do
  ffmpeg -i "$f" -metadata artist="$artist_name" -metadata album="$album_name" "out.mp3"
done < "$m3u_name"



##file_list=$(ls -1v *.mp3)
#echo "#EXTM3U" > "$m3u_name"
#for f in $(ls -1v *.mp3)
#do
#  echo "$f" >> "$m3u_name"
##  ffmpeg -i "$f" -metadata artist="$artist_name" -metadata album="$album_name"
#done
cd -
