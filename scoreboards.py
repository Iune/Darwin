from PIL import Image, ImageDraw, ImageFont, ImageOps
from unidecode import unidecode
import json
import os


def ordinalize(num):
    if num > 9:
        second_to_last_digit = str(num)[-2]
        if second_to_last_digit == '1':
            return 'th'
    last_digit = num % 10
    if (last_digit == 1):
        return 'st'
    elif (last_digit == 2):
        return 'nd'
    elif (last_digit == 3):
        return 'rd'
    else:
        return 'th'


'''
Convert a hexadecimal representation of a color to RGB (the format needed by the Python Imaging Library)
Function taken from http://stackoverflow.com/questions/214359/converting-hex-color-to-rgb-and-vice-versa
'''
def hex_to_rgb(value):
    value = value.lstrip('#')
    lv = len(value)
    return tuple(int(value[i:i + lv // 3], 16) for i in range(0, lv, lv // 3))


'''
A helper function which loads a json file with various permissible country names
(according to ISO standards), in order to map the two letter ISO code to the country's full name.
'''
def load_country_mappings():
    flags = {}
    with open("Resources/countries.json", encoding="utf8") as f:
        temp = json.load(f)
    for item in temp:
        flags[item['name']] = item
    return flags


# Makes sure the output directory exists. If it doesn't it creates said directory.
def create_output_dir():
    if not os.path.isdir('Output'):
        os.makedirs('Output', exist_ok=True)


'''
Strips diacritics and other special characters from voter names for use in creating
filesafe output file names
'''
def safe_file_name(file_name):
    safe = file_name.strip()
    for c in r'[]/\;,><&*:%=+@!#^()|?^':
        safe = safe.replace(c,'')
    safe = unidecode(safe)
    return safe

def load_fonts(scale):
    fonts = {}
    fonts['voter_header'] = ImageFont.truetype("Resources/Fonts/Dosis-Regular.ttf", 12*scale, encoding="unic")
    fonts['header'] = ImageFont.truetype("Resources/Fonts/Dosis-Bold.ttf", 21*scale, encoding="unic")
    fonts['country'] = ImageFont.truetype("Resources/Fonts/Dosis-Regular.ttf", 10*scale, encoding="unic")
    fonts['awarded_pts'] = ImageFont.truetype("Resources/Fonts/Dosis-Light.ttf", 14*scale, encoding="unic")
    fonts['total_pts'] = ImageFont.truetype("Resources/Fonts/Dosis-Bold.ttf", 14*scale, encoding="unic")
    return fonts


def load_colors(main_color="#2f292b", accent_color="#009688"):
    colors = {}
    colors['light_grey'] = hex_to_rgb("#EEEEEE")
    colors['white'] = hex_to_rgb("#FAFAFA")
    colors['black'] = hex_to_rgb("#212121")
    colors['text_grey'] = hex_to_rgb("#C4C4C4")
    colors['text_caption'] = hex_to_rgb("#7E7E7E")
    colors['text_white'] = hex_to_rgb("#FFFFFF")
    colors['main'] = hex_to_rgb(main_color)
    colors['accent'] = hex_to_rgb(accent_color)
    return colors


def determine_image_size(fonts, contest, scale, current_voter_num):
    img = Image.new('RGBA', size=(1,1))
    draw = ImageDraw.Draw(img)

    header_size = draw.textsize('{} Results'.format(contest.name), font=fonts['header'])
    voter_header_size = draw.textsize('Now Voting: {} ({}/{})'.format(contest.voters[current_voter_num],
            current_voter_num+1, contest.num_voters), font=fonts['voter_header'])
    entry_size = (0,0)
    user_size = (0,0)
    for entry in contest.data:
        temp_entry_size = draw.textsize("{} - {}".format(entry.artist, entry.song), font=fonts['country'])
        if temp_entry_size[0] > entry_size[0]:
            entry_size = temp_entry_size

        if contest.display_countries:
            temp_user_size = draw.textsize(entry.country, font=fonts['country'])
        else:
            temp_user_size = draw.textsize(entry.user, font=fonts['country'])
        if temp_user_size[0] > user_size[0]:
            user_size = temp_user_size

    flag_offset = 0
    if contest.display_flags:
        flag_offset = 24*scale

    rectangle_width = max(entry_size[0], user_size[0]) + 80*scale + flag_offset
    image_width = max((30*scale + 2*rectangle_width), (48*scale + header_size[0]), (10*scale + voter_header_size[0]))
    image_height = scale*(90 + 30*(int(contest.num_entries/2) + contest.num_entries%2) + 20)

    return [(image_width, image_height), rectangle_width, flag_offset, entry_size, user_size]

# Generates a scoreboard image that is inspired by Google's Material Design design guidelines
def generate_scoreboard(contest, sorted_data, current_voter_num, colors):
    create_output_dir()
    flags = load_country_mappings()
    safe_voter_name = safe_file_name(contest.voters[current_voter_num])
    scale = 4

    fonts = load_fonts(scale)

    image_size = determine_image_size(fonts, contest, scale, current_voter_num)
    image_width, image_height = image_size[0]
    rectangle_width = image_size[1]
    flag_offset = image_size[2]
    entry_size = image_size[3]
    user_size = image_size[4]

    img = Image.new('RGBA', size=(image_width, image_height))
    draw = ImageDraw.Draw(img)

    # Background rectangle for scoreboard
    draw.rectangle(((0,0), (image_width, image_height)), fill=colors['light_grey'])

    # Voting Top Bar
    draw.rectangle(((0,0), (image_width, 21*scale)), fill=colors['main'])
    draw.text((5*scale, 3*scale), "Now Voting: {} ({}/{})".format(contest.voters[current_voter_num],
            current_voter_num+1, contest.num_voters), fill=colors['text_white'], font=fonts['voter_header'])
    # Contest Name Top Bar
    draw.rectangle(((0, 20*scale), (image_width, 65*scale)), fill=colors['accent'])
    draw.text((24 * scale, 31 * scale), "{} Results".format(contest.name), fill=colors['text_white'], font=fonts['header'])

    # Determine number of entries to place on left column of scoreboard
    left_column = int(contest.num_entries/2) + contest.num_entries%2

    # Background rectangles for the two columns
    draw.rectangle(((10*scale, 90*scale), (10*scale + rectangle_width, 90*scale+30*scale*left_column)),
                fill=colors['white'], outline=colors['text_grey'])
    draw.rectangle(((20*scale+rectangle_width, 90*scale), (20*scale + 2*rectangle_width, 90*scale+30*scale*left_column)),
                fill=colors['white'], outline=colors['text_grey'])

    # Now place each entry onto the scoreboard
    for current_entry in range(contest.num_entries):
        if current_entry < left_column:
            x_offset = 0
            y_offset = current_entry
        else:
            x_offset = 10*scale + rectangle_width
            y_offset = current_entry - left_column

        entry = sorted_data[current_entry]

        if contest.display_flags:
            try:
                category = flags[entry.country]['category']
                country_iso = flags[entry.country]['alpha-2']

                flag = Image.open('Resources/Flags/{}/{}.png'.format(category, country_iso), 'r')
                flag_width, flag_height = flag.size

                if flag_width < flag_height:
                    flag = flag.resize((int((float(flag_width) / flag_height) * 20 * scale), 20 * scale), Image.ANTIALIAS)
                elif flag_width == flag_height:
                    flag = flag.resize((20 * scale, 20 * scale), Image.ANTIALIAS)
                else:
                    flag = flag.resize((20 * scale, int((float(flag_height) / flag_width) * 20 * scale)), Image.ANTIALIAS)
                flag = ImageOps.expand(flag, border=1, fill=colors['text_grey'])

                img.paste(flag, (int(20 * scale + 10 * scale - flag.width / 2.0) + x_offset,
                                 int(95 * scale + 10 * scale - flag.height / 2.0 + 30 * y_offset * scale)))

            except IndexError:
                country_iso = ""

            except KeyError:
                country_iso = ""

        # Display either the entry artist's country of origin or the user's name
        if contest.display_countries:
            country_string = entry.country
        else:
            country_string = entry.user

        draw.text((20*scale+x_offset+flag_offset, 93*scale+30*scale*y_offset), country_string,
                fill=colors['text_caption'], font=fonts['country'])

        # Display the entry's artist and song title
        draw.text((20*scale+x_offset+flag_offset, 105.5*scale+30*scale*y_offset), "{} - {}".format(entry.artist, entry.song),
                fill=colors['black'], font=fonts['country'])

        # Display the total points the entry currently has
        draw.rectangle(((20*scale+x_offset+flag_offset+max(entry_size[0],user_size[0])+10*scale, 95*scale+30*scale*y_offset),
                (20*scale+x_offset+flag_offset+max(entry_size[0],user_size[0])+10*scale+27*scale,
                 95*scale+30*scale*y_offset+20*scale)), fill=colors['main'])
        total_size = draw.textsize("{}".format(entry.display_pts), font=fonts['total_pts'])
        draw.text((20*scale+x_offset+flag_offset+max(entry_size[0],user_size[0])+10*scale+(27/2)*scale-(total_size[0]/2.0),
                95*scale+30*scale*y_offset), "{}".format(entry.display_pts), fill=colors['text_white'], font=fonts['total_pts'])

        # Display the points awarded by the current voter
        if entry.voters[current_voter_num] != 0 and entry.voters[current_voter_num] != '':
            draw.rectangle(((20*scale+x_offset+flag_offset+max(entry_size[0],user_size[0])+10*scale+27*scale, 95*scale+30*scale*y_offset),
                    (20*scale+x_offset+flag_offset+max(entry_size[0],user_size[0])+10*scale+27*scale+23*scale,
                    95*scale+30*scale*y_offset+20*scale)), fill=colors['accent'])
            awarded_size = draw.textsize("{}".format(entry.voters[current_voter_num]), font=fonts['awarded_pts'])
            draw.text((20*scale+x_offset+flag_offset+max(entry_size[0],user_size[0])+10*scale+27*scale+(22/2.0)*scale-(awarded_size[0]/2.0),
                    95*scale+30*scale*y_offset), "{}".format(entry.voters[current_voter_num]),
                    fill=colors['text_white'], font=fonts['awarded_pts'])

        # Draw a dividing line between entries
        if current_entry + 1 != left_column and current_entry + 1 != contest.num_entries:
            draw.line((10 * scale + x_offset, 120 * scale + 30 * scale * y_offset, 10 * scale + rectangle_width + x_offset,
                       120 * scale + 30 * scale * y_offset), fill=colors['text_grey'], width=1)
        if current_entry + 1 == contest.num_entries and left_column != contest.num_entries/2:
            draw.line((10 * scale + x_offset, 120 * scale + 30 * scale * y_offset, 10 * scale + rectangle_width + x_offset,
                   120 * scale + 30 * scale * y_offset), fill=colors['text_grey'], width=1)

    img = img.resize((int(image_width/2), int(image_height/2)), Image.ANTIALIAS)
    img.save('{}/{} - {}.png'.format('Output', current_voter_num + 1, safe_voter_name))


# Generates a summary image for the contest results inspired by Google's Material Design design guidelines
def generate_summary(contest, sorted_data, colors):
    create_output_dir()
    flags = load_country_mappings()
    safe_contest_name = safe_file_name(contest.name)
    scale = 4

    fonts = load_fonts(scale)

    image_size = determine_image_size(fonts, contest, scale, contest.num_voters-1)
    image_width, image_height = image_size[0]
    rectangle_width = image_size[1]
    flag_offset = image_size[2]
    entry_size = image_size[3]
    user_size = image_size[4]

    img = Image.new('RGBA', size=(image_width, image_height))
    draw = ImageDraw.Draw(img)

    # Background rectangle for scoreboard
    draw.rectangle(((0,0), (image_width, image_height)), fill=colors['light_grey'])

    # Voting Top Bar
    draw.rectangle(((0,0), (image_width, 21*scale)), fill=colors['main'])
    draw.text((5*scale, 3*scale), "Final Results", fill=colors['text_white'], font=fonts['voter_header'])
    # Contest Name Top Bar
    draw.rectangle(((0, 20*scale), (image_width, 65*scale)), fill=colors['accent'])
    draw.text((24 * scale, 31 * scale), "{} Results".format(contest.name), fill=colors['text_white'], font=fonts['header'])

    # Determine number of entries to place on left column of scoreboard
    left_column = int(contest.num_entries/2) + contest.num_entries%2

    # Background rectangles for the two columns
    draw.rectangle(((10*scale, 90*scale), (10*scale + rectangle_width, 90*scale+30*scale*left_column)),
                fill=colors['white'], outline=colors['text_grey'])
    draw.rectangle(((20*scale+rectangle_width, 90*scale), (20*scale + 2*rectangle_width, 90*scale+30*scale*left_column)),
                fill=colors['white'], outline=colors['text_grey'])

    # Now place each entry onto the scoreboard
    for current_entry in range(contest.num_entries):
        if current_entry < left_column:
            x_offset = 0
            y_offset = current_entry
        else:
            x_offset = 10*scale + rectangle_width
            y_offset = current_entry - left_column

        entry = sorted_data[current_entry]

        if contest.display_flags:
            try:
                category = flags[entry.country]['category']
                country_iso = flags[entry.country]['alpha-2']

                flag = Image.open('Resources/Flags/{}/{}.png'.format(category, country_iso), 'r')
                flag_width, flag_height = flag.size

                if flag_width < flag_height:
                    flag = flag.resize((int((float(flag_width) / flag_height) * 20 * scale), 20 * scale), Image.ANTIALIAS)
                elif flag_width == flag_height:
                    flag = flag.resize((20 * scale, 20 * scale), Image.ANTIALIAS)
                else:
                    flag = flag.resize((20 * scale, int((float(flag_height) / flag_width) * 20 * scale)), Image.ANTIALIAS)
                flag = ImageOps.expand(flag, border=1, fill=colors['text_grey'])

                img.paste(flag, (int(20 * scale + 10 * scale - flag.width / 2.0) + x_offset,
                                 int(95 * scale + 10 * scale - flag.height / 2.0 + 30 * y_offset * scale)))

            except IndexError:
                country_iso = ""

            except KeyError:
                country_iso = ""

        # Display either the entry artist's country of origin or the user's name
        if contest.display_countries:
            country_string = entry.country
        else:
            country_string = entry.user
        draw.text((20*scale+x_offset+flag_offset, 93*scale+30*scale*y_offset), country_string,
                fill=colors['text_caption'], font=fonts['country'])

        # Display the entry's artist and song title
        draw.text((20*scale+x_offset+flag_offset, 105.5*scale+30*scale*y_offset), "{} - {}".format(entry.artist, entry.song),
                fill=colors['black'], font=fonts['country'])

        # Display the total points the entry received
        draw.rectangle(((20*scale+x_offset+flag_offset+max(entry_size[0],user_size[0])+10*scale, 95*scale+30*scale*y_offset),
                (20*scale+x_offset+flag_offset+max(entry_size[0],user_size[0])+10*scale+27*scale,
                 95*scale+30*scale*y_offset+20*scale)), fill=colors['main'])
        total_size = draw.textsize("{}".format(entry.display_pts), font=fonts['total_pts'])
        draw.text((20*scale+x_offset+flag_offset+max(entry_size[0],user_size[0])+10*scale+(27/2.0)*scale-(total_size[0]/2.0),
                97.5*scale+30*scale*y_offset), "{}".format(entry.display_pts), fill=colors['text_white'], font=fonts['total_pts'])

        # Display the place the entry came in
        draw.rectangle(((20 * scale + x_offset + flag_offset + max(entry_size[0], user_size[0]) + 10 * scale + 27 * scale,
                95 * scale + 30 * scale * y_offset), (20 * scale + x_offset + flag_offset +
                max(entry_size[0], user_size[0]) + 10 * scale + 27 * scale + 23 * scale, 95 * scale + 30 * scale * y_offset +
                20 * scale)), fill=colors['accent'])
        place_size = draw.textsize("{}".format(current_entry+1), font=fonts['awarded_pts'])
        draw.text((20 * scale + x_offset + flag_offset + max(entry_size[0], user_size[0]) + 10 * scale + 27 * scale +
                (22/2.0) * scale - (place_size[0] / 2.0), 97.5 * scale + 30 * scale * y_offset),
                "{}".format(current_entry+1), fill=colors['text_white'], font=fonts['awarded_pts'])

        # Draw a dividing line between entries
        if current_entry + 1 != left_column and current_entry + 1 != contest.num_entries:
            draw.line((10 * scale + x_offset, 120 * scale + 30 * scale * y_offset, 10 * scale + rectangle_width + x_offset,
                       120 * scale + 30 * scale * y_offset), fill=colors['text_grey'], width=1)
        if current_entry + 1 == contest.num_entries and left_column != contest.num_entries / 2:
            draw.line((10 * scale + x_offset, 120 * scale + 30 * scale * y_offset, 10 * scale + rectangle_width + x_offset,
                   120 * scale + 30 * scale * y_offset), fill=colors['text_grey'], width=1)

    img = img.resize((int(image_width/2), int(image_height/2)), Image.ANTIALIAS)
    img.save('{}/{} - Summary.png'.format('Output', safe_contest_name))