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
# 💡 엔터키 사용 가능 안내 추가
duration = st.text_area("행사 기간 (엔터키로 줄바꿈 가능)", value="", placeholder="예:\n4/1(화) ~\n12/31(화)", height=80)

st.write("") 

st.subheader("2. 상품 정보 입력")
product_name = st.text_area("상품명 (엔터키로 줄바꿈 가능)", value="", placeholder="예:\n삼립)나이를 거꾸로\n먹는 떡국 떡", height=100)

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
        
        # 💡 [데이터 그리기 1] 행사 기간 (엔터키 기반, 안전 폭 유지)
        if duration:
            date_size = int(A4_W * 0.04)
            font_date = ImageFont.truetype(FONT_FILE, date_size)
            max_date_w = A4_W * 0.25 # 로고 영역과 겹치지 않게 안전 폭 설정
            
            lines_date = duration.split('\n')
            max_line_w_date = max([draw.textlength(line, font=font_date) for line in lines_date]) if lines_date else 0
            
            while max_line_w_date > max_date_w and date_size > 20:
                date_size -= 2
                font_date = ImageFont.truetype(FONT_FILE, date_size)
                max_line_w_date = max([draw.textlength(line, font=font_date) for line in lines_date])
                
            draw.text((margin_right, A4_H * 0.15), duration, font=font_date, fill=(0, 0, 0), anchor="rm", align="right", spacing=int(font_date.size*0.2))
        
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

        # 💡 [데이터 그리기 3] 상품명 (엔터키 기반, 위로 쌓이는 구조 유지)
        if product_name:
            title_size = int(A4_W * 0.055 * USER_TEXT_SCALE)
            font_title = ImageFont.truetype(FONT_FILE, title_size)
            max_title_w = A4_W * 0.50
            
            lines_title = product_name.split('\n')
            max_line_w_title = max([draw.textlength(line, font=font_title) for line in lines_title]) if lines_title else 0
            
            while max_line_w_title > max_title_w and title_size > 25:
                title_size -= 2
                font_title = ImageFont.truetype(FONT_FILE, title_size)
                max_line_w_title = max([draw.textlength(line, font=font_title) for line in lines_title])
            
            # anchor="rd"를 유지하여 엔터를 많이 쳐도 정상가를 누르지 않고 위쪽 빈 공간으로 텍스트가 자라납니다.
            draw.text((margin_right, A4_H * 0.60), product_name, font=font_title, fill=(0, 0, 0), anchor="rd", align="right", spacing=int(font_title.size*0.2))
        
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
                draw.text((margin_right - price_width - gap, A4_H * 0.82), count_text, font_count, fill=(220, 20, 20), anchor="rm")
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
