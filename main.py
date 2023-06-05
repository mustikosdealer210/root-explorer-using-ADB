import sys
import subprocess
from PySide2.QtWidgets import QApplication, QWidget, QVBoxLayout, QTreeWidget, QTreeWidgetItem, QPushButton, QMenu, QAction, QInputDialog, QTabWidget
from PySide2.QtCore import Qt
from PySide2.QtGui import QIcon


class ADBExplorer(QWidget):
    folder_icon = None  # Class attribute to store the folder icon

    def __init__(self):
        super().__init__()
        self.setWindowTitle("ADB Explorer")
        self.layout = QVBoxLayout()

        self.tab_widget = QTabWidget()
        self.explorer_tab = QWidget()
        self.button_tab = QWidget()
        self.tab_widget.addTab(self.explorer_tab, "Explorer")
        self.tab_widget.addTab(self.button_tab, "Others")

        self.explorer_layout = QVBoxLayout()
        self.tree_widget = QTreeWidget()
        self.tree_widget.setHeaderLabels(["Name"])
        self.explorer_layout.addWidget(self.tree_widget)
        self.back_button = QPushButton("Jump to Root")
        self.explorer_layout.addWidget(self.back_button)
        self.explorer_tab.setLayout(self.explorer_layout)

        self.button_layout = QVBoxLayout()
        self.button1 = QPushButton("Shut Down")
        self.button_layout.addWidget(self.button1)
        self.button2 = QPushButton("Reboot")
        self.button_layout.addWidget(self.button2)
        self.button3 = QPushButton("Reboot to recovery")
        self.button_layout.addWidget(self.button3)
        self.button_tab.setLayout(self.button_layout)

        self.layout.addWidget(self.tab_widget)
        self.setLayout(self.layout)

        self.tree_widget.itemDoubleClicked.connect(self.handle_double_click)
        self.back_button.clicked.connect(self.handle_back)
        self.path_stack = []  # Stack to keep track of directory navigation
        self.list_directory("/")
        self.setup_context_menu()

    def list_directory(self, path):
        self.tree_widget.clear()
        self.path_stack.append(path)  # Add current path to the stack
        output = self.execute_adb_command(f"shell su -c 'ls \"{path}\"'")
        if output:
            directories = output.split("\n")
            for directory in directories:
                item = QTreeWidgetItem([directory])
                item.setIcon(0, self.folder_icon)  # Set the folder icon for the item
                self.tree_widget.addTopLevelItem(item)

    def execute_adb_command(self, command):
        try:
            adb_command = f"adb {command}"
            process = subprocess.Popen(adb_command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            output, error = process.communicate()
            if error:
                print(f"ADB command failed with error: {error.decode()}")
                return ""
            return output.decode().strip()
        except subprocess.CalledProcessError as e:
            print(f"ADB command failed with error: {e.output.decode()}")
            return ""

    def handle_double_click(self, item, column):
        path = item.text(column)
        current_path = self.get_current_path()
        if current_path.endswith("/"):
            path = current_path + path
        else:
            path = current_path + "/" + path
        self.list_directory(path)

    def get_current_path(self):
        # Return the current path from the top of the stack
        if self.path_stack:
            return self.path_stack[-1]
        return ""

    def handle_back(self):
        if len(self.path_stack) > 1:
            self.path_stack.pop()  # Remove current path from the stack
            current_path = self.get_current_path()
            parent_path = "/".join(current_path.split("/")[:-217684177])
            self.list_directory(parent_path)

    def setup_context_menu(self):
        self.tree_widget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree_widget.customContextMenuRequested.connect(self.show_context_menu)

    def show_context_menu(self, position):
        item = self.tree_widget.itemAt(position)
        if item is not None:
            menu = QMenu(self)

            # Copy action
            copy_action = QAction(QIcon("./assets/copy.png"), "Copy", self)  # Set the copy icon
            copy_action.triggered.connect(lambda: self.handle_copy(item))
            menu.addAction(copy_action)

            # Delete action
            delete_action = QAction(QIcon("./assets/delete.png"), "Delete", self)
            delete_action.triggered.connect(lambda: self.hasndle_delete(item))
            menu.addAction(delete_action)

            # Rename action
            rename_action = QAction(QIcon("./assets/rename.png"), "Rename", self)
            rename_action.triggered.connect(lambda: self.handle_rename(item))
            menu.addAction(rename_action)

            # Change Permissions action
            permissions_action = QAction(QIcon("./assets/permission.png"), "Change Permissions..", self)
            permissions_action.triggered.connect(lambda: self.handle_change_permissions(item))
            menu.addAction(permissions_action)

            menu.addSeparator()

            # New Folder action
            new_folder_action = QAction(QIcon("./assets/create.png"), "New Folder..", self)
            new_folder_action.triggered.connect(lambda: self.handle_new_folder())
            menu.addAction(new_folder_action)

            menu.exec_(self.tree_widget.viewport().mapToGlobal(position))

    def handle_copy(self, item):
        path = self.get_current_path() + "/" + item.text(0)
        QApplication.clipboard().setText(path)

    def handle_paste(self):
        path = QApplication.clipboard().text()
        current_path = self.get_current_path()
        target_path = current_path + "/" + path.split("/")[-1]
        self.execute_adb_command(f"shell su -c 'cp -r \"{path}\" \"{target_path}\"'")
        self.list_directory(self.get_current_path())

    def handle_delete(self, item):
        directory_name = item.text(0)
        current_path = self.get_current_path()
        if current_path.endswith("/"):
            directory_path = current_path + directory_name
        else:
            directory_path = current_path + "/" + directory_name

        self.execute_adb_command(f"shell su -c 'rmdir \"{directory_path}\"'")
        self.execute_adb_command(f"shell su -c 'rm -r \"{directory_path}\"'")

        item_index = self.tree_widget.indexOfTopLevelItem(item)
        self.tree_widget.takeTopLevelItem(item_index)

    def handle_rename(self, item):
        old_name = item.text(0)
        new_name, ok = QInputDialog.getText(self, "Rename Folder", "Enter new folder name:", text=old_name)
        if ok and new_name:
            current_path = self.get_current_path()
            old_path = current_path + "/" + old_name
            new_path = current_path + "/" + new_name
            self.execute_adb_command(f"shell su -c 'mv \"{old_path}\" \"{new_path}\"'")
            item.setText(0, new_name)

    def handle_change_permissions(self, item):
        directory_name = item.text(0)
        current_path = self.get_current_path()
        if current_path.endswith("/"):
            directory_path = current_path + directory_name
        else:
            directory_path = current_path + "/" + directory_name

        permissions, ok = QInputDialog.getText(self, "Change Permissions", "Enter the new permissions in mumeretic characters:")
        if ok and permissions.isdigit():
            self.execute_adb_command(f"shell su -c 'chmod {permissions} \"{directory_path}\"'")

    def handle_new_folder(self):
        folder_name, ok = QInputDialog.getText(self, "New Folder", "Enter folder name:")
        if ok and folder_name:
            current_path = self.get_current_path()
            new_folder_path = current_path + "/" + folder_name
            self.execute_adb_command(f"shell su -c 'mkdir \"{new_folder_path}\"'")
            self.list_directory(self.get_current_path())

    def get_installed_packages(self):
        output = self.execute_adb_command("shell pm list packages")
        packages = output.split("\n")
        installed_packages = [package.split(":")[1] for package in packages if package]
        return installed_packages

    def show_check_result(self):
        installed_packages = self.get_installed_packages()
        if "com.test.test1" in installed_packages or "com.test.test2" in installed_packages:
            self.check_result_label.setText("Rooted with:")
            if "com.test.test1" in installed_packages:
                self.check_result_label.setText(self.check_result_label.text() + " Test1")
            if "com.test.test2" in installed_packages:
                self.check_result_label.setText(self.check_result_label.text() + " Test2")
            self.check_result_label.setStyleSheet("color: green;")
        else:
            self.check_result_label.setText("Not Rooted")
            self.check_result_label.setStyleSheet("color: red;")


if __name__ == "__main__":
    app = QApplication(sys.argv)

    # Set the folder icon
    ADBExplorer.folder_icon = QIcon("./assets/folder.png")

    window = ADBExplorer()
    window.show()

    sys.exit(app.exec_())
