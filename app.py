import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import io
import requests
import os
import base64

# 💡 [설정] 폰트 및 기본 설정
FONT_FILE = "GmarketSansBold.ttf"
st.set_page_config(page_title="GS25 신선강화점 홍보물 제작소", page_icon="🏪", layout="centered")

# 세션 상태 초기화
if 'bulk_data' not in st.session_state:
    st.session_state['bulk_data'] = []

st.title("🏪✨ 신선강화점 홍보물 제작소")
st.caption("홍보물 제작에서 해방되세요! 🎉")

st.write("---")

tab_single, tab_bulk, tab_preorder = st.tabs(["📱 단일 상품 제작", "💻 엑셀 대량 제작", "🗓️ 단톡방 사전예약"])

# 💡 봇 차단 방지를 위한 브라우저 위장 헤더
@st.cache_data
def get_icon_bytes(url):
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        res = requests.get(url, headers=headers, timeout=5)
        if res.status_code == 200:
            return res.content
        return None
    except:
        return None

def load_icon(url, size):
    icon_bytes = get_icon_bytes(url)
    if icon_bytes:
        try:
            img = Image.open(io.BytesIO(icon_bytes)).convert("RGBA")
            return img.resize(size, Image.LANCZOS)
        except:
            return None
    return None

# --- [공통 함수] 텍스트 스마트 줄바꿈 ---
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

# --- [함수 1] 일반 홍보물 생성 엔진 (가로형) ---
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

        if duration:
            max_date_w, max_date_h = A4_W * 0.25, A4_H * 0.20
            w_date, f_date = fit_text_to_box(duration, FONT_FILE, int(A4_W * 0.04), max_date_w, max_date_h, draw)
            draw.text((margin_right, A4_H * 0.15), w_date, font=f_date, fill=(0, 0, 0), anchor="rm", align="right", spacing=int(f_date.size*0.2))
        
        if event_type != "선택안함":
            promo_filename = f"{event_type}.png"
            if os.path.exists(promo_filename):
                p_img = Image.open(promo_filename).convert("RGBA")
                max_p_w, max_p_h = int(A4_W * 0.55), int(A4_H * 0.26)
                p_ratio = p_img.width / p_img.height
                t_p_h = max_p_h
                t_p_w = int(t_p_h * p_ratio)
                if t_p_w > max_p_w:
                    t_p_w = max_p_w
                    t_p_h = int(t_p_w / p_ratio)
                p_img = p_img.resize((t_p_w, t_p_h), Image.LANCZOS)
                img.paste(p_img, (int((A4_W * 0.5) - (t_p_w / 2)), int((A4_H * 0.28) - t_p_h)), p_img)

        if product_name:
            max_t_w, max_t_h = A4_W * 0.50, A4_H * 0.18 
            w_title, f_title = fit_text_to_box(product_name, FONT_FILE, int(A4_W * 0.055 * USER_TEXT_SCALE), max_t_w, max_t_h, draw, is_title=True)
            draw.text((margin_right, A4_H * 0.61), w_title, font=f_title, fill=(0, 0, 0), anchor="rd", align="right", spacing=int(f_title.size*0.2))
        
        if original_price:
            clean_op = str(original_price).strip()
            if clean_op:
                if not clean_op.endswith("원"): clean_op += "원"
                orig_text = f"정상가 {clean_op}"
                orig_size = int(A4_W * 0.02 * USER_TEXT_SCALE)
                font_orig = ImageFont.truetype(FONT_FILE, orig_size)
                while draw.textlength(orig_text, font=font_orig) > (A4_W * 0.4) and orig_size > 20:
                    orig_size -= 2
                    font_orig = ImageFont.truetype(FONT_FILE, orig_size)
                draw.text((margin_right, A4_H * 0.69), orig_text, font=font_orig, fill=(160, 160, 160), anchor="rm")

        if price:
            clean_p = str(price).strip()
            if clean_p:
                if not clean_p.endswith("원"): clean_p += "원"
                p_size = int(A4_W * 0.14 * USER_TEXT_SCALE)
                f_p = ImageFont.truetype(FONT_FILE, p_size)
                while draw.textlength(clean_p, font=f_p) > (A4_W * 0.45) and p_size > 15:
                    p_size -= 4
                    f_p = ImageFont.truetype(FONT_FILE, p_size)
                draw.text((margin_right, A4_H * 0.82), clean_p, font=f_p, fill=(220, 20, 20), anchor="rm")

        if img_source:
            if isinstance(img_source, str):
                if img_source.startswith("http"):
                    headers = {'User-Agent': 'Mozilla/5.0'}
                    res = requests.get(img_source, headers=headers)
                    p_img = Image.open(io.BytesIO(res.content)).convert("RGBA")
                elif img_source.startswith("data:image"):
                    header, encoded = img_source.split(",", 1)
                    data = base64.b64decode(encoded)
                    p_img = Image.open(io.BytesIO(data)).convert("RGBA")
                else:
                    p_img = Image.open(img_source).convert("RGBA")
            else:
                p_img = Image.open(img_source).convert("RGBA")
                
            m_i_w, m_i_h = int(A4_W * 0.35 * USER_IMG_SCALE), int(A4_H * 0.45 * USER_IMG_SCALE)
            i_w, i_h = p_img.size
            i_ratio = i_w / i_h
            t_w = int(m_i_h * i_ratio)
            t_h = m_i_h
            if t_w > m_i_w:
                t_w = m_i_w
                t_h = int(t_w / i_ratio)
            p_img = p_img.resize((t_w, t_h), Image.LANCZOS)
            img.paste(p_img, (int((A4_W * 0.25) - (t_w / 2)), int((A4_H * 0.65) - (t_h / 2))), p_img)

        return img.convert("RGB")
    except Exception as e:
        return None

