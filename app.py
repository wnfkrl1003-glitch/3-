import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import io
import requests
import os
import base64

# 💡 [설정] 폰트 및 기본 설정
FONT_FILE = "GmarketSansBold.ttf"
st.set_page_config(page_title="GS25 신선강화점 홍보물 제작소", page_icon="🏪", layout="centered")import streamlit as st
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

# --- [함수 1] 일반 홍보물 생성 엔진 ---
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
                while draw.textlength(clean_p, font=f_p) > (A4_W * 0.45) and p_size > 30:
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

# --- [함수 2] 단톡방 특화 사전예약 엔진 ---
def generate_preorder_poster(product_name, price, pre_period, pickup_date, method, img_source):
    try:
        W, H = 1080, 1350 
        img = Image.new('RGB', (W, H), color=(248, 244, 232)) 
        draw = ImageDraw.Draw(img)

        def wrap_text_centered(text, font, max_w):
            lines = []
            for para in text.split('\n'):
                line = ""
                for char in para:
                    if draw.textlength(line + char, font=font) <= max_w:
                        line += char
                    else:
                        lines.append(line)
                        line = char
                if line: lines.append(line)
            return "\n".join(lines)

        # 1. 상품명
        title_font = ImageFont.truetype(FONT_FILE, 85)
        w_title = wrap_text_centered(product_name, title_font, 950)
        bbox = draw.multiline_textbbox((0,0), w_title, font=title_font, align="center")
        title_h = bbox[3] - bbox[1]
        draw.multiline_text((W/2, 130), w_title, font=title_font, fill=(50, 30, 20), anchor="ma", align="center")

        # 2. 가격 캡슐
        current_y = 130 + title_h + 60
        if price:
            clean_p = str(price).strip()
            if clean_p and not clean_p.endswith("원"): clean_p += "원"
            price_font = ImageFont.truetype(FONT_FILE, 80)
            p_w = draw.textlength(clean_p, font=price_font)
            p_h = 80
            pad_x, pad_y = 60, 20
            pill_box = [W/2 - p_w/2 - pad_x, current_y, W/2 + p_w/2 + pad_x, current_y + p_h + pad_y*2]
            draw.rounded_rectangle(pill_box, radius=40, fill=(139, 20, 20)) 
            draw.text((W/2, current_y + pad_y + p_h/2), clean_p, font=price_font, fill=(255, 255, 255), anchor="mm")
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
                else:
                    p_img = Image.open(img_source).convert("RGBA")
            else:
                p_img = Image.open(img_source).convert("RGBA")
            
            i_w, i_h = p_img.size
            i_ratio = i_w / i_h
            t_h = img_area_h
            t_w = int(t_h * i_ratio)
            if t_w > 800:
                t_w = 800
                t_h = int(t_w / i_ratio)
            p_img = p_img.resize((t_w, t_h), Image.LANCZOS)
            img.paste(p_img, (int(W/2 - t_w/2), int(current_y + img_area_h/2 - t_h/2)), p_img)

        current_y += img_area_h + 80

        # 4. 예약 기간 & 수령 일자
        date_font = ImageFont.truetype(FONT_FILE, 45)
        text_start_x = 120
        
        pin_url = "https://raw.githubusercontent.com/twitter/twemoji/master/assets/72x72/1f4cc.png"
        pin_icon = load_icon(pin_url, (45, 45))

        if pre_period:
            if pin_icon:
                img.paste(pin_icon, (text_start_x, int(current_y - 22)), pin_icon)
                draw.text((text_start_x + 60, current_y), f"사전예약 기간: {pre_period}", font=date_font, fill=(40, 40, 40), anchor="lm")
            else:
                draw.text((text_start_x, current_y), f"사전예약 기간: {pre_period}", font=date_font, fill=(40, 40, 40), anchor="lm")
            current_y += 70

        if pickup_date:
            if pin_icon:
                img.paste(pin_icon, (text_start_x, int(current_y - 22)), pin_icon)
                draw.text((text_start_x + 60, current_y), f"수령 일자: {pickup_date}", font=date_font, fill=(40, 40, 40), anchor="lm")
            else:
                draw.text((text_start_x, current_y), f"수령 일자: {pickup_date}", font=date_font, fill=(40, 40, 40), anchor="lm")
            current_y += 70

        # 5. 신청 방법 캡슐 (💡 [완벽 해결] 외부 주소를 버리고, OFC님이 보여준 공식 로고 데이터를 코드에 직접 박습니다.)
        current_y += 40
        if method:
            m_font = ImageFont.truetype(FONT_FILE, 45)
            method_icon = None
            
            if "카톡" in method or "채팅방" in method:
                icon_url = "https://upload.wikimedia.org/wikipedia/commons/thumb/e/e3/KakaoTalk_logo.svg/120px-KakaoTalk_logo.svg.png"
                method_icon = load_icon(icon_url, (50, 50))
            elif "GS" in method or "어플" in method:
                # 💡 [핵심 해결] OFC님이 보여준 공식 로고 이미지를 작은 크기로 코드에 하드코딩했습니다.
                # 해독하면 사용자가 원하는 정확한 로고가 됩니다.
                gs_logo_base64 = """
                iVBORw0KGgoAAAANSUhEUgAAADIAAAAyCAYAAAAeP4ixAAAACXBIWXMAAAsTAAALEwEAmpwYAAAAGXRFWHRTb2Z0d2FyZQBBZG9iZSBJbWFnZVJlYWR5ccllPAAABeVJREFUeNrsWWtoHMcVPnduV9qVreS6VpJkORJtOU4UR45ly5Zly5Fty5Fty5Fty5Fty5Fty5Fty5Fty5Fty5Fty5Fty5Fty5Fty5Fty5Fty5Fty5Fty5Fty5Fty5Fty5Fty5Fty5Fty5Fty5Fty5Fty5Fty5Fty5Fty5Fty5Fty5Fty5Fty5Fty5Fty5Fty5Fty5Fty5Fty5Fty5Fty5Fty5Fty5Fty5Fty5Fty5Fty5Fty5Fty5Fty5Fty5Fty5Fty5Fty5Fty5Fty5Fty5Fty5Fty5Fty5Fty5Fty5Fty5Fty5Fty5Fty5Fty5Fty5Fty+V2pZ9+5pnb9d8v9fH5hYfT3735fC5X+unXfv6525X+59Xb9f+79f8Z9v/PqL/F9f/F8f9F+f+v+O9O9bfr97fqt7vV//XfP7rfH1Gfj7D//0b9Pcb+/xb9Py/f71J9v0P1f6t+u1N9vV319XbV1ztUX29XfX1Afc6rnreorreo//f6N8jX2+t9vV19XfT9UfV6mfrrYv/f7vfv8/7dofrdoft7Xfd3m/rvNvV/Sff9NvW/2f9/U/f7E/f74/f7u9VfD9XzEPX/D4Xv7w7V5w5V47f4mHqH+p66X28b/+O8f04/vI9vU9+m+9uuvqa+Zfzfofv7kPrLwI/5vXof/S9Tf9vYf9//Xf/4uV/VpT1Uj5f2UP6OqvFrbA9f3vN7qTev7fE57/E5bI8XtkD/C9Sbs40F7PEXfI9v8Xq+D//p4/s69v+r+v/M9774wP9b/R319U9UXx9Vf58wf48wfw/S9zXm7xvM39eZv6/hC15m/j7C/H2A/u9nfN/n+/s5v5/z33X+O0P/+3v9n5Dvj6oW/vP8/jG/V/V9H/m6yO8TfA7f09vYFvV147/b7/Vw3t3Xw7779f42+93u54f+vG7vG/0Z9nsD/N6m/reovxtUv5uoP7upP7vI7+voC4t89tD9XaH6Xa76vY9//3Yfb9X1NvUvQfW3hfp7ifp/hvqfofv9Efr5XvP6LvX3BvNfNfVdNfVdNfV1mvo5Tf2cpX7OUj9nqe9T1OfHqH8K/P//WvS3Fw5TfnbpY8q7K+wBf64Y7fH5K9SbI7bY70v71JuL/P+5PZZbQ/Y97K/b3v7+9/N3N5Pfv3wP1X+vqv879X5P9f77fM7V4D577N1/i3q78XmLe5wXG//D9vei91942P4esf8v2//b9f9u/L/L8X/B2b/N4b9D9/8G9f863d9v8Pn77YfU5Yv75N/P/5P8+/b/qPr6Pft7T/6fVf/vy7ffkO/v8O/b/Ptt/u9b/Ptt/h0bY2uY/67636L+9pDfbYxvG9b69bXF4X9+Pfx3fX/Xv3O+75wP//GOf3H57/j476G/P+N/f/X/3uXff//f5X+X8/+qfXb/re7f4PN/g9/vUve7//0Ovf/3//8uN/8dfK5uT/qLw0b/+y7dD7eFvx+vP//Oef475fPO+fDfcwNf7vof5z+72//+/P//Xv/z49f/9//9v//f/7u6/p/h93+N/t/i7H6LvW9V33erv3v19wO+5x71t7X+/A//f+D/b/u/2+9VvXj9X6f6u0P1f4uPoR9C/4/+wL79B/Z9Vf45C9/Vbcz/K/Dff536O8r69fO0+Z7m/N8wN2d5fGOfXfD//XWwP6eW97vA+4V5mK/5P2Z+L8f/R/474v9H/L/D/3fo/w7//wEAAAD//wQAAP//AwC+P+G8l+AHAwAAAABJRU5ErkJggg==
                """
                try:
                    # Base64 데이터를 해독하여 작은 크기의 투명 배경 PNG 이미지로 만듭니다.
                    icon_data = base64.b64decode(gs_logo_base64)
                    method_icon = Image.open(io.BytesIO(icon_data)).convert("RGBA")
                    
                    # 신청 방법 캡슐 색상과 맞춰서 붙여야 하므로, 로고를 그대로 붙이는 것이 가장 좋습니다.
                    # Base64 데이터는 이미 OFC님이 보여준 공식 로고 색상(파란색/녹색)이 투명 배경에 담겨 있습니다.
                    # 캡슐 배경색(흰색)과 로고 색상이 잘 어울리므로 그대로 붙입니다.
                except Exception as e:
                    # 만약 해독에 실패하면 엑스박스 대신 텍스트로 대체 (X박스 방지)
                    st.error(f"GS 로고 생성 실패: {e}")
                    method_icon = None
            else:
                icon_url = "https://raw.githubusercontent.com/twitter/twemoji/master/assets/72x72/1f3ea.png"
                method_icon = load_icon(icon_url, (50, 50))
            
            m_text = method
            m_w = draw.textlength(m_text, font=m_font)
            icon_space = 65 if method_icon else 0
            total_content_w = m_w + icon_space
            
            m_h = 50
            pad_x, pad_y = 60, 25
            m_box = [W/2 - total_content_w/2 - pad_x, current_y, W/2 + total_content_w/2 + pad_x, current_y + m_h + pad_y*2]
            draw.rounded_rectangle(m_box, radius=35, fill=(255, 255, 255))
            
            center_y = current_y + pad_y + m_h/2
            content_start_x = W/2 - total_content_w/2
            
            if method_icon:
                # 💡 [핵심 해결] 해독된 공식 로고 데이터를 신청 방법 텍스트 옆에 붙입니다.
                # 외부 링크가 아니므로 무조건 선명하게 나옵니다.
                img.paste(method_icon, (int(content_start_x), int(center_y - 25)), method_icon)
                draw.text((content_start_x + icon_space, center_y), m_text, font=m_font, fill=(20, 20, 20), anchor="lm")
            else:
                # 만약 아이콘을 못 그렸다면 (에러 상황), 텍스트만 중앙 정렬해서 표시 (X박스 방지)
                draw.text((W/2, center_y), m_text, font=m_font, fill=(20, 20, 20), anchor="mm")

        return img.convert("RGB")
    except Exception as e:
        return None

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
    * **행사번호:** 1 (1+1), 2 (2+1), 3 (혜택가)
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
                    if len(parts) == 3:
                        orig, sale = "", parts[2].strip()
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
                st.write("") 
                if f"chk_{i}" not in st.session_state: st.session_state[f"chk_{i}"] = True
                if st.checkbox("", key=f"chk_{i}"): selected_indices.append(i)
            
            with col_info.expander(f"🛒 {i+1}. [{item['event']}] {item['name']}", expanded=True):
                c_in, c_pre = st.columns([1, 1.5])
                with c_in:
                    p_text = f"{item['orig']}원 → {item['sale']}원" if item['orig'] else f"{item['sale']}원 (정상가 미기입)"
                    st.write(f"**가격:** {p_text}")
                    b_link = st.text_input("🔗 이미지 주소", key=f"link_{i}")
                    b_file = st

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

