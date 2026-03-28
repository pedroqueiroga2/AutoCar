import sys
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QVBoxLayout, QHBoxLayout, QShortcut
from PyQt5.QtGui import QKeySequence
from player_view import PlayerWindow

app = QApplication(sys.argv)

window = QWidget()
window.setWindowTitle("AutoUX")
window.resize(900, 700)

# Layout
main_layout = QVBoxLayout()
top_row = QHBoxLayout()
btn_music = QPushButton("Player de música")
btn_full = QPushButton("Tela Cheia")
btn_quit = QPushButton("Fechar")
top_row.addWidget(btn_music)
top_row.addWidget(btn_full)
top_row.addWidget(btn_quit)
main_layout.addLayout(top_row)
window.setLayout(main_layout)

# Player window (top-level)
player = PlayerWindow()

# Actions
def abrir_player():
    player.show()
    player.raise_()
    player.activateWindow()

def toggle_fullscreen():
    if window.isFullScreen():
        window.showNormal()
        btn_full.setText("Tela Cheia")
    else:
        window.showFullScreen()
        btn_full.setText("Sair Fullscreen")

def do_quit():
    try:
        player.stop()
    except Exception:
        pass
    app.quit()

btn_music.clicked.connect(abrir_player)
btn_full.clicked.connect(toggle_fullscreen)
btn_quit.clicked.connect(do_quit)

# F11 shortcut for fullscreen toggle
shortcut = QShortcut(QKeySequence("F11"), window)
shortcut.activated.connect(toggle_fullscreen)

# Ensure player stops on app exit
app.aboutToQuit.connect(player.stop)

# center and show
screen = app.primaryScreen().availableGeometry()
x = (screen.width() - window.width()) // 2
y = (screen.height() - window.height()) // 2
window.move(x, y)
window.show()

sys.exit(app.exec_())