import cv2
import pytesseract
from urllib import request
import serial
import mysql.connector
import threading

# Path to Tesseract-OCR executable
pytesseract.pytesseract.tesseract_cmd = r'/opt/homebrew/bin/tesseract'

# Function to read from serial port and update database
def read_serial_and_update_db():
    # Connect to the MySQL database
    mydb = mysql.connector.connect(
      host="localhost",
      user="root",
      password="chinthaprabha2",
      database="parking"
    )
    mycursor = mydb.cursor()

    # Open the serial port
    ser = serial.Serial('/dev/cu.usbserial-11230', 9600)

    while True:
        # Read data from the serial port
        data = ser.readline().decode().strip()
        
        # Insert data into the database
        sql = "UPDATE parking SET slotstatus = %s WHERE slotnumber = 1"
        val = (data,)
        mycursor.execute(sql, val)
        mydb.commit()

        print("Data inserted:", data)

        # Check if the input is not empty

    # Close the serial port
    ser.close()

# Function to capture image from mobile, extract text, and display
def capture_image_and_extract_text():
    # URL for the video stream from IP Webcam app
    url = "http://192.168.31.174:8080/video"

    # Open the video stream
    video_stream = request.urlopen(url)

    # Create a VideoCapture object with the URL
    cap = cv2.VideoCapture(url)

    # Check if the video stream is open
    if not video_stream or not cap.isOpened():
        print("Error: Could not open video stream.")
        exit()

    # Read the first frame from the video stream
    ret, frame = cap.read()

    # If the frame was successfully captured
    if ret:
        # Convert the frame to grayscale
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # Apply Gaussian blur to reduce noise
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)

        # Apply edge detection using the Canny edge detector
        edges = cv2.Canny(blurred, 50, 150)

        # Find contours in the edged image
        contours, _ = cv2.findContours(edges.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        # Sort contours by area and find the largest contour
        contours = sorted(contours, key=cv2.contourArea, reverse=True)[:10]

        number_plate_image = None
        for contour in contours:
            # Approximate the contour
            perimeter = cv2.arcLength(contour, True)
            approx = cv2.approxPolyDP(contour, 0.02 * perimeter, True)

            # If the contour has four vertices, it is likely a rectangle (number plate)
            if len(approx) == 4:
                number_plate = approx
                x, y, w, h = cv2.boundingRect(number_plate)
                number_plate_image = frame[y:y+h, x:x+w]
                break

        if number_plate_image is not None:
            # Convert the cropped image to grayscale
            gray_plate = cv2.cvtColor(number_plate_image, cv2.COLOR_BGR2GRAY)

            # Apply thresholding to preprocess the image
            _, thresh = cv2.threshold(gray_plate, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

            # Use pytesseract to extract text from the image
            text = pytesseract.image_to_string(thresh)

            if text.strip() == '':
                print("Image unclear")
            else:
                # Print the extracted text
                print("Extracted Text:", text)

                # Save the frame with the detected number plate
                cv2.imwrite("captured_frame_with_plate.jpg", frame)
                print("Frame with detected number plate saved as captured_frame_with_plate.jpg")
        else:
            print("Image unclear")

        # Release the video stream
        video_stream.close()
    else:
        print("Error: Could not capture frame from video stream.")


# Start the serial reading thread
serial_thread = threading.Thread(target=read_serial_and_update_db)
serial_thread.start()

# Wait for the serial reading thread to finish
serial_thread.join()
