import streamlit as st
import cv2
import os
import numpy as np
import pandas as pd
import time
from datetime import datetime
import shutil

# -------- BASE PROJECT PATH --------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

dataset = os.path.join(BASE_DIR, "dataset")

attendance_folder = os.path.join(BASE_DIR, "attendance")
database_folder = os.path.join(BASE_DIR, "database")

excel_file = os.path.join(attendance_folder, "attendance.xlsx")
face_db = os.path.join(database_folder, "face_database.csv")

os.makedirs(dataset, exist_ok=True)
os.makedirs(attendance_folder, exist_ok=True)
os.makedirs(database_folder, exist_ok=True)

if not os.path.exists(face_db):
    pd.DataFrame(columns=["ID","Name","Role"]).to_csv(face_db,index=False)



detector = cv2.CascadeClassifier(
    cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
)

recognizer = cv2.face.LBPHFaceRecognizer_create(
    radius=1,
    neighbors=8
)

faces = []
labels = []
names = {}
roles = {}

attendance = {}
detect_timer = {}
scan_time = 2
# cooldown_time = 7200   # 2 hours (in seconds)
cooldown_time = 20 # 20 seconds for testing


camera_fps = 15
frame_delay = 1 / camera_fps

cooldown = {}

# ---------------- TRAIN MODEL ---------------- #

def train():

    global faces, labels, names, roles

    faces = []
    labels = []
    names = {}
    roles = {}

    db = pd.read_csv(face_db)

    label = 0

    for _, row in db.iterrows():

        person_id = row["ID"]
        fullname = row["Name"]
        role = row["Role"]

        names[label] = fullname
        roles[label] = role

        path = os.path.join(dataset, person_id)

        if not os.path.exists(path):
            continue

        for img in os.listdir(path):

            img_path = os.path.join(path, img)
            gray = cv2.imread(img_path, 0)

            faces.append(gray)
            labels.append(label)

        label += 1

    if faces:
        recognizer.train(faces, np.array(labels))


# ---------------- FETCH REGISTERED FACES ---------------- #

def get_registered_people():

    db = pd.read_csv(face_db)

    people = []

    for _, row in db.iterrows():
        people.append((row["Name"], row["Role"]))

    return people

# ---------------- SAVE ATTENDANCE ---------------- #

def save_attendance():

    now = datetime.now()
    today = now.strftime("%Y-%m-%d")

    cutoff_in = datetime.strptime(f"{today} 15:30:00","%Y-%m-%d %H:%M:%S")
    cutoff_out = datetime.strptime(f"{today} 17:30:00","%Y-%m-%d %H:%M:%S")

    rows = []

    registered = get_registered_people()

    for name, role in registered:

        person = attendance.get(name, {
            "Name": name,
            "Role": role,
            "Time In": "",
            "Time Out": ""
        })

        status = "Pending"

        time_in = person["Time In"]
        time_out = person["Time Out"]

        if time_in and time_out:
            status = "Present"

        elif time_in and not time_out:

            in_time = datetime.strptime(
                f"{today} {time_in}",
                "%Y-%m-%d %H:%M:%S"
            )

            hours_passed = (now - in_time).total_seconds() / 3600

            if hours_passed >= 12:
                status = "Absent"

            elif now >= cutoff_out:
                status = "Absent"

            else:
                status = "Pending"

        elif not time_in:
            if now >= cutoff_in:
                status = "Absent"

        rows.append({
            "Name": person["Name"],
            "Role": person["Role"],
            "Time In": time_in,
            "Time Out": time_out,
            "Date": today,
            "Attendance": status
        })

    df = pd.DataFrame(rows)

    # ---------- EXCEL SAVE WITH HISTORY ----------

    if os.path.exists(excel_file):

        with pd.ExcelWriter(
            excel_file,
            engine="openpyxl",
            mode="a",
            if_sheet_exists="replace"
        ) as writer:

            df.to_excel(writer, index=False, sheet_name=today)

            worksheet = writer.book[today]

            for column in worksheet.columns:

                max_length = 0
                column_letter = column[0].column_letter

                for cell in column:
                    if cell.value:
                        max_length = max(max_length, len(str(cell.value)))

                worksheet.column_dimensions[column_letter].width = max_length + 3

    else:

        with pd.ExcelWriter(excel_file, engine="openpyxl") as writer:

            df.to_excel(writer, index=False, sheet_name=today)

            worksheet = writer.book[today]

            for column in worksheet.columns:

                max_length = 0
                column_letter = column[0].column_letter

                for cell in column:
                    if cell.value:
                        max_length = max(max_length, len(str(cell.value)))

                worksheet.column_dimensions[column_letter].width = max_length + 3

# ---------------- LOAD TODAY ATTENDANCE ---------------- #

