import streamlit as st
import pandas as pd
import datetime
import math
import google.generativeai as genai 
import streamlit.components.v1 as components 

# Custom Modules
from modules import safety_data_handler as data_handler
from modules import safety_ui as ui
from modules import safety_ai as ai

# 1. UI 설정 및 CSS 적용
st.set_page_config(page_title="(주)플랜텍 스마트 위험성평가 AI (체험판)", page_icon="🛡️", layout="wide")
ui.apply_custom_css()
ui.disable_translation()

# 2. 데이터 로드 및 초기화
# 시연용 체험판이므로 API 키를 코드 실행 시 강제로 주입합니다.
api_key = "AIzaSyCXP3noWGj7GCDIlCPyiW6RDrN8GXuUY24"

safety_index, ref_vocab, synonym_map = data_handler.load_safety_index()

# 참고 용어 텍스트 구성
ref_vocab_text = f"""[현장 표준 용어 참고 - 반드시 아래 용어를 우선 사용하세요]
- 보호구 용어: {', '.join(ref_vocab.get('protectors', [])[:30])}
- 안전장비 용어: {', '.join(ref_vocab.get('safety_equip', [])[:30])}
- 공구/장비 용어: {', '.join(ref_vocab.get('tools', [])[:30])}
- 준비자료 용어: {', '.join(ref_vocab.get('docs', [])[:20])}
"""

today_str = datetime.datetime.now().strftime("%Y.%m.%d")

# 3. 메인 타이틀
st.title("(주)플랜텍 스마트 위험성평가 AI")
st.caption("체험판")
st.markdown("**개발자:** (주)플랜텍 전재호")

# 카운트다운 로직 (2026년 3월 6일 기준)
target_date = datetime.date(2026, 3, 6)
today_date = datetime.date.today()
days_left = (target_date - today_date).days

if days_left > 0:
    st.warning(f"⏳ **체험판 안내**: 데모 시연을 위해 내장된 AI API 키는 **2026년 3월 6일**에 파기됩니다. (종료까지 **D-{days_left}**일)")
elif days_left == 0:
    st.warning(f"⏳ **체험판 안내**: 데모 시연을 위해 내장된 AI API 키는 **오늘** 파기됩니다. (D-Day)")
else:
    st.error("❌ **체험판 만료**: 시연용 API 키 사용 기간이 만료되었습니다. 정상적인 AI 응답이 불가능할 수 있습니다.")
    
    
st.divider()

# 4. 사용자 입력 (1단계: 작업 정보)
st.markdown("### 1. 작업 개요 및 위험 특성")
col1, col2 = st.columns(2)
with col1:
    site_name = st.text_input("현장명", placeholder="예: OO건설 현장")
    task_name = st.text_input("작업명", placeholder="예: 외부 비계 해체 작업")
    location = st.text_input("작업 위치", placeholder="예: 105동 외부 지상 3층~5층")

with col2:
    risk_factors = st.multiselect(
        "해당되는 위험 작업 특성을 모두 선택하세요 (자동 추천에 반영)",
        ["일반작업 (해당 없음)", "고소작업 (추락 위험)", "화기작업 (화재 발생)", "밀폐공간 (질식 위험)", 
         "전기작업 (감전 위험)", "중량물 취급 (근골격계/낙하)", "화학물질 취급", 
         "건설기계 사용", "해체/철거 작업"]
    )
    risk_context_manual = st.text_input("기타 위험 특성 (직접 입력)", placeholder="예: 강풍 예상, 야간 작업, 인접 장비 동시 작업 등")

# 세션 상태 초기화
if "draft_generated" not in st.session_state:
    st.session_state.draft_generated = False

# 분석 버튼
analyze_btn = st.button("📋 작업 정보 분석 및 장비 추천받기 (1단계)", use_container_width=True)

