import sys
import os
import vlc
from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.QtWidgets import QMessageBox, QToolBar, QStatusBar, QLabel, QSlider
from pathlib import Path

class MediaController:
    def __init__(self, video_frame):
        self.instance = vlc.Instance()
        self.player = self.instance.media_player_new()

        if sys.platform.startswith('linux'):
            self.player.set_xwindow(video_frame.winId())
        elif sys.platform == "win32":
            self.player.set_hwnd(video_frame.winId())
        elif sys.platform == "darwin":
            self.player.set_nsobject(int(video_frame.winId()))

    def play(self):
        self.player.play()

    def pause(self):
        self.player.pause()

    def stop(self):
        self.player.stop()

    def set_media(self, media_path):
        media = self.instance.media_new(media_path)
        self.player.set_media(media)

    def set_position(self, position):
        self.player.set_position(position)

    def set_volume(self, volume):
        self.player.audio_set_volume(volume)

    def toggle_fullscreen(self):
        self.player.toggle_fullscreen()

    def is_fullscreen(self):
        return self.player.get_fullscreen()

class VideoPlayer(QtWidgets.QMainWindow):
    def __init__(self):
        super(VideoPlayer, self).__init__()
        self.setWindowTitle("Відео Програвач")
        self.setGeometry(100, 100, 1000, 600)

        # Застосування темного стилю
        self.setStyleSheet("""
            QMainWindow { background-color: #2e2e2e; }
            QFrame, QWidget { background-color: #1e1e1e; color: #ffffff; }
            QPushButton { border: none; background-color: #3a3a3a; padding: 5px; }
            QPushButton:hover { background-color: #565656; }
            QSlider::groove:horizontal { height: 6px; background-color: #444444; }
            QSlider::handle:horizontal { width: 12px; background-color: #d9d9d9; }
        """)

        # Створення відео віджета
        self.video_frame = QtWidgets.QFrame(self)
        self.video_frame.setStyleSheet("background-color: black;")
        self.video_frame.setFixedSize(800, 450)

        # Панель управління з вбудованими іконками
        self.toolbar = QToolBar("Панель управління")
        self.addToolBar(QtCore.Qt.BottomToolBarArea, self.toolbar)

        # Кнопки з вбудованими іконками для керування відтворенням
        self.play_button = QtWidgets.QPushButton(self.style().standardIcon(QtWidgets.QStyle.SP_MediaPlay), "")
        self.pause_button = QtWidgets.QPushButton(self.style().standardIcon(QtWidgets.QStyle.SP_MediaPause), "")
        self.stop_button = QtWidgets.QPushButton(self.style().standardIcon(QtWidgets.QStyle.SP_MediaStop), "")
        self.next_button = QtWidgets.QPushButton(self.style().standardIcon(QtWidgets.QStyle.SP_MediaSkipForward), "")
        self.prev_button = QtWidgets.QPushButton(self.style().standardIcon(QtWidgets.QStyle.SP_MediaSkipBackward), "")
        self.fullscreen_button = QtWidgets.QPushButton(self.style().standardIcon(QtWidgets.QStyle.SP_TitleBarMaxButton), "")
        self.favorites_button = QtWidgets.QPushButton(self.style().standardIcon(QtWidgets.QStyle.SP_ComputerIcon), "")  # Заміна на іконку сердечка

        # Додавання елементів до панелі управління
        self.toolbar.addWidget(self.prev_button)
        self.toolbar.addWidget(self.play_button)
        self.toolbar.addWidget(self.pause_button)
        self.toolbar.addWidget(self.stop_button)
        self.toolbar.addWidget(self.next_button)
        self.toolbar.addWidget(self.fullscreen_button)
        self.toolbar.addWidget(self.favorites_button)  # Кнопка для улюблених

        # Повзунок для гучності
        # Повзунок для гучності
        self.volume_slider = QSlider(QtCore.Qt.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(50)
        self.volume_slider.setFixedWidth(100)  # Зменшити довжину повзунка
        self.toolbar.addWidget(self.volume_slider)

        # Повзунок для позиції відтворення
        self.time_slider = QSlider(QtCore.Qt.Horizontal)
        self.time_slider.setRange(0, 100)
        self.toolbar.addWidget(self.time_slider)

        # Індикатор часу і статус-бар
        self.time_label = QLabel("00:00")
        self.status_bar = QStatusBar()
        self.status_bar.addPermanentWidget(self.time_label)
        self.setStatusBar(self.status_bar)

        # Список відео та улюблені
        self.tab_widget = QtWidgets.QTabWidget(self)
        self.video_model = QtGui.QStandardItemModel(self)
        self.my_videos_list = QtWidgets.QListView()
        self.my_videos_list.setModel(self.video_model)
        self.tab_widget.addTab(self.my_videos_list, "Мої Відео")
        self.favorites_list = QtWidgets.QListWidget()
        self.tab_widget.addTab(self.favorites_list, "Улюблені")

        # Розміщення відео віджета і панелі вкладок
        h_main = QtWidgets.QHBoxLayout()
        h_main.addWidget(self.tab_widget)
        vbox = QtWidgets.QVBoxLayout()
        vbox.addWidget(self.video_frame)  # Додано відео віджет
        h_main.addLayout(vbox)
        container = QtWidgets.QWidget()
        container.setLayout(h_main)
        self.setCentralWidget(container)

        # Ініціалізація контролера медіа
        self.media_controller = MediaController(self.video_frame)
        self.playlist = []
        self.current_index = -1
        self.favorites = set()

        # Підключення сигналів
        self.play_button.clicked.connect(lambda: self.control_video("play"))
        self.pause_button.clicked.connect(lambda: self.control_video("pause"))
        self.stop_button.clicked.connect(lambda: self.control_video("stop"))
        self.next_button.clicked.connect(self.next_video)
        self.prev_button.clicked.connect(self.prev_video)
        self.fullscreen_button.clicked.connect(self.toggle_fullscreen)
        self.volume_slider.valueChanged.connect(self.set_volume)
        self.time_slider.sliderMoved.connect(self.set_position)
        self.favorites_button.clicked.connect(self.add_to_favorites)  # Підключення кнопки улюблених

        # Сигнал для вибору відео
        self.my_videos_list.doubleClicked.connect(self.select_video_from_list)
        self.ask_for_file_access()

        # Таймер для оновлення позиції відео
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.update_time)
        self.timer.start(1000)  # Оновлюємо кожну секунду

    def control_video(self, action):
        if action == "play":
            self.media_controller.play()
        elif action == "pause":
            self.media_controller.pause()
        elif action == "stop":
            self.media_controller.stop()

    def ask_for_file_access(self):
        message = QMessageBox()
        message.setWindowTitle("Доступ до файлів")
        message.setText("Додаток потребує доступу до файлів комп'ютера для автоматичного пошуку відео.")
        message.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
        result = message.exec_()

        if result == QMessageBox.Ok:
            self.scan_for_videos()

    def scan_for_videos(self):
        video_extensions = ('.mp4', '.avi', '.mkv', '.mov')
        search_path = str(Path.home())

        for root, _, files in os.walk(search_path):
            for file in files:
                if file.lower().endswith(video_extensions):
                    full_path = os.path.join(root, file)
                    self.playlist.append(full_path)
                    item = QtGui.QStandardItem(file)
                    self.video_model.appendRow(item)

        if self.current_index == -1 and self.playlist:
            self.current_index = 0
            self.load_video()

    def load_video(self):
        if 0 <= self.current_index < len(self.playlist):
            self.media_controller.set_media(self.playlist[self.current_index])
            self.setWindowTitle(f"Відео Програвач - {os.path.basename(self.playlist[self.current_index])}")
            self.control_video("play")
            self.highlight_current_video()

    def highlight_current_video(self):
        selection_model = self.my_videos_list.selectionModel()
        index = self.video_model.index(self.current_index, 0)
        selection_model.clearSelection()
        selection_model.select(index, QtCore.QItemSelectionModel.Select)

    def next_video(self):
        if self.current_index < len(self.playlist) - 1:
            self.current_index += 1
            self.load_video()

    def prev_video(self):
        if self.current_index > 0:
            self.current_index -= 1
            self.load_video()

    def select_video_from_list(self, index):
        self.current_index = index.row()
        self.load_video()

    def set_position(self, position):
        self.media_controller.set_position(position / 100)

    def set_volume(self, volume):
        self.media_controller.set_volume(volume)

    def toggle_fullscreen(self):
        if self.media_controller.is_fullscreen():
            self.media_controller.toggle_fullscreen()
            self.showNormal()
            self.tab_widget.show()  # Показуємо бокову панель
        else:
            self.media_controller.toggle_fullscreen()
            self.showFullScreen()
            self.tab_widget.hide()  # Сховуємо бокову панель
            
        self.resize_video_widget()  

    def resize_video_widget(self):
        video_height = self.height() - self.toolbar.height()  # Висота без панелі керування
        video_width = self.width()  # Ширина екрану
        self.video_frame.setGeometry(0, 0, video_width, video_height)  # Встановлюємо нові розміри
   
    def resizeEvent(self, event):
        super(VideoPlayer, self).resizeEvent(event)  # Викликаємо батьківський метод
        if self.media_controller.is_fullscreen():
            self.resize_video_widget()  # Оновлення розмірів відео віджета при зміні розміру вікна

    def add_to_favorites(self):
        if self.current_index >= 0:
            video_path = self.playlist[self.current_index]
        if video_path not in self.favorites:
            self.favorites.add(video_path)
            self.favorites_list.addItem(os.path.basename(video_path))
            QMessageBox.information(self, "Успіх", f"Відео '{os.path.basename(video_path)}' додано до улюблених!")
        else:
            self.favorites.remove(video_path)  # Видалити відео з улюблених
            for i in range(self.favorites_list.count()):
                if self.favorites_list.item(i).text() == os.path.basename(video_path):
                    self.favorites_list.takeItem(i)  # Видалити елемент з списку
                    break
            QMessageBox.information(self, "Успіх", f"Відео '{os.path.basename(video_path)}' видалено з улюблених!")

    def update_time(self):
        if self.media_controller.player.get_state() == vlc.State.Playing:
            current_time = self.media_controller.player.get_time() // 1000  # В мілісекундах
            total_time = self.media_controller.player.get_length() // 1000  # В мілісекундах
            self.time_slider.setValue(int(current_time / total_time * 100))  # Оновлення повзунка
            self.time_label.setText(f"{current_time // 60:02}:{current_time % 60:02} / {total_time // 60:02}:{total_time % 60:02}")  # Оновлення індикатора часу

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    player = VideoPlayer()
    player.show()
    sys.exit(app.exec_())