# --- [함수 2] 💡 단톡방 사전예약 엔진 (잘림 방지 및 줄바꿈 최적화) ---
def generate_preorder_poster(store_header, product_name, price, pre_period, pickup_date, description, method, img_source):
    try:
        W = 1080
        H_initial = 2500 
        img = Image.new('RGB', (W, H_initial), color=(248, 244, 232)) 
        draw = ImageDraw.Draw(img)

        def wrap_text_centered(text, font, max_w):
            lines = []
            for para in text.split('\n'):
                words = para.split(' ') 
                current_line = ""
                for word in words:
                    test_line = current_line + (" " if current_line else "") + word
                    if draw.textlength(test_line, font=font) <= max_w:
                        current_line = test_line
                    else:
                        if current_line:
                            lines.append(current_line)
                            current_line = word
                        else:
                            char_line = ""
                            for char in word:
                                if draw.textlength(char_line + char, font=font) <= max_w:
                                    char_line += char
                                else:
                                    lines.append(char_line)
                                    char_line = char
                            current_line = char_line
                if current_line:
                    lines.append(current_line)
            return "\n".join(lines)

        header_font = ImageFont.truetype(FONT_FILE, 45)
        draw.text((W/2, 60), store_header, font=header_font, fill=(80, 60, 50), anchor="ma")
        
        line_y = 125
        draw.line([(120, line_y), (W-120, line_y)], fill=(200, 190, 180), width=3) 

        # 1. 상품명
        title_font = ImageFont.truetype(FONT_FILE, 85)
        w_title = wrap_text_centered(product_name, title_font, 950)
        bbox = draw.multiline_textbbox((0,0), w_title, font=title_font, align="center")
        title_h = bbox[3] - bbox[1]
        title_start_y = line_y + 45 
        draw.multiline_text((W/2, title_start_y), w_title, font=title_font, fill=(50, 30, 20), anchor="ma", align="center")

        # 2. 가격 캡슐
        current_y = title_start_y + title_h + 50
        if price:
            clean_p = str(price).strip()
            if clean_p and not clean_p.endswith("원"): clean_p += "원"
            p_size = 80
            price_font = ImageFont.truetype(FONT_FILE, p_size)
            max_text_w = W - 180 
            while draw.textlength(clean_p, font=price_font) > max_text_w and p_size > 40:
                p_size -= 2
                price_font = ImageFont.truetype(FONT_FILE, p_size)
            w_price = wrap_text_centered(clean_p, price_font, max_text_w)
            bbox = draw.multiline_textbbox((0,0), w_price, font=price_font, align="center")
            p_w, p_h = bbox[2] - bbox[0], bbox[3] - bbox[1]
            pad_x, pad_y = 60, 25
            pill_box = [W/2 - p_w/2 - pad_x, current_y, W/2 + p_w/2 + pad_x, current_y + p_h + pad_y*2]
            draw.rounded_rectangle(pill_box, radius=40, fill=(139, 20, 20)) 
            draw.multiline_text((W/2, current_y + pad_y + p_h/2), w_price, font=price_font, fill=(255, 255, 255), anchor="mm", align="center", spacing=15)
            current_y = pill_box[3] + 60
        else:
            current_y += 60

        # 3. 상품 이미지
        img_area_h = 450
        if img_source:
            if isinstance(img_source, str):
                if img_source.startswith("http"):
                    headers = {'User-Agent': 'Mozilla/5.0'}
                    res = requests.get(img_source, headers=headers)
                    p_img = Image.open(io.BytesIO(res.content)).convert("RGBA")
                elif img_source.startswith("data:image"):
                    header, encoded = img_source.split(",", 1)
                    data = base64.b64decode(encoded)
                    p_img = Image.open(io.BytesIO(data)).convert("RGBA")
                else: p_img = Image.open(img_source).convert("RGBA")
            else: p_img = Image.open(img_source).convert("RGBA")
            i_w, i_h = p_img.size
            i_ratio = i_w / i_h
            t_h = img_area_h
            t_w = int(t_h * i_ratio)
            if t_w > 800:
                t_w = 800
                t_h = int(t_w / i_ratio)
            p_img = p_img.resize((t_w, t_h), Image.LANCZOS)
            img.paste(p_img, (int(W/2 - t_w/2), int(current_y + img_area_h/2 - t_h/2)), p_img)

        current_y += img_area_h + 70

        # 4. 예약 기간 & 수령 일자
        date_font = ImageFont.truetype(FONT_FILE, 45)
        text_start_x = 120
        pin_url = "https://raw.githubusercontent.com/twitter/twemoji/master/assets/72x72/1f4cc.png"
        pin_icon = load_icon(pin_url, (45, 45))

        if pre_period:
            if pin_icon: img.paste(pin_icon, (text_start_x, int(current_y - 22)), pin_icon)
            draw.text((text_start_x + 60, current_y), f"사전예약 기간: {pre_period}", font=date_font, fill=(40, 40, 40), anchor="lm")
            current_y += 70
        if pickup_date:
            if pin_icon: img.paste(pin_icon, (text_start_x, int(current_y - 22)), pin_icon)
            draw.text((text_start_x + 60, current_y), f"수령 일자: {pickup_date}", font=date_font, fill=(40, 40, 40), anchor="lm")
            current_y += 70

        # 4.5 상품 설명란
        if description:
            current_y += 30
            desc_font = ImageFont.truetype(FONT_FILE, 40)
            w_desc = wrap_text_centered(description, desc_font, 900)
            bbox_d = draw.multiline_textbbox((0,0), w_desc, font=desc_font, align="center", spacing=15)
            draw.multiline_text((W/2, current_y), w_desc, font=desc_font, fill=(100, 80, 70), anchor="ma", align="center", spacing=15)
            current_y += (bbox_d[3] - bbox_d[1]) + 50

        # 5. 신청 방법 캡슐
        if method:
            current_y += 30
            m_font = ImageFont.truetype(FONT_FILE, 45)
            method_icon = None
            if "카톡" in method or "채팅방" in method:
                icon_url = "https://upload.wikimedia.org/wikipedia/commons/thumb/e/e3/KakaoTalk_logo.svg/120px-KakaoTalk_logo.svg.png"
                method_icon = load_icon(icon_url, (50, 50))
            elif "GS" in method or "어플" in method:
                method_icon = Image.new('RGBA', (50, 50), (0, 0, 0, 0))
                mdraw = ImageDraw.Draw(method_icon)
                mdraw.rounded_rectangle([0, 0, 50, 50], radius=12, fill=(0, 190, 225)) 
                try:
                    gs_f = ImageFont.truetype(FONT_FILE, 24)
                    mdraw.text((25, 25), "GS", font=gs_f, fill=(255, 255, 255), anchor="mm")
                except: pass
            else:
                icon_url = "https://raw.githubusercontent.com/twitter/twemoji/master/assets/72x72/1f3ea.png"
                method_icon = load_icon(icon_url, (50, 50))
            
            m_text = method
            m_w = draw.textlength(m_text, font=m_font)
            icon_space = 65 if method_icon else 0
            total_w = m_w + icon_space
            m_h, pad_x, pad_y = 50, 60, 25
            m_box = [W/2 - total_w/2 - pad_x, current_y, W/2 + total_w/2 + pad_x, current_y + m_h + pad_y*2]
            draw.rounded_rectangle(m_box, radius=35, fill=(255, 255, 255))
            c_y, c_x = current_y + pad_y + m_h/2, W/2 - total_w/2
            if method_icon:
                img.paste(method_icon, (int(c_x), int(c_y - 25)), method_icon)
                draw.text((c_x + icon_space, c_y), m_text, font=m_font, fill=(20, 20, 20), anchor="lm")
            else: 
                draw.text((W/2, c_y), m_text, font=m_font, fill=(20, 20, 20), anchor="mm")
            
            current_y = m_box[3] 
        
        final_h = max(1350, int(current_y + 100)) 
        img = img.crop((0, 0, W, final_h))

        return img.convert("RGB")
    except Exception as e: return None

