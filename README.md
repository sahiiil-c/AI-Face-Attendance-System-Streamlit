# AI Face Attendance System

A **Streamlit-based AI Face Recognition Attendance System** that automatically records attendance using computer vision.

This project allows:

* Face registration for **students and teachers**
* Automatic **face recognition attendance**
* **Excel-based attendance records**
* **Student login portal**
* **Teacher dashboard with analytics**
* **Auto installation of required Python libraries**

---
# Works better with vs code
##Official VS code Download link

[Official VS code Download Page](https://code.visualstudio.com/download)

[VS code direct download for windows](https://code.visualstudio.com/sha/download?build=stable&os=win32-x64-user)

---
# Project Structure

```
AI_Face_Attendance_System/
│
├── ai_face_attendance_system_st.py      # Face recognition & attendance system
├── User_login_st.py                     # Student & teacher dashboard
├── Auto_libraries_importer.py           # Auto installs required libraries
│
├── dataset/                             # Stores face images for each user
│
├── attendance/
│   └── attendance.xlsx                  # Attendance records by date
│
└── database/
    ├── face_database.csv                # Registered users
    ├── teacher_database.csv             # Teacher login credentials
    └── active_sessions.csv              # Active login sessions
```

---

# Requirements

* Python **3.8+**
* Webcam or IP Camera
* Windows / Linux / Mac

---

# Install Dependencies

Run the auto installer before running the system.

```
python Auto_libraries_importer.py
```

This will automatically install:

* streamlit
* opencv-python
* numpy
* pandas
* openpyxl
* matplotlib
* seaborn

---

# How to Run the Face Attendance System

Run the face recognition system:

```
streamlit run ai_face_attendance_system_st.py
```

Features:

* Face detection using OpenCV
* Automatic attendance marking
* Time In / Time Out recording
* Face registration
* Duplicate face prevention
* Multi-face detection blocking
* Attendance saved to Excel

---

# How to Run the Login Portal

Run the dashboard system:

```
streamlit run User_login_st.py
```

Features:

* Student login using **Student ID**
* Teacher login using **username and password**
* Attendance analytics
* Charts and reports
* Student attendance records

---

# Default Login Credentials

### Teacher Login

```
Username: teacher
Password: admin123
```

### Student Login

Use the **Student ID generated during face registration**

Example:

```
ID_001
```

---

# How Face Registration Works

1. Click **Register Face** in the camera interface
2. Enter:

   * Full name
   * Role (student or teacher)
3. The system captures **25 face images**
4. Images are stored inside:

```
dataset/ID_xxx/
```

5. The model retrains automatically

---

# Attendance Logic

The system records:

| Field      | Description                |
| ---------- | -------------------------- |
| Name       | Person name                |
| Role       | Student / Teacher          |
| Time In    | First detection            |
| Time Out   | Second detection           |
| Date       | Attendance date            |
| Attendance | Present / Pending / Absent |

Attendance is stored inside:

```
attendance/attendance.xlsx
```

Each **day becomes a separate sheet**.

---

# Features

* Face recognition attendance
* Duplicate face detection prevention
* Face alignment checks
* Cooldown timer between scans
* Student login system
* Teacher analytics dashboard
* Excel attendance storage
* Automatic library installer
* Multi-face detection blocking

---

# Security Features

* Prevents duplicate face registrations
* Blocks multiple faces during attendance
* Session control for login portal
* Attendance cooldown timer

---

# Technologies Used

* Python
* Streamlit
* OpenCV
* NumPy
* Pandas
* Matplotlib
* Seaborn

---

# Future Improvements

Possible upgrades:

* Real-time database (Firebase / SQL)
* Mobile camera integration
* Cloud deployment
* Face mask detection
* Live attendance notifications
* Calendar view for attendance

---

# Guide to run the code - No python method
## Install Python and pip (Windows)

If Python is not installed on your computer, follow these steps.

## Step 1 — Download Python

Download Python from the official website:

**Python Official Downloads Page**
https://www.python.org/downloads/windows/

Direct installer links:

### Windows 64-bit

[Download python for windows 64 bit](https://www.python.org/ftp/python/3.12.2/python-3.12.2-amd64.exe)

### Windows 32-bit

[Download python for windows 64 bit](https://www.python.org/ftp/python/3.12.2/python-3.12.2.exe)

Download the correct version for your system.

---

## Step 2 — Install Python

1. Run the downloaded installer.
2. Check the option:

```
Add Python to PATH
```

3. Click:

```
Install Now
```

This installs both **Python and pip automatically**.

---

## Step 3 — Verify Installation

Open **Command Prompt** and run:

```
python --version
```

Example output:

```
Python 3.12.2
```

Then verify pip:

```
pip --version
```

Example output:

```
pip 23.x from ...
```

---

## Step 4 — Upgrade pip (Recommended)

Run:

```
python -m pip install --upgrade pip
```

---

## Step 5 — Install Project Dependencies

Navigate to the project folder and run:

```
python Auto_libraries_importer.py
```

This will automatically install all required libraries for the project.

---

## Check if Python is 32-bit or 64-bit

Run this command:

```
python
```

You will see something like:

```
Python 3.12.2 (tags/v3.12.2:...) [MSC v.1937 64 bit (AMD64)]
```

or

```
32 bit
```

This tells you your Python architecture.




---
# Author

**Sahil Chavan**

Artificial Intelligence & Machine Learning Engineering Student

---

# License

This project is open source and available under the **MIT License**.
