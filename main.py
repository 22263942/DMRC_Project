import cv2
import face_recognition
import pandas as pd
import pyttsx3
import numpy as np
import os

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
    # Check if the DataFrame has columns, if not, create them
    global passenger_df

    if passenger_df.empty:
        passenger_df = pd.DataFrame(columns=["Name", "ID", "Metro Balance", "Photo"])

    passenger_df.loc[len(passenger_df)] = [name, passenger_id, balance, photo_path]
    passenger_df.to_excel(DATABASE_FILE, index=False)

def detect_face():
    cap = cv2.VideoCapture(0)

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)  # Convert BGR to RGB for face_recognition

        # Detect faces using the face_recognition library
        faces = face_recognition.face_locations(rgb_frame)
        face_encodings = face_recognition.face_encodings(rgb_frame, faces)  # Get face encodings for detected faces

        if not face_encodings:
            # No faces detected in the current frame
            continue

        for (top, right, bottom, left), face_encoding in zip(faces, face_encodings):
            cv2.rectangle(frame, (left, top), (right, bottom), (255, 0, 0), 2)

            detected_passenger_info = recognize_passenger(face_encoding)

            if detected_passenger_info is not None:
                entry_gate_open()
                deduct_balance(detected_passenger_info, passenger_df)  # Pass passenger_df to the function
                exit_gate_open()
            else:
                engine.say("Unauthorized entry. Please register at the counter.")
                engine.runAndWait()

        cv2.imshow("Video", frame)

        if cv2.runAndWait(1) & 0xFF == ord('q'): 
            break

    cap.release()
    cv2.destroyAllWindows()


def recognize_passenger(face_encodings):
    # Load the registered passenger images and encode them
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

    # Encode the detected face from the camera
    #face_encodings = face_recognition.face_encodings(face)

    #if not face_encodings:
        # No face encodings detected
    #    return None

    for face_encoding in face_encodings:
        for i, face_encoding in enumerate(registered_faces):
            face_distance = face_recognition.face_distance(
                np.array([face_encoding]), np.array(face_encodings)
            )
            similarity_threshold = 0.6  # Adjust this threshold based on your dataset

            if face_distance < similarity_threshold:
                passenger_id = passenger_ids[i]
                # Return the entire passenger DataFrame instead of just the ID
                return passenger_df[passenger_df["ID"] == passenger_id]

    return None



def entry_gate_open():
    engine.say("Welcome! Entry gate opening.")
    engine.runAndWait()


def deduct_balance(passenger_info, passenger_df):
    passenger_id = passenger_info["ID"].item()  # Extract the scalar value of passenger ID
    balance = passenger_info["Metro Balance"].item()  # Extract the scalar value of balance
    if balance >= 10:
        engine.say("Balance deducted for the journey.")
        passenger_df.loc[passenger_df["ID"] == passenger_id, "Metro Balance"] = balance - 10
        passenger_df.to_excel(DATABASE_FILE, index=False)
    else:
        engine.say("Insufficient balance. Please recharge your card.")
    engine.runAndWait()



def exit_gate_open():
    engine.say("Thank you for traveling . Exit gate opening.")
    engine.runAndWait()


def capture_photo():
    cap = cv2.VideoCapture(0)

    while True:
        ret, frame = cap.read()
        cv2.imshow("Capture Photo", frame)

        if cv2.waitKey(1) & 0xFF == ord('y'):
            # Generate a unique photo filename based on passenger ID
            passenger_id = len(passenger_df) + 1  # Use the next available ID for new passenger
            photo_path = f"registered_faces\{passenger_id}.jpg"

            # Save the photo and break the loop
            cv2.imwrite(photo_path, frame)
            break

    cap.release()
    cv2.destroyAllWindows()

    return photo_path


while True:
    choice = int(input("1. Register Passenger\n2. Start Journey\n3. Exit\nEnter your choice: "))

    if choice == 1:
        name = input("Enter passenger name: ")
        passenger_id = int(input("Enter passenger ID: "))
        balance = float(input("Enter metro card balance: "))
        print("Please stand in front of the camera. Press 'y' to capture your photo.")
        input("Press Enter to continue...")
        photo_path = capture_photo()

        register_passenger(name, passenger_id, balance, photo_path)
        print("Passenger registered successfully.")

    elif choice == 2:
        detect_face()

    elif choice == 3:
        break

    else:
        print("Invalid choice. Please try again.")