import serial
import mysql.connector

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
ser.close()

