# NeoExplorer_Python

A Python desktop app that shows **NEOs** (Near-Earth Objects, e.g. asteroids) approaching our planet on a given date.

## Features

- Great Tkinter project for getting started with asteroid and near-earth object exploration.
- No API key needed for quick use. Get a free API key from NASA for longer use.
- Shows all detected celestial objects approaching the earth on a given day.
- Uses the online NASA NEO API.
- Requires only two Python packages: *requests* and *pydantic*.
- Works with Python 3.10 and above.

The following figure shows NeoExplorer in action.

<img width="802" height="532" alt="image" src="https://github.com/user-attachments/assets/2300ded9-a6de-4667-a137-0a766e48b698" />

*Figure 1* - The app showing celestial objects and their properties. 

## The UI Layout

There are two classes that form the UI: the main window and the NeoExplorer control hosted inside it.
The main window UI uses Tkinter Frames for its layout, as shown in the following figure.

<img width="779" height="506" alt="image" src="https://github.com/user-attachments/assets/867b9d2a-e7e4-4d46-8c77-433d05050d50" />

*Figure 2* - The main form hosting the NeoExplorer control.

The Frames use the Pack Manager for their layout, as shown in the figure.

The NeoExplorer control is a separate class with its own internal layout, as shown in the next figure.

<img width="735" height="478" alt="image" src="https://github.com/user-attachments/assets/ca7d81e4-bb73-489f-a1d4-2b25b5b898b0" />

*Figure 3* - The UI of the NeoExplorer control.

The layout of the NeoExplorer is considerably more complicated than the main form. The reason is the use of a Tkinter Paned_Window which hosts two Panes divided by a splitter.
The left pane in turn hosts a frame with a Treeview and a vertical Scrollbar.

## How it Works
The main form of the app is just used to setup the layout and handle user interactions with the UI controls. The start and end dates default to covering yesterday and today. The NASA service rejects requests that cover more than seven days. By clicking the **Search for Objects** button the app queries the NASA online service at ```api.nasa.gov/neo``` to get a list of NEOs in the given period.

By default, all the NEOs whose magnitude (brightness) is below the given value are displayed. Note that counterintuitively, brightness increases with lower values in magnitude. 
<br><br>
You can further filter the results by checking the **Potentially Hazardous** and **Sentry Objects** checkboxes. NASA tags asteroids like this:

1. *Potentially Hazardous*. A NEO that comes within 7.5 million kilometers of Earth's orbit and has an absolute magnitude under 22 (making its diameter at least 140 meters).
2. *Sentry Objects*. A NEO tagged in NASA's *Sentry* system, an automated collision-monitoring system. Sentry objects are considered to possibly hit the Earth in the next 100 years.

The following figure shows the sequence diagram of the overall system.

<img width="729" height="534" alt="image" src="https://github.com/user-attachments/assets/273b9477-e2d9-4763-aba6-f6f30a686ced" />

*Figure 4* - The sequence diagram of the app.

The following listing shows the highlights of the code for app's main window.

```python
imports ...

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
        return date.strptime(yyyymmdd.strip(), "%Y-%m-%d")

    def get_faintest_magnitude(self) -> int:
        try:
            return int(self.spinbox_faintest_magnitude.get())
        except ValueError:
            return 0  # invalid value

    def set_busy_cursor(self, is_busy: bool) -> None:
        # ...

    def show_statusbar_message(self, message: str) -> None:
        self.label_statusbar_message.config(text=message)
        self.label_statusbar_message.update_idletasks()


if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()  # hide root window
    app = NeoExplorerApp(root)
    app.run(center=True)
```
*Listing 1* - The code for the main form, which hosts NeoExplorer.

The interesting stuff is primarily in class NeoExplorer, which fills most of the main form's surface. NeoExplorer handles the download and display of the NEO data. The download of data is achieved with code like this:

```python
   def get_near_earth_objects(self, start_date: date = None, end_date: date = None) -> int:

        start_date_str: str = date.today().isoformat() if start_date == None else start_date.isoformat()
        end_date_str: str = date.today().isoformat() if end_date == None else end_date.isoformat()

        url = "https://api.nasa.gov/neo/rest/v1/feed"
        params = {
            "start_date": start_date_str,
            "end_date": end_date_str,
            "api_key": self._nasa_api_key,
        }

        response = requests.get(url, params=params, timeout=10) # get the data from NASA

        if response.status_code == HTTPStatus.OK:
            raw_json = response.json()
            neo_feed: NeoFeedResponse = NeoFeedResponse.model_validate(raw_json)
            return self.set_objects_found(neo_feed)  # populate Treeview with results
        else:
          return 0
```
*Listing 2* - The code related to the retrieval of NEO data.

The NASA API requires an api key with each request. You can use the default key "DEMO_KEY" for limited use but if you exceed NASA's hourly threshold you'll start seeing HTTP error "429 (Too Many Requests)". 
To avoid this problem, go to ```api.nasa.gov``` and get a free personal key. You can use this key in two different ways:

