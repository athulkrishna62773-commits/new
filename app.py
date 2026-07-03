import streamlit as st
from PIL import Image, ImageOps, ImageFilter  # The standard Python image toolkit

# 1. Page layout and header setup
st.set_page_config(page_title="Image Filter Studio", page_icon="🖼️", layout="centered")

st.title("🖼️ Instant Image Filter Studio")
st.write("Upload any image file from your computer and apply beautiful visual filters instantly!")

# 2. File Uploader Component: Allows students to pick a local photo file
uploaded_file = st.file_uploader("Choose an image file...", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    # Open the uploaded binary file data as a structured PIL Image object
    original_image = Image.open(uploaded_file)
    
    # 3. Sidebar Filter Selector Tray
    st.sidebar.header("⚙️ Filter Control Panel")
    selected_filter = st.sidebar.selectbox(
        "Choose a Visual Filter Effect:",
        ["Original", "Black & White", "Sepia Tone", "Gaussian Blur", "Contour Sketch"]
    )
    
    # 4. Processing Engine: Modifying the image object using conditional rules
    processed_image = original_image  # Default fallback state
    
    if selected_filter == "Black & White":
        # ImageOps.grayscale converts standard color pixels into single-channel gray values
        processed_image = ImageOps.grayscale(original_image)
        
    elif selected_filter == "Sepia Tone":
        # A quick trick to make sepia: turn to grayscale, then tint it with a warm brown overlay
        gray = ImageOps.grayscale(original_image)
        processed_image = ImageOps.colorize(gray, "#704214", "#C0B283")
        
    elif selected_filter == "Gaussian Blur":
        # Applies a smooth smoothing convolution filter matrix over pixels
        processed_image = original_image.filter(ImageFilter.GaussianBlur(radius=5))
        
    elif selected_filter == "Contour Sketch":
        # Finds high-contrast structural edges to create a rough pencil outline effect
        processed_image = original_image.filter(ImageFilter.CONTOUR)

    # 5. Display the Original vs Processed images side-by-side using web columns
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📸 Original Image")
        st.image(original_image, use_container_width=True)
        
    with col2:
        st.markdown(f"### ✨ {selected_filter} Result")
        st.image(processed_image, use_container_width=True)
        
    # 6. Download Button for the newly filtered image output file
    # We must save the processed image payload temporarily to let the user download it
    temp_save_path = "output_filtered.png"
    processed_image.save(temp_save_path)
    
    with open(temp_save_path, "rb") as file:
        st.download_button(
            label="📥 Download Filtered Image",
            data=file,
            file_name="filtered_photo.png",
            mime="image/png"
        )
else:
    st.info("💡 Standby: Please upload a photo file from your device to activate the image canvas filters.")
