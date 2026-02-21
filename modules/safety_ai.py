import json
import streamlit as st
import google.generativeai as genai

def generate_draft_equipment(api_key, task_name, location, risk_factors, risk_context_manual, ref_vocab_text, ref_data_text):
    """1단계: 장비 및 준비물 추천 초안 생성"""
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-flash-latest', generation_config={"response_mime_type": "application/json"})
        
        req_prompt = f"""
            건설 안전 전문가로서 다음 작업에 필요한 장비와 준비물을 제안하세요.
            
            [작업 정보]
            - 작업명: {task_name}
            - 장소: {location}
            - 위험 특성: {', '.join(risk_factors)}
            - 기타: {risk_context_manual}
            
            {ref_vocab_text}
            {ref_data_text}
            
            [요청 사항]
            **작업명 "{task_name}"에 정확히 맞는** 장비와 준비물을 추천하세요.
            참고 데이터가 있더라도, 실제 작업 내용과 맞지 않으면 무시하고 작업명에 맞게 새로 작성하세요.
            위 '현장 표준 용어'에 해당 항목이 있으면 반드시 그 용어를 그대로 사용하세요.
            1. 보호구 (필수 및 권장)
            2. 안전장비 (시설물 포함)
            3. 사용 공구/장비
            4. 준비자료 (허가서 등)
            
            [중요 규칙]
            - 모든 항목명에 괄호 안 부가설명을 넣지 마세요.
              예: "안전모" (O), "안전모(턱끈포함)" (X), "굴착기" (O), "굴착기(백호우)" (X)
            - "안전대" 대신 반드시 "전체식 안전벨트"로 작성하세요.
            - 공구/장비명은 현장에서 실제 사용하는 용어를 쓰세요.
            - **[제외 항목]** 스패너, 렌치, 드라이버, 망치 등 작업자가 손으로 들고 다니는 소형 수공구는 절대 포함하지 마세요. (주요 대형 장비 위주로 작성)
            - **[제외 항목]** 샤클, 슬링벨트, 용접봉, 절단석 등 소모성 자재나 너무 세세한 부속품은 제외하세요.
            - **[제외 서류]** "신호수배치확인서", "건설기계검사증" 등은 제외하고 "작업계획서", "안전작업 허가서" 등 핵심 서류만 포함하세요.
            - **[명칭 통일]** "작업허가서"와 "안전작업 허가서"가 중복되지 않게 "안전작업 허가서"로 통일하세요.
            - **[장비 명칭]** 시트파일/파일 공사 시 "바이브레이터"는 혼동될 수 있으므로 "진동 해머(Vibro Hammer)" 또는 "항타기"로 명확히 적으세요. (콘크리트 타설 시에만 "바이브레이터" 사용)
            - 소화기는 화기작업(용접, 가스절단, 도장 등)에만 포함하세요.
            - 작업명에 맞는 실제 장비를 추천하세요 (부속품 제외):
              * 콘크리트/MAT 타설: 공구→레미콘, 펌프카, 바이브레이터 / 안전장비→반사경, 스토퍼
              * 자재반입/하역/운반: 공구→지게차, 카고트럭, 와이어로프 / 안전장비→신호봉, 라바콘
              * 철근작업: 공구→절단기, 절곡기(밴딩기)
              * 비계/가설: 공구→전동공구 / 안전장비→안전네트, 추락방지망
            - 해당 작업에 실제로 사용하지 않는 장비는 절대 포함하지 마세요.
            
            [JSON 포맷]
            {{
                "protectors": "안전모, 안전화, ...",
                "safety_equip": "CCTV, 라바콘, ...",
                "tools": "...",
                "docs": "..."
            }}
            """
        
        response = model.generate_content(req_prompt)
        return json.loads(response.text)
    except Exception as e:
        raise e

