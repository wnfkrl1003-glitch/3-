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

# 💡 [핵심 수정] 봇 차단 방지를 위한 브라우저 위장(User-Agent) 헤더 추가
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
