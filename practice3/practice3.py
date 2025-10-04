import os
import socket
from datetime import datetime


class SocketServer:
    def __init__(self):
        self.bufsize = 1024 # 버퍼 크기 설정
        with open('./response.bin', 'rb') as file:
            self.RESPONSE = file.read() # 응답 파일 읽기

        self.DIR_PATH = './request'
        self.createDir(self.DIR_PATH)

    def createDir(self, path):
        """디렉토리 생성"""
        try:
            if not os.path.exists(path):
                os.makedirs(path)
        except OSError:
            print("Error: Failed to create the directory.")

    def run(self, ip, port):
        # 소켓 생성
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind((ip, port))
        self.sock.listen(10)
        print("Start the socket server...")
        print("\nCtrl+C\" for stopping the server !\r\n")

        try:
            while True:
                # 클라이언트의 요청 대기
                clnt_sock, req_addr = self.sock.accept()
                clnt_sock.settimeout(5.0) # 타임아웃 설정 (5초)
                print("Request message...\r\n")

                response = b""
                # 여기에 구현하세요.
                while True:
                    try:
                        chunk = clnt_sock.recv(self.bufsize)
                        if not chunk:  # 더 이상 읽을 데이터가 없으면 중단
                            break
                        response += chunk  # 기존 response 뒤에 이어붙임
                    except socket.timeout:
                        break
                    except ConnectionResetError:
                        break

                # 타임스탬프 파일명으로 저장
                ts = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
                file_path = os.path.join(self.DIR_PATH, f"{ts}.bin")
                with open(file_path, "wb") as f:
                    f.write(response)

                print(f"Saved request: {file_path} ({len(response)} bytes)")



                # 응답 전송
                clnt_sock.sendall(self.RESPONSE)

                # 클라이언트 소켓 닫기
                clnt_sock.close()
        except KeyboardInterrupt:
            print("\nStop the server...")

        # 서버 소켓 닫기
        self.sock.close()


if __name__ == "__main__":
    server = SocketServer()
    server.run("127.0.0.1", 8000)