def load_today_attendance():

    global attendance

    if os.path.exists(excel_file):

        df = pd.read_excel(excel_file)

        for _, row in df.iterrows():

            attendance[row["Name"]] = {
                "Name": row["Name"],
                "Role": row["Role"],
                "Time In": "" if pd.isna(row["Time In"]) else row["Time In"],
                "Time Out": "" if pd.isna(row["Time Out"]) else row["Time Out"],
                "Date": row["Date"]
            }

# ---------------- SESSION STATES ---------------- #

if "camera_on" not in st.session_state:
    st.session_state.camera_on = False

if "register_mode" not in st.session_state:
    st.session_state.register_mode = False

if "rescan_mode" not in st.session_state:
    st.session_state.rescan_mode = False


# ---------------- UI HEADER ---------------- #

st.title("AI Face Attendance System")


camera_type = st.selectbox(
    "Camera Source",
    ["Laptop Webcam", "IP Webcam"]
)

ip_url = ""

if camera_type == "IP Webcam":
    ip_url = st.text_input(
        "IP Webcam URL",
        "http://192.168.add:8080"
    )


# ---------------- START STOP BUTTONS ---------------- #

col1, col2 = st.columns(2)

with col1:
    if st.button("Start Camera"):
        st.session_state.camera_on = True

with col2:
    if st.button("Stop Camera"):
        st.session_state.camera_on = False
        if "cap" in st.session_state:
            st.session_state.cap.release()
            del st.session_state.cap


status_placeholder = st.empty()
frame_placeholder = st.empty()


# REGISTER BUTTON BELOW FRAME
register_placeholder = st.empty()

train()
load_today_attendance()


# ---------------- CAMERA STREAM ---------------- #

if st.session_state.camera_on and not st.session_state.register_mode:

    if register_placeholder.button("Register Face"):

        # switch to registration mode
        st.session_state.register_mode = True

        # stop camera completely
        if "cap" in st.session_state:
            st.session_state.cap.release()
            del st.session_state.cap

        # clear the frame
        frame_placeholder.empty()

        # stop the camera loop immediately
        st.stop()

    if "cap" not in st.session_state:

        if camera_type == "Laptop Webcam":
            st.session_state.cap = cv2.VideoCapture(0)
        else:
            st.session_state.cap = cv2.VideoCapture(ip_url + "/video")

    cap = st.session_state.cap

    while st.session_state.camera_on and not st.session_state.register_mode:

        ret, frame = cap.read()

        if not ret:
            st.warning("Camera frame not available")
            break

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        faces_detected = detector.detectMultiScale(gray,1.3,5)
        
        if len(faces_detected) == 0:
            frame_placeholder.image(frame, channels="BGR", use_container_width=True)
            time.sleep(frame_delay)
            continue
        # Block multiple faces
        if len(faces_detected) > 1:

            status_placeholder.error("Multiple faces detected - attendance blocked")

            frame_placeholder.image(frame, channels="BGR", use_container_width=True)
            time.sleep(frame_delay)
            continue

        current_name = "Unknown"
        current_role = ""

        for (x,y,w,h) in faces_detected:

            face = gray[y:y+h, x:x+w]
            face = cv2.resize(face,(200,200))

            if faces:

                label,conf = recognizer.predict(face)

                if conf < 70:
                    current_name = names[label]
                    current_role = roles[label]

            display = f"{current_name}-{current_role}" if current_name!="Unknown" else "Unknown"

            cv2.rectangle(frame,(x,y),(x+w,y+h),(0,255,0),2)

            cv2.putText(frame,display,(x,y-10),
                        cv2.FONT_HERSHEY_SIMPLEX,0.7,(0,255,0),2)

            # -------- ATTENDANCE -------- #

            if current_name != "Unknown":

                # cooldown check
                today = datetime.now().strftime("%Y-%m-%d")

                if current_name in attendance:

                    saved_time = attendance[current_name].get("Time In", "")

                    if saved_time:

                        in_time = datetime.strptime(
                            f"{today} {saved_time}",
                            "%Y-%m-%d %H:%M:%S"
                        )

                        elapsed = (datetime.now() - in_time).total_seconds()

                        if elapsed < cooldown_time:

                            remaining = int(cooldown_time - elapsed)

                            hours = remaining // 3600
                            minutes = (remaining % 3600) // 60
                            seconds = remaining % 60

                            time_format = f"{hours:02}:{minutes:02}:{seconds:02}"

                            status_placeholder.warning(
                                f"{current_name} cooldown {time_format}"
                            )

                            continue

                # start scan timer
                if current_name not in detect_timer:
                    detect_timer[current_name] = time.time()

                elif time.time() - detect_timer[current_name] >= scan_time:

                    now = datetime.now()
                    today = now.strftime("%Y-%m-%d")
                    current_time = now.strftime("%H:%M:%S")

                    if current_name not in attendance:

                        attendance[current_name] = {
                            "Name": current_name,
                            "Role": current_role,
                            "Time In": current_time,
                            "Time Out": "",
                            "Date": today
                        }

                        status_placeholder.markdown(f"## ✅ {current_name} Time In Marked")
                        
                        time.sleep(3)
                        status_placeholder.markdown("")

                    else:

                        if attendance[current_name]["Time Out"] == "":

                            attendance[current_name]["Time Out"] = current_time

                            status_placeholder.success(f"## ✅ {current_name} Time Out Marked")
                            
                            time.sleep(3)
                            status_placeholder.empty()

                        else:

                            status_placeholder.warning(
                                f"{current_name} attendance already completed"
                            )
                            time.sleep(1)
                            status_placeholder.empty()

                    detect_timer.pop(current_name, None)

                    cooldown[current_name] = time.time()

                    save_attendance()

        frame_placeholder.image(
            frame,
            channels="BGR",
            use_container_width=True
        )

        time.sleep(frame_delay)



