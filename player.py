import vlc
from typing import List, Optional

class AudioPlayer:
    def __init__(self):
        self.instance = vlc.Instance("--no-video")
        self.player = self.instance.media_player_new()
        self.playlist: List[str] = []
        self.index: int = -1

    def load_playlist(self, paths: List[str], start_index: int = 0):
        self.playlist = list(paths)
        # não iniciar automaticamente
        if 0 <= start_index < len(self.playlist):
            self.index = start_index
        else:
            self.index = -1

    def play_index(self, i: int):
        if not (0 <= i < len(self.playlist)):
            return
        self.index = i
        media = self.instance.media_new(self.playlist[self.index])
        self.player.set_media(media)
        self.player.play()

    def play(self, path: Optional[str] = None):
        if path is None:
            # se já existe um índice válido, carregue o media e toque
            if self.index >= 0:
                self.play_index(self.index)
            return
        # se veio um path, toque esse arquivo (ou o índice correspondente na playlist)
        if path in self.playlist:
            self.play_index(self.playlist.index(path))
        else:
            self.playlist = [path]
            self.play_index(0)

    def pause(self):
        self.player.pause()

    def stop(self):
        self.player.stop()

    def next(self):
        if not self.playlist:
            return
        nxt = (self.index + 1) if (self.index + 1) < len(self.playlist) else 0
        self.play_index(nxt)

    def previous(self):
        if not self.playlist:
            return
        prev = (self.index - 1) if (self.index - 1) >= 0 else len(self.playlist) - 1
        self.play_index(prev)

    def set_volume(self, vol: int):
        self.player.audio_set_volume(max(0, min(100, int(vol))))

    def get_time(self) -> int:
        return self.player.get_time()  # ms

    def get_length(self) -> int:
        return self.player.get_length()  # ms

    def is_playing(self) -> bool:
        return bool(self.player.is_playing())