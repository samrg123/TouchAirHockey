import cv2 as cv
import numpy as np
cv2 = cv

camera_port = 1
camera = cv2.VideoCapture(camera_port)
# camera = cv2.VideoCapture()


contourMaxLevel = int(100)
contourMaxValue = int(100)
contoursThreshold = 160
contoursThresholdMaxValue = 255
contoursThresholdMinValue = 0

# Note: in opencv HSV
targetHSVColor = [174, 252, 253]

target_threshold = 30

# defaultHSVFileter = {
#     "hmin": targetHSVColor[0] - target_threshold,
#     "hmax": targetHSVColor[0] + target_threshold,
#     "smin": targetHSVColor[1] - target_threshold,
#     "smax": targetHSVColor[1] + target_threshold,
#     "vmin": targetHSVColor[2] - target_threshold,
#     "vmax": targetHSVColor[2] + target_threshold
# }

defaultHSVFileter = {
    "hmin": 0,
    "hmax": 255,
    "smin": 0,
    "smax": 80,
    "vmin": 200,
    "vmax": 255
}

hmin, hmax, smin, smax, vmin, vmax = 0, 255, 0, 255, 0, 255

def passF(value):
    pass

def inRange(value, min, max):
    return value >= min and value <= max
    
def getMask(frame, colorLower, colorUpper, iterations=1):
    mask = cv2.inRange(frame, colorLower, colorUpper)
    mask = cv2.erode(mask, None, iterations)
    mask = cv2.dilate(mask, None, iterations)
    return mask

def fitEllipse(image, ellipseKernelSize = (12, 12), iterations=1):
    
    
    hsvEllipse = cv2.cvtColor(image, cv2.COLOR_RGB2HSV)
                    
    #color = cv2.cvtColor( np.uint8([[[253,3,70 ]]]),cv2.COLOR_RGB2HSV)
    #print(color)

    colorLower = (hmin, smin, vmin)
    colorUpper = (hmax, smax, vmax)

    ellipseMask = getMask(image, colorLower, colorUpper, iterations)

    ellipseKernel = cv.getStructuringElement(cv.MORPH_ELLIPSE, ellipseKernelSize)

    dilatedEllipse = cv2.dilate(ellipseMask , ellipseKernel, iterations)
    # contours, hierarchy = cv.findContours(dilatedEllipse, cv.RETR_TREE, cv.CHAIN_APPROX_SIMPLE)

    contours, hierarchy = cv.findContours(ellipseMask, cv.RETR_TREE, cv.CHAIN_APPROX_SIMPLE)

    minArea = 1000
    maxArea = 8000
    minRadius = 15
    maxRadius = 1000
    minRadiusDelta = 0
    maxRadiusDelta = maxRadius
    # hsv_red = cv2.cvtColor(np.uint8([[[253,3,50 ]]]),cv2.COLOR_BGR2HSV)

    # print(hsv_red)    

    for contour in contours:

        area = cv.contourArea(contour)
    
        if True or inRange(area, minArea, maxArea):
            
            if len(contour) < 5:
                continue
            try:
                ellipse = cv2.fitEllipse(contour)
            except:
                continue
            (xc,yc),(d1,d2),angle = ellipse
            
            if not (inRange(d1, minRadius, maxRadius) and 
                    inRange(d2, minRadius, maxRadius) and 
                    inRange(np.abs(d2 - d1), minRadiusDelta, maxRadiusDelta)):
                continue 

            cv2.ellipse(dilatedEllipse, ellipse, (36,255,12), 2)        
            print(area)

    print("\nXXXX\n")
    cv.imshow("window_ellispe", dilatedEllipse)


def initializeTrackbars(window_name = "window"):
    cv2.createTrackbar("hmin", window_name, defaultHSVFileter["hmin"], 255, passF)
    cv2.createTrackbar("hmax", window_name, defaultHSVFileter["hmax"], 255, passF)
    cv2.createTrackbar("smin", window_name, defaultHSVFileter["smin"], 255, passF)
    cv2.createTrackbar("smax", window_name, defaultHSVFileter["smax"], 255, passF)
    cv2.createTrackbar("vmin", window_name, defaultHSVFileter["vmin"], 255, passF)
    cv2.createTrackbar("vmax", window_name, defaultHSVFileter["vmax"], 255, passF)

