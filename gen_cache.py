#!/usr/bin/python

#pylint: disable=missing-function-docstring, missing-module-docstring, line-too-long, missing-class-docstring

import sys
import sqlite3
from sqlite3 import Error

from httpx import Client

import jmespath

class Show:
    def __init__(self, title: str, url: str, alt_title: str):
        self.title = title
        self.url = url
        self.alt_title = alt_title

def create_connection():
    conn = None
    try:
        conn = sqlite3.connect('fred.db')
    except Error as e:
        print(e)
    return conn

def create_database():
    con = create_connection()
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
        numberOfEpisodes INT
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
        episode_url VARCHAR
    );
    '''
    cur.execute(sql)
    return con, cur

def get_all_shows():
    ''' Perform a keyword search on the Channel 5 site '''

    con, cur = create_database()

    client = Client(
        headers={
            'user-agent': 'Dalvik/2.9.8 (Linux; U; Android 9.9.2; ALE-L94 Build/NJHGGF)',
            'Host': 'corona.channel5.com',
            'Origin': 'https://www.channel5.com',
            'Referer':'https://www.channel5.com/',
        })

    url = "https://corona.channel5.com/shows/search.json?platform=my5desktop&friendly=1"
    response = client.get(url, timeout=30)
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
    response = client.get(url, timeout=30)
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

def get_one_off (cur, show):

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

def get_episodes (cur, client, show, season):

    episode_url = f"https://corona.channel5.com/shows/{show['alt_title']}/seasons/{season['season_number']}/episodes.json?platform=my5desktop&friendly=1&linear=true"
    response = client.get(episode_url)
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


def main() -> None:

    get_all_shows()
    sys.exit()

if __name__ == '__main__':
    main()
