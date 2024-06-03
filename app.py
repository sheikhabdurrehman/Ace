# Python In-built packages
from pathlib import Path
import PIL
import pandas as pd
import tempfile
import os
# External packages
import streamlit as st
import subprocess

# Local Modules
import settings
import helper
import database

# Setting page layout
st.set_page_config(
    page_title="Inventory Management using YOLOv8",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Main page heading
st.title("Autonomous Customer Experience")

# Sidebar
st.sidebar.header("ML Model Config")

# Model Options
# model_type = st.sidebar.radio(
#     "Select Task", ['Detection'])

confidence = float(st.sidebar.slider(
    "Select Model Confidence", 25, 100, 40)) / 100

# Selecting Detection Or Segmentation
# if model_type == 'Detection':
model_path = Path(settings.DETECTION_MODEL)

# Load Pre-trained ML Model
try:
    model = helper.load_model(model_path)
except Exception as ex:
    st.error(f"Unable to load model. Check the specified path: {model_path}")
    st.error(ex)

names = []
# Get model classes
classes = model.names
for value in classes:
    names.append(classes[value])

# Create the dictionary to store detection counts
detection_counts = {cls: 0 for cls in names}

def update_detection_counts(boxes):
    for box in boxes:
        label = box.label
        if label in detection_counts:
            detection_counts[label] += 1

st.sidebar.header("Image/Video Config")
source_radio = st.sidebar.radio(
    "Select Source", settings.SOURCES_LIST)

source_img = None
source_vid = None

st.sidebar.header("Inventory Stock Status")
stock_alert = st.sidebar.empty()
stock_table = st.sidebar.empty()
# Function to retrieve and display item counts from the database
def display_inventory_counts(stock_table):
    try:
        inventory_counts = database.data_updates()
        stock_table.empty()
        stock_table.table(inventory_counts)
    except Exception as ex:
        st.sidebar.error("Error retrieving inventory counts.")
        st.sidebar.error(ex)


# Call the function to display inventory counts
display_inventory_counts(stock_table)


# If image is selected
if source_radio == settings.IMAGE:
    source_img = st.sidebar.file_uploader(
        "Choose an image...", type=("jpg", "jpeg", "png", 'bmp', 'webp'))

    col1, col2 = st.columns(2)

    with col1:
        try:
            if source_img is None:
                default_image_path = str(settings.DEFAULT_IMAGE)
                default_image = PIL.Image.open(default_image_path)
                st.image(default_image_path, caption="Default Image",
                         use_column_width=True)
            else:
                uploaded_image = PIL.Image.open(source_img)
                st.image(source_img, caption="Uploaded Image",
                         use_column_width=True)
        except Exception as ex:
            st.error("Error occurred while opening the image.")
            st.error(ex)

    with col2:
        if source_img is None:
            default_detected_image_path = str(settings.DEFAULT_DETECT_IMAGE)
            default_detected_image = PIL.Image.open(
                default_detected_image_path)
            st.image(default_detected_image_path, caption='Detected Image',
                     use_column_width=True)
        else:
            if st.sidebar.button('Detect Objects'):
                res = model.predict(uploaded_image, conf=confidence)
                # print(res)
                boxes = res[0].boxes
                res_plotted = res[0].plot()[:, :, ::-1]
                st.image(res_plotted, caption='Detected Image', use_column_width=True)
                data = res[0]
                count_tensor = data.boxes.cls
                for value in data.boxes.cls:
                    class_index = int(value)
                    object_name =  model.names[class_index]
                    detection_counts[object_name]+=1
                try:
                    st.write("Detection Results")
                    # st.write("Detection counts:", detection_counts)
                    df = pd.DataFrame(list(detection_counts.items()), columns=['Product', 'Count'])
                    st.table(df)
                except Exception as ex:
                    print("", ex)
                    st.write("No image is uploaded yet!")

elif source_radio == settings.VIDEO:
    source_vid = st.sidebar.file_uploader(
        "Choose a video...", type=("mp4", "avi", "mov", "mkv"))
    if source_vid is None:
        video_path = r"videos\video_3.mp4"
        st.video(data=video_path, start_time=0, subtitles=None, end_time=None, loop=True, autoplay=True, muted=True)
    if source_vid is not None:
        print("Video File is ", source_vid)
        width = 100
        side = 70

        # _, container, _ = st.columns([side, width, side])
        # container.video(data=source_vid, start_time=0, subtitles=None, end_time=None, loop=True, autoplay=True, muted=True)
        # container.video(data=source_vid, start_time=0, subtitles=None, end_time=None, loop=True, autoplay=True, muted=True)

        col1, col2 = st.columns(2)
        # Display the first video in the first column
        col1.video(data=source_vid, start_time=0, subtitles=None, end_time=None, loop=True, autoplay=True, muted=True)
        # Display the second video in the second column

        if st.sidebar.button('Detect Objects'):
            # col2.video(data=r"videos/loading_video.mp4", start_time=0, subtitles=None, end_time=None, loop=True, autoplay=True, muted=True)
            helper.play_uploaded_video(confidence, model, source_vid, col2,  stock_table, stock_alert)
            # res = model.predict(source_vid, conf=confidence, stream=True)

elif source_radio == settings.WEBCAM:
    video_path = r"videos\video_3.mp4"
    helper.play_webcam(confidence, model, stock_table, stock_alert)

else:
    st.error("Please select a valid source type!")

