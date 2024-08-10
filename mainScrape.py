import requests
from bs4 import BeautifulSoup
import re
import pandas as pd
import csv
import time

# clean the text content
def clean_cell(cell):
    if cell:
        # if info in the cell is listed, get the items individually
        list_items = cell.find_all('li')
        if list_items:
            # separate the listed items with commas
            text = ', '.join(item.get_text(strip=True) for item in list_items)
        else:

            text = ' '.join(cell.stripped_strings)

        # remove the hyperlink boxes
        text = re.sub(r'\[\d+\]', '', text)
        return text.strip()
    return ''

start=time.time()
fp = open('dramas.csv', 'r', encoding='utf-8', )
reader = csv.reader(fp)

cast = {}
intel = {}

next(reader)

for line in reader:
    print(line)

    url = line[1]
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')

    # info box on right side of wiki that has basic info about drama
    infobox = soup.find('table', {'class': 'infobox'})

    # get the info from each
    info = {}
    for row in infobox.find_all('tr'):
        header = row.find('th')
        if header:
            key = clean_cell(header)
            value = row.find('td') if row.find('td') else ''
            value = clean_cell(value)
            info[key] = value

    # i only care about these topics
    desired_keys = ["Genre", "Created by", "Written by", "Directed by"]

    # get info box specifics
    for key in desired_keys:
        if key in info:

            # split incase the things were listed
            infokeylist = info[key].split(',')
            if key in intel:
                for i in infokeylist:

                    # update the intel dict with the info
                    if i in intel[key]:
                        intel[key][i] += 1
                    else:
                        intel[key][i] = 1
            else:
                intel[key] = {}
                for i in infokeylist:
                    intel[key][i] = 1

    # get the cast header
    cast_header = soup.find(id='Cast')
    if cast_header is None:
        cast_header = soup.find(id='Cast_and_characters')
    if cast_header is None:
        cast_header = soup.find(id='Cast_members')

    # walk through the cast list
    cast_list = cast_header.find_all_next('li')

    actor_list = []
    for item in cast_list:
        text = item.get_text(strip=True)

        # only want actor name
        if 'as' in text:

            text = text.split('[')[0].strip()

            # usually the line has actor "as" character so we stop there
            # causes issues with people with "as" in their name, but since its kdrama this isn't common
            actor = text.split('as')[0].strip()

            # majority of actors in these shows will not have this long name
            # will probably indicate a bug
            if len(actor) < 17:
                actor_list.append(actor)
        else:
            break

    # remove dupes
    actor_list = list(set(actor_list))
    print(actor_list)

    # update the actors dict
    for actor in actor_list:
        if actor in cast:
            cast[actor] += 1
        else:
            cast[actor] = 1

# print(cast)

# make separate dfs for each internal dict (stat)
for key, inner_dict in intel.items():
    df = pd.DataFrame([(subkey, value) for subkey, value in inner_dict.items()], columns=[key, 'Count'])

    # sort the dfs by the count
    df.sort_values(by=['Count'], ascending=False, inplace=True)
    file_name = f"{key.replace(' ', '_').lower()}_data.csv"

    # put dataframe in csv
    df.to_csv(file_name, index=False)
    print(f"Dataframe 'df' saved as '{file_name}'.")

df2 = pd.DataFrame(list(cast.items()), columns=['Actors', 'Count'])
df2.sort_values(by=['Count'], ascending=False, inplace=True)

# put cast data frame in csv
df2.to_csv('cast_data.csv', index=False)

print("Dataframe 'df2' saved as 'cast_data.csv'.")
end = time.time()
print(f"Execution time: {(end - start).__round__()} seconds.")