def updateTrackbarValue(window_name = "window"):
    global hmin, hmax, smin, smax, vmin, vmax
    hmin = cv2.getTrackbarPos("hmin", window_name)
    hmax = cv2.getTrackbarPos("hmax", window_name)
    smin = cv2.getTrackbarPos("smin", window_name)
    smax = cv2.getTrackbarPos("smax", window_name)
    vmin = cv2.getTrackbarPos("vmin", window_name)
    vmax = cv2.getTrackbarPos("vmax", window_name)

def main():
    cv.namedWindow('window')

    initializeTrackbars()

    while True:
        ret, frame = camera.read()
        cv2.imshow('window',frame)

        hsv = cv2.cvtColor(frame, cv2.COLOR_RGB2HSV)

        fitEllipse(frame)
                
        updateTrackbarValue()

        colorLower = (hmin, smin, vmin)
        colorUpper = (hmax, smax, vmax)

        mask = getMask(hsv, colorLower, colorUpper)

        contours, hierarchy = cv.findContours(mask, cv.RETR_TREE, cv.CHAIN_APPROX_SIMPLE)

        # imgray = cv.cvtColor(frame, cv.COLOR_BGR2GRAY)
        # ret, thresh = cv.threshold(imgray, contoursThreshold, contoursThresholdMaxValue, contoursThresholdMinValue)
        # contours, hierarchy = cv.findContours(thresh, cv.RETR_TREE, cv.CHAIN_APPROX_SIMPLE)


        cv.drawContours(
            hsv, 
            contours, 
            -1, # num contours -1 means draw all
            (0,255,0), # color
            3,
            cv.LINE_AA,
            maxLevel=contourMaxLevel # Thickness 
        )

        # cv.extract()

        cv2.imshow('window_mask',mask)

        cv2.imshow('window_hsv',hsv)

        cv2.waitKey(100)

if __name__ == "__main__":
    main()
    


# ret, frame = camera.read()

# cv2.imshow('window', frame)

# cv2.createTrackbar("hmin", "window", 120, 255, changeHmin)
# cv2.createTrackbar("hmax", "window", 120, 255, changeHmax)
# cv2.createTrackbar("smin", "window", 120, 255, changeSmin)
# cv2.createTrackbar("smax", "window", 120, 255, changeSmax)
# cv2.createTrackbar("vmin", "window", 120, 255, changeVmin)
# cv2.createTrackbar("vmax", "window", 120, 255, changeVmax)

# while True:
#     ret, frame = camera.read()
#     cv2.imshow('window',frame)
    
#     hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
            
#     hmin = cv2.getTrackbarPos("hmin", "window")
#     hmax = cv2.getTrackbarPos("hmax", "window")
#     smin = cv2.getTrackbarPos("smin", "window")
#     smax = cv2.getTrackbarPos("smax", "window")
#     vmin = cv2.getTrackbarPos("vmin", "window")
#     vmax = cv2.getTrackbarPos("vmax", "window")
    

#     colorLower = (hmin, smin, vmin)
#     colorUpper = (hmax, smax, vmax)

#     mask = cv2.inRange(hsv, colorLower, colorUpper)
#     mask = cv2.erode(mask, None, iterations=2)
#     mask = cv2.dilate(mask, None, iterations=2)

#     contours, hierarchy = cv.findContours(mask, cv.RETR_TREE, cv.CHAIN_APPROX_SIMPLE)

#     # imgray = cv.cvtColor(frame, cv.COLOR_BGR2GRAY)
#     # ret, thresh = cv.threshold(imgray, contoursThreshold, contoursThresholdMaxValue, contoursThresholdMinValue)
#     # contours, hierarchy = cv.findContours(thresh, cv.RETR_TREE, cv.CHAIN_APPROX_SIMPLE)


#     cv.drawContours(
#         hsv, 
#         contours, 
#         -1, # num contours -1 means draw all
#         (0,255,0), # color
#         3,
#         cv.LINE_AA,
#         maxLevel=contourMaxLevel # Thickness 
#     )

#     # cv.extract()

#     cv2.imshow('window_mask',mask)

