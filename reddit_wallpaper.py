#!/bin/python3



##################################
# CONFIGURATION - Edit this part #
##################################
subreddits = "EarthPorn+BotanicalPorn+WaterPorn+SeaPorn+SkyPorn+DesertPorn+LakePorn"; #Subreddits to pull from. Seperate each with a plus sign.
link_file = "~/.background" #Where to put link to most recently-fetched wallpaper
wallpaper_folder = "~/Pictures/Backgrounds" #Folder to download to
command = ['feh', '--bg-fill', link_file] #Replace this with the command you use to set your desktop background, split into each component argument/part
          #GNOME : ['gsettings', 'set', 'org.gnome.desktop.background', 'picture-uri', 'file://' + link_file]
          #Mac : ['osascript', '-e', 'tell application "Finder" to set desktop picture to POSIX file "' + link_file + '"']
min_width = 1600
min_height = 900





##############################################
# THE REST OF THIS DOESN'T NEED TO BE EDITED #
##############################################
import subprocess
import json
import sys
import os

wallpaper_folder = os.path.expanduser(wallpaper_folder)
subprocess.run(["mkdir", wallpaper_folder], stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)

print("Fetching listing from http://api.reddit.com/r/" + subreddits + "/top\n")
try:
    reddit = json.loads(subprocess.run(['curl', '-A', "Mozilla/5.0 (X11; Linux x86_64; rv:74.0) Gecko/20100101 Firefox/74.0", "https://api.reddit.com/r/EarthPorn/top"], stdout=subprocess.PIPE).stdout.decode('utf-8'))
except:
    print("\n\n\nFailed to load Reddit. Please check your internet connection and try again.")
    sys.exit(0)

print("\n\nSearching for image with height of at least " + str(min_height) + " and width of at least " + str(min_width) + "\n")
try:
    startAt = int(sys.argv[1])
except:
    startAt = 0
num = -1
for x in reddit["data"]["children"]:
    num = num + 1
    if(startAt > 0):
        startAt = startAt-1
        continue
    image = x["data"]["preview"]["images"][0]["source"]
    if(int(image["width"]) >= min_width and int(image["height"]) >= min_height and image["height"] <= image["width"]):
        break
    else:
        image = None

try:
    url = str(image["url"])
except:
    print("\n\n\nFailed to find image of the specified size. Please try again later.")
    sys.exit(0)

#Print some data about the image
print("\n\nImage found!")
print("\nNumber " + str(num))
print(x["data"]["title"])
print("Width: " + str(image["width"]) + " Height: " + str(image["height"]))
print("URL: " + url)
print("\n")

subprocess.run(['rm', os.path.expanduser(link_file) + '_bak'], stdout=subprocess.PIPE)
subprocess.run(['mv', os.path.expanduser(link_file), os.path.expanduser(link_file) + '_bak'], stdout=subprocess.PIPE)
title = str(x["data"]["url"].split("/")[-1])

subprocess.run(['curl', x["data"]["url"], '-o', wallpaper_folder + "/" + title], stdout=subprocess.PIPE)
subprocess.run(['ln','-s', wallpaper_folder + "/" + title, os.path.expanduser(link_file)], stdout=subprocess.PIPE)


command2 = []
for x in command:
    command2.append(x.replace(link_file,wallpaper_folder + "/" + title))


subprocess.run(command2, stdout=subprocess.PIPE)
