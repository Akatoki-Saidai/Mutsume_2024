#-*- cording: utf-8 -*-

import subprocess

try:
    try:
        # print("glados")
        if glados.poll() is None:
            # ファイルパス要変更
            glados = subprocess.Popen("aplay /home/desktop/grados.wav", shell=True)
            print(glados.returncode)
        else:
            print("spreaker is running now!")
            print(glados.returncode)
    except subprocess.SubprocessError as sp_e:
        print(f"An error occuerd runnning speaker subprocess(grados): {sp_e}")
except Exception as e:
    print(f"An error occuerd runnning speaker: {e}")


