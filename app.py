import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import io
import requests
import os
import pandas as pd

# 💡 [설정] 폰트 및 기본 설정
FONT_FILE = "GmarketSansBold.ttf"
st.set_page_config(page_title="GS25 신선강화점 홍보물 제작소", page_icon="🏪", layout="centered")

# 세션 상태 초기화 (불러온 엑셀 데이터를 저장)
if 'bulk_data' not in st.session_state:
    st.session_state['bulk_data'] = []

st.title("🏪✨ 신선강화점 홍보물 제작소")
st.caption("홍보물 제작에서 해방되세요! 🎉")

st.write("---")

# 💡 [핵심] 탭 기능으로 단일 입력과 엑셀 입력을 분리
tab_single, tab_bulk = st.tabs(["📱 단일 상품 제작", "💻 엑셀로 한 번에 만들기"])

# --- [함수] 홍보물 생성 엔진 (기존의 완벽 방어 레이아웃 유지) ---
def generate_poster(event_type, duration, product_name, original_price, price, img_source):
    try:
        A4_W, A4_H = 3508, 2480 
        img = Image.open("template.jpg").convert("RGBA")
        img = img.resize((A4_W, A4_H)) 
        draw = ImageDraw.Draw(img)
        
        USER_MARGIN_PX = 72      
        USER_IMG_SCALE = 1.1     
        USER_TEXT_SCALE = 1.6    # 겹침 방지 황금 비율
        margin_right = A4_W - USER_MARGIN_PX 
        max_text_width = A4_W * 0.50 

        # 1. 행사 기간
        if duration:
            date_size = int(A4_W * 0.04)
            font_date = ImageFont.truetype(FONT_FILE, date_size)
            max_date_w = A4_W * 0.25 
            lines_date = duration.split('\n')
            max_line_w_date = max([draw.textlength(line, font=font_date) for line in lines_date])
            while max_line_w_date > max_date_w and date_size > 20:
                date_size -= 2
                font_date = ImageFont.truetype(FONT_FILE, date_size)
                max_line_w_date = max([draw.textlength(line, font=font_date) for line in lines_date])
            draw.text((margin_right, A4_H * 0.15), duration, font=font_date, fill=(0, 0, 0), anchor="rm", align="right", spacing=int(font_date.size*0.2))
        
        # 2. 로고
        if event_type != "선택안함":
            promo_filename = f"{event_type}.png"
            if os.path.exists(promo_filename):
                p_img = Image.open(promo_filename).convert("RGBA")
                p_img.thumbnail((int(A4_W * 0.55), int(A4_H * 0.26)), Image.LANCZOS)
                img.paste(p_img, (int((A4_W * 0.5) - (p_img.width / 2)), int((A4_H * 0.28) - p_img.height)), p_img)

        # 3. 상품명 (Bottom-up 정렬)
        if product_name:
            title_size = int(A4_W * 0.055 * USER_TEXT_SCALE)
            font_title = ImageFont.truetype(FONT_FILE, title_size)
            lines_title = product_name.split('\n')
            max_line_w_title = max([draw.textlength(line, font=font_title) for line in lines_title])
            while max_line_w_title > max_text_width and title_size > 25:
                title_size -= 2
                font_title = ImageFont.truetype(FONT_FILE, title_size)
                max_line_w_title = max([draw.textlength(line, font=font_title) for line in lines_title])
            draw.text((margin_right, A4_H * 0.60), product_name, font=font_title, fill=(0, 0, 0), anchor="rd", align="right", spacing=int(font_title.size*0.2))
        
        # 4. 정상가
        if original_price:
            orig_text = f"정상가 {original_price}"
            orig_size = int(A4_W * 0.02 * USER_TEXT_SCALE)
            font_orig = ImageFont.truetype(FONT_FILE, orig_size)
            while draw.textlength(orig_text, font=font_orig) > (A4_W * 0.4) and orig_size > 20:
                orig_size -= 2
                font_orig = ImageFont.truetype(FONT_FILE, orig_size)
            draw.text((margin_right, A4_H * 0.68), orig_text, font=font_orig, fill=(160, 160, 160), anchor="rm")

        # 5. 매가 (빨간색 가격)
        if price:
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
                draw.text((margin_right - draw.textlength(price_t, font=f_p) - (A4_W * 0.02), A4_H * 0.82), count_t, font=f_c, fill=(220, 20, 20), anchor="rm")
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
    st.markdown("엑셀에서 **[상품명 | 정상가 | 매가]** 3개 열을 복사해서 아래에 붙여넣으세요.")
    bulk_input = st.text_area("데이터 붙여넣기", placeholder="아메리카노 2000 1000\n꿀호떡 4500 4000", height=150)
    
    global_ev = st.selectbox("공통 행사 종류", ["선택안함", "1+1", "2+1", "혜택가"])
    global_du = st.text_input("공통 행사 기간", placeholder="예: 4/1 ~ 4/30")

    if st.button("📥 데이터 매칭하기"):
        if bulk_input:
            lines = bulk_input.strip().split('\n')
            new_data = []
            for line in lines:
                parts = line.split()
                if len(parts) >= 3:
                    new_data.append({"name": parts[0], "orig": parts[1], "sale": parts[2]})
            st.session_state['bulk_data'] = new_data
            st.success(f"총 {len(new_data)}개의 상품을 불러왔습니다. 아래에서 사진을 추가하세요!")

    # 불러온 데이터가 있다면 개별 편집 카드 생성
    if st.session_state['bulk_data']:
        st.write("---")
        for i, item in enumerate(st.session_state['bulk_data']):
            with st.expander(f"🛒 {i+1}. {item['name']} - 사진 넣기 및 제작", expanded=True):
                c1, c2 = st.columns([1, 1.5])
                with c1:
                    st.write(f"**상품명:** {item['name']}")
                    st.write(f"**가격:** {item['orig']} → {item['sale']}")
                    b_link = st.text_input("🔗 이미지 주소", key=f"link_{i}")
                    b_file = st.file_uploader("📂 사진 업로드", type=["jpg", "png"], key=f"file_{i}")
                
                with c2:
                    current_src = b_file if b_file else (b_link if b_link else None)
                    b_res = generate_poster(global_ev, global_du, item['name'], item['orig'], item['sale'], current_src)
                    if b_res:
                        st.image(b_res, use_container_width=True)
                        buf = io.BytesIO()
                        b_res.save(buf, format="JPEG", quality=100)
                        st.download_button(f"📥 {i+1}번 다운로드", buf.getvalue(), f"promo_{i}.jpg", "image/jpeg", use_container_width=True)