if analyze_btn:
    if not task_name:
        st.error("작업명을 입력해주세요.")
    elif not api_key:
        st.error("API 키를 먼저 입력해주세요.")
    else:
        # 유사 작업 검색
        matched_entry, match_score = data_handler.find_best_match(task_name, safety_index, synonym_map)
        
        # 참고 데이터 텍스트 구성
        ref_data_text = ""
        if matched_entry and match_score >= 0.3:
            md = matched_entry["data"]
            ref_data_text = f"""
                [참고: 유사 작업 표준 데이터 - "{matched_entry['name']}"]
                아래는 유사한 작업의 표준 데이터입니다. 하지만 사용자의 실제 작업명은 "{task_name}"이므로,
                작업 내용에 맞게 적절히 참고만 하고, 작업명에 맞지 않는 항목은 제외하거나 교체하세요.
                - 참고 보호구: {md.get('protectors', '')}
                - 참고 안전장비: {md.get('safety_equip', '')}
                - 참고 공구/장비: {md.get('tools', '')}
                - 참고 준비자료: {md.get('docs', '')}
            """
        
        with st.spinner("작업 특성을 분석하여 안전 장비를 추천 중입니다... 🤖"):
            try:
                draft_data = ai.generate_draft_equipment(
                    api_key, task_name, location, risk_factors, risk_context_manual, ref_vocab_text, ref_data_text
                )
                
                st.session_state.draft_data = draft_data
                st.session_state.matched_entry = matched_entry if (matched_entry and match_score >= 0.3) else None
                st.session_state.draft_generated = True
                
                if matched_entry and match_score >= 0.3:
                    st.success(f"📂 유사 작업 **{matched_entry['name']}**을 참고하여 AI가 **{task_name}**에 맞게 추천했습니다.")
                else:
                    st.info("🤖 AI가 작업 내용을 분석하여 추천했습니다.")
            except Exception as e:
                st.error(f"분석 실패: {e}")

