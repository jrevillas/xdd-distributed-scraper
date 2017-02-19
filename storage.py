import os

from pymongo import MongoClient

client = MongoClient(os.environ.get("MONGODB_URI"))
db = client[os.environ.get("MONGODB_DATABASE")]

def add_season(tv_show_name):
    collection = db["xdd_tv_shows"]
    tv_show = collection.find_one({"name": tv_show_name})
    tv_show["seasons"].append([])
    collection.replace_one({"_id": result["_id"]}, result)

def create_tv_show(tv_show_name):
    collection = db["xdd_tv_shows"]
    collection.insert_one({
        "name": tv_show_name,
        "seasons": [[]]})

def get_tv_show(tv_show_name):
    collection = db["xdd_tv_shows"]
    tv_show = collection.find_one({"name": tv_show_name})
    if tv_show is not None:
        return tv_show
    create_tv_show(tv_show_name)
    return get_tv_show(tv_show_name)
