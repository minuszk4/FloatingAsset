from PyQt5.QtWidgets import QWidget, QPushButton, QVBoxLayout, QFileDialog, QApplication
import sys

class AssetSelector(QWidget):
    def __init__(self, callback):
        super().__init__()
        self.callback = callback
        self.initUI()

    def initUI(self):
        self.setWindowTitle("Chọn Asset")
        self.setGeometry(100, 100, 300, 100)

        btn = QPushButton("Chọn File APNG/GIF", self)
        btn.clicked.connect(self.openFileDialog)

        layout = QVBoxLayout()
        layout.addWidget(btn)
        self.setLayout(layout)

    def openFileDialog(self):
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Chọn File", "", "Images (*.gif *.apng);;All Files (*)", options=options
        )
        if file_path:
            self.callback(file_path)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = AssetSelector(lambda path: print("Chọn:", path))
    window.show()
    sys.exit(app.exec_())
