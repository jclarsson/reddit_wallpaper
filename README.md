# reddit_wallpaper


## Reddit Wallpaper Script
Usage: ./reddit_wallpaper.py [number of posts to skip]

Optional:
* Enter an integer as an argument to this program if you
do not want to use the first wallpaper at the top of
the subreddit for today. This will skip that amount of
posts and start lower down. Whenever you run this
program, it will tell you the number assosciated with
each post. So, if it downloads a picture you aren't
very fond of, use that picture's number plus one as
the argument for this script.
* Otherwise, you may run this script with no arguments
in order to fetch the top post from today.

**Required packages:**
* python3
* curl


Most Unix systems (Mac, Linux, BSD) should already have curl, however, you should check to make sure your Python installation is up-to-date.

**Configuration:**

* **subreddits** *string*: List of subreddits to pull from. Seperate each with a plus sign

* **link_file** *string (file name and location)*: This chooses a location to place a symbolic link to your new background.
* **wallpaper_folder** *string (directory name and location)*: This chooses a location to download the wallpapers to

* **command** *array\<string\>*: The command used to set wallpapers in your OS or DE, broken up into an array. Each entry in the array should represent either the command or its arguments. For example, ["ls", "-a", "~"] would represent "ls -a ~". The file contains examples that you can use for Feh (Wallpaper setter for barebones WMs), GNOME (Desktop environment on Linux), or Mac OS X.

* **min_width** *int*: Minimum width of the image to grab from Reddit. It is recommended to set this to be the same as the width of your largest monitor.
* **min_height** *int*: Minimum height of the image to grab from Reddit. It is recommended to set this to be the same as the height of your largest monitor.
