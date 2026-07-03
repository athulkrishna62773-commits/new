import streamlit as st
from PIL import Image, ImageOps, ImageFilter, ImageEnhance
import segno
import base64
import io

# ============================================================
# PAGE CONFIGURATION
# ============================================================
st.set_page_config(page_title="Creative Workspace Studio", page_icon="🎨", layout="wide")

# ============================================================
# SIDEBAR NAVIGATION
# ============================================================
st.sidebar.title("🧭 Workspace Navigation")
app_mode = st.sidebar.radio(
    "Select a working mode:",
    ["🎨 Advanced Image Studio", "🔮 Universal QR Engine"]
)
st.sidebar.markdown("---")


# ============================================================
# HELPER FUNCTIONS (each wrapped defensively so the UI never crashes)
# ============================================================

def format_bytes(size):
    """Human-readable byte size formatting."""
    if size is None:
        return "N/A"
    size = float(size)
    for unit in ["B", "KB", "MB", "GB"]:
        if size < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} TB"


def apply_filter(image, filter_name):
    """Applies the selected visual filter to a PIL image."""
    try:
        if filter_name == "Original":
            return image
        elif filter_name == "Black & White":
            return ImageOps.grayscale(image)
        elif filter_name == "Sepia Tone":
            gray = ImageOps.grayscale(image)
            return ImageOps.colorize(gray, "#704214", "#C0B283")
        elif filter_name == "Gaussian Blur":
            return image.filter(ImageFilter.GaussianBlur(radius=5))
        elif filter_name == "Contour Sketch":
            return image.filter(ImageFilter.CONTOUR)
        elif filter_name == "Vibrant Saturation":
            enhancer = ImageEnhance.Color(image.convert("RGB"))
            return enhancer.enhance(2.2)
        elif filter_name == "Retro Negative":
            rgb_image = image.convert("RGB")
            return ImageOps.invert(rgb_image)
        elif filter_name == "Emboss Art":
            return image.filter(ImageFilter.EMBOSS)
        else:
            return image
    except Exception as e:
        st.warning(f"⚠️ Filter engine could not apply '{filter_name}': {e}")
        return image


def apply_crop(image, top, bottom, left, right):
    """Crops the image using pixel boundaries from each edge."""
    try:
        width, height = image.size
        box_left, box_top = left, top
        box_right, box_bottom = width - right, height - bottom
        if box_right <= box_left or box_bottom <= box_top:
            st.warning("⚠️ Crop boundaries overlap or exceed image size. Skipping crop.")
            return image
        return image.crop((box_left, box_top, box_right, box_bottom))
    except Exception as e:
        st.warning(f"⚠️ Crop engine failed: {e}")
        return image


def apply_resize(image, width, height):
    """Resizes the image to the given width/height."""
    try:
        if width <= 0 or height <= 0:
            st.warning("⚠️ Resize dimensions must be positive. Skipping resize.")
            return image
        return image.resize((int(width), int(height)))
    except Exception as e:
        st.warning(f"⚠️ Resize engine failed: {e}")
        return image


def compress_image(image, quality):
    """Saves the image with a quality-driven compression strategy.
    Returns (bytes, mime_type, file_extension)."""
    try:
        buffer = io.BytesIO()
        if quality >= 100:
            save_image = image
            if save_image.mode not in ("RGB", "RGBA", "L"):
                save_image = save_image.convert("RGBA")
            save_image.save(buffer, format="PNG")
            return buffer.getvalue(), "image/png", "png"
        else:
            save_image = image.convert("RGB") if image.mode != "RGB" else image
            save_image.save(buffer, format="JPEG", quality=int(quality), optimize=True)
            return buffer.getvalue(), "image/jpeg", "jpg"
    except Exception as e:
        st.warning(f"⚠️ Compression engine failed, falling back to lossless PNG: {e}")
        buffer = io.BytesIO()
        try:
            image.convert("RGB").save(buffer, format="PNG")
        except Exception:
            pass
        return buffer.getvalue(), "image/png", "png"


def generate_qr_bytes(payload, dark_color, light_color, scale=8, error="m"):
    """Builds a QR PNG from any string payload. Returns (bytes, error_message)."""
    try:
        qr = segno.make(payload, error=error)
        buffer = io.BytesIO()
        qr.save(buffer, kind="png", scale=scale, dark=dark_color, light=light_color, border=3)
        return buffer.getvalue(), None
    except Exception as e:
        return None, str(e)