1. By saving the key as a system Environment variable. This way you don't have to embed the key in your code. This is the approach I took. I used the variable name "NASA_API_KEY".
2. By embedding the key directly in the source code in the NeoExplorerApp __init__ method. Replace the line:

```python
  self.api_key = os.getenv("NASA_API_KEY")
```
with the line:

```python
  self.api_key.ApiKey = <your-api-key>;
```

## Handling the NEO Response Data
NASA returns the NEO data in JSON format. I could have consumed this data directly, using methods in the ```json``` module to extract the various pieces of NEO data. 
This works okay for simple JSON responses. For more complex data, it is easier to deserialize the JSON into Python objects, often called *Models* or *DTOs* (Data Transfer Objects). 
I used Google Gemini to generate the Model classes for me. The prompt was:

```Create Python classes I can use to deserialize the JSON code returned by api.nasa.gov/neo/rest/v1/feed```. 

Gemini produced the following code:

```python
import pydantic
from typing import List, Dict

class NeoFeedResponse(pydantic.BaseModel):
    element_count: int
    near_earth_objects: Dict[str, List[NearEarthObject]]
    
class NearEarthObject(pydantic.BaseModel):
    id: str
    name: str
    absolute_magnitude_h: float
    is_potentially_hazardous_asteroid: bool
    is_sentry_object: bool
    estimated_diameter: EstimatedDiameter
    close_approach_data: List[CloseApproachData]
    
class CloseApproachData(pydantic.BaseModel):
    close_approach_date: str
    close_approach_date_full: str
    relative_velocity: RelativeVelocity
    miss_distance: MissDistance
    orbiting_body: str

class DiameterRange(pydantic.BaseModel):
    #...

class EstimatedDiameter(pydantic.BaseModel):
    #...

class RelativeVelocity(pydantic.BaseModel):
    #...

class MissDistance(pydantic.BaseModel):
    #...
```
*Listing 3* - The Model classes used to handle the NASA API's response JSON.

In the interest of brevity, I commented out the lower level classes.
<br>

## Displaying the NEO Data
After downloading and deserializing the data into the various classes shown above, it is displayed in the Tkinter Treeview, which ends up looking something like this:

<img width="288" height="386" alt="image" src="https://github.com/user-attachments/assets/9dc40a97-bbbf-4867-95ed-45b2cb7f0e8f" />

*Figure 5* - The Treeview, showing NEOs grouped by date.

The code to populate the Treeview is shown in the following listing.

```python
class NeoExplorer(NeoExplorerUI):
    #...

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
```

*Listing 4* - Populating the Treeview with data grouped by date.

Selecting a NEO in the Treeview fires a ```tree_select``` event that handles the display of relevant NEO properties like this:

```python
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
```
*Listing 5* - Showing the details of a selected NEO.

# Designing the UI with Visual Designer

If your app has a very simple UI, you can just use straight Python to add and position the various UI controls. For more complicated UIs you should be using a drag-and-drop visual designer tool. 
There are several out there, such as PyQt, PAGE and Pygubu Designer. For this project I used the latter. It's a Tkinter-based open-source app hosted on GitHub at 
```https://github.com/alejandroautalan/pygubu-designer```. 
The latest version has some bugs but works well enough to get the job done.
The following figure shows Pygubu Designer while editing the main window of NeoExplorerApp.

<img width="1483" height="758" alt="image" src="https://github.com/user-attachments/assets/c12afbbd-3ffd-4c6c-a149-8f2a4fb7d4c8" />

*Figure 6* - Editing the main windows of NeoExplorerApp using Pygubu Designer.

When you click the **Save** button, the designer saves the layout in an XML file named after the Pygubu Designer project file. 
For a project file named ```neo_explorer_app.py```, the XML is saved in the file ```neo_explorer_app.ui```.
The **Build Code** button creates a python script that reads the XML layout file and builds the corresponding UI at runtime. The following figure shows the class hierarchy of the app class.

<img width="396" height="249" alt="image" src="https://github.com/user-attachments/assets/d5c66ef0-0a74-49e8-a1b9-22e4f90b3901" />

*Figure 7* - The UI base class of NeoExplorerApp that builds the UI at runtime.

The following figure shows Pygubu Designer while editing the NeoExplorer control UI.

<img width="1368" height="758" alt="image" src="https://github.com/user-attachments/assets/e448c410-f949-40eb-a2b5-d778d3a0ad81" />

*Figure 8* - Editing the NeoExplorer control UI using Pygubu Designer.

Just like NeoExplorerApp, NeoExplorer will have a UI base class that builds the control's UI at runtime.

That's basically it! Two main classes: NeoExplorerApp and NeoExplorer. Pretty straightforward.

## Acknowlegements

Many thanks to Google Gemini for the generation of the Model classes.
