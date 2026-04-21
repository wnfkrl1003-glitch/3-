import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import io
import requests
import os

# 💡 [설정] Gmarket Sans Bold 폰트 파일명
FONT_FILE = "GmarketSansBold.ttf"

st.set_page_config(page_title="GS25 신선강화점 홍보물 제작소", page_icon="🏪", layout="centered", initial_sidebar_state="collapsed")

st.title("🏪✨ 신선강화점 홍보물 제작소")
st.caption("홍보물 제작에서 해방되세요! 🎉")

st.write("---")

st.subheader("1. 행사 정보 입력")
event_type = st.selectbox("행사 종류", ["선택안함", "1+1", "2+1", "혜택가"])
duration = st.text_area("행사 기간", value="", placeholder="예: 4/1(화) ~ 12/31(화)", height=80)

st.write("") 

st.subheader("2. 상품 정보 입력")
product_name = st.text_area("상품명", value="", placeholder="예: 삼립)나이를 거꾸로 먹는 떡국 떡", height=100)

col1, col2 = st.columns(2)
with col1:
    original_price = st.text_input("정상가 (선택사항)", value="", placeholder="예: 2,000원")
with col2:
    price = st.text_input("행사 매가 (빨간색 가격)", value="", placeholder="예: 3개 4,000원")

st.write("---")

with st.expander("📸 3. 상품 사진 넣기 (터치해서 열기)", expanded=True):
    st.markdown("**(PC 접속 시)** 구글 \"XXX 누끼\"로 검색 후 이미지 \"링크\" 주소 복사 후 붙여넣기")
    image_url = st.text_input("🔗 이미지 주소 입력", value="", placeholder="https://...")
    
    st.write("---")
    
    st.markdown("**(모바일 접속 시)** 구글 \"XXX 누끼\"로 검색 후 이미지 다운로드 후 업로드")
    uploaded_image = st.file_uploader("📂 이미지 파일 업로드", type=["jpg", "jpeg", "png"])

st.write("---")

