import streamlit as st
import socket
import qrcode
import pandas as pd
import altair as alt
from pathlib import Path
import pickle
import os

import streamlit_authenticator as stauth

st.set_page_config(
    page_title= "Dashboard Denchai-Chiengrai-Chieng Khong"
)

names = ['CKST','SRT']
usernames = ['CKST','SRT']

file_path = Path(__file__).parent / "hashed_pw.pkl"
with file_path.open("rb") as file:
    hashed_passwords = pickle.load(file)

authenticator = stauth.Authenticate(names, usernames, hashed_passwords,"streamlit app","abced", cookie_expiry_days=30)
name, authentication_status, username = authenticator.login('Login', 'sidebar')

if authentication_status == False:
    print(name,username)
    st.error('Username/password is incorrect')
elif authentication_status == None:
    st.warning('Please enter your username and password')

elif authentication_status:
    #data
    df1 = pd.read_csv('data/messages.csv')  # columns 'User ID', 'User Name', 'stage', 'Message', 'data_date'
    df2 = pd.read_excel("data/2_TEAM.xlsx",sheet_name="data", header=0)
    df3 = pd.read_excel("data/3_TEAM.xlsx",sheet_name="data", header=0)
    df = pd.concat([df2,df3])
    # Adjust sta 789+900 to keep only the first three sta 789
    df['sta'] = df['sta'].str.slice(stop=3)
    df['งานรังวัดแล้ว'] = df['งานรังวัดแล้ว'].dt.date
    df['ได้ รว.9/บันทึกถ้อยคำแล้ว'] = df['ได้ รว.9/บันทึกถ้อยคำแล้ว'].dt.date
    #df['ทำบัญชีประกาศค่าทดแทนแล้ว'] = df['ทำบัญชีประกาศค่าทดแทนแล้ว'].dt.date
    #df['ปิดประกาศ/เรียกทำสัญญาแล้ว'] = df['ปิดประกาศ/เรียกทำสัญญาแล้ว'].dt.date
    df['มาทำสัญญาแล้ว'] = df['มาทำสัญญาแล้ว'].dt.date
    df['จ่ายเงินแล้ว 75 % แล้ว งวด 1'] = df['จ่ายเงินแล้ว 75 % แล้ว งวด 1'].dt.date
    df['จ่ายเงินครบ 100%'] = df['จ่ายเงินครบ 100%'].dt.date
    df.loc[df['จ่ายเงินครบ 100%'].notnull(),'จ่ายเงินแล้ว 75 % แล้ว งวด 1'] = None # remove status 75% payment if paid 100%

    with st.sidebar:
        hostname = socket.gethostname()
        ip_address = socket.gethostbyname_ex(hostname)
        ip = []
        for address in ip_address:
            if address is not None:
                ip.append(address)

        print(ip)
        if len(ip[-1]) > 1:
            address = ip[-1][1]
        else:
            address = ip[-1]

        st.success(f"Host: {hostname}")
        URL = f'http://{address}:8501'
        #URL = f'https://5c6b-171-100-46-39.ngrok-free.app'
        img = qrcode.make(URL)
        img.save('qcode.png')
        st.image('qcode.png', width=100)

        #contract = st.selectbox(
        #    'Select Contract_: C2, C3', ('2', '3'))
        st.write(f"Specify Station (3-digits) from {df['sta'].min()} to {df['sta'].max()}")
        start_sta = st.text_input("Specify Beginning Sta.", value=df['sta'].min())
        end_sta = st.text_input("Specify Ending Sta.", value=df['sta'].max())

        # Upload Data Files
        uploaded_files = st.file_uploader("Upload File for Updating Status of Land Aquisition", accept_multiple_files=True)
        if uploaded_files is not None:
            for uploaded_file in uploaded_files:
                bytes_data = uploaded_file.read()
                st.write("filename:", uploaded_file.name)
                # Save file to data directory
                save_path = os.path.join("data", uploaded_file.name)
                with open(save_path, "wb") as f:
                    f.write(uploaded_file.getvalue())
                st.succeƒss(f"File saved to {save_path}")

    select_by_sta = (df['sta'] >= start_sta) & (df['sta'] <= end_sta)
    source = df.loc[select_by_sta]
    select_by_fin = (source['จ่ายเงินครบ 100%'].isnull())
    fin_deed_list = df[df['จ่ายเงินครบ 100%'].notnull()]['เลขแปลง'].tolist()
    land_deed_list = source['เลขแปลง'].tolist()
    remain_deed_list = [item for item in land_deed_list if item not in fin_deed_list]
    filtered_df1 = df1[df1['Message'].isin(remain_deed_list)]

    # Function to create bar plot
    def create_bar_plot(data):
        # Count non-null values in each column
        counts = data.count()

        # Create a DataFrame from the counts
        counts_df = pd.DataFrame({'Column': counts.index, 'Count': counts.values})
        # Create bar chart
        bar_chart = alt.Chart(counts_df).mark_bar().encode(
            x=alt.X('Column', sort=None),
            y='Count'
        ).properties(
            title='Count of Non-Blank Values for Each Column'
        )

        return bar_chart


    dashboard = st.container()
    with dashboard:
        st.title ("Land Aquisition Status")
        st.altair_chart(create_bar_plot(source[['เลขแปลง','งานรังวัดแล้ว','ได้ รว.9/บันทึกถ้อยคำแล้ว','ปิดประกาศ/เรียกทำสัญญาแล้ว','มาทำสัญญาแล้ว','จ่ายเงินแล้ว 75 % แล้ว งวด 1','จ่ายเงินครบ 100%']]),use_container_width=True)
        st.write(f'**รายการแปลงที่ดินทั้งหมดในช่วงที่กำหนดรวม = {source.shape[0]} แปลง**')
        df.loc[select_by_sta][['sta','เลขแปลง','เอกสารสิทธิ์','งานรังวัดแล้ว','ได้ รว.9/บันทึกถ้อยคำแล้ว','ทำบัญชีประกาศค่าทดแทนแล้ว','ปิดประกาศ/เรียกทำสัญญาแล้ว','มาทำสัญญาแล้ว','จ่ายเงินแล้ว 75 % แล้ว งวด 1','จ่ายเงินครบ 100%']]

        # Group by 'Category' column and count the occurrences in each group
        grouped_df = filtered_df1.groupby('stage').size().reset_index(name='Count')

        st.write(f"**จำนวนแปลงทั้งหมดที่เหลือค้างจ่ายในช่วงที่ระบุ = {len(remain_deed_list)} แปลง**")
        source.loc[select_by_fin][['sta','เลขแปลง','เอกสารสิทธิ์','งานรังวัดแล้ว','ได้ รว.9/บันทึกถ้อยคำแล้ว','ทำบัญชีประกาศค่าทดแทนแล้ว','ปิดประกาศ/เรียกทำสัญญาแล้ว','มาทำสัญญาแล้ว','จ่ายเงินแล้ว 75 % แล้ว งวด 1','จ่ายเงินครบ 100%']]

        st.write(f'**สรุปจำนวนที่อยู่ระหว่างดำเนินการภายใน รฟท จากที่เหลือในช่วงนี้ทั้งหมด {len(remain_deed_list)} แปลง**')
        group_filtered_df1 = filtered_df1.groupby('stage').size().reset_index(name='Count')

        st.write(group_filtered_df1)

        # Plotting the bar chart using Altair
        bar_chart = alt.Chart(grouped_df).mark_bar().encode(
            x='stage',
            y='Count'
        )

        # Streamlit app
        bar_chart
        st.write(f'**รายการละเอียดเลขที่แปลงที่ตรวจสอบแล้วโดย รฟท จากที่เหลือในช่วงนี้ทั้งหมด {len(remain_deed_list)} แปลง**')
        filtered_df1[['User Name', 'stage', 'Message', 'data_date']]
