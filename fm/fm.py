# むつめ祭2024にて機体を遠隔操作するためのプログラムです

# スピーカー設定をPWM出力可能にしておく(/boot/firmware/config.txtの末尾に"dtoverlay=audremap,pins_18_19"を追加)

print('セットアップを開始します')

import json
import os
import subprocess
import sys
import threading
import time

##### インストールとか #####
# print('実行環境を確認しています')
os.chdir(os.path.dirname(__file__))
# if sys.prefix == sys.base_prefix:
#     print('<<エラー>>\n仮想環境で実行してください (source fm_env/bin/activate を実行)\nもし仮想環境で実行しているなら，sudoを外して実行しなおしてください')
#     if not os.path.exists('fm_env'):
#         print('仮想環境のセットアップを開始します')
#         subprocess.run('sudo python -m venv fm_env --system-site-packages', shell=True)
#         print('仮想環境のセットアップが完了しました')
#     exit(1)
# print('実行環境の確認が完了しました\n必要なライブラリをインストールしています')
# subprocess.run('pip install picamera2 libcamera', shell=True)
# subprocess.run('pip install pyPS4Controller ds4drv', shell=True)
# print('ライブラリのインストールが完了しました')
print('コントローラと無線接続を行います\n\nPS4コントローラーのPSボタンとSHAREボタンを同時に，青いランプが光るまで長押ししてください\n')
subprocess.Popen('sudo ds4drv', shell=True, stdout=subprocess.DEVNULL)
time.sleep(20)
#######################


print('ライブラリをインポートしています')
from gpiozero import LED
from gpiozero import Motor
from gpiozero.pins.pigpio import PiGPIOFactory
import libcamera
from picamera2 import Picamera2
from pyPS4Controller.controller import Controller
print('ライブラリのインポートが完了しました')

print('別のPythonファイルを読み込んでいます')
import start_gui
print('別のPythonファイルの読み込みが完了しました')


##### モーター #####
print('モーターのセットアップを開始します')

PIN_R1 = 4
PIN_R2 = 23
PIN_L1 = 26
PIN_L2 = 5
motor_right = Motor(forward = PIN_R1, backward = PIN_R2, pin_factory = PiGPIOFactory())
motor_left  = Motor(forward = PIN_L1, backward = PIN_L2, pin_factory = PiGPIOFactory())

def motor_calib():
    power = 0
    delta_power = 0.2

    print("右モーターのテストを行います")
    for i in range(int(1 / delta_power)):
        if 0<=power<=1:
            motor_right.value = power
            power += delta_power
    motor_right.value = 1
    time.sleep(0.5)

    for i in range((int(1 / delta_power))*2):
        if -1<=power<=1:
            motor_right.value = power
            power -= delta_power
    motor_right.value = -1
    time.sleep(0.5)

    for i in range(int(1 / delta_power)):
        if -1<=power<=0:
            motor_right.value = power
            power += delta_power
    motor_right.value = 0
    time.sleep(0.5)

    print("左モーターのテストを行います")
    for i in range(int(1 / delta_power)):
        if 0<=power<=1:
            motor_left.value = power
            power += delta_power
    motor_left.value = 1
    time.sleep(0.5)

    for i in range((int(1 / delta_power))*2):
        if -1<=power<=1:
            motor_left.value = power
            power -= delta_power
    motor_left.value = -1
    time.sleep(0.5)

    for i in range(int(1 / delta_power)):
        if -1<=power<=0:
            motor_left.value = power
            power += delta_power
    motor_left.value = 0
    time.sleep(0.5)

print('モーターのセットアップが完了しました')


##### ライト #####
print('ライトのセットアップを開始します')

high_power_led = LED(17)
high_power_led.off()

print('ライトのセットアップが完了しました')


##### スピーカー #####

print('スピーカーのセットアップを開始しました')
class C():
    def poll(self):
        return 0  # まだ開始していない

proces_aplay = C()
# .poll()は終了していなかったらNone，終了していたらそのステータスを返す．
def audio_play(audio_path):
    global proces_aplay
    print('音楽を再生します')
    if (proces_aplay.poll() != None):
        proces_aplay = subprocess.Popen(f"aplay --device=hw:1,0 {audio_path}", shell=True)
        # proces_aplay.returncode
        print("音楽の再生中です")
    else:
        print("音楽がすでに再生中のためキャンセルします")

print('スピーカーのセットアップが完了しました')


###### コントローラ #####
print('コントローラーによる制御システムのセットアップを開始しました')

last_controll_time = time.time()

def transf(raw):
    temp = raw / (1 << 15)
    # Filter values that are too weak for the motors to move
    if abs(temp) < 0.05:
        return 0
    # Return a value between 0.2 and 1.0
    else:
        return round(temp, 2)

