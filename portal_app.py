import streamlit as st
import pandas as pd
import requests
import io
import re
from PIL import Image, ImageDraw

st.set_page_config(page_title="YPG Credentials Portal", page_icon="🇬🇭", layout="centered")

# --- HIDE STREAMLIT BRANDING & GITHUB LINK ---
hide_menu_style = """
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    </style>
"""
st.markdown(hide_menu_style, unsafe_allow_html=True)

# --- Form Links ---
NEW_REG_LINK = "https://forms.gle/3xyDZGTJWnNuxhY19"
CORRECTION_LINK = "https://forms.gle/tbfSs7G6D8PyKYUb9"

# Your Google Drive File ID
DATABASE_FILE_ID = "1-SmT8WIVy0FyE-NBKxPA5QSjkSX96ArS"

@st.cache_data(ttl=600)
def load_database():
    try:
        url = f"https://drive.google.com/uc?export=download&id={DATABASE_FILE_ID}"
        df = pd.read_csv(url)
        return df
    except Exception as e:
        return None

def apply_watermark(image_path):
    try:
        # Load the image from the internet (GitHub)
        # image_path is just the filename now
        canvas = Image.open(image_path).convert("RGBA")
        
        # THE SECURITY WATERMARK (Anti-Screenshot)
        watermark = Image.new("RGBA", canvas.size, (255, 255, 255, 0))
        watermark_draw = ImageDraw.Draw(watermark)
        
        # Create a repeating line of text
        text_line = "DRAFT - DO NOT PRINT   " * 5
        
        # Determine size of the text
        font_size = int(canvas.width * 0.06)
        
        # Draw multiple rows of text to cover the whole image top to bottom
        for y in range(-canvas.height, canvas.height * 2, int(canvas.height * 0.12)):
            watermark_draw.text((-canvas.width, y), text_line, 
                                fill=(0, 0, 0, 160), # Dark black with transparency
                                font_size=font_size)
        
        # Rotate the entire watermark layer diagonally
        watermark = watermark.rotate(35, expand=False, center=(canvas.width // 2, canvas.height // 2))
        
        # Merge the watermark onto the ID card
        final_preview = Image.alpha_composite(canvas, watermark)
        return final_preview.convert("RGB")
    except Exception as e:
        return None

# --- APP LAYOUT ---
st.title("🇬🇭 YPG Delegate Portal")
st.write("Welcome! Search for your record to review your official YPG ID Card.")

st.info("Are you a new MP who has not submitted details yet?")
st.link_button("➕ First-Time Registration", NEW_REG_LINK, type="primary")

st.markdown("---")

# --- SEARCH ENGINE ---
df = load_database()

if df is not None:
    st.subheader("🔍 Find Your Record")
    
    # Filter 1: Region
    regions = sorted(df['Region'].dropna().unique().tolist())
    selected_region = st.selectbox("1. Select Your Region", ["-- Choose Region --"] + regions)
    
    if selected_region != "-- Choose Region --":
        # Filter 2: Constituency
        const_df = df[df['Region'] == selected_region]
        constituencies = sorted(const_df['Constituency'].dropna().unique().tolist())
        selected_const = st.selectbox("2. Select Your Constituency", ["-- Choose Constituency --"] + constituencies)
        
        if selected_const != "-- Choose Constituency --":
            # Filter 3: Name
            person_df = const_df[const_df['Constituency'] == selected_const]
            
            def make_name(row):
                return f"{row.get('First_Name', '')} {row.get('Surname', '')}".strip()
            
            names = ["-- Choose Your Name --"] + person_df.apply(make_name, axis=1).tolist()
            selected_name = st.selectbox("3. Select Your Name", names)
            
            if selected_name != "-- Choose Your Name --":
                
                # Fetch specific person's data
                selected_idx = names.index(selected_name) - 1
                row = person_df.iloc[selected_idx]
                
                first_name = row.get('First_Name', '')
                surname = row.get('Surname', '')
                mp_id = row.get('MP_ID', '') # Grab their official ID number
                
                st.markdown("---")
                
                with st.spinner("Retrieving your secure preview..."):
                    # Look in the main folder for the images (since we skipped the folder earlier)
                    front_path = f"{mp_id}_front.jpg"
                    back_path = f"{mp_id}_back.jpg"
                    
                    # Apply watermarks
                    front_preview = apply_watermark(front_path)
                    back_preview = apply_watermark(back_path)
                    
                    if front_preview and back_preview:
                        st.markdown("### 🪪 Your ID Card Preview")
                        
                        # Display Results Side-by-Side
                        card_col1, card_col2 = st.columns(2)
                        with card_col1:
                            st.image(front_preview, caption="FRONT (Watermarked)", use_container_width=True)
                        with card_col2:
                            st.image(back_preview, caption="BACK (Watermarked)", use_container_width=True)
                            
                        st.markdown("---")
                        st.markdown("### Is everything correct?")
                        
                        col_btn1, col_btn2 = st.columns(2)
                        with col_btn1:
                            if st.button("✅ Yes, Everything Looks Good!", type="primary", use_container_width=True):
                                st.balloons()
                                st.success("Awesome! Your ID is verified and locked in for printing. You can safely close this page.")
                        with col_btn2:
                            st.link_button("✏️ No, Submit a Correction", CORRECTION_LINK, use_container_width=True)
                            
                    else:
                        st.warning(f"⚠️ We could not locate the exported ID designs for {first_name} {surname} (ID: {mp_id}).")
else:
    st.error("Connecting to the database... If this persists, the Google Drive link may not be public.")