# --- [탭 1] 단일 상품 제작 ---
with tab_single:
    ev = st.selectbox("행사 종류", ["선택안함", "1+1", "2+1", "혜택가"], key="s_ev")
    du = st.text_area("행사 기간", placeholder="예: 4/1~4/30", height=80, key="s_du")
    pn = st.text_area("상품명", placeholder="예: 삼립)호떡", height=80, key="s_pn")
    col_p1, col_p2 = st.columns(2)
    op = col_p1.text_input("정상가 (선택사항)", key="s_op", placeholder="예: 2,000")
    sp = col_p2.text_input("매가", key="s_sp", placeholder="예: 1,000")
    img_f = st.file_uploader("이미지 업로드", type=["jpg", "png"], key="s_file")
    if st.button("🚀 일반 홍보물 만들기", use_container_width=True):
        res = generate_poster(ev, du, pn, op, sp, img_f)
        if res:
            st.image(res, use_container_width=True)
            buf = io.BytesIO()
            res.save(buf, format="JPEG", quality=90)
            st.download_button("📥 다운로드", buf.getvalue(), "promo.jpg", "image/jpeg", use_container_width=True)
            res.close()

# --- [탭 2] 엑셀 대량 제작 ---
with tab_bulk:
    st.subheader("📁 엑셀 데이터 불러오기")
    st.markdown("""
    엑셀에서 데이터를 복사해서 아래에 붙여넣으세요. **정상가는 비워둬도 작동합니다!**
    * **4열 복사:** [행사번호 | 상품명 | 정상가 (선택사항) | 매가]
    * **3열 복사:** [행사번호 | 상품명 | 매가] (정상가 생략 시)
    """)
    bulk_input = st.text_area("데이터 붙여넣기", placeholder="1\t꿀호떡\t2000\t1000\n3\t삼겹살\t\t7500", height=150)
    global_du = st.text_input("공통 행사 기간", placeholder="예: 4/1 ~ 4/30")

    if st.button("📥 데이터 매칭하기"):
        if bulk_input:
            lines = bulk_input.strip().split('\n')
            new_data = []
            event_map = {"1": "1+1", "2": "2+1", "3": "혜택가"}
            for line in lines:
                parts = line.split('\t') if '\t' in line else line.split()
                if len(parts) >= 3:
                    e_type = event_map.get(parts[0].strip(), "선택안함")
                    name = parts[1].strip()
                    if len(parts) == 3: orig, sale = "", parts[2].strip()
                    else:
                        orig = parts[2].strip() if parts[2].strip() else ""
                        sale = parts[3].strip() if len(parts) > 3 else parts[2].strip()
                    new_data.append({"event": e_type, "name": name, "orig": orig, "sale": sale})
            st.session_state['bulk_data'] = new_data
            for i in range(len(new_data)): st.session_state[f"chk_{i}"] = True

    if st.session_state['bulk_data']:
        st.write("---")
        col_all1, col_all2, _ = st.columns([1, 1, 3])
        if col_all1.button("✅ 전체 선택"):
            for i in range(len(st.session_state['bulk_data'])): st.session_state[f"chk_{i}"] = True
        if col_all2.button("🚫 전체 해제"):
            for i in range(len(st.session_state['bulk_data'])): st.session_state[f"chk_{i}"] = False
        
        selected_indices = []
        for i, item in enumerate(st.session_state['bulk_data']):
            col_sel, col_info = st.columns([0.1, 0.9])
            with col_sel:
                if f"chk_{i}" not in st.session_state: st.session_state[f"chk_{i}"] = True
                if st.checkbox("", key=f"chk_{i}"): selected_indices.append(i)
            
            with col_info.expander(f"🛒 {i+1}. [{item['event']}] {item['name']}", expanded=True):
                c_in, c_pre = st.columns([1, 1.5])
                with c_in:
                    p_text = f"{item['orig']}원 → {item['sale']}원" if item['orig'] else f"{item['sale']}원 (정상가 미기입)"
                    st.write(f"**가격:** {p_text}")
                    b_link = st.text_input("🔗 이미지 주소", key=f"link_{i}")
                    b_file = st.file_uploader("📂 사진 업로드", type=["jpg", "png"], key=f"file_{i}")
                with c_pre:
                    src = b_file if b_file else (b_link if b_link else None)
                    src_sig = f"{b_file.name}_{b_file.size}" if b_file else str(b_link)
                    sig = f"{item['event']}_{item['name']}_{item['orig']}_{item['sale']}_{src_sig}_{global_du}"
                    if item.get('sig') != sig:
                        b_res = generate_poster(item['event'], global_du, item['name'], item['orig'], item['sale'], src)
                        if b_res:
                            buf = io.BytesIO()
                            b_res.save(buf, format="JPEG", quality=85)
                            item['img_bytes'], item['sig'] = buf.getvalue(), sig
                            b_res.close()
                    if 'img_bytes' in item: st.image(item['img_bytes'], use_container_width=True)

        if st.button("📑 선택한 상품 PDF로 한 번에 만들기", use_container_width=True):
            if not selected_indices: st.warning("선택된 상품이 없습니다.")
            else:
                with st.spinner("PDF 생성 중..."):
                    try:
                        img_list = []
                        for idx in selected_indices:
                            if 'img_bytes' in st.session_state['bulk_data'][idx]:
                                img_list.append(Image.open(io.BytesIO(st.session_state['bulk_data'][idx]['img_bytes'])).convert("RGB"))
                        if img_list:
                            pdf_buf = io.BytesIO()
                            img_list[0].save(pdf_buf, format="PDF", save_all=True, append_images=img_list[1:], resolution=300.0)
                            st.download_button("📥 완성된 PDF 다운로드", pdf_buf.getvalue(), "GS25_Promos.pdf", "application/pdf", use_container_width=True)
                    except Exception as e: st.error(f"PDF 생성 오류: {e}")

