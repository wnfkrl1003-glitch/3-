import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import io
import requests
import os
import base64
import streamlit.components.v1 as components
from datetime import datetime, date

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

def format_date_range(start_date, end_date):
    weekdays = ["월", "화", "수", "목", "금", "토", "일"]
    s_f = f"{start_date.month}/{start_date.day}({weekdays[start_date.weekday()]})"
    e_f = f"{end_date.month}/{end_date.day}({weekdays[end_date.weekday()]})"
    return f"{s_f} ~ {e_f}"

def format_single_date(target_date):
    weekdays = ["월", "화", "수", "목", "금", "토", "일"]
    return f"{target_date.month}/{target_date.day}({weekdays[target_date.weekday()]})"

@st.cache_data
def get_icon_bytes(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        res = requests.get(url, headers=headers, timeout=5)
        if res.status_code == 200: return res.content
        return None
    except: return None

def load_icon(url, size):
    icon_bytes = get_icon_bytes(url)
    if icon_bytes:
        try:
            img = Image.open(io.BytesIO(icon_bytes)).convert("RGBA")
            return img.resize(size, Image.LANCZOS)
        except: return None
    return None

# 💡 [핵심 엔진] 괄호 유령 방지 및 의미 단위 스마트 줄바꿈
def wrap_text_safe(text, font, max_w, draw_obj):
    lines = []
    # 혼자 떨어지면 안 되는 금칙어 리스트
    prohibited_start = [')', ']', '}', '원', '개', '캔', 'g', 'G', 'ml', 'ML', '입', 'L', 'l', '%', ',', '.']
    for para in text.split('\n'):
        words = para.split(' ')
        current_line = ""
        for word in words:
            test_line = current_line + (" " if current_line else "") + word
            if draw_obj.textlength(test_line, font=font) <= max_w:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line)
                    current_line = word
                else:
                    char_line = ""
                    j = 0
                    while j < len(word):
                        char = word[j]
                        if draw_obj.textlength(char_line + char, font=font) <= max_w:
                            char_line += char
                            j += 1
                        else:
                            # [금칙어 보호 1] 잘리는 글자가 괄호나 단위면 앞 글자를 데리고 다음 줄로 갑니다.
                            if char in prohibited_start and len(char_line) > 0:
                                pushed_char = char_line[-1]
                                lines.append(char_line[:-1])
                                char_line = pushed_char + char
                                j += 1
                            # [금칙어 보호 2] 앞 글자가 여는 괄호면 괄호를 통째로 다음 줄로 데리고 갑니다.
                            elif len(char_line) > 0 and char_line[-1] in ['(', '[']:
                                lines.append(char_line[:-1])
                                char_line = char_line[-1] + char
                                j += 1
                            else:
                                lines.append(char_line)
                                char_line = char
                                j += 1
                    current_line = char_line
        if current_line:
            lines.append(current_line)
    return "\n".join(lines)

