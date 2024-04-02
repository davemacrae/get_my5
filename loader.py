#!/usr/bin/python

#pylint: disable=missing-function-docstring, missing-module-docstring, line-too-long, missing-class-docstring

# import os
import sys
import json
import sqlite3
from sqlite3 import Error
import re

from termcolor import colored
from httpx import Client

from beaupy import confirm, select #, select_multiple
from beaupy.spinners import Spinner, DOTS
from rich.console import Console
import jmespath

class Show:
    def __init__(self, title: str, url: str, alt_title: str):
        self.title = title
        self.url = url
        self.alt_title = alt_title

console = Console()

def create_connection():
    conn = None
    try:
        conn = sqlite3.connect(':memory:')
    except Error as e:
        print(e)
    return conn

def create_database():
    con = create_connection()
    cur = con.cursor()

    sql = '''
    CREATE TABLE IF NOT EXISTS videos(
    rowid INTEGER PRIMARY KEY AUTOINCREMENT,
    series VARCHAR,
    episode VARCHAR,
    url VARCHAR,
    UNIQUE (url) 
    );
    '''
    cur.execute(sql)
    return con, cur

def get_next_data(show: Show):

    con, cur = create_database()

    # get seasons list
    client = Client(
    headers={
        'user-agent': 'Dalvik/2.9.8 (Linux; U; Android 9.9.2; ALE-L94 Build/NJHGGF)',
        'Host': 'corona.channel5.com',
        'Origin': 'https://www.channel5.com',
        'Referer':'https://www.channel5.com/',
    })

    response = client.get(show.url)
    if response.status_code == 200:
        myjson = json.loads(response.content)
    else:
        print (f"Response gave an error {response.status_code} \n {response.content}")
        sys.exit(0)

    res = jmespath.search("""
            seasons[*].{
            seasonNumber: seasonNumber,
            sea_f_name: sea_f_name
            } """,  myjson)

    beaupylist = []
    # create list of season urls to get episodes
    # for i in range seasons
    urllist = []

    for i, value in enumerate(res):
        if value['seasonNumber'] is None:
            value['seasonNumber'] = '0'
        if  value['sea_f_name'] is None:
            value['sea_f_name'] = "unknown"

        urllist.append(f"https://corona.channel5.com/shows/{show.alt_title}/seasons/{value['seasonNumber']}/episodes.json?platform=my5desktop&friendly=1&linear=true")

    allseries = []
    totalvideos = 0

    # For each season, grab the list of episodes
    for url in urllist:
        response = client.get(url)
        if response.status_code == 200:
            myjson = response.json()
        else:
            print (f"Response gave an error {response.status_code} \n {response.content}")
            sys.exit(0)
        # odd case has nill results
        # question episodes
        MOVIE = False
        results = jmespath.search("""
                        episodes[*].{
                        title: title,
                        sea_f_name: sea_f_name,
                        f_name: f_name,
                        sea_num: sea_num,
                        ep_num: ep_num                         
                        } """,  myjson)
        if results == []: # there are no seasons, it's just a single show
            headers = {
                'Accept': 'application/json, text/plain, */*',
                'Host': 'corona.channel5.com',
                'Origin': 'https://www.channel5.com',
                'Referer': 'https://www.channel5.com/',
            }
            url = f"https://corona.channel5.com/shows/{show.alt_title}/episodes/next.json?platform=my5desktop&friendly=1"
            response = client.get(url, headers=headers)
            if response.status_code == 200:
                myjson = response.json()
                # console.print_json(data = myjson)
                results = jmespath.search("""
                    {
                    title: sh_title,
                    sh_f_name: sh_f_name,
                    f_name: f_name,
                    ep_num: ep_num                         
                    } """,  myjson)
                MOVIE = True
            else:
                print (f"Response gave an error {response.status_code} \n {response.content}")
                sys.exit(0)

        if MOVIE:
            url = f"https://www.channel5.com/show/{results['sh_f_name']}/"
            infoline = "[info] Detected a single Movie; downloading directly\n\n"
            print(colored(infoline, 'green'))
            print(f"Get {url}")
