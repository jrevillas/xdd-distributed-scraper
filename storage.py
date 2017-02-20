import os

from pymongo import MongoClient

if not "MONGODB_URI" in os.environ:
    print("MONGODB_URI is not set, exiting...")
    quit()

if not "MONGODB_DATABASE" in os.environ:
    print("MONGODB_DATABASE is not set, exiting...")
    quit()

client = MongoClient(os.environ.get("MONGODB_URI"))
db = client[os.environ.get("MONGODB_DATABASE")]

episodes = db["xdd_episodes"]
tv_shows = db["xdd_tv_shows"]

def add_episode(tv_show_name):
    episode_id = episodes.insert_one({"mirrors": []}).inserted_id
    tv_show = get_tv_show(tv_show_name)
    tv_show["seasons"][len(tv_show["seasons"]) - 1].append({
        "id": episode_id,
        "name": ""})
    update_tv_show(tv_show)

def add_season(tv_show_name):
    tv_show = get_tv_show(tv_show_name)
    tv_show["seasons"].append([])
    update_tv_show(tv_show)

def create_tv_show(tv_show_name):
    tv_shows.insert_one({
        "name": tv_show_name,
        "seasons": [[]]})

def get_episode(tv_show_name, season_number, episode_number):
    season_index = season_number - 1
    episode_index = episode_number - 1
    tv_show = get_tv_show(tv_show_name)
    if season_index - len(tv_show["seasons"]) == 0:
        add_season(tv_show_name)
        return get_episode(tv_show_name, season_number, episode_number)
    if episode_index - len(tv_show["seasons"][season_index]) == 0:
        add_episode(tv_show_name)
        return get_episode(tv_show_name, season_number, episode_number)
    episode_id = tv_show["seasons"][season_index][episode_index]["id"]
    return episodes.find_one({"_id": episode_id})

def get_tv_show(tv_show_name):
    tv_show = tv_shows.find_one({"name": tv_show_name})
    if tv_show is not None:
        return tv_show
    create_tv_show(tv_show_name)
    return get_tv_show(tv_show_name)

def update_episode(episode):
    episodes.replace_one({"_id": episode["_id"]}, episode)

def update_tv_show(tv_show):
    tv_shows.replace_one({"_id": tv_show["_id"]}, tv_show)
