import argparse
import math
import os
import cv2 as cv
import numpy as np

def inRange(value, min, max):
    return value >= min and value <= max

def clamp(value, min, max):
    if value > max:
        return max
    
    if value < min:
        return min

    return value

def normalize(x, minX, maxX, normalizeMin = 0, normalizeMax = 1):
    return (x / (maxX - minX)) * (normalizeMax - normalizeMin) + normalizeMin

class LogLevel:
    Debug = 2
    Warn  = 1
    Error = 0

verboseLevel:int = LogLevel.Debug

def log(msg, logLevel = LogLevel.Debug):
    global verboseLevel

    if(verboseLevel >= logLevel):
        print(msg)

# NOTE: Colors are in BGR to align with opencv
class Color:
    
    white = (255, 255, 255)
    black = (  0,   0,   0)
    red   = (  0,   0, 255)
    green = (  0, 255,   0)
    blue  = (255,   0,   0)


class Slider:
    
    def __init__(self, name:str, window:str, minValue:int = 0, maxValue:int = 255, defaultValue:int = None, onSetValue = None) -> None:
        self.name = name
        self.window = window

        self.minValue = int(minValue)
        self.maxValue = int(maxValue)
        self.onSetValue = onSetValue
        
        defaultValue = minValue if defaultValue is None else defaultValue
        assert inRange(defaultValue, minValue, maxValue), f"DefaultValue: {defaultValue} is out of range: [{minValue}, {maxValue}]"
        self.setValue(defaultValue)


        cv.createTrackbar(self.name, self.window, self._value, self.maxValue, self.setValue)

    def getValue(self):
        return self._value

    def setValue(self, value:int):

        if self.onSetValue is not None:
            self.onSetValue(value)

        self._value = int(clamp(value, self.minValue, self.maxValue))


class NamedImage:

    def __init__(self, name:str, pixels:cv.Mat, nameOrigin:tuple[int, int] = None) -> None:
        self.name = name
        self.pixels = pixels

        self.font = cv.FONT_HERSHEY_DUPLEX
        self.fontColor = Color.white
        self.fontSize = .75
        self.fontThickness = 1

        self.fontShadowColor = Color.black
        self.fontShadowSize = 2

        self.defaultFontPadding = [10, 10]

        self.setNameOrigin(nameOrigin)

    def getTextSize(self, text:str):
        textWidth, textHeight  = cv.getTextSize(text, self.font, self.fontSize, self.getShadowThickness())[0]
        return (textWidth, textHeight)

    def setNameOrigin(self, nameOrigin:tuple[int, int]):

        if nameOrigin is None:

            _, nameHeight  = self.getTextSize(self.name)
            self.nameOrigin = (self.defaultFontPadding[0], nameHeight + self.defaultFontPadding[1])
        
        else:
            self.nameOrigin = nameOrigin 

    def getShadowThickness(self):
        return self.fontThickness + self.fontShadowSize

    def drawText(self, text:str, origin:tuple[int, int]):

        # Note: opencv requires integer position for text
        intOrigin = (int(origin[0]), int(origin[1]))

        shadowImage = cv.putText(self.pixels, text, intOrigin, self.font, self.fontSize, self.fontShadowColor, self.getShadowThickness(), cv.LINE_AA)
        return cv.putText(shadowImage, text, intOrigin, self.font, self.fontSize, self.fontColor, self.fontThickness, cv.LINE_AA)

    def getImage(self):
        return self.drawText(self.name, self.nameOrigin)

class MinMaxSlider:

    def __init__(self, name:str, window:str, minValue:int = 0, maxValue:int = 255, defaultMinValue:int = None, defaultMaxValue:int = None) -> None:
        
        # TODO: Have these share the same row?
        self.minSlider = Slider(f"{name} min\n", window, minValue, maxValue, defaultMinValue)        
        self.maxSlider = Slider(f"{name} max\n", window, minValue, maxValue, defaultMaxValue)        

    def getMinValue(self):
        return self.minSlider.getValue()

    def getMaxValue(self):
        return self.maxSlider.getValue()        

class Finger:
    def __init__(self, x, y, d1, d2, angle) -> None:
        self.x = x
        self.y = y
        self.d1 = d1
        self.d2 = d2
        self.angle = angle

    # TODO: This is a hack to get things working, we really want to use a
    #       a clipping rectangle and transform coordinates to that
    def correctY(self, y):
        ret = y * 2
        if ret > 1:
            return 1
        elif ret < -1:
            return -1
        else:
            return ret

    def __str__(self) -> str:

        # TODO: replace d1, d2 with width/height and add angle
        #       Make sure this doesn't break loren's airhockey code!
        return f"x: {self.x} y: {self.correctY(self.y)} d1: {self.d1} d2: {self.d2}"
