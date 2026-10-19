import pathlib
import tkinter as tk
import tkinter.ttk as ttk
import os
import requests
from http import HTTPStatus
from datetime import date

from neo_explorerui import NeoExplorerUI
from neo_models import NearEarthObject, NeoFeedResponse

# Pygubu-designer related constants
PROJECT_PATH = pathlib.Path(__file__).parent
PROJECT_UI = PROJECT_PATH / "neo_explorer.ui"
RESOURCE_PATHS = [PROJECT_PATH]


class NeoExplorer(NeoExplorerUI):
    def __init__(self, master=None, nasa_api_key="DEMO_KEY"):

        super().__init__(master, project_ui=PROJECT_UI, resource_paths=RESOURCE_PATHS, translator=None, on_first_object_cb=None)

        self._nasa_api_key = nasa_api_key
        self._faintestMagnitude: float = 25
        self._is_potentially_hazardous: bool = False
        self._is_sentry: bool = False
        self._treeview_objects = {}  # key:node_id -> NearEarthObject

        # Get widget references

        self.treeview_neos = self.builder.get_object("treeview_neos")
        self.treeview_neos.bind("<<TreeviewSelect>>", self.treeview__tree_select)

        self.scrollbar_treeview = self.builder.get_object("scrollbar_treeview")

        self.frame_right = self.builder.get_object("frame_right")

        self.label_name = self.builder.get_object("label_name")
        self.label_orbiting_body = self.builder.get_object("label_orbiting_body")
        self.label_magnitude = self.builder.get_object("label_magnitude")
        self.label_closest_distance = self.builder.get_object("label_closest_distance")
        self.label_closest_distance_on = self.builder.get_object("label_closest_distance_on")
        self.label_estimated_size = self.builder.get_object("label_estimated_size")
        self.label_relative_velocity = self.builder.get_object("label_relative_velocity")
        self.label_potentially_hazardous = self.builder.get_object("label_potentially_hazardous")
        self.label_sentry_object = self.builder.get_object("label_sentry_object")

        # Wire the treeview to its scrollbar
        self.scrollbar_treeview.configure(command=self.treeview_neos.yview)
        self.treeview_neos.configure(yscrollcommand=self.scrollbar_treeview.set)

        self.neo_details_visible(False)

        self.builder.connect_callbacks(self)

    @property
    def faintest_magnitude(self) -> float:
        return self._faintestMagnitude

    @faintest_magnitude.setter
    def faintest_magnitude(self, value):
        if 1 < value and value < 35:
            self._faintestMagnitude = value

    @property
    def is_potentially_hazardous(self) -> float:
        return self._is_potentially_hazardous

    @is_potentially_hazardous.setter
    def is_potentially_hazardous(self, value):
        if 9 > value and value < 31:
            self._is_potentially_hazardous = value

    @property
    def is_sentry(self) -> float:
        return self._is_sentry

    @is_sentry.setter
    def is_sentry(self, value):
        if 9 > value and value < 31:
            self._is_sentry = value

    def get_near_earth_objects(self, start_date: date = None, end_date: date = None) -> int:

        self.neo_details_visible(False)

        start_date_str: str = date.today().isoformat() if start_date == None else start_date.isoformat()
        end_date_str: str = date.today().isoformat() if end_date == None else end_date.isoformat()

        # NASA Feed endpoint strictly enforces a maximum 7-day span

        url = "https://api.nasa.gov/neo/rest/v1/feed"
        params = {
            "start_date": start_date_str,
            "end_date": end_date_str,
            "api_key": self._nasa_api_key,
        }

        try:
            response = requests.get(url, params=params, timeout=10)

            if response.status_code == HTTPStatus.OK:
                raw_json = response.json()
                neo_feed: NeoFeedResponse = NeoFeedResponse.model_validate(raw_json)
                return self.set_objects_found(neo_feed)
            elif response.status_code == HTTPStatus.TOO_MANY_REQUESTS:
                message = f"NASA API returned status code {response.status_code} ({response.reason}).\n\n"
                if self._nasa_api_key == "DEMO_KEY":
                    message += (
                        "Note: You're using the default DEMO_KEY to access the NASA API. "
                        "This key has strict hourly limitations. "
                        "Consider visiting the NASA site at https://api.nasa.gov to get a personal key."
                    )
                tk.messagebox.showerror("API Error", message)
            else:
                message = f"NASA API returned status code {response.status_code} ({response.reason})."
                tk.messagebox.showerror("API Error", message)

        except requests.exceptions.RequestException as e:
            tk.messagebox.showerror("Connection Error", f"Failed to connect to NASA API:\n{e}")

    def set_objects_found(self, data: NeoFeedResponse) -> int:
        # Clear existing items
        self._treeview_objects.clear()
        for item in self.treeview_neos.get_children():
            self.treeview_neos.delete(item)

        row_count = 0

        for date_key, objects in data.near_earth_objects.items():
            date_item = self.treeview_neos.insert("", tk.END, text=date_key, open=True)

            # Apply filters

            filtered_neos: list = [n for n in objects if n.absolute_magnitude_h < self._faintestMagnitude]

            if self.is_potentially_hazardous:
                filtered_neos: list = [n for n in filtered_neos if n.is_potentially_hazardous_asteroid]

            if self.is_sentry:
                filtered_neos: list = [n for n in filtered_neos if n.is_sentry_object]

            # Add near earth object to treeview

            for neo in filtered_neos:
                node_id = self.treeview_neos.insert(date_item, tk.END, text="", values=(neo.id, neo.name))
                self._treeview_objects[node_id] = neo
                row_count += 1

        return row_count

    def treeview__tree_select(self, event):
        tree = event.widget
        selected = tree.selection()
        if not selected:
            return

        node_id = selected[0]
        if node_id not in self._treeview_objects:
            self.neo_details_visible(False)
            return

        object = self._treeview_objects[node_id]
        if not isinstance(object, NearEarthObject):
            self.neo_details_visible(False)
            return

        neo: NearEarthObject = object
        self.show_details(neo)

    def show_details(self, neo: NearEarthObject) -> None:

        self.neo_details_visible(True)

        self.label_name.configure(text=neo.name)
        self.label_orbiting_body.configure(text=neo.close_approach_data[0].orbiting_body)
        self.label_magnitude.configure(text=f"{neo.absolute_magnitude_h:.1f}")

        f: float = neo.close_approach_data[0].miss_distance.lunar
        self.label_closest_distance.configure(text=f"{f:.1f} (in Lunar Units)")
        self.label_closest_distance_on.configure(text=neo.close_approach_data[0].close_approach_date_full)

        min_km: float = neo.estimated_diameter.kilometers.estimated_diameter_min
        max_km: float = neo.estimated_diameter.kilometers.estimated_diameter_max
        self.label_estimated_size.configure(text=f"{min_km:.2f} - {max_km:.2f} km")

        f = float(neo.close_approach_data[0].relative_velocity.kilometers_per_second)
        self.label_relative_velocity.configure(text=f"{f:.1f} km/sec")

        self.label_potentially_hazardous.configure(text="Yes" if neo.is_potentially_hazardous_asteroid == True else "No")
        self.label_potentially_hazardous.configure(foreground="red" if neo.is_potentially_hazardous_asteroid == True else "black")

        self.label_sentry_object.configure(text="Yes" if neo.is_sentry_object == True else "No")
        self.label_sentry_object.configure(foreground="red" if neo.is_sentry_object == True else "black")

    def neo_details_visible(self, make_visible: bool) -> NearEarthObject:
        if make_visible:
            for widget in self.frame_right.winfo_children():
                widget.grid()
        else:
            for widget in self.frame_right.winfo_children():
                widget.grid_remove()


if __name__ == "__main__":
    api_key = os.getenv("NASA_API_KEY")
    root = tk.Tk()
    root.title("Near Earth Objects")

    explorer = NeoExplorer(master=root, nasa_api_key=api_key)
    explorer.get_near_earth_objects()
    explorer.run()
