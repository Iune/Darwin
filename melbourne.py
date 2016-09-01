import argparse
import csv
import scoreboards

class Contest:
    def __init__(self, name, data, voters, display_flags, display_countries):
        self.name = name
        self.data = data
        self.voters = voters
        self.display_flags = display_flags
        self.display_countries = display_countries

        self.num_voters = len(self.voters)
        self.num_entries = len(self.data)

class Entry:
    def __init__(self, user, country, artist, song, voters):
        self.user = user
        self.country = country
        self.artist = artist
        self.song = song
        self.voters = voters

        # total_pts is the one used when sorting
        # display_pts is the one displayed on the scoreboards
        # When an entry is disqualified, total_pts != display_pts (we want to sort the entry last, but display the points it got)
        self.total_pts = 0
        self.display_pts = 0

        self.num_voters = 0
        self.disqualified = False


# Load the CSV data from file
def load_data(file_location):
    data = []

    # Identify the delimiter used in the CSV file
    with open(file_location, encoding='utf8') as file:
        sniffer = csv.Sniffer()
        dialect = sniffer.sniff(file.readline())
        delimiter = dialect.delimiter

    with open(file_location, encoding='utf8') as file:
        reader = csv.reader(file, delimiter=delimiter)
        for row in reader:
            # Ignore the first column when importing CSV data
            data.append(row[1:])

    return data


# Format the raw CSV data and create an instance of the Contest class
def create_contest(args, data):
    formatted_data = []

    # We want to format the table rows into an easily searchable dictionary
    for row in data[1:]:
        formatted_data.append(Entry(row[0].strip(), row[1].strip(), row[2].strip(), row[3].strip(), row[5:]))

    voters = data[0][5:]
    return Contest(args.contest_name, formatted_data, voters, args.flags, args.countries)


# Add current voter's votes and return the sorted data
def process_voter(contest, current_voter_num):
    for row in contest.data:
        if row.voters[current_voter_num].upper() == 'DQ':
            row.disqualified = True
            row.total_pts = -1
        try:
            points = int(row.voters[current_voter_num])
            # Don't add to total_pts if the entry is disqualified
            if not row.disqualified:
                row.total_pts += points

            row.display_pts += points
            row.num_voters += 1
        except ValueError:
            continue
    # Sort by total_pts then display_pts, number of voters and finally artist name
    return sorted(contest.data, key=lambda k: (-k.total_pts, -k.display_pts, -k.num_voters, k.artist.lower()))


def print_leaders(sorted_data):
    place = 1
    for entry in sorted_data:
        if place == 6:
            break

        print("{:1}: {:3} pts. | {} - {} ({})".format(place, entry.display_pts, entry.artist, entry.song, entry.user))
        place += 1


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("file_location", help="Input CSV file location")
    parser.add_argument("contest_name", help="Contest name")
    parser.add_argument("-f", "--flags", action="store_true", help="Display flags in the scoreboards?")
    parser.add_argument("-c", "--countries", action="store_true", help="Display artists' countries of origin in the scoreboards?")
    parser.add_argument("--main", dest="main_color", help="Main color used in the scoreboards (Default: #2f292b")
    parser.add_argument("--accent", dest="accent_color", help="Accent color used in the scoreboards (Default: #009688")
    args = parser.parse_args()

    data = load_data(args.file_location)
    contest = create_contest(args, data)

    if args.main_color != None and args.accent_color != None:
        colors = scoreboards.load_colors(main_color=args.main_color, accent_color=args.accent_color)
    elif args.main_color == None and args.accent_color != None:
        colors = scoreboards.load_colors(accent_color=args.accent_color)
    elif args.main_color != None and args.accent_color == None:
        colors = scoreboards.load_colors(main_color=args.main_color)
    else:
        colors = scoreboards.load_colors()

    for current_voter_num in range(contest.num_voters):
        sorted_data = process_voter(contest, current_voter_num)

        print("\nGenerating Scoreboard {}/{} (Voter: {})".format(current_voter_num+1, contest.num_voters, contest.voters[current_voter_num]))
        print("       ---- Top 5 ----")
        print_leaders(sorted_data)
        scoreboards.generate_scoreboard(contest, sorted_data, current_voter_num, colors)
    scoreboards.generate_summary(contest, sorted_data, colors)

if __name__ == "__main__":
    main()