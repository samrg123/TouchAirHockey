import math
import sys
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

# NOTE: Colors are in BGR to align with opencv
class Color:
    
    white = (255, 255, 255)
    black = (  0,   0,   0)
    red   = (  0,   0, 255)
    green = (  0, 255,   0)
    blue  = (255,   0,   0)


class Slider:
    
    def __init__(self, name:str, window:str, minValue:int = 0, maxValue:int = 255, defaultValue:int = None) -> None:
        self.name = name
        self.window = window

        self.minValue = minValue
        self.maxValue = maxValue
        
        defaultValue = minValue if defaultValue is None else defaultValue
        assert inRange(defaultValue, minValue, maxValue), f"DefaultValue: {defaultValue} is out of range: [{minValue}, {maxValue}]"
        self.setValue(defaultValue)

        cv.createTrackbar(self.name, self.window, self._value, self.maxValue, self.setValue)

    def getValue(self):
        return self._value

    def setValue(self, value:int):
        self._value = clamp(value, self.minValue, self.maxValue)


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
        self.minSlider = Slider(f"{name} min", window, minValue, maxValue, defaultMinValue)        
        self.maxSlider = Slider(f"{name} max", window, minValue, maxValue, defaultMaxValue)        

    def getMinValue(self):
        return self.minSlider.getValue()

    def getMaxValue(self):
        return self.maxSlider.getValue()        