def fit_text_to_box(text, font_file, max_size, max_w, max_h, draw_obj):
    font_size = max_size
    min_size = 15
    while font_size >= min_size:
        font = ImageFont.truetype(font_file, font_size)
        wrapped_text = wrap_text_safe(text, font, max_w, draw_obj)
        bbox = draw_obj.multiline_textbbox((0, 0), wrapped_text, font=font, spacing=int(font_size*0.2))
        
        lines = wrapped_text.split('\n')
        actual_max_w = max([draw_obj.textlength(line, font=font) for line in lines]) if lines else 0
        
        if (bbox[3] - bbox[1]) <= max_h and actual_max_w <= max_w:
            return wrapped_text, font
        font_size -= 2
    font = ImageFont.truetype(font_file, min_size)
    return wrap_text_safe(text, font, max_w, draw_obj), font

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

        # 💡 [날짜 개선] 기간이 길면 ~ 를 기준으로 깔끔하게 두 줄로 강제 배치
        if duration:
            if "~" in duration and "\n" not in duration:
                duration = duration.replace("~", "~\n")
            max_date_w, max_date_h = A4_W * 0.22, A4_H * 0.20
            w_date, f_date = fit_text_to_box(duration, FONT_FILE, int(A4_W * 0.035), max_date_w, max_date_h, draw)
            draw.multiline_text((margin_right, A4_H * 0.15), w_date, font=f_date, fill=(0, 0, 0), anchor="rm", align="right", spacing=int(f_date.size*0.2))
        
        # 💡 [로고 개선] 로고 크기를 살짝 줄이고 좌측으로 당겨 날짜와의 겹침 원천 차단
        if event_type != "선택안함":
            promo_filename = f"{event_type}.png"
            if os.path.exists(promo_filename):
                p_img = Image.open(promo_filename).convert("RGBA")
                max_p_w, max_p_h = int(A4_W * 0.45), int(A4_H * 0.22)
                p_ratio = p_img.width / p_img.height
                t_p_h = max_p_h
                t_p_w = int(t_p_h * p_ratio)
                if t_p_w > max_p_w:
                    t_p_w = max_p_w
                    t_p_h = int(t_p_w / p_ratio)
                p_img = p_img.resize((t_p_w, t_p_h), Image.LANCZOS)
                # 중심을 40% 지점으로 이동
                img.paste(p_img, (int((A4_W * 0.40) - (t_p_w / 2)), int((A4_H * 0.28) - t_p_h)), p_img)

        # 상품명 (의미 단위 줄바꿈 적용 & multiline_text 사용)
        if product_name:
            max_t_w, max_t_h = A4_W * 0.45, A4_H * 0.18 
            w_title, f_title = fit_text_to_box(product_name, FONT_FILE, int(A4_W * 0.055 * USER_TEXT_SCALE), max_t_w, max_t_h, draw)
            draw.multiline_text((margin_right, A4_H * 0.61), w_title, font=f_title, fill=(0, 0, 0), anchor="rd", align="right", spacing=int(f_title.size*0.2))
        
        if original_price:
            clean_op = str(original_price).strip()
            if clean_op:
                if not clean_op.endswith("원"): clean_op += "원"
                orig_text = f"정상가 {clean_op}"
                orig_size = int(A4_W * 0.02 * USER_TEXT_SCALE)
                font_orig = ImageFont.truetype(FONT_FILE, orig_size)
                while draw.textlength(orig_text, font=font_orig) > (A4_W * 0.45) and orig_size > 20:
                    orig_size -= 2
                    font_orig = ImageFont.truetype(FONT_FILE, orig_size)
                draw.text((margin_right, A4_H * 0.69), orig_text, font=font_orig, fill=(160, 160, 160), anchor="rm")

        if price:
            clean_p = str(price).strip()
            if clean_p:
                if not clean_p.endswith("원"): clean_p += "원"
                p_size = int(A4_W * 0.14 * USER_TEXT_SCALE)
                c_size = int(A4_W * 0.06 * USER_TEXT_SCALE)
                
                if any(unit in clean_p for unit in ["캔", "개"]):
                    unit = "캔" if "캔" in clean_p else "개"
                    parts = clean_p.split(unit, 1)
                    count_t = parts[0] + unit
                    price_t = parts[1].strip()
                    
                    f_p = ImageFont.truetype(FONT_FILE, p_size)
                    f_c = ImageFont.truetype(FONT_FILE, c_size)
                    
                    while (draw.textlength(price_t, font=f_p) + draw.textlength(count_t, font=f_c)) > (A4_W * 0.45) and p_size > 30:
                        p_size -= 4
                        c_size -= 2
                        f_p = ImageFont.truetype(FONT_FILE, p_size)
                        f_c = ImageFont.truetype(FONT_FILE, c_size)
                        
                    draw.text((margin_right, A4_H * 0.82), price_t, font=f_p, fill=(220, 20, 20), anchor="rm")
                    price_w = draw.textlength(price_t, font=f_p)
                    draw.text((margin_right - price_w - (A4_W * 0.02), A4_H * 0.82), count_t, font=f_c, fill=(220, 20, 20), anchor="rm")
                else:
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
                else: p_img = Image.open(img_source).convert("RGBA")
            else: p_img = Image.open(img_source).convert("RGBA")
            m_i_w, m_i_h = int(A4_W * 0.35 * USER_IMG_SCALE), int(A4_H * 0.45 * USER_IMG_SCALE)
            i_w, i_h = p_img.size
            i_ratio = i_w / i_h
            t_w, t_h = int(m_i_h * i_ratio), m_i_h
            if t_w > m_i_w: t_w, t_h = m_i_w, int(t_w / i_ratio)
            p_img = p_img.resize((t_w, t_h), Image.LANCZOS)
            img.paste(p_img, (int((A4_W * 0.25) - (t_w / 2)), int((A4_H * 0.65) - (t_h / 2))), p_img)
        return img.convert("RGB")
    except Exception as e: return None

