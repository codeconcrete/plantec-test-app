import streamlit as st
import datetime

def apply_custom_css():
    st.markdown("""
<style>
    h1, h2, h3, p, div { font-family: 'Noto Sans KR', sans-serif; }
    
    div.stButton > button {
        background-color: #0085ff; color: white; border: none;
        border-radius: 5px; padding: 10px 20px; font-weight: bold; width: 100%;
    }
    
    /* Table styling - only for the report tables */
    .safety-table {
        width: 100% !important; 
        table-layout: fixed !important;
        border-collapse: collapse;
        font-family: 'Malgun Gothic', 'Noto Sans KR', sans-serif;
        font-size: 11pt;
        margin-bottom: 5px;
        color: #000000;
    }
    .safety-table th, .safety-table td {
        border: 1px solid #000000;
        padding: 2px;
        text-align: center;
        vertical-align: middle;
        background-color: #ffffff;
        color: #000000;
        word-break: break-all;
    }
    .safety-table th {
        background-color: #f0f0f0;
        font-weight: bold;
    }
    .left-align {
        text-align: left !important;
        padding-left: 5px;
    }
    
    /* Screen A4 Preview Container */
    .a4-page {
        width: 297mm;
        height: 210mm;
        padding: 10mm 15mm 15mm 15mm; /* 상 10mm, 우하좌 15mm 적용 */
        margin: 0 auto;
        background: white;
        color: black;
        box-shadow: 0 0 10px rgba(0,0,0,0.1);
        margin-bottom: 20px;
        box-sizing: border-box;
        border: 1px solid #ddd;
        display: block;
    }
    
    /* PRINT SETTINGS - CONTAINER METHOD */
    @media print {
        @page {
            size: A4 landscape;
            margin: 0 !important;
        }
        
        html, body {
            width: max-content !important;
            height: max-content !important;
            min-width: 100% !important;
            margin: 0 !important;
            padding: 0 !important;
            background-color: white !important;
        }
        
        /* 1. Hide EVERYTHING by default */
        body * {
            visibility: hidden;
        }
        
        /* 2. Show only the printable area and its children constructed in Python */
        #printable-area, #printable-area * {
            visibility: visible;
        }
        
        /* 3. Position the printable area at top-left to overlay hidden content */
        #printable-area {
            position: absolute !important;
            left: 0 !important;
            top: 0 !important;
            width: max-content !important;
            min-width: 100% !important;
            margin: 0 !important;
            padding: 0 !important;
            z-index: 99999 !important;
        }
        
        /* 4. Restore natural flow for pages within the area */
        .a4-page {
            position: relative !important;
            width: max-content !important;
            min-width: 297mm !important;
            height: max-content !important;
            min-height: 200mm !important;
            page-break-after: always !important;
            page-break-inside: avoid !important;
            margin: 0 !important;
            padding: 10mm 15mm 15mm 15mm !important; /* 상 10mm, 우하좌 15mm 적용 (화면과 동일) */
            box-sizing: border-box !important;
            background-color: white !important;
            box-shadow: none !important;
            border: none !important;
            -webkit-print-color-adjust: exact;
            print-color-adjust: exact;
            display: block !important;
        }
        
        /* 5. Escape Streamlit's nested layout boundaries */
        .stApp, [data-testid="stAppViewContainer"], [data-testid="stMain"], [data-testid="stMainBlockContainer"], .block-container, div[data-testid="stVerticalBlock"], .element-container, .stMarkdown, [data-testid="stMarkdownContainer"] {
            position: static !important;
            width: 100% !important;
            max-width: 100% !important;
            min-width: 0 !important;
            margin: 0 !important;
            padding: 0 !important;
            height: auto !important;
            min-height: 0 !important;
            overflow: visible !important;
            transform: none !important;
            display: block !important;
        }
        
        /* Hide UI elements rigorously */
        header, footer, [data-testid="stHeader"], [data-testid="stSidebar"], .stButton, .no-print, [data-testid="stToolbar"] {
            display: none !important;
        }
    }
    
    /* End of Safety UI CSS */
        
        .safety-table {
            width: 100% !important;
        }
</style>
""", unsafe_allow_html=True)

def disable_translation():
    import streamlit.components.v1 as components
    # Streamlit 기본 html lang="en" 속성 등에 의해 Edge 번역 팝업이 뜨는 것을 원천적으로 막기 위한 JS Injection
    js = """
    <script>
        var doc = window.parent.document;
        doc.documentElement.lang = 'ko';
        doc.documentElement.setAttribute('translate', 'no');
        
        if (!doc.querySelector('meta[name="google"]')) {
            var meta = doc.createElement('meta');
            meta.name = 'google';
            meta.content = 'notranslate';
            doc.head.appendChild(meta);
        }
    </script>
    """
    components.html(js, height=0, width=0)

