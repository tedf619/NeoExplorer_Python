#!/usr/bin/python3
"""
NeoExplorerApp

Hosts the NeoExplorer control

UI source file: neo_explorer_app.ui
"""

import pathlib
import tkinter as tk
from tkinter import messagebox
import tkinter.ttk as ttk
import os
from datetime import date, timedelta
from neo_explorer_appui import NeoExplorerAppUI
from neo_explorer import NeoExplorer

# Pygubu Designer related constants
PROJECT_PATH = pathlib.Path(__file__).parent
PROJECT_UI = PROJECT_PATH / "neo_explorer_app.ui"
RESOURCE_PATHS = [PROJECT_PATH]


class NeoExplorerApp(NeoExplorerAppUI):
    def __init__(self, root, master=None):
        super().__init__(
            master,
            project_ui=PROJECT_UI,
            resource_paths=RESOURCE_PATHS,
            translator=None,
            on_first_object_cb=None,
        )
        self.root = root
        self.builder.connect_callbacks(self)

        self.api_key = os.getenv("NASA_API_KEY")

        # get widget references

        self.entry_start_date = self.builder.get_object("entry_start_date")
        self.entry_end_date = self.builder.get_object("entry_end_date")

        self.spinbox_faintest_magnitude = self.builder.get_object("spinbox_faintest_magnitude")

        self.checkbutton_potentially_hazardous = self.builder.get_object("checkbutton_potentially_hazardous")
        self.is_potentially_hazardous = self.builder.get_variable("is_potentially_hazardous")  # variable bound to checkbutton

        self.checkbutton_sentry_objects = self.builder.get_object("checkbutton_sentry_objects")
        self.sentry_objects = self.builder.get_variable("sentry_objects")  # variable bound to checkbutton

        self.button_search_for_objects = self.builder.get_object("button_search_for_objects")

        self.frame_middle = self.builder.get_object("frame_middle")

        self.label_statusbar_message = self.builder.get_object("label_statusbar_message")

        # initialize widgets

        yesterday = date.today() - timedelta(days=1)
        self.set_entry_text(self.entry_start_date, yesterday.isoformat())

        self.set_entry_text(self.entry_end_date, date.today().isoformat())

        self.spinbox_faintest_magnitude.set(25)
        self.is_potentially_hazardous.set(0)
        self.sentry_objects.set(0)

        self.button_search_for_objects.config(command=self.button_search_for_objects__click)

        # add NEO Explorer widget to UI

        self.neo_explorer = NeoExplorer(self.frame_middle, nasa_api_key=self.api_key)
        self.frame_middle.pack(expand=True, fill=tk.BOTH)

        # wrap up initialization...

        self.set_panel_middle_visible(False)
        self.show_statusbar_message("Perform a Search to see results")

    def set_entry_text(self, entry_control: tk.Entry, text: str) -> None:
        entry_control.delete(0, tk.END)
        entry_control.insert(0, text)

    def button_search_for_objects__click(self):
        start_date: date = self.get_date_from_yyyymmdd(self.entry_start_date.get())
        end_date: date = self.get_date_from_yyyymmdd(self.entry_end_date.get())

        if start_date == None or end_date == None:
            messagebox.showerror("Error", "The search dates are invalid.")
            return

        search_period_days = (end_date - start_date).days

        if search_period_days > 7:
            messagebox.showerror("Invalid Dates", "The date range must be less than 7 days.")
            return

        # Set filters
        self.neo_explorer.faintest_magnitude = self.get_faintest_magnitude()
        self.neo_explorer.is_potentially_hazardous = self.is_checked(self.checkbutton_potentially_hazardous)
        self.neo_explorer.is_sentry = self.is_checked(self.checkbutton_sentry_objects)

        self.set_panel_middle_visible(False)  # hide Objects Found frame
        self.set_busy_cursor(True)
        self.show_statusbar_message("Searching...")

        objectsFound: int = self.neo_explorer.get_near_earth_objects(start_date, end_date)

        self.set_panel_middle_visible(True)  # show Objects Found frame

        self.show_statusbar_message(f"Objects found: {objectsFound}")
        self.set_busy_cursor(False)

    def is_checked(self, checkbutton: tk.CheckButton) -> bool:
        return checkbutton.instate(["selected"])

    def set_panel_middle_visible(self, isVisible: bool) -> None:
        if isVisible:
            self.frame_middle.pack(fill=tk.BOTH, expand=True)
        else:
            self.frame_middle.pack_forget()

    def get_date_from_yyyymmdd(self, yyyymmdd: str) -> date:
        try:
            return date.strptime(yyyymmdd.strip(), "%Y-%m-%d")
        except ValueError as e:
            print(f"Error parsing date '{yyyymmdd}': {e}")
            return None

    def get_faintest_magnitude(self) -> int:
        try:
            return int(self.spinbox_faintest_magnitude.get())
        except ValueError:
            return 0  # invalid value

    def set_busy_cursor(self, is_busy: bool) -> None:
        if is_busy:
            self.set_cursor_recursively(self.root, "watch")
        else:
            self.set_cursor_recursively(self.root, "")

        self.root.update_idletasks()

    def set_cursor_recursively(self, widget, cursor_name: str) -> None:
        try:
            widget.config(cursor=cursor_name)
        except tk.TclError:
            pass  # Skip widgets that don't support cursors

        for child in widget.winfo_children():
            self.set_cursor_recursively(child, cursor_name)

    def show_statusbar_message(self, message: str) -> None:
        self.label_statusbar_message.config(text=message)
        self.label_statusbar_message.update_idletasks()


if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()  # hide root window
    app = NeoExplorerApp(root)
    app.run(center=True)
