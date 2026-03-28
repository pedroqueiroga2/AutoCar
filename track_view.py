from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QSlider, QSizePolicy
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPixmap, QFont, QImage, QTransform, QPainter, QColor
import os
from io import BytesIO

# tentativa de usar mutagen para metadados/capas MP4
try:
    from mutagen.mp4 import MP4, MP4Cover
except Exception:
    MP4 = None
    MP4Cover = None

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
        self.cover.setStyleSheet("border-radius:8px; background:transparent;")

        # rotation state for disc (se usado) — inicializa antes de chamar _set_cover_or_disc
        self._rot_angle = 0
        self._rot_timer = QTimer(self)
        self._rot_timer.setInterval(50)
        self._rot_timer.timeout.connect(self._rotate_disc)
        self._has_disc = False

        top.addWidget(self.cover)
        # mostra o disco padrão até carregarmos metadados
        self._set_cover_or_disc(None)

        # meta (title / artist) with semi-transparent background boxes
        meta = QVBoxLayout()
        self.title = QLabel(os.path.basename(path))
        f = QFont(); f.setPointSize(14); f.setBold(True)
        self.title.setFont(f)
        self.title.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.title.setStyleSheet("background: rgba(0,0,0,160); color: #ffffff; padding:6px; border-radius:6px;")

        # label padrão para artista/álbum quando metadados inexistentes
        self.artist = QLabel("Artista Desconhecido - Álbum Desconhecido")
        self.artist.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.artist.setStyleSheet("background: rgba(0,0,0,120); color: #e6eef6; padding:4px; border-radius:6px;")
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

        # progress + time (time labels with semi-transparent background)
        prog_row = QHBoxLayout()
        self.time_label = QLabel("0:00")
        self.time_label.setStyleSheet("background: rgba(0,0,0,120); color: #e6eef6; padding:4px; border-radius:4px;")
        self.time_label.setFixedWidth(48)
        self.time_label.setAlignment(Qt.AlignCenter)

        self.slider = QSlider(Qt.Horizontal)
        self.slider.setRange(0, 1000)
        self.slider.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        self.total_label = QLabel("0:00")
        self.total_label.setStyleSheet("background: rgba(0,0,0,120); color: #e6eef6; padding:4px; border-radius:4px;")
        self.total_label.setFixedWidth(48)
        self.total_label.setAlignment(Qt.AlignCenter)

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

        # rotation state for disc (if used)
        self._rot_angle = 0
        self._rot_timer = QTimer(self)
        self._rot_timer.setInterval(50)
        self._rot_timer.timeout.connect(self._rotate_disc)

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
            # atualiza título, artist e capa inicial (caso playlist já carregada)
            self._on_track_changed()

    # comandos ligados ao player
    def on_play_pause(self):
        if not self.player:
            return
        if self.player.is_playing():
            self.player.pause()
        else:
            self.player.play()
        self._update_play_button_text()
        # start/stop disc rotation based on playing
        if self.player.is_playing():
            if getattr(self, "_has_disc", False):
                self._rot_timer.start()
        else:
            self._rot_timer.stop()

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
        # detecta mudança de faixa vinda de outro lugar
        if self.player:
            idx = getattr(self.player, "index", -1)
            if idx != getattr(self, "current_index", -1):
                self._on_track_changed()

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
                # atualizar artist/album/capa
                artist, album, cover_pix = self._extract_metadata(newpath)
                artist_text = artist if artist else "Artista Desconhecido"
                album_text = album if album else "Álbum Desconhecido"
                self.artist.setText(f"{artist_text} - {album_text}")
                self._set_cover_or_disc(cover_pix)
                # opcional: atualizar total_label imediatamente se disponível
                length = self.player.get_length()
                if length > 0:
                    self.total_label.setText(self._ms_to_str(length))
                # atualiza progresso agora
                self._update_progress()

    def _update_play_button_text(self):
        self.btn_play.setText("Pause" if self.player and self.player.is_playing() else "▶")
        # control rot timer based on playing
        if getattr(self, "_has_disc", False):
            if self.player and self.player.is_playing():
                self._rot_timer.start()
            else:
                self._rot_timer.stop()

    def _ms_to_str(self, ms: int):
        s = int(ms/1000)
        return f"{s//60}:{s%60:02d}"

    # --- cover / metadata helpers ---
    def _extract_metadata(self, path):
        """Tenta extrair artista, album e cover (QPixmap) do arquivo (MP4)."""
        artist = None
        album = None
        cover_pix = None

        # primeiro tenta mutagen MP4 (se disponível)
        if MP4:
            try:
                mp4 = MP4(path)
                tags = mp4.tags or {}
                # mp4 tags: '\xa9ART' artist, '\xa9alb' album
                artist = tags.get("\xa9ART", [None])[0]
                album = tags.get("\xa9alb", [None])[0]
                covr = tags.get("covr")
                if covr:
                    # covr is list of MP4Cover; take first
                    imgdata = covr[0]
                    if isinstance(imgdata, MP4Cover):
                        imgdata = bytes(imgdata)
                    # build QPixmap from bytes
                    img = QImage.fromData(imgdata)
                    if not img.isNull():
                        cover_pix = QPixmap.fromImage(img)
            except Exception:
                # falha silenciosa; fallback abaixo
                pass

        # se tiver cover_path passado como argumento anterior, já estaria tratado,
        # e caso não tenhamos cover_pix, retornamos None e a UI desenha disco
        return artist, album, cover_pix

    def _set_cover_or_disc(self, cover_pix: QPixmap):
        """Configura o QLabel de capa com a pixmap ou disco girando."""
        if cover_pix and not cover_pix.isNull():
            self._has_disc = False
            self._rot_timer.stop()
            pix = cover_pix.scaled(self.cover.width(), self.cover.height(),
                                   Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
            self.cover.setPixmap(pix)
        else:
            # desenhar disco base e iniciar rotação se estiver tocando
            self._has_disc = True
            base = self._create_disc_pixmap(self.cover.width(), self.cover.height())
            self._disc_base = base
            self.cover.setPixmap(base)
            if self.player and self.player.is_playing():
                self._rot_timer.start()
            else:
                self._rot_timer.stop()

    def _create_disc_pixmap(self, w, h):
        pix = QPixmap(w, h)
        pix.fill(Qt.transparent)
        p = QPainter(pix)
        p.setRenderHint(QPainter.Antialiasing, True)
        cx, cy = w/2, h/2
        R = min(w, h) * 0.45

        # outer: leve gradiente claro
        grad = QColor(180, 180, 180)
        p.setBrush(grad)
        p.setPen(Qt.NoPen)
        p.drawEllipse(int(cx-R), int(cy-R), int(2*R), int(2*R))

        # middle darker ring
        p.setBrush(QColor(50, 50, 60))
        inner = R * 0.72
        p.drawEllipse(int(cx-inner), int(cy-inner), int(2*inner), int(2*inner))

        # subtle highlight arc
        p.setPen(Qt.NoPen)
        highlight = QColor(255,255,255,30)
        p.setBrush(highlight)
        p.drawPie(int(cx-R), int(cy-R), int(2*R), int(2*R), 30*16, 40*16)

        # center hole
        hole = R * 0.16
        p.setBrush(QColor(20, 20, 20))
        p.drawEllipse(int(cx-hole), int(cy-hole), int(2*hole), int(2*hole))

        p.end()
        return pix

    def _rotate_disc(self):
        """Gira a imagem do disco (self._disc_base) e aplica no label."""
        if not getattr(self, "_has_disc", False):
            return
        self._rot_angle = (self._rot_angle + 6) % 360
        transform = QTransform().rotate(self._rot_angle)
        rotated = self._disc_base.transformed(transform, Qt.SmoothTransformation)
        # centered crop to label size
        rw = rotated.width(); rh = rotated.height()
        lw = self.cover.width(); lh = self.cover.height()
        # if rotated is larger, scale down then crop center
        if rw != lw or rh != lh:
            rotated = rotated.scaled(lw, lh, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
        self.cover.setPixmap(rotated)

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
        try:
            self.timer.stop()
            self._rot_timer.stop()
        except:
            pass
        event.accept()