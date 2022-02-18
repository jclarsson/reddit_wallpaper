#!/bin/python3

import gi, os, json, threading, time, requests, subprocess, sys
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GdkPixbuf, Gio, GLib

if "requests" not in sys.modules:
    print("Error: missing dependency \"requests\". Please run \"pip3 install requests\" to fix this. Some systems may include it in their package manager as python-requests.")

if "gi" not in sys.modules:
    print("Error: missing dependency \"gi\". Please install pygobject3 and gtk+3 from your package manager.")

if ("gi" not in sys.modules) or ("requests" not in sys.modules):
    print("Unmet dependencies. Aborting now.")
    exit()


class RedditWallpaperWindow(Gtk.Window):  # Main window
    storage_directory = os.path.expanduser("~/.local/share/reddit_wallpaper")
    reddit = []
    subreddits = None
    sort = None
    wallpaper_manager = None
    min_width = None
    min_height = None

    def __init__(self):
        print("Starting Reddit Wallpaper Fetcher")

        # Initiate Gtk.Window
        Gtk.Window.__init__(self, title="Reddit Wallpaper")
        self.set_default_size(768, 512)
        self.set_icon_name("preferences-desktop-wallpaper")

        # Make sure that the storage directory is set up. This folder will contain the config.json, copies of saved/set wallpapers, as well as provide temporary storage for downloaded thumbnails.
        if not os.path.isdir(self.storage_directory):
            try:
                os.makedirs(self.storage_directory)
                print("Created new storage directory.")
            except:
                print("ERROR: Failed to make storage directory.")
                quit()
        if not os.path.isdir(self.storage_directory + "/Wallpapers"):
            try:
                os.makedirs(self.storage_directory + "/Wallpapers")
                print("Created new Wallpapers download directory. I would recommend setting up a link to this from within the Pictures folder by running \"ln -s ~/.local/share/reddit_wallpaper/Wallpapers ~/Pictures/Wallpapers\"")
            except:
                print("ERROR: Failed to make Wallpaper download directory.")
                quit()
        if not os.path.isdir(self.storage_directory + "/Thumbnails"):
            try:
                os.makedirs(self.storage_directory + "/Thumbnails")
                print("Created new Thumbnails directory")
            except:
                print("ERROR: Failed to make Thumbnails directory.")
                quit()

        # Initiate Settings object
        self.settings = Settings(self.storage_directory, self)

        # Setup left side (Main panel). It's a GtkStack with one container for the progress bar and another for the thumbnails
        self.left = Gtk.Stack()

        self.stack1 = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.stack1.set_border_width(10)
        self.progressbar = Gtk.ProgressBar()
        self.progressbar.set_text("Loading...")
        self.progressbar.set_show_text(True)
        self.stack1.pack_start(self.progressbar, True, False, 0)

        self.stack2 = Gtk.ScrolledWindow()
        self.stack2fb = Gtk.FlowBox()
        self.stack2fb.set_valign(Gtk.Align.START)
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        box.pack_start(Gtk.Label(label="    Select an icon to set your wallpaper", xalign=0), False, False, 10)
        box.pack_start(self.stack2fb, True, True, 0)
        self.stack2.add(box)

        self.stack3 = Gtk.ScrolledWindow()
        self.stack3fb = Gtk.FlowBox()
        self.stack3fb.set_valign(Gtk.Align.START)
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        box.pack_start(Gtk.Label(label="    Select an icon to set your wallpaper", xalign=0), False, False, 10)
        box.pack_start(self.stack3fb, True, True, 0)
        self.stack3.add(box)

        self.left.add_named(self.stack1, "a")
        self.left.add_named(self.stack2, "b")
        self.left.add_named(self.stack3, "c")
        self.left.set_visible_child_name("a")

        # Setup right side. This is the settings panel, and it can hide or show.
        self.right = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.right.set_border_width(10)
        self.right.set_property("width-request", 256)
        self.left.set_property("width-request", 512)

        settings_buttons = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        self.srbutton = Gtk.Button.new_with_label("Apply settings and Refresh")
        self.srbutton.connect("clicked", self.apply_settings, True)
        self.srbutton.set_sensitive(False)
        settings_buttons.pack_start(self.srbutton, True, True, 0)
        button = Gtk.Button()
        icon = Gio.ThemedIcon(name="document-save-symbolic")
        image = Gtk.Image.new_from_gicon(icon, Gtk.IconSize.BUTTON)
        button.add(image)
        button.set_tooltip_text("Save settings")
        button.connect("clicked", self.save_settings)
        settings_buttons.pack_end(button, True, True, 0)
        self.right.pack_end(settings_buttons, False, False, 0)

        self.setup_settings()

        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        hbox.pack_start(self.left, True, True, 0)
        hbox.pack_end(self.right, False, False, 0)
        self.add(hbox)

        # Setup header bar
        hb = Gtk.HeaderBar()
        hb.set_show_close_button(True)
        hb.props.title = "Reddit Wallpaper"
        if sys.platform == "linux" or sys.platform == "linux2":
            self.set_titlebar(hb)

        self.refreshbutton = Gtk.Button()
        icon = Gio.ThemedIcon(name="view-refresh-symbolic")
        image = Gtk.Image.new_from_gicon(icon, Gtk.IconSize.BUTTON)
        self.refreshbutton.add(image)
        self.refreshbutton.set_sensitive(False)
        self.refreshbutton.connect("clicked", self.refresh)
        self.refreshbutton.set_tooltip_text("Refresh wallpapers from Reddit")
        hb.pack_start(self.refreshbutton)

        self.hbsort = Gtk.ComboBoxText()

        for index, i in enumerate(self.settings.sort_types):
            self.hbsort.append_text(i)
            if i == self.settings.get("sort"):
                self.hbsort.set_active(index)
        self.hbsort.connect("changed", self.update_sort_from_hb)
        self.hbsort.set_sensitive(False)
        hb.pack_start(self.hbsort)

        button = Gtk.ToggleButton()
        icon = Gio.ThemedIcon(name="preferences-system-symbolic")
        image = Gtk.Image.new_from_gicon(icon, Gtk.IconSize.BUTTON)
        button.add(image)
        button.connect("clicked", self.on_settings_click)
        if self.settings.get("show_settings_pane") is True:
            button.set_active(True)
        button.set_tooltip_text("Configuration")
        hb.pack_end(button)

        self.recents = Gtk.Popover()
        self.recentsbox = Gtk.ScrolledWindow()
        self.recentsfb = Gtk.FlowBox()
        self.recentsfb.set_valign(Gtk.Align.START)
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        opendirbtn = Gtk.Button.new_with_label("Open wallpaper directory")
        opendirbtn.connect("clicked", self.show_dir)
        box.pack_start(self.recentsfb, True, True, 0)
        box.pack_start(opendirbtn, False, False, 10)
        self.recentsbox.add(box)
        self.recents.add(self.recentsbox)
        self.recentsbox.set_min_content_height(400)
        self.recentsbox.set_policy(hscrollbar_policy=Gtk.PolicyType.NEVER, vscrollbar_policy=Gtk.PolicyType.AUTOMATIC)
        self.recentsbox.show_all()
        self.recents.set_position(Gtk.PositionType.BOTTOM)

        button = Gtk.MenuButton(popover=self.recents)
        icon = Gio.ThemedIcon(name="document-open-recent-symbolic")
        image = Gtk.Image.new_from_gicon(icon, Gtk.IconSize.BUTTON)
        button.add(image)
        button.set_tooltip_text("Restore previously-downloaded wallpapers")
        hb.pack_end(button)

        self.show_all()
        if self.settings.get("show_settings_pane") is True:
            self.hbsort.hide()
        else:
            self.right.hide()

        t1 = threading.Thread(target=self.load)
        t1.start()

        t2 = threading.Thread(target=self.refreshRecents)
        t2.start()

    def show_dir(self, sender):
        subprocess.run(['xdg-open', self.storage_directory + "/Wallpapers/"])

    def save_settings(self, sender):
        self.apply_settings(sender, False)
        self.settings.save()

    def set_progress(self, fraction, title):
        self.progressbar.set_fraction(fraction)
        self.progressbar.set_text(title)

    def finish_load(self):
        self.left.show_all()
        self.left.set_visible_child_name("b")
        self.refreshbutton.set_sensitive(True)
        self.hbsort.set_sensitive(True)
        self.srbutton.set_sensitive(True)

    def refreshRecents(self):
        print("Refreshing recents")
        for i in self.recentsfb.get_children():
            self.recentsfb.remove(i)
        files = sorted([os.path.join(self.storage_directory + "/Wallpapers/",i) for i in os.listdir(self.storage_directory + "/Wallpapers/")], key=os.path.getmtime)[::-1]
        for entry in files:
            if (entry.endswith('.png') or entry.endswith('.jpg') or entry.endswith('.jpeg') or entry.endswith('.tif') or entry.endswith('.tiff') or entry.endswith('.gif') or entry.endswith('.webp') or entry.endswith('.bmp')):
                button = Gtk.Button()
                try:
                    pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_size(entry,200,200)

                    image = Gtk.Image().new_from_pixbuf(pixbuf)

                    button.add(image)
                except gi.repository.GLib.Error:
                    button.set_label(entry.replace(self.storage_directory + "/Wallpapers/", ""))

                button.connect("clicked", self.set_wallpaper_from_recent, entry.replace(self.storage_directory + "/Wallpapers/", ""))
                button.set_tooltip_text(entry.replace(self.storage_directory + "/Wallpapers/", ""))

                self.recentsfb.add(button)
        self.recentsfb.show_all()

    def set_wallpaper_from_recent(self, sender, title):
        self.run_wallpaper_manager(title) 

    def refresh(self, sender):
        self.refreshbutton.set_sensitive(False)
        self.hbsort.set_sensitive(False)
        self.srbutton.set_sensitive(False)
        self.left.set_visible_child_name("a")
        for i in self.stack2fb.get_children():
            self.stack2fb.remove(i)
        t1 = threading.Thread(target=self.load)
        t1.start()

    def update_sort_from_hb(self, sender):

        if self.settings.set("sort", self.hbsort.get_active_text()) is not False:
            self.refresh(sender)


    def load(self):
        GLib.idle_add(self.set_progress, 0.05, "Fetching listing from Reddit")

        try:
            if "?" in self.settings.get("sort"):
                max_listings = "&"
            else:
                max_listings = "/?"
            self.reddit = json.loads(requests.get("https://api.reddit.com/r/" + self.settings.get("subreddits") + "/" + self.settings.get("sort") + max_listings + "limit=100", headers={'User-agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:86.0) Gecko/20100101 Firefox/86.0'}).content)

        except:
            GLib.idle_add(self.set_progress, 0, "Failed to load Reddit. Please check your internet connection and try again.")
            return

        GLib.idle_add(self.set_progress, 0.25, "Searching for all matching images")

        images = []

        try:
            for index, x in enumerate(self.reddit["data"]["children"]):

                try:
                    image = x["data"]["preview"]["images"][0]["source"]  # this contains metadata about the image

                    if int(image["width"]) >= int(self.settings.get("min_width")) and int(image["height"]) >= int(self.settings.get("min_height")):  # and image["height"] <= image["width"]):
                        images.append(index)
                except KeyError:
                    print("Entry with no preview")
        except TypeError:
            GLib.idle_add(self.set_progress, 1, "Error scanning for images.")
            time.sleep(5)
            GLib.idle_add(self.finish_load)
            return
            

        GLib.idle_add(self.set_progress, 0.5, "Downloading thumbnails...")
        length = len(images)
        curr_len = 0.5
        for num in images:
            GLib.idle_add(self.set_progress, curr_len, "Downloading thumbnails... (" + str(int(((curr_len - 0.5) / 0.5) * length) + 1) + " of " + str(length) + ")")
            with open(self.storage_directory + "/Thumbnails/thumb_" + str(num), 'wb') as f:
                try:
                    f.write(requests.get(self.reddit["data"]["children"][num]["data"]["thumbnail"]).content)
                except requests.exceptions.MissingSchema:
                    print("Failed to fetch thumbnail from " + self.reddit["data"]["children"][num]["data"]["thumbnail"])
        
            GLib.idle_add(self.preview_new, num)
            curr_len += 0.5/length
        GLib.idle_add(self.finish_load)

    def preview_new(self, num):
        button = Gtk.Button()

        image = Gtk.Image().new_from_file(self.storage_directory + "/Thumbnails/thumb_" + str(num))

        button.add(image)

        button.connect("clicked", self.set_wallpaper, num)
        button.set_tooltip_text(self.reddit["data"]["children"][num]["data"]["title"])

        self.stack2fb.add(button)

    def set_wallpaper(self, button, num):
        self.left.set_visible_child_name("a")
        t1 = threading.Thread(target=self.do_set_wallpaper, args=[self, button, num])
        t1.start()

    def do_set_wallpaper(self, sender, button, num):
        GLib.idle_add(self.set_progress, 0, "Setting wallpaper")
        GLib.idle_add(self.set_progress, 0.05, "Downloading image from Reddit...")
        x = self.reddit["data"]["children"][num]

        title = str(x["data"]["url"].split("/")[-1])

        with open(self.storage_directory + "/Wallpapers/" + title, 'wb') as f:
            f.write(requests.get(x["data"]["url"]).content)
        GLib.idle_add(self.set_progress, 0.5, "Adding source to EXIF data (If exiftool is installed)")

        try:
            subprocess.run(['exiftool', '-overwrite_original', '-userComment="https://www.reddit.com' + x["data"]["permalink"] + '"', self.storage_directory + "/Wallpapers/" + title], stdout=subprocess.PIPE)

        except:
            try:
                subprocess.run(['/usr/bin/vendor_perl/exiftool', '-overwrite_original', '-userComment="https://www.reddit.com' + x["data"]["permalink"] + '"', self.storage_directory + "/Wallpapers/" + title], stdout=subprocess.PIPE)
            except:
                print("Couldn't edit exif data")

        GLib.idle_add(self.set_progress, 0.8, "Setting wallpaper")
        self.run_wallpaper_manager(title)
        time.sleep(0.25)
        GLib.idle_add(self.finish_load)
        self.refreshRecents()

    def run_wallpaper_manager(self, title):
        if self.settings.get("wallpaper_manager") == "GNOME":
            subprocess.run(['gsettings', 'set', 'org.gnome.desktop.background', 'picture-uri', 'file://' + self.storage_directory + "/Wallpapers/" + title])
        elif self.settings.get("wallpaper_manager") == "KDE":
            subprocess.run(['dbus-send', '--session', '--dest=org.kde.plasmashell', '--type=method_call', '/PlasmaShell', 'org.kde.PlasmaShell.evaluateScript',"string: \nvar Desktops = desktops(); \nfor (i=0;i<Desktops.length;i++) { \n        d = Desktops[i]; \n        d.wallpaperPlugin = \"org.kde.image\"; \n        d.currentConfigGroup = Array(\"Wallpaper\", \n                                    \"org.kde.image\", \n                                    \"General\"); \n        d.writeConfig(\"Image\", \"file://" + self.storage_directory + "/Wallpapers/" + title + "\"); \n}"])
            subprocess.run(['kwriteconfig5', '--file', 'kscreenlockerrc', '--group', 'Greeter', '--group', 'Wallpaper', '--group', 'org.kde.image', '--group', 'General', '--key', 'Image', 'file://' + self.storage_directory + "/Wallpapers/" + title])
        elif self.settings.get("wallpaper_manager") == "feh":
            subprocess.run(['feh', '--bg-fill', self.storage_directory + "/Wallpapers/" + title])
        elif self.settings.get("wallpaper_manager") == "Mac OS":
            subprocess.run(['osascript', '-e', 'tell application "Finder" to set desktop picture to POSIX file "' + self.storage_directory + "/Wallpapers/" + title + '"'])
        else:
            command = self.settings.get("wallpaper_manager")
            command = command.replace("$wallpaper", self.storage_directory + "/Wallpapers/" + title)
            subprocess.run(["bash", "-c", command])

    def setup_settings(self):
        label = Gtk.Label()
        label.set_markup("<big><b>Settings</b></big>")
        label.set_xalign(0)
        self.right.pack_start(label, False, False, 0)

        label = Gtk.Label()
        label.set_markup("<b>Subreddits</b>")
        label.set_xalign(0)
        self.right.pack_start(label, False, False, 0)