# 2단계: 추천 결과 확인 및 수정
if st.session_state.draft_generated:
    st.markdown("### 2. 추천 장비 및 준비물 확인 (수정 가능)")
    matched = st.session_state.get('matched_entry')
    if matched:
        st.success(f"📂 유사 작업 **{matched.get('name', '')}** 참고 — AI가 **{task_name}**에 맞게 추천한 결과입니다. 수정 가능합니다.")
    else:
        st.info("🤖 AI가 추천한 내용입니다. 현장 상황에 맞게 수정하세요.")
    
    draft = st.session_state.draft_data
    
    # 공통 기본값
    common_defaults = {
        "protectors": ["안전모", "안전화"],
        "safety_equip": [],
        "tools": [],
        "docs": ["TBM", "안전작업 허가서"],
    }
    
    col3, col4 = st.columns(2)
    with col3:
        protectors_list = data_handler.clean_item_list(data_handler.parse_to_list(draft.get("protectors", "")))
        for d_item in common_defaults["protectors"]:
            if d_item not in protectors_list:
                protectors_list.insert(0, d_item)
        prot_defaults = [p for p in protectors_list if p in common_defaults["protectors"] or p in data_handler.clean_item_list(data_handler.parse_to_list(draft.get("protectors", "")))]
        protectors_selected = st.multiselect("보호구", options=protectors_list, default=prot_defaults)
        protectors_extra = st.text_input("보호구 추가 입력", placeholder="예: 방열복, 절연장갑 (쉼표로 구분)", key="prot_extra")
        protectors = protectors_selected + [x.strip() for x in protectors_extra.split(',') if x.strip()]

        tools_list = data_handler.clean_item_list(data_handler.parse_to_list(draft.get("tools", "")))
        for d_item in common_defaults["tools"]:
            if d_item not in tools_list:
                tools_list.insert(0, d_item)
        tools_selected = st.multiselect("사용 공구/장비", options=tools_list, default=tools_list)
        tools_extra = st.text_input("공구/장비 추가 입력", placeholder="예: 지게차, 슬링벨트 (쉼표로 구분)", key="tools_extra")
        tools = tools_selected + [x.strip() for x in tools_extra.split(',') if x.strip()]
    
    with col4:
        safety_equip_list = data_handler.clean_item_list(data_handler.parse_to_list(draft.get("safety_equip", "")))
        for d_item in common_defaults["safety_equip"]:
            if d_item not in safety_equip_list:
                safety_equip_list.insert(0, d_item)
        safety_equip_selected = st.multiselect("안전장비/시설", options=safety_equip_list, default=safety_equip_list)
        safety_extra = st.text_input("안전장비 추가 입력", placeholder="예: 안전난간, 경광등 (쉼표로 구분)", key="equip_extra")
        safety_equip = safety_equip_selected + [x.strip() for x in safety_extra.split(',') if x.strip()]

        materials_list = data_handler.clean_item_list(data_handler.parse_to_list(draft.get("docs", "")))
        for d_item in common_defaults["docs"]:
            if d_item not in materials_list:
                materials_list.insert(0, d_item)
        docs_defaults = [d for d in materials_list if d in common_defaults["docs"] or d in data_handler.parse_to_list(draft.get("docs", ""))]
        materials_selected = st.multiselect("준비자료/허가서", options=materials_list, default=docs_defaults)
        materials_extra = st.text_input("준비자료 추가 입력", placeholder="예: 밀폐공간작업허가서 (쉼표로 구분)", key="docs_extra")
        materials = materials_selected + [x.strip() for x in materials_extra.split(',') if x.strip()]
        
    # 추가 입력 필드 (결재란 및 조치자 등)
    st.markdown("##### ✍️ 추가 정보 입력 (결재란 및 담당자)  <span style='font-size:14px; font-weight:normal; color:#666;'>*날짜 등 빈칸이 필요하면 지워서 비워둘 수 있습니다.</span>", unsafe_allow_html=True)
    
    col_add1, col_add2, col_add3 = st.columns(3)
    with col_add1:
        st.markdown("**작성자 (Writer)**")
        writer_name = st.text_input("성명", value="관리감독자", key="writer_name", label_visibility="collapsed")
        writer_date_str = st.text_input("작성일", value=datetime.date.today().strftime("%Y.%m.%d"), key="writer_date")
        
        st.markdown("**조치자**")
        action_taker = st.text_input("조치자 성명", value="공급사 관리감독자", key="action_taker", label_visibility="collapsed")

    with col_add2:
        st.markdown("**검토자 (Reviewer)**")
        reviewer_name = st.text_input("성명", value="안전관리자", key="reviewer_name", label_visibility="collapsed")
        reviewer_date_str = st.text_input("검토일", value=datetime.date.today().strftime("%Y.%m.%d"), key="reviewer_date")
        
        st.markdown("**이행상태 확인**")
        checker_name = st.text_input("확인자 성명", value="시공사 관리감독자", key="checker_name", label_visibility="collapsed")

    with col_add3:
        st.markdown("**승인자 (Approver)**")
        approver_name = st.text_input("성명", value="현장소장", key="approver_name", label_visibility="collapsed")
        approver_date_str = st.text_input("승인일", value=datetime.date.today().strftime("%Y.%m.%d"), key="approver_date")

    st.markdown("---")
    generate_final_btn = st.button("🚀 위험성평가표 최종 생성하기 (2단계)", use_container_width=True)

    if generate_final_btn:
        with st.spinner("최종 위험성평가표를 생성하고 있습니다... 🛡️"):
            try:
                # 참고할 위험성평가 데이터 구성
                ref_risks_text = ""
                matched_entry = st.session_state.get('matched_entry')
                if matched_entry:
                    ref_risks_text = ''.join([
                        chr(10) + '                [참고: 표준 데이터의 유사 작업 위험성평가 예시 - 아래 내용을 참고하여 비슷한 톤과 표현으로 작성하세요]' + chr(10) +
                        chr(10).join([
                            f"                - 단계: {r.get('step','')}, 위험요인: {r.get('factor','')}, 대책: {r.get('measure','')}"
                            for r in matched_entry.get('risks', [])[:6]
                        ])
                    ])

                data = ai.generate_risk_assessment(
                    api_key, task_name, location, risk_factors, risk_context_manual,
                    protectors, safety_equip, tools, materials, ref_vocab_text, ref_risks_text
                )
                
                df = pd.DataFrame(data)
                df["위험성"] = df["빈도"] * df["강도"]
                df["등급"] = df["위험성"].apply(lambda x: "🔴 상" if x>=6 else ("🟡 중" if x>=3 else "🟢 하"))
                
                st.session_state.result_df = df
                st.success("최종 생성 완료! 아래 결과를 확인하세요.")

            except Exception as e:
                st.error(f"생성 중 오류 발생: {e}")

