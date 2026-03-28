from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QSlider, QSizePolicy
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPixmap, QFont
import os

class TrackDetailWindow(QWidget):
    def __init__(self, path: str, player=None, parent=None, cover_path=None):
        super().__init__(parent)
        self.path = path
        self.player = player
        self.setWindowTitle(os.path.basename(path))
        self.resize(520, 320)
        self.setStyleSheet(self._default_qss())

        main = QVBoxLayout()
        main.setContentsMargins(20,20,20,20)
        main.setSpacing(12)

        # Top: cover + meta
        top = QHBoxLayout()
        # cover
        self.cover = QLabel()
        self.cover.setFixedSize(140,140)
        self.cover.setStyleSheet("border-radius:8px; background:#222;")
        if cover_path and os.path.exists(cover_path):
            pix = QPixmap(cover_path).scaled(140,140, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
            self.cover.setPixmap(pix)
        top.addWidget(self.cover)

        # meta (title / artist)
        meta = QVBoxLayout()
        self.title = QLabel(os.path.basename(path))
        f = QFont(); f.setPointSize(14); f.setBold(True)
        self.title.setFont(f)
        self.artist = QLabel("Artista - Álbum")
        meta.addWidget(self.title)
        meta.addWidget(self.artist)
        meta.addStretch()
        top.addLayout(meta)

        main.addLayout(top)

        # Center big controls row
        controls = QHBoxLayout()
        self.btn_prev = QPushButton("◀◀")
        self.btn_play = QPushButton("▶")
        self.btn_next = QPushButton("▶▶")
        for btn in (self.btn_prev, self.btn_play, self.btn_next):
            btn.setFixedSize(72,72)
            btn.setStyleSheet("border-radius:36px;")  # círculo
        controls.addStretch()
        controls.addWidget(self.btn_prev)
        controls.addSpacing(12)
        controls.addWidget(self.btn_play)
        controls.addSpacing(12)
        controls.addWidget(self.btn_next)
        controls.addStretch()
        main.addLayout(controls)

        # progress + time
        prog_row = QHBoxLayout()
        self.time_label = QLabel("0:00")
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setRange(0, 1000)
        self.slider.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.total_label = QLabel("0:00")
        prog_row.addWidget(self.time_label)
        prog_row.addWidget(self.slider)
        prog_row.addWidget(self.total_label)
        main.addLayout(prog_row)

        # back button
        back = QPushButton("Voltar")
        main.addWidget(back, alignment=Qt.AlignCenter)

        self.setLayout(main)

        # timer para atualizar progresso
        self.timer = QTimer(self)
        self.current_index = self.player.index if self.player else -1
        self.timer.setInterval(500)
        self.timer.timeout.connect(self._update_progress)

        # conexões (ligue aos métodos do AudioPlayer)
        self.btn_play.clicked.connect(self.on_play_pause)
        self.btn_prev.clicked.connect(lambda: self._client_prev())
        self.btn_next.clicked.connect(lambda: self._client_next())
        back.clicked.connect(self.close)
        self.slider.sliderReleased.connect(self.on_seek)

        # inicialização sem autoplay
        if self.player:
            # posicione índice sem tocar; timer roda para atualizar UI
            if path in getattr(self.player, "playlist", []):
                self.player.index = self.player.playlist.index(path)
            else:
                self.player.load_playlist([path], 0)
            self.timer.start()
            self._update_play_button_text()

    # comandos ligados ao player
    def on_play_pause(self):
        if not self.player:
            return
        if self.player.is_playing():
            self.player.pause()
        else:
            self.player.play()
        self._update_play_button_text()

    def _client_prev(self):
        if self.player:
            self.player.previous()
            self._on_track_changed()
            self._update_play_button_text()

    def _client_next(self):
        if self.player:
            self.player.next()
            self._on_track_changed()
            self._update_play_button_text()

    def on_seek(self):
        if not self.player:
            return
        length = self.player.get_length()
        if length > 0:
            pos = self.slider.value() / 1000.0
            ms = int(pos * length)
            self.player.player.set_time(ms)

    def _update_progress(self):
        if not self.player:
            return
        length = self.player.get_length()
        t = max(0, self.player.get_time())
        if length > 0:
            self.slider.blockSignals(True)
            self.slider.setValue(int((t / length) * 1000))
            self.slider.blockSignals(False)
            self.time_label.setText(self._ms_to_str(t))
            self.total_label.setText(self._ms_to_str(length))
        self._update_play_button_text()
        
        
    def _on_track_changed(self):
        if not self.player:
            return
        idx = getattr(self.player, "index", -1)
        if idx != self.current_index:
            self.current_index = idx
            if 0 <= idx < len(getattr(self.player, "playlist", [])):
                newpath = self.player.playlist[idx]
                self.title.setText(os.path.basename(newpath))
                # opcional: atualizar total_label imediatamente se disponível
                length = self.player.get_length()
                if length > 0:
                    self.total_label.setText(self._ms_to_str(length))
                # atualiza progresso agora
                self._update_progress()

    def _update_play_button_text(self):
        self.btn_play.setText("Pause" if self.player and self.player.is_playing() else "▶")

    def _ms_to_str(self, ms: int):
        s = int(ms/1000)
        return f"{s//60}:{s%60:02d}"

    def _default_qss(self):
        return """
        QWidget { background: qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 #0f1720, stop:1 #111827); color: #e6eef6; }
        QPushButton { background: #2b6ef6; color: white; border: none; padding: 6px 12px; border-radius:6px; }
        QPushButton#small { background: transparent; color:#cfe3ff; }
        QSlider::groove:horizontal { height:6px; background:#3a3f44; border-radius:3px; }
        QSlider::handle:horizontal { background:#2b6ef6; width:12px; margin:-4px 0; border-radius:6px; }
        QLabel { color: #e6eef6; }
        """

    def closeEvent(self, event):
        try: self.timer.stop()
        except: pass
        event.accept()