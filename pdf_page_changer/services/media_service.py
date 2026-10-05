from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QObject, QUrl, Signal
from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer
from PySide6.QtMultimediaWidgets import QVideoWidget


class MediaService(QObject):
    error = Signal(str)
    playback_changed = Signal(bool)

    def __init__(self):
        super().__init__()
        self._player = QMediaPlayer(self)
        self._audio = QAudioOutput(self)
        self._player.setAudioOutput(self._audio)
        self._player.setLoops(QMediaPlayer.Loops.Infinite)
        self._player.errorOccurred.connect(self._on_error)
        self._player.playbackStateChanged.connect(self._on_state_changed)

    def attach_video_output(self, video_widget: QVideoWidget) -> None:
        self._player.setVideoOutput(video_widget)

    def play(self, path: Path) -> None:
        if not path.exists():
            raise FileNotFoundError(f"No existe el video: {path}")
        self._player.setSource(QUrl.fromLocalFile(str(path.resolve())))
        self._player.play()

    def stop(self) -> None:
        self._player.stop()
        self._player.setSource(QUrl())

    def is_playing(self) -> bool:
        return self._player.playbackState() == QMediaPlayer.PlaybackState.PlayingState

    def _on_error(self, error: QMediaPlayer.Error, message: str) -> None:
        if error != QMediaPlayer.Error.NoError:
            self.error.emit(message or "Error de reproducción de video.")

    def _on_state_changed(self, state: QMediaPlayer.PlaybackState) -> None:
        self.playback_changed.emit(
            state == QMediaPlayer.PlaybackState.PlayingState
        )
