#!/bin/bash -e

if [ -z "$1" ] || [ -z "$2" ] ; then
    echo "Missing input file or output file/directory"
    echo "Usage: $0 input_path output_path"
    echo "input_path Path to input mp3 file"
    echo "output_path Path to output mp3 file. If a directory is provided, then the output path will be given by output_path and filename of input_path"
    exit 1
fi

input_mp3_path=$1

# Convert MP3 to wav
wav_filename_in="$input_mp3_path.wav"
ffmpeg -i "$input_mp3_path" -v 0 "$wav_filename_in"

# Increase rate WAV by +5%
wav_filename_out="$input_mp3_path.out.wav"
soundstretch "$wav_filename_in" "$wav_filename_out" -rate=+5 > /dev/null
rm "$wav_filename_in"

# Re-encode into MP3
if [ -d "$2" ] ; then
    output_mp3_path="$2/$(basename "$input_mp3_path")"
else
    output_mp3_path="$2"
fi
ffmpeg -i "$wav_filename_out" -vn -ac 2 -ar 44100 -ab 192k -f mp3 -v 0 "$output_mp3_path"
rm "$wav_filename_out"
