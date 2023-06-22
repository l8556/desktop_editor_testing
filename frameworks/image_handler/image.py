# -*- coding: utf-8 -*-

import cv2
import numpy as np

# from skimage.metrics import structural_similarity
import mss
import mss.tools


class Image:

    @staticmethod
    def read(img_path: str) -> cv2.imread:
        return cv2.imread(img_path)

    @staticmethod
    def find_template_on_window(
            window_coord: tuple,
            template: str,
            threshold: "int | float" = 0.8
    ) -> "list[int, int] | None":

        window = cv2.cvtColor(Image.grab_coordinate(window_coord), cv2.COLOR_BGR2GRAY)
        template = cv2.cvtColor(cv2.imread(template), cv2.COLOR_BGR2GRAY)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(cv2.matchTemplate(window, template, cv2.TM_CCOEFF_NORMED))
        if max_val >= threshold:
            h, w = template.shape
            center_x = max_loc[0] + w // 2 + window_coord[0]
            center_y = max_loc[1] + h // 2 + window_coord[1]
            return [center_x, center_y]
        return None

    @staticmethod
    def is_image_present(template_path: str, window_coordinates: tuple = None, threshold: "int | float" = 0.8) -> bool:
        window = cv2.cvtColor(Image.grab_coordinate(window_coordinates), cv2.COLOR_BGR2GRAY)
        template = cv2.cvtColor(cv2.imread(template_path), cv2.COLOR_BGR2GRAY)
        _, max_val, _, _ = cv2.minMaxLoc(cv2.matchTemplate(window, template, cv2.TM_CCOEFF_NORMED))
        return True if max_val >= threshold else False

    @staticmethod
    def grab_coordinate(window_coordinates: tuple = None, monitor_num: int = 1) -> np.array:
        with mss.mss() as sct:
            if isinstance(window_coordinates, tuple):
                left, top, right, bottom = window_coordinates
                return np.array(sct.grab({"left": left, "top": top, "width": right - left, "height": bottom - top}))
            return np.array(sct.grab(sct.monitors[monitor_num]))

    @staticmethod
    def find_contours(img):
        rgb, gray = cv2.cvtColor(img, cv2.COLOR_BGR2RGB), cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        _, binary = cv2.threshold(gray, 125, 255, cv2.THRESH_BINARY)
        contours, hierarchy = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            if h >= 500:
                return rgb[y:y + h, x:x + w]

    # @staticmethod
    # def find_difference(img_1: np.ndarray, img_2: np.ndarray) -> float:
    #     before, after = cv2.cvtColor(img_1, cv2.COLOR_BGR2GRAY), cv2.cvtColor(img_2, cv2.COLOR_BGR2GRAY)
    #     return structural_similarity(before, after, full=True)

    @staticmethod
    def draw_differences(img_1: np.ndarray, img_2: np.ndarray, diff: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        thresh = cv2.threshold((diff * 255).astype("uint8"), 0, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)[1]
        contours = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        for contur in contours[0] if len(contours) == 2 else contours[1]:
            if cv2.contourArea(contur) > 40:
                x, y, w, h = cv2.boundingRect(contur)
                cv2.rectangle(img_1, (x, y), (x + w, y + h), (0, 0, 255), 0)
                cv2.rectangle(img_2, (x, y), (x + w, y + h), (0, 0, 255), 0)
        return img_1, img_2

    @staticmethod
    def save(path, img):
        cv2.imwrite(path, img)

    @staticmethod
    def put_text(cv2_opened_image, text: str):
        cv2.putText(cv2_opened_image, text, (20, 35), cv2.FONT_HERSHEY_COMPLEX, 1, color=(0, 0, 255), thickness=2)

    @staticmethod
    def make_screenshot_by_coordinante(img_path: str, coordinate: tuple) -> None:
        left, top, right, bottom = coordinate
        with mss.mss() as sct:
            img = sct.grab({"left": left, "top": top, "width": right - left, "height": bottom - top})
            mss.tools.to_png(img.rgb, img.size, output=img_path)

    @staticmethod
    def make_screenshot(img_path: str) -> None:
        with mss.mss() as sct:
            sct.shot(output=img_path)
