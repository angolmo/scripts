import argparse
import music_tag
import os

if __name__ == "__main__":
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument("directory")
    arg_parser.add_argument("--artist")
    arg_parser.add_argument("--album")
    arg_parser.add_argument("--m3u-name")
    args = arg_parser.parse_args()
    
    listed_files = sorted(os.listdir(args.directory))
    mp3_files = []
    for file in listed_files:
        if file.endswith("mp3")and os.path.isfile(os.path.join(args.directory, file)):
            mp3_files.append(file)
    
    # Create m3u file
    m3u_name = args.m3u_name if args.m3u_name else args.artist + " - " + args.album + ".m3u"
    with open(os.path.join(args.directory, m3u_name), 'w') as f:
        f.write("\n".join(mp3_files))
        f.write("\n")

    # Write ID3 tags for this folder based on artist and album
    for mp3 in mp3_files:
        mp3_meta = music_tag.load_file(os.path.join(args.directory, mp3))
        if args.album:
            mp3_meta['album'] = args.album
        if args.artist:
            mp3_meta['artist'] = args.artist
        mp3_meta.save()
