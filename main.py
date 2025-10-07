import sys
import os
import json
import winreg as reg
from PyQt5.QtWidgets import QApplication, QMainWindow, QMenu, QAction, QListWidget, QLabel, QVBoxLayout, QWidget, QSystemTrayIcon, QStyle
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt
from asset_selector import AssetSelector
from asset_viewer import AssetViewer
from apng import APNG

CONFIG_FILE = "assets_config.json"

def set_run_at_startup(enable=True):
    exe_path = os.path.abspath(sys.argv[0])
    key = r"Software\Microsoft\Windows\CurrentVersion\Run"
    app_name = "AssetManager"

    with reg.OpenKey(reg.HKEY_CURRENT_USER, key, 0, reg.KEY_ALL_ACCESS) as reg_key:
        if enable:
            reg.SetValueEx(reg_key, app_name, 0, reg.REG_SZ, exe_path)
        else:
            try:
                reg.DeleteValue(reg_key, app_name)
            except FileNotFoundError:
                pass

def is_run_at_startup():
    exe_path = os.path.abspath(sys.argv[0])
    key = r"Software\Microsoft\Windows\CurrentVersion\Run"
    app_name = "AssetManager"

    try:
        with reg.OpenKey(reg.HKEY_CURRENT_USER, key, 0, reg.KEY_READ) as reg_key:
            value, _ = reg.QueryValueEx(reg_key, app_name)
            return value == exe_path
    except FileNotFoundError:
        return False

class AssetManager(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Asset Manager")
        self.setGeometry(100, 100, 400, 300)

        self.setWindowFlags(Qt.Tool)

        self.open_viewers = {}
        self.asset_counter = 0

        menubar = self.menuBar()
        asset_menu = menubar.addMenu("Asset")

        select_action = QAction("Chọn Asset", self)
        select_action.triggered.connect(self.select_asset)
        asset_menu.addAction(select_action)

        show_action = QAction("Hiển thị Asset", self)
        show_action.triggered.connect(self.show_assets)
        asset_menu.addAction(show_action)

        close_action = QAction("Đóng Asset", self)
        close_action.triggered.connect(self.close_assets)
        asset_menu.addAction(close_action)

        minimize_action = QAction("Thu nhỏ (Chạy nền)", self)
        minimize_action.triggered.connect(self.minimize_to_tray)
        asset_menu.addAction(minimize_action)

        self.run_with_windows_action = QAction("Chạy cùng Windows", self, checkable=True)
        self.run_with_windows_action.setChecked(is_run_at_startup())
        self.run_with_windows_action.triggered.connect(self.toggle_run_with_windows)
        asset_menu.addAction(self.run_with_windows_action)

        self.asset_list = QListWidget()
        self.asset_list.setContextMenuPolicy(3)
        self.asset_list.customContextMenuRequested.connect(self.show_asset_menu)
        self.asset_list.itemClicked.connect(self.preview_asset)

        self.preview_label = QLabel("Preview")
        self.preview_label.setFixedSize(200, 200)
        self.preview_label.setStyleSheet("background-color: #333;")

        layout = QVBoxLayout()
        layout.addWidget(self.asset_list)
        layout.addWidget(self.preview_label)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        # System tray icon
        self.tray_icon = QSystemTrayIcon(QIcon(QApplication.style().standardIcon(QStyle.SP_ComputerIcon)))
        tray_menu = QMenu()
        restore_action = QAction("Hiển thị lại", self)
        restore_action.triggered.connect(self.restore_from_tray)
        tray_menu.addAction(restore_action)

        exit_action = QAction("Thoát", self)
        exit_action.triggered.connect(self.exit_app)
        tray_menu.addAction(exit_action)

        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()

        self.load_assets()

    def select_asset(self):
        self.selector = AssetSelector(self.open_asset)
        self.selector.show()

    def open_asset(self, file_path, is_hidden=False, size=None):
        ext = file_path.lower().split('.')[-1]
        if ext == "apng":
            file_path = self.convert_apng_to_gif(file_path)

        asset_id = self.asset_counter
        viewer = AssetViewer(file_path, asset_id)

        if size:
            viewer.resize(size[0], size[1])
        if is_hidden:
            viewer.hide()
            viewer.is_hidden = True

        viewer.show()

        self.open_viewers[asset_id] = viewer
        self.asset_list.addItem(f"{asset_id}: {os.path.basename(file_path)}")
        self.asset_counter += 1

    def show_assets(self):
        for viewer in self.open_viewers.values():
            viewer.show()

    def close_assets(self):
        for viewer in self.open_viewers.values():
            viewer.close()
        self.open_viewers.clear()
        self.asset_list.clear()

    def preview_asset(self, item):
        asset_id = int(item.text().split(":")[0])
        viewer = self.open_viewers.get(asset_id)
        if viewer:
            pixmap = viewer.pixmap() if viewer.pixmap() else viewer.movie.currentPixmap()
            if pixmap:
                self.preview_label.setPixmap(pixmap.scaled(200, 200, aspectRatioMode=1))

    def show_asset_menu(self, pos):
        item = self.asset_list.itemAt(pos)
        if not item:
            return

        asset_id = int(item.text().split(":")[0])
        viewer = self.open_viewers.get(asset_id)
        if not viewer:
            return

        menu = QMenu()
        if viewer.is_hidden:
            menu.addAction("Hiển thị", lambda: self.toggle_asset_visibility(asset_id))
        else:
            menu.addAction("Ẩn", lambda: self.toggle_asset_visibility(asset_id))
        menu.addAction("Xóa", lambda: self.delete_asset(asset_id))
        menu.exec_(self.asset_list.mapToGlobal(pos))

    def toggle_asset_visibility(self, asset_id):
        viewer = self.open_viewers.get(asset_id)
        if viewer:
            if viewer.is_hidden:
                viewer.show()
                viewer.is_hidden = False
            else:
                viewer.hide()
                viewer.is_hidden = True

    def delete_asset(self, asset_id):
        viewer = self.open_viewers.pop(asset_id, None)
        if viewer:
            viewer.close()
        for index in range(self.asset_list.count()):
            item = self.asset_list.item(index)
            if int(item.text().split(":")[0]) == asset_id:
                self.asset_list.takeItem(index)
                break

    def convert_apng_to_gif(self, apng_path):
        gif_path = os.path.splitext(apng_path)[0] + "_temp.gif"
        APNG.open(apng_path).save(gif_path)
        return gif_path

    def save_assets(self):
        data = []
        for asset_id, viewer in self.open_viewers.items():
            size = [viewer.width(), viewer.height()]
            data.append({
                "id": asset_id,
                "path": viewer.file_path,
                "is_hidden": viewer.is_hidden,
                "size": size
            })
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def load_assets(self):
        if not os.path.exists(CONFIG_FILE):
            return
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            for asset in data:
                self.open_asset(asset["path"], is_hidden=asset["is_hidden"], size=asset["size"])

    def minimize_to_tray(self):
        self.hide()
        self.tray_icon.showMessage("Asset Manager", "Ứng dụng đang chạy nền...", QSystemTrayIcon.Information, 2000)

    def restore_from_tray(self):
        self.show()

    def exit_app(self):
        self.save_assets()
        QApplication.quit()

    def closeEvent(self, event):
        self.save_assets()
        event.accept()

    def toggle_run_with_windows(self, checked):
        set_run_at_startup(checked)

def run_app():
    app = QApplication(sys.argv)
    manager = AssetManager()
    manager.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    run_app()