#     cv2.imshow('window_hsv',hsv)

#     #cv2.imshow('window2',thresh)
    
    """
    if len(cnts) > 0:
        # find the largest contour in the mask, then use
        # it to compute the minimum enclosing circle and
        # centroid
        c = max(cnts, key=cv2.contourArea)
        ((x, y), radius) = cv2.minEnclosingCircle(c)
        M = cv2.moments(c)
        center = (int(M["m10"] / M["m00"]), int(M["m01"] / M["m00"]))

        # only proceed if the radius meets a minimum size
        if radius > 10:
            print("center: {},{}".format(int(x), int(y)))

            # draw the circle and centroid on the frame,
            # then update the list of tracked points
            cv2.circle(frame, (int(x), int(y)), int(radius),
                (0, 255, 255), 2)
            cv2.circle(frame, center, 5, (0, 0, 255), -1)
            
            # position Servo at center of circle
            mapObjectPosition(int(x), int(y))
            
            # if the led is not already on, turn the LED on
            if not ledOn:
                GPIO.output(redLed, GPIO.HIGH)
                ledOn = True

        if (outside_flag):
            centerVal = checkCenter(int(x), leftInnerbound, rightInnerbound)
            cv2.line(frame, (leftInnerbound, 0), (leftInnerbound, 500), (255, 0, 0), 2)
            cv2.line(frame, (rightInnerbound, 0), (rightInnerbound, 500), (255, 0, 0), 2)
        else:
            centerVal = checkCenter(int(x), leftbound, rightbound)
            cv2.line(frame, (leftbound, 0), (leftbound, 500), (255, 0, 0), 2)
            cv2.line(frame, (rightbound, 0), (rightbound, 500), (255, 0, 0), 2)
        if(centerVal == 0):
            move_robot('F')
            outside_flag = False
            movement = 'Forward'
        elif(centerVal == 1):
            move_robot('R')
            outside_flag = True
            movement = 'Left'
        elif(centerVal == 2):
            move_robot('L')
            outside_flag = True
            movement = 'Right'
        else:
            move_robot('S')
            movement = 'Stop'

    # if the ball is not detected, turn the LED off
    elif ledOn:
        GPIO.output(redLed, GPIO.LOW)
        ledOn = False

    else: 
        move_robot('S')

    # show the frame to our screen
    cv2.putText(frame, movement, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2, cv2.LINE_AA)
    cv2.imshow("Frame", frame)

    # if [ESC] key is pressed, stop the loop
    key = cv2.waitKey(1) & 0xFF
    if key == 27:
            break
    """

    """
    
    ret, thresh = cv2.threshold(frame, 127, 255, 0)
    contours, hierarchy = cv2.findContours(thresh)

    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    colorLower = (24, 100, 100)
    colorUpper = (44, 255, 255)

    mask = cv2.inRange(hsv, colorLower, colorUpper)
    mask = cv2.erode(mask, None, iterations=2)
    mask = cv2.dilate(mask, None, iterations=2)
    """

    # cnts = cv2.findContours(mask.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # cnts = cv2.findContours(mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE, offset=(2,2))[1]

    # frame = imutils.resize(frame, width=500)
    # frame = imutils.rotate(frame, angle=180)

    # # print(frame)
    # # break

    # # cv2.imshow('frame', frame)
    # # if cv2.waitKey(1) & 0xFF == ord('q'):
    # #     break
    # # continue

    # 
    # # print(hsv)
    # # break

    # # construct a mask for the object color, then perform
    # # a series of dilations and erosions to remove any small
    # # blobs left in the mask
    # mask = cv2.inRange(hsv, colorLower, colorUpper)
    # mask = cv2.erode(mask, None, iterations=2)
    # mask = cv2.dilate(mask, None, iterations=2)

    # # find contours in the mask and initialize the current
    # # (x, y) center of the object
    # cnts = cv2.findContours(mask.copy(), cv2.RETR_EXTERNAL,
    #     cv2.CHAIN_APPROX_SIMPLE)
    # #print(cnts)
    # cnts = cnts[0] #if imutils.is_cv2() else cnts[1]

    # cv2.findContours(frame)
    
    # cv2.waitKey(100)