def generate_risk_assessment(api_key, task_name, location, risk_factors, risk_context_manual, protectors, safety_equip, tools, materials, ref_vocab_text, ref_risks_text):
    """2단계: 위험성평가표 생성"""
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(
            'gemini-flash-latest', 
            generation_config={"response_mime_type": "application/json"}
        )

        prompt = f"""
        건설 안전 기술사로서 아래 작업에 대한 위험성평가표(JSA)를 작성하세요.
        
        [작업 정보]
        - 작업명: {task_name}
        - 작업 위치: {location}
        - 위험 특성: {', '.join(risk_factors)} / {risk_context_manual}
        - 보호구: {', '.join(protectors)}
        - 안전장비: {', '.join(safety_equip)}
        - 사용장비: {', '.join(tools)}
        - 준비자료: {', '.join(materials)}
        
        {ref_vocab_text}
        {ref_risks_text}
        
        [작업 규칙]
        1. '작업준비' -> '본작업' -> '작업종료/정리' 3단계를 기본으로 하되, **'본작업'은 반드시 구체적인 단위 작업명으로 세분화해서 작성하세요.** (예: '본작업: 펌프카 설치', '본작업: 타설 진행')
        2. '작업준비' 단계의 맨 첫 번째 행은 반드시 '작업자 개인 보호구 및 복장 상태 확인'에 대한 내용이어야 합니다.
        3. [중요] **위험요인별 대책 개수는 '위험성 등급'에 따라 다르게 작성하세요.**
           - **상(6점 이상):** 반드시 **4개 ~ 5개**의 구체적 대책 작성
           - **중(3점 ~ 5점):** 반드시 **3개**의 대책 작성
           - **하(2점 이하):** 반드시 **2개**의 대책 작성
           **(각 대책의 시작 부분에 반드시 "- "를 붙여서 구분하세요. 줄바꿈은 반드시 '\\n' 문자를 사용하세요. 실제 엔터키 사용 금지)**
        4. [중요] **위험성 평가 점수(빈도×강도)를 보수적으로 산정하세요.**
           - 무조건적인 고위험 평가를 지양하고, 현실적인 빈도(1~3)와 강도(1~2)를 우선 고려하세요.
           - 특별히 위험한 경우가 아니라면 '상' 등급(6점 이상)이 너무 많이 나오지 않도록 조절하세요.
           - 빈도는 1~5, 강도는 1~4 범위 내에서 선택하되, 곱(위험성)이 절대 8을 초과하지 않도록 하세요.
        5. 반드시 JSON 포맷으로만 출력하세요. (Markdown 코드 블록 없이 순수 JSON만 출력)
        6. [중요] 위 '현장 표준 용어'에 있는 표현을 우선적으로 사용하세요. 현장 실무 용어를 그대로 쓰세요.
        7. [중요] **반드시 최소 12개 이상, 최대 20개 이하의 위험요인 항목**을 생성하세요.
           - '작업준비': 3~4개
           - '본작업: (세부단계1)': 3~5개
           - '본작업: (세부단계2)': 3~5개 (필요시 세부단계 추가)
           - '작업종료/정리': 2~3개
        8. [중요] **위험요인은 반드시 1가지 위험만 기술하세요.** 여러 위험을 "및", "또는"으로 묶지 마세요.
           - 잘못된 예: "체인 이탈 또는 파손으로 인한 낙하 및 깔림 위험" (X)
           - 올바른 예: "체인 이탈로 인한 자재 낙하 위험" (O) → 별도 행: "인양 자재에 의한 작업자 깔림 위험" (O)
           각 위험요인에 대해 그에 맞는 구체적인 대책을 작성하세요.
        
        [JSON 예시]
        [
            {{"단계": "1) 작업준비", "위험요인": "...", "대책": "...", "빈도": 2, "강도": 3}},
            {{"단계": "2) 본작업: ...", "위험요인": "...", "대책": "...", "빈도": 2, "강도": 3}}
        ]
        """
        
        response = model.generate_content(prompt)
        
        # JSON 파싱 전처리
        text = response.text
        if "```json" in text:
            text = text.replace("```json", "").replace("```", "")
        text = text.strip()
        
        raw_data = json.loads(text, strict=False)
        
        # [NEW] Explode multiline '대책' into separate rows for DataEditor UI
        exploded_data = []
        for row in raw_data:
            measures_text = str(row.get("대책", ""))
            
            # Split by newline and remove empty lines
            meas_lines = [line.strip() for line in measures_text.split('\n') if line.strip()]
            
            if not meas_lines:
                # Fallback if somehow empty
                meas_lines = ["- 대책을 입력하세요."]
                
            for meas in meas_lines:
                new_row = row.copy()
                new_row["대책"] = meas
                exploded_data.append(new_row)
            
        return exploded_data
    except Exception as e:
        raise e
