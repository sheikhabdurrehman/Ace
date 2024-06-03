import streamlit as st

# Function to show a notification alert at the top right of the page
def show_notification(message, alert_type='info'):
    if alert_type == 'info':
        st.sidebar.info(message)
    elif alert_type == 'success':
        st.sidebar.success(message)
    elif alert_type == 'warning':
        st.sidebar.warning(message)
    elif alert_type == 'error':
        st.sidebar.error(message)

# Example usage of the notification function
show_notification("This is an informational alert!", "info")

st.title("Streamlit Notification Alert Example")
st.write("This page demonstrates how to show a notification alert at the top right.")

# Add more content to the page
st.write("You can add more content to your Streamlit app here.")
