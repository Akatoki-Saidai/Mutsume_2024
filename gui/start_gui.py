import http.server
import socketserver
import socket
import ipaddress

# 任意のサーバーにアクセスしIPを確認
try:
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(('1.1.1.1', 80))
    local_ip = ipaddress.ip_address(s.getsockname()[0])
except Exception as e:
    local_ip = socket.gethostbyname_ex(socket.gethostname())[2][0]

HOST, PORT = '', 8000

# 受信用のJSONファイルを作成
with open("./data_from_browser", "w") as f:
    f.write('{"motor_l": 0, "motor_r": 0, "light": false, "buzzer": false }')

# 送信用のJSONファイルを作成
with open("./data_to_browser", "w") as f:
    f.write('{\n    "motor_l": 0,\n    "motor_r": 0,\n    "light": false,\n    "buzzer": false,\n    "lat": null,\n    "lon": null,\n    "grav": [null, null, null],\n    "mag": [null, null, null],\n    "local_ip": "' + str(local_ip) + ':' + str(PORT) + '"\n}')

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
    print("サーバーが稼働しました！\n同じネットワーク内のブラウザで http://" + str(local_ip) + ":" + str(PORT) + " にアクセスしてください")
    httpd.serve_forever()

## 参考にしたサイト
# https://stackoverflow.com/questions/66514500/how-do-i-configure-a-python-server-for-post