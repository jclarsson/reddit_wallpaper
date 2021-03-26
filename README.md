# reddit_wallpaper


## Reddit Wallpaper Fetcher
Usage: python3 reddit_wallpaper.py

**Dependencies:**
* Python 3
* Python requests
   * Install with pip install requests
   * Install on Debian, Arch, and Fedora as python-requests
* Python Gobject
   * Install on Debian as pygobject
   * Install on Arch and Fedora as python-gobject
   * Install on Mac with "brew install pygobject3"
* GTK 3
   * Install on Debian as gtk+3.0
   * Install on Arch and Fedora as gtk3
   * Install on Mac with "brew install gtk+3 adwaita-icon-theme"
   
***

Stores data in ~/.local/share/reddit_wallpaper

Directory structure:
* ~/.local/share/reddit_wallpaper
   * config.json: Stores the configuration saved through the app. It is possible, though NOT recommended, to edit this manually.
   * Wallpapers: Stores all pictures that you have downloaded and set as your wallpaper through this program. This may, over time, start to take up a lot of space, so you may want to manually delete some of the older pictures after some time.
   * Thumbnails (temporary): Stores downloaded thumbnails while the program is open. This directory is automatically deleted when the program closes, and should not appear unless it is open.