# --- [함수 2] 단톡방 사전예약 엔진 ---
def generate_preorder_poster(store_header, product_name, price, pre_period, pickup_date, description, method, img_source):
    try:
        W, H_initial = 1080, 2500 
        img = Image.new('RGB', (W, H_initial), color=(248, 244, 232)) 
        draw = ImageDraw.Draw(img)

        header_font = ImageFont.truetype(FONT_FILE, 45)
        draw.text((W/2, 60), store_header, font=header_font, fill=(80, 60, 50), anchor="ma")
        line_y = 125
        draw.line([(120, line_y), (W-120, line_y)], fill=(200, 190, 180), width=3) 

        title_font = ImageFont.truetype(FONT_FILE, 85)
        w_title = wrap_text_safe(product_name, title_font, 950, draw)
        bbox = draw.multiline_textbbox((0,0), w_title, font=title_font, align="center")
        title_h = bbox[3] - bbox[1]
        t_y = line_y + 45 
        draw.multiline_text((W/2, t_y), w_title, font=title_font, fill=(50, 30, 20), anchor="ma", align="center")

        cur_y = t_y + title_h + 50
        if price:
            clean_p = str(price).strip()
            if not clean_p.endswith("원"): clean_p += "원"
            p_size = 80
            p_f = ImageFont.truetype(FONT_FILE, p_size)
            max_p_w = W - 180 
            while draw.textlength(clean_p, font=p_f) > max_p_w and p_size > 40:
                p_size -= 2
                p_f = ImageFont.truetype(FONT_FILE, p_size)
            w_p = wrap_text_safe(clean_p, p_f, max_p_w, draw)
            bbox_p = draw.multiline_textbbox((0,0), w_p, font=p_f, align="center")
            p_w, p_h = bbox_p[2] - bbox_p[0], bbox_p[3] - bbox_p[1]
            pad_x, pad_y = 60, 25
            pill = [W/2 - p_w/2 - pad_x, cur_y, W/2 + p_w/2 + pad_x, cur_y + p_h + pad_y*2]
            draw.rounded_rectangle(pill, radius=40, fill=(139, 20, 20)) 
            draw.multiline_text((W/2, cur_y + pad_y + p_h/2), w_p, font=p_f, fill=(255, 255, 255), anchor="mm", align="center", spacing=15)
            cur_y = pill[3] + 60
        else: cur_y += 60

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
            t_h, t_w = img_area_h, int(img_area_h * i_ratio)
            if t_w > 800: t_w, t_h = 800, int(800 / i_ratio)
            p_img = p_img.resize((t_w, t_h), Image.LANCZOS)
            img.paste(p_img, (int(W/2 - t_w/2), int(cur_y + img_area_h/2 - t_h/2)), p_img)

        cur_y += img_area_h + 70
        d_f = ImageFont.truetype(FONT_FILE, 45)
        pin_url = "https://raw.githubusercontent.com/twitter/twemoji/master/assets/72x72/1f4cc.png"
        pin_icon = load_icon(pin_url, (45, 45))

        if pre_period:
            if pin_icon: img.paste(pin_icon, (120, int(cur_y - 22)), pin_icon)
            draw.text((180, cur_y), f"사전예약 기간: {pre_period}", font=d_f, fill=(40, 40, 40), anchor="lm")
            cur_y += 70
        if pickup_date:
            if pin_icon: img.paste(pin_icon, (120, int(cur_y - 22)), pin_icon)
            draw.text((180, cur_y), f"수령 일자: {pickup_date}", font=d_f, fill=(40, 40, 40), anchor="lm")
            cur_y += 70

        if description:
            cur_y += 30
            desc_font = ImageFont.truetype(FONT_FILE, 40)
            w_desc = wrap_text_safe(description, desc_font, 900, draw)
            bbox_d = draw.multiline_textbbox((0,0), w_desc, font=desc_font, align="center", spacing=15)
            draw.multiline_text((W/2, cur_y), w_desc, font=desc_font, fill=(100, 80, 70), anchor="ma", align="center", spacing=15)
            cur_y += (bbox_d[3] - bbox_d[1]) + 50

        if method:
            cur_y += 30
            m_f = ImageFont.truetype(FONT_FILE, 45)
            method_icon = None
            if "카톡" in method or "채팅방" in method:
                icon_url = "https://upload.wikimedia.org/wikipedia/commons/thumb/e/e3/KakaoTalk_logo.svg/120px-KakaoTalk_logo.svg.png"
                method_icon = load_icon(icon_url, (50, 50))
            elif "GS" in method or "어플" in method:
                method_icon = Image.new('RGBA', (50, 50), (0, 0, 0, 0))
                mdraw = ImageDraw.Draw(method_icon)
                mdraw.rounded_rectangle([0, 0, 50, 50], radius=12, fill=(0, 190, 225)) 
                try: mdraw.text((25, 25), "GS", font=ImageFont.truetype(FONT_FILE, 24), fill=(255, 255, 255), anchor="mm")
                except: pass
            else:
                icon_url = "https://raw.githubusercontent.com/twitter/twemoji/master/assets/72x72/1f3ea.png"
                method_icon = load_icon(icon_url, (50, 50))
            m_w = draw.textlength(method, font=m_f)
            i_space = 65 if method_icon else 0
            total_w, m_h, pad_x, pad_y = m_w + i_space, 50, 60, 25
            m_box = [W/2 - total_w/2 - pad_x, cur_y, W/2 + total_w/2 + pad_x, cur_y + m_h + pad_y*2]
            draw.rounded_rectangle(m_box, radius=35, fill=(255, 255, 255))
            c_y, c_x = cur_y + pad_y + m_h/2, W/2 - total_w/2
            if method_icon:
                img.paste(method_icon, (int(c_x), int(c_y - 25)), method_icon)
                draw.text((c_x + i_space, c_y), method, font=m_f, fill=(20, 20, 20), anchor="lm")
            else: draw.text((W/2, c_y), method, font=m_f, fill=(20, 20, 20), anchor="mm")
            cur_y = m_box[3] 
        final_h = max(1350, int(cur_y + 100)) 
        img = img.crop((0, 0, W, final_h))
        return img.convert("RGB")
    except Exception as e: return None