if 'result_df' in st.session_state:
    st.divider()
    
    # 3. 결과 수정 및 확정
    st.divider()
    st.markdown("### 📝 위험성평가 세부 편집 (전문가 모드)")
    st.info("💡 각 단계별(▼) 아코디언을 열어 위험요인 그룹 내에서 대책을 수정하세요. 표 안에서 ➕ 버튼을 누르면 해당 위험요인 바로 아래에 새 대책 행이 정확히 삽입됩니다.")
    
    if 'result_df' not in st.session_state or st.session_state.result_df.empty:
        st.warning("데이터가 없습니다.")
    else:
        current_df = st.session_state.result_df.copy()
        
        # 전체 데이터를 담을 임시 리스트 (나중에 하나로 합침)
        updated_data_frames = []
        
        # 작업단계 별로 그룹화
        grouped_by_step = current_df.groupby('단계', sort=False)
        
        for step_name, step_group in grouped_by_step:
            with st.expander(f"📁 {step_name}", expanded=True):
                # 단계 이름 수정 기능
                new_step_name = st.text_input("현재 그룹 단계명 수정", value=step_name, key=f"step_rename_{step_name}")
                
                # 다시 위험요인 별로 그룹화
                grouped_by_factor = step_group.groupby('위험요인', sort=False)
                
                for factor_name, factor_group in grouped_by_factor:
                    with st.container(border=True):
                        col_title, col_action = st.columns([8, 1])
                        # 위험요인 수정 박스
                        new_factor_name = col_title.text_input("⚠️ 유해·위험요인", value=factor_name, key=f"factor_rename_{step_name}_{factor_name}")
                        
                        # 단일 요소 빈도, 강도 추출 및 기본값 설정
                        first_row = factor_group.iloc[0]
                        default_freq = int(first_row.get('빈도', 1))
                        default_sev = int(first_row.get('강도', 1))
                        
                        col_freq, col_sev, col_risk = st.columns([1, 1, 1.5])
                        new_freq = col_freq.number_input("빈도", min_value=1, max_value=5, value=default_freq, key=f"freq_{step_name}_{factor_name}")
                        new_sev = col_sev.number_input("강도", min_value=1, max_value=4, value=default_sev, key=f"sev_{step_name}_{factor_name}")
                        
                        risk_score = new_freq * new_sev
                        risk_grade = "🔴 상" if risk_score >= 6 else ("🟡 중" if risk_score >= 3 else "🟢 하")
                        
                        # 위험성 등급을 눈에 띄게 표시
                        col_risk.markdown(f"**위험성 (등급)**<br><span style='font-size:16px;'>{risk_score} ({risk_grade})</span>", unsafe_allow_html=True)
                        
                        # 대책 입력용 에디터 (빈도/강도 제외)
                        sub_df = factor_group[['대책']].copy()
                        sub_df.insert(0, '🗑️', False) # 명시적 삭제용 체크박스
                        # "선택" 체크박스 열 너비 강제 최소화 CSS 주입
                        st.markdown("""
                        <style>
                        /* 명시적 추가/삭제 버튼을 사용하므로 왼쪽 인덱스 열을 완전히 숨김처리 */
                        div[data-testid="stDataFrame"] div[role="rowheader"] {
                            display: none !important;
                        }
                        </style>
                        """, unsafe_allow_html=True)

                        edited_sub_df = st.data_editor(
                            sub_df,
                            num_rows="fixed", # 명시적 버튼을 사용하므로 기본 동적 추가 비활성화하여 인덱스 숨김 유지
                            use_container_width=True,
                            key=f"editor_{step_name}_{factor_name}",
                            column_config={
                                "🗑️": st.column_config.CheckboxColumn("선택", help="삭제할 항목을 선택하세요", default=False, width="small"),
                                "대책": st.column_config.TextColumn("위험 제거 및 감소 대책 (더블클릭 편집)", width="large", required=True)
                            },
                            hide_index=True
                        )
                        
                        # 명시적인 행 추가/삭제 버튼 제공
                        _, add_col, del_col = st.columns([7.6, 1.2, 1.2])
                        
                        if add_col.button("추가", key=f"btn_add_{step_name}_{factor_name}", use_container_width=True):
                            # 새 빈 행 추가 
                            edited_sub_df.loc[len(edited_sub_df)] = [False, ""]
                            st.session_state['needs_rerun'] = True
                        
                        if del_col.button("삭제", key=f"btn_del_{step_name}_{factor_name}", use_container_width=True):
                            # 버튼이 눌렸을 때만 '🗑️'가 True인 행 지우기
                            edited_sub_df = edited_sub_df[edited_sub_df['🗑️'] == False].reset_index(drop=True)
                            st.session_state['needs_rerun'] = True
                        
                        # 저장용 데이터프레임에서는 삭제용 체크박스 컬럼을 지웁니다
                        final_sub_df = edited_sub_df.drop(columns=['🗑️'])
                        
                        # 하위 표 계산식 복원 (위에서 입력한 단일 빈도/강도를 전체 대책에 동일 적용)
                        final_sub_df['대책'] = final_sub_df['대책'].fillna('- 대책을 입력하세요.')
                        final_sub_df["빈도"] = new_freq
                        final_sub_df["강도"] = new_sev
                        final_sub_df["위험성"] = risk_score
                        final_sub_df["등급"] = risk_grade
                        
                        # 다시 상위 정보(단계, 위험요인)를 붙여서 보관
                        final_sub_df.insert(0, '위험요인', new_factor_name)
                        final_sub_df.insert(0, '단계', new_step_name)
                        
                        # 대책이 하나라도 남아있는 경우만 추가 (모두 삭제하면 그룹 자체를 생략)
                        if not final_sub_df.empty:
                            updated_data_frames.append(final_sub_df)
                        
        # 3. 모든 그룹 변경사항을 하나의 Dataframe으로 재병합 (A4 출력을 위함)
        if updated_data_frames:
            st.session_state.result_df = pd.concat(updated_data_frames, ignore_index=True)

    # A4 출력 로직
    st.divider()
    st.markdown("### 📋 위험성평가 결과 (A4 출력용)")
    
    df = st.session_state.result_df.copy()
    
    # [NEW] PDF 출력을 위한 대책 Roll-up (동일 위험요인의 개별 행들을 하나로 병합)
    rollup_rows = []
    
    # 단계와 위험요인 순서를 유지하며 그룹화
    for (step, factor), group in df.groupby(['단계', '위험요인'], sort=False):
        # 빈 대책이나 '-' 만 있는 텍스트는 걸러내고 조인
        measures = group['대책'].astype(str).tolist()
        valid_measures = [m for m in measures if m.strip() and m.strip() != '-']
        combined_measures = "\n".join(valid_measures) if valid_measures else "- 대책을 입력하세요."
        
        # 빈도, 강도는 그룹 내 최댓값 적용
        max_freq = int(group['빈도'].max())
        max_int = int(group['강도'].max())
        max_risk = max_freq * max_int
        grade_text = "상" if max_risk >= 6 else ("중" if max_risk >= 3 else "하")
        max_grade = f"{max_risk}({grade_text})"
        
        rollup_rows.append({
            '단계': step,
            '위험요인': factor,
            '대책': combined_measures,
            '빈도': max_freq,
            '강도': max_int,
            '위험성': max_risk,
            '등급': max_grade
        })
        
    rollup_df = pd.DataFrame(rollup_rows)
    
    # Flatten Data for Pagination
    grouped_df = rollup_df.groupby('단계', sort=False)
    flat_data = []
    
    for step_name, group in grouped_df:
        first_in_group = True
        for idx, row in group.iterrows():
            item = row.to_dict()
            item['is_first'] = first_in_group
            item['step_name'] = step_name
            item['group_size'] = len(group)
            flat_data.append(item)
            first_in_group = False
            
    # Dynamic Pagination Logic using UI helper
    pages = []
    current_page = []
    
    current_height = 0
    
    # Header HTML
    header_html = ui.create_header_html(
        task_name, location, site_name, protectors, safety_equip, tools, materials,
        writer_name, writer_date_str, action_taker, 
        reviewer_name, reviewer_date_str, checker_name, 
        approver_name, approver_date_str
    )
    
    # Calculate Dynamic Header Height
    # Base height for header includes the fixed rows and standard spacing
    # Base height for header includes the fixed rows and standard spacing
    base_header_lines = 15.0 # Increased base lines to account for padding & margins tighter
    
    # Calculate extra lines needed for long text in header fields
    # Make characters per line VERY conservative based on the visual column widths
    extra_title_lines = max(0, ui.count_view_lines(task_name, 45) - 1)
    extra_prot_lines = max(0, ui.count_view_lines(', '.join(protectors), 30) - 1)
    extra_loc_lines = max(0, ui.count_view_lines(location, 30) - 1)
    extra_equip_lines = max(0, ui.count_view_lines(', '.join(safety_equip), 30) - 1)
    extra_tools_lines = max(0, ui.count_view_lines(', '.join(tools), 30) - 1)
    extra_mat_lines = max(0, ui.count_view_lines(', '.join(materials), 30) - 1)
    
    # Add up all the extra lines that expand the header vertically
    # Some items are on the same row, so we take the max of the row's items
    row2_extra = max(extra_prot_lines, extra_loc_lines)
    row3_extra = extra_equip_lines
    row4_extra = extra_tools_lines
    row5_extra = extra_mat_lines
    
    total_header_lines = base_header_lines + extra_title_lines + row2_extra + row3_extra + row4_extra + row5_extra
    
    # Capacity in "lines" (Heuristic) - User-specified values
    PAGE_N_CAPACITY = 43.0 
    # Page 1: fixed total height. Base content=33 when header is minimal.
    # When header grows, content area shrinks proportionally.
    extra_header = total_header_lines - base_header_lines  # only the overflow
    PAGE_1_CAPACITY = max(10.0, 33.0 - extra_header)
    
    limit = PAGE_1_CAPACITY
    
    # Process items as a queue
    queue = flat_data.copy()
    
    while queue:
        item = queue.pop(0)
        
        measure_text = str(item.get('대책', ''))
        factor_text = str(item.get('위험요인', ''))
        
        # Calculate height: relaxed constraints increase line capacity per row
        step_lines = ui.count_view_lines(item['step_name'], 10) if item['is_first'] else 0
        measure_lines = ui.count_view_lines(measure_text, 36) # Relaxed constraint
        factor_lines = ui.count_view_lines(factor_text, 20)  # 위험요인 칼럼은 좁으므로 보수적으로
        
        row_height = max(item['is_first'] * max(step_lines, 1), factor_lines, measure_lines)
        
        if current_height + row_height <= limit:
            current_page.append(item)
            current_height += row_height
        else:
            # Overflow
            remaining_space = limit - current_height
            
            # 1. Try to split to fill remainder of CURRENT page
            split_succcess = False
            if current_height > 0 and remaining_space >= 3.0:
                # Use bullet-aware split for measures
                head_meas, tail_meas = ui.split_measures_by_bullet(measure_text, int(remaining_space), 30)
                # Keep standard split for factors (less critical, allow filling)
                head_fact, tail_fact = ui.split_text_to_fit(factor_text, int(remaining_space), 22)
                
                # Critical Check: If measure text exists but head is empty, it means first bullet didn't fit.
                # In this case, we should NOT split. Move entire row to next page.
                if measure_text and not head_meas:
                     # Force page break (fail split)
                     pass 
                elif head_meas or head_fact:
                    # Success split (at least some measures fit, or factor fit)
                    # Note: if head_meas is valid partial, we proceed.
                    item_head = item.copy()
                    item_head['대책'] = head_meas
                    item_head['위험요인'] = head_fact
                    
                    item_tail = item.copy()
                    item_tail['대책'] = tail_meas if tail_meas else "(대책 내용 계속)"
                    item_tail['위험요인'] = tail_fact if tail_fact else f"{factor_text} (계속)"
                    item_tail['is_first'] = False
                    
                    current_page.append(item_head)
                    pages.append(current_page)
                    current_page = []
                    current_height = 0
                    limit = PAGE_N_CAPACITY
                    
                    queue.insert(0, item_tail)
                    split_succcess = True
                    continue

            # 2. If we couldn't split to fit remainder (or remainder too small), start new page
            if current_height > 0:
                pages.append(current_page)
                current_page = []
                current_height = 0
                limit = PAGE_N_CAPACITY
                # Treat this item as if it's the start of the new page
                queue.insert(0, item)
                continue
            
            # 3. We are on a FRESH page (current_height == 0) but item doesn't fit
            # Force split against the full limit
            head_meas, tail_meas = ui.split_measures_by_bullet(measure_text, int(limit), 30)
            
            # [CRITICAL FIX] If a SINGLE bullet point is larger than the entire page,
            # split_measures_by_bullet returns empty head. We must fallback to arbitrary split.
            if measure_text and not head_meas:
                 head_meas, tail_meas = ui.split_text_to_fit(measure_text, int(limit), 30)

            head_fact, tail_fact = ui.split_text_to_fit(factor_text, int(limit), 22)
            
            if head_meas or head_fact:
                item_head = item.copy()
                item_head['대책'] = head_meas
                item_head['위험요인'] = head_fact
                
                item_tail = item.copy()
                item_tail['대책'] = tail_meas if tail_meas else "(대책 내용 계속)"
                item_tail['위험요인'] = tail_fact if tail_fact else f"{factor_text} (계속)"
                item_tail['is_first'] = False # Tail is always continuation
                
                current_page.append(item_head)
                pages.append(current_page)
                current_page = []
                current_height = 0
                limit = PAGE_N_CAPACITY
                
                queue.insert(0, item_tail)
                continue
            else:
                 # Cannot split even for full page? (e.g. very long word or bug)
                 # Force add to avoid infinite loop
                 current_page.append(item)
                 current_height += row_height
    
    if current_page:
        pages.append(current_page)
        
    # Render Pages
    full_html = ""
    
    # ---------------------------------------------------------
    # [FIX] Print Button via Iframe (avoids Markdown sanitization)
    # ---------------------------------------------------------
    print_btn_html = """
    <html>
    <head>
    <style>
        body { margin: 0; padding: 0; text-align: center; background-color: transparent; }
        .print-btn {
            background-color: #2ecc71; 
            color: white; 
            padding: 12px 24px; 
            border: none; 
            border-radius: 5px; 
            cursor: pointer; 
            font-size: 16px; 
            font-weight: bold; 
            font-family: 'Noto Sans KR', sans-serif;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            transition: all 0.3s ease;
            display: inline-flex;
            align-items: center;
            gap: 8px;
        }
        .print-btn:hover {
            background-color: #27ae60;
            transform: translateY(-2px);
            box-shadow: 0 6px 8px rgba(0,0,0,0.15);
        }
        .desc {
            margin-top: 8px; font-size: 13px; color: #888; font-family: sans-serif;
        }
    </style>
    </head>
    <body>
        <button class="print-btn" onclick="window.parent.print()">
            <span>🖨️ 평가표 PDF 저장 / 인쇄</span>
        </button>
        <div class="desc">💡 팝업창에서 <b>'PDF로 저장'</b>을 선택하세요.</div>
    </body>
    </html>
    """
    st.components.v1.html(print_btn_html, height=100)
    
    # Continue rendering report pages
    # Wrap everything in a printable area for CSS targeting
    full_html += '<div id="printable-area">'
    
    for i, page_items in enumerate(pages):
        # A4 Page Container
        header_text = header_html if i == 0 else f'<div style="text-align:right; font-size:10px; margin-bottom:5px; color:black;">공종별 위험성평가표 ({i+1}/{len(pages)})</div>'
        
        full_html += f"""<div class="a4-page">
{header_text}
<table class="safety-table">
<colgroup>
<col style="width: 10%;">
<col style="width: 25%;">
<col style="width: 50%;">
<col style="width: 5%;">
<col style="width: 5%;">
<col style="width: 5%;">
</colgroup>
<tr>
<th>작업단계</th>
<th>위험요인</th>
<th>위험 제거 및 감소대책</th>
<th>빈도</th>
<th>강도</th>
<th>등급</th>
</tr>"""
        
        from itertools import groupby
        
        # Group items by step_name for rowspan calculation
        step_groups = []
        for key, group in groupby(page_items, key=lambda x: x['step_name']):
            step_groups.append(list(group))
            
        for group in step_groups:
            rowspan = len(group)
            for idx, item in enumerate(group):
                step_cell_html = ""
                if idx == 0:
                    step_display = item['step_name']
                    if not item['is_first']:
                         step_display += " (계속)"
                    step_cell_html = f'<td rowspan="{rowspan}" style="vertical-align: middle; font-weight: bold; background-color: #f9f9f9;">{step_display}</td>'
                
                # Grade Styling
                grade_val = item['등급'].strip()
                grade_display = grade_val
                if "상" in grade_val:
                    grade_display = f'<span style="color:red; font-weight:bold;">{grade_val}</span>'
                elif "중" in grade_val:
                    grade_display = f'<span style="color:#d35400; font-weight:bold;">{grade_val}</span>'
                elif "하" in grade_val:
                    grade_display = f'<span style="color:green; font-weight:bold;">{grade_val}</span>'

                full_html += f"""
<tr>
{step_cell_html}
<td style="text-align:left;">{item['위험요인'].replace(chr(10), '<br>')}</td>
<td style="text-align:left;">{item['대책'].replace(chr(10), '<br>')}</td>
<td>{item['빈도']}</td>
<td>{item['강도']}</td>
<td>{grade_display}</td>
</tr>"""
            
        full_html += """
</table>
</div>"""
        
    full_html += '</div>' # Close printable-area
        
    st.markdown(full_html, unsafe_allow_html=True)
    ui.mark_printable_container()

# 버튼 클릭 후 즉각적인 UI 반영을 위한 리런 로직
if st.session_state.get('needs_rerun', False):
    st.session_state['needs_rerun'] = False
    
    # data_editor가 들고 있는 내부 상태가 남아서 새로고침을 방해하므로, 위젯 상태를 강제로 초기화
    for key in list(st.session_state.keys()):
        if key.startswith("editor_"):
            del st.session_state[key]
            
    st.rerun()
