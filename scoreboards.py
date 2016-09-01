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
    fonts['voter_header'] = ImageFont.truetype("Resources/Fonts/RobotoCondensed-Regular.ttf", 12*scale, encoding="unic")
    fonts['header'] = ImageFont.truetype("Resources/Fonts/RobotoCondensed-Bold.ttf", 21 * scale, encoding="unic")
    fonts['country'] = ImageFont.truetype("Resources/Fonts/RobotoCondensed-Regular.ttf", 10 * scale, encoding="unic")
    fonts['awarded_pts'] = ImageFont.truetype("Resources/Fonts/RobotoCondensed-Light.ttf", 14 * scale, encoding="unic")
    fonts['total_pts'] = ImageFont.truetype("Resources/Fonts/RobotoCondensed-Bold.ttf", 14 * scale, encoding="unic")
    return fonts


def load_colors(main_color="#FFFFFF", accent_color="#FFFFFF"):
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
    voter_header_size = draw.textsize('Now Voting: {} ({}/{})'.format(contest.voters[current_voter_num], current_voter_num+1, contest.num_voters), font=fonts['voter_header'])
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
    image_width = max(max((20*scale + rectangle_width)), (48*scale + header_size[0]), (10*scale + voter_header_size[0]))
    image_height = scale*(90 + 30*(int(contest.num_entries/2) + contest.num_entries%2) + 20)

    return (image_width, image_height)


# Generates a scoreboard image that is inspired by Google's Material Design design guidelines
def generate_scoreboard(contest, sorted_data, current_voter_num):
    create_output_dir()
    flags = load_country_mappings()
    safe_voter_name = safe_file_name(contest.voters[current_voter_num])
    scale = 4

    fonts = load_fonts(scale)
    colors = load_colors()

    (image_width, image_height) = determine_image_size(fonts, contest, scale, current_voter_num)
    img = Image.new('RGBA', size=(image_width, image_height))
    draw = ImageDraw.Draw(img)