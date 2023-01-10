from PyQt5 import QtWidgets, uic, QtCore
from PyQt5.QtGui import QImage, QPixmap 
import sys
import serial
import keyboard
import time
import cv2
import numpy as np
import sqlite3
def findData(cursor,id):
    cursor.execute("SELECT * FROM DATA WHERE PHONE=?", (id,))
    rows = cursor.fetchall()
    # print("select")
    return rows

def updateData(cursor,id):
    try:
        cursor.execute('''INSERT INTO DATA VALUES (?, ?)''',(id,0))
        print("create")
        conn.commit()
    except:    
        data = findData(cursor,id)
        num = data[0][1]+1
        cursor.execute('''UPDATE DATA SET NUM = ? WHERE PHONE=?;''',(num,id))
        print("update")
        conn.commit()

def getGift(cursor,id):
    data = findData(cursor,id)
    num = data[0][1]-5
    cursor.execute('''UPDATE DATA SET NUM = ? WHERE PHONE=?;''',(num,id))
    print("update")
    conn.commit()

def getAllData(cursor):
    print("Data Inserted in the table: ")
    data=cursor.execute('''SELECT * FROM DATA''')
    for row in data:
        print(row)   
    return data

def detect(frame, net):
	# resize the video stream window at a maximum width of 500 pixels
	# time.sleep(0.4)
	check_bottle = False
	t = time.time()
	frame =cv2.flip(frame,1)
	# frame = imutils.resize(frame, width=500)
	(h, w) = frame.shape[:2]
	blob = cv2.dnn.blobFromImage(cv2.resize(frame, (300, 300)), 0.007843, (300, 300), 127.5)
	# pass the blob through the network and get the detections
	net.setInput(blob)
	detections = net.forward()
	# loop over the detections
	for i in np.arange(0, detections.shape[2]):
		global label
		# extract the probability of the prediction
		probability = detections[0, 0, i, 2]
		# filter out weak detections by ensuring that probability is
		# greater than the min probability
		if probability > 0.5:
			idx = int(detections[0, 0, i, 1])
			box = detections[0, 0, i, 3:7] * np.array([w, h, w, h])
			(startX, startY, endX, endY) = box.astype("int")
			# draw the prediction on the frame
			label = "{}".format(CLASSES[idx])
			cv2.rectangle(frame, (startX, startY), (endX, endY), COLORS[idx], 2)
			y = startY - 15 if startY - 15 > 15 else startY + 15
			cv2.putText(frame, label+ ": " + str(probability), (startX, y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, COLORS[idx], 2)
			if label == "bottle":
				check_bottle = True
	# cv2.imshow("Frame", frame)
	# cv2.waitKey(1)
	# print("FPS: ", 1/(time.time() - t))
	if check_bottle:
		return frame, True
	return frame, False

class Ui(QtWidgets.QMainWindow):
    def __init__(self):
        super(Ui, self).__init__()
        # root config
        uic.loadUi('screen.ui', self)
        self.setWindowTitle("MÁY AI THU CHAI NHỰA ĐỔI QUÀ")
        # const 
        self.cap = cv2.VideoCapture(0)
        self.check_bottle = False
        self.user_id = ""
        self.num_bottle = 0
        self.total_bottle = 0
        self.warning = "Xin chào quý khách"
        self.check_user = False

        # TIMER 
        self.timer_root = QtCore.QTimer(self)
        self.timer_root.timeout.connect(self.show_frame)
        self.timer_root.timeout.connect(self.checkBottle)

        self.timer_1 = QtCore.QTimer(self)
        self.timer_1.timeout.connect(self.getId)

        self.timer_1_sec = QtCore.QTimer(self)
        self.timer_1_sec.timeout.connect(self.checkOut)
        self.wait_time = 0

        self.timer_root.start(1)
        self.timer_1.start(50)

        self.timer_win = QtCore.QTimer(self)
        self.timer_win.timeout.connect(self.showNumBot)
        self.timer_win.start(50)


        self.show()
    def show_detect(self):
        _, self.image = self.cap.read()
        self.image, self.check_bottle = detect(self.image, net)
        self.image = cv2.resize(self.image, (480,320))
        self.image = cv2.cvtColor(self.image, cv2.COLOR_BGR2RGB)
        self.convert = QImage(self.image, self.image.shape[1], self.image.shape[0], self.image.strides[0], QImage.Format.Format_RGB888)
        self.frame.setPixmap(QPixmap.fromImage(self.convert))
    def show_frame(self):
        _, self.image = self.cap.read()
        self.image = cv2.resize(self.image, (480,320))
        self.image = cv2.cvtColor(self.image, cv2.COLOR_BGR2RGB)
        self.convert = QImage(self.image, self.image.shape[1], self.image.shape[0], self.image.strides[0], QImage.Format.Format_RGB888)
        self.frame.setPixmap(QPixmap.fromImage(self.convert))        
    def checkBottle(self):
        x = ser.readline()
        # print(x)
        # print(result)
        if (x[:-2].decode("utf-8")) == "0001":
            time.sleep(0.01)
            self.show_detect()
            # result = detect(frame, net)
            if self.check_bottle :
                ser.write("0001".encode("utf-8"))
                print("bottle here")
                time.sleep(0.01)
                self.num_bottle+=1
                if self.check_user == True:
                    updateData(cursor, self.user_id)
                    self.timer_1_sec.start(1000)
            else:
                ser.write("0000".encode("utf-8"))
                time.sleep(0.01)
    def getId(self):
        list_num = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "0"]
        self.user_id =  self.phoneid.text()
        if keyboard.is_pressed("enter"):
            if 10<=len(self.user_id)<12:
                for i in self.user_id:
                    if i not in list_num:
                        self.warning = "Mời nhập lại số điện thoại"
                        self.phoneid.clear()
                        self.user_id = ""
                        
                if len(self.user_id) >0:
                    self.warning = "Đăng nhập thành công"
                    self.check_user = True
            else:
                self.warning = "Mời nhập số điện thoại"
                self.phoneid.clear()
                self.user_id = ""
        elif keyboard.is_pressed("*"):
                # self.warning = "Hẹn gặp lại"
                self.reset()
        elif keyboard.is_pressed("tab"):
            print("pass")
            print(self.total_bottle)
            print(self.check_user)
            if self.total_bottle >=5 and self.check_user:
                print("hello")
                getGift(cursor, self.user_id)
                # ser.write("0011".encode("utf-8"))
                time.sleep(1)
            else:
                self.warning = "Phải có ít nhất 5 chai"
            
    def checkOut(self):
        self.wait_time += 1
        if self.wait_time == 10:
            self.reset()
            self.timer_1_sec.stop()

    def showNumBot(self):
        self.total.setText(str(self.total_bottle))
        self.numbot.setText(str(self.num_bottle))
        self.warning_label.setText(self.warning)
        if self.check_user:
            data_bot = findData(cursor,self.user_id)
            if data_bot:
                self.total.setText(str(data_bot[0][1]))
                self.total_bottle = data_bot[0][1]
            else:
                self.total.setText("0")
    
    def reset(self):
        self.phoneid.clear()
        self.check_bottle = False
        self.user_id = ""
        self.num_bottle = 0
        self.total_bottle = 0
        self.warning = "Xin chào quý khách"
        self.check_user = False
if __name__ == "__main__":
    ser = serial.Serial("COM8",9600, timeout = 0.01)
    prototxtPath =r"./realtime-object-detection-master/MobileNetSSD_deploy.prototxt.txt"
    weightsPath = r"./realtime-object-detection-master/MobileNetSSD_deploy.caffemodel"

    CLASSES = ["background", "aeroplane", "bicycle", "bird", "boat", "bottle", "bus", "car", "cat", "chair", "cow", "diningtable",
    "dog", "horse", "motorbike", "person", "pottedplant", "sheep", "sofa", "train", "tvmonitor"]
    COLORS = np.random.uniform(0, 255, size = (len(CLASSES), 3))
    conn = sqlite3.connect('database.db')
    print("Opened database successfully")
    cursor = conn.cursor()
    # load our serialized model from disk
    print("[INFO] loading model...")
    net = cv2.dnn.readNet(prototxtPath,weightsPath)
    print("[INFO] starting video stream...")
    app = QtWidgets.QApplication(sys.argv)
    window = Ui()
    sys.exit(app.exec())
    