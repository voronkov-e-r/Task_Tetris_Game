import sys
import random
from PyQt5.QtWidgets import QMainWindow, QFrame, QDesktopWidget, QApplication, QLabel, QPushButton, QSpinBox, \
    QHBoxLayout, QVBoxLayout, QWidget, QTextEdit, QGroupBox
from PyQt5.QtCore import Qt, QBasicTimer, pyqtSignal, QTimer
from PyQt5.QtGui import QPainter, QColor, QPen, QBrush


class Shape(object):
    sizes = (
        ((-1, 0), (0, 0), (0, 1), (1, 0)),  # T
        ((-1, 0), (0, 0), (1, 0), (1, 1)),  # L
        ((-1, 0), (0, 0), (-1, 1), (1, 0)),  # \L
        ((-1, 0), (0, 0), (-1, 1), (0, 1)),  # []
        ((-1, 0), (0, 0), (1, 0), (2, 0)),  # |
        ((-1, 0), (0, 0), (0, 1), (1, 1)),  # Z
        ((-1, 1), (0, 0), (0, 1), (1, 0))  # \Z
    )
    colors = (Qt.red, Qt.green, Qt.blue, Qt.magenta, Qt.yellow)

    def __init__(self, type):
        self.type = type
        self.size = self.getSize(type)
        self.color = random.choice(Shape.colors)
        self.rotation = 0

    def getSize(self, type):
        return Shape.sizes[type]

    def getColor(self):
        return Shape.colors.index(self.color)

    def rotate(self):
        if self.type != 3:
            self.rotation = (self.rotation + 90) % 360
            rotated = []
            for (x, y) in self.size:
                new_x = -y
                new_y = x
                rotated.append((new_x, new_y))
            self.size = tuple(rotated)

    def reset_rotation(self):
        while self.rotation != 0:
            self.rotate()