#         self.subreddits = Gtk.ListBox()
        # self.subreddits.set_selection_mode(Gtk.SelectionMode.SINGLE)
        # for i in self.settings.get("subreddits").split("+"):
        #     row = Gtk.ListBoxRow()
        #     row.add(Gtk.Label(label=i))
        #     self.subreddits.add(row)
        # self.subreddits.unselect_all()
        self.subreddits = Gtk.Entry()
        self.subreddits.set_text(self.settings.get("subreddits"))

        self.right.pack_start(self.subreddits, False, False, 0)

        label = Gtk.Label()
        label.set_markup("List of subreddits separated by a Plus (+) sign")
        label.set_xalign(0)
        label.set_line_wrap(True)
        label.set_justify(Gtk.Justification.LEFT)
        self.right.pack_start(label, False, False, 0)

        label = Gtk.Label()
        label.set_markup("<b>Sort</b>")
        label.set_xalign(0)
        self.right.pack_start(label, False, False, 0)

        self.sort = Gtk.ComboBoxText()

        for index, i in enumerate(self.settings.sort_types):
            self.sort.append_text(i)
            if i == self.settings.get("sort"):
                self.sort.set_active(index)
        self.right.pack_start(self.sort, False, False, 0)

        label = Gtk.Label()
        label.set_markup("How should Reddit sort the entries. Recommended: top/?t=week")
        label.set_line_wrap(True)
        label.set_justify(Gtk.Justification.LEFT)
        label.set_max_width_chars(34)
        label.set_xalign(0)
        self.right.pack_start(label, False, False, 0)

        label = Gtk.Label()
        label.set_markup("<b>Wallpaper Manager</b>")
        label.set_xalign(0)
        self.right.pack_start(label, False, False, 0)

        self.wallpaper_manager = Gtk.Entry()
        self.wallpaper_manager.set_text(self.settings.get("wallpaper_manager"))

        self.right.pack_start(self.wallpaper_manager, False, False, 0)

        label = Gtk.Label()
        label.set_markup("Supported values are: GNOME, KDE, Mac OS, feh, or a custom command with $wallpaper which will be filled in to be the location of the downloaded wallpaper.")
        label.set_line_wrap(True)
        label.set_max_width_chars(34)
        label.set_justify(Gtk.Justification.LEFT)
        label.set_xalign(0)
        self.right.pack_start(label, False, False, 0)

        label = Gtk.Label()
        label.set_markup("<b>Minimum Width</b>")
        label.set_xalign(0)
        self.right.pack_start(label, False, False, 0)

        self.min_width = Gtk.Entry()
        self.min_width.set_text(self.settings.get("min_width"))

        self.right.pack_start(self.min_width, False, False, 0)

        label = Gtk.Label()
        label.set_markup("Minimum width of image to search for, must be a positive integer.")
        label.set_line_wrap(True)
        label.set_justify(Gtk.Justification.LEFT)
        label.set_xalign(0)
        label.set_max_width_chars(34)
        self.right.pack_start(label, False, False, 0)

        label = Gtk.Label()
        label.set_markup("<b>Minimum Height</b>")
        label.set_xalign(0)
        self.right.pack_start(label, False, False, 0)

        self.min_height = Gtk.Entry()
        self.min_height.set_text(self.settings.get("min_height"))

        self.right.pack_start(self.min_height, False, False, 0)

        label = Gtk.Label()
        label.set_markup("Minimum height of image to search for, must be a positive integer.")
        label.set_line_wrap(True)
        label.set_justify(Gtk.Justification.LEFT)
        label.set_max_width_chars(34)
        label.set_xalign(0)
        self.right.pack_start(label, False, False, 0)

    def apply_settings(self, sender, refresh):
        returnvalues = list()
        returnvalues.append(self.settings.set("subreddits", self.subreddits.get_text()))
        returnvalues.append(self.settings.set("sort", self.sort.get_active_text()))
        returnvalues.append(self.settings.set("wallpaper_manager", self.wallpaper_manager.get_text()))
        returnvalues.append(self.settings.set("min_width", self.min_width.get_text()))
        returnvalues.append(self.settings.set("min_height", self.min_height.get_text()))
        
        if refresh is True and (not (False in returnvalues)):
            self.refresh(sender)

    def on_settings_click(self, sender):
        if sender.get_active():
            self.right.show_all()
            self.hbsort.hide()
            self.settings.set("show_settings_pane", True)
        else:
            self.right.hide()
            self.hbsort.show_all()
            self.settings.set("show_settings_pane", False)

        for index, i in enumerate(self.settings.sort_types):
            if i == self.settings.get("sort"):
                self.hbsort.set_active(index)
                self.sort.set_active(index)

    def on_close(self, args):
        with os.scandir(self.storage_directory + "/Thumbnails") as it:
            for entry in it:
                if entry.name.startswith('thumb_') and entry.is_file():
                    os.remove(self.storage_directory + "/Thumbnails/" + entry.name)
        os.rmdir(self.storage_directory + "/Thumbnails")
        print("Erased all thumbnails")
        self.save_settings(args)

        Gtk.main_quit()


