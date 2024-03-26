import os
import sys
import gc
import base64
import atexit
import math
import subprocess
import glob
from PySide2 import QtWidgets, QtGui, QtCore
from PySide2.QtWidgets import QSplitter, QGroupBox, QVBoxLayout, QLabel, QApplication, QComboBox 
from PySide2.QtCore import Qt
from modelChecker.modelChecker_UI import UI
from contextlib import contextmanager
import maya.cmds as cmds
import maya.mel as mel

# Paths and Directories --------------------------------------------------
ICON_DIR = r"N:\SAFE\projects_template\reference\tools\assetManager\icons"
ON_IMAGE_PATH = os.path.join(ICON_DIR, "on_switch.png")
OFF_IMAGE_PATH = os.path.join(ICON_DIR, "off_switch.png")
REFRESH_IMAGE_PATH = os.path.join(ICON_DIR, "refresh.png")

# Function to check for lingering processes --------------------------------------------------
def check_lingering_processes():
    # Get a list of all running processes in Maya
    all_processes = cmds.listProcesses()

    # Filter out the current process
    current_process = cmds.about(pid=True)
    lingering_processes = [p for p in all_processes if p != current_process]

    if lingering_processes:
        print("Lingering processes detected:")
        for process in lingering_processes:
            print(f"Process ID: {process}")
    else:
        print("No lingering processes detected.")

# Register the cleanup function
atexit.register(check_lingering_processes)

# Define the folder_depth function ---------------------------------------------------
def folder_depth(path):
    """Calculate the depth of a folder."""
    return path.count(os.path.sep)
    
# Define the open_directory context manager ---------------------------------------------------
@contextmanager
def open_directory(directory):
    current_dir = os.getcwd()
    os.chdir(directory)
    try:
        yield
    finally:
        os.chdir(current_dir)
        
# Preferences Functions --------------------------------------------------
import getpass

username = getpass.getuser()  # Get the current username

PREF_FILE_PATH = rf"C:\Users\{username}\AppData\Local\Autodesk\safe\2022\prefs\assetBrowserUserSettings.txt"

# Modify the write_preferences function to write preferences in a readable format
def write_preferences(key, value):
    PREF_FILE_PATH = rf"C:\Users\{username}\AppData\Local\Autodesk\safe\2022\prefs\assetBrowserUserSettings.txt"
    preferences = {}  # Store preferences in a dictionary

    # Read existing preferences from the file
    if os.path.exists(PREF_FILE_PATH):
        with open(PREF_FILE_PATH, 'r') as pref_file:
            for line in pref_file:
                line = line.strip()
                if line:
                    k, v = line.split(' = ')
                    preferences[k] = v

    # Update the dictionary with the new preference
    preferences[key] = value

    # Write preferences back to the file
    with open(PREF_FILE_PATH, 'w') as pref_file:
        for k, v in preferences.items():
            pref_file.write(f"{k} = {v}\n")

# Modify the read_preferences function to read preferences in a readable format
def read_preferences(key):
    PREF_FILE_PATH = rf"C:\Users\{username}\AppData\Local\Autodesk\safe\2022\prefs\assetBrowserUserSettings.txt"
    if os.path.exists(PREF_FILE_PATH):
        preferences = {}
        with open(PREF_FILE_PATH, 'r') as pref_file:
            for line in pref_file:
                parts = line.strip().split(' = ')
                if len(parts) == 2:
                    k, v = parts
                    if k == key:
                        return v
                    preferences[k] = v  # Add this line
        print("Preferences:", preferences)  # Add this line
    return None

# Function to save UI location and size to preferences on close
def save_ui_preferences(ui_location, ui_size):
    # Save UI location and size to preferences
    write_preferences('ui_width', str(ui_size.width()))
    write_preferences('ui_height', str(ui_size.height()))
    write_preferences('ui_location_x', str(ui_location.x()))
    write_preferences('ui_location_y', str(ui_location.y()))

# Function to set Asset Browser status in preferences
def set_asset_browser_status(status):
    write_preferences('Asset Browser Status', status)

# Function to get Asset Browser status from preferences
def get_asset_browser_status():
    return read_preferences('Asset Browser Status')

def restore_ui_preferences():
    ui_width_str = read_preferences('ui_width')
    ui_height_str = read_preferences('ui_height')
    ui_location_x_str = read_preferences('ui_location_x')
    ui_location_y_str = read_preferences('ui_location_y')

    if ui_width_str and ui_height_str and ui_location_x_str and ui_location_y_str:
        ui_width = int(ui_width_str)
        ui_height = int(ui_height_str)
        ui_location_x = int(ui_location_x_str)
        ui_location_y = int(ui_location_y_str)

        return QtCore.QSize(ui_width, ui_height), QtCore.QPoint(ui_location_x, ui_location_y)
    return None, None

def on_window_close(asset_browser):
    # Get the width and height of the asset_browser
    ui_size = asset_browser.size()
    ui_location = asset_browser.pos()

    # Save UI preferences
    save_ui_preferences(ui_location, ui_size)
    
    # Set Asset Browser status to closed
    set_asset_browser_status('Closed')
    
# Project Preferences Functions -------------------------------------------------- 

# New function to populate the dropdown list with available project preferences
def populate_project_dropdown(combo_box):
    project_pref_files = glob.glob(r"N:\SAFE\TOOLS\Maya\assetBrowser\PROJECTS\*_project.preference.txt")
    project_names = [os.path.splitext(os.path.basename(file))[0].split("_")[0] for file in project_pref_files]
    project_paths = [file for file in project_pref_files]
    combo_box.clear()
    combo_box.addItems(project_names)
    return dict(zip(project_names, project_paths))

# New function to handle changing project preferences
def change_project_preferences(project_name, asset_browser):
    preferences = read_project_preferences(project_name)
    if preferences:
        asset_dir = preferences.get("Work Path", "")
        publish_asset_dir = preferences.get("Publish Path", "")
        if asset_dir and publish_asset_dir:
            asset_browser.asset_dir = asset_dir
            asset_browser.publish_asset_dir = publish_asset_dir
            asset_browser.initUI()  # Update the UI based on new preferences
        else:
            print("Asset directory or publish asset directory is not set in preferences.")
    else:
        print("Project preferences not found.")
                
# New function to read project preferences


# Modify the read_project_preferences function to correctly format the paths


def read_project_preferences(project_name):
    project_preference_file = rf"N:\SAFE\TOOLS\Maya\assetBrowser\PROJECTS\{project_name}_project.preference.txt"
    if os.path.exists(project_preference_file):
        project_preferences = {}
        with open(project_preference_file, 'r') as pref_file:
            for line in pref_file:
                parts = line.strip().split(':')
                if len(parts) == 2:
                    key, value = parts[0].strip(), parts[1].strip()
                    # Normalize and replace backslashes with forward slashes
                    value = os.path.normpath(value).replace('\\', '/')
                    # Extract the drive letter using string slicing
                    drive_letter = project_preference_file[:project_preference_file.find(':')]
                    # Concatenate the drive letter with the normalized path
                    value = f"{drive_letter}:{value}"
                    project_preferences[key] = value
        print("Project preferences read successfully:", project_preferences)  # Add this line
        return project_preferences
    else:
        print("Project preferences file not found.")  # Add this line
        return None




           
# Custom folder filter ---------------------------------------------------
class CustomFileSystemModel(QtWidgets.QFileSystemModel):
    def filterAcceptsRow(self, source_row, source_parent):
        index = self.index(source_row, 0, source_parent)
        file_info = self.fileInfo(index)

        # Exclude folders starting with "_"
        if file_info.isDir() and file_info.fileName().startsWith("_", QtCore.Qt.CaseSensitive):
            return False

        return super().filterAcceptsRow(source_row, source_parent)