# --- [탭 1] 단일 상품 제작 ---
with tab_single:
    ev = st.selectbox("행사 종류", ["선택안함", "1+1", "2+1", "혜택가"], key="s_ev")
    d_mode = st.radio("날짜 입력 방식", ["달력 선택", "직접 입력"], horizontal=True, key="s_dmode")
    if d_mode == "달력 선택":
        dates = st.date_input("행사 기간 선택", value=[date.today(), date.today()], key="s_dates")
        if (isinstance(dates, list) or isinstance(dates, tuple)) and len(dates) == 2: du = format_date_range(dates[0], dates[1])
        else: du = ""
    else: du = st.text_area("행사 기간 직접 입력", placeholder="예: 4/1~4/30", height=80, key="s_du")
    
    pn = st.text_area("상품명", placeholder="예: 삼립)호떡", height=80, key="s_pn")
    col_p1, col_p2 = st.columns(2)
    op = col_p1.text_input("정상가 (선택사항)", key="s_op", placeholder="예: 2,000")
    sp = col_p2.text_input("매가", key="s_sp", placeholder="예: 1,000")
    img_f = st.file_uploader("이미지 업로드", type=["jpg", "png"], key="s_file")
    if st.button("🚀 일반 홍보물 만들기", use_container_width=True, key="btn_single"):
        res = generate_poster(ev, du, pn, op, sp, img_f)
        if res:
            st.image(res, use_container_width=True)
            buf = io.BytesIO()
            res.save(buf, format="JPEG", quality=90)
            st.download_button("📥 다운로드", buf.getvalue(), "promo.jpg", "image/jpeg", use_container_width=True)

# --- [탭 2] 엑셀 대량 제작 ---
with tab_bulk:
    st.subheader("📁 엑셀 데이터 불러오기")
    bulk_input = st.text_area("데이터 붙여넣기", placeholder="1\t꿀호떡\t2000\t1000\n3\t삼겹살\t\t7500", height=150)
    gb_dmode = st.radio("공통 날짜 입력 방식", ["달력 선택", "직접 입력"], horizontal=True, key="gb_dmode")
    if gb_dmode == "달력 선택":
        gb_dates = st.date_input("공통 행사 기간 선택", value=[date.today(), date.today()], key="gb_dates")
        if (isinstance(gb_dates, list) or isinstance(gb_dates, tuple)) and len(gb_dates) == 2: global_du = format_date_range(gb_dates[0], gb_dates[1])
        else: global_du = ""
    else: global_du = st.text_input("공통 행사 기간 직접 입력", placeholder="예: 4/1 ~ 4/30")

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
                    st.write(f"**가격:** {item['orig']}원 → {item['sale']}원" if item['orig'] else f"**가격:** {item['sale']}원")
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
                    if 'img_bytes' in item: st.image(item['img_bytes'], use_container_width=True)

        if st.button("📑 선택한 상품 PDF로 한 번에 만들기", use_container_width=True):
            if not selected_indices: st.warning("선택된 상품이 없습니다.")
            else:
                with st.spinner("PDF 생성 중..."):
                    img_list = [Image.open(io.BytesIO(st.session_state['bulk_data'][idx]['img_bytes'])).convert("RGB") for idx in selected_indices if 'img_bytes' in st.session_state['bulk_data'][idx]]
                    if img_list:
                        pdf_buf = io.BytesIO()
                        img_list[0].save(pdf_buf, format="PDF", save_all=True, append_images=img_list[1:], resolution=300.0)
                        st.download_button("📥 완성된 PDF 다운로드", pdf_buf.getvalue(), "GS25_Promos.pdf", "application/pdf", use_container_width=True)

