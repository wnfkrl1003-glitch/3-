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
duration = st.text_input("행사 기간", value="", placeholder="예: 4/1(화) ~ 4/30(수)")

st.write("") 

st.subheader("2. 상품 정보 입력")
product_name = st.text_input("상품명", value="", placeholder="예: 신선가득꿀호떡")
price = st.text_input("가격", value="", placeholder="예: 3개 4,000원")

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
        USER_TEXT_SCALE = 2.0    
        
        margin_right = A4_W - USER_MARGIN_PX 
        max_text_width = A4_W * 0.50 
        
        # [데이터 그리기 1] 행사 기간 (가로 폭 제한 방어벽 적용)
        if duration:
            date_size = int(A4_W * 0.04)
            font_date = ImageFont.truetype(FONT_FILE, date_size)
            max_date_width = A4_W * 0.30  # 로고 침범 방지
            
            while draw.textlength(duration, font=font_date) > max_date_width and date_size > 30:
                date_size -= 2
                font_date = ImageFont.truetype(FONT_FILE, date_size)
                
            draw.text((margin_right, A4_H * 0.15), duration, font=font_date, fill=(0, 0, 0), anchor="rm")
        
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
            title_size = int(A4_W * 0.055 * USER_TEXT_SCALE)
            font_title = ImageFont.truetype(FONT_FILE, title_size)
            while draw.textlength(product_name, font=font_title) > max_text_width and title_size > 30:
                title_size -= 2
                font_title = ImageFont.truetype(FONT_FILE, title_size)
            draw.text((margin_right, A4_H * 0.55), product_name, font=font_title, fill=(0, 0, 0), anchor="rm")
        
        # [데이터 그리기 4] 가격 영역 - 오토 스케일링, 분리 버그, 에러 완벽 해결
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
                total_width = draw.textlength(price_text, font=font_price) + draw.textlength(count_text, font=font_count) + gap
                
                while total_width > max_price_width and price_size > 30:
                    price_size -= 4
                    count_size -= 2 
                    font_price = ImageFont.truetype(FONT_FILE, price_size)
                    font_count = ImageFont.truetype(FONT_FILE, count_size)
                    total_width = draw.textlength(price_text, font=font_price) + draw.textlength(count_text, font=font_count) + gap
                
                draw.text((margin_right, A4_H * 0.80), price_text, font=font_price, fill=(220, 20, 20), anchor="rm")
                price_width = draw.textlength(price_text, font=font_price)
                draw.text((margin_right - price_width - gap, A4_H * 0.80), count_text, font=font_count, fill=(220, 20, 20), anchor="rm")
            else:
                font_price = ImageFont.truetype(FONT_FILE, price_size)
                while draw.textlength(price, font=font_price) > max_price_width and price_size > 30:
                    price_size -= 4
                    font_price = ImageFont.truetype(FONT_FILE, price_size)
                # 💡 [버그 해결] font_price 파라미터 정상 등록 완료
                draw.text((margin_right, A4_H * 0.80), price, font=font_price, fill=(220, 20, 20), anchor="rm")
        
        # [데이터 그리기 5] 상품 이미지 처리
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