class Settings:  # Settings object
    # Global variables used:
    #   default_json (string): Stores the default settings, used for creating new config.json, verifying the keys of config.json, and resetting config.json back to default.
    #   location (string): Storage location, typically ~/.local/share/reddit_wallpaper
    #   config_file (string): Full path of config.json
    #   settings (dictionary): Array containing all keys and values stored in settings
    #   default_settings (JSON Object): Default settings loaded from default_json string

    default_json = '{"subreddits": "EarthPorn+BotanicalPorn+WaterPorn+SeaPorn+SkyPorn+DesertPorn+LakePorn", "sort": "top/?t=week", "wallpaper_manager": "GNOME", "min_width": "1920", "min_height": "1080", "show_settings_pane": true}'
    settings = {}
    sort_types = ("hot", "new", "top/?t=hour", "top/?t=day", "top/?t=week", "top/?t=month", "top/?t=year", "top/?t=all", "random")

    def __init__(self, location, window):
        self.window = window
        self.location = location
        self.config_file = location + "/config.json"
        self.defualt_settings = json.loads(self.default_json)

        # Load default settings, and then replace them with all valid settings previously saved
        self.load(json.loads(self.default_json))
        try:
            with open(self.config_file) as f:
                self.load(json.load(f))
            print("Loaded existing settings file at " + self.config_file)

        except:
            print("config.json does not exist or is unreadable, loading default settings.")

    def load(self, jsondict):  # Iterates through the JSON data and runs it through self.set() in order to verify that the value is valid
        for i in jsondict:
            self.set(i, jsondict[i])

    def set(self, key, value):  # Verify the input and then set the key
        settings = self.settings
        if key == "subreddits":
            settings[key] = value
        elif key == "sort":
            if value in self.sort_types:
                settings[key] = value
            else:
                self.throw_error("Invalid value for key \"sort\".")
                return False
        elif key == "wallpaper_manager":
            if value in ("GNOME", "KDE", "feh", "Mac OS"):
                settings[key] = value
            elif '$wallpaper' in value:
                settings[key] = value
            else:
                self.throw_error("Invalid value for key \"wallpaper_manager\". Must be either GNOME, KDE, Feh, Mac OS, or a custom command using \"$wallpaper\" to replace the command's argument.")
                return False
        elif key == "min_width":
            try:
                if int(value) > 0:
                    settings[key] = value
                else:
                    self.throw_error("Invalid value for key \"min_width\". Value must be an integer above 0.")
                    return False
            except:
                self.throw_error("Invalid value for key \"min_width\". Value must be an integer above 0.")
                return False

        elif key == "min_height":
            try:
                if int(value) > 0:
                    settings[key] = value
                else:
                    self.throw_error("Invalid value for key \"min_height\". Value must be an integer above 0.")
                    return False
            except:
                self.throw_error("Invalid value for key \"min_height\". Value must be an integer above 0.")
                return False
        elif key == "show_settings_pane":
            try:
                if isinstance(value, bool):
                    settings[key] = value
                else:
                    self.throw_error("Invalid value for key \"show_settings_pane\". Value must be boolean.")
                    return False
            except:
                self.throw_error("Invalid value for key \"show_settings_pane\". Value must be boolean.")
                return False

        else:
            self.throw_error("Error: Invalid key.")
            return False
        self.settings = settings
        return True

    def get(self, key):
        return self.settings[key]

    def save(self):
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.settings, f)
            print("Saved settings to " + self.config_file)

        except:
            self.throw_error("Cannot save settings to config.json. This is bad!")

    def throw_error(self, error):  # Prints error to stdout and also show a dialog
        print(error)

        dialog = Gtk.MessageDialog(
            transient_for=self.window,
            flags=0,
            message_type=Gtk.MessageType.ERROR,
            buttons=Gtk.ButtonsType.OK,
            text="Error in settings",
        )
        dialog.format_secondary_text(
            "Error: " + error
        )
        dialog.run()

        dialog.destroy()


win = RedditWallpaperWindow()
win.connect("destroy", win.on_close)
Gtk.main()