# ---------------- REGISTRATION FORM ---------------- #

if st.session_state.register_mode:

    st.subheader("Register New Face")

    fullname_input = st.text_input("Full Name")

    role = st.radio(
        "Role",
        ["student","teacher"],
        horizontal=True
    )

    # Buttons
    col1, col2, col3 = st.columns([2,2,2])

    with col2:
        submit = st.button("Submit Registration")

    with col3:
        cancel = st.button("Cancel")

    # Cancel
    # Cancel
    if cancel:

        # stop camera completely
        if "cap" in st.session_state:
            st.session_state.cap.release()
            del st.session_state.cap

        # reset camera state
        st.session_state.camera_on = False

        frame_placeholder.empty()

        st.session_state.register_mode = False

        st.rerun()

    # Submit
    if submit:

        # Check mandatory field
        if not fullname_input.strip():
            st.warning("⚠ Full name is mandatory")
            st.stop()

        parts = fullname_input.strip().split()

        if len(parts) < 2:
            st.warning("⚠ Please enter at least First and Last name")
            st.stop()

        first = parts[0]
        last = parts[-1]

        # Middle initial if exists
        middle = ""

        if len(parts) > 2:
            middle = parts[1][0].upper()

        # Build folder name
        if middle:
            fullname = f"{first.capitalize()} {middle} {last.capitalize()}"
        else:
            fullname = f"{first.capitalize()} {last.capitalize()}"

        db = pd.read_csv(face_db)

        if role == "student":
            count = len(db[db["Role"]=="student"]) + 1
            new_id = f"ID_{count:03}"

        else:
            count = len(db[db["Role"]=="teacher"]) + 1
            new_id = f"T_{count:03}"

        folder = new_id

        path = os.path.join(dataset, folder)
        
        

        if not os.path.exists(path):
            os.makedirs(path)

        if "cap" in st.session_state:
            st.session_state.cap.release()

        cap = cv2.VideoCapture(0)

        count = 0

        progress_placeholder = st.empty()

        while count < 25:

            progress_placeholder.markdown(
                f"### Images captured: {count} / 25"
            )

            ret, frame = cap.read()

            if not ret:
                continue

            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            gray = cv2.equalizeHist(gray)

            faces_reg = detector.detectMultiScale(gray,1.3,5)

            # -------- DUPLICATE FACE CHECK --------
            if faces:

                for (x,y,w,h) in faces_reg:

                    face_test = gray[y:y+h, x:x+w]
                    face_test = cv2.resize(face_test,(200,200))

                    label,conf = recognizer.predict(face_test)

                    if conf < 60:

                        existing_name = names[label]
                        existing_role = roles[label]
                        
                        st.error(f"⚠ Face already registered as {existing_name} as a {existing_role}")

                        cap.release()

                        st.session_state.register_mode = False

                        st.stop()

            # Block multiple faces
            if len(faces_reg) > 1:
                st.warning("Multiple faces detected - registration blocked")
                continue

            if len(faces_reg) == 0:
                continue

            for (x,y,w,h) in faces_reg:

                frame_h, frame_w = gray.shape

                # ---- FACE SIZE CHECK ----
                if w < 120 or h < 120:
                    st.warning("Move closer to the camera")
                    continue

                # ---- FACE CENTER CHECK ----
                face_center_x = x + w/2
                frame_center_x = frame_w/2

                if abs(face_center_x - frame_center_x) > frame_w * 0.25:
                    st.warning("Center your face")
                    continue

                # ---- SAVE FACE ----
                face = gray[y:y+h, x:x+w]
                face = cv2.resize(face,(200,200))

                cv2.imwrite(f"{path}/{count}.jpg",face)

                count += 1

                break

        cap.release()

        db.loc[len(db)] = [new_id, fullname, role]
        db.to_csv(face_db,index=False)
        
        train()

        st.success("Registration Successful")

        st.session_state.register_mode = False
        st.rerun()