class Touchpad:

    def __init__(self, cameraPort:int, windowName:str=None) -> None:

        # Configure Camera
        self.camera_port = cameraPort
        self.camera = cv.VideoCapture(cameraPort)

        self.camera.set(cv.CAP_PROP_FRAME_HEIGHT, 720)
        self.camera.set(cv.CAP_PROP_FRAME_WIDTH, 1280)
        self.camera.set(cv.CAP_PROP_ISO_SPEED, 200)
        # self.camera.set(cv.CAP_PROP_FPS, 30)
        # self.camera.set(cv.CAP_PROP_AUTO_WB, 0)
        # self.camera.set(cv.CAP_PROP_AUTO_EXPOSURE, 0)
        # self.camera.set(cv.CAP_PROP_MONOCHROME, 0)
        # self.camera.set(cv.CAP_PROP_BRIGHTNESS, 255)

        print(self.getCameraInfo())

        self.renderImages:list[NamedImage] = []

        # Configure filters
        # TODO: Make theseSldiers?
        self.ellipseIterations = 1
        self.ellipseKernelSize = (20, 20)
        self.ellipseKernel = cv.getStructuringElement(cv.MORPH_ELLIPSE, self.ellipseKernelSize)

        self.denoiseIterations = 1
        self.denoiseKernelSize = (1, 1)
        self.denoiseKernel = cv.getStructuringElement(cv.MORPH_ELLIPSE, self.ellipseKernelSize)

        # create windows
        self.windowName = windowName if windowName is not None else f"Touchpad: {cameraPort}"
        self.propertiesWindowsName = self.windowName + " - Properties"
        cv.namedWindow(self.windowName, cv.WINDOW_NORMAL|cv.WINDOW_KEEPRATIO)
        cv.namedWindow(self.propertiesWindowsName, cv.WINDOW_AUTOSIZE)

        # create sliders
        targetRGB = np.uint8([[[250, 237, 255 ]]])
        self.targetHSVColor = cv.cvtColor( np.uint8(targetRGB),cv.COLOR_RGB2HSV).reshape(3)
        self.targetHSVTolerance = [50, 150, 150]

        self.hSlider = MinMaxSlider("h", self.propertiesWindowsName, 
            defaultMinValue = clamp(self.targetHSVColor[0] - self.targetHSVTolerance[0], 0, 255), 
            defaultMaxValue = clamp(self.targetHSVColor[0] + self.targetHSVTolerance[0], 0, 255)
        )

        self.sSlider = MinMaxSlider("s", self.propertiesWindowsName, 
            defaultMinValue = clamp(self.targetHSVColor[1] - self.targetHSVTolerance[1], 0, 255), 
            defaultMaxValue = clamp(self.targetHSVColor[1] + self.targetHSVTolerance[1], 0, 255)
        )

        self.vSlider = MinMaxSlider("v", self.propertiesWindowsName, 
            defaultMinValue = clamp(self.targetHSVColor[2] - self.targetHSVTolerance[2], 0, 255), 
            defaultMaxValue = clamp(self.targetHSVColor[2] + self.targetHSVTolerance[2], 0, 255)
        )

    def __bool__(self):
        return cv.getWindowProperty(self.windowName, cv.WND_PROP_VISIBLE) == 1 and \
               cv.getWindowProperty(self.propertiesWindowsName, cv.WND_PROP_VISIBLE) == 1

    def getCameraInfo(self):
        props = [
            "CAP_PROP_APERTURE",
            "CAP_PROP_AUTOFOCUS",
            "CAP_PROP_AUTO_EXPOSURE",
            "CAP_PROP_AUTO_WB",
            "CAP_PROP_BACKEND",
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
        numXImages = int(math.ceil(np.sqrt(numImages)))
        numYImages = int(math.ceil(numImages/numXImages))

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
            self.hSlider.getMinValue(),
            self.sSlider.getMinValue(),
            self.vSlider.getMinValue()
        )


    def getMaxHSV(self):
        return (
            self.hSlider.getMaxValue(),
            self.sSlider.getMaxValue(),
            self.vSlider.getMaxValue()
        ) 

    def update(self):
        
        self.renderImages.clear()

        _, rawFrame = self.camera.read()
        
        rawImage = NamedImage("Raw", rawFrame)
        self.renderImages.append(rawImage)
        
        self.fitEllipse(rawImage)
        

    def getMask(self, image, colorLower, colorUpper):        

        boundedImage = cv.inRange(image, colorLower, colorUpper)

        # Note: OPEN is erosion followed by dilation (AKA standard denoise)
        denoisedImage = cv.morphologyEx(boundedImage, cv.MORPH_OPEN, self.denoiseKernel, iterations=self.denoiseIterations)

        # Note: closing is dilation followed by erosion
        closedImage = cv.morphologyEx(denoisedImage, cv.MORPH_CLOSE, self.denoiseKernel, iterations=self.denoiseIterations)

        return closedImage
        

    def fitEllipse(self, namedImage:NamedImage):
        
        hsvImage = cv.cvtColor(namedImage.pixels, cv.COLOR_BGR2HSV)
        self.renderImages.append(NamedImage("HSV", hsvImage))

        hsvMask = self.getMask(hsvImage, self.getMinHSV(), self.getMaxHSV())
        self.renderImages.append(NamedImage("MASK", hsvMask))

        dilatedEllipse = cv.dilate(hsvMask , self.ellipseKernel, self.ellipseIterations)
        self.renderImages.append(NamedImage("DIALATED", dilatedEllipse))

        contours, hierarchy = cv.findContours(dilatedEllipse, cv.RETR_TREE, cv.CHAIN_APPROX_SIMPLE)

        minArea = 2000
        maxArea = 30000
        minRadius = 20
        maxRadius = 300
        minRadiusDelta = 0
        maxRadiusDelta = maxRadius

        for contour in contours:

            # Note: opencv requires at least 5 vertices to fit ellipse
            if len(contour) < 5:
                continue

            area = cv.contourArea(contour)
            if not inRange(area, minArea, maxArea):
                continue 
        
            ellipse = cv.fitEllipse(contour)
            (xc,yc), (d1,d2), angle = ellipse
            
            if not (inRange(d1, minRadius, maxRadius) and 
                    inRange(d2, minRadius, maxRadius) and 
                    inRange(np.abs(d2 - d1), minRadiusDelta, maxRadiusDelta)):
                continue 

            cv.ellipse(namedImage.pixels, ellipse, Color.green, 2)        
            namedImage.drawText(f"[{np.round(xc, 2)}, {np.round(yc, 2)}]", (xc, yc))

            # TODO: Write out


def main():

    touchpad = Touchpad(2)

    while touchpad:
        touchpad.update()
        touchpad.draw()



if __name__ == "__main__":
    main()
    