#           my5.main(url)
            sys.exit(0)

        for i, value in enumerate(results):
            totalvideos += 1
            url = f"https://www.channel5.com/show/{show.alt_title}/{value['sea_f_name']}/{value['f_name']}"
            print(f"{value['sea_num']}\t{value['ep_num']}\t{url}")
            sql = f''' INSERT OR IGNORE INTO videos(series, episode, url) VALUES('{value['sea_num']}','{value['ep_num']}','{url}');'''
            allseries.append(value['sea_num'])
            cur.execute(sql)

    while True:
        if totalvideos <= 16:
            search = '0'
            break
        unique_list = list(dict.fromkeys(allseries))
        print("[info] Series found are:-")
        for item in unique_list:
            print(item, end = ' ')
        print("\n[info]There are over 16 videos to display.\nEnter the series number(s) to see a partial list,\n\
        or enter '0' to show all episodes available\n\n\
        Separate series numbers with a space \n")
        search = input("? ")
        if not re.match("^[0-9 ]+$", search):
            print ("Use only numbers and Spaces!")
        else:
            break

    if search == '0':
        cur.execute("SELECT * FROM videos")

    elif not isinstance(search, int):
        srchlist = search.split(' ')
        partsql = "SELECT * FROM videos WHERE series='"
        for srch in srchlist:
            partsql = f"{partsql}{srch}' OR series='"
        partsql = partsql.rstrip(" OR series='")
        sql = partsql + "';"
        cur.execute(sql)

    else:
        search = "Series " + search
        cur.execute("SELECT * FROM videos WHERE series=?", (search,))
    rows = cur.fetchall()
    if len(rows)==0:
        print("[info] No series of that number found. Exiting. Check and try again. ")
    con.close()
    beaupylist = []
    index = []
    inx = 0
    for col in rows:
        beaupylist.append(f"{col[1]} {col[2]} {col[3]}")
        index.append(inx)
        inx+=1
    return index, beaupylist

def keywordsearch(search) -> Show:
    ''' Perform a keyword search on the Channel 5 site '''

    client = Client(
        headers={
            'user-agent': 'Dalvik/2.9.8 (Linux; U; Android 9.9.2; ALE-L94 Build/NJHGGF)',
            'Host': 'corona.channel5.com',
            'Origin': 'https://www.channel5.com',
            'Referer':'https://www.channel5.com/',
        })

    url = f"https://corona.channel5.com/shows/search.json?platform=my5desktop&friendly=1&query={search}"
    response = client.get(url)
    myjson = response.json()

    res = jmespath.search("""
                            shows[].{
                                title: title,
                                slug: f_name,
                                synopsis: s_desc
                            } 
                          """,  myjson)
    show_list = []
    beaupylist = []
    for i in range(0 ,len(res)): #pylint: disable=consider-using-enumerate
        slug = res[i]['slug']
        #title = slug.replace('-', '_').title()
        url =f"https://corona.channel5.com/shows/{slug}/seasons.json?platform=my5desktop&friendly=1"

        #url = rinseurl(url)
        synopsis = res[i]['synopsis']
        strtuple = f"{res[i]['title']}\t{synopsis}"
        beaupylist.append(strtuple)
        show_list.append(Show(res[i]['title'], url, slug))
    # spinner.stop()

    # if there is only one show found then there is no point in doing a selection
    found_show = []
    if beaupylist:
        if len(beaupylist) > 1:
            found = select(beaupylist)
            if found:
                found_title = found.split('\t')[0]
                found_show = [show for show in show_list if show.title == found_title][0]
        else:
            found_show = show_list[0]

    return found_show


def main() -> None:

    search = input("Search word(s)? ")

    show = keywordsearch(search)
    if not show: #
        print(f"[info] Nothing found for {search}")
        sys.exit()

    print(f"[info] getting data for {show.title}")

    index, beaupylist = get_next_data(show)
#     dir = "\nUse up/down keys + spacebar to de-select or re-select videos to download\n"
#     print(colored(dir, 'red'))
#     links = select_multiple(beaupylist, ticked_indices=index,  minimal_count=1,
#            page_size=30, pagination=True)
#     for link in links:
#         url = link.split(' ')[2]
#         print(url)
# #        my5.main(url)
###############################################################################################
# The beaupy module that produces checkbox lists seems to clog and confuse my linux box's terminal;
# I do a reset after downloading.
# if that is not what you want, as it may remove any presets, comment out the 'if' phrase below
# Note: Only resets unix boxes
###############################################################################################
#     if os.name == 'posix':
#         spinner = Spinner(CLOCK, "[info] Preparing to reset Terminal...")
#         spinner.start()
#         time.sleep(5)
#         spinner.stop()
#         os.system('reset')


if __name__ == '__main__':
    main()
