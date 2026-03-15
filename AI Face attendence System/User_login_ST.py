import streamlit as st
import pandas as pd
import os
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime

# -------- BASE PROJECT PATH --------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

attendance_file = os.path.join(BASE_DIR, "attendance", "attendance.xlsx")
face_db = os.path.join(BASE_DIR, "database", "face_database.csv")
session_file = os.path.join(BASE_DIR, "database", "active_sessions.csv")

st.title("Attendance Portal")

# ---------------- SESSION STATES ---------------- #

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "user_role" not in st.session_state:
    st.session_state.user_role = None

if "user_name" not in st.session_state:
    st.session_state.user_name = None

if "user_id" not in st.session_state:
    st.session_state.user_id = None

# ---------------- LOGOUT BUTTON ---------------- #

if st.session_state.logged_in:

    col1, col2 = st.columns([8,2])

    with col2:
        if st.button("🔓 Logout", use_container_width=True):

            if os.path.exists(session_file):
                sessions = pd.read_csv(session_file)
                sessions = sessions[sessions["ID"] != st.session_state.user_id]
                sessions.to_csv(session_file, index=False)

            st.session_state.logged_in = False
            st.session_state.user_role = None
            st.session_state.user_name = None
            st.session_state.user_id = None

            st.rerun()


# ---------------- LOGIN SCREEN ---------------- #

if not st.session_state.logged_in:

    role = st.selectbox("Login As", ["Student", "Teacher"])

    # -------- STUDENT LOGIN -------- #

    if role == "Student":

        student_id = st.text_input("Enter Student ID (Example: ID_001)").strip()

        if st.button("Login"):

            db = pd.read_csv(face_db)

            student = db[db["ID"].str.lower() == student_id.lower()]

            if student.empty:
                st.error("Invalid ID")

            else:

                # load active sessions
                if os.path.exists(session_file):
                    sessions = pd.read_csv(session_file)

                    # ----- AUTO SESSION CLEANUP -----
                    sessions["LoginTime"] = pd.to_datetime(sessions["LoginTime"])

                    timeout_minutes = 1
                    now = datetime.now()

                    # calculate remaining time
                    sessions["RemainingSeconds"] = (
                        timeout_minutes * 60 - (now - sessions["LoginTime"]).dt.total_seconds()
                    )

                    # keep only valid sessions
                    sessions = sessions[sessions["RemainingSeconds"] > 0]

                    sessions.to_csv(session_file, index=False)

                    # -------- SHOW COUNTDOWN --------
                    if not sessions.empty:
                        remaining = int(sessions.iloc[0]["RemainingSeconds"])
                        minutes = remaining // 60
                        seconds = remaining % 60

                        st.warning(f"Session expires in {minutes:02}:{seconds:02}")

                else:
                    sessions = pd.DataFrame(columns=["ID","LoginTime"])

                if student_id.lower() in sessions["ID"].str.lower().values:
                    st.warning("This student is already logged in from another device")

                else:

                    name = student.iloc[0]["Name"]

                    new_session = pd.DataFrame({
                        "ID": [student.iloc[0]["ID"]],
                        "LoginTime": [datetime.now()]
                    })

                    sessions = pd.concat([sessions, new_session], ignore_index=True)
                    sessions.to_csv(session_file, index=False)

                    st.session_state.logged_in = True
                    st.session_state.user_role = "Student"
                    st.session_state.user_name = name
                    st.session_state.user_id = student_id

                    st.rerun()

    # -------- TEACHER LOGIN -------- #

    if role == "Teacher":

        username = st.text_input("Username").lower().strip()
        password = st.text_input("Password", type="password").strip()

        
        if st.button("Login"):

            # Default admin teacher (keep existing login)
            if username.lower() == "teacher" and password == "admin123":

                st.session_state.logged_in = True
                st.session_state.user_role = "Teacher"
                st.session_state.user_name = "Teacher"
                st.session_state.user_id = "T_ADMIN"

                st.rerun()

            else:

                teacher_db_file = os.path.join(BASE_DIR, "database", "teacher_database.csv")

                if os.path.exists(teacher_db_file):

                    tdb = pd.read_csv(teacher_db_file)

                    teacher = tdb[
                        (tdb["Username"].str.lower() == username.lower()) &
                        (tdb["Password"] == password)
                    ]

                    if teacher.empty:
                        st.error("Invalid credentials")

                    else:

                        st.session_state.logged_in = True
                        st.session_state.user_role = "Teacher"
                        st.session_state.user_name = teacher.iloc[0]["Name"]
                        st.session_state.user_id = teacher.iloc[0]["TeacherID"]

                        st.rerun()

                else:
                    st.error("Teacher database not found")


