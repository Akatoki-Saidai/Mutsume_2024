import pyaudio
import threading
import wave

class Playing():
    now = False  # 実質的なグローバル変数

def _play_audio(filename):
    print('speaker,play,start')
    with wave.open(filename, 'rb') as wf:
        # PyAudioのインスタンスを生成
        speaker = pyaudio.PyAudio()

        # Streamを生成
        stream = speaker.open(format=speaker.get_format_from_width(wf.getsampwidth()),
                        channels=wf.getnchannels(),
                        rate=wf.getframerate(),
                        output=True)

        """
        format: ストリームを読み書きする際のデータ型
        channels: モノラルだと1、ステレオだと2、それ以外の数字は入らない
        rate: サンプル周波数
        output: 出力モード
        """

        # チャンク数を指定
        CHUNK = 16

        # データを1度に16個読み取る
        data = wf.readframes(CHUNK)

        # 実行
        while data != '':
            # ストリームへの書き込み
            stream.write(data)
            # 再度1024個読み取る
            data = wf.readframes(CHUNK)

        # ファイルが終わったら終了処理
        stream.stop_stream()
        stream.close()

        speaker.terminate()
    print('speaker,play,end')

def play():
    if not Playing.now:
        Playing.now = True
        t = threading.Thread(target=_play_audio, args=('ファイル名1.wav',))
        t.start()
        Playing.now = False

# def play2():
#     if not Playing.now:
#         Playing.now = True
#         t = threading.Thread(target=play_audio, args=('ファイル名2.wav',))
#         t.start()
#         Playing.now = False