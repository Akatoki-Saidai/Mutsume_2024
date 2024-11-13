# むつめ祭2024にて機体を遠隔操作するためのプログラムです

# ×ボタン→〇ボタン，〇ボタン→△ボタン，△ボタン→□ボタン，□ボタン→×ボタン
# スピーカー設定をPWM出力可能にしておく(/boot/firmware/config.txtの末尾に"dtoverlay=audremap,pins_12_13"を追加)

import os
import json
import threading
import time

from gpiozero import LED
from gpiozero import Motor
from gpiozero.pins.pigpio import PiGPIOFactory
from picamera2 import Picamera2
from pyPS4Controller.controller import Controller

import start_gui
import speaker


##### モーター #####
PIN_R1 = 4
PIN_R2 = 23
PIN_L1 = 13
PIN_L2 = 5
motor_right = Motor(forward = PIN_R1, backward = PIN_R2, pin_factory = PiGPIOFactory)
motor_left  = Motor(forward = PIN_L1, backward = PIN_L2, pin_factory = PiGPIOFactory)


##### ライト #####
high_power_led = LED(17)
high_power_led.off()


###### コントローラ #####

class LastControl():
    time = time.time()  # 実質的なグローバル変数

def transf(raw):
    temp = (raw + 32767) / 65534 / 2
    # Filter values that are too weak for the motors to move
    if abs(temp) < 0.9:  # <-- 0.3の間違いでは?
        return 0
    # Return a value between 0.3 and 1.0
    else:
        return round(temp, 1)

class MyController(Controller):
    def __init__(self, **kwargs):
        Controller.__init__(self, **kwargs)
    
    def on_R3_up(self, value):
        print(f'ctrl,R3,up,{value}')
        LastControl.time = time.time()
        motor_right.value = transf(value)
    
    def on_R3_down(self, value):
        print(f'ctrl,R3,down,{value}')
        LastControl.time = time.time()
        motor_right.value = -transf(value)
    
    def on_L3_up(self, value):
        print(f'ctrl,L3,up,{value}')
        LastControl.time = time.time()
        motor_left.value = transf(value)
    
    def on_L3_down(self, value):
        print(f'ctrl,L3,down,{value}')
        LastControl.time = time.time()
        motor_left.value = -transf(value)
    
    def on_x_press(self):
        print('ctrl,x,press')
        LastControl.time = time.time()
        speaker.play()
    
    def on_square_press(self):
        print('ctrl,square,press')
        LastControl.time = time.time()
        high_power_led.on()

    def on_square_release(self):
        print('ctrl,square,release')
        LastControl.time = time.time()
        high_power_led.off()

def connect():
    print('ctrl,connect')

def disconnect():
    print('ctrl,disconnect')

def start_controller():
    controller = MyController(interface="/dev/input/js0", connecting_using_ds4drv=False)
    controller.listen(on_connect=connect, on_disconnect=disconnect)


##### GUI #####

def read_from_gui():
    if time.time() - LastControl.time < 1:
        return
    
    data_from_browser = {}
    with open('data_from_browser', 'r') as f:
        data_from_browser = json.load(f)
    
    motor_right.value = float(data_from_browser['motor_r'])
    motor_left.value = float(data_from_browser['motor_l'])
    if bool(data_from_browser['light']):
        high_power_led.on()
    else:
        high_power_led.off()
    if bool(data_from_browser['buzzer']):
        speaker.play()
    print(f'gui,{data_from_browser['motor_l']},{data_from_browser['motor_r']},{data_from_browser['light']},{data_from_browser['buzzer']}')

def write_to_gui():
    data_to_browser = {}
    data_to_browser['motor_r'] = motor_right.value
    data_to_browser['motor_l'] = motor_left.value
    data_to_browser['light'] = high_power_led.value
    data_to_browser['buzzer'] = speaker.Playing.now
    s = json.dumps(data_to_browser)
    with open('data_to_browser', 'w') as f:
        f.write(s)

def update_gui():
    while True:
        read_from_gui()
        write_to_gui()
        time.sleep(0.1)


##### カメラ #####

picam2 = Picamera2()
picam2.start()

def start_camera():
    while True:
        picam2.capture_file('camera_temp.jpg')
        os.rename("camera_temp.jpg", "camera.jpg")


##### 平行処理を開始 #####

# コントローラーを起動
controller_thread = threading.Thread(target=start_controller)

# GUI用のサーバーを起動
server_thread = threading.Thread(target=start_gui.start_server)

# GUIのデータを読み込み・書き込み
gui_thread = threading.Thread(target=update_gui)

# カメラで撮影開始
camera_thread = threading.Thread(target=start_camera)


while threading.active_count() != 1:
    print(f'main,{threading.active_count()}')
    time.sleep(10)

# 参考にしたサイト
# https://qiita.com/kaitolucifer/items/e4ace07bd8e112388c75