# ============================================================
# MODE A: ADVANCED IMAGE STUDIO
# ============================================================
if app_mode == "🎨 Advanced Image Studio":
    st.title("🎨 Advanced Image Studio")
    st.write("Upload a photo, apply cinematic filters, crop and resize with precision, and compress your export — all live.")

    uploaded_file = st.file_uploader("📤 Choose an image file...", type=["jpg", "jpeg", "png"])

    if uploaded_file is not None:
        try:
            original_image = Image.open(uploaded_file)
            original_image.load()
        except Exception as e:
            st.error(f"⚠️ Could not read this image file: {e}")
            st.stop()

        original_bytes_size = getattr(uploaded_file, "size", None)
        if original_bytes_size is None:
            try:
                uploaded_file.seek(0)
                original_bytes_size = len(uploaded_file.read())
            except Exception:
                original_bytes_size = None

        img_width, img_height = original_image.size

        # -------------------- SIDEBAR CONTROLS --------------------
        st.sidebar.header("⚙️ Filter Control Panel")
        selected_filter = st.sidebar.selectbox(
            "Choose a Visual Filter Effect:",
            ["Original", "Black & White", "Sepia Tone", "Gaussian Blur",
             "Contour Sketch", "Vibrant Saturation", "Retro Negative", "Emboss Art"]
        )

        with st.sidebar.expander("✂️ Crop Canvas Tools", expanded=False):
            crop_top = st.number_input("Top (px)", 0, max(img_height - 1, 0), 0)
            crop_bottom = st.number_input("Bottom (px)", 0, max(img_height - 1, 0), 0)
            crop_left = st.number_input("Left (px)", 0, max(img_width - 1, 0), 0)
            crop_right = st.number_input("Right (px)", 0, max(img_width - 1, 0), 0)

        with st.sidebar.expander("📐 Resize Dimensions", expanded=False):
            maintain_ratio = st.checkbox("Maintain Aspect Ratio", value=True)
            new_width = st.number_input("Width (px)", 1, 8000, img_width)
            if maintain_ratio and img_width > 0:
                new_height = int(new_width * (img_height / img_width))
                st.caption(f"Height auto-locked to {new_height}px")
            else:
                new_height = st.number_input("Height (px)", 1, 8000, img_height)

        with st.sidebar.expander("🗜️ Compression Engine", expanded=True):
            quality = st.slider("Export Quality (1-100)", 1, 100, 85)
            st.caption("100 = lossless PNG • below 100 = optimized JPEG")

        # -------------------- PROCESSING PIPELINE --------------------
        processed_image = apply_filter(original_image, selected_filter)
        processed_image = apply_crop(processed_image, crop_top, crop_bottom, crop_left, crop_right)
        processed_image = apply_resize(processed_image, new_width, new_height)

        export_bytes, mime_type, ext = compress_image(processed_image, quality)

        # -------------------- SIDE BY SIDE DISPLAY --------------------
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("### 📸 Original Image")
            st.image(original_image, use_container_width=True)
            st.caption(f"Size: {format_bytes(original_bytes_size)} • {img_width}×{img_height}px")

        with col2:
            st.markdown(f"### ✨ {selected_filter} Result")
            st.image(processed_image, use_container_width=True)
            st.caption(
                f"Size: {format_bytes(len(export_bytes) if export_bytes else None)} • "
                f"{processed_image.size[0]}×{processed_image.size[1]}px"
            )

        # -------------------- COMPRESSION METRICS --------------------
        st.markdown("---")
        st.markdown("### 📊 Optimization Metrics")
        m1, m2, m3 = st.columns(3)
        m1.metric("Original Weight", format_bytes(original_bytes_size))
        m2.metric("Export Weight", format_bytes(len(export_bytes) if export_bytes else None))
        if original_bytes_size and export_bytes:
            delta_pct = (1 - (len(export_bytes) / original_bytes_size)) * 100
            m3.metric("Weight Reduction", f"{delta_pct:.1f}%")
        else:
            m3.metric("Weight Reduction", "N/A")

        # -------------------- DOWNLOAD --------------------
        if export_bytes:
            st.download_button(
                label="📥 Download Filtered Image",
                data=export_bytes,
                file_name=f"filtered_photo.{ext}",
                mime=mime_type
            )
        else:
            st.error("⚠️ Export pipeline could not produce a downloadable file. Try adjusting the compression quality.")
    else:
        st.info("💡 Standby: Please upload a photo file from your device to activate the image canvas filters.")


