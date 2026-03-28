from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QListWidget,
    QFileDialog, QLabel, QHBoxLayout
)
from player import AudioPlayer
from media_loader import list_mp4
from track_view import TrackDetailWindow
from PyQt5.QtCore import Qt  
import os

class PlayerWindow(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Player de música")
        self.resize(800, 600)

        layout = QVBoxLayout()
        btn_open = QPushButton("Abrir pasta")
        self.list_widget = QListWidget()
        self.status = QLabel("Nenhuma faixa selecionada")
        controls = QHBoxLayout()
        btn_play = QPushButton("Play")
        btn_stop = QPushButton("Stop")
        btn_close = QPushButton("Fechar")
        controls.addWidget(btn_play)
        controls.addWidget(btn_stop)
        controls.addWidget(btn_close)

        layout.addWidget(btn_open)
        layout.addWidget(self.list_widget)
        layout.addLayout(controls)
        layout.addWidget(self.status)
        self.setLayout(layout)

        self.player = AudioPlayer()
        self.detail_window = None
        self.playlist_paths = []

        btn_open.clicked.connect(self.open_folder)
        self.list_widget.itemDoubleClicked.connect(self.open_detail)
        btn_play.clicked.connect(self.play_button_clicked)
        btn_stop.clicked.connect(self.player.stop)
        btn_close.clicked.connect(self.close)

    def open_folder(self):
        pasta = QFileDialog.getExistingDirectory(self, "Escolha pasta com músicas")
        if not pasta:
            return
        arquivos = list_mp4(pasta)
        self.list_widget.clear()
        self.playlist_paths = arquivos
        for f in arquivos:
            self.list_widget.addItem(f)
        # preload playlist into player (do not start)
        self.player.load_playlist(self.playlist_paths, 0)
        self.status.setText(f"{len(self.playlist_paths)} faixas carregadas")

    def open_detail(self, item_or_obj=None):
        if item_or_obj is None:
            item = self.list_widget.currentItem()
            if item is None:
                return
            path = item.text()
            start_index = self.playlist_paths.index(path) if path in self.playlist_paths else 0
        elif hasattr(item_or_obj, "text"):
            path = item_or_obj.text()
            start_index = self.playlist_paths.index(path) if path in self.playlist_paths else 0
        else:
            path = str(item_or_obj)
            start_index = 0

        if self.playlist_paths:
            self.player.load_playlist(self.playlist_paths, start_index)
        else:
            self.player.load_playlist([path], 0)

        # cria janela TOP-LEVEL (sem parent) para abrir separada
        self.detail_window = TrackDetailWindow(path, player=self.player)
        self.detail_window.setAttribute(Qt.WA_DeleteOnClose)
        self.detail_window.show()
        self.detail_window.raise_()
        self.detail_window.activateWindow()
        self.status.setText(os.path.basename(path))

    def stop(self):
        try:
            self.player.stop()
        except Exception:
            pass

    def closeEvent(self, event):
        self.stop()
        event.accept()
        
    def play_button_clicked(self):
        item = self.list_widget.currentItem()
        if item is None:
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.information(self, "Seleção", "Selecione uma faixa antes de tocar.")
            return
        self.open_detail(item)