import cv2
import socketio
import base64

# 创建 Socket.IO 实例
sio = socketio.Client()
@sio.event
def connect():
    print('Connected to server')

# 向服务器发送消息
def send_message(message):
    sio.emit('message', message)

# 监听服务器的响应
@sio.on('response')
def handle_response(data):
    print('Server response:', data)

# 向服务器发送帧数据
def send_frame(frame):
    try:
        resized_frame = cv2.resize(frame, (640, 640))
        # 将帧编码为 JPEG 格式并转换为 base64 编码字符串
        encoded_frame = base64.b64encode(cv2.imencode('.jpg', resized_frame, [cv2.IMWRITE_JPEG_QUALITY, 50])[1]).decode('utf-8')
        sio.emit('frame', encoded_frame)
    except Exception as e:
        print('Error sending frame:', e)

# 运行客户端
if __name__ == '__main__':
    cap = cv2.VideoCapture(1)  # 0代表默认摄像头
    try:
        sio.connect('ws://47.99.83.0:5000/')  # 使用正确的 WebSocket 地址
        # 向服务器发送消息
        send_message('Hello, server!')
        while True:
            ret, frame = cap.read()
            if ret:
                send_frame(frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):  # 按q键退出循环
                break
    finally:
        cap.release()
        cv2.destroyAllWindows()
        sio.disconnect()
