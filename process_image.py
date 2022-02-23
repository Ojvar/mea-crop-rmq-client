import cv2
import json


"""
    Contrast control (1.0-3.0)
    Brightness control (0-100)
"""


def process_image(data, alpha=1.25, beta=25):
    try:
        data = json.loads(data)

        source_path = data['source']
        target_path = data['target']

        print("Correcting Image %s" % source_path)
        image = cv2.imread(source_path)

        manual_result = cv2.convertScaleAbs(image, alpha=alpha, beta=beta)
        manual_result = cv2.rotate(manual_result, cv2.cv2.ROTATE_180)

        cv2.imwrite(target_path, manual_result)
        print("Output Image %s" % target_path)
        return True
    except:
        print("CONVERT ERROR \n %s \n %s" % (source_path, target_path))
        return False
