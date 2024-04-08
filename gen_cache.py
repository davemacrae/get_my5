#!/usr/bin/python

#pylint: disable=missing-function-docstring, missing-module-docstring, line-too-long, missing-class-docstring

import sys
import sqlite3
from sqlite3 import Error
import argparse
from pathlib import Path

from httpx import Client

import jmespath

class Show:
    def __init__(self, title: str, url: str, alt_title: str):
        self.title = title
        self.url = url
        self.alt_title = alt_title

def create_connection(args):
    ''' Connect to database.
        If a database name is provided then attempt to connect to it
        If the --create flag has been passed then explicitly create a new DB 
        or zero out (by deletion) an existing one.

        If no db name has been provided and the --create option isn't given, try
        to create a new DB in the usual places.
    '''
    if args.db:
        try:
            cache_db = Path(args.db)
            if not cache_db.is_file() and not args.create:
                print (f"{cache_db} does not exist, use --create to create it")
                sys.exit(-1)

            if cache_db.is_file() and args.create:
                cache_db.unlink()
            return sqlite3.connect(cache_db)
        except Error as e:
            print(f"{e} DB File is {cache_db}")
            sys.exit()

    home_dir = Path.home()
    cache_db = home_dir / ".config" / "get_my5" / "cache.db"
    if not cache_db.is_file() and not args.create:
        print (f"Default DB, {cache_db}, does not exist, use --create to create it")
        sys.exit(-1)

    try:
        cache_db.parent.mkdir(parents=True, exist_ok=True)
        return sqlite3.connect(cache_db)
    except PermissionError:
        print (f"You don't have permission to create the directory {cache_db.parent}")
        sys.exit(-1)
    except Error as e:
        print(f"{e} - DB File is {cache_db}")
        sys.exit(-1)

def create_database(con):

    cur = con.cursor()

    sql = '''
    CREATE TABLE IF NOT EXISTS shows(
        rowid INTEGER PRIMARY KEY AUTOINCREMENT,
        id INT,
        title VARCHAR,
        alt_title VARCHAR,
        genre VARCHAR,
        sub_genre VARCHAR,
        synopsis VARCHAR,
        UNIQUE(id)
    );
    '''
    cur.execute(sql)
    sql = '''
    CREATE TABLE IF NOT EXISTS seasons(
        rowid INTEGER PRIMARY KEY AUTOINCREMENT,
        id INT,
        season_number INT,
        season_name VARCHAR,
        numberOfEpisodes INT,
        UNIQUE(id)
    );
    '''
    cur.execute(sql)
    sql = '''
    CREATE TABLE IF NOT EXISTS episodes(
        rowid INTEGER PRIMARY KEY AUTOINCREMENT,
        id INT,
        title VARCHAR,
        episode_name VARCHAR,
        episode_number INT,
        episode_description VARCHAR,
        episode_url VARCHAR,
        UNIQUE(episode_url)
    );
    '''
    cur.execute(sql)
    return cur

def get_all_shows(con):
    ''' Perform a keyword search on the Channel 5 site '''

    cur = create_database(con)

    client = Client(
        headers={
            'user-agent': 'Dalvik/2.9.8 (Linux; U; Android 9.9.2; ALE-L94 Build/NJHGGF)',
            'Host': 'corona.channel5.com',
            'Origin': 'https://www.channel5.com',
            'Referer':'https://www.channel5.com/',
        })

    url = "https://corona.channel5.com/shows/search.json?platform=my5desktop&friendly=1"
    try:
        response = client.get(url, timeout=30)
    except KeyboardInterrupt:
        print ("Interrupted - No data committed")
        sys.exit(-1)

    myjson = response.json()

    show_data = jmespath.search("""
                            shows[].{
                                id: id,
                                title: title,
                                alt_title: f_name,
                                synopsis: s_desc,
                                genre: genre,
                                sub_genre: primary_vod_genre
                            } 
                          """,  myjson)

    for _, show in enumerate(show_data):
        sql = f'''INSERT OR IGNORE INTO shows(id, title, alt_title, genre, sub_genre, synopsis) VALUES (
                    {show['id']},
                    "{show['title']}",
                    "{show['alt_title']}",
                    "{show['genre']}",
                    "{show['sub_genre']}",
                    "{show['synopsis']}"
                    )'''
        cur.execute(sql)

        get_seasons(cur, client, show)

    con.commit()
    con.close()
    return

def get_seasons(cur, client, show) -> None:

    url =f"https://corona.channel5.com/shows/{show['alt_title']}/seasons.json?platform=my5desktop&friendly=1"
    try:
        response = client.get(url, timeout=30)
    except KeyboardInterrupt:
        print ("Interrupted - No data committed")
        sys.exit(-1)
    myjson = response.json()

    season_data = jmespath.search("""
                        seasons[].{
                            season_number: seasonNumber,
                            season_name: sea_f_name,
                            numberOfEpisodes: numberOfEpisodes
                        } 
                        """,  myjson)
    for _, season in enumerate(season_data):
        sql = f'''INSERT OR IGNORE INTO seasons(id, season_number, season_name, numberOfEpisodes) VALUES (
                    {show['id']},
                    "{season['season_number']}",
                    "{season['season_name']}",
                    "{season['numberOfEpisodes']}"
                    )'''
        cur.execute(sql)
        if season['season_number']:
            get_episodes(cur, client, show, season)
        else:
            get_one_off(cur, show)

def get_one_off (cur, show) -> None:

    url = f"https://www.channel5.com/show/{show['alt_title']}"
    if not show['synopsis']:
        show['synopsis'] = "None"

    sql = f'''INSERT OR IGNORE INTO episodes (id, title, episode_description, episode_number, episode_url) VALUES (
                {show['id']},
                '{show['title'].replace("'", "''")}',
                '{show['synopsis'].replace("'", "''")}',
                0,
                '{url}'
    )'''
    cur.execute(sql)

def get_episodes (cur, client, show, season) -> None:

    episode_url = f"https://corona.channel5.com/shows/{show['alt_title']}/seasons/{season['season_number']}/episodes.json?platform=my5desktop&friendly=1&linear=true"

    try:
        response = client.get(episode_url, timeout=30)
    except KeyboardInterrupt:
        print ("Interrupted - No data committed")
        sys.exit(-1)

    myjson = response.json()
    results = jmespath.search("""
                    episodes[*].{
                    title: title,
                    episode_name: f_name,
                    ep_num: ep_num,
                    ep_description: s_desc
                    } """,  myjson)
    for _, value in enumerate(results):
        url = f'''{show['alt_title']}/{season['season_name']}/{value['episode_name']}'''
        sql = f'''INSERT OR IGNORE INTO episodes (id, title, episode_name, episode_number, episode_description, episode_url) VALUES (
                {show['id']},
                '{value['title'].replace("'", "''")}',
                '{value['episode_name'].replace("'", "''")}',
                {value['ep_num']},
                '{value['ep_description'].replace("'", "''")}',
                '{url}'
        )'''
        cur.execute(sql)

    return

def arg_parser():

    ''' Process the command line arguments '''

    parser = argparse.ArgumentParser(description="Channel 5 Cache Builder.")
    parser.add_argument(
        "--db",
        help="Database name"
    )
    parser.add_argument(
        "--create",
        help="Create a new cache database",
        default=False,
        action="store_true",
    )

    args = parser.parse_args()

    return args

def main() -> None:

    args = arg_parser()

    con = create_connection(args)

    get_all_shows(con)

    sys.exit(0)

if __name__ == '__main__':
    main()
