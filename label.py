import argparse
import cv2
import numpy as np


from autowebcompat import utils

labels_directory = "label_persons/"

parser = argparse.ArgumentParser()
parser.add_argument("file_name", action="store")
args = parser.parse_args()

labels = utils.read_labels(labels_directory + args.file_name + ".csv")
boundary_boxes = utils.read_boundary_boxes(labels_directory + args.file_name + "_boundary_box.csv")

images_to_show = [i for i in utils.get_images() if i not in labels]
drawing = False
key_map = {"Escape": 27, "r": 114, "Enter": 13, "y": 121, "n": 110, "d": 100}
cv2.namedWindow('firefox')
cv2.namedWindow('chrome')


def draw_boundary_box(event, mouse_x, mouse_y, flags, param):
    global start_x, start_y, drawing, end_x, end_y
    [drawing_area, boxes] = param

    if event == cv2.EVENT_LBUTTONDOWN:
        drawing = True
        start_x, start_y = mouse_x, mouse_y
        end_x, end_y = mouse_x, mouse_y
    elif event == cv2.EVENT_MOUSEMOVE:
        if drawing is True:
            box_start_x, box_start_y = start_x, start_y
            box_end_x, box_end_y = end_x, end_y
            if box_start_x > box_end_x:
                box_start_x, box_end_x = box_end_x, box_start_x
            if box_start_y > box_end_y:
                box_start_y, box_end_y = box_end_y, box_start_y
            box_start_x = max(0, box_start_x)
            box_start_y = max(0, box_start_y)
            box_end_x = min(drawing_area.shape[1], box_end_x)
            box_end_y = min(drawing_area.shape[0], box_end_y)
            drawing_area[box_start_y:box_end_y + 1, box_start_x:box_end_x + 1, 0:3] = 0
            end_x = max(mouse_x, 0)
            end_y = max(mouse_y, 0)
            cv2.rectangle(drawing_area, (start_x, start_y), (end_x, end_y), (0, 255, 0), -1)
    elif event == cv2.EVENT_LBUTTONUP:
        drawing = False
        start_x = max(0, start_x)
        start_y = max(0, start_y)
        end_x = min(drawing_area.shape[1], end_x)
        end_y = min(drawing_area.shape[0], end_y)
        cv2.rectangle(drawing_area, (start_x, start_y), (end_x, end_y), (0, 255, 0), -1)
        boxes.append([min(start_x, end_x), min(start_y, end_y), max(start_x, end_x), max(start_y, end_y)])


# The images are not the same and you want to mark the boundary box.
def get_new_image():
    if len(images_to_show) == 0:
        cv2.destroyAllWindows()
        return
    current_image = images_to_show.pop()
    print("Reading %s" % current_image)
    firefox_ss = cv2.imread("data/%s_firefox.png" % current_image)
    chrome_ss = cv2.imread("data/%s_chrome.png" % current_image)
    drawing_area_firefox = np.zeros((firefox_ss.shape), np.uint8)
    drawing_area_chrome = np.zeros((chrome_ss.shape), np.uint8)
    boxes_firefox = []
    boxes_chrome = []
    cv2.setMouseCallback('firefox', draw_boundary_box, [drawing_area_firefox, boxes_firefox])
    cv2.setMouseCallback('chrome', draw_boundary_box, [drawing_area_chrome, boxes_chrome])
    visiblity = 1
    while True:
        firefox_window = cv2.addWeighted(drawing_area_firefox, 1 - visiblity, firefox_ss, visiblity, 0)
        chrome_window = cv2.addWeighted(drawing_area_chrome, 1 - visiblity, chrome_ss, visiblity, 0)
        cv2.imshow('firefox', firefox_window)
        cv2.imshow('chrome', chrome_window)
        cv2.moveWindow('firefox', 20, 0)
        cv2.moveWindow('chrome', 20 + firefox_window.shape[1], 0)
        k = cv2.waitKey(1) & 0xFF
        # <Escape> quits marking area without saving
        if k == key_map["Escape"]:
            cv2.destroyAllWindows()
            return
        # 'r' resets the present selection of boundary boxes
        elif k == key_map["r"]:
            drawing_area_firefox = np.zeros((firefox_ss.shape), np.uint8)
            drawing_area_chrome = np.zeros((chrome_ss.shape), np.uint8)
            boxes_chrome = []
            boxes_firefox = []
            cv2.setMouseCallback('firefox', draw_boundary_box, [drawing_area_firefox, boxes_firefox])
            cv2.setMouseCallback('chrome', draw_boundary_box, [drawing_area_chrome, boxes_chrome])
        # <Return> saves the current marking and moves to next image or skips it if no label is assigned
        elif k == key_map["Enter"]:
            if current_image not in labels.keys():
                break
            boundary_boxes[current_image + '_firefox'] = boxes_firefox
            boundary_boxes[current_image + '_chrome'] = boxes_chrome
            break
        elif k == key_map["y"]:
            labels[current_image] = 'y'
            break
        elif k == key_map["n"]:
            labels[current_image] = 'n'
            visiblity = 0.5
        elif k == key_map["d"]:
            labels[current_image] = 'd'
            visiblity = 0.5

    get_new_image()


get_new_image()

# Store results.
utils.write_boundary_boxes(boundary_boxes, labels_directory + args.file_name + "_boundary_box.csv")
utils.write_labels(labels, labels_directory + args.file_name + ".csv")