# ---------------- DASHBOARD ---------------- #

if st.session_state.logged_in:

    role = st.session_state.user_role
    name = st.session_state.user_name

    st.success(f"Welcome {name}")

    if os.path.exists(attendance_file):

        xl = pd.ExcelFile(attendance_file)

        all_data = []
        for sheet in xl.sheet_names:
            df = xl.parse(sheet)
            all_data.append(df)

        df = pd.concat(all_data, ignore_index=True)

        df["Date"] = pd.to_datetime(df["Date"])

        current_month = datetime.now().month
        current_year = datetime.now().year

        df_month = df[
            (df["Date"].dt.month == current_month) &
            (df["Date"].dt.year == current_year)
        ]


        # ---------------- STUDENT DASHBOARD ---------------- #

        if role == "Student":

            student_data = df_month[df_month["Name"] == name]

            present = (student_data["Attendance"] == "Present").sum()
            absent = (student_data["Attendance"] == "Absent").sum()
            pending = (student_data["Attendance"] == "Pending").sum()

            total = present + absent + pending

            percentage = round((present / total) * 100, 2) if total > 0 else 0

            # -------- METRICS -------- #

            c1, c2, c3, c4 = st.columns(4)

            c1.metric("Present", present)
            c2.metric("Absent", absent)
            c3.metric("Pending", pending)
            c4.metric("Attendance %", f"{percentage}%")

            st.divider()


            # -------- LIVE ATTENDANCE FEED -------- #

            st.subheader("Live Attendance Feed")

            recent = df.sort_values("Date", ascending=False).head(10)

            for _, row in recent.iterrows():

                status = row["Attendance"]
                student = row["Name"]
                time = datetime.strptime(row["Time In"], "%H:%M:%S").strftime("%I:%M %p")

                if status == "Present":
                    st.markdown(f"🟢 **{student}** marked Present — {time}")

                elif status == "Absent":
                    st.markdown(f"🔴 **{student}** marked Absent — {time}")

                else:
                    st.markdown(f"🟡 **{student}** Pending — {time}")
            
            # -------- CHARTS SIDE BY SIDE -------- #

            chart1, chart2 = st.columns(2)

            # BAR CHART
            with chart1:

                chart_data = pd.DataFrame({
                    "Status": ["Present", "Absent", "Pending"],
                    "Days": [present, absent, pending]
                })

                fig, ax = plt.subplots()

                sns.barplot(
                    data=chart_data,
                    x="Status",
                    y="Days",
                    ax=ax
                )

                ax.set_title("Monthly Attendance")
                ax.set_xlabel("Status")
                ax.set_ylabel("Days")

                st.pyplot(fig)

            # PIE CHART
            with chart2:

                values = [present, absent, pending]
                labels = ["Present", "Absent", "Pending"]

                filtered_values = []
                filtered_labels = []

                for v, l in zip(values, labels):
                    if v > 0:
                        filtered_values.append(v)
                        filtered_labels.append(l)

                fig2, ax2 = plt.subplots()

                ax2.pie(
                    filtered_values,
                    labels=filtered_labels,
                    autopct="%1.1f%%",
                    startangle=90
                )

                ax2.axis("equal")

                st.pyplot(fig2)

            st.subheader("Attendance Records")
            st.dataframe(student_data, use_container_width=True)


        # ---------------- TEACHER DASHBOARD ---------------- #

        if role == "Teacher":

            st.header("📊 Teacher Dashboard")

            tab1, tab2, tab3 = st.tabs([
                "👨‍🏫 My Attendance",
                "📊 Class Overview",
                "🎓 Student Records"
            ])

            # ---------------- TEACHER PERSONAL ATTENDANCE ---------------- #

            with tab1:

                st.subheader("My Attendance Overview")

                teacher_data = df_month[
                    (df_month["Name"] == name) &
                    (df_month["Role"] == "teacher")
                ]

                if teacher_data.empty:

                    st.warning("No attendance records found for this month.")

                else:

                    present = (teacher_data["Attendance"] == "Present").sum()
                    absent = (teacher_data["Attendance"] == "Absent").sum()
                    pending = (teacher_data["Attendance"] == "Pending").sum()

                    c1, c2, c3 = st.columns(3)

                    c1.metric("Present", present)
                    c2.metric("Absent", absent)
                    c3.metric("Pending", pending)

                    st.divider()

                    st.subheader("My Attendance Records")
                    st.dataframe(teacher_data, use_container_width=True)

                    st.divider()

                    chart1, chart2 = st.columns(2)

                    with chart1:

                        st.subheader("Attendance Distribution")

                        chart_data = pd.DataFrame({
                            "Status": ["Present", "Absent", "Pending"],
                            "Days": [present, absent, pending]
                        })

                        fig, ax = plt.subplots()

                        sns.barplot(
                            data=chart_data,
                            x="Status",
                            y="Days",
                            ax=ax
                        )
                        
                        
                        ax.set_ylim(0, 31)
                        ax.set_xlabel("Attendance Status")
                        ax.set_ylabel("Days in Month")
                        ax.set_title("Monthly Attendance")
                        
                        st.pyplot(fig)

                    with chart2:

                        st.subheader("Attendance Summary")

                        summary = teacher_data.groupby("Attendance").size()

                        fig2, ax2 = plt.subplots()

                        summary.plot(
                            kind="bar",
                            ax=ax2
                        )

                        st.pyplot(fig2)

            with tab3:

                st.subheader("Student Attendance Records")

                student_data = df_month[df_month["Role"] == "student"]

                if student_data.empty:

                    st.warning("No student records available.")

                else:

                    present = (student_data["Attendance"] == "Present").sum()
                    absent = (student_data["Attendance"] == "Absent").sum()
                    pending = (student_data["Attendance"] == "Pending").sum()

                    c1, c2, c3 = st.columns(3)

                    c1.metric("Present", present)
                    c2.metric("Absent", absent)
                    c3.metric("Pending", pending)

                    st.divider()

                    st.subheader("All Student Records")
                    st.dataframe(student_data, use_container_width=True)

                    st.divider()

                    chart1, chart2 = st.columns(2)

                    with chart1:

                        st.subheader("Attendance Distribution")

                        chart_data = pd.DataFrame({
                            "Status": ["Present", "Absent", "Pending"],
                            "Days": [present, absent, pending]
                        })

                        fig, ax = plt.subplots()

                        sns.barplot(
                            data=chart_data,
                            x="Status",
                            y="Days",
                            ax=ax
                        )

                        ax.set_ylim(0, 31)
                        ax.set_xlabel("Attendance Status")
                        ax.set_ylabel("Days in Month")
                        ax.set_title("Monthly Attendance")

                        st.pyplot(fig)

                    with chart2:

                        st.subheader("Student Attendance Count")

                        student_summary = student_data.groupby("Name")["Attendance"].value_counts().unstack().fillna(0)

                        fig2, ax2 = plt.subplots()

                        student_summary.plot(
                            kind="bar",
                            stacked=True,
                            ax=ax2
                        )

                        st.pyplot(fig2)

            with tab2:

                st.subheader("Student Attendance Overview")

                present = (df_month["Attendance"] == "Present").sum()
                absent = (df_month["Attendance"] == "Absent").sum()
                pending = (df_month["Attendance"] == "Pending").sum()

                c1, c2, c3 = st.columns(3)

                c1.metric("Present", present)
                c2.metric("Absent", absent)
                c3.metric("Pending", pending)

                st.divider()

                st.subheader("All Student Attendance")

                st.dataframe(df_month, use_container_width=True)

                st.divider()

                chart1, chart2 = st.columns(2)

                # Attendance Distribution
                with chart1:

                        st.subheader("Attendance Distribution")

                        chart_data = pd.DataFrame({
                            "Status": ["Present", "Absent", "Pending"],
                            "Days": [present, absent, pending]
                        })

                        fig, ax = plt.subplots()

                        sns.barplot(
                            data=chart_data,
                            x="Status",
                            y="Days",
                            ax=ax
                        )

                        ax.set_ylim(0, 31)
                        ax.set_xlabel("Attendance Status")
                        ax.set_ylabel("Days in Month")
                        ax.set_title("Monthly Attendance")

                        st.pyplot(fig)

                # Student-wise Summary
                with chart2:

                    st.subheader("Student Attendance Count")

                    student_summary = df_month.groupby("Name")["Attendance"].value_counts().unstack().fillna(0)

                    fig2, ax2 = plt.subplots()

                    student_summary.plot(
                        kind="bar",
                        stacked=True,
                        ax=ax2
                    )

                    st.pyplot(fig2)