# ============================================================
# MODE B: UNIVERSAL QR ENGINE
# ============================================================
else:
    st.title("🔮 Universal QR Engine")
    st.write("Generate scannable QR codes from raw text, live web links, or embedded image payloads.")

    st.sidebar.header("🎨 QR Styling Overrides")
    dark_color = st.sidebar.color_picker("Line Color (Dark)", "#000000")
    light_color = st.sidebar.color_picker("Background Color (Light)", "#FFFFFF")

    tab_text, tab_link, tab_image = st.tabs(["📝 Text to QR", "🔗 Link to QR", "🖼️ Image to QR"])

    # -------------------- TEXT TO QR --------------------
    with tab_text:
        st.markdown("### 📝 Text to QR Pipeline")
        st.write("Encode any raw paragraph directly into a scannable matrix. Scanners will display the literal text.")
        text_payload = st.text_area("Enter your text:", height=150, key="text_payload")

        if st.button("⚡ Generate Text QR", key="gen_text_qr"):
            if not text_payload.strip():
                st.warning("⚠️ Please enter some text before generating a QR code.")
            else:
                qr_bytes, error = generate_qr_bytes(text_payload, dark_color, light_color)
                if error:
                    st.error(f"⚠️ QR generation failed: {error}")
                else:
                    st.image(qr_bytes, caption="Text QR Code", width=300)
                    st.download_button("📥 Download Text QR", data=qr_bytes,
                                        file_name="text_qr.png", mime="image/png", key="dl_text_qr")

    # -------------------- LINK TO QR --------------------
    with tab_link:
        st.markdown("### 🔗 Link to QR Pipeline")
        st.write("Encode a live website URL. Scanning devices will natively redirect to the target page.")
        url_payload = st.text_input("Enter a website URL:", placeholder="https://example.com", key="url_payload")

        if st.button("⚡ Generate Link QR", key="gen_link_qr"):
            clean_url = url_payload.strip()
            if not clean_url:
                st.warning("⚠️ Please enter a URL before generating a QR code.")
            else:
                try:
                    if not (clean_url.startswith("http://") or clean_url.startswith("https://")):
                        clean_url = "https://" + clean_url
                        st.caption(f"ℹ️ Auto-prefixed protocol → {clean_url}")
                except Exception as e:
                    st.warning(f"⚠️ Could not normalize URL: {e}")

                qr_bytes, error = generate_qr_bytes(clean_url, dark_color, light_color)
                if error:
                    st.error(f"⚠️ QR generation failed: {error}")
                else:
                    st.image(qr_bytes, caption="Link QR Code", width=300)
                    st.download_button("📥 Download Link QR", data=qr_bytes,
                                        file_name="link_qr.png", mime="image/png", key="dl_link_qr")

    # -------------------- IMAGE TO QR --------------------
    with tab_image:
        st.markdown("### 🖼️ Image to QR Pipeline")
        st.write("Convert a small image into a Base64 data-URI and embed it directly inside a high-capacity QR matrix.")
        st.caption("⚠️ QR codes have strict data limits. Use small thumbnails for reliable scanning.")

        image_file = st.file_uploader("Upload an image to embed:", type=["jpg", "jpeg", "png"], key="qr_image_upload")

        max_dim = st.slider("Max Thumbnail Dimension (px)", 32, 512, 128, key="qr_max_dim")
        embed_quality = st.slider("Embedded JPEG Quality", 10, 95, 50, key="qr_embed_quality")

        if image_file is not None:
            try:
                src_image = Image.open(image_file)
                src_image.load()
                thumb = src_image.convert("RGB").copy()
                thumb.thumbnail((max_dim, max_dim))

                thumb_buffer = io.BytesIO()
                thumb.save(thumb_buffer, format="JPEG", quality=embed_quality, optimize=True)
                b64_string = base64.b64encode(thumb_buffer.getvalue()).decode("utf-8")
                data_uri = f"data:image/jpeg;base64,{b64_string}"

                st.caption(
                    f"Encoded payload length: {len(data_uri)} characters "
                    f"(QR byte-mode ceiling ≈ 2,953 chars at low error correction)"
                )
                st.image(thumb, caption="Thumbnail to be embedded", width=150)

                if st.button("⚡ Generate Image QR", key="gen_image_qr"):
                    qr_bytes, error = generate_qr_bytes(data_uri, dark_color, light_color, scale=6, error="l")
                    if error:
                        st.error(
                            f"⚠️ Image payload is too large to fit in a QR matrix ({error}). "
                            f"Try lowering the thumbnail dimension or quality above."
                        )
                    else:
                        st.image(qr_bytes, caption="Image-Embedded QR Code", width=300)
                        st.download_button("📥 Download Image QR", data=qr_bytes,
                                            file_name="image_qr.png", mime="image/png", key="dl_image_qr")
            except Exception as e:
                st.error(f"⚠️ Could not process the uploaded image: {e}")
        else:
            st.info("💡 Standby: Upload an image to begin the Base64 embedding pipeline.")
