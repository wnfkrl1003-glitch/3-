import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import io
import requests
import os
from fpdf import FPDF

# 💡 [설정] 폰트 및 기본 설정
FONT_FILE = "GmarketSansBold.ttf"
st.set_page_config(page_title="GS25 신선강화점 홍보물 제작소", page_icon="🏪", layout="centered")

# 세션 상태 초기화
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

        # 💡 [핵심 기술] 편의점 상품명 특화 스마트 줄바꿈 알고리즘 (유지)
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
                                if char == ' ' or char == ')':
                                    last_break_idx = len(current_line) - 1
                                elif i + 1 < len(paragraph) and paragraph[i+1] == '(':
                                    last_break_idx = len(current_line) - 1
                            i += 1
                        else:
                            if current_line == "":
                                current_line = char
                                lines.append(current_line)
                                current_line = ""
                                i += 1
                            elif is_title and last_break_idx != -1:
                                break_char = current_line[last_break_idx]
                                if break_char == ' ':
                                    lines.append(current_line[:last_break_idx])
                                else:
                                    lines.append(current_line[:last_break_idx+1])
                                current_line = current_line[last_break_idx+1:]
                                last_break_idx = -1 
                            else:
                                lines.append(current_line)
                                current_line = ""
                                last_break_idx = -1
                                
                    if current_line:
                        lines.append(current_line)
                
                wrapped_text = "\n".join(lines)
                bbox = draw_obj.multiline_textbbox((0, 0), wrapped_text, font=font, spacing=int(font_size*0.2))
                if (bbox[3] - bbox[1]) <= max_h:
                    return wrapped_text, font
                font_size -= 2
            return wrapped_text, ImageFont.truetype(font_file, min_size)

        # 1. 행사 기간
        if duration:
            max_date_w, max_date_h = A4_W * 0.25, A4_H * 0.20
            w_date, f_date = fit_text_to_box(duration, FONT_FILE, int(A4_W * 0.04), max_date_w, max_date_h, draw, is_title=False)
            draw.text((margin_right, A4_H * 0.15), w_date, font=f_date, fill=(0, 0, 0), anchor="rm", align="right", spacing=int(f_date.size*0.2))
        
        # 2. 로고 크기 강제 확대/축소
        if event_type != "선택안함":
            promo_filename = f"{event_type}.png"
            if os.path.exists(promo_filename):
                p_img = Image.open(promo_filename).convert("RGBA")
                max_promo_w = int(A4_W * 0.55) 
                max_promo_h = int(A4_H * 0.26) 
                aspect_ratio_promo = p_img.width / p_img.height
                target_promo_h = max_promo_h
                target_promo_w = int(target_promo_h * aspect_ratio_promo)
                if target_promo_w > max_promo_w:
                    target_promo_w = max_promo_w
                    target_promo_h = int(target_promo_w / aspect_ratio_promo)
                p_img = p_img.resize((target_promo_w, target_promo_h), Image.LANCZOS)
                paste_promo_x = int((A4_W * 0.5) - (target_promo_w / 2)) 
                paste_promo_y = int((A4_H * 0.28) - target_promo_h) 
                img.paste(p_img, (paste_promo_x, paste_promo_y), p_img)
            else:
                font_promo_huge = ImageFont.truetype(FONT_FILE, int(A4_W * 0.16)) 
                draw.text((A4_W * 0.5, A4_H * 0.20), event_type, font=font_promo_huge, fill=(30, 100, 200), anchor="mm")

        # 3. 상품명 (스마트 줄바꿈 활성화: is_title=True)
        if product_name:
            max_title_w, max_title_h = A4_W * 0.50, A4_H * 0.18 
            w_title, f_title = fit_text_to_box(product_name, FONT_FILE, int(A4_W * 0.055 * USER_TEXT_SCALE), max_title_w, max_title_h, draw, is_title=True)
            draw.text((margin_right, A4_H * 0.61), w_title, font=f_title, fill=(0, 0, 0), anchor="rd", align="right", spacing=int(f_title.size*0.2))
        
        # 4. 정상가 '원' 자동 추가
        if original_price:
            clean_op = str(original_price).strip()
            if clean_op and not clean_op.endswith("원"):
                clean_op += "원"
            orig_text = f"정상가 {clean_op}"
            orig_size = int(A4_W * 0.02 * USER_TEXT_SCALE)
            font_orig = ImageFont.truetype(FONT_FILE, orig_size)
            while draw.textlength(orig_text, font=font_orig) > (A4_W * 0.4) and orig_size > 20:
                orig_size -= 2
                font_orig = ImageFont.truetype(FONT_FILE, orig_size)
            draw.text((margin_right, A4_H * 0.69), orig_text, font=font_orig, fill=(160, 160, 160), anchor="rm")

        # 5. 매가 (빨간색 가격) '원' 자동 추가
        if price:
            clean_p = str(price).strip()
            if clean_p and not clean_p.endswith("원"):
                clean_p += "원"
            price = clean_p
            p_size, c_size = int(A4_W * 0.14 * USER_TEXT_SCALE), int(A4_W * 0.06 * USER_TEXT_SCALE)
            if any(unit in price for unit in ["캔", "개"]):
                unit = "캔" if "캔" in price else "개"
                parts = price.split(unit, 1)
                count_t, price_t = parts[0] + unit, parts[1].strip()
                f_p, f_c = ImageFont.truetype(FONT_FILE, p_size), ImageFont.truetype(FONT_FILE, c_size)
                while (draw.textlength(price_t, font=f_p) + draw.textlength(count_t, font=f_c)) > (A4_W * 0.45) and p_size > 30:
                    p_size, c_size = p_size - 4, c_size - 2
                    f_p, f_c = ImageFont.truetype(FONT_FILE, p_size), ImageFont.truetype(FONT_FILE, c_size)
                draw.text((margin_right, A4_H * 0.82), price_t, font=f_p, fill=(220, 20, 20), anchor="rm")
                price_w = draw.textlength(price_t, font=f_p)
                draw.text((margin_right - price_w - (A4_W * 0.02), A4_H * 0.82), count_t, font=f_c, fill=(220, 20, 20), anchor="rm")
            else:
                f_p = ImageFont.truetype(FONT_FILE, p_size)
                while draw.textlength(price, font=f_p) > (A4_W * 0.45) and p_size > 30:
                    p_size -= 4
                    f_p = ImageFont.truetype(FONT_FILE, p_size)
                draw.text((margin_right, A4_H * 0.82), price, font=f_p, fill=(220, 20, 20), anchor="rm")

        # 6. 이미지
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

