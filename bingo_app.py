import tkinter as tk
from PIL import Image, ImageTk
import random
import time
import os
import pygame

# 初期設定
ASSETS_FOLDER = "assets"
BACKGROUND_IMAGE = f"{ASSETS_FOLDER}/background.png"
CONFIG_FILE = "config.txt"

# 設定値をロード
def load_config():
    config = {}
    with open(CONFIG_FILE, "r") as file:
        for line in file:
            key, value = line.strip().split("=")
            config[key] = int(value)
    return config

config = load_config()

# Configファイルから値をロード
MIN_VALUE = config["MIN_VALUE"]
MAX_VALUE = config["MAX_VALUE"]
digit1_position = {'x': config["DIGIT1_X"], 'y': config["DIGIT1_Y"]}
digit2_position = {'x': config["DIGIT2_X"], 'y': config["DIGIT2_Y"]}
MAIN_WIDTH = config["MAIN_WIDTH"]
MAIN_HEIGHT = config["MAIN_HEIGHT"]
SUB_WIDTH = config["SUB_WIDTH"]
SUB_HEIGHT = config["SUB_HEIGHT"]
ROULETTE_DEFAULT_SPEED = config["ROULETTE_DEFAULT_SPEED"]
ROULETTE_LENGTH = config["ROULETTE_LENGTH"]
ROULETTE_LENGTH_MARGINE = config["ROULETTE_LENGTH_MARGINE"]
ROULETTE_ACCEL = config["ROULETTE_ACCEL"]
ROULETTE_ACCEL_LENGTH = config["ROULETTE_ACCEL_LENGTH"]
ROULETTE_SOUND = f"{ASSETS_FOLDER}/Ring.wav"
STOP_SOUND = f"{ASSETS_FOLDER}/Rang.wav"

selected_numbers = set()

# 効果音を初期化
def init_sound():
    pygame.mixer.init()
    sound_change = pygame.mixer.Sound(ROULETTE_SOUND)  # 抽選中の音
    sound_confirm = pygame.mixer.Sound(STOP_SOUND)  # 確定時の音
    return sound_change, sound_confirm

# 効果音を再生
def play_sound(effect):
    effect.play()

class BingoApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Bingo Roulette")
        self.root.geometry(f"{MAIN_WIDTH}x{MAIN_HEIGHT}")

        # 背景画像
        self.bg_image = ImageTk.PhotoImage(Image.open(BACKGROUND_IMAGE))
        self.bg_label = tk.Label(self.root, image=self.bg_image)
        self.bg_label.place(x=0, y=0, relwidth=1, relheight=1)

        # 数字画像の読み込み
        self.digit_images = {}
        for i in range(10):
            file_path = os.path.join(ASSETS_FOLDER, f"{i}.png")
            self.digit_images[i] = ImageTk.PhotoImage(Image.open(file_path).convert("RGBA"))

        # 数字の表示ラベル
        self.digit1_label = tk.Label(self.root, bg=None, borderwidth=0, highlightthickness=0)
        self.digit1_label.place(x=digit1_position['x'], y=digit1_position['y'])

        self.digit2_label = tk.Label(self.root, bg=None, borderwidth=0, highlightthickness=0)
        self.digit2_label.place(x=digit2_position['x'], y=digit2_position['y'])

        # デフォルトで「0」の画像を表示
        self.display_number(0)

        # メニューバー
        self.menu = tk.Menu(self.root)
        self.root.config(menu=self.menu)

        # ファイルメニュー
        file_menu = tk.Menu(self.menu, tearoff=0)
        file_menu.add_command(label="リセット", command=self.reset_game)  # リセット機能
        self.menu.add_cascade(label="ファイル", menu=file_menu)

        # サブウィンドウを作成
        self.history_window = self.show_history_window()

        # イベントバインド
        self.root.bind("<space>", lambda event: self.draw_number())
        self.root.bind("<Button-1>", lambda event: self.draw_number())

    # 数字を選ぶ
    def draw_number(self):
        global MIN_VALUE, MAX_VALUE, selected_numbers

        available_numbers = [n for n in range(MIN_VALUE, MAX_VALUE + 1) if n not in selected_numbers]
        if not available_numbers:
            tk.messagebox.showinfo("終了", "全ての数字が選ばれました！")
            return

        # ルーレット演出
        sound_change, sound_confirm = init_sound()
        selected = random.choice(available_numbers)
        sleep_time = ROULETTE_DEFAULT_SPEED * 0.01
        length_margine = []
        for i in range(ROULETTE_LENGTH_MARGINE):
            length_margine.insert(0, -i)
            length_margine.append(i)
        length = ROULETTE_LENGTH if ROULETTE_LENGTH > ROULETTE_LENGTH_MARGINE else ROULETTE_LENGTH_MARGINE + 1
        length = length + random.choice(length_margine)
        accel_length = ROULETTE_ACCEL_LENGTH if ROULETTE_ACCEL_LENGTH > 5 else 6  + random.choice([-5, -4, -3, -2, -1, 0, 1, 2, 3, 4, 5 ])
        numbers_array = []
        sleep_time_array = []
        current_number = selected
        for i in range(length):
            numbers_array.insert(0, current_number)
            sleep_time_array.append(sleep_time)
            current_number = get_previous_value(available_numbers, current_number)  # 前の値を取得
            if not length - i > accel_length :
                sleep_time += ROULETTE_ACCEL / 100
        for i in range(len(numbers_array)):
            self.display_number(numbers_array[i])
            play_sound(sound_change)
            self.root.update()
            time.sleep(sleep_time_array[i])
        play_sound(sound_confirm)

        # 最終選択
        self.display_number(selected)
        selected_numbers.add(selected)
        self.update_history_window()

    # 数字を画像で表示
    def display_number(self, number):
        digit1 = number // 10  # 十の位
        digit2 = number % 10   # 一の位

        # 画像を設定
        self.digit1_label.config(image=self.digit_images[digit1])
        self.digit2_label.config(image=self.digit_images[digit2])

        # 現在の位置を適用
        self.digit1_label.place(x=digit1_position['x'], y=digit1_position['y'])
        self.digit2_label.place(x=digit2_position['x'], y=digit2_position['y'])

    # サブウィンドウ: 抽選履歴
    def show_history_window(self):
        history_window = tk.Toplevel(self.root)
        history_window.title("抽選履歴")
        history_window.geometry(f"{SUB_WIDTH}x{SUB_HEIGHT}")

        tk.Label(history_window, text="抽選された数字一覧", font=("Helvetica", 14)).pack(pady=10)

        # フレーム内に全ての数字を表示
        self.history_frame = tk.Frame(history_window)
        self.history_frame.pack(pady=10, padx=10)

        self.create_number_grid(self.history_frame)

        return history_window

    # 数字グリッドを作成
    def create_number_grid(self, parent):
        self.number_labels = []  # 全数字のラベルを保持
        for i in range(MIN_VALUE, MAX_VALUE + 1):
            color = "red" if i in selected_numbers else "black"
            label = tk.Label(parent, text=str(i), fg=color, font=("Helvetica", 12), width=3, relief="flat")
            label.grid(row=(i-1)//10, column=(i-1)%10, padx=5, pady=5)
            self.number_labels.append(label)

    # 抽選履歴を更新
    def update_history_window(self):
        for i, label in enumerate(self.number_labels, start=MIN_VALUE):
            color = "red" if i in selected_numbers else "black"
            label.config(fg=color)

    # ゲームリセット
    def reset_game(self):
        global selected_numbers
        selected_numbers = set()
        self.display_number(0)  # デフォルト状態に戻す
        self.update_history_window()
    
# 特定の値の一つ前の値を取得する関数
def get_previous_value(arr, target):
    try:
        # 対象値のインデックスを取得
        index = arr.index(target)
        # 先頭の場合は最後尾の値を返す
        if index == 0:
            return arr[-1]
        # それ以外の場合は一つ前の値を返す
        return arr[index - 1]
    except ValueError:
        # 対象値が見つからない場合の処理
        return None

# アプリ実行
if __name__ == "__main__":
    root = tk.Tk()
    app = BingoApp(root)
    root.mainloop()