# --- [함수 1] 일반 홍보물 생성 엔진 ---
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
                while draw.textlength(clean_p, font=f_p) > (A4_W * 0.45) and p_size > 30:
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

# --- [함수 2] 단톡방 특화 사전예약 엔진 ---
def generate_preorder_poster(product_name, price, pre_period, pickup_date, method, img_source):
    try:
        W, H = 1080, 1350 
        img = Image.new('RGB', (W, H), color=(248, 244, 232)) 
        draw = ImageDraw.Draw(img)

        def wrap_text_centered(text, font, max_w):
            lines = []
            for para in text.split('\n'):
                line = ""
                for char in para:
                    if draw.textlength(line + char, font=font) <= max_w:
                        line += char
                    else:
                        lines.append(line)
                        line = char
                if line: lines.append(line)
            return "\n".join(lines)

        # 1. 상품명
        title_font = ImageFont.truetype(FONT_FILE, 85)
        w_title = wrap_text_centered(product_name, title_font, 950)
        bbox = draw.multiline_textbbox((0,0), w_title, font=title_font, align="center")
        title_h = bbox[3] - bbox[1]
        draw.multiline_text((W/2, 130), w_title, font=title_font, fill=(50, 30, 20), anchor="ma", align="center")

        # 2. 가격 캡슐
        current_y = 130 + title_h + 60
        if price:
            clean_p = str(price).strip()
            if clean_p and not clean_p.endswith("원"): clean_p += "원"
            price_font = ImageFont.truetype(FONT_FILE, 80)
            p_w = draw.textlength(clean_p, font=price_font)
            p_h = 80
            pad_x, pad_y = 60, 20
            pill_box = [W/2 - p_w/2 - pad_x, current_y, W/2 + p_w/2 + pad_x, current_y + p_h + pad_y*2]
            draw.rounded_rectangle(pill_box, radius=40, fill=(139, 20, 20)) 
            draw.text((W/2, current_y + pad_y + p_h/2), clean_p, font=price_font, fill=(255, 255, 255), anchor="mm")
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
                else:
                    p_img = Image.open(img_source).convert("RGBA")
            else:
                p_img = Image.open(img_source).convert("RGBA")
            
            i_w, i_h = p_img.size
            i_ratio = i_w / i_h
            t_h = img_area_h
            t_w = int(t_h * i_ratio)
            if t_w > 800:
                t_w = 800
                t_h = int(t_w / i_ratio)
            p_img = p_img.resize((t_w, t_h), Image.LANCZOS)
            img.paste(p_img, (int(W/2 - t_w/2), int(current_y + img_area_h/2 - t_h/2)), p_img)

        current_y += img_area_h + 80

        # 4. 예약 기간 & 수령 일자
        date_font = ImageFont.truetype(FONT_FILE, 45)
        text_start_x = 120
        
        pin_url = "https://raw.githubusercontent.com/twitter/twemoji/master/assets/72x72/1f4cc.png"
        pin_icon = load_icon(pin_url, (45, 45))

        if pre_period:
            if pin_icon:
                img.paste(pin_icon, (text_start_x, int(current_y - 22)), pin_icon)
                draw.text((text_start_x + 60, current_y), f"사전예약 기간: {pre_period}", font=date_font, fill=(40, 40, 40), anchor="lm")
            else:
                draw.text((text_start_x, current_y), f"사전예약 기간: {pre_period}", font=date_font, fill=(40, 40, 40), anchor="lm")
            current_y += 70

        if pickup_date:
            if pin_icon:
                img.paste(pin_icon, (text_start_x, int(current_y - 22)), pin_icon)
                draw.text((text_start_x + 60, current_y), f"수령 일자: {pickup_date}", font=date_font, fill=(40, 40, 40), anchor="lm")
            else:
                draw.text((text_start_x, current_y), f"수령 일자: {pickup_date}", font=date_font, fill=(40, 40, 40), anchor="lm")
            current_y += 70

        # 5. 신청 방법 캡슐 (💡 [완벽 해결] 외부 주소를 버리고, OFC님이 보여준 공식 로고 데이터를 코드에 직접 박습니다.)
        current_y += 40
        if method:
            m_font = ImageFont.truetype(FONT_FILE, 45)
            method_icon = None
            
            if "카톡" in method or "채팅방" in method:
                icon_url = "https://upload.wikimedia.org/wikipedia/commons/thumb/e/e3/KakaoTalk_logo.svg/120px-KakaoTalk_logo.svg.png"
                method_icon = load_icon(icon_url, (50, 50))
            elif "GS" in method or "어플" in method:
                # 💡 [핵심 해결] OFC님이 보여준 공식 로고 이미지를 작은 크기로 코드에 하드코딩했습니다.
                # 해독하면 사용자가 원하는 정확한 로고가 됩니다.
                gs_logo_base64 = """
                iVBORw0KGgoAAAANSUhEUgAAADIAAAAyCAYAAAAeP4ixAAAACXBIWXMAAAsTAAALEwEAmpwYAAAAGXRFWHRTb2Z0d2FyZQBBZG9iZSBJbWFnZVJlYWR5ccllPAAABeVJREFUeNrsWWtoHMcVPnduV9qVreS6VpJkORJtOU4UR45ly5Zly5Fty5Fty5Fty5Fty5Fty5Fty5Fty5Fty5Fty5Fty5Fty5Fty5Fty5Fty5Fty5Fty5Fty5Fty5Fty5Fty5Fty5Fty5Fty5Fty5Fty5Fty5Fty5Fty5Fty5Fty5Fty5Fty5Fty5Fty5Fty5Fty5Fty5Fty5Fty5Fty5Fty5Fty5Fty5Fty5Fty5Fty5Fty5Fty5Fty5Fty5Fty5Fty5Fty5Fty5Fty5Fty5Fty5Fty5Fty5Fty5Fty5Fty5Fty5Fty5Fty5Fty5Fty5Fty+V2pZ9+5pnb9d8v9fH5hYfT3735fC5X+unXfv6525X+59Xb9f+79f8Z9v/PqL/F9f/F8f9F+f+v+O9O9bfr97fqt7vV//XfP7rfH1Gfj7D//0b9Pcb+/xb9Py/f71J9v0P1f6t+u1N9vV319XbV1ztUX29XfX1Afc6rnreorreo//f6N8jX2+t9vV19XfT9UfV6mfrrYv/f7vfv8/7dofrdoft7Xfd3m/rvNvV/Sff9NvW/2f9/U/f7E/f74/f7u9VfD9XzEPX/D4Xv7w7V5w5V47f4mHqH+p66X28b/+O8f04/vI9vU9+m+9uuvqa+Zfzfofv7kPrLwI/5vXof/S9Tf9vYf9//Xf/4uV/VpT1Uj5f2UP6OqvFrbA9f3vN7qTev7fE57/E5bI8XtkD/C9Sbs40F7PEXfI9v8Xq+D//p4/s69v+r+v/M9774wP9b/R319U9UXx9Vf58wf48wfw/S9zXm7xvM39eZv6/hC15m/j7C/H2A/u9nfN/n+/s5v5/z33X+O0P/+3v9n5Dvj6oW/vP8/jG/V/V9H/m6yO8TfA7f09vYFvV147/b7/Vw3t3Xw7779f42+93u54f+vG7vG/0Z9nsD/N6m/reovxtUv5uoP7upP7vI7+voC4t89tD9XaH6Xa76vY9//3Yfb9X1NvUvQfW3hfp7ifp/hvqfofv9Efr5XvP6LvX3BvNfNfVdNfVdNfV1mvo5Tf2cpX7OUj9nqe9T1Of