# --- [탭 1] 단일 상품 제작 ---
with tab_single:
    st.info("하나의 상품을 정밀하게 제작할 때 사용하세요.")
    ev = st.selectbox("행사 종류 ", ["선택안함", "1+1", "2+1", "혜택가"], key="s_ev")
    du = st.text_area("행사 기간 ", placeholder="예: 4/1(화) ~ 4/30(목)", height=80, key="s_du")
    pn = st.text_area("상품명 ", placeholder="예: 신선가득꿀호떡", height=80, key="s_pn")
    col_p1, col_p2 = st.columns(2)
    op = col_p1.text_input("정상가", key="s_op")
    sp = col_p2.text_input("행사 매가", key="s_sp")
    
    st.write("---")
    img_link = st.text_input("🔗 이미지 주소 (PC 권장)", key="s_link")
    img_file = st.file_uploader("📂 이미지 업로드 (모바일 권장)", type=["jpg", "png"], key="s_file")
    
    if st.button("🚀 홍보물 만들기", use_container_width=True):
        final_src = img_file if img_file else (img_link if img_link else None)
        result = generate_poster(ev, du, pn, op, sp, final_src)
        if result:
            st.image(result, use_container_width=True)
            buf = io.BytesIO()
            result.save(buf, format="JPEG", quality=100)
            st.download_button("📥 고화질 다운로드", buf.getvalue(), "promo.jpg", "image/jpeg", use_container_width=True)

