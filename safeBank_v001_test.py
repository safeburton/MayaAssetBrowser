import os
from PySide2 import QtWidgets, QtGui

# Define the AssetBrowser class
class AssetBrowser(QtWidgets.QWidget):
    def __init__(self, asset_dir, parent=None):
        super(AssetBrowser, self).__init__(parent)
        self.asset_dir = asset_dir
        self.levels = 4  # Number of levels to display
        self.file_lists = []  # List to store file list widgets for each level
        self.initUI()

    # Initialize the user interface
    def initUI(self):
        self.setWindowTitle('Asset Browser')
        layout = QtWidgets.QHBoxLayout(self)

        # Create file list widgets for each level
        for _ in range(self.levels):
            file_list_widget = QtWidgets.QTreeWidget()
            file_list_widget.setHeaderHidden(True)
            file_list_widget.itemClicked.connect(self.itemClicked)
            self.file_lists.append(file_list_widget)
            layout.addWidget(file_list_widget)

        # Populate file lists with contents from the asset directory
        self.populateFileLists(self.asset_dir)

    # Populate file lists recursively with contents from directories
    def populateFileLists(self, directory):
        for level, file_list_widget in enumerate(self.file_lists):
            file_list_widget.clear()
            if os.path.exists(directory) and os.listdir(directory):  # Check if directory exists and is not empty
                self.populateDirectory(directory, file_list_widget)
                directory = os.path.join(directory, os.listdir(directory)[0])  # Go down a level
            else:
                break  # Stop populating lists if directory is empty or doesn't exist

    # Populate a specific file list with contents from a directory
    def populateDirectory(self, directory, file_list_widget):
        for item_name in sorted(os.listdir(directory)):
            item_path = os.path.join(directory, item_name)
            item = QtWidgets.QTreeWidgetItem(file_list_widget)
            item.setText(0, item_name)
            if os.path.isdir(item_path):
                item.setIcon(0, QtGui.QIcon.fromTheme("folder"))

    # Handle item click event
    def itemClicked(self, item, column):
        current_list_widget = self.sender()
        current_column_index = self.file_lists.index(current_list_widget)

        if column == current_column_index:  # Only proceed if the click is in the correct column
            if column < self.levels - 1:  # Only proceed if not in the last column
                selected_directory = self.asset_dir
                for level in range(column + 1):
                    selected_directory = os.path.join(selected_directory, self.file_lists[level].currentItem().text(0))
                if os.path.isdir(selected_directory):
                    self.populateFileList(selected_directory, self.file_lists[column + 1])  # Populate next column

    # Populate a specific file list with contents from a directory
    def populateFileList(self, directory, file_list_widget):
        file_list_widget.clear()
        self.populateDirectory(directory, file_list_widget)


if __name__ == '__main__':
    import sys
    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication(sys.argv)
    asset_dir = r"D:\WORKSPACE\new_folderStructure\GF\3D\ASSETS"
    asset_browser = AssetBrowser(asset_dir)
    asset_browser.show()
    sys.exit(app.exec_())
