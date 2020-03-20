#!/bin/python3

##########################################################
# Reddit Wallpaper Script                                #
# Usage: ./reddit_wallpaper.py [number of posts to skip] #
#                                                        #
# Optional:                                              #
# Enter an integer as an argument to this program if you #
# do not want to use the first wallpaper at the top of   #
# the subreddit for today. This will skip that amount of #
# posts and start lower down. Whenever you run this      #
# program, it will tell you the number assosciated with  #
# each post. So, if it downloads a picture you aren't    #
# very fond of, use that picture's number plus one as    #
# the argument for this script.                          #
# Otherwise, you may run this script with no arguments   #
# in order to fetch the top post from today.             #
#                                                        #
# Required packages:                                     #
#  * python3                                             #
#  * curl                                                #
##########################################################

# Most Unix systems (Mac, Linux, BSD) should already have curl, however, you should check to make sure your Python installation is up-to-date.




##################################
# CONFIGURATION - Edit this part #
##################################

## List of subreddits to pull from. Seperate each with a plus sign

subreddits = "EarthPorn+BotanicalPorn+WaterPorn+SeaPorn+SkyPorn+DesertPorn+LakePorn";



## Locations

link_file = "~/.background" #Where to put link to most recently-fetched wallpaper
wallpaper_folder = "~/Pictures/Backgrounds" #Folder to download wallpaper to



## Replace the command with the command you use to set your desktop background, split into each component argument/part. Examples of common commands are included below. Make sure that only ONE instance of "command = " is uncommented. Otherwise, Python will use the bottom-most instance of "command = ".

command = ['feh', '--bg-fill', link_file] 
# GNOME LINUX DE:
# command = ['gsettings', 'set', 'org.gnome.desktop.background', 'picture-uri', 'file://' + link_file]
# MAC OS X:
# command = ['osascript', '-e', 'tell application "Finder" to set desktop picture to POSIX file "' + link_file + '"']
          


#Minimum widths of images to fetch. It is recommended to set this to your display resolution so that it doesn't fetch any small, pixellated images, but you can set these to 0 to fetch images of any size.

min_width = 1600   #Should probably be the width of your display
min_height = 900   #Should probably be the height of your display















###############################################
# THE REST OF THIS DOES NOT NEED TO BE EDITED #
#     ----------------------------------      #
# If you encounter a problem, you should feel #
# free to edit the code below. However, this  #
# script is provided on an "As-is" basis      #
# without warranties or conditions of any     #
# kind, either express or implied.            #
###############################################

import subprocess
import json
import sys
import os


wallpaper_folder = os.path.expanduser(wallpaper_folder) #subprocess doesn't like the "~" symbol, so this expands it to the full path
subprocess.run(["mkdir", wallpaper_folder], stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT) #make the wallpaper directory if it doesn't already exist



print("Fetching listing from http://api.reddit.com/r/" + subreddits + "/top\n")
try:
    reddit = json.loads(subprocess.run(['curl', '-A', "Mozilla/5.0 (X11; Linux x86_64; rv:74.0) Gecko/20100101 Firefox/74.0", "https://api.reddit.com/r/EarthPorn/top"], stdout=subprocess.PIPE).stdout.decode('utf-8')) #fetch JSON from reddit
    #Reddit requires a useragent line so I just used the Firefox user agent. It really doesn't matter what the useragent is as long as it's valid.

except:
    print("\n\n\nFailed to load Reddit. Please check your internet connection and try again.")
    sys.exit(0) #Exit the program if it can't load the JSON from Reddit for whatever reason



print("\n\nSearching for image with height of at least " + str(min_height) + " and width of at least " + str(min_width) + "\n")

#If an integer is provided as a command line argument, skip that amount of posts. Otherwise, start from zero.
try:
    startAt = int(sys.argv[1])
except:
    startAt = 0

num = -1 #keeps track of the post number

#cycle through the posts until it either finds the first valid post, or until it runs out of posts
for x in reddit["data"]["children"]:
    num = num + 1 #increment post number
    if(startAt > 0):
        startAt = startAt-1
        continue  #skips the rest of the code below until the right amount of posts have been skipped

    image = x["data"]["preview"]["images"][0]["source"] #this contains metadata about the image

    if(int(image["width"]) >= min_width and int(image["height"]) >= min_height and image["height"] <= image["width"]):
        break          #end the loop if the right image has been found
    else:
        image = None   #otherwise, clear the variable storing metadata and run the loop again


#checks to see if the for loop above ended with a valid image, exits the program if it didn't
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


#these two lines remove the previous instance of ~/.background_bak and then renames the current ~/.background to ~/.background_bak. ~/.background_bak keeps track of the previously-fetched background to make it easy to rollback this script.
subprocess.run(['rm', os.path.expanduser(link_file) + '_bak'], stdout=subprocess.PIPE)
subprocess.run(['mv', os.path.expanduser(link_file), os.path.expanduser(link_file) + '_bak'], stdout=subprocess.PIPE)


title = str(x["data"]["url"].split("/")[-1]) #the name of the image and its file extension

subprocess.run(['curl', x["data"]["url"], '-o', wallpaper_folder + "/" + title], stdout=subprocess.PIPE)           #downloads the image to the backgrounds folder
subprocess.run(['ln','-s', wallpaper_folder + "/" + title, os.path.expanduser(link_file)], stdout=subprocess.PIPE) #makes a symbolic link ~/.background which points to the downloaded image


#the following is expands the symlink to its pointed-to location in order to set the desktop wallpaper. I would typically want to just set it to ~/.background instead of expanding the symlink, but Mac OS does not like setting the desktop wallpaper to a symlink.
command2 = []
for x in command:
    command2.append(x.replace(link_file,wallpaper_folder + "/" + title))



#this runs the command that sets your desktop to the new image. If you don't want the program to do this, you can just comment this line out and it will download without setting the wallpaper.
subprocess.run(command2, stdout=subprocess.PIPE)