# --- [탭 2] 엑셀로 한 번에 만들기 ---
with tab_bulk:
    st.subheader("📁 엑셀 데이터 불러오기")
    st.markdown("""
    엑셀에서 **[행사번호 | 상품명 | 정상가 | 매가]** 4개 열을 복사해서 붙여넣으세요.
    * **1**: 1+1 / **2**: 2+1 / **3**: 혜택가
    """)
    bulk_input = st.text_area("데이터 붙여넣기", placeholder="1 신선가득꿀호떡 2000 1000\n2 혜자도시락 5000 4500", height=150)
    
    global_du = st.text_input("공통 행사 기간", placeholder="예: 4/1 ~ 4/30")

    if st.button("📥 데이터 매칭하기"):
        if bulk_input:
            lines = bulk_input.strip().split('\n')
            new_data = []
            event_map = {"1": "1+1", "2": "2+1", "3": "혜택가"}
            for line in lines:
                parts = line.split()
                if len(parts) >= 4:
                    e_type = event_map.get(parts[0], "선택안함")
                    new_data.append({
                        "event": e_type,
                        "name": parts[1],
                        "orig": parts[2],
                        "sale": parts[3]
                    })
            st.session_state['bulk_data'] = new_data
            st.success(f"총 {len(new_data)}개의 상품 정보를 행사 종류와 함께 불러왔습니다.")

    # 💡 [핵심] 체크박스 + 개별 사진 입력 + PDF 일괄 저장
    if st.session_state['bulk_data']:
        st.write("---")
        st.info("💡 PDF로 합칠 상품만 왼쪽 체크박스를 선택하세요. (개별 저장도 가능합니다)")
        
        selected_indices = []
        for i, item in enumerate(st.session_state['bulk_data']):
            # 체크박스와 아코디언(Expander)을 나란히 배치
            col_sel, col_info = st.columns([0.1, 0.9])
            
            with col_sel:
                st.write("") # 높이 조절용 여백
                is_checked = st.checkbox("", value=True, key=f"chk_{i}")
                if is_checked:
                    selected_indices.append(i)
            
            with col_info.expander(f"🛒 {i+1}. [{item['event']}] {item['name']}", expanded=True):
                c1, c2 = st.columns([1, 1.5])
                with c1:
                    st.write(f"**가격:** {item['orig']}원 → {item['sale']}원")
                    b_link = st.text_input("🔗 이미지 주소", key=f"link_{i}")
                    b_file = st.file_uploader("📂 사진 업로드", type=["jpg", "png"], key=f"file_{i}")
                
                with c2:
                    current_src = b_file if b_file else (b_link if b_link else None)
                    b_res = generate_poster(item['event'], global_du, item['name'], item['orig'], item['sale'], current_src)
                    if b_res:
                        st.image(b_res, use_container_width=True)
                        st.session_state['bulk_data'][i]['img_obj'] = b_res # PDF용 이미지 저장
                        # 개별 다운로드 버튼 (선택 사항)
                        buf_single = io.BytesIO()
                        b_res.save(buf_single, format="JPEG", quality=100)
                        st.download_button(f"📥 {i+1}번만 개별 저장", buf_single.getvalue(), f"promo_{i}.jpg", "image/jpeg", use_container_width=True)

        st.write("---")
        # PDF 일괄 다운로드 버튼
        if st.button("📑 선택한 상품(체크된 항목) PDF로 한 번에 만들기", use_container_width=True):
            if not selected_indices:
                st.warning("선택된 상품이 없습니다. 왼쪽 체크박스를 확인해주세요.")
            else:
                with st.spinner("PDF 문서를 굽는 중입니다..."):
                    pdf = FPDF(orientation='L', unit='mm', format='A4')
                    for idx in selected_indices:
                        if 'img_obj' in st.session_state['bulk_data'][idx]:
                            poster = st.session_state['bulk_data'][idx]['img_obj']
                            pdf.add_page()
                            img_byte_arr = io.BytesIO()
                            poster.save(img_byte_arr, format='JPEG')
                            pdf.image(img_byte_arr, x=0, y=0, w=297, h=210)
                    
                    pdf_output = pdf.output(dest='S').encode('latin-1')
                    st.download_button("📥 완성된 PDF 다운로드 (인쇄용)", pdf_output, "GS25_Promos.pdf", "application/pdf", use_container_width=True)