# Define the Work class ---------------------------------------------------
class AssetBrowser(QtWidgets.QWidget):
    def __init__(self, asset_dir, publish_asset_dir, parent=None):
        super(AssetBrowser, self).__init__(parent)
        self.asset_dir = asset_dir
        self.publish_asset_dir = publish_asset_dir
        self.levels = 6
        self.list_titles = ["Type", "Category", "Asset", "LOD", "User", "Scene"]
        self.file_views = []
        self.file_models = []  
        self.publish_dir = ""  # Add a new attribute for publish directory *MAYBE REMOVE     
        self.thumbnail_label = None
        self.file_info_text = None
        self.selected_file_path = None
        self.last_selected_folder_path = None
        self.layout = None
        self.init_preferences()  # Load preferences on initialization
        self.initUI()
        self.file_models = []  # Keep track of created QFileSystemModel instances
        self.publish_tab = None
        self.work_tab = None

        # Register keyboard shortcut for restoring settings
        QtWidgets.QShortcut(QtGui.QKeySequence(QtCore.Qt.ControlModifier + QtCore.Qt.Key_R), self, self.resetUISettings)

    def init_preferences(self):
        # Restore UI location and size from preferences
        restore_ui_preferences()

    def resetUISettings(self):
        # Set custom UI settings
        ui_width = 1790
        ui_height = 1205
        ui_location_x = 329
        ui_location_y = 86
        asset_browser_status = 'Closed'

        # Resize and move the UI
        self.resize(ui_width, ui_height)
        self.move(ui_location_x, ui_location_y)

        # Set Asset Browser status
        set_asset_browser_status(asset_browser_status)

        # Update UI based on the new settings
        self.init_preferences()
    
    def initUI(self):
        self.setWindowTitle('Asset Browser')
        self.layout = QtWidgets.QVBoxLayout(self)  # Use QVBoxLayout for vertical layout
        self.layout.setContentsMargins(0, 12, 0, 0)  # Add this line
    
        # Create a horizontal layout for the image, project label, and dropdown list
        header_layout = QtWidgets.QHBoxLayout()  # Create a QHBoxLayout for the header
        self.layout.addLayout(header_layout)  # Add the header layout to the main vertical layout
    
        # Adding the image
        image_label = QtWidgets.QLabel()
        pixmap = QtGui.QPixmap(os.path.join(ICON_DIR, "safeBank_logoTitle_v001.png"))
        image_label.setPixmap(pixmap)
        header_layout.addWidget(image_label)
    
        # Add a spacer to push the image to the left edge
        header_layout.addStretch()
    
        # Add the project label
        project_label = QLabel("Project:")
        header_layout.addWidget(project_label)
    
        # Add the project dropdown list
        self.project_combo_box = QComboBox()
        self.project_combo_box.setMinimumWidth(200)  # Set minimum width for the dropdown list
        header_layout.addWidget(self.project_combo_box)
                
        # Add a spacer to create space between the dropdown list and the edge of the window
        header_layout.addSpacing(10)  # Adjust the value (in pixels) for the desired spacing
    
        # Populate the project dropdown list
        populate_project_dropdown(self.project_combo_box)
     
        # Connect the project dropdown list signal to change_project_preferences method
        self.project_combo_box.currentIndexChanged.connect(self.changeProjectPreferences)  # Fix this line

        # Call the change_project_preferences method initially to set the initial project preferences
        self.changeProjectPreferences()
        
    # Inside the AssetBrowser class, add the following method
    def changeProjectPreferences(self):
        # Read project preferences
        project_preferences = read_project_preferences(self.project_combo_box.currentText())
    
        # Check if project preferences are found
        if project_preferences:
            # Assign asset directory and publish asset directory from project preferences
            asset_dir = project_preferences.get('Work Path')
            publish_asset_dir = project_preferences.get('Publish Path')
    
            # Check if asset directory and publish asset directory are set
            if asset_dir and publish_asset_dir:
                # Update the asset directory and publish asset directory in the UI
                self.asset_directory_label.setText(asset_dir)
                self.publish_asset_directory_label.setText(publish_asset_dir)
            else:
                # Raise an exception if either asset directory or publish asset directory is not set
                raise ValueError("Asset directory or publish asset directory is not set in preferences.")
        else:
            # Raise an exception if project preferences are not found
            raise FileNotFoundError("Project preferences file not found.")

                                
        # Create a horizontal layout for the tabs
        tabs_layout = QtWidgets.QHBoxLayout()

        # Create the tab widget
        self.tab_widget = QtWidgets.QTabWidget(self)
        tabs_layout.addWidget(self.tab_widget)

        # Add the tabs to the tab widget
        self.work_tab = QtWidgets.QWidget()
        self.tab_widget.addTab(self.work_tab, "Work")
        
        model_check_tab = QtWidgets.QWidget()
        self.tab_widget.addTab(model_check_tab, "Model Check")
        
        self.publish_tab = QtWidgets.QWidget()
        self.tab_widget.addTab(self.publish_tab, "Publish")
        
        export_tab = QtWidgets.QWidget()
        self.tab_widget.addTab(export_tab, "Export")      
        
        # Add the tabs layout to the main layout
        self.layout.addLayout(tabs_layout)
    
        # Call change_project_preferences to set the initial project preferences
        change_project_preferences(self.project_combo_box.currentText(), self)
        
        # Add content to the tabs
        self.addWorkTabContent(work_tab, asset_dir)
        self.addPublishTabContent(publish_tab, publish_asset_dir)
        # Add content to other tabs if needed        
                                
    def cleanup(self):
        # Properly dispose of QFileSystemModel instances
        for model in self.file_models:
            del model
                        
    def closeEvent(self, event):
        # Get window geometry
        geometry = asset_browser.saveGeometry()
        geometry_bytes = base64.b64encode(geometry)
        write_preferences('Window Geometry', geometry_bytes.decode())

        # Call the base class closeEvent to proceed with the window closing
        super(AssetBrowser, self).closeEvent(event)
                  
    # Work Tab ==============================================================================================================================      
    
    def addWorkTabContent(self, work_tab, asset_dir):
        # Add content to the "Work" tab only if it's not already added
        if work_tab.layout() is None:
            work_layout = QtWidgets.QVBoxLayout(work_tab)
            # Add your content here
            print("Work tab content added")
            print("Asset Directory:", asset_dir)
    
        # Function to extract headers from directories
        def extract_headers(directory):
            header_folders = []
            for root, dirs, files in os.walk(directory):
                for dir in dirs:
                    if dir.startswith("_"):
                        header_folders.append(dir.lstrip("_").capitalize())
            return header_folders
    
        # Get headers from the asset directory and sort them based on their position in the folder structure
        headers = sorted(extract_headers(self.asset_dir), key=lambda x: folder_depth(os.path.join(self.asset_dir, "_" + x.lower())))
    
        # Create a frame for the project setting and folder path
        project_frame = QtWidgets.QFrame()
        project_frame.setFrameShape(QtWidgets.QFrame.StyledPanel)
        project_frame_layout = QtWidgets.QHBoxLayout(project_frame)
        work_layout.addWidget(project_frame)
    
        # Add the set project button
        set_project_button = QtWidgets.QPushButton("Set Project")
        set_project_button.clicked.connect(self.setProject)
        project_frame_layout.addWidget(set_project_button)
    
        # Add the folder path line edit
        self.folder_path_lineedit = QtWidgets.QLineEdit()
        self.folder_path_lineedit.returnPressed.connect(self.pasteLink)  # Connect returnPressed signal to pasteLink method
        project_frame_layout.addWidget(self.folder_path_lineedit)
                
        # Add the open folder button
        open_folder_button = QtWidgets.QPushButton("Open Folder")
        open_folder_button.clicked.connect(self.openFolder)
        project_frame_layout.addWidget(open_folder_button)
    
        # Add the refresh button
        refresh_icon = QtGui.QPixmap(REFRESH_IMAGE_PATH)
        refresh_label = QtWidgets.QLabel()
        refresh_label.setPixmap(refresh_icon)
        refresh_label.mousePressEvent = self.refreshDirectories
        project_frame_layout.addWidget(refresh_label)

        # Connect the returnPressed signal of the text edit field to the pasteLink method
        self.folder_path_lineedit.returnPressed.connect(self.pasteLink)  # Add this line here
    
        # Create a layout for the views, thumbnail, and file info
        views_thumbnail_layout = QtWidgets.QHBoxLayout()
        work_layout.addLayout(views_thumbnail_layout)
    
        # Inside addWorkTabContent method after creating views and models
        views_thumbnail_layout = QtWidgets.QHBoxLayout()
        work_layout.addLayout(views_thumbnail_layout)
        
        for i, header in enumerate(headers):
            # Create a layout for each level
            level_layout = QtWidgets.QGridLayout()  # Change to QGridLayout for vertical scaling
            
            # Add header label
            header_label = QLabel(header)
            header_label.setAlignment(QtCore.Qt.AlignCenter)
            level_layout.addWidget(header_label, 0, 0, 1, 2)  # Add header label spanning two columns
            
            # Use the open_directory context manager
            # Create view
            view = QtWidgets.QListView()
            
            # Set custom model here
            model = CustomFileSystemModel()  # Create custom model instance
            view.setModel(model)  # Set custom model for the view
            
            model.setRootPath(QtCore.QDir.rootPath())  # Set root path for the model
            view.setIconSize(QtCore.QSize(20, 20))  # Set icon size
    
            # Set the size policy for vertical stretching
            view.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
            
            # Open the directory with a managed context
            with open_directory(self.asset_dir):
                root_index = view.model().index(self.asset_dir)
                view.setRootIndex(root_index)
            
            view.clicked.connect(lambda index, i=i: self.viewClicked(index, i))
            
            level_layout.addWidget(view, 1, 0)  # Add view at row 1, column 0
            
            # Add the level layout to the main layout
            views_thumbnail_layout.addLayout(level_layout)
            
            # Append the view to the file_views list
            self.file_views.append(view)
            self.file_models.append(model)

    
        # Apply filter settings to file models
        for model in self.file_models:
            model.setFilter(QtCore.QDir.AllDirs | QtCore.QDir.Files | QtCore.QDir.NoDotAndDotDot)
            model.setNameFilters(["*.mb", "*.ma", "*.fbx", "*.obj", "*.abc"])
            model.setNameFilterDisables(False)
    
        # Populate the first view upon launch
        self.populateDirectory(self.asset_dir, self.file_views[0])
    
        # Initialize the last five views with the dummy blank directory
        dummy_blank_directory = r"N:\SAFE\Asset_Browser\tools\safeBank\script\BLANK"
        for view in self.file_views[1:]:
            view.model().setRootPath(dummy_blank_directory)
            view.setRootIndex(view.model().index(dummy_blank_directory))
    
        # Connect the directory change for the first view to update subsequent views
        self.file_views[0].doubleClicked.connect(lambda index: self.populateNextView(index))
        
        # Add a scroll area for the image and information frame
        scroll_area = QtWidgets.QScrollArea()
        scroll_area.setWidgetResizable(True)
    
        # Add a frame for the thumbnail and file info
        info_frame = QtWidgets.QFrame()
        info_frame.setFrameShape(QtWidgets.QFrame.StyledPanel)
        info_frame_layout = QtWidgets.QVBoxLayout(info_frame)
        scroll_area.setWidget(info_frame)  # Set the info_frame as the widget inside the scroll area
    
        # Add frame for the thumbnail
        thumbnail_frame = QtWidgets.QFrame()
        thumbnail_frame_layout = QtWidgets.QVBoxLayout(thumbnail_frame)
        info_frame_layout.addWidget(thumbnail_frame)
    
        # Add thumbnail label
        self.thumbnail_label = QtWidgets.QLabel()
        self.thumbnail_label.setFixedSize(200, 200)
        thumbnail_frame_layout.addWidget(self.thumbnail_label)
        
        # Add the scroll area to the layout
        views_thumbnail_layout.addWidget(scroll_area)
    
        # Add frame for file info
        file_info_frame = QtWidgets.QFrame()
        file_info_frame_layout = QtWidgets.QVBoxLayout(file_info_frame)
        info_frame_layout.addWidget(file_info_frame)
    
        # Add header label for file information
        file_info_header_label = QtWidgets.QLabel("File Information")
        file_info_header_label.setAlignment(QtCore.Qt.AlignCenter)  # Align text to the center
        file_info_frame_layout.addWidget(file_info_header_label)
    
        # Add file info text field
        self.file_info_text = QtWidgets.QTextEdit()
        self.file_info_text.setReadOnly(True)  # Make it read-only
        file_info_frame_layout.addWidget(self.file_info_text)
    
        # Add feedback field
        self.feedback_field = QtWidgets.QLabel()
        work_layout.addWidget(self.feedback_field)
    
        # Add a frame for the dropdown and buttons
        dropdown_buttons_frame = QtWidgets.QFrame()
        dropdown_buttons_frame.setFrameShape(QtWidgets.QFrame.StyledPanel)
        dropdown_buttons_layout = QtWidgets.QHBoxLayout(dropdown_buttons_frame)
        work_layout.addWidget(dropdown_buttons_frame)
    
        # Set fixed width for buttons
        button_width = 100
    
        # Add a stretchable space to push the label to the left
        dropdown_buttons_layout.addStretch()
    
        # Add the file type label
        file_type_label = QtWidgets.QLabel("File Type:")
        dropdown_buttons_layout.addWidget(file_type_label)
    
        # Add the file type dropdown
        self.file_type_dropdown = QtWidgets.QComboBox()
        self.file_type_dropdown.addItems(["All", ".mb", ".ma", ".fbx", ".obj", ".abc"])
        dropdown_buttons_layout.addWidget(self.file_type_dropdown)
        self.file_type_dropdown.setFixedWidth(button_width)
        self.file_type_dropdown.currentIndexChanged.connect(self.updateFileFilters)
    
        # Connect the dropdown filter's currentIndexChanged signal to update the filters
        self.file_type_dropdown.currentIndexChanged.connect(self.updateFiltersAndSearch)
    
        # Add space between dropdown and import button
        dropdown_buttons_layout.addSpacing(button_width)
    
        # Add half of the buttons
        first_half_buttons = ["Import", "Reference"]
        for title in first_half_buttons:
            button = QtWidgets.QPushButton(title)
            button.setFixedWidth(button_width)
            dropdown_buttons_layout.addWidget(button)
    
        # Add spacer
        dropdown_buttons_layout.addSpacing(button_width)
    
        # Add the remaining buttons
        second_half_buttons = ["Open", "Save", "Save As"]
        for title in second_half_buttons:
            button = QtWidgets.QPushButton(title)
            button.setFixedWidth(button_width)
            dropdown_buttons_layout.addWidget(button)
    
        # Connect buttons
        buttons = dropdown_buttons_frame.findChildren(QtWidgets.QPushButton)
        for button in buttons:
            button.clicked.connect(self.buttonClicked)
    
        # Add a frame for search and notes (occupying half the window width each)
        search_notes_frame = QtWidgets.QFrame()
        search_notes_frame.setFrameShape(QtWidgets.QFrame.StyledPanel)
        search_notes_layout = QtWidgets.QHBoxLayout(search_notes_frame)
        work_layout.addWidget(search_notes_frame)
    
        # Add a frame for search (occupying half the window width)
        search_frame = QtWidgets.QFrame()
        search_frame.setFrameShape(QtWidgets.QFrame.StyledPanel)
        search_frame_layout = QtWidgets.QVBoxLayout(search_frame)
        search_notes_layout.addWidget(search_frame)
    
        # Add the search bar to the search frame
        search_bar_layout = QtWidgets.QHBoxLayout()
        search_frame_layout.addLayout(search_bar_layout)
        self.search_bar = QtWidgets.QLineEdit()
        search_bar_layout.addWidget(self.search_bar)
    
        # Add the search button to the search frame
        search_button = QtWidgets.QPushButton("Search")
        search_button.clicked.connect(self.searchFiles)
        search_bar_layout.addWidget(search_button)
    
        # Connect returnPressed signal of the search bar to searchFiles method
        self.search_bar.returnPressed.connect(self.searchFiles)
    
        # Add the search results list to the search frame
        self.results_list = QtWidgets.QListWidget()
        search_frame_layout.addWidget(self.results_list)
    
        # Add a frame for notes (occupying half the window width)
        notes_frame = QtWidgets.QFrame()
        notes_frame.setFrameShape(QtWidgets.QFrame.StyledPanel)
        notes_layout = QtWidgets.QVBoxLayout(notes_frame)
        search_notes_layout.addWidget(notes_frame)
    
        # Add notes box to the notes frame
        notes_label = QtWidgets.QLabel("Notes:")
        notes_layout.addWidget(notes_label)
        self.notes_box = QtWidgets.QTextEdit()
        notes_layout.addWidget(self.notes_box)
    
        # Display default file information
        self.displayFileInfoDefaults()
    
        # Connect the itemClicked signal of the search results list to the searchViewClicked method
        self.results_list.itemClicked.connect(self.searchViewClicked)

    def openFolder(self):
        selected_path = self.folder_path_lineedit.text()
        if os.path.exists(selected_path):
            if os.path.isdir(selected_path):
                # Open the selected folder in the default file browser
                try:
                    subprocess.Popen(f'explorer "{selected_path}"')
                except Exception as e:
                    print(f"Error opening folder: {e}")
            else:
                # Extract the directory part of the path
                directory_path = os.path.dirname(selected_path)
                if os.path.exists(directory_path):
                    # Open the directory containing the file in the default file browser
                    try:
                        subprocess.Popen(f'explorer "{directory_path}"')
                    except Exception as e:
                        print(f"Error opening folder: {e}")
                else:
                    print("Parent directory does not exist.")
        else:
            print("Selected path does not exist.")
                
    def populateDirectory(self, directory, view, scale_factor=1):
        view.model().setRootPath(directory)
        view.setRootIndex(view.model().index(directory))
    
        # Check if the current directory contains a subdirectory named "scenes"
        scenes_path = os.path.join(directory, "scenes")
    
        print("Scenes path:", scenes_path)  # Add print statement to check scenes path
    
        # Check if the "scenes" folder exists
        if os.path.exists(scenes_path):
            print("Scenes folder exists.")  # Add print statement for scenes folder
            # Populate the view with contents of "scenes" folder
            self.populateSubdirectoryRecursively(scenes_path, view)
        else:
            # If "scenes" folder doesn't exist, check for two levels down
            sub_scenes_path = os.path.join(directory, "*", "scenes")
            sub_scenes_paths = glob.glob(sub_scenes_path)
    
            if sub_scenes_paths:
                print("Sub-scenes folder exists.")  # Add print statement for sub-scenes folder
                # Populate the view with contents of sub-scenes folder
                self.populateSubdirectoryRecursively(sub_scenes_paths[0], view)
            else:
                print("Scenes folder not found.")  # Add print statement if scenes folder doesn't exist
                # Proceed with regular population
                self.populateSubdirectoryRecursively(directory, view)
    
        # Clear subsequent views and update selection
        self.clearSubsequentViews(self.file_views.index(view), scale_factor)
    
    def populateSubdirectoryRecursively(self, directory, view):
        # Populate the current directory
        view.model().setRootPath(directory)
        view.setRootIndex(view.model().index(directory))
        
        # Recursively populate subdirectories
        for root, dirs, files in os.walk(directory):
            for dir in dirs:
                dir_path = os.path.join(root, dir)
                view.model().fetchMore(view.model().index(dir_path))

    def viewClicked(self, index, view_index):
        selected_file_path = self.file_views[view_index].model().filePath(index)
        selected_file_path = os.path.normpath(selected_file_path)  # Normalize the path
        self.folder_path_lineedit.setText(selected_file_path)  # Update folder path line edit
        
        # Store the selected index before clearing the selection
        selected_index = self.file_views[view_index].currentIndex()
        
        # Clear selection in all views
        for view in self.file_views:
            view.selectionModel().clearSelection()
        
        # Clear selection in the search results list
        self.results_list.clearSelection()
        
        if os.path.isdir(selected_file_path):
            # If a folder is selected, populate the directory and update last selected folder path
            self.populateDirectory(selected_file_path, self.file_views[view_index + 1])
            self.last_selected_folder_path = selected_file_path
        else:
            # If a file is selected, clear subsequent views and update selected file path
            self.clearSubsequentViews(view_index)
            self.selected_file_path = selected_file_path
            self.displayNotes()
            self.displayThumbnail(selected_file_path)
            self.displayFileInfo(selected_file_path)
            # Since a file is selected, do not update last selected folder path
        
        # Reselect the clicked item in the navigation list
        self.file_views[view_index].setCurrentIndex(selected_index)

    def searchViewClicked(self, item):
        selected_file_path = item.text()
        self.folder_path_lineedit.setText(selected_file_path)  # Update folder path line edit
    
        # Clear selection in all views
        for view in self.file_views:
            view.selectionModel().clearSelection()
    
        # Clear selection in the navigation list
        for view in self.file_views:
            view.clearSelection()
    
        if os.path.isdir(selected_file_path):
            # No need to populate the directory if a folder is selected
            pass
        else:
            # Clear subsequent views if a file is clicked
            self.clearSubsequentViews(0)
            self.selected_file_path = selected_file_path
            self.displayNotes()
            self.displayThumbnail(selected_file_path)
            self.displayFileInfo(selected_file_path)
                
    def clearSubsequentViews(self, view_index, scale_factor=1):
        # Clear the root index for all views to the right of the current view
        for subsequent_view in self.file_views[view_index + 1:]:
            # Set the root index to the dummy blank directory
            dummy_blank_directory = r"N:\SAFE\Asset_Browser\tools\safeBank\script\BLANK"
            subsequent_view.model().setRootPath(dummy_blank_directory)
            subsequent_view.setRootIndex(subsequent_view.model().index(dummy_blank_directory))
            
            # Adjust the size of subsequent views based on the scale factor
            subsequent_view.resize(subsequent_view.size().width(), subsequent_view.size().height() * scale_factor)

            
    def pasteLink(self):
        link = self.folder_path_lineedit.text().strip()  # Get the text from the text edit field
        if os.path.exists(link):  # Check if the path exists
            parts = link.split(os.path.sep)  # Split the path by separator
            asset_index = parts.index("Asset")  # Find the index of "Asset"
            scenes_index = None  # Initialize scenes index
            user_index = None  # Initialize user index
            maya_flag = False  # Flag to indicate whether "maya" folder is found
            
            # Print debug information
            print("Number of parts:", len(parts))
            print("Expected number of views:", self.levels)
    
            # Iterate through each part of the path to update navigation lists
            for i, part in enumerate(parts):
                if i >= asset_index and i < asset_index + self.levels:
                    view_index = i - asset_index
                    if view_index >= len(self.file_views):
                        print("Index out of range:", view_index)
                        break
    
                    view = self.file_views[view_index]  # Get the corresponding view
                    model = view.model()
    
                    # Check if the folder name contains "maya" or "scenes" in any order or capitalization
                    if "maya" in part.lower() or "scenes" in part.lower():
                        maya_flag = True
                        continue
    
                    # Search for the "user" folder
                    if user_index is None and part.lower() == "user":
                        user_index = i  # Set the index of the "user" folder
                        continue
    
                    if maya_flag:
                        # If "maya" folder was found previously, skip its contents and "scenes" folder
                        if part.lower() == "scenes":
                            scenes_index = i
                            break
                        continue
    
                    if user_index is not None and i == user_index + 1:
                        # If the folder follows the "user" folder, consider it as the "user" folder
                        continue
    
                    if user_index is not None and i > user_index and part.lower() == "maya":
                        # If "maya" folder is encountered after the "user" folder,
                        # set the flag to skip "maya" folder and its contents
                        maya_flag = True
                        continue
    
                    root_index = model.index(os.path.sep.join(parts[:i + 1]))
                    view.setRootIndex(root_index)  # Set the root index for the current view
    
            if scenes_index is not None:
                # Directly show the contents of "scenes" folder if it follows "user" and "maya"
                view_index = scenes_index - asset_index
                if view_index >= 0 and view_index < len(self.file_views):
                    view = self.file_views[view_index]
                    model = view.model()
                    scenes_path = os.path.join(os.path.sep.join(parts[:scenes_index + 1]), "scenes")
                    root_index = model.index(scenes_path)
                    view.setRootIndex(root_index)
                    self.clearSubsequentViews(view_index)  # Clear subsequent views after displaying scenes folder contents
                else:
                    print("Index out of range for scenes view:", view_index)
    
            # Highlight the last item in the pasted path
            last_item = parts[-1]
            if last_item:
                for view in self.file_views:
                    selection_model = view.selectionModel()
                    index = model.index(link)  # Use the link directly as the index
                    selection_model.clearSelection()
                    selection_model.select(index, QtCore.QItemSelectionModel.Select)
    
            # Set focus to the path text field to handle keyboard shortcuts
            self.folder_path_lineedit.setFocus()
        else:
            QtWidgets.QMessageBox.warning(self, "Invalid Path", "The pasted link does not exist.")
    
        # Debug feedback
        print("Pasted Path:", link)
        print("Parts:", parts)
        print("Asset Index:", asset_index)
        print("Scenes Index:", scenes_index)
        print("Selected Path:", link)



    # Override keyPressEvent method to handle Ctrl+C shortcut
    def keyPressEvent(self, event):
        if event.key() == Qt.Key_C and event.modifiers() & Qt.ControlModifier:
            QApplication.clipboard().setText(self.folder_path_lineedit.text().strip())
        else:
            super().keyPressEvent(event)

 
    def displayNotes(self):
        # Check if a file is selected
        if self.selected_file_path is not None:
            # Construct the note file path by replacing the file extension with '.txt'
            note_file_path = os.path.splitext(self.selected_file_path)[0] + '.txt'
            # Check if the note file exists
            if os.path.isfile(note_file_path):
                # Read and display the contents of the note file
                with open(note_file_path, 'r') as f:
                    notes_content = f.read()
                self.notes_box.setText(notes_content)
                return
        # If no note file found or no file is selected, clear the notes box
        self.notes_box.clear()

    def displayThumbnail(self, file_path):
        # Construct the thumbnail file path
        thumbnail_path = os.path.splitext(file_path)[0] + '.png'
        # Debug print for the thumbnail path
        print(f"Thumbnail Path: {thumbnail_path}")
        # Check if thumbnail exists
        if os.path.exists(thumbnail_path):
            try:
                pixmap = QtGui.QPixmap(thumbnail_path)
                self.thumbnail_label.setPixmap(pixmap.scaled(200, 200, QtCore.Qt.KeepAspectRatio))
                return
            except Exception as e:
                print(f"Error loading thumbnail: {e}")
        else:
            print("Thumbnail not found.")

    def displayFileInfoDefaults(self):
        # Display default file information
        default_info = (
            "File Path:\n\n"
            "File Name:\n\n"
            "Date Created:\n\n"
            "Date Modified:\n\n"
            "User Created:\n\n"
            "Size:\n"
        )
        self.file_info_text.setText(default_info)

    def displayFileInfo(self, file_path):
        # Get file information
        file_info = ""

        # Check if the file exists
        if os.path.exists(file_path):
            # File Path
            file_info += f"File Path:\n{file_path}\n"

            # File Name
            file_name = os.path.basename(file_path)
            file_info += f"File Name:\n{file_name}\n"

            # Date Created
            date_created = self.convertTimestamp(os.path.getctime(file_path))
            file_info += f"Date Created:\n{date_created}\n"

            # Date Modified
            date_modified = self.convertTimestamp(os.path.getmtime(file_path))
            file_info += f"Date Modified:\n{date_modified}\n"

            # User Created
            user_created = self.getOwner(file_path)
            file_info += f"User Created:\n{user_created}\n"

            # Size
            size = self.convertSize(os.path.getsize(file_path))
            file_info += f"Size:\n{size}\n"
        else:
            # If the file does not exist, set default values
            file_info += (
                "File Path:\n\n"
                "File Name:\n\n"
                "Date Created:\n\n"
                "Date Modified:\n\n"
                "User Created:\n\n"
                "Size:\n"
            )

        self.file_info_text.setText(file_info)

    def convertTimestamp(self, timestamp):
        return QtCore.QDateTime.fromSecsSinceEpoch(timestamp).toString("dd/MM/yy")

    def convertSize(self, size):
        # Convert bytes to human-readable format
        for unit in ['bytes', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.2f} {unit}"
            size /= 1024.0

    def getOwner(self, file_path):
        return os.getlogin()  # Replace this with a function to get owner name if available

    def refreshDirectories(self, event):
        for view in self.file_views:
            view.model().refresh()

    def setProject(self):
        selected_directory = self.folder_path_lineedit.text()
        selected_directory = selected_directory.replace('\\', '/')  # Replace backward slashes with forward slashes
        mel.eval('setProject "{}";'.format(selected_directory))

    def updateFileFilters(self):
        selected_file_type = self.file_type_dropdown.currentText()
        name_filters = []
        if selected_file_type == ".mb":
            name_filters = ["*.mb"]
        elif selected_file_type == ".ma":
            name_filters = ["*.ma"]
        elif selected_file_type == ".fbx":
            name_filters = ["*.fbx"]
        elif selected_file_type == ".obj":
            name_filters = ["*.obj"]
        elif selected_file_type == ".abc":
            name_filters = ["*.abc"]                        
        else:
            # If "All" is selected or any other case, include all supported file types
            name_filters = ["*.mb", "*.ma", "*.fbx", "*.obj", "*.abc"]

        # Update name filters for all file views
        for view in self.file_views:
            view.model().setNameFilters(name_filters)
            view.model().setNameFilterDisables(False)

        # Update name filters for the search results list
        self.results_list.clear()
        self.results_list.setNameFilters(name_filters)
        self.results_list.setNameFilterDisables(False)

        # Refresh directories to apply the new filters
        self.refreshDirectories(None)  # Passing None as event parameter since not used in refreshDirectories

    def buttonClicked(self):
        sender_button = self.sender()
        if sender_button:
            button_text = sender_button.text()
            if button_text == "Import":
                self.importFile()
            elif button_text == "Reference":
                self.referenceFile()
            elif button_text == "Open":
                self.openFile()
            elif button_text == "Save":
                self.saveFile()
            elif button_text == "Save As":
                self.saveAsFile()
                
    def importFile(self):
        if self.selected_file_path:
            cmds.file(self.selected_file_path, i=True)
    
    def referenceFile(self):
        if self.selected_file_path:
            cmds.file(self.selected_file_path, reference=True)
    
    def openFile(self):
        # Check if there are unsaved changes in the current scene
        if cmds.file(q=True, modified=True):
            # Prompt the user to save the changes
            result = QtWidgets.QMessageBox.question(self, 'Unsaved Changes',
                                                   'There are unsaved changes. Do you want to save before opening a new file?',
                                                   QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No | QtWidgets.QMessageBox.Cancel)
    
            if result == QtWidgets.QMessageBox.Yes:
                # Save the current scene and open the selected file
                self.saveAndOpenSelectedFile()
                return
            elif result == QtWidgets.QMessageBox.Cancel:
                # User canceled the operation, do nothing
                return
    
        # If there are no unsaved changes or the user chooses not to save, proceed with opening the selected file
        if self.selected_file_path:
            # Check if there is a saved file
            if cmds.file(q=True, sceneName=True):
                # If a file is already open, close it before opening the new file
                cmds.file(new=True, force=True)
            # Open the selected file
            self.openSelectedFile()
    
    def saveFile(self):
        cmds.file(save=True)
    
    def saveAsFile(self):
        file_path = cmds.fileDialog2(dialogStyle=2, fm=0, fileFilter='Maya Files (*.ma *.mb);;Maya ASCII (*.ma);;Maya Binary (*.mb)')
        if file_path:
            cmds.file(rename=file_path[0])
            cmds.file(save=True)
            
    def saveAndOpenSelectedFile(self):
        # Prompt the user to save the scene with "Save As"
        file_path = cmds.fileDialog2(dialogStyle=2, fm=0, fileFilter='Maya Files (*.ma *.mb);;Maya ASCII (*.ma);;Maya Binary (*.mb)')
        if file_path:
            cmds.file(rename=file_path[0])
            cmds.file(save=True)
            # After saving, check if the selected file is not empty and open it
            if self.selected_file_path:
                self.openSelectedFile()
            
    def openSelectedFile(self):
        # Open the selected file
        cmds.file(self.selected_file_path, open=True, force=True)
        
    def searchFiles(self, existing_results=None):
        search_text = self.search_bar.text().lower()
        selected_directory = self.folder_path_lineedit.text()
        selected_file_type = self.file_type_dropdown.currentText().lower()
        results = []
    
        # Check if there is a last selected folder path and use it if present
        if selected_directory and not existing_results:
            selected_directory = self.last_selected_folder_path
    
        # Search only within the last selected folder
        for root, dirs, files in os.walk(selected_directory):
            for file in files:
                file_lower = file.lower()
                if search_text in file_lower and file_lower.endswith(('.mb', '.ma', '.fbx', '.obj', '.abc')):
                    if selected_file_type == "all" or file_lower.endswith(selected_file_type):
                        # Append the full file path to the results list
                        full_file_path = os.path.normpath(os.path.join(root, file))
                        results.append(full_file_path)
    
        print("Selected Directory:", selected_directory)
        print("Search Results:", results)
    
        # Combine existing results with new results if available
        if existing_results:
            results.extend(existing_results)
    
        # Clear previous items from the list
        self.results_list.clear()
    
        # Add filtered items to the list
        self.results_list.addItems(results)
    
        # Clear selection in the file views
        for view in self.file_views:
            view.clearSelection()
        
    def updateFiltersAndSearch(self):
        # Check if there is text in the search bar
        if self.search_bar.text():
            # If there is text, run the search function with the current dropdown filter applied
            self.searchFiles()
                              