class Touchpad:
    
    class RenderLevel:
        All      = 2
        Internal = 2
        Debug    = 1
        Minimal  = 0        
    class Sliders:
        def __init__(self, touchpad) -> None:

            # Note: The original width of the window sets the width of the trackbars
            self.sliderWidth = 400 
            cv.resizeWindow(touchpad.propertiesWindowName, self.sliderWidth, 0)

            self.hue = MinMaxSlider("hue", touchpad.propertiesWindowName, 
                defaultMinValue = clamp(touchpad.targetHSVColor[0] - touchpad.targetHSVTolerance[0], 0, 255), 
                defaultMaxValue = clamp(touchpad.targetHSVColor[0] + touchpad.targetHSVTolerance[0], 0, 255)
            )

            self.saturation = MinMaxSlider("sat", touchpad.propertiesWindowName, 
                defaultMinValue = clamp(touchpad.targetHSVColor[1] - touchpad.targetHSVTolerance[1], 0, 255), 
                defaultMaxValue = clamp(touchpad.targetHSVColor[1] + touchpad.targetHSVTolerance[1], 0, 255)
            )

            self.value = MinMaxSlider("val", touchpad.propertiesWindowName, 
                defaultMinValue = clamp(touchpad.targetHSVColor[2] - touchpad.targetHSVTolerance[2], 0, 255), 
                defaultMaxValue = clamp(touchpad.targetHSVColor[2] + touchpad.targetHSVTolerance[2], 0, 255)
            )

            self.area = MinMaxSlider("area", touchpad.propertiesWindowName, 
                minValue = 100,
                maxValue = 5000,
                defaultMinValue = 200,
                defaultMaxValue = 3000
            )

            self.diameter = MinMaxSlider("diam.", touchpad.propertiesWindowName, 
                minValue = 0,
                maxValue = 1000,
                defaultMinValue = 5,
                defaultMaxValue = 300
            )

            self.maxRadiusAspect = Slider("ratio max\n", touchpad.propertiesWindowName,
                minValue = 1,
                maxValue = 10,
                defaultValue = 3
            )

            # Note: opencv doesn't support fractional values for sliders so we keep things as whole percents
            self.maxNormalizedEllipseErrorPercent = Slider("error max\n", touchpad.propertiesWindowName,
                minValue = 0,
                maxValue = 100,
                defaultValue = 30                               
            )

            self.brightness = Slider("bright.\n", touchpad.propertiesWindowName, 
                minValue = 0, 
                maxValue = 255, 
                defaultValue = 255,
                onSetValue = lambda newValue : touchpad.setCameraProp(cv.CAP_PROP_BRIGHTNESS, newValue)
            )

            # Note: opencv doesn't support negative value for sliders so we keep things positive 
            self.negativeExposure = Slider("-Exposure\n", touchpad.propertiesWindowName, 
                minValue = 0, 
                maxValue = 11, 
                defaultValue = 7,
                onSetValue = lambda newValue : (
                    touchpad.setCameraProp(cv.CAP_PROP_EXPOSURE, -newValue), 

                    # don't know why, but setting exposure resets brightness so we force it back here
                    touchpad.setCameraProp(cv.CAP_PROP_BRIGHTNESS, self.brightness.getValue())
                )
            )

            self.renderLevel = Slider("Render\n", touchpad.propertiesWindowName,
                minValue = touchpad.RenderLevel.Minimal,                          
                maxValue = touchpad.RenderLevel.All,                          
                defaultValue = touchpad.RenderLevel.Minimal                     
            )

            # Note: resize the properties window to fit two sliders side-by side (plus 25% padding)
            cv.resizeWindow(touchpad.propertiesWindowName, int(self.sliderWidth*2.25), 0)

                
    def __init__(self, cameraPort:int, windowName:str=None, outputFilePath="touchpad.out") -> None:

        # setup tmp output files
        self.outputFilePath = os.path.abspath(outputFilePath)        
        self.tmpOutputFilePath = self.outputFilePath+".tmp"

        # Configure Camera
        self.camera_port = cameraPort
        self.camera = cv.VideoCapture(cameraPort)

        self.cameraHeight = 720
        self.cameraWidth  = 1280
        self.camera.set(cv.CAP_PROP_FRAME_HEIGHT, self.cameraHeight)
        self.camera.set(cv.CAP_PROP_FRAME_WIDTH, self.cameraWidth)

        self.cameraFPS = 30
        self.camera.set(cv.CAP_PROP_FPS, self.cameraFPS)

        self.setCameraProp(cv.CAP_PROP_AUTO_EXPOSURE, -1)
        # self.camera.set(cv.CAP_PROP_AUTO_WB, 0)

        print(self.getCameraInfo())

        self.frameId = 0
        self.renderImages:list[NamedImage] = []
        self.fingers:list[Finger] = []

        # Configure filters
        # TODO: Make these sliders?
        self.ellipseIterations = 2
        self.ellipseKernelSize = (5, 5)
        self.ellipseKernel = cv.getStructuringElement(cv.MORPH_ELLIPSE, self.ellipseKernelSize)

        self.denoiseIterations = 3
        self.denoiseKernelSize = (5, 5)
        self.denoiseKernel = cv.getStructuringElement(cv.MORPH_ELLIPSE, self.denoiseKernelSize)

        # create windows
        self.windowName = windowName if windowName is not None else f"Touchpad: {cameraPort}"
        self.propertiesWindowName = self.windowName + " - Properties"
        cv.namedWindow(self.windowName, cv.WINDOW_NORMAL|cv.WINDOW_KEEPRATIO)
        cv.namedWindow(self.propertiesWindowName, cv.WINDOW_NORMAL|cv.WINDOW_KEEPRATIO)
        
        targetRGB = np.uint8([[[210, 203, 227 ]]])
        self.targetHSVColor = cv.cvtColor( np.uint8(targetRGB),cv.COLOR_RGB2HSV).reshape(3)
        self.targetHSVTolerance = [100, 100, 150]

        # create sliders
        self.sliders = self.Sliders(self)

    def setCameraProp(self, property:int, value:int):

        # Note: Hack to get camera properties to apply
        #       self.camera.get doesn't report properties correctly
        #       from experimentation camera properties only apply themselves
        #       if there is a change from the value they are currently set to
        self.camera.set(property, value-1)
        self.camera.read()
        cv.waitKey(100)
        
        self.camera.set(property, value)
        self.camera.read()
        cv.waitKey(100)

    def __bool__(self):
        return cv.getWindowProperty(self.windowName, cv.WND_PROP_VISIBLE) == 1 and \
               cv.getWindowProperty(self.propertiesWindowName, cv.WND_PROP_VISIBLE) == 1

    def getCameraInfo(self):
        props = [
            "CAP_PROP_APERTURE",
            "CAP_PROP_AUTOFOCUS",
            "CAP_PROP_AUTO_EXPOSURE",
            "CAP_PROP_AUTO_WB",
            "CAP_PROP_BACKLIGHT",
            "CAP_PROP_BITRATE",
            "CAP_PROP_BRIGHTNESS",
            "CAP_PROP_CODEC_PIXEL_FORMAT",
            "CAP_PROP_CONTRAST",
            "CAP_PROP_CONVERT_RGB",
            "CAP_PROP_EXPOSURE",
            "CAP_PROP_FPS",
            "CAP_PROP_FRAME_HEIGHT",
            "CAP_PROP_FRAME_WIDTH",
            "CAP_PROP_GAIN",
            "CAP_PROP_GAMMA",
            "CAP_PROP_ISO_SPEED",
            "CAP_PROP_MODE",
            "CAP_PROP_MONOCHROME",
            "CAP_PROP_SATURATION",
            "CAP_PROP_SETTINGS",
            "CAP_PROP_SHARPNESS",
            "CAP_PROP_SPEED",
            "CAP_PROP_WB_TEMPERATURE",
            "CAP_PROP_ZOOM",
        ]

        infoStr = "Camera Info: {\n"
        for prop in props:
            infoStr+= f"\t{prop}: {self.camera.get(getattr(cv, prop))}\n"

        return infoStr+"}\n"

    def draw(self):
        
        # Create a blank window image buffer
        _, _, windowWidth, windowHeight = windowRect = cv.getWindowImageRect(self.windowName)
        windowImage = np.zeros((windowHeight, windowWidth, 3), dtype=np.uint8)

        # Compute layout of image grid 
        numImages = len(self.renderImages)
        numXImages = max(1, int(math.ceil(np.sqrt(numImages))))
        numYImages = max(1, int(math.ceil(numImages/numXImages)))

        maxImageWidth  = int(windowWidth/numXImages)
        maxImageHeight = int(windowHeight/numYImages)

        maxImageAspect = maxImageWidth/maxImageHeight

        # Blit images to window image buffer
        for i in range(0, numImages):
                
            row = i//numXImages
            col = i - row*numXImages

            y = row*maxImageHeight
            x = col*maxImageWidth

            image = self.renderImages[i].getImage()
            imageAspect = image.shape[1] / image.shape[0]
    
            if imageAspect >= maxImageAspect:
    
                # Fit to width of image
                imageWidth = maxImageWidth
                imageHeight = int(imageWidth/imageAspect + .5)
                y+= (maxImageHeight - imageHeight)//2

            else:
                # Fit to height of image
                imageHeight = maxImageHeight
                imageWidth = int(imageAspect*imageHeight + .5)
                x+= (maxImageWidth - imageWidth)//2

            resizedImage = cv.resize(image, (imageWidth, imageHeight), interpolation=cv.INTER_LANCZOS4)

            # Note: We add empty color dimension to the resized image if its monochromatic so numpy
            #       can broadcast it to 3 color channel destination   
            if(len(resizedImage.shape) == 2):
                resizedImage = resizedImage[..., np.newaxis]

            windowImage[y:y+imageHeight, x:x+imageWidth] = resizedImage 

        # Display window image buffer
        # Note: We need to pause via waitKey to allow opencv to display frame
        cv.imshow(self.windowName, windowImage)
        cv.waitKey(1)
        

    def getMinHSV(self):
        return (
            self.sliders.hue.getMinValue(),
            self.sliders.saturation.getMinValue(),
            self.sliders.value.getMinValue()
        )


    def getMaxHSV(self):
        return (
            self.sliders.hue.getMaxValue(),
            self.sliders.saturation.getMaxValue(),
            self.sliders.value.getMaxValue()
        ) 

    # Note: appends render image if current render level is greater than or equal to `minRenderLevel`
    def addRenderImage(self, image:NamedImage, minRenderLevel:int):

        if self.sliders.renderLevel.getValue() >= minRenderLevel:
            self.renderImages.append(image)

    def update(self):
        
        # clear out last frame
        self.fingers.clear()
        self.renderImages.clear()

        self.frameId+= 1 
        _, rawPixels = self.camera.read()
        
        rawImage = NamedImage("Raw", rawPixels)
        self.addRenderImage(rawImage, self.RenderLevel.Minimal)
        
        # TODO: Rename this to something better
        self.fitEllipse(rawImage)
        
        self.publishFingers()

    def publishFingers(self):

        # write output to tmpFile
        frameStr = f"frameId: {self.frameId} "
        with open(self.tmpOutputFilePath, "w") as tmpFile:
            for finger in self.fingers:
                tmpFile.write(frameStr + str(finger)+"\n")

            tmpFile.flush()
            os.fsync(tmpFile.fileno())

        # Atomic move tmp file to output file
        maxPublishAttempts = 10
        publishAttemptDelay = 10
        for i in range(0, maxPublishAttempts):
            try:
                os.replace(self.tmpOutputFilePath, self.outputFilePath)
                break
            except Exception as e:
                log(f"Failed to publish fingers on attempt {i+1}/{maxPublishAttempts}", LogLevel.Warn)
                cv.waitKey(publishAttemptDelay)
        
        
    def getMask(self, image, colorLower, colorUpper):        

        # Note: OPEN is erosion followed by dilation (AKA standard denoise)
        denoisedImage = cv.morphologyEx(image, cv.MORPH_OPEN, self.denoiseKernel, iterations=self.denoiseIterations)
        self.addRenderImage(NamedImage("Denoised", denoisedImage), self.RenderLevel.Internal)

        # Note: closing is dilation followed by erosion
        closedImage = cv.morphologyEx(denoisedImage, cv.MORPH_CLOSE, self.denoiseKernel, iterations=self.denoiseIterations)
        self.addRenderImage(NamedImage("Closed", closedImage), self.RenderLevel.Internal)

        boundedImage = cv.inRange(closedImage, colorLower, colorUpper)

        return boundedImage
        
    # Returns the ellipse that fits the contour and satisfies the current constraints or None if no ellipse if found
    def getConstrainedEllipse(self, contour):

        # Note: opencv requires at least 5 vertices to fit ellipse
        if len(contour) < 5:
            return None

        # Ignore obvious small or giant splotches
        minArea = self.sliders.area.getMinValue()
        maxArea = self.sliders.area.getMaxValue()
        contourArea = cv.contourArea(contour)
        if not inRange(contourArea, minArea, maxArea):
            return None 

        ellipse = cv.fitEllipse(contour)
        (x, y), (d1, d2), angle = ellipse

        # TODO: Make sure that x, y is inbounds of clipping rect!

        # Make sure the ellipse isn't to small/big
        minDiameter = self.sliders.diameter.getMinValue()
        maxDiameter = self.sliders.diameter.getMaxValue()        
        if not (inRange(d1, minDiameter, maxDiameter) and 
                inRange(d2, minDiameter, maxDiameter)):
            return None 

        # Make sure the ellipse isn't to stretched 
        aspectRatio = np.abs(d1/d2)
        maxRadiusAspect = self.sliders.maxRadiusAspect.getValue()
        if not inRange(aspectRatio, 1/maxRadiusAspect, maxRadiusAspect):
            return None

        # Make sure the fit ellipse is actually approximates a decent ellipse
        # Note: ellipse area is pi*r1*r2
        ellipseArea = math.pi*d1*d2/4
        normalizedEllipseError = (ellipseArea - contourArea) / ellipseArea

        maxNormalizedEllipseError = self.sliders.maxNormalizedEllipseErrorPercent.getValue()/100
        if abs(normalizedEllipseError) > maxNormalizedEllipseError:
            log(f"IGNORING - normalizedEllipseError: {normalizedEllipseError} | ellipseArea: {ellipseArea} | contourArea: {contourArea}")
            return None

        # Bingo - we got a good ellipse!
        log(f"ELLIPSE: diameter: [{d1}, {d2}] | AspectRatio: {aspectRatio} | contourArea: {contourArea} | ellipseArea: {ellipseArea} | error: {normalizedEllipseError}")
        return ellipse

    def fitEllipse(self, namedImage:NamedImage):

        # Convert image to HSV
        hsvImage = cv.cvtColor(namedImage.pixels, cv.COLOR_BGR2HSV)
        self.addRenderImage(NamedImage("HSV", hsvImage), self.RenderLevel.Debug)

        # Get image binary mask
        hsvMask = self.getMask(hsvImage, self.getMinHSV(), self.getMaxHSV())
        self.addRenderImage(NamedImage("MASK", hsvMask), self.RenderLevel.Internal)

        # Preform a gradient on the mask to form 'rings' around fingers
        gradientEllipse = cv.morphologyEx(hsvMask, cv.MORPH_GRADIENT, self.ellipseKernel, self.ellipseIterations)
        self.addRenderImage(NamedImage("GRADIENT", gradientEllipse), self.RenderLevel.Debug)
    
        contours, hierarchies = cv.findContours(gradientEllipse, cv.RETR_TREE, cv.CHAIN_APPROX_SIMPLE)
        if hierarchies is None:
            return

        # Draw all contours in red (we'll draw over the good ones with green when we detect a finger)
        cv.drawContours(namedImage.pixels, contours, -1, color=Color.red)

        for i, (contour, hierarchy) in enumerate(zip(contours, hierarchies[0])):

            nextContour, prevContour, childContour, parentContour = hierarchy

            # we only care about the inner hole of a ring
            if childContour != -1:
                continue

            fingerEllipse = self.getConstrainedEllipse(contour) 
            if fingerEllipse is None:
                continue

            # TODO: Also make sure that parent contour is matches all constraints!
            # if parentContour

            (fingerX, fingerY), (fingerWidth, fingerHeight), fingerAngle = fingerEllipse

            # Draw ellipse on image
            cv.ellipse(namedImage.pixels, fingerEllipse, Color.green, 2)        
            namedImage.drawText(f"[{np.round(fingerX, 2)}, {np.round(fingerY, 2)}]", (fingerX, fingerY))

            # Normalize finger coordinates and add to queue
            normalizedX = normalize(fingerX, 0, self.cameraWidth, -1, 1)
            normalizedY = normalize(fingerY, 0, self.cameraHeight, -1, 1)
            self.fingers.append(Finger(normalizedX, normalizedY, fingerWidth, fingerHeight, fingerAngle))


def main():

    argParser = argparse.ArgumentParser(
        prog = "Touchpad",
        description ="Driver for EECS 598 IR Touchpad",
    )

    argParser.add_argument("-p", "--port", metavar="n", action="store", default=0, required=False, help="IR Camera port number")
    argParser.add_argument("-o", "--output", metavar="path", action="store", default="touchpad.out", required=False, help="Output filepath to write finger positions to")
    argParser.add_argument("-v", "--verbose", metavar="path", action="store", default="0", required=False, help="Sets the verbose level (higher means more logging)")

    args = argParser.parse_args()
    
    global verboseLevel
    verboseLevel = int(args.verbose)

    log(f"Touchpad: [\n"+
        f"\tPort: {args.port}\n"+        
        f"\tOutputFile: {args.output}\n"+        
        f"]\n"
    )

    touchpad = Touchpad(cameraPort=int(args.port), windowName="Touchpad", outputFilePath=args.output)

    while touchpad:
        touchpad.update()
        touchpad.draw()



if __name__ == "__main__":
    main()
    