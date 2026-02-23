import sys
import os

# 디버그 및 PyInstaller windowed 모드 stdout 크래시 방지
class DummyWriter:
    def write(self, *args, **kwargs): pass
    def flush(self): pass

# 1. 포크 밤(무한 증식) 방지를 위한 극단적 런타임 개입 (가장 최상단)
# PyInstaller 패키징 환경에서 sys.executable 커맨드를 통해 스스로를 자식 프로세스로 호출했을 때, 
# Tkinter UI부터 실행되지 않고 즉시 Streamlit 부트스트랩으로 전환되게 만드는 백도어입니다.
if len(sys.argv) > 1 and sys.argv[1] == "RUN_STREAMLIT":
    try:
        log_f = open("debug_streamlit.log", "w", encoding="utf-8")
        sys.stdout = log_f
        sys.stderr = log_f
    except Exception:
        sys.stdout = DummyWriter()
        sys.stderr = DummyWriter()

    port = int(sys.argv[2])
    app_path = sys.argv[3]
    
    # Streamlit CLI 파서에게 맞게 파라미터 변조
    sys.argv = ["streamlit", "run", app_path, "--server.port", str(port), "--server.headless", "true", "--global.developmentMode", "false", "--server.address", "127.0.0.1", "--theme.base", "light"]
    
    from streamlit.web.cli import main
    try:
        sys.exit(main())
    except Exception as e:
        import traceback
        err_msg = traceback.format_exc()
        try:
            import ctypes
            ctypes.windll.user32.MessageBoxW(0, f"Streamlit Server Crash:\n\n{err_msg}", "SmartSafety Error", 0x10)
        except:
            pass
        traceback.print_exc()
    sys.exit(0)

import subprocess
import time
import socket
import urllib.request
import webbrowser
import tempfile

server_process = None
current_port = None

def find_free_port():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(('', 0))
    s.listen(1)
    port = s.getsockname()[1]
    s.close()
    return port

def run_streamlit(port):
    global server_process
    app_path = "safety_app.py"
    if hasattr(sys, '_MEIPASS'):
        app_path = os.path.join(sys._MEIPASS, "safety_app.py")
        cmd = [sys.executable, "RUN_STREAMLIT", str(port), app_path]
    else:
        cmd = [sys.executable, os.path.abspath(__file__), "RUN_STREAMLIT", str(port), app_path]
    
    # 터미널 창 숨김 처리 (백그라운드 실행)
    startupinfo = None
    if os.name == 'nt':
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

    env = os.environ.copy()
    
    # 자식 프로세스 구동 - 위쪽 sys.argv == "RUN_STREAMLIT" 로직으로 빠지게 됨
    server_process = subprocess.Popen(
        cmd, 
        startupinfo=startupinfo,
        env=env
    )

def check_server_ready(port, timeout=60):
    url = f"http://127.0.0.1:{port}"
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        try:
            req = urllib.request.urlopen(url, timeout=2)
            if req.getcode() == 200:
                return True
        except Exception:
            pass
        time.sleep(2)
    return False

def open_app_window(port):
    url = f"http://127.0.0.1:{port}"
    # Edge/Chrome 독립 프로세스 생존 보장을 위한 독립된 User Data Directory 지정
    temp_dir = os.path.join(tempfile.gettempdir(), "SmartSafetyAppProfile")
    os.makedirs(temp_dir, exist_ok=True)
    
    # 1순위: Windows 10/11 기본 내장 Edge 브라우저를 독립된 앱 창 모드(--app)로 띄우기
    try:
        # Edge의 실제 실행 파일 경로들을 탐색합니다.
        edge_paths = [
            r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
            r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"
        ]
        for ep in edge_paths:
            if os.path.exists(ep):
                proc = subprocess.Popen([ep, f'--app={url}', f'--user-data-dir={temp_dir}', '--window-size=1280,900', '--disable-features=Translate', '--disable-translate', '--lang=ko'])
                return proc
    except Exception:
        pass
        
    # 2순위: Chrome 브라우저를 앱 창 모드로 띄우기
    try:
        chrome_paths = [
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"
        ]
        for cp in chrome_paths:
            if os.path.exists(cp):
                proc = subprocess.Popen([cp, f'--app={url}', f'--user-data-dir={temp_dir}', '--window-size=1280,900', '--disable-features=Translate', '--disable-translate', '--lang=ko'])
                return proc
    except Exception:
        pass
        
    # 3순위: 위 브라우저들이 없으면 사용자의 기본 웹 브라우저 탭으로 열기 (프로세스 추적 불가 폴백)
    webbrowser.open(url)
    return None

if __name__ == '__main__':
    try:
        log_g = open("debug_gui.log", "w", encoding="utf-8")
        sys.stdout = log_g
        sys.stderr = log_g
    except Exception:
        sys.stdout = DummyWriter()
        sys.stderr = DummyWriter()
        
    current_port = find_free_port()
    run_streamlit(current_port)
    
    # 서버 준비 대기 (GUI 없이 백그라운드 블로킹)
    is_ready = check_server_ready(current_port, timeout=60)
    
    if is_ready:
        # 창 열기 및 핸들 획득
        browser_proc = open_app_window(current_port)
        
        if browser_proc:
            # 브라우저 창 닫힐 때까지 대기
            browser_proc.wait()
            
    # 브라우저가 직접 닫혔거나 서버 구동에 실패한 경우
    if server_process:
        server_process.terminate()
        server_process.wait(timeout=5)
        
    sys.exit(0)