def create_header_html(task_name, location, protectors, safety_equip, tools, materials, writer, writer_date, action_taker, reviewer, reviewer_date, checker, approver, approver_date):
    return f'''
<div style="text-align:right; font-size:10px; margin-bottom:5px; color:black;">(보존기간 : 3년)</div>
<table class="safety-table" style="width: 100%; table-layout: fixed;">
    <colgroup>
        <col style="width: 15%;">
        <col style="width: 35%;">
        <col style="width: 10%;">
        <col style="width: 15%;">
        <col style="width: 10%;">
        <col style="width: 15%;">
    </colgroup>
    <tr>
        <th>단위 작업명</th>
        <td class="left-align" colspan="5" style="color: blue; font-weight: bold; font-size:14px;">{task_name}</td>
    </tr>
    <tr>
        <th>보 호 구</th>
        <td class="left-align">{', '.join(protectors)}</td>
        <th>작 업 구 역</th>
        <td colspan="3" class="left-align">{location}</td>
    </tr>
    <tr>
        <th>안 전 장 비</th>
        <td class="left-align">{', '.join(safety_equip)}</td>
        <th>작성자</th>
        <td style="text-align: left; padding-left: 5px; padding-right: 5px;">{writer} <span style="float: right; color: #999;">(서 명)</span></td>
        <th>작성일</th>
        <td>{writer_date}</td>
    </tr>
    <tr>
        <th>공구 및 장비</th>
        <td class="left-align">{', '.join(tools)}</td>
        <th>검토자</th>
        <td style="text-align: left; padding-left: 5px; padding-right: 5px;">{reviewer} <span style="float: right; color: #999;">(서 명)</span></td>
        <th>검토일</th>
        <td>{reviewer_date}</td>
    </tr>
    <tr>
        <th>준비 자료</th>
        <td class="left-align">{', '.join(materials)}</td>
        <th>승인자</th>
        <td style="text-align: left; padding-left: 5px; padding-right: 5px;">{approver} <span style="float: right; color: #999;">(서 명)</span></td>
        <th>승인일</th>
        <td>{approver_date}</td>
    </tr>
    <tr>
        <th>조치자</th>
        <td style="text-align: left; padding-left: 5px; padding-right: 5px;">{action_taker} <span style="float: right; color: #999;">(서 명)</span></td>
        <th>이행상태 확인</th>
        <td colspan="3" style="text-align: left; padding-left: 5px; padding-right: 5px;">{checker} <span style="float: right; color: #999;">(서 명)</span></td>
    </tr>
</table>
'''

import math

def count_view_lines(text, chars_per_line):
    """줄바꿈과 자동 줄바꿈(wrapping)을 모두 고려한 줄 수 계산"""
    if not text:
        return 1
    # Fix: Split by actual newline character, not literal string '\n'
    lines = str(text).split('\n')
    total = 0
    for line in lines:
        length = len(line)
        if length == 0:
            total += 1
        else:
            total += math.ceil(length / chars_per_line)
    return total

def split_text_to_fit(text, max_lines, chars_per_line):
    """주어진 줄 수(max_lines)에 맞춰 텍스트를 앞부분(head)과 뒷부분(tail)으로 분리"""
    if not text:
        return "", ""
    
    # Fix: Split by actual newline character
    raw_lines = str(text).split('\n')
    head_lines = []
    tail_lines = []
    
    current_lines = 0
    
    for i, line in enumerate(raw_lines):
        line_len = len(line)
        # Empty line takes 1 line of space
        line_cost = 1 if line_len == 0 else math.ceil(line_len / chars_per_line)
        
        if current_lines + line_cost <= max_lines:
            head_lines.append(line)
            current_lines += line_cost
        else:
            # 이 줄에서 잘라야 함 or this line itself is too big
            # Calculate remaining lines we can fit
            remaining_lines_capacity = max_lines - current_lines
            
            if remaining_lines_capacity > 0:
                # Can fit some part of this line.
                # How many chars can we fit?
                # Each line we can fit takes 'chars_per_line' chars.
                # So we can take roughly remaining_lines_capacity * chars_per_line
                
                # Careful: complex split logic.
                # If remaining_lines_capacity is 1, we can take up to 1 * chars_per_line.
                max_chars = int(remaining_lines_capacity * chars_per_line)
                
                if max_chars > 0 and line_len > 0:
                     # Split at max_chars (or line_len if smaller, but logic says line_len is bigger or else it would fit)
                     split_idx = min(max_chars, line_len)
                     
                     head_lines.append(line[:split_idx])
                     tail_lines.append(line[split_idx:])
                     tail_lines.extend(raw_lines[i+1:])
                     return '\n'.join(head_lines), '\n'.join(tail_lines)
            
            # If we cannot fit even a single char or logic above case falling through:
            # Put entire line in tail
            tail_lines.append(line)
            tail_lines.extend(raw_lines[i+1:])
            return '\n'.join(head_lines), '\n'.join(tail_lines)
            
    return '\n'.join(head_lines), ""

def split_measures_by_bullet(text, max_lines, chars_per_line):
    """
    대책 텍스트를 '- ' 단위로 파싱하여, max_lines 내에 들어가는 만큼만 head로 반환.
    중간에 짤리면 해당 항목 전체를 tail로 넘김 (통째로 다음페이지 이동).
    """
    if not text:
        return "", ""
    
    # 1. 항목 단위로 파싱
    lines = str(text).split('\n')
    items = []
    current_item = []
    
    for line in lines:
        stripped = line.strip()
        # 대책 구분: 하이픈(-) 또는 번호(1.) 등으로 시작하면 새로운 항목
        if stripped.startswith('-') or stripped.startswith('•') or (stripped and stripped[0].isdigit() and stripped[1] == '.') or (len(current_item) == 0):
             if current_item:
                 items.append("\n".join(current_item))
             current_item = [line]
        else:
             # 줄바꿈되었지만 같은 항목의 내용인 경우 연결
             current_item.append(line)
    if current_item:
        items.append("\n".join(current_item))
        
    # 2. 높이 계산 및 분배
    head_items = []
    tail_items = []
    current_h = 0
    
    for i, item in enumerate(items):
        # 해당 항목의 높이 계산
        h = count_view_lines(item, chars_per_line)
        
        if current_h + h <= max_lines:
            head_items.append(item)
            current_h += h
        else:
            # 공간 부족: 이 항목부터는 모두 tail로 (통째로 넘김)
            tail_items = items[i:]
            break
            
    return "\n".join(head_items), "\n".join(tail_items)
