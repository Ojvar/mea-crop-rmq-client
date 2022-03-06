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

        if 'crop' not in data:
            crop = True
        else:
            crop = bool(data['crop'])

        if 'color_adjust' not in data:
            color_adjust = True
        else:
            color_adjust = bool(data['color_adjust'])

        if 'bw_lower' not in data:
            bw_lower = 120
        else:
            bw_lower = float(data['bw_lower'])

        if 'bw_upper' not in data:
            bw_upper = 255
        else:
            bw_upper = float(data['bw_upper'])

        if 'alpha' not in data:
            alpha = 1.25
        else:
            alpha = float(data['alpha'])

        if 'beta' not in data:
            beta = 1.0
        else:
            beta = float(data['beta'])

        if 'rotate' not in data:
            rotate = True
        else:
            rotate = bool(data['rotate'])

        if 'bw' not in data:
            bw = False
        else:
            bw = bool(data['bw'])
        print("BW I ")
        print(bw)

        if 'padding' not in data:
            padding = 5
        else:
            padding = int(data['padding'])

        if 'sharpness' not in data:
            sharpness = 0
        else:
            sharpness = int(data['sharpness'])

        source_path = data['source']
        target_path = data['target']

        print("Correcting Image %s" % source_path)
        image = cv2.imread(source_path)

        if rotate:
            image = cv2.rotate(image, cv2.cv2.ROTATE_180)

        # Color correction
        if color_adjust:
            image = cv2.convertScaleAbs(image, alpha=alpha, beta=beta)

        # Apply sharpness filter
        if 0 != sharpness:
            image = sharp_image(image, value=sharpness)

        # Crop Image
        if crop == True:
            crop_result = crop_image(image, padding=padding)
            if (crop_result is not None):
                image = crop_result

        # Apply BW filter
        if bw == True:
            image = convert_to_bw(image, bw_lower=bw_lower, bw_upper=bw_upper)
            print('converted to bw')

        cv2.imwrite(target_path, image)
        print("Output Image %s" % target_path)
        return True
    except Exception as e:
        print(e)
        return False


def convert_to_bw(image, bw_lower=120, bw_upper=255):
    img = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    ret, output = cv2.threshold(
        img, bw_lower, bw_upper, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return output


def sharp_image(image, value=5.0):
    value += 5
    kernel = np.array([[0, -1, 0],
                       [-1, value, -1],
                       [0, -1, 0]])
    return cv2.filter2D(src=image, ddepth=-1, kernel=kernel)


def crop_image(img, coef=0.25, rCoef=4, padding=10):
    originalImage = img.copy()
    heightImg, widthImg, _ = img.shape
    widthImg = int(widthImg * coef)
    heightImg = int(heightImg * coef)
    img = cv2.resize(img, (widthImg, heightImg))  # RESIZE IMAGE

    blur_matrix = (7, 7)

    # CREATE A BLANK IMAGE FOR TESTING DEBUGING IF REQUIRED
    imgBlank = np.zeros((heightImg, widthImg, 3), np.uint8)

    # CONVERT IMAGE TO GRAY SCALE
    imgGray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    imgBlur = cv2.GaussianBlur(imgGray, blur_matrix, 1)  # ADD GAUSSIAN BLUR

    imgThreshold = cv2.Canny(imgBlur, 255, 1)

    kernel = np.ones(blur_matrix)
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
        imgAdaptiveThre = None

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
