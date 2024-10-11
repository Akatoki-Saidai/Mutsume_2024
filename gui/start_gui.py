import http.server
import socketserver
import socket
import ipaddress

# 任意のサーバーにアクセスしIPを確認
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.connect(('8.8.8.8', 80))
local_ip = ipaddress.ip_address(s.getsockname()[0])

HOST, PORT = '', 8000

try:
    # 受信用のJSONファイルを作成
    with open("./data_from_browser", "x") as f:
        f.write('{"motor_l": 0, "motor_r": 0, "light": false, "buzzer": false }')

    # 送信用のJSONファイルを作成
    with open("./data_to_browser", "x") as f:
        f.write('{\n    "motor_l": 0,\n    "motor_r": 0,\n    "lat": null,\n    "lon": null,\n    "grav": [null, null, null],\n    "mag": [null, null, null],\n    "map_coordinates_upper_left": [null, null],\n    "map_coordinates_lower_right": [null, null],\n    "local_ip": "' + str(local_ip) + ':' + str(PORT) + '"\n}')
except:
    pass

class Handler(http.server.SimpleHTTPRequestHandler):
    def do_POST(self):        
        file_length = int(self.headers['Content-Length'])
        with open("./data_from_browser", 'w') as f:
            f.write(self.rfile.read(file_length).decode('utf-8'))
        self.send_response(201, 'Created')
        self.end_headers()
        with open("./data_to_browser", "r") as f:
            self.wfile.write(f.read().encode('utf-8'))

with socketserver.TCPServer((HOST, PORT), Handler) as httpd:
    print("サーバーが稼働しました\n同じネットワーク内のブラウザで http://" + str(local_ip) + ":" + str(PORT) + "にアクセスしてください！")
    httpd.serve_forever()

## 参考にしたサイト
# https://stackoverflow.com/questions/66514500/how-do-i-configure-a-python-server-for-post