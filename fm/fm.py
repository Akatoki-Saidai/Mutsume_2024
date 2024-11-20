# むつめ祭2024にて機体を遠隔操作するためのプログラムです

# スピーカー設定をPWM出力可能にしておく(/boot/firmware/config.txtの末尾に"dtoverlay=audremap,pins_18_19"を追加)

import json
import os
import subprocess
# import sys
import threading
import time

##### インストールとか #####
'''
os.chdir(os.path.dirname(__file__))
if sys.prefix == sys.base_prefix:
    subprocess.run('python -m venv fm_env --system-site-packages', shell=True)
    print('仮想環境で実行してください (fm_env/bin/activate で起動)')
    exit(1)
subprocess.run('pip install picamera2', shell=True)
subprocess.run('pip install pyPS4Controller ds4drv', shell=True)
print('\nPS4コントローラーのPSボタンとSHAREボタンを同時に長押ししてください\n')
subprocess.run('ds4drv', shell=True)
'''
#######################

from gpiozero import LED
from gpiozero import Motor
from gpiozero.pins.pigpio import PiGPIOFactory
from picamera2 import Picamera2
from pyPS4Controller.controller import Controller

import start_gui


##### モーター #####
PIN_R1 = 4
PIN_R2 = 23
PIN_L1 = 5
PIN_L2 = 26
motor_right = Motor(forward = PIN_R1, backward = PIN_R2, pin_factory = PiGPIOFactory())
motor_left  = Motor(forward = PIN_L1, backward = PIN_L2, pin_factory = PiGPIOFactory())

def motor_calib():
    power = 0
    delta_power = 0.2

    print("right_motor calibration")
    for i in range(int(1 / delta_power)):
        if 0<=power<=1:
            motor_right.value = power
            power += delta_power
    motor_right.value = 1

    for i in range((int(1 / delta_power))*2):
        if -1<=power<=1:
            motor_right.value = power
            power -= delta_power
    motor_right.value = -1

    for i in range(int(1 / delta_power)):
        if -1<=power<=0:
            motor_right.value = power
            power += delta_power
    motor_right.value = 0

    print("left_motor calibration")
    for i in range(int(1 / delta_power)):
        if 0<=power<=1:
            motor_left.value = power
            power += delta_power
    motor_left.value = 1

    for i in range((int(1 / delta_power))*2):
        if -1<=power<=1:
            motor_left.value = power
            power -= delta_power
    motor_left.value = -1

    for i in range(int(1 / delta_power)):
        if -1<=power<=0:
            motor_left.value = power
            power += delta_power
    motor_left.value = 0


##### ライト #####
high_power_led = LED(17)
high_power_led.off()


##### スピーカー #####
class C():
    def poll(self):
        return None
proces_aplay = C()
def audio_play():
    global proces_aplay
    print('speaker,play')
    if proces_aplay.poll() == None:
        proces_aplay = subprocess.Popen("aplay --device=hw:1,0 /home/jaxai/Desktop/GLaDOS_escape_02_entry-00.wav", shell=True)
        proces_aplay.returncode


###### コントローラ #####

last_controll_time = time.time()

def transf(raw):
    # temp = raw / (1 << 15)
    temp = raw / 32767
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
        print(f'ctrl,R2,press(=R3),{value}')
        global last_controll_time
        last_controll_time = time.time()
        # 右モーター前進/後退
        power = -transf(value)
        print(f"Setting motor_right.value to {power}")
        motor_right.value = power
        print(f"motor_right.value is now {motor_right.value}")
        # print(power)

    def on_R2_release(self):
        print(f'ctrl,R2,release(=R3)')
        global last_controll_time
        last_controll_time = time.time()
        # 右モーター前進/後退
        motor_right.value = 0
    
    def on_L3_up(self, value):
        print(f'ctrl,L3,up,{value}')
        global last_controll_time
        last_controll_time = time.time()
        # 左モーター前進
        power = -transf(value)
        print(f"Setting motor_left.value to {power}")
        motor_left.value = power
        print(f"motor_left.value is now {motor_left.value}")
        # print(power)
    
    def on_L3_down(self, value):
        print(f'ctrl,L3,down,{value}')
        global last_controll_time
        last_controll_time = time.time()
        # 左モーター後退
        power = -transf(value)
        print(f"Setting motor_left.value to {power}")
        motor_left.value = power
        print(f"motor_left.value is now {motor_left.value}")
        # print(power)

    def on_L3_y_at_rest(self, value):
        print(f'ctrl,L3,rest,{value}')
        global last_controll_time
        last_controll_time = time.time()
        # 左モーター後退
        power = -transf(value)
        motor_left.value = power
        print(power)


    def on_x_press(self):
        print('ctrl,x,press')
        global last_controll_time
        last_controll_time = time.time()
        # 音楽を再生
        audio_play()
    
    def on_square_press(self):
        print('ctrl,square,press')
        global last_controll_time
        last_controll_time = time.time()
        # ライトをオン…しません
        # high_power_led.on()

    def on_square_release(self):
        print('ctrl,square,release')
        global last_controll_time
        last_controll_time = time.time()
        # ライトをオフ…しません
        # high_power_led.off()

def connect():
    print('ctrl,connect')

def disconnect():
    print('ctrl,disconnect')

def start_controller():
    controller = MyController(interface="/dev/input/js0", connecting_using_ds4drv=False)
    controller.listen(on_connect=connect, on_disconnect=disconnect)


##### GUI #####

def read_from_gui():
    global last_controll_time
    if time.time() - last_controll_time < 1:
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
        audio_play()
    print(f"gui,{data_from_browser['motor_l']},{data_from_browser['motor_r']},{data_from_browser['light']},{data_from_browser['buzzer']}")

def write_to_gui():
    data_to_browser = {}
    data_to_browser['motor_r'] = motor_right.value
    data_to_browser['motor_l'] = motor_left.value
    data_to_browser['light'] = high_power_led.value
    data_to_browser['buzzer'] = False if (proces_aplay.poll() == None) else True
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


##### モーターの動作確認 #####

motor_calib()


##### 平行処理を開始 #####

# コントローラーを起動
controller_thread = threading.Thread(target=start_controller)

# GUI用のサーバーを起動
server_thread = threading.Thread(target=start_gui.start_server)

# GUIのデータを読み込み・書き込み
gui_thread = threading.Thread(target=update_gui)

# カメラで撮影開始
camera_thread = threading.Thread(target=start_camera)

controller_thread.start()
server_thread.start()
gui_thread.start()
camera_thread.start()


while threading.active_count() != 1:
    print(f'main,{threading.active_count()}')
    time.sleep(10)

### 参考にしたサイト
# thread関連
# https://qiita.com/kaitolucifer/items/e4ace07bd8e112388c75
# コントローラーの接続
# https://hellobreak.net/raspberry-pi-ps4-controller-0326/