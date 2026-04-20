import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import io
import requests
import os
from duckduckgo_search import DDGS  # 실시간 이미지 검색 라이브러리

# [설정] Gmarket Sans Bold 폰트 파일명
FONT_FILE = "GmarketSansBold.ttf"

st.set_page_config(page_title="GS25 신선강화점 홍보물 제작소", page_icon="🏪", layout="centered", initial_sidebar_state="collapsed")

# 세션 상태 초기화 (선택한 이미지를 기억하기 위함)
if 'selected_image_url' not in st.session_state:
    st.session_state['selected_image_url'] = None

st.title("🏪✨ 신선강화점 홍보물 제작소")
st.caption("홍보물 제작에서 해방되세요! 🎉")

st.write("---")

st.subheader("1. 행사 정보 입력")
event_type = st.selectbox("행사 종류", ["선택안함", "1+1", "2+1", "혜택가"])
duration = st.text_input("행사 기간", value="", placeholder="예: 4/1(화) ~ 4/30(수)")

st.write("") 

st.subheader("2. 상품 정보 입력")
product_name = st.text_input("상품명", value="", placeholder="예: 삼립 신선가득꿀호떡")
price = st.text_input("가격", value="", placeholder="예: 3개 4,000원")

st.write("---")

# 💡 [핵심 업데이트] 실시간 이미지 검색 & 선택 기능
st.subheader("📸 3. 상품 사진 선택")
tab1, tab2, tab3 = st.tabs(["🔍 실시간 이미지 검색", "🤖 AI 자동 생성", "📂 직접 업로드"])

with tab1:
    st.info("💡 상품명 뒤에 '누끼'를 붙여 검색하면 배경 없는 깔끔한 사진을 찾기 쉽습니다.")
    search_query = st.text_input("이미지 검색어", value=f"{product_name} 누끼" if product_name else "")
    
    if st.button("🔎 검색 시작"):
        if search_query:
            with st.spinner("이미지를 찾는 중..."):
                try:
                    # DuckDuckGo를 이용한 실시간 이미지 검색 (최대 10개)
                    with DDGS() as ddgs:
                        results = [r for r in ddgs.images(search_query, max_results=10)]
                    
                    if results:
                        st.write("마음에 드는 이미지를 클릭하세요:")
                        # 이미지들을 격자(Grid) 형태로 보여줌
                        cols = st.columns(3)
                        for idx, result in enumerate(results):
                            with cols[idx % 3]:
                                st.image(result['image'], use_container_width=True)
                                if st.button(f"선택 {idx+1}", key=f"btn_{idx}"):
                                    st.session_state['selected_image_url'] = result['image']
                                    st.success(f"{idx+1}번 이미지가 선택되었습니다!")
                    else:
                        st.error("검색 결과가 없습니다. 검색어를 바꿔보세요.")
                except Exception as e:
                    st.error(f"검색 중 오류가 발생했습니다: {e}")
        else:
            st.warning("검색어를 입력해주세요.")

with tab2:
    st.info("일러스트 느낌의 이미지가 필요할 때 사용하세요.")
    ai_keyword = st.text_input("AI 작명가", value=product_name if product_name else "")
    if st.button("✨ AI 이미지 생성"):
        st.session_state['selected_image_url'] = f"https://image.pollinations.ai/prompt/{ai_keyword},white%20background,3d%20icon?nologo=true"
        st.image(st.session_state['selected_image_url'], width=200)

with tab3:
    uploaded_image = st.file_uploader("📂 이미지 파일 업로드", type=["jpg", "jpeg", "png"])

st.write("---")

# 홍보물 제작 버튼
if st.button("🚀 A4 홍보물 뚝딱 만들기", use_container_width=True):
    try:
        A4_W, A4_H = 3508, 2480 
        img = Image.open("template.jpg").convert("RGBA")
        img = img.resize((A4_W, A4_H)) 
        draw = ImageDraw.Draw(img)
        
        # OFC님이 설정하신 황금 비율 (여백 72, 텍스트 2배)
        USER_MARGIN_PX = 72      
        USER_IMG_SCALE = 1.1     
        USER_TEXT_SCALE = 2.0    
        margin_right = A4_W - USER_MARGIN_PX 
        max_text_width = A4_W * 0.50 
        
        # 1. 행사 기간
        if duration:
            font_date = ImageFont.truetype(FONT_FILE, int(A4_W * 0.04))
            draw.text((margin_right, A4_H * 0.15), f"{duration}", font=font_date, fill=(0, 0, 0), anchor="rm")
        
        # 2. 행사 종류
        if event_type != "선택안함":
            promo_filename = f"{event_type}.png"
            if os.path.exists(promo_filename):
                promo_img = Image.open(promo_filename).convert("RGBA")
                promo_img = promo_img.resize((int(A4_W * 0.4), int(A4_H * 0.2)), Image.LANCZOS) # 사이즈 조정
                img.paste(promo_img, (int(A4_W * 0.3), int(A4_H * 0.05)), promo_img)

        # 3. 상품명
        if product_name:
            font_title = ImageFont.truetype(FONT_FILE, int(A4_W * 0.055 * USER_TEXT_SCALE))
            draw.text((margin_right, A4_H * 0.55), product_name, font=font_title, fill=(0, 0, 0), anchor="rm")
        
        # 4. 가격
        if price:
            font_price = ImageFont.truetype(FONT_FILE, int(A4_W * 0.14 * USER_TEXT_SCALE))
            draw.text((margin_right, A4_H * 0.80), price, font=font_price, fill=(220, 20, 20), anchor="rm")
        
        # 5. 이미지 합성 (업로드 우선 > 검색 선택 이미지 순)
        final_product_img = None
        if uploaded_image:
            final_product_img = Image.open(uploaded_image).convert("RGBA")
        elif st.session_state['selected_image_url']:
            res = requests.get(st.session_state['selected_image_url'])
            final_product_img = Image.open(io.BytesIO(res.content)).convert("RGBA")

        if final_product_img:
            # 비율 유지하며 리사이즈
            final_product_img.thumbnail((int(A4_W * 0.45), int(A4_H * 0.55)), Image.LANCZOS)
            img.paste(final_product_img, (int(A4_W * 0.05), int(A4_H * 0.4)), final_product_img)

        final_img = img.convert("RGB")
        st.image(final_img, use_container_width=True)
        
        buf = io.BytesIO()
        final_img.save(buf, format="JPEG", quality=100)
        st.download_button("📥 고화질 다운로드", buf.getvalue(), "promo.jpg", "image/jpeg", use_container_width=True)
        
    except Exception as e:
        st.error(f"제작 중 오류 발생: {e}")
