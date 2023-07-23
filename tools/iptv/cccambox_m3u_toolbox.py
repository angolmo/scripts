"""
Toolbox to parse m3u files from ccambox

M3U files have this format:
- Follows M3U standard format for iptv (see https://en.wikipedia.org/wiki/M3U)
- First line of the file is the header directive #EXTM3U
- Each channel is defined by two consecutive lines: first one with the #EXTINF directive containing the information about the channel,
    and second one with the URL to the channel
- Conventions for lines starting by #EXTINF directives:
    - Every line contains a field called group-title which contains the country of the channel. Exceptions are sometimes made for the 
        special channels (movies, series etc)
    - Every line contains a field called tvg-name which contains the name of the channel very usually starting with some initials of the country
        surrounded by ||. Examples of this can be:
          #EXTINF:-1 tvg-ID="" tvg-name="|PL| -= Poland =-" tvg-logo="" group-title="POLAND",|PL| -= Poland =-
          #EXTINF:-1 tvg-ID="uk.Sky Sports News" tvg-name="|GB| SKY SPORTS News HD" tvg-logo="http://instanttv.info:8080/logos/skysportsnews.svg" group-title="UNITED KINGDOM",|GB| SKY SPORTS News HD
    - Often times channels inside a country are grouped by category. A category is defined with a special channel whose URL is broken 
        and whose tvg-name field contains some special characters with the name of the category in the middle. Examples of this can be:
          #EXTINF:-1 tvg-ID="" tvg-name="•----• UK Sports •----•" tvg-logo="" group-title="UNITED KINGDOM",•----• UK Sports •----•
          #EXTINF:-1 tvg-ID="" tvg-name="######## SWITZERLAND - MALTA ########" tvg-logo="" group-title="",######## SWITZERLAND - MALTA ########
          #EXTINF:-1 tvg-ID="" tvg-name="######## ITALIAN MOVIES ########" tvg-logo="" group-title="",######## ITALIAN MOVIES ########
          #EXTINF:-1 tvg-ID="" tvg-name="======== SERIES ========" tvg-logo="" group-title="",======== SERIES ========
          #EXTINF:-1 tvg-ID="" tvg-name="***** Arabic Sport *****" tvg-logo="" group-title="ARABIC",***** Arabic Sport *****
          #EXTINF:-1 tvg-ID="" tvg-name="|PL| -= Poland =-" tvg-logo="" group-title="POLAND",|PL| -= Poland =-



#EXTM3U
#EXTINF:-1 tvg-ID="" tvg-name="•----• UK Sports •----•" tvg-logo="" group-title="UNITED KINGDOM",•----• UK Sports •----•
http://url-to-channel
#EXTINF:-1 tvg-ID="uk.Sky Sports News" tvg-name="|GB| SKY SPORTS News HD" tvg-logo="http://instanttv.info:8080/logos/skysportsnews.svg" group-title="UNITED KINGDOM",|GB| SKY SPORTS News HD
http://url-to-channel

... Other channels from UK Sports subgroup

#EXTINF:-1 tvg-ID="" tvg-name="•----• UK Movies •----•" tvg-logo="" group-title="UNITED KINGDOM",•----• UK Movies •----•
http://url-to-channel
#EXTINF:-1 tvg-ID="UK| SKY CINEMA ACTION" tvg-name="|GB| SKY Cinema Action FHD" tvg-logo="http://instanttv.info:8080/logos/skycinemaaction.light.svg" group-title="UNITED KINGDOM",|GB| SKY Cinema Action FHD
http://url-to-channel
#EXTINF:-1 tvg-ID="UK| SKY CINEMA ACTION" tvg-name="|GB| SKY Cinema Action SD" tvg-logo="http://instanttv.info:8080/logos/skycinemaaction.light.svg" group-title="UNITED KINGDOM",|GB| SKY Cinema Action SD
http://url-to-channel

... Other channels from UK Movies

"""

import argparse
import logging
import os.path
import re
import sys

# Parses a line of extinf and returns a dictionary with the data contained in it
def extinf_to_dict(extinf_line, logger):
    extinf_regex = re.compile(r'^#EXTINF:([\-]?\d)((?:\s+[^\s="]*="[^"]*")+),(.*)')
    match_line = extinf_regex.match(extinf_line)
    if not match_line:
        logger.error('failed to match extinf_line: {}'.format(extinf_line))
        return dict()
    extinf_dict = dict(re.findall(r'(\S+)="(.*?)"', match_line.group(2)))
    extinf_dict['duration'] = match_line.group(1)
    extinf_dict['title'] = match_line.group(3)
    #logger.debug("{}".format(extinf_dict))
    return extinf_dict

