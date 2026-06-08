#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import cv2
import numpy as np
import tkinter as tk
from tkinter import filedialog
import sys
import os

# read image
tk.Tk().withdraw()
image_path = filedialog.askopenfilename(
    title="Select image",
    filetypes=[("Image files", "*.jpg *.jpeg *.png *.bmp *.tiff *.webp")],
)
save_dir = os.path.dirname(image_path)

if not image_path:
    sys.exit(0)


# dummy function that does nothing
def dummy(value):
    pass  # required by OpenCV trackbar API


def draw_kernel_bar(kernel_name, contrast_val, brightness, mode, width):
    mode_names = {0: "color", 1: "grayscale", 2: "sepia"}
    text = f"Contrast: {contrast_val:.2f}x  Brightness: {brightness:+d}  Filter: {kernel_name}  Mode: {mode_names[mode]}"
    font = cv2.FONT_HERSHEY_SIMPLEX

    # scale font to fit the width
    font_scale = width / 1200.0
    font_scale = max(0.34, font_scale)
    thickness = max(1, round(width / 800)) if font_scale > 0.7 else 1

    bar_height = round(width / 34) + 12
    (text_w, text_h), _ = cv2.getTextSize(text, font, font_scale, thickness)
    bar = np.zeros((bar_height, width, 3), dtype=np.uint8)

    # if text still too wide, shrink further
    if text_w > width - 20:
        font_scale *= (width - 20) / text_w
        (text_w, text_h), _ = cv2.getTextSize(text, font, font_scale, thickness)
        bar_height = round(width / 34) + 12
        bar = np.zeros((bar_height, width, 3), dtype=np.uint8)

    y = text_h + 8
    cv2.putText(bar, text, (10, y), font, font_scale, (255, 255, 255), thickness)
    return bar


def get_current_image(mode, color_modified, sepia_modified, gray_modified):
    if mode == 0:
        return color_modified
    elif mode == 2:
        return sepia_modified
    else:
        return gray_modified


def apply_sepia(img):
    kernel = np.array(
        [[0.272, 0.534, 0.131], [0.349, 0.686, 0.168], [0.393, 0.769, 0.189]]
    )
    return cv2.transform(img, kernel).clip(0, 255).astype(np.uint8)


# define convolution kernels
identity_kernel = np.array([[0, 0, 0], [0, 1, 0], [0, 0, 0]])

sharpen_kernel = np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]])

unsharp_masking = np.array(
    [
        [1, 4, 6, 4, 1],
        [4, 16, 24, 16, 4],
        [6, 24, -476, 24, 6],
        [4, 16, 24, 16, 4],
        [1, 4, 6, 4, 1],
    ],
    np.float32,
) / (-256.0)

gaussian_kernel1 = cv2.getGaussianKernel(3, 0)
gaussian_kernel2 = cv2.getGaussianKernel(5, 0)

box_kernel = np.array([[1, 1, 1], [1, 1, 1], [1, 1, 1]], np.float32) / 9.0

scharr_kernel_hor = np.array([[3, 0, -3], [10, 0, -10], [3, 0, -3]])

sobel_kernel_hor = np.array([[-1, 0, 1], [-2, 0, 2], [-1, 0, 1]])

scharr_kernel_ver = np.array([[3, 10, 3], [0, 0, 0], [-3, -10, -3]])

sobel_kernel_ver = np.array([[-1, -2, -1], [0, 0, 0], [1, 2, 1]])

diag_kernel1 = np.array([[-1, -1, -1], [-1, 0, 1], [1, 1, 1]])

diag_kernel2 = np.array([[1, 1, 1], [1, 0, -1], [-1, -1, -1]])

ridge_det = np.array([[-1, -1, -1], [-1, 8, -1], [-1, -1, -1]])

