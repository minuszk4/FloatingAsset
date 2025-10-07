from PyQt5.QtWidgets import QLabel, QMenu
from PyQt5.QtGui import QMovie, QPixmap, QCursor
from PyQt5.QtCore import Qt

class AssetViewer(QLabel):
    def __init__(self, file_path, asset_id):
        super().__init__()
        self.asset_id = asset_id
        self.file_path = file_path

        self.setMouseTracking(True)
        self.resizing = False
        self.drag_position = None
        self.resize_margin = 10
        self.original_size = None
        self.is_hidden = False
        self.allow_overlap = False  # Mặc định luôn trên cùng
        self.update_layer_state()


        if file_path.lower().endswith(".gif"):
            self.movie = QMovie(file_path)
            self.setMovie(self.movie)
            self.movie.start()
            self.original_size = self.movie.frameRect().size()
        else:
            pixmap = QPixmap(file_path)
            self.setPixmap(pixmap)
            self.original_size = pixmap.size()

        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_NoSystemBackground, True)

        self.setScaledContents(True)
        self.resize(self.original_size)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            if self.is_in_resize_zone(event.pos()):
                self.resizing = True
            else:
                self.drag_position = event.globalPos() - self.frameGeometry().topLeft()
        elif event.button() == Qt.RightButton:
            self.show_context_menu(event.pos())

    def mouseMoveEvent(self, event):
        if self.resizing:
            new_width = max(event.x(), 50)
            new_height = max(event.y(), 50)
            self.resize(new_width, new_height)
        elif self.drag_position and event.buttons() == Qt.LeftButton:
            self.move(event.globalPos() - self.drag_position)
        else:
            if self.is_in_resize_zone(event.pos()):
                self.setCursor(QCursor(Qt.SizeFDiagCursor))
            else:
                self.setCursor(QCursor(Qt.ArrowCursor))

    def mouseReleaseEvent(self, event):
        self.resizing = False
        self.drag_position = None

    def is_in_resize_zone(self, pos):
        return pos.x() >= self.width() - self.resize_margin and pos.y() >= self.height() - self.resize_margin

    def show_context_menu(self, pos):
        menu = QMenu(self)
        menu.addAction("Thu nhỏ", lambda: self.resize_asset(0.5))
        menu.addAction("Phóng to", lambda: self.resize_asset(1.5))
        menu.addAction("Khôi phục kích thước gốc", lambda: self.resize_asset(1.0))
        menu.addAction("Ẩn", self.toggle_visibility)

        layer_action = menu.addAction("Cho phép các cửa sổ khác đè lên")
        layer_action.setCheckable(True)
        layer_action.setChecked(self.allow_overlap)
        layer_action.triggered.connect(self.toggle_layer_mode)

        menu.exec_(self.mapToGlobal(pos))


    def resize_asset(self, scale_factor):
        new_width = int(self.original_size.width() * scale_factor)
        new_height = int(self.original_size.height() * scale_factor)
        self.resize(new_width, new_height)

    def toggle_visibility(self):
        if self.is_hidden:
            self.show()
            self.is_hidden = False
        else:
            self.hide()
            self.is_hidden = True
    def update_layer_state(self):
        if self.allow_overlap:
            self.setWindowFlags(Qt.FramelessWindowHint | Qt.Tool)
        else:
            self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.show()
    def toggle_layer_mode(self, checked):
        self.allow_overlap = checked
        self.update_layer_state()