# 右スティック前：R2_press　負
# 右スティック後：R2_press　正
# 左スティック前：L3_up　負
# 左スティック後：L3_down　正
# ×ボタン→〇ボタン，〇ボタン→△ボタン，△ボタン→□ボタン，□ボタン→×ボタン
class MyController(Controller):
    def __init__(self, **kwargs):
        Controller.__init__(self, **kwargs)
    
    def on_R2_press(self, value):
        global last_controll_time
        last_controll_time = time.time()
        # 右モーター前進/後退
        power = -transf(value)
        motor_right.value = power
        print(f'右スティックの操作中. 右モーター出力:{motor_right.value} raw:{value}')

    def on_R2_release(self):
        global last_controll_time
        last_controll_time = time.time()
        # 右モーター停止
        motor_right.value = 0
        print(f'右スティック操作終了. 右モーター出力:{motor_right.value}')

    def on_L3_up(self, value):
        global last_controll_time
        last_controll_time = time.time()
        # 左モーター前進
        power = -transf(value)
        motor_left.value = power
        print(f'左スティックの操作中. 左モーター出力:{motor_left.value} raw:{value}')

    def on_L3_down(self, value):
        global last_controll_time
        last_controll_time = time.time()
        # 左モーター後退
        power = -transf(value)
        motor_left.value = power
        print(f'左スティックの操作中. 左モーター出力:{motor_left.value} raw:{value}')

    def on_L3_y_at_rest(self):
        global last_controll_time
        last_controll_time = time.time()
        # 左モーター停止
        motor_left.value = 0
        print(f'左スティック操作終了. 左モーター出力:{motor_left.value}')


    def on_x_press(self):
        print('□ボタンが押されました')
        global last_controll_time
        last_controll_time = time.time()
        # 音楽を再生
        audio_play("/home/jaxai/Desktop/GLaDOS_escape_02_entry-00.wav")
    
    def on_square_press(self):
        print('△ボタンが押されました')
        global last_controll_time
        last_controll_time = time.time()
        audio_play("/home/jaxai/Desktop/kane_tarinai.wav")
    
    def on_circle_press():
        print('×ボタンが押されました')
        global last_controll_time
        last_controll_time = time.time()
        audio_play("/home/jaxai/Desktop/hatodokei.wav")

    def on_triangle_press():
        print('○ボタンが押されました')
        global last_controll_time
        last_controll_time = time.time()
        audio_play("/home/jaxai/Desktop/otoko_ou!.wav")


def connect():
    print('ctrl,connect')

def disconnect():
    print('ctrl,disconnect')

def start_controller():
    while True:
        try:
            controller = MyController(interface="/dev/input/js0", connecting_using_ds4drv=False)
            controller.listen(on_connect=connect, on_disconnect=disconnect)
        except Exception as e:
            print(f'<<エラー>>\nコントローラーによる制御でエラーが発生しました: {e}')

print('コントローラーによる制御システムのセットアップが完了しました')


##### GUI #####
print('GUIによる制御システムのセットアップを開始しました')

def read_from_gui():
    global last_controll_time
    if time.time() - last_controll_time < 1:
        return
    
    data_from_browser = {}
    with open('data_from_browser.json', 'r') as f:
        data_from_browser = json.load(f)
    
    motor_right.value = float(data_from_browser['motor_r'])
    motor_left.value = float(data_from_browser['motor_l'])
    if bool(data_from_browser['light']):
        # high_power_led.on()
        pass
    else:
        # high_power_led.off()
        pass
    if bool(data_from_browser['buzzer']):
        audio_play()

def write_to_gui():
    data_to_browser = {}
    with open('data_to_browser.json', 'r') as f:
        data_to_browser = json.load(f)

    with open('data_to_browser.json', 'w') as f:
        data_to_browser['motor_r'] = motor_right.value
        data_to_browser['motor_l'] = motor_left.value
        data_to_browser['light'] = bool(high_power_led.value)
        data_to_browser['buzzer'] = False if (proces_aplay.poll() == None) else True
        f.write(json.dumps(data_to_browser))

def update_gui():
    while True:
    #     try:
        read_from_gui()
        write_to_gui()
        time.sleep(0.1)
        # except Exception as e:
        #     print(f'<<エラー>>\nGUIによる制御中にエラーが発生しました: {e}')

print('GUIによる制御システムのセットアップが完了しました')


##### カメラ #####
print('カメラのセットアップを開始しました')

picam2 = Picamera2()
picam_config = picam2.create_preview_configuration()
picam_config["transform"] = libcamera.Transform(hflip=1, vflip=1)
picam2.configure(picam_config)
picam2.start()

def start_camera():
    while True:
        try:
            picam2.capture_file('camera_temp.jpg')
            os.rename("camera_temp.jpg", "camera.jpg")
        except Exception as e:
            print(f'<<エラー>>\nカメラによる画像撮影中にエラーが発生しました: {e}')

print('カメラのセットアップが完了しました')


##### モーターの動作確認 #####
print('モーターの動作確認を開始します')
motor_calib()
print('モーターの動作確認が完了しました')


##### 平行処理を開始 #####
print('並行処理による同時実行システムの定義を行います')

# コントローラーを起動
controller_thread = threading.Thread(target=start_controller)

# GUI用のサーバーを起動
server_thread = threading.Thread(target=start_gui.start_server)

# GUIのデータを読み込み・書き込み
gui_thread = threading.Thread(target=update_gui)

# カメラで撮影開始
camera_thread = threading.Thread(target=start_camera)

print('コントローラーを起動します')
controller_thread.start()

print('GUI用のサーバーを起動します')
server_thread.start()

print('GUIによる制御システムを起動します')
gui_thread.start()

print('カメラによる連続撮影を開始します')
camera_thread.start()

print('セットアップが完了しました')

first_thread_count = threading.active_count()
while threading.active_count() != 1:
    if first_thread_count == threading.active_count():
        print('正常に実行されています')
    else:
        print('<<エラー>>\nプログラムの一部が停止しています')
        exit(1)
    time.sleep(10)

### 参考にしたサイト
# thread関連
# https://qiita.com/kaitolucifer/items/e4ace07bd8e112388c75
# コントローラーの接続
# https://hellobreak.net/raspberry-pi-ps4-controller-0326/