# --- [탭 3] 단톡방 사전예약 제작 ---
with tab_preorder:
    st.info("💡 단톡방 사전예약 홍보물을 만듭니다. 점포명을 넣으면 홍보물 상단에 자동 반영됩니다.")
    store_input = st.text_input("🏪 점포명", placeholder="예: 0000점 (미입력 시 기본 문구 추출)", key="pre_store")
    final_header = f"GS25 {store_input} 사전 예약" if store_input else "GS25 사전 예약"
    pn_pre = st.text_area("상품명", placeholder="예: 한우 냉장 육회 200G", height=80, key="pre_pn")
    price_pre = st.text_input("가격 및 할인 조건", placeholder="예: BC카드 구매 시 18,900원", key="pre_pr")
    col1, col2 = st.columns(2)
    pre_dmode = col1.radio("예약기간 방식", ["달력", "직접"], horizontal=True, key="pre_dmode")
    if pre_dmode == "달력":
        pre_dates = col1.date_input("예약 기간", value=[date.today(), date.today()], key="pre_dates")
        period_pre = format_date_range(pre_dates[0], pre_dates[1]) if len(pre_dates) == 2 else ""
    else: period_pre = col1.text_input("예약 기간 직접 입력", placeholder="예: 4/24~4/28", key="pre_per")
    pick_dmode = col2.radio("수령일 방식", ["달력", "직접"], horizontal=True, key="pick_dmode")
    if pick_dmode == "달력":
        p_date = col2.date_input("수령 일자", value=date.today(), key="p_date")
        pickup_pre = format_single_date(p_date)
    else: pickup_pre = col2.text_input("수령일자 직접 입력", placeholder="예: 4/30(목)", key="pre_pick")
    desc_pre = st.text_area("📄 상품 설명 (선택사항)", placeholder="예: 소스 동봉 / 1차 완판", height=80, key="pre_desc")
    method_pre = st.selectbox("신청 방법", ["매장 방문 예약", "우리동네GS 어플 접속 후 사전 예약", "단체 채팅방 카톡 요청"], key="pre_met")
    st.write("---")
    img_link_pre, img_file_pre = st.text_input("🔗 이미지 주소", key="pre_link"), st.file_uploader("📂 사진 업로드", type=["jpg", "png"], key="pre_file")
    if st.button("🚀 단톡방용 사전예약 홍보물 만들기", use_container_width=True):
        src_pre = img_file_pre if img_file_pre else (img_link_pre if img_link_pre else None)
        res_pre = generate_preorder_poster(final_header, pn_pre, price_pre, period_pre, pickup_pre, desc_pre, method_pre, src_pre)
        if res_pre:
            st.image(res_pre, use_container_width=True)
            buf_pre = io.BytesIO()
            res_pre.save(buf_pre, format="JPEG", quality=100)
            st.download_button("📥 이미지 다운로드", buf_pre.getvalue(), "preorder.jpg", "image/jpeg", use_container_width=True)
            st.write("---")
            st.subheader("💬 단톡방 공유용 메시지")
            kakao_text = f"📢 {final_header} 안내 📢\n\n🎁 상품명: {pn_pre}\n💰 특가: {price_pre}\n\n🗓️ 예약 기간: {period_pre}\n📦 수령 일자: {pickup_pre}\n\n✨ 상세 안내 ✨\n{desc_pre}\n\n👉 신청 방법: {method_pre}\n\n지금 바로 예약하시고 특별한 혜택을 누려보세요! 🥰"
            st.code(kakao_text, language="text")
            safe_text = kakao_text.replace('\n', '\\n').replace('`', '\\`')
            components.html(f"""<div style="text-align: center;"><button onclick="navigator.clipboard.writeText(`{safe_text}`).then(() => alert('✅ 복사되었습니다!'));" style="width: 100%; padding: 15px; font-size: 18px; background-color: #FEE500; color: #3C1E1E; border: none; border-radius: 10px; cursor: pointer; font-weight: bold;">📋 카톡 메시지 전체 복사하기</button></div>""", height=80)
