import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import io
import requests
import os
from fpdf import FPDF

# 💡 [설정] 폰트 및 기본 설정
FONT_FILE = "GmarketSansBold.ttf"
st.set_page_config(page_title="GS25 신선강화점 홍보물 제작소", page_icon="🏪", layout="centered")

if 'bulk_data' not in st.session_state:
    st.session_state['bulk_data'] = []

st.title("🏪✨ 신선강화점 홍보물 제작소")
st.caption("홍보물 제작에서 해방되세요! 🎉")

st.write("---")

tab_single, tab_bulk = st.tabs(["📱 단일 상품 제작", "💻 엑셀로 한 번에 만들기"])

# --- [함수] 홍보물 생성 엔진 ---
def generate_poster(event_type, duration, product_name, original_price, price, img_source):
    try:
        A4_W, A4_H = 3508, 2480 
        img = Image.open("template.jpg").convert("RGBA")
        img = img.resize((A4_W, A4_H)) 
        draw = ImageDraw.Draw(img)
        
        USER_MARGIN_PX = 72      
        USER_IMG_SCALE = 1.1     
        USER_TEXT_SCALE = 1.6    
        margin_right = A4_W - USER_MARGIN_PX 

        def fit_text_to_box(text, font_file, max_size, max_w, max_h, draw_obj, is_title=False):
            font_size = max_size
            min_size = 15
            while font_size >= min_size:
                font = ImageFont.truetype(font_file, font_size)
                lines = []
                for paragraph in text.split('\n'):
                    current_line = ""
                    last_break_idx = -1
                    i = 0
                    while i < len(paragraph):
                        char = paragraph[i]
                        test_line = current_line + char
                        if draw_obj.textlength(test_line, font=font) <= max_w:
                            current_line = test_line
                            if is_title:
                                if char in [' ', ')']: last_break_idx = len(current_line) - 1
                                elif i + 1 < len(paragraph) and paragraph[i+1] == '(': last_break_idx = len(current_line) - 1
                            i += 1
                        else:
                            if current_line == "":
                                current_line = char
                                lines.append(current_line)
                                current_line = ""
                                i += 1
                            elif is_title and last_break_idx != -1:
                                lines.append(current_line[:last_break_idx+1])
                                current_line = current_line[last_break_idx+1:]
                                last_break_idx = -1
                            else:
                                lines.append(current_line)
                                current_line = ""
                    if current_line: lines.append(current_line)
                wrapped_text = "\n".join(lines)
                bbox = draw_obj.multiline_textbbox((0, 0), wrapped_text, font=font, spacing=int(font_size*0.2))
                if (bbox[3] - bbox[1]) <= max_h: return wrapped_text, font
                font_size -= 2
            return wrapped_text, ImageFont.truetype(font_file, min_size)

        if duration:
            max_date_w, max_date_h = A4_W * 0.25, A4_H * 0.20
            w_date, f_date = fit_text_to_box(duration, FONT_FILE, int(A4_W * 0.04), max_date_w, max_date_h, draw)
            draw.text((margin_right, A4_H * 0.15), w_date, font=f_date, fill=(0, 0, 0), anchor="rm", align="right")
        
        if event_type != "선택안함":
            promo_filename = f"{event_type}.png"
            if os.path.exists(promo_filename):
                p_img = Image.open(promo_filename).convert("RGBA")
                p_img.thumbnail((int(A4_W * 0.55), int(A4_H * 0.26)), Image.LANCZOS)
                img.paste(p_img, (int((A4_W * 0.5) - (p_img.width / 2)), int((A4_H * 0.28) - p_img.height)), p_img)

        if product_name:
            max_title_w, max_title_h = A4_W * 0.50, A4_H * 0.18 
            w_title, f_title = fit_text_to_box(product_name, FONT_FILE, int(A4_W * 0.055 * USER_TEXT_SCALE), max_title_w, max_title_h, draw, is_title=True)
            draw.text((margin_right, A4_H * 0.61), w_title, font=f_title, fill=(0, 0, 0), anchor="rd", align="right")
        
        if original_price:
            clean_op = str(original_price).strip()
            if not clean_op.endswith("원"): clean_op += "원"
            orig_text = f"정상가 {clean_op}"
            orig_size = int(A4_W * 0.02 * USER_TEXT_SCALE)
            font_orig = ImageFont.truetype(FONT_FILE, orig_size)
            draw.text((margin_right, A4_H * 0.69), orig_text, font=font_orig, fill=(160, 160, 160), anchor="rm")

        if price:
            clean_p = str(price).strip()
            if not clean_p.endswith("원"): clean_p += "원"
            p_size, c_size = int(A4_W * 0.14 * USER_TEXT_SCALE), int(A4_W * 0.06 * USER_TEXT_SCALE)
            f_p = ImageFont.truetype(FONT_FILE, p_size)
            draw.text((margin_right, A4_H * 0.82), clean_p, font=f_p, fill=(220, 20, 20), anchor="rm")

        if img_source:
            if isinstance(img_source, str) and img_source.startswith("http"):
                res = requests.get(img_source)
                p_img = Image.open(io.BytesIO(res.content)).convert("RGBA")
            else:
                p_img = Image.open(img_source).convert("RGBA")
            p_img.thumbnail((int(A4_W * 0.35 * USER_IMG_SCALE), int(A4_H * 0.45 * USER_IMG_SCALE)), Image.LANCZOS)
            img.paste(p_img, (int((A4_W * 0.25) - (p_img.width / 2)), int((A4_H * 0.65) - (p_img.height / 2))), p_img)

        return img.convert("RGB")
    except Exception as e:
        return None

