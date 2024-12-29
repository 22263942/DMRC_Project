import cv2
import face_recognition
import pandas as pd
import pyttsx3
import numpy as np
import os
from tkinter import Tk, Label, Button, Entry, StringVar, IntVar, messagebox
from tkinter import PhotoImage, Canvas

# Initialize the Text-to-Speech engine
engine = pyttsx3.init()

# Load or create the passenger database (Excel file)
DATABASE_FILE = r"passenger_database.xlsx"

try:
    passenger_df = pd.read_excel(DATABASE_FILE)
except FileNotFoundError:
    passenger_df = pd.DataFrame(columns=["Name", "ID", "My Balance", "Photo"])
    passenger_df.to_excel(DATABASE_FILE, index=False)

def register_passenger(name, passenger_id, balance, photo_path):
    global passenger_df

    if passenger_df.empty:
        passenger_df = pd.DataFrame(columns=["Name", "ID", "My Balance", "Photo"])

    passenger_df.loc[len(passenger_df)] = [name, passenger_id, balance, photo_path]
    passenger_df.to_excel(DATABASE_FILE, index=False)

def detect_face():
    cap = cv2.VideoCapture(0)

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        faces = face_recognition.face_locations(rgb_frame)
        face_encodings = face_recognition.face_encodings(rgb_frame, faces)

        if not face_encodings:
            continue

        for (top, right, bottom, left), face_encoding in zip(faces, face_encodings):
            cv2.rectangle(frame, (left, top), (right, bottom), (255, 0, 0), 2)

            detected_passenger_info = recognize_passenger(face_encoding)

            if detected_passenger_info is not None:
                entry_gate_open()
                deduct_balance(detected_passenger_info, passenger_df)
                exit_gate_open()
            else:
                engine.say("Unauthorized entry. Please register at the counter.")
                engine.runAndWait()

        cv2.imshow("Video", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

def recognize_passenger(face_encodings):
    registered_faces_path = "registered_faces/"
    registered_faces = []
    passenger_ids = []

    for image_file in os.listdir(registered_faces_path):
        passenger_id = int(image_file.split(".")[0])
        image_path = os.path.join(registered_faces_path, image_file)
        passenger_image = face_recognition.load_image_file(image_path)
        passenger_face_encoding = face_recognition.face_encodings(passenger_image)[0]

        registered_faces.append(passenger_face_encoding)
        passenger_ids.append(passenger_id)

    for face_encoding in face_encodings:
        for i, registered_face_encoding in enumerate(registered_faces):
            face_distance = face_recognition.face_distance(
                np.array([registered_face_encoding]), np.array(face_encoding)
            )
            similarity_threshold = 0.6

            if face_distance < similarity_threshold:
                passenger_id = passenger_ids[i]
                return passenger_df[passenger_df["ID"] == passenger_id]

    return None

def entry_gate_open():
    engine.say("Welcome! Entry gate opening.")
    engine.runAndWait()

def deduct_balance(passenger_info, passenger_df):
    passenger_id = passenger_info["ID"].item()
    balance = passenger_info["Metro Balance"].item()
    if balance >= 10:
        engine.say("Balance deducted for the journey.")
        passenger_df.loc[passenger_df["ID"] == passenger_id, "Metro Balance"] = balance - 10
        passenger_df.to_excel(DATABASE_FILE, index=False)
    else:
        engine.say("Insufficient balance. Please recharge your card.")
    engine.runAndWait()

def exit_gate_open():
    engine.say("Thank you for traveling. Exit gate opening.")
    engine.runAndWait()

def capture_photo():
    cap = cv2.VideoCapture(0)

    while True:
        ret, frame = cap.read()
        cv2.imshow("Capture Photo", frame)

        if cv2.waitKey(1) & 0xFF == ord('y'):
            passenger_id = len(passenger_df) + 1
            photo_path = f"registered_faces\{passenger_id}.jpg"
            cv2.imwrite(photo_path, frame)
            break

    cap.release()
    cv2.destroyAllWindows()

    return photo_path

def register_passenger_gui():
    register_window = Tk()
    register_window.title("Register Passenger")
    register_window.geometry("600x900")

    name_var = StringVar()
    passenger_id_var = IntVar()
    balance_var = IntVar()

    canvas = Canvas(register_window, width=500, height=200)
    canvas.pack()

    logo = PhotoImage(file="colorful-letter-gradient-logo-design_474888-2309.png")  # Replace with your logo file
    canvas.create_image(200, 60, anchor="center", image=logo)

    Label(register_window, text="Enter passenger name:", font=("Helvetica", 12)).pack(pady=5)
    Entry(register_window, textvariable=name_var, font=("Helvetica", 12)).pack(pady=5)

    Label(register_window, text="Enter passenger ID:", font=("Helvetica", 12)).pack(pady=5)
    Entry(register_window, textvariable=passenger_id_var, font=("Helvetica", 12)).pack(pady=5)

    Label(register_window, text="Enter metro card balance:", font=("Helvetica", 12)).pack(pady=5)
    Entry(register_window, textvariable=balance_var, font=("Helvetica", 12)).pack(pady=5)

    capture_button = Button(register_window, text="Capture Photo", command=lambda: capture_photo_gui(register_window), font=("Helvetica", 12))
    capture_button.pack(pady=10)

    register_button = Button(register_window, text="Register", command=lambda: register_passenger(
        name_var.get(),
        passenger_id_var.get(),
        balance_var.get(),
        capture_photo()
    ), font=("Helvetica", 12), bg="#4CAF50", fg="white")
    register_button.pack(pady=10)

    register_window.mainloop()

def capture_photo_gui(parent):
    cap = cv2.VideoCapture(0)

    while True:
        ret, frame = cap.read()
        cv2.imshow("Capture Photo", frame)

        if cv2.waitKey(1) & 0xFF == ord('y'):
            passenger_id = len(passenger_df) + 1
            photo_path = f"registered_faces\{passenger_id}.jpg"
            cv2.imwrite(photo_path, frame)
            break

    cap.release()
    cv2.destroyAllWindows()

    messagebox.showinfo("Capture Photo", "Photo captured successfully!")
    parent.destroy()

while True:
    choice = int(input("1. Register Passenger\n2. Start Journey\n3. Exit\nEnter your choice: "))

    if choice == 1:
        register_passenger_gui()
        print("Passenger registered successfully.")

    elif choice == 2:
        detect_face()

    elif choice == 3:
        break

    else:
        print("Invalid choice. Please try again.")
