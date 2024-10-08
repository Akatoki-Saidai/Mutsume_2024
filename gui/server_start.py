import http.server
import socketserver
import socket
import json
import os


HOST, PORT = "", 8000


# 受信用のJSONファイルのフォーマット
with open("./input_data", "w") as f:
    f.write('{/n    "motor_l": 0,/n    "motor_r": 0,/n    "light": false,/n    "buzzer": false/n}')

local_ip = socket.gethostbyname_ex(socket.gethostname())[2][0]
# 送信用のJSONファイルのフォーマット
with open("./output_data", "w") as f:
    f.write('{\n    "motor_l": 0,\n    "motor_r": 0,\n    "lat": null,\n    "lon": null,\n    "grav": [null, null, null],\n    "mag": [null, null, null],\n    "map_coordinates_upper_left": [null, null],\n    "map_coordinates_lower_right": [null, null],\n    "local_ip": "' + local_ip + ':' + str(PORT) + '"\n}')

class Handler(http.server.SimpleHTTPRequestHandler):
    def do_POST(self):        
        file_length = int(self.headers['Content-Length'])
        with open("./input_data", 'w') as f:
            f.write(self.rfile.read(file_length).decode('utf-8'))
        self.send_response(201, 'Created')
        self.end_headers()
        # reply_body = '{\n"keka": 5\n}'
        # self.wfile.write(reply_body.encode('utf-8'))
        with open("./output_data", "r") as f:
            self.wfile.write(f.read().encode('utf-8'))

with socketserver.TCPServer((HOST, PORT), Handler) as httpd:
    print("serving at port", PORT)
    print("please access to http://" + local_ip + ":" + str(PORT))
    httpd.serve_forever()

## 参考にしたサイト
# https://stackoverflow.com/questions/66514500/how-do-i-configure-a-python-server-for-post