# ModelCheck Tab ======================================================================================================================             
    def addModelTabContent(self, model_check_tab):
        layout = QtWidgets.QVBoxLayout(model_check_tab)
        scroll_area = QtWidgets.QScrollArea()
        scroll_area.setWidgetResizable(True)  # Allow the widget inside the scroll area to resize
        ui_instance = UI()  # Create an instance of the UI class
        scroll_area.setWidget(ui_instance)  # Set the UI instance as the widget inside the scroll area
        layout.addWidget(scroll_area)  # Add the scroll area to the layout
        
# Publish Tab ======================================================================================================================          
    def addPublishTabContent(self, publish_tab, publish_asset_dir):
        # Add content to the "Publish" tab only if it's not already added
        if publish_tab.layout() is None:
            publish_layout = QtWidgets.QVBoxLayout(publish_tab)
            # Add your content here
            print("Publish tab content added")
            print("Publish Asset Directory:", publish_asset_dir)
                    
            # Function to extract headers from directories
            def extract_headers(directory):
                header_folders = []
                for root, dirs, files in os.walk(directory):
                    for dir in dirs:
                        if dir.startswith("_"):
                            header_folders.append(dir.lstrip("_").capitalize())
                return header_folders
        
            # Get headers from the asset directory and sort them based on their position in the folder structure
            headers = sorted(extract_headers(publish_asset_dir), key=lambda x: folder_depth(os.path.join(publish_asset_dir, "_" + x.lower())))
    
        # Create a frame for the project setting and folder path
        project_frame = QtWidgets.QFrame()
        project_frame.setFrameShape(QtWidgets.QFrame.StyledPanel)
        project_frame_layout = QtWidgets.QHBoxLayout(project_frame)
        publish_layout.addWidget(project_frame)
    
        # Add the set project button
        set_project_button = QtWidgets.QPushButton("Set Project")
        set_project_button.clicked.connect(self.setProject)
        project_frame_layout.addWidget(set_project_button)
    
        # Add the folder path line edit
        self.folder_path_lineedit = QtWidgets.QLineEdit()
        project_frame_layout.addWidget(self.folder_path_lineedit)
                
        # Add the open folder button
        open_folder_button = QtWidgets.QPushButton("Open Folder")
        open_folder_button.clicked.connect(self.openFolder)
        project_frame_layout.addWidget(open_folder_button)
    
        # Add the refresh button
        refresh_icon = QtGui.QPixmap(REFRESH_IMAGE_PATH)
        refresh_label = QtWidgets.QLabel()
        refresh_label.setPixmap(refresh_icon)
        refresh_label.mousePressEvent = self.refreshDirectories
        project_frame_layout.addWidget(refresh_label)
    
        # Create a layout for the views, thumbnail, and file info
        views_thumbnail_layout = QtWidgets.QHBoxLayout()
        publish_layout.addLayout(views_thumbnail_layout)
    
        # Inside addPublishTabContent method after creating views and models
        views_thumbnail_layout = QtWidgets.QHBoxLayout()
        publish_layout.addLayout(views_thumbnail_layout)
        
        for i, header in enumerate(headers):
            # Create a layout for each level
            level_layout = QtWidgets.QGridLayout()  # Change to QGridLayout for vertical scaling
            
            # Add header label
            header_label = QLabel(header)
            header_label.setAlignment(QtCore.Qt.AlignCenter)
            level_layout.addWidget(header_label, 0, 0, 1, 2)  # Add header label spanning two columns
            
            # Use the open_directory context manager
            # Create view
            view = QtWidgets.QListView()
            
            # Set custom model here
            model = CustomFileSystemModel()  # Create custom model instance
            view.setModel(model)  # Set custom model for the view
            
            model.setRootPath(QtCore.QDir.rootPath())  # Set root path for the model
            view.setIconSize(QtCore.QSize(20, 20))  # Set icon size
    
            # Set the size policy for vertical stretching
            view.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
            
            # Open the directory with a managed context
            with open_directory(self.publish_asset_dir):
                root_index = view.model().index(self.publish_asset_dir)
                view.setRootIndex(root_index)
            
            view.clicked.connect(lambda index, i=i: self.viewClicked(index, i))
            
            level_layout.addWidget(view, 1, 0)  # Add view at row 1, column 0
            
            # Add the level layout to the main layout
            views_thumbnail_layout.addLayout(level_layout)
            
            # Append the view to the file_views list
            self.file_views.append(view)
            self.file_models.append(model)

        # Apply filter settings to file models
        for model in self.file_models:
            model.setFilter(QtCore.QDir.AllDirs | QtCore.QDir.Files | QtCore.QDir.NoDotAndDotDot)
            model.setNameFilters(["*.mb", "*.ma", "*.fbx", "*.obj", "*.abc"])
            model.setNameFilterDisables(False)
    
        # Populate the first view upon launch
        self.populateDirectory(publish_asset_dir, self.file_views[0])
    
        # Initialize the last five views with the dummy blank directory
        dummy_blank_directory = r"N:\SAFE\Asset_Browser\tools\safeBank\script\BLANK"
        for view in self.file_views[1:]:
            view.model().setRootPath(dummy_blank_directory)
            view.setRootIndex(view.model().index(dummy_blank_directory))
    
        # Connect the directory change for the first view to update subsequent views
        self.file_views[0].doubleClicked.connect(lambda index: self.populateNextView(index))
        
        # Add a scroll area for the image and information frame
        scroll_area = QtWidgets.QScrollArea()
        scroll_area.setWidgetResizable(True)
    
        # Add a frame for the thumbnail and file info
        info_frame = QtWidgets.QFrame()
        info_frame.setFrameShape(QtWidgets.QFrame.StyledPanel)
        info_frame_layout = QtWidgets.QVBoxLayout(info_frame)
        scroll_area.setWidget(info_frame)  # Set the info_frame as the widget inside the scroll area
    
        # Add frame for the thumbnail
        thumbnail_frame = QtWidgets.QFrame()
        thumbnail_frame_layout = QtWidgets.QVBoxLayout(thumbnail_frame)
        info_frame_layout.addWidget(thumbnail_frame)
    
        # Add thumbnail label
        self.thumbnail_label = QtWidgets.QLabel()
        self.thumbnail_label.setFixedSize(200, 200)
        thumbnail_frame_layout.addWidget(self.thumbnail_label)
        
        # Add the scroll area to the layout
        views_thumbnail_layout.addWidget(scroll_area)
    
        # Add frame for file info
        file_info_frame = QtWidgets.QFrame()
        file_info_frame_layout = QtWidgets.QVBoxLayout(file_info_frame)
        info_frame_layout.addWidget(file_info_frame)
    
        # Add header label for file information
        file_info_header_label = QtWidgets.QLabel("File Information")
        file_info_header_label.setAlignment(QtCore.Qt.AlignCenter)  # Align text to the center
        file_info_frame_layout.addWidget(file_info_header_label)
    
        # Add file info text field
        self.file_info_text = QtWidgets.QTextEdit()
        self.file_info_text.setReadOnly(True)  # Make it read-only
        file_info_frame_layout.addWidget(self.file_info_text)
    
        # Add feedback field
        self.feedback_field = QtWidgets.QLabel()
        publish_layout.addWidget(self.feedback_field)
    
        # Add a frame for the dropdown and buttons
        dropdown_buttons_frame = QtWidgets.QFrame()
        dropdown_buttons_frame.setFrameShape(QtWidgets.QFrame.StyledPanel)
        dropdown_buttons_layout = QtWidgets.QHBoxLayout(dropdown_buttons_frame)
        publish_layout.addWidget(dropdown_buttons_frame)
    
        # Set fixed width for buttons
        button_width = 100
    
        # Add a stretchable space to push the label to the left
        dropdown_buttons_layout.addStretch()
    
        # Add the file type label
        file_type_label = QtWidgets.QLabel("File Type:")
        dropdown_buttons_layout.addWidget(file_type_label)
    
        # Add the file type dropdown
        self.file_type_dropdown = QtWidgets.QComboBox()
        self.file_type_dropdown.addItems(["All", ".mb", ".ma", ".fbx", ".obj", ".abc"])
        dropdown_buttons_layout.addWidget(self.file_type_dropdown)
        self.file_type_dropdown.setFixedWidth(button_width)
        self.file_type_dropdown.currentIndexChanged.connect(self.updateFileFilters)
    
        # Connect the dropdown filter's currentIndexChanged signal to update the filters
        self.file_type_dropdown.currentIndexChanged.connect(self.updateFiltersAndSearch)
    
        # Add space between dropdown and import button
        dropdown_buttons_layout.addSpacing(button_width)
    
        # Add half of the buttons
        first_half_buttons = ["Import", "Reference"]
        for title in first_half_buttons:
            button = QtWidgets.QPushButton(title)
            button.setFixedWidth(button_width)
            dropdown_buttons_layout.addWidget(button)
    
        # Add spacer
        dropdown_buttons_layout.addSpacing(button_width)
    
        # Add the remaining buttons
        second_half_buttons = ["Open", "Save", "Save As"]
        for title in second_half_buttons:
            button = QtWidgets.QPushButton(title)
            button.setFixedWidth(button_width)
            dropdown_buttons_layout.addWidget(button)
    
        # Connect buttons
        buttons = dropdown_buttons_frame.findChildren(QtWidgets.QPushButton)
        for button in buttons:
            button.clicked.connect(self.buttonClicked)
    
        # Add a frame for search and notes (occupying half the window width each)
        search_notes_frame = QtWidgets.QFrame()
        search_notes_frame.setFrameShape(QtWidgets.QFrame.StyledPanel)
        search_notes_layout = QtWidgets.QHBoxLayout(search_notes_frame)
        publish_layout.addWidget(search_notes_frame)
    
        # Add a frame for search (occupying half the window width)
        search_frame = QtWidgets.QFrame()
        search_frame.setFrameShape(QtWidgets.QFrame.StyledPanel)
        search_frame_layout = QtWidgets.QVBoxLayout(search_frame)
        search_notes_layout.addWidget(search_frame)
    
        # Add the search bar to the search frame
        search_bar_layout = QtWidgets.QHBoxLayout()
        search_frame_layout.addLayout(search_bar_layout)
        self.search_bar = QtWidgets.QLineEdit()
        search_bar_layout.addWidget(self.search_bar)
    
        # Add the search button to the search frame
        search_button = QtWidgets.QPushButton("Search")
        search_button.clicked.connect(self.searchFiles)
        search_bar_layout.addWidget(search_button)
    
        # Connect returnPressed signal of the search bar to searchFiles method
        self.search_bar.returnPressed.connect(self.searchFiles)
    
        # Add the search results list to the search frame
        self.results_list = QtWidgets.QListWidget()
        search_frame_layout.addWidget(self.results_list)
    
        # Add a frame for notes (occupying half the window width)
        notes_frame = QtWidgets.QFrame()
        notes_frame.setFrameShape(QtWidgets.QFrame.StyledPanel)
        notes_layout = QtWidgets.QVBoxLayout(notes_frame)
        search_notes_layout.addWidget(notes_frame)
    
        # Add notes box to the notes frame
        notes_label = QtWidgets.QLabel("Notes:")
        notes_layout.addWidget(notes_label)
        self.notes_box = QtWidgets.QTextEdit()
        notes_layout.addWidget(self.notes_box)
    
        # Display default file information
        self.displayFileInfoDefaults()
    
        # Connect the itemClicked signal of the search results list to the searchViewClicked method
        self.results_list.itemClicked.connect(self.searchViewClicked)

    def openFolder(self):
        selected_path = self.folder_path_lineedit.text()
        if os.path.exists(selected_path):
            if os.path.isdir(selected_path):
                # Open the selected folder in the default file browser
                try:
                    subprocess.Popen(f'explorer "{selected_path}"')
                except Exception as e:
                    print(f"Error opening folder: {e}")
            else:
                # Extract the directory part of the path
                directory_path = os.path.dirname(selected_path)
                if os.path.exists(directory_path):
                    # Open the directory containing the file in the default file browser
                    try:
                        subprocess.Popen(f'explorer "{directory_path}"')
                    except Exception as e:
                        print(f"Error opening folder: {e}")
                else:
                    print("Parent directory does not exist.")
        else:
            print("Selected path does not exist.")
                
    def populateDirectory(self, directory, view, scale_factor=1):
        view.model().setRootPath(directory)
        view.setRootIndex(view.model().index(directory))
    
        # Check if the current directory contains a subdirectory named "scenes"
        scenes_path = os.path.join(directory, "scenes")
    
        print("Scenes path:", scenes_path)  # Add print statement to check scenes path
    
        # Check if the "scenes" folder exists
        if os.path.exists(scenes_path):
            print("Scenes folder exists.")  # Add print statement for scenes folder
            # Populate the view with contents of "scenes" folder
            self.populateSubdirectoryRecursively(scenes_path, view)
        else:
            print("Scenes folder not found.")  # Add print statement if scenes folder doesn't exist
            # Proceed with regular population
            self.populateSubdirectoryRecursively(directory, view)
    
        # Clear subsequent views and update selection
        self.clearSubsequentViews(self.file_views.index(view), scale_factor)
    
    def populateSubdirectoryRecursively(self, directory, view):
        # Populate the current directory
        view.model().setRootPath(directory)
        view.setRootIndex(view.model().index(directory))
        
        # Recursively populate subdirectories
        for root, dirs, files in os.walk(directory):
            for dir in dirs:
                dir_path = os.path.join(root, dir)
                view.model().fetchMore(view.model().index(dir_path))

    def viewClicked(self, index, view_index):
        selected_file_path = self.file_views[view_index].model().filePath(index)
        selected_file_path = os.path.normpath(selected_file_path)  # Normalize the path
        self.folder_path_lineedit.setText(selected_file_path)  # Update folder path line edit
        
        # Store the selected index before clearing the selection
        selected_index = self.file_views[view_index].currentIndex()
        
        # Clear selection in all views
        for view in self.file_views:
            view.selectionModel().clearSelection()
        
        # Clear selection in the search results list
        self.results_list.clearSelection()
        
        if os.path.isdir(selected_file_path):
            # If a folder is selected, populate the directory and update last selected folder path
            self.populateDirectory(selected_file_path, self.file_views[view_index + 1])
            self.last_selected_folder_path = selected_file_path
        else:
            # If a file is selected, clear subsequent views and update selected file path
            self.clearSubsequentViews(view_index)
            self.selected_file_path = selected_file_path
            self.displayNotes()
            self.displayThumbnail(selected_file_path)
            self.displayFileInfo(selected_file_path)
            # Since a file is selected, do not update last selected folder path
        
        # Reselect the clicked item in the navigation list
        self.file_views[view_index].setCurrentIndex(selected_index)

    def searchViewClicked(self, item):
        selected_file_path = item.text()
        self.folder_path_lineedit.setText(selected_file_path)  # Update folder path line edit
    
        # Clear selection in all views
        for view in self.file_views:
            view.selectionModel().clearSelection()
    
        # Clear selection in the navigation list
        for view in self.file_views:
            view.clearSelection()
    
        if os.path.isdir(selected_file_path):
            # No need to populate the directory if a folder is selected
            pass
        else:
            # Clear subsequent views if a file is clicked
            self.clearSubsequentViews(0)
            self.selected_file_path = selected_file_path
            self.displayNotes()
            self.displayThumbnail(selected_file_path)
            self.displayFileInfo(selected_file_path)
                
    def clearSubsequentViews(self, view_index, scale_factor=1):
        # Clear the root index for all views to the right of the current view
        for subsequent_view in self.file_views[view_index + 1:]:
            # Set the root index to the dummy blank directory
            dummy_blank_directory = r"N:\SAFE\Asset_Browser\tools\safeBank\script\BLANK"
            subsequent_view.model().setRootPath(dummy_blank_directory)
            subsequent_view.setRootIndex(subsequent_view.model().index(dummy_blank_directory))
            
            # Adjust the size of subsequent views based on the scale factor
            subsequent_view.resize(subsequent_view.size().width(), subsequent_view.size().height() * scale_factor)
                
    def displayNotes(self):
        # Check if a file is selected
        if self.selected_file_path is not None:
            # Construct the note file path by replacing the file extension with '.txt'
            note_file_path = os.path.splitext(self.selected_file_path)[0] + '.txt'
            # Check if the note file exists
            if os.path.isfile(note_file_path):
                # Read and display the contents of the note file
                with open(note_file_path, 'r') as f:
                    notes_content = f.read()
                self.notes_box.setText(notes_content)
                return
        # If no note file found or no file is selected, clear the notes box
        self.notes_box.clear()

    def displayThumbnail(self, file_path):
        # Construct the thumbnail file path
        thumbnail_path = os.path.splitext(file_path)[0] + '.png'
        # Debug print for the thumbnail path
        print(f"Thumbnail Path: {thumbnail_path}")
        # Check if thumbnail exists
        if os.path.exists(thumbnail_path):
            try:
                pixmap = QtGui.QPixmap(thumbnail_path)
                self.thumbnail_label.setPixmap(pixmap.scaled(200, 200, QtCore.Qt.KeepAspectRatio))
                return
            except Exception as e:
                print(f"Error loading thumbnail: {e}")
        else:
            print("Thumbnail not found.")

    def displayFileInfoDefaults(self):
        # Display default file information
        default_info = (
            "File Path:\n\n"
            "File Name:\n\n"
            "Date Created:\n\n"
            "Date Modified:\n\n"
            "User Created:\n\n"
            "Size:\n"
        )
        self.file_info_text.setText(default_info)

    def displayFileInfo(self, file_path):
        # Get file information
        file_info = ""

        # Check if the file exists
        if os.path.exists(file_path):
            # File Path
            file_info += f"File Path:\n{file_path}\n"

            # File Name
            file_name = os.path.basename(file_path)
            file_info += f"File Name:\n{file_name}\n"

            # Date Created
            date_created = self.convertTimestamp(os.path.getctime(file_path))
            file_info += f"Date Created:\n{date_created}\n"

            # Date Modified
            date_modified = self.convertTimestamp(os.path.getmtime(file_path))
            file_info += f"Date Modified:\n{date_modified}\n"

            # User Created
            user_created = self.getOwner(file_path)
            file_info += f"User Created:\n{user_created}\n"

            # Size
            size = self.convertSize(os.path.getsize(file_path))
            file_info += f"Size:\n{size}\n"
        else:
            # If the file does not exist, set default values
            file_info += (
                "File Path:\n\n"
                "File Name:\n\n"
                "Date Created:\n\n"
                "Date Modified:\n\n"
                "User Created:\n\n"
                "Size:\n"
            )

        self.file_info_text.setText(file_info)

    def convertTimestamp(self, timestamp):
        return QtCore.QDateTime.fromSecsSinceEpoch(timestamp).toString("dd/MM/yy")

    def convertSize(self, size):
        # Convert bytes to human-readable format
        for unit in ['bytes', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.2f} {unit}"
            size /= 1024.0

    def getOwner(self, file_path):
        return os.getlogin()  # Replace this with a function to get owner name if available

    def refreshDirectories(self, event):
        for view in self.file_views:
            view.model().refresh()

    def setProject(self):
        selected_directory = self.folder_path_lineedit.text()
        selected_directory = selected_directory.replace('\\', '/')  # Replace backward slashes with forward slashes
        mel.eval('setProject "{}";'.format(selected_directory))

    def updateFileFilters(self):
        selected_file_type = self.file_type_dropdown.currentText()
        name_filters = []
        if selected_file_type == ".mb":
            name_filters = ["*.mb"]
        elif selected_file_type == ".ma":
            name_filters = ["*.ma"]
        elif selected_file_type == ".fbx":
            name_filters = ["*.fbx"]
        elif selected_file_type == ".obj":
            name_filters = ["*.obj"]
        elif selected_file_type == ".abc":
            name_filters = ["*.abc"]                        
        else:
            # If "All" is selected or any other case, include all supported file types
            name_filters = ["*.mb", "*.ma", "*.fbx", "*.obj", "*.abc"]

        # Update name filters for all file views
        for view in self.file_views:
            view.model().setNameFilters(name_filters)
            view.model().setNameFilterDisables(False)

        # Update name filters for the search results list
        self.results_list.clear()
        self.results_list.setNameFilters(name_filters)
        self.results_list.setNameFilterDisables(False)

        # Refresh directories to apply the new filters
        self.refreshDirectories(None)  # Passing None as event parameter since not used in refreshDirectories

    def buttonClicked(self):
        sender_button = self.sender()
        if sender_button:
            button_text = sender_button.text()
            if button_text == "Import":
                self.importFile()
            elif button_text == "Reference":
                self.referenceFile()
            elif button_text == "Open":
                self.openFile()
            elif button_text == "Save":
                self.saveFile()
            elif button_text == "Save As":
                self.saveAsFile()
                
    def importFile(self):
        if self.selected_file_path:
            cmds.file(self.selected_file_path, i=True)
    
    def referenceFile(self):
        if self.selected_file_path:
            cmds.file(self.selected_file_path, reference=True)
    
    def openFile(self):
        # Check if there are unsaved changes in the current scene
        if cmds.file(q=True, modified=True):
            # Prompt the user to save the changes
            result = QtWidgets.QMessageBox.question(self, 'Unsaved Changes',
                                                   'There are unsaved changes. Do you want to save before opening a new file?',
                                                   QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No | QtWidgets.QMessageBox.Cancel)
    
            if result == QtWidgets.QMessageBox.Yes:
                # Save the current scene and open the selected file
                self.saveAndOpenSelectedFile()
                return
            elif result == QtWidgets.QMessageBox.Cancel:
                # User canceled the operation, do nothing
                return
    
        # If there are no unsaved changes or the user chooses not to save, proceed with opening the selected file
        if self.selected_file_path:
            # Check if there is a saved file
            if cmds.file(q=True, sceneName=True):
                # If a file is already open, close it before opening the new file
                cmds.file(new=True, force=True)
            # Open the selected file
            self.openSelectedFile()
    
    def saveFile(self):
        cmds.file(save=True)
    
    def saveAsFile(self):
        file_path = cmds.fileDialog2(dialogStyle=2, fm=0, fileFilter='Maya Files (*.ma *.mb);;Maya ASCII (*.ma);;Maya Binary (*.mb)')
        if file_path:
            cmds.file(rename=file_path[0])
            cmds.file(save=True)
            
    def saveAndOpenSelectedFile(self):
        # Prompt the user to save the scene with "Save As"
        file_path = cmds.fileDialog2(dialogStyle=2, fm=0, fileFilter='Maya Files (*.ma *.mb);;Maya ASCII (*.ma);;Maya Binary (*.mb)')
        if file_path:
            cmds.file(rename=file_path[0])
            cmds.file(save=True)
            # After saving, check if the selected file is not empty and open it
            if self.selected_file_path:
                self.openSelectedFile()
            
    def openSelectedFile(self):
        # Open the selected file
        cmds.file(self.selected_file_path, open=True, force=True)
        
    def searchFiles(self, existing_results=None):
        search_text = self.search_bar.text().lower()
        selected_directory = self.folder_path_lineedit.text()
        selected_file_type = self.file_type_dropdown.currentText().lower()
        results = []
    
        # Check if there is a last selected folder path and use it if present
        if selected_directory and not existing_results:
            selected_directory = self.last_selected_folder_path
    
        # Search only within the last selected folder
        for root, dirs, files in os.walk(selected_directory):
            for file in files:
                file_lower = file.lower()
                if search_text in file_lower and file_lower.endswith(('.mb', '.ma', '.fbx', '.obj', '.abc')):
                    if selected_file_type == "all" or file_lower.endswith(selected_file_type):
                        # Append the full file path to the results list
                        full_file_path = os.path.normpath(os.path.join(root, file))
                        results.append(full_file_path)
    
        print("Selected Directory:", selected_directory)
        print("Search Results:", results)
    
        # Combine existing results with new results if available
        if existing_results:
            results.extend(existing_results)
    
        # Clear previous items from the list
        self.results_list.clear()
    
        # Add filtered items to the list
        self.results_list.addItems(results)
    
        # Clear selection in the file views
        for view in self.file_views:
            view.clearSelection()
        
    def updateFiltersAndSearch(self):
        # Check if there is text in the search bar
        if self.search_bar.text():
            # If there is text, run the search function with the current dropdown filter applied
            self.searchFiles()
            