if st.button("🚀 A4 홍보물 뚝딱 만들기", use_container_width=True):
    try:
        A4_W, A4_H = 3508, 2480 
        
        img = Image.open("template.jpg").convert("RGBA")
        img = img.resize((A4_W, A4_H)) 
        draw = ImageDraw.Draw(img)
        
        USER_MARGIN_PX = 72      
        USER_IMG_SCALE = 1.1     
        USER_TEXT_SCALE = 1.6    
        margin_right = A4_W - USER_MARGIN_PX 
        max_text_width = A4_W * 0.50 

        # 💡 [핵심 기술] 절대 영역 방어 함수
        def fit_text_to_box(text, font_file, max_size, max_w, max_h, draw_obj):
            font_size = max_size
            min_size = 15 # 어떤 극한의 텍스트가 와도 방어할 최소 크기
            while font_size >= min_size:
                font = ImageFont.truetype(font_file, font_size)
                lines = []
                for paragraph in text.split('\n'):
                    current_line = ""
                    for char in paragraph:
                        test_line = current_line + char
                        if draw_obj.textlength(test_line, font=font) <= max_w:
                            current_line = test_line
                        else:
                            if current_line:
                                lines.append(current_line)
                            current_line = char
                    if current_line:
                        lines.append(current_line)
                
                wrapped_text = "\n".join(lines)
                bbox = draw_obj.multiline_textbbox((0, 0), wrapped_text, font=font, spacing=int(font_size*0.2))
                text_h = bbox[3] - bbox[1]
                
                if text_h <= max_h:
                    return wrapped_text, font
                font_size -= 2
                
            font = ImageFont.truetype(font_file, min_size)
            return wrapped_text, font
        
        # 💡 [데이터 그리기 1] 행사 기간 (10번 생각한 완전 격리 조치!)
        if duration:
            # 기존 0.30에서 0.18(18%)로 가로 폭을 대폭 줄여서 중앙 로고와 절대 물리적으로 충돌하지 않게 설계함
            max_date_w = A4_W * 0.18  
            max_date_h = A4_H * 0.20  
            base_size = int(A4_W * 0.04)
            wrapped_date, font_date = fit_text_to_box(duration, FONT_FILE, base_size, max_date_w, max_date_h, draw)
            draw.text((margin_right, A4_H * 0.15), wrapped_date, font=font_date, fill=(0, 0, 0), anchor="rm", align="right", spacing=int(font_date.size*0.2))
        
        # [데이터 그리기 2] 행사 종류 로고
        if event_type != "선택안함":
            promo_filename = f"{event_type}.png"
            if os.path.exists(promo_filename):
                promo_img = Image.open(promo_filename).convert("RGBA")
                max_promo_w = int(A4_W * 0.55) 
                max_promo_h = int(A4_H * 0.26) 
                aspect_ratio_promo = promo_img.width / promo_img.height
                target_promo_h = max_promo_h
                target_promo_w = int(target_promo_h * aspect_ratio_promo)
                if target_promo_w > max_promo_w:
                    target_promo_w = max_promo_w
                    target_promo_h = int(target_promo_w / aspect_ratio_promo)
                promo_img = promo_img.resize((target_promo_w, target_promo_h), Image.LANCZOS)
                paste_promo_x = int((A4_W * 0.5) - (target_promo_w / 2)) 
                paste_promo_y = int((A4_H * 0.28) - target_promo_h) 
                img.paste(promo_img, (paste_promo_x, paste_promo_y), promo_img)
            else:
                font_promo_huge = ImageFont.truetype(FONT_FILE, int(A4_W * 0.16)) 
                draw.text((A4_W * 0.5, A4_H * 0.20), event_type, font=font_promo_huge, fill=(30, 100, 200), anchor="mm")

        # [데이터 그리기 3] 상품명 
        if product_name:
            max_title_w = A4_W * 0.50 
            max_title_h = A4_H * 0.25 
            base_size = int(A4_W * 0.055 * USER_TEXT_SCALE)
            wrapped_title, font_title = fit_text_to_box(product_name, FONT_FILE, base_size, max_title_w, max_title_h, draw)
            
            draw.text((margin_right, A4_H * 0.60), wrapped_title, font=font_title, fill=(0, 0, 0), anchor="rd", align="right", spacing=int(font_title.size*0.2))
        
        # [데이터 그리기 4] 정상가 
        if original_price:
            display_original_price_text = f"정상가 {original_price}"
            orig_size = int(A4_W * 0.02 * USER_TEXT_SCALE)
            font_orig = ImageFont.truetype(FONT_FILE, orig_size)
            max_orig_width = A4_W * 0.40  
            while draw.textlength(display_original_price_text, font=font_orig) > max_orig_width and orig_size > 20:
                orig_size -= 2
                font_orig = ImageFont.truetype(FONT_FILE, orig_size)
            
            draw.text((margin_right, A4_H * 0.68), display_original_price_text, font=font_orig, fill=(160, 160, 160), anchor="rm")

        # [데이터 그리기 5] 매가(빨간색 가격) 
        if price:
            price_size = int(A4_W * 0.14 * USER_TEXT_SCALE)
            count_size = int(A4_W * 0.06 * USER_TEXT_SCALE)
            max_price_width = A4_W * 0.45 
            
            if "캔" in price or "개" in price:
                split_char = "캔" if "캔" in price else "개"
                parts = price.split(split_char, 1)
                count_text = parts[0] + split_char 
                price_text = parts[1].strip()      
                
                font_price = ImageFont.truetype(FONT_FILE, price_size)
                font_count = ImageFont.truetype(FONT_FILE, count_size)
                gap = A4_W * 0.02
                total_width = draw.textlength(price_text, font_price) + draw.textlength(count_text, font_count) + gap
                
                while total_width > max_price_width and price_size > 30:
                    price_size -= 4
                    count_size -= 2 
                    font_price = ImageFont.truetype(FONT_FILE, price_size)
                    font_count = ImageFont.truetype(FONT_FILE, count_size)
                    total_width = draw.textlength(price_text, font_price) + draw.textlength(count_text, font_count) + gap
                
                draw.text((margin_right, A4_H * 0.82), price_text, font=font_price, fill=(220, 20, 20), anchor="rm")
                price_width = draw.textlength(price_text, font_price)
                draw.text((margin_right - price_width - gap, A4_H * 0.82), count_text, font=font_count, fill=(220, 20, 20), anchor="rm")
            else:
                font_price = ImageFont.truetype(FONT_FILE, price_size)
                while draw.textlength(price, font_price) > max_price_width and price_size > 30:
                    price_size -= 4
                    font_price = ImageFont.truetype(FONT_FILE, price_size)
                draw.text((margin_right, A4_H * 0.82), price, font_price, fill=(220, 20, 20), anchor="rm")
        
        # [데이터 그리기 6] 상품 이미지 처리
        product_img = None
        if image_url:
            try:
                response = requests.get(image_url)
                product_img = Image.open(io.BytesIO(response.content)).convert("RGBA")
            except: pass
        elif uploaded_image:
            product_img = Image.open(uploaded_image).convert("RGBA")
            
        if product_img:
            max_img_w = int(A4_W * 0.35 * USER_IMG_SCALE)
            max_img_h = int(A4_H * 0.45 * USER_IMG_SCALE)
            
            img_w, img_h = product_img.size
            aspect_ratio = img_w / img_h
            
            target_h = max_img_h
            target_w = int(target_h * aspect_ratio)
            
            if target_w > max_img_w:
                target_w = max_img_w
                target_h = int(target_w / aspect_ratio)
                
            product_img = product_img.resize((target_w, target_h), Image.LANCZOS)
            paste_x = int((A4_W * 0.25) - (target_w / 2)) 
            paste_y = int((A4_H * 0.65) - (target_h / 2)) 
            img.paste(product_img, (paste_x, paste_y), product_img)

        final_img = img.convert("RGB")
        st.image(final_img, caption="신선강화점 전용 쇼카드 미리보기", use_container_width=True)
        
        buf = io.BytesIO()
        final_img.save(buf, format="JPEG", quality=100) 
        byte_im = buf.getvalue()
        
        st.download_button(label="📥 고화질 다운로드 (인쇄용)", data=byte_im, file_name="promo_fresh_final.jpg", mime="image/jpeg", use_container_width=True)
        st.success("🎉 '신선강화점' 홍보물이 준비되었습니다!")
        
    except FileNotFoundError:
        st.error(f"⚠️ '{FONT_FILE}' 또는 'template.jpg' 파일이 깃허브에 업로드되어 있는지 확인해주세요.")
