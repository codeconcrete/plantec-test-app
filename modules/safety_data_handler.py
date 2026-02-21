import json
import re
import streamlit as st

def parse_to_list(text_data):
    if isinstance(text_data, list):
        return text_data
    if not text_data:
        return []
    return [item.strip() for item in text_data.split(',') if item.strip()]

def clean_item_list(items):
    """모든 항목에서 괄호 내용 제거 및 특수 치환"""
    cleaned = []
    for item in items:
        # Remove text in parentheses: "굴착기(백호우)" -> "굴착기", "안전모(턱끈포함)" -> "안전모"
        new_item = re.sub(r'\([^)]*\)', '', item).strip()
        
        # Specific replacements
        if "안전대" in new_item and "벨트" not in new_item:
            new_item = "전체식 안전벨트"
        
        if new_item:
            cleaned.append(new_item)
    # Remove duplicates while preserving order
    return list(dict.fromkeys(cleaned))

@st.cache_data
def load_safety_index():
    """safety_data.json의 모든 단위작업을 인덱싱하여 키워드 매칭이 가능하게 함"""
    try:
        with open('safety_data.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
    except:
        return [], {}, {}
    
    index = []  # [{name, keywords, data, division, work_type, path}, ...]
    all_vocab = {"protectors": set(), "safety_equip": set(), "tools": set(), "docs": set()}
    
    # 키워드 추출 함수: 번호/괄호 제거 후 핵심 단어만 추출
    def extract_keywords(text):
        # 번호 제거: "1) 가설공사" -> "가설공사", "(7) 콘크리트 타설 및 양생" -> "콘크리트 타설 및 양생"
        cleaned = re.sub(r'^\d+\)\s*', '', text)
        cleaned = re.sub(r'^\(\d+\)\s*', '', cleaned)
        # 공백, 특수문자로 분리
        words = re.split(r'[\s,/·및\-_]+', cleaned)
        # 의미있는 단어만 (1글자 이상)
        keywords = set()
        for w in words:
            w = w.strip()
            if len(w) >= 1:
                keywords.add(w.lower())
        return keywords
    
    # 동의어 매핑 (사용자가 입력할 수 있는 다양한 표현 대응)
    synonym_map = {
        'mat': ['콘크리트', '타설', 'mat'],
        '타설': ['콘크리트', '타설', '양생'],
        '콘크리트': ['콘크리트', '타설', 'conc', 'rc'],
        '비계': ['비계', '가설', '스캐폴딩'],
        '용접': ['용접', '화기'],
        '배관': ['배관', '파이프', 'pipe'],
        '도장': ['도장', '페인트', '방청'],
        '철근': ['철근', '배근', 'conc', 'rc'],
        '토공': ['토공', '굴착', '되메우기', '터파기'],
        '굴착': ['토공', '굴착', '터파기'],
        '방수': ['방수', '우레탄', '아스팔트', '시트'],
        '거푸집': ['거푸집', '폼', '형틀', '탈형'],
        '양중': ['양중', '크레인', '인양'],
        '크레인': ['양중', '크레인', '인양'],
        '해체': ['해체', '철거', '잔재물'],
        '전기': ['전기', '배선', '케이블'],
        '철골': ['철골', '강구조', 'steel'],
        '포장': ['포장', '아스팔트', '아스콘'],
    }
    
    for division_name, division_data in data.items():
        if not isinstance(division_data, dict):
            continue
        for work_type_name, work_type_data in division_data.items():
            if not isinstance(work_type_data, dict):
                continue
            for unit_work_name, unit_work_data in work_type_data.items():
                if not isinstance(unit_work_data, dict) or "protectors" not in unit_work_data:
                    continue
                
                keywords = extract_keywords(unit_work_name)
                keywords.update(extract_keywords(work_type_name))
                
                entry = {
                    "name": unit_work_name,
                    "keywords": keywords,
                    "data": {
                        "protectors": unit_work_data.get("protectors", ""),
                        "safety_equip": unit_work_data.get("safety_equip", ""),
                        "tools": unit_work_data.get("tools", ""),
                        "docs": unit_work_data.get("docs", ""),
                    },
                    "risks": unit_work_data.get("risks", []),
                    "division": division_name,
                    "work_type": work_type_name,
                    "path": f"{division_name} > {work_type_name} > {unit_work_name}"
                }
                index.append(entry)
                
                # 전체 용어 수집 (프롬프트 참고용)
                for item in unit_work_data.get("protectors", "").split(','):
                    cleaned = re.sub(r'\([^)]*\)', '', item).strip()
                    if cleaned:
                        all_vocab["protectors"].add(cleaned)
                for item in unit_work_data.get("safety_equip", "").split(','):
                    if item.strip():
                        all_vocab["safety_equip"].add(item.strip())
                for item in unit_work_data.get("tools", "").split(','):
                    if item.strip():
                        all_vocab["tools"].add(item.strip())
                for item in unit_work_data.get("docs", "").split(','):
                    if item.strip():
                        all_vocab["docs"].add(item.strip())
    
    vocab_sorted = {k: sorted(v) for k, v in all_vocab.items()}
    return index, vocab_sorted, synonym_map

def find_best_match(task_name, index, synonym_map):
    """사용자 입력 작업명과 가장 유사한 safety_data.json 항목 찾기"""
    if not task_name or not index:
        return None, 0
    
    # 사용자 입력 키워드 추출
    user_words_raw = re.split(r'[\s,/·및\-_]+', task_name.strip())
    user_keywords = set()
    for w in user_words_raw:
        w = w.strip().lower()
        if len(w) >= 1:
            user_keywords.add(w)
            # 동의어 확장
            for syn_key, syn_values in synonym_map.items():
                if syn_key in w or w in syn_key:
                    user_keywords.update(syn_values)
    
    best_match = None
    best_score = 0
    
    for entry in index:
        entry_keywords = entry["keywords"]
        # 확장된 entry 키워드 (동의어 포함)
        expanded_entry = set(entry_keywords)
        for kw in entry_keywords:
            for syn_key, syn_values in synonym_map.items():
                if syn_key in kw or kw in syn_key:
                    expanded_entry.update(syn_values)
        
        # 교집합 기반 점수 계산
        overlap = user_keywords & expanded_entry
        if not overlap:
            continue
        
        # 점수 = 겹치는 키워드 수 / 사용자 키워드 수 (0~1) 
        score = len(overlap) / max(len(user_keywords), 1)
        
        # 직접 키워드 매칭 보너스 (원본 키워드끼리 겹치면 가산점)
        direct_overlap = set(w.lower() for w in user_words_raw if len(w.strip()) >= 1) & entry_keywords
        score += len(direct_overlap) * 0.3
        
        if score > best_score:
            best_score = score
            best_match = entry
    
    return best_match, best_score