# Main entry point --------------------------------------------------------
# Inside the main entry point
if __name__ == '__main__':
    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication(sys.argv)

    try:
        # Check Asset Browser status from preferences
        status = read_preferences('Asset Browser Status')
        if status == 'Open':
            # If Asset Browser was open, activate the existing window
            existing_app = QtWidgets.QApplication.instance()
            for widget in existing_app.topLevelWidgets():
                if isinstance(widget, AssetBrowser):
                    widget.activateWindow()
                    widget.raise_()
                    break
        else:
            # If Asset Browser was closed, set the status to Open and show the window
            # Populate project dropdown list
            populate_project_dropdown(asset_browser.project_combo_box)

            # Read asset directories from preferences file
            asset_dir = read_preferences('Asset Directory')
            publish_asset_dir = read_preferences('Publish Asset Directory')

            # Check if the asset directories are retrieved properly
            if asset_dir is None or publish_asset_dir is None:
                raise ValueError("Asset directory or publish asset directory is not set in preferences.")

            # Create the AssetBrowser instance with both asset_dir and publish_asset_dir arguments
            asset_browser = AssetBrowser(asset_dir, publish_asset_dir)

            asset_browser.show()
            write_preferences('Asset Browser Status', 'Open')  # Update the status after showing the window

        # Restore UI preferences
        ui_size, ui_location = restore_ui_preferences()
        if ui_size and ui_location:
            # Ensure the existing UI is activated/selected if it's already open
            if 'asset_browser' in locals():
                asset_browser.resize(ui_size)
                asset_browser.move(ui_location)
                asset_browser.activateWindow()
                asset_browser.raise_()

        # Register the function to save UI preferences on window close
        if 'asset_browser' in locals():
            asset_browser.closeEvent = lambda event: on_window_close(asset_browser)

        # Register cleanup function to close file handles when the script exits
        def close_file_handles():
            for obj in gc.get_objects():
                if hasattr(obj, 'close'):
                    try:
                        obj.close()
                    except Exception as e:
                        print("Error occurred while closing:", e)

        atexit.register(close_file_handles)

        # In Maya, let Maya handle the event loop
        if 'maya' in sys.executable.lower():
            pass  # In Maya, let Maya handle the event loop
        else:
            sys.exit(app.exec_())

    except Exception as e:
        print("An exception occurred:", e)