# --- [탭 3] 단톡방 사전예약 제작 ---
with tab_preorder:
    st.info("💡 단톡방 사전예약 홍보물을 만듭니다. '상품 설명'에 소스 동봉, 완판 소식 등을 자유롭게 적어보세요.")
    
    # 💡 [맞춤 반영] 예시 문구 0000점 복구 완료!
    store_input = st.text_input("🏪 점포명", placeholder="예: 0000점 (미입력 시 기본 문구 추출)", key="pre_store")
    
    if store_input:
        final_header = f"GS25 {store_input} 사전 예약"
    else:
        final_header = "GS25 사전 예약"
    
    pn_pre = st.text_area("상품명", placeholder="예: 한우 냉장 육회 200G", height=80, key="pre_pn")
    price_pre = st.text_input("가격 및 할인 조건", placeholder="예: BC카드 구매 시 18,900원", key="pre_pr")
    
    col1, col2 = st.columns(2)
    period_pre = col1.text_input("사전예약 기간", placeholder="예: 4/24(금) ~ 4/28(화)", key="pre_per")
    pickup_pre = col2.text_input("수령일자", placeholder="예: 4/30(목)", key="pre_pick")
    
    desc_pre = st.text_area("📄 상품 설명 (선택사항)", placeholder="예: 전용 소스 동봉 / 1차 완판 화제 상품! / 수량 한정", height=80, key="pre_desc")
    
    # 💡 [맞춤 반영] 신청 방법 문구 직관적으로 변경 완료!
    method_pre = st.selectbox("신청 방법", ["매장 방문 예약", "우리동네GS 어플 접속 후 사전 예약", "단체 채팅방 카톡 요청"], key="pre_met")
    
    st.write("---")
    img_link_pre = st.text_input("🔗 이미지 주소", key="pre_link")
    img_file_pre = st.file_uploader("📂 사진 업로드", type=["jpg", "png"], key="pre_file")
    
    if st.button("🚀 단톡방용 사전예약 홍보물 만들기", use_container_width=True):
        src_pre = img_file_pre if img_file_pre else (img_link_pre if img_link_pre else None)
        res_pre = generate_preorder_poster(final_header, pn_pre, price_pre, period_pre, pickup_pre, desc_pre, method_pre, src_pre)
        if res_pre:
            st.image(res_pre, use_container_width=True, caption="단톡방 최적화 세로형 디자인")
            buf_pre = io.BytesIO()
            res_pre.save(buf_pre, format="JPEG", quality=100)
            st.download_button("📥 카톡 공유용 이미지 다운로드", buf_pre.getvalue(), "preorder_promo.jpg", "image/jpeg", use_container_width=True)
            res_pre.close()
