import os

from tasks import scrap_tv_show

if not "TV_SHOW" in os.environ:
    print("TV_SHOW is not set, exiting...")
    quit()

if not "XDD_SESSION" in os.environ:
    print("XDD_SESSION is not set, exiting...")
    quit()

scrap_tv_show(os.environ.get("TV_SHOW"), os.environ.get("XDD_SESSION"))