class Game:
    def __init__(self, width, height, level, start_speed):
        self.width = width
        self.height = height
        self.fild = [[0 for _ in range(width)] for _ in range(height)]
        self.temp_shape = None
        self.temp_x = (self.width - 1) // 2
        self.temp_y = 1
        self.score = 0
        self.start_speed = start_speed
        self.speed = 800
        self.drought = 0
        self.level = level
        self.final_flag = False

    def create_new_shape(self):
        if self.drought >= 10:
            self.temp_shape = Shape(4)
        else:
            self.temp_shape = Shape(random.randint(0, 6))

        if self.temp_shape.type == 4:
            self.drought = 0
        else:
            self.drought += 1

        self.temp_shape.reset_rotation()
        self.temp_x = (self.width - 1) // 2
        self.temp_y = 1

        if not self.can_place_new_shape():
            return False

        self.place_current_shape()
        return True

    def can_place_new_shape(self):
        for cords in self.temp_shape.size:
            x = cords[0] + self.temp_x
            y = -cords[1] + self.temp_y
            if y >= len(self.fild) or x < 0 or x >= len(self.fild[0]) or self.fild[y][x] != 0:
                return False
        return True

    def clear_current_shape(self):
        for cords in self.temp_shape.size:
            x = cords[0] + self.temp_x
            y = -cords[1] + self.temp_y
            if 0 <= y < len(self.fild) and 0 <= x < len(self.fild[0]):
                self.fild[y][x] = 0

    def place_current_shape(self):
        for cords in self.temp_shape.size:
            x = cords[0] + self.temp_x
            y = -cords[1] + self.temp_y
            if 0 <= y < len(self.fild) and 0 <= x < len(self.fild[0]):
                self.fild[y][x] = self.temp_shape.getColor() + 1

    def can_move(self, new_x, new_y):
        max_x = max(i[0] for i in self.temp_shape.size)
        min_x = min(i[0] for i in self.temp_shape.size)

        if new_x + max_x >= len(self.fild[0]) or new_x + min_x < 0:
            return False

        self.clear_current_shape()

        for cords in self.temp_shape.size:
            x = cords[0] + new_x
            y = -cords[1] + new_y
            if y >= len(self.fild) or self.fild[y][x] != 0:
                self.place_current_shape()
                return False

        return True

    def canRotate(self):
        self.clear_current_shape()

        test_shape = Shape(self.temp_shape.type)
        test_shape.size = self.temp_shape.size
        test_shape.rotate()

        for (x, y) in test_shape.size:
            new_x = self.temp_x + x
            new_y = self.temp_y - y
            if new_y >= len(self.fild) or new_x < 0 or new_x >= len(self.fild[0]) or self.fild[new_y][new_x] != 0:
                self.place_current_shape()
                return False
        return True

    def line_detect(self):
        lines = []
        for i in range(len(self.fild)):
            if all(cell != 0 for cell in self.fild[i]):
                lines.append(i)

        if not lines:
            return

        for i in lines:
            self.fild[i] = [0] * len(self.fild[0])
            for j in range(i, 0, -1):
                self.fild[j], self.fild[j - 1] = self.fild[j - 1], self.fild[j]

        self.set_score(len(lines))

    def set_score(self, lines):
        if lines == 4:
            self.score += 6000
        else:
            self.score += lines * 1000
        self.set_difficulty()

    def set_difficulty(self):
        change = (self.score // 5000) * 100
        self.speed = self.start_speed - change
        self.level = (1000 - self.start_speed + change) // 100

    def game_over(self):
        self.final_flag = True


class StartScreen(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Tetris - Настройки')
        self.setFixedSize(400, 400)

        main_layout = QVBoxLayout()

        desc_group = QGroupBox("О игре Tetris")
        desc_layout = QVBoxLayout()

        description = QTextEdit()
        description.setReadOnly(True)
        description.setText("""
                Классическая игра Тетрис:

                Цель: Располагать падающие фигуры так, 
                чтобы они заполняли горизонтальные линии.

                Управление:
                ← → - двигать фигуру влево/вправо
                ↑ - повернуть фигуру
                ↓ - ускорить падение

                Чем больше линий удаляется за раз, 
                тем больше очков вы получаете!
                """)
        description.setMaximumHeight(150)

        desc_layout.addWidget(description)
        desc_group.setLayout(desc_layout)

        settings_group = QGroupBox("Настройки игры")
        settings_layout = QVBoxLayout()

        width_layout = QHBoxLayout()
        width_label = QLabel("Ширина поля (9-15):")
        self.width_spin = QSpinBox()
        self.width_spin.setRange(9, 15)
        self.width_spin.setValue(9)
        width_layout.addWidget(width_label)
        width_layout.addWidget(self.width_spin)

        height_layout = QHBoxLayout()
        height_label = QLabel("Высота поля (15-25):")
        self.height_spin = QSpinBox()
        self.height_spin.setRange(15, 25)
        self.height_spin.setValue(15)
        height_layout.addWidget(height_label)
        height_layout.addWidget(self.height_spin)

        level_layout = QHBoxLayout()
        level_label = QLabel("Начальный уровень (1-10):")
        self.level_spin = QSpinBox()
        self.level_spin.setRange(1, 10)
        self.level_spin.setValue(1)
        level_layout.addWidget(level_label)
        level_layout.addWidget(self.level_spin)

        settings_layout.addLayout(width_layout)
        settings_layout.addLayout(height_layout)
        settings_layout.addLayout(level_layout)
        settings_group.setLayout(settings_layout)

        start_button = QPushButton("Начать игру")
        start_button.setStyleSheet("""
                    QPushButton {
                        font-size: 16px;
                        font-weight: bold;
                        padding: 10px;
                        background-color: #4CAF50;
                        color: white;
                        border-radius: 5px;
                    }
                    QPushButton:hover {
                        background-color: #45a049;
                    }
                """)
        start_button.clicked.connect(self.start_game)

        main_layout.addWidget(desc_group)
        main_layout.addWidget(settings_group)
        main_layout.addWidget(start_button)

        self.setLayout(main_layout)

    def start_game(self):
        width = self.width_spin.value()
        height = self.height_spin.value()
        level = self.level_spin.value()

        self.game_window = Tetris(width, height, level)
        self.game_window.show()
        self.close()

class Tetris(QMainWindow):
    def __init__(self, width, height, level):
        super().__init__()

        start_speed = 1000 - level * 100
        self.game = Game(width, height, level, start_speed)

        self.label = QLabel("Score:\n0", self)
        self.label.setGeometry(50 * self.game.width, 50 * self.game.height - 70, 100, 50)
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setStyleSheet("""
            QLabel {
                border: 2px solid #000000;
                border-radius: 5px;
                padding: 10px;
                background-color: #f0f0f0;
                font-size: 13px;
            }
        """)

        self.level_label = QLabel(f"Level: \n{self.game.level}", self)
        self.level_label.setGeometry(50 * self.game.width, 50 * self.game.height - 120, 100, 50)
        self.level_label.setAlignment(Qt.AlignCenter)
        self.level_label.setStyleSheet("""
                    QLabel {
                        border: 2px solid #000000;
                        border-radius: 5px;
                        padding: 10px;
                        background-color: #f0f0f0;
                        font-size: 13px;
                    }
                """)

        self.final_label = QLabel("YOU LOOSE!", self)
        self.final_label.setGeometry(25 * self.game.width - 150, 25 * self.game.height - 75, 300, 150)
        self.final_label.setAlignment(Qt.AlignCenter)
        self.final_label.setStyleSheet("""
                    QLabel {
                        border: 2px solid #000000;
                        border-radius: 5px;
                        padding: 10px;
                        background-color: #c0c0c0;
                        color: #f00;
                        font-weight: 500;
                        font-size: 30px;
                    }
                """)
        self.final_label.setVisible(False)

        self.setFixedSize(50 * self.game.width + 100, 50 * self.game.height)
        self.show()

        self.timer = QTimer()
        self.timer.timeout.connect(self.tick)
        self.timer.start(self.game.start_speed)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setPen(QPen(Qt.black, 3))
        painter.drawLine(50 * self.game.width, 0, 50 * self.game.width, 50 * self.game.height)

        for i in range(len(self.game.fild)):
            for j in range(len(self.game.fild[i])):
                if self.game.fild[i][j] == 0:
                    continue
                painter.setBrush(QBrush(Shape.colors[self.game.fild[i][j] - 1], Qt.SolidPattern))
                painter.drawRect(j * 50, i * 50, 50, 50)

    def keyPressEvent(self, event):
        key = event.key()

        if not self.game.final_flag and self.game.temp_shape is not None:
            if key == Qt.Key_Right:
                if self.game.can_move(self.game.temp_x + 1, self.game.temp_y):
                    self.game.clear_current_shape()
                    self.game.temp_x += 1
                    self.game.place_current_shape()

            elif key == Qt.Key_Left:
                if self.game.can_move(self.game.temp_x - 1, self.game.temp_y):
                    self.game.clear_current_shape()
                    self.game.temp_x -= 1
                    self.game.place_current_shape()

            elif key == Qt.Key_Up:
                if self.game.canRotate():
                    self.game.clear_current_shape()
                    self.game.temp_shape.rotate()
                    self.game.place_current_shape()

            elif key == Qt.Key_Down:
                while self.game.can_move(self.game.temp_x, self.game.temp_y + 1):
                    self.game.clear_current_shape()
                    self.game.temp_y += 1
                    self.game.place_current_shape()

            self.repaint()

    def tick(self):
        if self.game.temp_shape is None:
            if not self.game.create_new_shape():
                self.game.game_over()
                self.game_over()
        else:
            if self.game.can_move(self.game.temp_x, self.game.temp_y + 1):
                self.game.clear_current_shape()
                self.game.temp_y += 1
                self.game.place_current_shape()
            else:
                self.game.place_current_shape()
                self.game.line_detect()
                self.set_ticks()
                self.game.temp_shape = None
                self.label.setText(f"Score:\n{self.game.score}")
                self.level_label.setText(f"Level: \n{self.game.level}")

        self.repaint()

    def game_over(self):
        self.timer.stop()
        self.final_label.setText(f"YOU LOOSE!\nFinal Score: \n{self.game.score}")
        self.final_label.setVisible(True)
        self.level_label.setVisible(False)
        self.label.setVisible(False)

    def set_ticks(self):
        self.game.set_difficulty()
        ticks = self.game.speed
        self.timer.stop()
        self.timer.start(ticks)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    game = StartScreen()
    game.show()
    sys.exit(app.exec_())