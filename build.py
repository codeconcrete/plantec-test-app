import os
import sys
import subprocess
import streamlit

def build():
    # Streamlit 패키지 경로를 동적으로 찾기
    st_path = os.path.dirname(streamlit.__file__)
    
    # 윈도우에서는 경로 구분자와 데이터 복사 구분자가 다름 (;)
    # PyInstaller --add-data "source;dest"
    st_data_hook = f"--add-data={st_path};streamlit"
    modules_hook = "--add-data=modules;modules"
    data_hook = "--add-data=safety_data.json;."
    app_hook = "--add-data=safety_app.py;."
    
    cmd = [
        "pyinstaller",
        "--noconfirm",
        "--onedir",          # 폴더 형태로 빌드 (onefile은 압축푸는 시간이 오래걸려 초기 로딩이 느림)
        "--windowed",        # 검은 터미널 창 숨김 (Tkinter 서버창만 뜸)
        "--name", "SmartSafetyDemo_v2",
        "--icon", "NONE",   # 기본 아이콘 사용
        "--hidden-import=pandas",
        "--hidden-import=google.generativeai",
        st_data_hook,
        modules_hook,
        data_hook,
        app_hook,
        "--copy-metadata=streamlit",  # <== 핵심: Streamlit 버전 체크(importlib.metadata) 용도
        "main.py"
    ]
    
    print("패키징 시작...")
    print("실행 명령어:", " ".join(cmd))
    
    # PyInstaller 구동
    subprocess.run(cmd, check=True)
    
    # [NEW] Post-build HTML patch for translation blocking
    print("Streamlit 정적 HTML 한국어/번역방지 패치 중...")
    try:
        dist_html_path = os.path.join("dist", "SmartSafetyDemo_v2", "_internal", "streamlit", "static", "index.html")
        if os.path.exists(dist_html_path):
            with open(dist_html_path, "r", encoding="utf-8") as f:
                html_content = f.read()
            
            html_content = html_content.replace('<html lang="en">', '<html lang="ko" translate="no">')
            html_content = html_content.replace('<head>', '<head><meta name="google" content="notranslate">')
            
            with open(dist_html_path, "w", encoding="utf-8") as f:
                f.write(html_content)
            print("HTML 패치 성공.")
        else:
            print(f"경고: {dist_html_path} 파일을 찾을 수 없습니다.")
    except Exception as e:
        print(f"HTML 패치 중 오류 발생: {e}")
        
    print("패키징 완료! dist/SmartSafetyDemo_v2 폴더를 확인하세요.")

if __name__ == '__main__':
    build()
