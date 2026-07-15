import copy
import sys
import random
from PyQt5.QtWidgets import QMainWindow, QFrame, QDesktopWidget, QApplication, QLabel
from PyQt5.QtCore import Qt, QBasicTimer, pyqtSignal, QTimer, QObject, QThread
from PyQt5.QtGui import QPainter, QColor, QPen, QBrush


class BotWorker(QObject):
    move_calculated = pyqtSignal(tuple)

    def __init__(self, game):
        super().__init__()
        self.game = game
        self.agent = Bot(game)

    def calculate_move(self):
        best_move = self.agent.get_best_move()
        self.move_calculated.emit(best_move)


class Bot:
    def __init__(self, game):
        self.game = game
        self.a = -0.510066
        self.b = 0.760666
        self.c = -0.35663
        self.d = -0.184483

    def evaluate_positions(self, positions):
        list_aggr = []
        for pos in positions:
            aggr = self.aggregate_height(pos)
            comp = self.complete_lines(pos)
            hole = self.holes(pos)
            bump = self.bumpiness(pos)
            best_pos = (self.a * aggr) + (self.b * comp) + (self.c * hole) + (self.d * bump)
            list_aggr.append(best_pos)

        if not list_aggr:
            return None

        max_value = max(list_aggr)
        max_index = list_aggr.index(max_value)
        return positions[max_index]

    def aggregate_height(self, pos):
        temp_game = copy.deepcopy(self.game)
        temp_game.clear_current_shape()
        temp_game.temp_x, temp_game.temp_y = pos[1], pos[2]
        if pos[0] == 90:
            temp_game.temp_shape.rotate()
        elif pos[0] == 180:
            temp_game.temp_shape.rotate()
            temp_game.temp_shape.rotate()
        elif pos[0] == 270:
            temp_game.temp_shape.rotate()
            temp_game.temp_shape.rotate()
            temp_game.temp_shape.rotate()

        temp_game.place_current_shape()

        total_height = 0
        for x in range(temp_game.width):
            for y in range(temp_game.height):
                if temp_game.fild[y][x] != 0:
                    total_height += (temp_game.height - y)
                    break
        return total_height

    def complete_lines(self, pos):
        temp_game = copy.deepcopy(self.game)
        temp_game.clear_current_shape()
        temp_game.temp_x, temp_game.temp_y = pos[1], pos[2]
        if pos[0] == 90:
            temp_game.temp_shape.rotate()
        elif pos[0] == 180:
            temp_game.temp_shape.rotate()
            temp_game.temp_shape.rotate()
        elif pos[0] == 270:
            temp_game.temp_shape.rotate()
            temp_game.temp_shape.rotate()
            temp_game.temp_shape.rotate()

        temp_game.place_current_shape()

        complete_lines = 0
        for y in range(temp_game.height):
            if all(cell != 0 for cell in temp_game.fild[y]):
                complete_lines += 1
        return complete_lines

    def holes(self, pos):
        temp_game = copy.deepcopy(self.game)
        temp_game.clear_current_shape()
        temp_game.temp_x, temp_game.temp_y = pos[1], pos[2]
        if pos[0] == 90:
            temp_game.temp_shape.rotate()
        elif pos[0] == 180:
            temp_game.temp_shape.rotate()
            temp_game.temp_shape.rotate()
        elif pos[0] == 270:
            temp_game.temp_shape.rotate()
            temp_game.temp_shape.rotate()
            temp_game.temp_shape.rotate()

        temp_game.place_current_shape()

        holes = 0
        for x in range(temp_game.width):
            block_found = False
            for y in range(temp_game.height):
                if temp_game.fild[y][x] != 0:
                    block_found = True
                elif block_found:
                    holes += 1
        return holes

    def bumpiness(self, pos):
        temp_game = copy.deepcopy(self.game)
        temp_game.clear_current_shape()
        temp_game.temp_x, temp_game.temp_y = pos[1], pos[2]
        if pos[0] == 90:
            temp_game.temp_shape.rotate()
        elif pos[0] == 180:
            temp_game.temp_shape.rotate()
            temp_game.temp_shape.rotate()
        elif pos[0] == 270:
            temp_game.temp_shape.rotate()
            temp_game.temp_shape.rotate()
            temp_game.temp_shape.rotate()

        temp_game.place_current_shape()

        heights = []
        for x in range(temp_game.width):
            for y in range(temp_game.height):
                if temp_game.fild[y][x] != 0:
                    heights.append(temp_game.height - y)
                    break
            else:
                heights.append(0)

        bumpiness = 0
        for i in range(len(heights) - 1):
            bumpiness += abs(heights[i] - heights[i + 1])
        return bumpiness

    def get_possible_positions(self):
        positions = []
        original_shape = copy.deepcopy(self.game.temp_shape)
        original_x, original_y = self.game.temp_x, self.game.temp_y

        # Test all rotations
        for rotation in [0, 90, 180, 270]:
            self.game.temp_shape = copy.deepcopy(original_shape)
            for _ in range(rotation // 90):
                if self.game.canRotate():
                    self.game.temp_shape.rotate()

            # Find leftmost and rightmost positions
            left_x = original_x
            while self.game.can_move(left_x - 1, original_y):
                left_x -= 1

            right_x = original_x
            while self.game.can_move(right_x + 1, original_y):
                right_x += 1

            # Test all x positions
            for x in range(left_x, right_x + 1):
                temp_y = original_y
                while self.game.can_move(x, temp_y + 1):
                    temp_y += 1

                if self.game.can_move(x, temp_y):  # Check if position is valid
                    positions.append((rotation, x, temp_y))

        self.game.temp_shape = original_shape
        self.game.temp_x, self.game.temp_y = original_x, original_y
        return positions

    def get_best_move(self):
        positions = self.get_possible_positions()
        if not positions:
            return None
        best_pos = self.evaluate_positions(positions)
        return best_pos


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
    def __init__(self, width=9, height=15):
        self.width = width
        self.height = height
        self.fild = [[0 for _ in range(width)] for _ in range(height)]
        self.temp_shape = None
        self.temp_x = 4
        self.temp_y = 1
        self.score = 0
        self.speed = 800
        self.drought = 0
        self.level = 1
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
        self.temp_x = 4
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
        change = ((self.score // 5000) + 1) * 100
        self.speed = 1000 - change
        self.level = change // 100

    def game_over(self):
        self.final_flag = True


class Tetris(QMainWindow):
    def __init__(self):
        super().__init__()

        self.game = Game()
        self.game2 = Game()
        self.agent = Bot(self.game2)
        self.squeue = []

        # Таймер для основного игрового цикла
        self.timer1 = QTimer()
        self.timer1.timeout.connect(self.tick1)

        # Таймер для бота
        self.timer2 = QTimer()
        self.timer2.timeout.connect(self.tick2)

        # Таймер для плавного движения бота
        self.motion_timer = QTimer()
        self.motion_timer.timeout.connect(self.process_bot_moves)
        self.motion_timer.setInterval(250)  # Быстрый интервал для плавности

        self.bot_thread = QThread()
        self.bot_worker = BotWorker(self.game2)
        self.bot_worker.moveToThread(self.bot_thread)
        self.bot_worker.move_calculated.connect(self.handle_bot_move)
        self.bot_thread.start()

        self.init_ui()
        self.start_game()

    def init_ui(self):
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

        self.level_label = QLabel("Level: \n1", self)
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

        self.label2 = QLabel("Score:\n0", self)
        self.label2.setGeometry((50 * self.game.width) * 2 + 100, 50 * self.game.height - 70, 100, 50)
        self.label2.setAlignment(Qt.AlignCenter)
        self.label2.setStyleSheet("""
                    QLabel {
                        border: 2px solid #000000;
                        border-radius: 5px;
                        padding: 10px;
                        background-color: #f0f0f0;
                        font-size: 13px;
                    }
                """)

        self.level_label2 = QLabel("Level: \n1", self)
        self.level_label2.setGeometry((50 * self.game.width) * 2 + 100, 50 * self.game.height - 120, 100, 50)
        self.level_label2.setAlignment(Qt.AlignCenter)
        self.level_label2.setStyleSheet("""
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

        self.final_label2 = QLabel("YOU LOOSE!", self)
        self.final_label2.setGeometry(25 * self.game.width * 3 - 50, 25 * self.game.height - 75, 300, 150)
        self.final_label2.setAlignment(Qt.AlignCenter)
        self.final_label2.setStyleSheet("""
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
        self.final_label2.setVisible(False)

        self.ultra_final_label = QLabel("", self)
        self.ultra_final_label.setGeometry(50 * self.game.width -100, 25 * self.game.height - 300, 300, 150)
        self.ultra_final_label.setAlignment(Qt.AlignCenter)
        self.ultra_final_label.setStyleSheet("""
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
        self.ultra_final_label.setVisible(False)

        self.setFixedSize(2 * (50 * self.game.width + 100), 50 * self.game.height)
        self.show()

    def start_game(self):
        self.timer1.start(self.game.speed)
        self.timer2.start(self.game2.speed)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setPen(QPen(Qt.black, 3))
        painter.drawLine(50 * self.game.width, 0, 50 * self.game.width, 50 * self.game.height)
        painter.drawLine(50 * self.game.width + 100, 0, 50 * self.game.width + 100, 50 * self.game.height)
        painter.drawLine(50 * self.game.width + 100 + 50 * self.game.width, 0,
                         50 * self.game.width + 100 + 50 * self.game.width, 50 * self.game.height)

        # Рисуем первое поле
        for i in range(len(self.game.fild)):
            for j in range(len(self.game.fild[i])):
                if self.game.fild[i][j] == 0:
                    continue
                painter.setBrush(QBrush(Shape.colors[self.game.fild[i][j] - 1], Qt.SolidPattern))
                painter.drawRect(j * 50, i * 50, 50, 50)

        # Рисуем второе поле
        for i in range(len(self.game2.fild)):
            for j in range(len(self.game2.fild[i])):
                if self.game2.fild[i][j] == 0:
                    continue
                painter.setBrush(QBrush(Shape.colors[self.game2.fild[i][j] - 1], Qt.SolidPattern))
                painter.drawRect(j * 50 + 50 * self.game2.width + 100, i * 50, 50, 50)

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

    def tick1(self):
        #if self.game.final_flag:  # Добавляем проверку на завершение игры
        #    return

        if self.game.temp_shape is None:
            if not self.game.create_new_shape():
                self.game.game_over()
                self.game_over1()
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

    def tick2(self):
        #if self.game2.final_flag:  # Добавляем проверку на завершение игры
        #    return

        if self.game2.temp_shape is None:
            if not self.game2.create_new_shape():
                self.game2.game_over()
                self.game_over2()
            elif not self.motion_timer.isActive():  # Добавляем новую фигуру только если бот не активен
                self.prepare_bot_move()
        else:
            if not self.motion_timer.isActive():  # Двигаем вниз только если бот не активен
                if self.game2.can_move(self.game2.temp_x, self.game2.temp_y + 1):
                    self.game2.clear_current_shape()
                    self.game2.temp_y += 1
                    self.game2.place_current_shape()
                else:
                    self.game2.place_current_shape()
                    self.game2.line_detect()
                    self.set_ticks()
                    self.game2.temp_shape = None
                    self.label2.setText(f"Score:\n{self.game2.score}")
                    self.level_label2.setText(f"Level: \n{self.game2.level}")

        self.repaint()

    def prepare_bot_move(self):
        if self.game2.temp_shape is not None and not self.squeue:
            # Запускаем вычисления в отдельном потоке
            QTimer.singleShot(0, self.bot_worker.calculate_move)

    def handle_bot_move(self, best_move):
        if best_move:
            rotation, xPos, yPos = best_move
            current_rotation = self.game2.temp_shape.rotation
            required_rotation = rotation

            rotations_needed = (required_rotation - current_rotation) % 360 // 90
            self.squeue = []

            for _ in range(rotations_needed):
                self.squeue.append(Qt.Key_Up)

            if xPos > self.game2.temp_x:
                for _ in range(xPos - self.game2.temp_x):
                    self.squeue.append(Qt.Key_Right)
            else:
                for _ in range(self.game2.temp_x - xPos):
                    self.squeue.append(Qt.Key_Left)

            self.motion_timer.start()

    def process_bot_moves(self):
        if not self.squeue:
            self.motion_timer.stop()
            self.execute_bot_action(Qt.Key_Down)
            return

        action = self.squeue.pop(0)
        self.execute_bot_action(action)

    def execute_bot_action(self, key):
        if not self.game2.final_flag and self.game2.temp_shape is not None:
            if key == Qt.Key_Right:
                if self.game2.can_move(self.game2.temp_x + 1, self.game2.temp_y):
                    self.game2.clear_current_shape()
                    self.game2.temp_x += 1
                    self.game2.place_current_shape()

            elif key == Qt.Key_Left:
                if self.game2.can_move(self.game2.temp_x - 1, self.game2.temp_y):
                    self.game2.clear_current_shape()
                    self.game2.temp_x -= 1
                    self.game2.place_current_shape()

            elif key == Qt.Key_Up:
                if self.game2.canRotate():
                    self.game2.clear_current_shape()
                    self.game2.temp_shape.rotate()
                    self.game2.place_current_shape()


            elif key == Qt.Key_Down:
                while self.game2.can_move(self.game2.temp_x, self.game2.temp_y + 1):
                    self.game2.clear_current_shape()
                    self.game2.temp_y += 1
                    self.game2.place_current_shape()

        self.repaint()

    def game_over1(self):
        self.timer1.stop()
        self.final_label.setText(f"YOU OVER!\nFinal Score: \n{self.game.score}")
        self.final_label.setVisible(True)
        self.level_label.setVisible(False)
        self.label.setVisible(False)

        if self.game2.final_flag:
            if self.game2.score > self.game.score:
                self.ultra_final_label.setText("BOT WIN!")
            elif self.game2.score < self.game.score:
                self.ultra_final_label.setText("YOU WIN!")
            else:
                self.ultra_final_label.setText("Tie...")

            self.ultra_final_label.setVisible(True)

    def game_over2(self):
        self.timer2.stop()
        self.motion_timer.stop()
        self.final_label2.setText(f"BOT OVER!\nFinal Score: \n{self.game2.score}")
        self.final_label2.setVisible(True)
        self.level_label2.setVisible(False)
        self.label2.setVisible(False)

        if self.game.final_flag:
            if self.game2.score > self.game.score:
                self.ultra_final_label.setText("BOT WIN!")
            elif self.game2.score < self.game.score:
                self.ultra_final_label.setText("YOU WIN!")
            else:
                self.ultra_final_label.setText("Tie...")

            self.ultra_final_label.setVisible(True)

    def set_ticks(self):
        ticks1 = self.game.speed
        self.timer1.stop()
        self.timer1.start(ticks1)

        ticks2 = self.game2.speed
        self.timer2.stop()
        self.timer2.start(ticks2)


app = QApplication(sys.argv)
game = Tetris()
sys.exit(app.exec_())