import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import io
import requests
import os

# 💡 [설정] 폰트 파일명 정의 (폴더 내 파일명과 일치해야 합니다)
FONT_FILE = "GmarketSansBold.ttf"

st.set_page_config(page_title="홍보물 뚝딱 제작소", layout="centered", initial_sidebar_state="collapsed")

st.title("🏪 홍보물 뚝딱 제작소")
st.caption("지마켓 산스 폰트로 더욱 깔끔해진 홍보물을 제작해보세요.")

st.write("---")

# 1단 레이아웃: 모바일 터치 편의성 증대
st.subheader("1. 행사 정보 입력")
event_type = st.selectbox("행사 종류", ["선택안함", "1+1", "2+1", "혜택가"])
duration = st.text_input("행사 기간", value="", placeholder="예: 4/1(화) ~ 4/30(수)")

st.write("") 

st.subheader("2. 상품 정보 입력")
# 💡 [수정] 요청하신 실전용 예시로 플레이스홀더 변경
product_name = st.text_input("상품명", value="", placeholder="예: 신선가득꿀호떡")
price = st.text_input("가격", value="", placeholder="예: 3개 4,000원")

st.write("---")

with st.expander("📸 3. 상품 사진 넣기 (터치해서 열기)", expanded=True):
    image_url = st.text_input("🔗 구글 이미지 주소 복사 후 붙여넣기", value="", placeholder="https://...")
    st.write("또는")
    uploaded_image = st.file_uploader("📂 갤러리에서 사진 업로드", type=["jpg", "jpeg", "png"])

st.write("---")

if st.button("🚀 A4 홍보물 만들기", use_container_width=True):
    try:
        # A4 가로 고해상도 (3508 x 2480)
        A4_W, A4_H = 3508, 2480 
        
        img = Image.open("template.jpg").convert("RGBA")
        img = img.resize((A4_W, A4_H)) 
        draw = ImageDraw.Draw(img)
        
        # 💡 [황금 비율 수치 고정]
        USER_MARGIN_PX = 72      
        USER_IMG_SCALE = 1.1     
        USER_TEXT_SCALE = 2.0    
        
        margin_right = A4_W - USER_MARGIN_PX 
        max_text_width = A4_W * 0.50 
        
        # 1. 행사 기간
        if duration:
            font_date = ImageFont.truetype(FONT_FILE, int(A4_W * 0.04))
            draw.text((margin_right, A4_H * 0.15), f"{duration}", font=font_date, fill=(0, 0, 0), anchor="rm")
        
        # 2. 행사 종류 (바닥 고정 레이아웃)
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
                # 이미지 없을 시 텍스트 대체
                font_promo_huge = ImageFont.truetype(FONT_FILE, int(A4_W * 0.16)) 
                draw.text((A4_W * 0.5, A4_H * 0.20), event_type, font=font_promo_huge, fill=(30, 100, 200), anchor="mm")

        # 3. 상품명 (지마켓 산스 + 오토 스케일링)
        if product_name:
            title_size = int(A4_W * 0.055 * USER_TEXT_SCALE)
            font_title = ImageFont.truetype(FONT_FILE, title_size)
            while draw.textlength(product_name, font=font_title) > max_text_width and title_size > 30:
                title_size -= 2
                font_title = ImageFont.truetype(FONT_FILE, title_size)
            draw.text((margin_right, A4_H * 0.55), product_name, font=font_title, fill=(0, 0, 0), anchor="rm")
        
        # 4. 가격 (지마켓 산스 + 오토 스케일링)
        if price:
            price_size = int(A4_W * 0.14 * USER_TEXT_SCALE)
            count_size = int(A4_W * 0.06 * USER_TEXT_SCALE)
            
            if "캔" in price or "개" in price:
                split_char = "캔" if "캔" in price else "개"
                parts = price.split(split_char)
                count_text = parts[0] + split_char 
                price_text = parts[1].strip()      
                
                font_price = ImageFont.truetype(FONT_FILE, price_size)
                font_count = ImageFont.truetype(FONT_FILE, count_size)
                gap = A4_W * 0.02
                total_width = draw.textlength(price_text, font=font_price) + draw.textlength(count_text, font=font_count) + gap
                
                while total_width > max_text_width and price_size > 40:
                    price_size -= 2
                    count_size -= 1 
                    font_price = ImageFont.truetype(FONT_FILE, price_size)
                    font_count = ImageFont.truetype(FONT_FILE, count_size)
                    total_width = draw.textlength(price_text, font=font_price) + draw.textlength(count_text, font=font_count) + gap
                
                draw.text((margin_right, A4_H * 0.80), price_text, font=font_price, fill=(220, 20, 20), anchor="rm")
                price_width = draw.textlength(price_text, font=font_price)
                draw.text((margin_right - price_width - gap, A4_H * 0.80), count_text, font=font_count, fill=(220, 20, 20), anchor="rm")
            else:
                font_price = ImageFont.truetype(FONT_FILE, price_size)
                while draw.textlength(price, font=font_price) > max_text_width and price_size > 40:
                    price_size -= 2
                    font_price = ImageFont.truetype(FONT_FILE, price_size)
                draw.text((margin_right, A4_H * 0.80), price, font=font_price, fill=(220, 20, 20), anchor="rm")
        
        # 5. 상품 이미지
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
        st.image(final_img, caption="지마켓 산스가 적용된 홍보물!", use_container_width=True)
        
        buf = io.BytesIO()
        final_img.save(buf, format="JPEG", quality=100) 
        byte_im = buf.getvalue()
        
        st.download_button(label="📥 고화질 다운로드 (인쇄용)", data=byte_im, file_name="promo_final.jpg", mime="image/jpeg", use_container_width=True)
        st.success("🎉 지마켓 산스 폰트로 깔끔하게 완성되었습니다!")
        
    except FileNotFoundError:
        st.error(f"⚠️ '{FONT_FILE}' 또는 'template.jpg' 파일이 폴더에 없습니다.")
