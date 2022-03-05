import cv2
import json
import numpy as np


"""
    Contrast control (1.0-3.0)
    Brightness control (0-100)
"""


def process_image(data):
    try:
        data = json.loads(data)

        if 'alpha' not in data:
            alpha = 1.25
        else:
            alpha = float(data['alpha'])

        if 'beta' not in data:
            beta = 1.0
        else:
            beta = float(data['beta'])

        if 'rotate' not in data:
            rotate = true
        else:
            rotate = bool(data['rotate'])

        if 'padding' not in data:
            padding = 5
        else:
            padding = int(data['padding'])

        source_path = data['source']
        target_path = data['target']

        print("Correcting Image %s" % source_path)
        image = cv2.imread(source_path)

        if rotate:
            image = cv2.rotate(image, cv2.cv2.ROTATE_180)

        # Color correction
        image = cv2.convertScaleAbs(image, alpha=alpha, beta=beta)

        # Crop Image
        image = crop_image(image, padding=padding)

        cv2.imwrite(target_path, image)
        print("Output Image %s" % target_path)
        return True
    except Exception as e:
        print("CONVERT ERROR \n %s \n %s" % (source_path, target_path))
        print(e)
        return False


def crop_image(img, coef=0.25, rCoef=4, padding=10):
    heightImg, widthImg, _ = img.shape

    originalImage = img.copy()

    widthImg = int(widthImg * coef)
    heightImg = int(heightImg * coef)
    img = cv2.resize(img, (widthImg, heightImg))  # RESIZE IMAGE

    # CREATE A BLANK IMAGE FOR TESTING DEBUGING IF REQUIRED
    imgBlank = np.zeros((heightImg, widthImg, 3), np.uint8)

    # CONVERT IMAGE TO GRAY SCALE
    imgGray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    imgBlur = cv2.GaussianBlur(imgGray, (5, 5), 1)  # ADD GAUSSIAN BLUR

    imgThreshold = cv2.Canny(imgBlur, 255, 1)

    kernel = np.ones((5, 5))
    imgDial = cv2.dilate(imgThreshold, kernel, iterations=2)  # APPLY DILATION
    imgThreshold = cv2.erode(imgDial, kernel, iterations=1)  # APPLY EROSION

    # FIND ALL COUNTOURS
    contours, hierarchy = cv2.findContours(
        imgThreshold, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # FIND THE BIGGEST COUNTOUR
    biggest, maxArea = biggestContour(contours)
    if biggest.size != 0:
        # Convert to original size & use original image
        biggest = reorder(biggest) * rCoef
        img = originalImage
        widthImg = int(widthImg * rCoef)
        heightImg = int(heightImg * rCoef)

        # BIGGEST CONTOUR
        pts1 = np.float32(biggest)
        pts2 = np.float32([[0, 0], [widthImg, 0], [0, heightImg], [
                          widthImg, heightImg]])
        matrix = cv2.getPerspectiveTransform(pts1, pts2)

        imgWarpColored = cv2.warpPerspective(
            img, matrix, (widthImg, heightImg))

        # REMOVE 'x' PIXELS FORM EACH SIDE
        imgWarpColored = imgWarpColored[padding:imgWarpColored.shape[0] -
                                        padding, padding:imgWarpColored.shape[1] - padding]
        imgWarpColored = cv2.resize(imgWarpColored, (widthImg, heightImg))
        imgAdaptiveThre = cv2.medianBlur(imgWarpColored, 3)
    else:
        imgAdaptiveThre = img

    return imgAdaptiveThre


def reorder(myPoints):
    myPoints = myPoints.reshape((4, 2))
    myPointsNew = np.zeros((4, 1, 2), dtype=np.int32)
    add = myPoints.sum(1)

    myPointsNew[0] = myPoints[np.argmin(add)]
    myPointsNew[3] = myPoints[np.argmax(add)]
    diff = np.diff(myPoints, axis=1)
    myPointsNew[1] = myPoints[np.argmin(diff)]
    myPointsNew[2] = myPoints[np.argmax(diff)]
    return myPointsNew


def biggestContour(contours):
    biggest = np.array([])
    max_area = 0
    for i in contours:
        area = cv2.contourArea(i)
        if area > 5000:
            peri = cv2.arcLength(i, True)
            approx = cv2.approxPolyDP(i, 0.02 * peri, True)
            if area > max_area and len(approx) == 4:
                biggest = approx
                max_area = area
    return biggest, max_area