# Evaluates if a channel is in reality a category
def is_category_header(extinf_dict):
    tvg_name = extinf_dict['tvg-name']
    return "----" in tvg_name or "####" in tvg_name or "====" in tvg_name or "****" in tvg_name or "-=" in tvg_name

# Evaluates whether the given line is part of the file header or not
def is_file_header(line):
    return line.startswith("#EXTM3U") or line.startswith("#EXT-X")

# Helper type to collect statistics
class stats:
    def __init__(self):
        self.lines = 0
        self.channels = 0
        self.matched_channels = 0
        self.category_headers = 0
        self.matched_category_headers = 0
        self.groups = 0
        self.matched_group_channels = 0

    def new_line(self):
        self.lines += 1

    def new_channel(self, increase_lines = True):
        self.channels += 1
        if increase_lines: self.lines += 2

    def new_channel_match(self):
        self.matched_channels += 1

    def new_category_header(self):
        self.category_headers += 1

    def new_category_header_match(self):
        self.matched_category_headers += 1

    def new_group(self):
        self.groups += 1

    def new_group_channel_match(self):
        self.matched_group_channels += 1

    def __str__(self):
        return '{} lines parsed\n{}/{} channels parsed\n{} groups found\n{} channels are category headers\n{} category headers for given group\n{} channels in given group'.format(
            self.lines, self.matched_channels, self.channels, self.groups, self.category_headers, self.matched_category_headers, self.matched_group_channels)

## Main

if __name__ == "__main__":
 
    # Parse arguments
    parser = argparse.ArgumentParser(description='Toolbox for ccambox m3u file')
    parser.add_argument('m3u_file', help='path to m3u file')
    parser.add_argument('-g', '--groups', action='store_true', help='display all the groups in the m3u file')
    parser.add_argument('-c', '--categories', dest='categories_group', type=str, help='display all the categories whose group-title matches group')
    parser.add_argument('-ch', '--channels', dest='channels_group', type=str, help='display all the channels whose group-title matches group')
    parser.add_argument('-cg', '--change-groups', dest='group_to_change', type=str, help='change group-title by the category')
    parser.add_argument('-v', '--verbose', action='store_true', help='verbose output')
    parser.add_argument('--stats', action='store_true', help='show file stats')

    args = parser.parse_args()

    # Start and configure logger
    logger = logging.getLogger(__name__)
    logging.basicConfig(format='%(levelname)s: %(message)s')
    if args.verbose: 
        logger.setLevel(logging.DEBUG)
    else: 
        logger.setLevel(logging.INFO)
    
    # Check file exists
    if not os.path.exists(args.m3u_file):
        logger.error("could not open file {}".format(args.m3u_file))
        sys.exit(1)

    # Create stats manager
    stats = stats()

    # Start parsing the file
    with open(args.m3u_file, 'r') as f:
        groups = list()
        categories = list()
        channels = ''
        file_header = ''
        while True:
            # read line and figure out if it's part of the header or not
            new_line = f.readline()
            if is_file_header(new_line):
                file_header += new_line
                stats.new_line()
                continue
            extinf = new_line
            url = f.readline()
            if not url: 
                break # EOF

            extinf_dict = extinf_to_dict(extinf, logger)
            if extinf_dict:
                stats.new_channel_match()
                group_title = extinf_dict['group-title']

                if group_title not in groups:
                    groups.append(group_title)
                    stats.new_group()

                if is_category_header(extinf_dict):
                    tvg_name = extinf_dict['tvg-name']
                    if args.categories_group and args.categories_group in group_title:
                        categories.append(tvg_name)
                        stats.new_category_header_match()
                    if args.group_to_change:
                        tvg_name_to_group = " ".join(re.findall("[a-zA-Z]+", tvg_name))
                        logger.debug('{} will be used as group-title="{}"'.format(tvg_name, tvg_name_to_group))

                if args.group_to_change and args.group_to_change in group_title:
                    extinf = re.sub('group-title=".*"', 'group-title="{}"'.format(tvg_name_to_group),extinf)
                    logger.debug('sub result is {}'.format(extinf))

                if args.channels_group and args.channels_group in group_title:
                    channels += '{}{}'.format(extinf, url)
                    stats.new_group_channel_match()
            else:
                logger.warning("Channel failed to match: {}".format(extinf))
            stats.new_channel()

    if args.groups:
        print("Groups:\n{}\n".format(groups))
    if args.categories_group:
        print('Categories whose group-title includes {}:\n{}\n'.format(args.categories_group, categories))
    if args.channels_group:
        print('{}{}'.format(file_header, channels))
    if args.stats:
        print('Stats:\n{}\n'.format(stats))