kernels = [
    (identity_kernel, "identity"),
    (sharpen_kernel, "sharpen"),
    (unsharp_masking, "unsharp"),
    (gaussian_kernel1, "gaussian3"),
    (gaussian_kernel2, "gaussian5"),
    (box_kernel, "box"),
    (scharr_kernel_hor, "scharr_h"),
    (scharr_kernel_ver, "scharr_v"),
    (sobel_kernel_hor, "sobel_h"),
    (sobel_kernel_ver, "sobel_v"),
    (diag_kernel1, "diag1"),
    (diag_kernel2, "diag2"),
    (ridge_det, "ridge"),
]
filter_len = len(kernels) - 1

# read in an image, make a grayscale and sepia copies
color_original = cv2.imread(image_path)
gray_original = cv2.cvtColor(color_original, cv2.COLOR_BGR2GRAY)
sepia_original = apply_sepia(color_original)

# create the UI (window and trackbars)
cv2.namedWindow("app", cv2.WINDOW_NORMAL)
cv2.resizeWindow("app", 700, 700)
cv2.moveWindow("app", 150, 0)

# arguments: trackbarName, windowName, value (initial value),
# count (max value), onChange (event handler)
cv2.createTrackbar("contrast", "app", 33, 100, dummy)
cv2.createTrackbar("brightness", "app", 127, 254, dummy)
cv2.createTrackbar("filter", "app", 0, filter_len, dummy)
cv2.createTrackbar("grayscale/sepia", "app", 0, 2, dummy)

# main UI loop
count = 1
while True:
    # read all fo the trackbar values
    mode = cv2.getTrackbarPos("grayscale/sepia", "app")
    contrast = cv2.getTrackbarPos("contrast", "app")
    contrast_val = contrast / 33.0
    brightness = cv2.getTrackbarPos("brightness", "app") - 127
    kernel_idx = cv2.getTrackbarPos("filter", "app")
    kernel, kernel_name = kernels[kernel_idx]

    # apply the filters
    color_modified = cv2.filter2D(color_original, -1, kernel)
    gray_modified = cv2.filter2D(gray_original, -1, kernel)
    sepia_modified = cv2.filter2D(sepia_original, -1, kernel)

    # apply the brightness and contrast
    color_modified = cv2.addWeighted(
        color_modified, contrast_val, np.zeros_like(color_modified), 0, brightness
    )

    gray_modified = cv2.addWeighted(
        gray_modified, contrast_val, np.zeros_like(gray_modified), 0, brightness
    )

    sepia_modified = cv2.addWeighted(
        sepia_modified, contrast_val, np.zeros_like(sepia_modified), 0, brightness
    )

    # wait for keypress (100 milliseconds)
    key = cv2.waitKey(100)
    if key == ord("q"):
        break

    elif key == ord("a"):
        # quick save
        img_to_save = get_current_image(
            mode, color_modified, sepia_modified, gray_modified
        )
        cv2.imwrite(os.path.join(save_dir, f"output_{count}.png"), img_to_save)
        count += 1

    elif key == ord("s"):
        save_path = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("PNG", "*.png"), ("JPEG", "*.jpg"), ("BMP", "*.bmp")],
        )
        if save_path:
            img_to_save = get_current_image(
                mode, color_modified, sepia_modified, gray_modified
            )
            cv2.imwrite(save_path, img_to_save)

    if cv2.getWindowProperty("app", cv2.WND_PROP_VISIBLE) < 1:
        break

    # show the image
    if mode == 0:
        bar = draw_kernel_bar(
            kernel_name, contrast_val, brightness, mode, color_modified.shape[1]
        )
        cv2.imshow("app", np.vstack([color_modified, bar]))
    elif mode == 2:
        bar = draw_kernel_bar(
            kernel_name, contrast_val, brightness, mode, sepia_modified.shape[1]
        )
        cv2.imshow("app", np.vstack([sepia_modified, bar]))
    else:
        gray_3ch = cv2.cvtColor(gray_modified, cv2.COLOR_GRAY2BGR)
        bar = draw_kernel_bar(
            kernel_name, contrast_val, brightness, mode, gray_3ch.shape[1]
        )
        cv2.imshow("app", np.vstack([gray_3ch, bar]))

# window cleanup
cv2.destroyAllWindows()
