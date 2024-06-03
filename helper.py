from ultralytics import YOLO
import time
import streamlit as st
import cv2
import tempfile
from collections import defaultdict
import settings
import subprocess
import os
import pandas as pd
from datetime import datetime
import database


inventory = defaultdict(lambda: {"total": 0, "current": 0})
live_count = defaultdict(int)

names = []

def load_model(model_path):
    model = YOLO(model_path)
    # Get model classes
    classes = model.names
    if len(names)<1:
        for value in classes:
            names.append(classes[value])
    return model

def reduce_fps(input_video_path, output_video_path, fps=3):
    # Use ffmpeg to reduce FPS
    command = [
        'ffmpeg', '-i', input_video_path, '-filter:v', f'fps=fps={fps}',
        output_video_path, '-y'
    ]
    subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

def show_alert(alerter, item):
    alerter.error(f"{item} is out of stock!")


def display_tracker_options():
    return True, "bytetrack.yaml"


def _display_detected_frames(conf, model, st_frame, image, is_display_tracking=None, tracker=None):

    # image = cv2.resize(image, (720, int(720*(9/16))))
    # Create the dictionary to store detection counts
    detection_counts = {cls: 0 for cls in names}
    
    if is_display_tracking:
        res = model.track(image, conf=conf, persist=True, tracker=tracker)
    else:
        res = model.predict(image, conf=conf)
    res_plotted = res[0].plot()

    st_frame.image(res_plotted, caption='🔵 Live Model Predictions', channels="BGR", use_column_width=True)
    boxes = res[0].boxes
    res_plotted = res[0].plot()[:, :, ::-1]
    # st.image(res_plotted, caption='Detected Image', use_column_width=True)
    data = res[0]
    count_tensor = data.boxes.cls
    for value in data.boxes.cls:
        class_index = int(value)
        object_name =  model.names[class_index]
        detection_counts[object_name]+=1
    try:
        df = pd.DataFrame(list(detection_counts.items()), columns=['Product', 'Count'])
        print(df.head())
        return df
    except Exception as ex:
        print("", ex)
        return None

def display_inventory_counts(stock_table, video={}):
    try:
        if video == {}:
            inventory_counts = database.data_updates()
        else:
            inventory_counts = database.data_updates(custom_row=video)
        stock_table.empty()
        stock_table.table(inventory_counts)
        # Filter the names where Counts is less than Minimum
        low_count_items = inventory_counts[inventory_counts['Counts'] < inventory_counts['Threshold']]['Name'].tolist()
        return low_count_items
    except Exception as ex:
        st.sidebar.error("Error retrieving inventory counts.")
        st.sidebar.error(ex)


def play_webcam(conf, model, stock_table, stock_alert):
    col1, col2 = st.columns(2)
    video_df = []
    video_df = pd.DataFrame(columns=["Frame_Timestamp"]+names)
    print("video_df")
    print(video_df)
    source_webcam = settings.WEBCAM_PATH
    is_display_tracker, tracker = display_tracker_options()
    if st.sidebar.button('Detect Objects'):
        try:
            vid_cap = cv2.VideoCapture(source_webcam)
            if not vid_cap.isOpened():
                st.sidebar.error("Error opening video source")
                return
            live_frame = col1.empty()
            detected_frame = col2.empty()

            table_placeholder = st.empty()
            while vid_cap.isOpened():
                success, image = vid_cap.read()
                if not success:
                    vid_cap.release()
                    break
                # live_frame.empty()
                # Display live video in the first column
                live_frame.image(image,caption="🔴 Live Camera Feed", channels="BGR")

                # Process the frame and display detected video in the second column
                df = _display_detected_frames(conf, model, detected_frame, image, is_display_tracker, tracker)
                print(df)
                if df is not None:
                    df1_dict = df.set_index('Product').to_dict()['Count']
                    # Create a DataFrame from the dictionary with appropriate columns
                    new_row = pd.DataFrame([df1_dict])
                    print("new_row")
                    # Adding a placeholder for 'FrameNo' in new_row with value 0 or any other suitable value
                    new_row.insert(0, 'Frame_Timestamp', [datetime.now()])
                    print(new_row)
                    database.create_and_append_to_warehouse_rack(new_row)
                    # Append the new row to video_df
                    video_df = pd.concat([video_df, new_row], ignore_index=True)
                    # Update the table in Streamlit
                    table_placeholder.table(video_df.tail(10)[::-1])
                    low_count_items = display_inventory_counts(stock_table)
                    stock_alert.empty()
                    if low_count_items != [] or low_count_items != None:
                        names_string = ', '.join(low_count_items)
                        show_alert(stock_alert, names_string)
                # Wait a bit before the next frame
                cv2.waitKey(1)
        except Exception as e:
            st.sidebar.error("Error loading video: " + str(e))
    else:
        video_path = r"videos\video_3.mp4"
        st.video(data=video_path, start_time=0, subtitles=None, end_time=None, loop=True, autoplay=True, muted=True)

def play_uploaded_video(conf, model, source_vid, col2, stock_table, stock_alert):
    is_display_tracker, tracker = display_tracker_options()
    # Create a placeholder for the table
    table_placeholder = st.empty()
    if source_vid is not None:
        video_df = []
        video_df = pd.DataFrame(columns=["FrameNo"]+names)
        print("video_df")
        print(video_df)
         # Write the uploaded video to a temporary file
        input_tfile = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4')
        input_tfile.write(source_vid.read())
        input_tfile.close()
        
        # Create a temporary file for the output video with reduced FPS
        output_tfile = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4')
        output_tfile.close()

        # Reduce the FPS of the input video
        reduce_fps(input_tfile.name, output_tfile.name, fps=1)

        # Use the video with reduced FPS for processing
        vid_cap = cv2.VideoCapture(output_tfile.name)
        st_frame = col2.empty()
        counter = 0
        while vid_cap.isOpened():
            success, image = vid_cap.read()
            if success:
                counter+=1
                df = _display_detected_frames(conf, model, st_frame, image, is_display_tracker, tracker)
                print(counter)
                if df is not None:
                    df1_dict = df.set_index('Product').to_dict()['Count']
                    # Create a DataFrame from the dictionary with appropriate columns
                    new_row = pd.DataFrame([df1_dict])
                    print("new_row")
                    frames_items_dict = new_row.to_dict(orient='records')[0]
                    print(frames_items_dict)
                    print(new_row)

                    # Adding a placeholder for 'FrameNo' in new_row with value 0 or any other suitable value
                    new_row.insert(0, 'FrameNo', counter)
                    
                    # Append the new row to video_df
                    video_df = pd.concat([video_df, new_row], ignore_index=True)
                    # Update the table in Streamlit
                    table_placeholder.table(video_df)
                    low_count_items = display_inventory_counts(stock_table, frames_items_dict)
                    stock_alert.empty()
                    if low_count_items != [] or low_count_items != None:
                        names_string = ', '.join(low_count_items)
                        show_alert(stock_alert, names_string)
                    # Wait for a while before the next update (for demonstration purposes)
                    # time.sleep(1)
            else:
                vid_cap.release()
                break
