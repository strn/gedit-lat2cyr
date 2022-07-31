# -*- coding: utf-8 -*-

import logging, sys
from . import serbcyr
import gi

gi.require_version('Gtk', '3.0')
gi.require_version('Gedit', '3.0')
from gi.repository import GObject, Gio, Gtk, Gedit

try:
    import gettext
    gettext.bindtextdomain('gedit-plugins')
    gettext.textdomain('gedit-plugins')
    _ = gettext.gettext
except:
    _ = lambda s: s


logging.basicConfig(
    format='%(asctime)s %(levelname)5s - %(message)s',
    datefmt="%Y-%m-%d %H:%M:%S",
    encoding='utf-8',
    level=logging.INFO,
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)


class Lat2CyrAppActivatable(GObject.Object, Gedit.AppActivatable):
    app = GObject.Property(type=Gedit.App)

    def __init__(self):
        GObject.Object.__init__(self)

    def do_activate(self):
        # https://docs.gtk.org/gtk4/func.accelerator_parse.html
        self.app.add_accelerator("<Alt>Y", "win.lat2cyr", None)
        self.app.add_accelerator("<Alt>X", "win.cyr2lat", None)
        logging.debug(f"{__name__} app: plugin activated")

    def do_deactivate(self):
        self.app.remove_accelerator("win.lat2cyr", None)
        self.app.remove_accelerator("win.cyr2lat", None)
        logging.debug(f"{__name__} app: plugin deactivated")


class Lat2CyrWindowActivatable(GObject.Object, Gedit.WindowActivatable):

    window = GObject.Property(type=Gedit.Window)

    def __init__(self):
        GObject.Object.__init__(self)


    def do_activate(self):
        action = Gio.SimpleAction(name="lat2cyr")
        action.connect('activate', lambda a, p: self.lat2cyr())
        self.window.add_action(action)

        action = Gio.SimpleAction(name="cyr2lat")
        action.connect('activate', lambda a, p: self.cyr2lat())
        self.window.add_action(action)


    def do_deactivate(self):
        self.window.remove_action("lat2cyr")
        self.window.remove_action("cyr2lat")


    def do_update_state(self):
        view = self.window.get_active_view()
        enable = view is not None and view.get_editable()
        logging.debug(f"{__name__} win: do_update_state - enable={enable}")
        self.window.lookup_action("lat2cyr").set_enabled(enable)
        self.window.lookup_action("cyr2lat").set_enabled(enable)


    def lat2cyr(self):
        view = self.window.get_active_view()
        if view and hasattr(view, "lat2cyr_view_activatable"):
            view.lat2cyr_view_activatable.lat2cyr(view.get_buffer())


    def cyr2lat(self):
        view = self.window.get_active_view()
        if view and hasattr(view, "lat2cyr_view_activatable"):
            view.lat2cyr_view_activatable.cyr2lat(view.get_buffer())


class Lat2CyrViewActivatable(GObject.Object, Gedit.ViewActivatable):

    view = GObject.property(type=Gedit.View)

    def __init__(self):
        self.popup_handler_id = 0
        self.cyr = serbcyr.SerbCyr()
        GObject.Object.__init__(self)


    def do_activate(self):
        self.view.lat2cyr_view_activatable = self
        self.popup_handler_id = self.view.connect('populate-popup', self.populate_popup)


    def do_deactivate(self):
        if self.popup_handler_id != 0:
            self.view.disconnect(self.popup_handler_id)
            self.popup_handler_id = 0
        delattr(self.view, "lat2cyr_view_activatable")


    def populate_popup(self, view, popup):
        if not isinstance(popup, Gtk.MenuShell):
            return

        item = Gtk.SeparatorMenuItem()
        item.show()
        popup.append(item)

        item = Gtk.MenuItem.new_with_mnemonic(_("_Latin To Cyryllic"))
        item.set_sensitive(self.is_enabled())
        item.show()
        item.connect('activate', lambda i: self.lat2cyr(view.get_buffer()))
        popup.append(item)

        item = Gtk.MenuItem.new_with_mnemonic(_('_Cyrillic To Latin'))
        item.set_sensitive(self.is_enabled())
        item.show()
        item.connect('activate', lambda i: self.cyr2lat(view.get_buffer()))
        popup.append(item)


    def is_enabled(self):
        document = self.view.get_buffer()
        if document is None:
            return False
        start = None
        end = None
        try:
            start, end = document.get_selection_bounds()
        except:
            pass
        return start is not None and end is not None


    def do_update_state(self):
        # Called whenever the view has been updated
        pass


    def lat2cyr(self, document):
        start, end = document.get_selection_bounds()
        text = document.get_text(start, end, False)
        #logging.debug(f"{__name__} view: lat2cyr text='{text}'")
        document.begin_user_action()
        document.delete(start, end)
        document.insert(start, self.cyr.text_to_cyrillic(text))
        document.end_user_action()


    def cyr2lat(self, document):
        start, end = document.get_selection_bounds()
        text = document.get_text(start, end, False)
        #logging.debug(f"{__name__} view: cyr2lat text='{text}'")
        document.begin_user_action()
        document.delete(start, end)
        document.insert(start, self.cyr.text_to_latin(text))
        document.end_user_action()