# --- [탭 1] 단일 제작 ---
with tab_single:
    st.info("하나의 상품을 제작합니다.")
    ev = st.selectbox("행사 종류", ["선택안함", "1+1", "2+1", "혜택가"], key="s_ev")
    du = st.text_area("행사 기간", placeholder="예: 4/1~4/30", key="s_du")
    pn = st.text_area("상품명", placeholder="예: 신선가득꿀호떡", key="s_pn")
    op = st.text_input("정상가", key="s_op")
    sp = st.text_input("매가", key="s_sp")
    img_f = st.file_uploader("이미지 업로드", type=["jpg", "png"], key="s_file")
    
    if st.button("🚀 홍보물 만들기", use_container_width=True):
        res = generate_poster(ev, du, pn, op, sp, img_f)
        if res:
            st.image(res, use_container_width=True)
            buf = io.BytesIO()
            res.save(buf, format="JPEG")
            st.download_button("📥 다운로드", buf.getvalue(), "promo.jpg", use_container_width=True)

# --- [탭 2] 엑셀/대량 제작 ---
with tab_bulk:
    st.subheader("📁 엑셀 데이터 불러오기")
    bulk_input = st.text_area("데이터 붙여넣기 [행사번호 | 상품명 | 정상가 | 매가]", height=150)
    global_du = st.text_input("공통 행사 기간", placeholder="예: 4/1 ~ 4/30")

    if st.button("📥 데이터 매칭하기"):
        if bulk_input:
            lines = bulk_input.strip().split('\n')
            new_data = []
            event_map = {"1": "1+1", "2": "2+1", "3": "혜택가"}
            for line in lines:
                parts = line.split()
                if len(parts) >= 4:
                    new_data.append({"event": event_map.get(parts[0], "선택안함"), "name": parts[1], "orig": parts[2], "sale": parts[3], "selected": True})
            st.session_state['bulk_data'] = new_data

    # 💡 [핵심] 체크박스 및 PDF 생성 로직
    if st.session_state['bulk_data']:
        st.write("---")
        st.info("PDF로 만들고 싶은 상품만 체크하세요.")
        
        selected_indices = []
        for i, item in enumerate(st.session_state['bulk_data']):
            col_check, col_content = st.columns([0.1, 0.9])
            # 개별 체크박스
            is_selected = col_check.checkbox("", value=True, key=f"check_{i}")
            if is_selected:
                selected_indices.append(i)
                
            with col_content.expander(f"{i+1}. [{item['event']}] {item['name']}"):
                c1, c2 = st.columns([1, 1.5])
                with c1:
                    b_link = st.text_input("🔗 이미지 주소", key=f"link_{i}")
                    b_file = st.file_uploader("📂 사진 업로드", type=["jpg", "png"], key=f"file_{i}")
                with c2:
                    curr_src = b_file if b_file else (b_link if b_link else None)
                    b_res = generate_poster(item['event'], global_du, item['name'], item['orig'], item['sale'], curr_src)
                    if b_res:
                        st.image(b_res, use_container_width=True)
                        st.session_state['bulk_data'][i]['img'] = b_res # PDF용 이미지 저장

        # 💡 [핵심] 선택한 상품만 PDF로 묶어서 다운로드
        if st.button("📥 선택한 상품 PDF로 한 번에 만들기", use_container_width=True):
            if not selected_indices:
                st.warning("선택된 상품이 없습니다.")
            else:
                with st.spinner("PDF 문서를 생성 중입니다..."):
                    pdf = FPDF(orientation='L', unit='mm', format='A4')
                    for idx in selected_indices:
                        if 'img' in st.session_state['bulk_data'][idx]:
                            poster = st.session_state['bulk_data'][idx]['img']
                            pdf.add_page()
                            # PIL 이미지를 바이트로 변환하여 PDF에 삽입
                            img_byte_arr = io.BytesIO()
                            poster.save(img_byte_arr, format='JPEG')
                            pdf.image(img_byte_arr, x=0, y=0, w=297, h=210)
                    
                    pdf_output = pdf.output(dest='S').encode('latin-1')
                    st.download_button("📥 완성된 PDF 다운로드", pdf_output, "GS25_Promos.pdf", "application/pdf", use_container_width=True)
                    st.success("PDF 생성이 완료되었습니다!")
