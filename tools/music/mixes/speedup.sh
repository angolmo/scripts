#!/bin/bash -e

for f in *.mp3 ; 
do
    output_path="$f.2"
    echo "Processing $f ..."
    bash speedup_one.sh "$f" "$output_path"
    echo "   $output_path created successfully"
    echo ""
done
