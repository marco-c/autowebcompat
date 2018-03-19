import argparse
import cv2
import numpy as np


from autowebcompat import utils

labels_directory = "label_persons/"

parser = argparse.ArgumentParser()
parser.add_argument("file_name", action="store")
args = parser.parse_args()

labels = utils.read_labels(labels_directory + args.file_name + ".csv")
bounding_boxes = utils.read_bounding_boxes(labels_directory + args.file_name + "_bounding_box.json")

images_to_show = [i for i in utils.get_images() if i not in labels]
drawing = False
shifting = False
changing_shape = False
box_to_shift = []
key_map = {"Escape": 27, "r": 114, "Enter": 13, "Space": 32, "y": 121, "n": 110, "d": 100}
cv2.namedWindow('firefox')
cv2.namedWindow('chrome')
cv2.namedWindow('firefox_chrome_overlay')


def reset_bounding_boxes(drawing_area_shape):
    return np.zeros(drawing_area_shape, np.uint8)


def top_left_bottom_right_box(start_x, start_y, end_x, end_y):
    box_start_x, box_start_y = start_x, start_y
    box_end_x, box_end_y = end_x, end_y
    box_start_x, box_end_x = min(box_start_x, box_end_x), max(box_start_x, box_end_x)
    box_start_y, box_end_y = min(box_start_y, box_end_y), max(box_start_y, box_end_y)
    return box_start_x, box_start_y, box_end_x, box_end_y


def fit_bounding_box(start_x, start_y, end_x, end_y, x_max, y_max):
    start_x = max(0, start_x)
    start_y = max(0, start_y)
    end_x = min(x_max, end_x)
    end_y = min(y_max, end_y)
    return [start_x, start_y, end_x, end_y]


def check_cross_click(start_x, start_y, box):
    if start_x >= box[2] - 15 and start_x <= box[2] and start_y >= box[1] and start_y <= box[1] + 15:
        return True
    return False


def check_plus_click(start_x, start_y, box):
    center_x = (box[0] + box[2]) // 2
    center_y = (box[1] + box[3]) // 2
    if start_x >= center_x - 10 and start_x <= center_x + 10 and start_y >= center_y - 10 and start_y <= center_y + 10:
        return True
    return False


def check_arrow_click(start_x, start_y, box):
    if start_x >= box[2] - 10 and start_x <= box[2] and start_y >= box[3] - 10 and start_y <= box[3]:
        return True
    return False


def shift_bounding_box(box_to_shift, start_x, start_y, end_x, end_y):
    box_start_x = box_to_shift[0] + (end_x - start_x)
    box_start_y = box_to_shift[1] + (end_y - start_y)
    box_end_x = box_to_shift[2] + (end_x - start_x)
    box_end_y = box_to_shift[3] + (end_y - start_y)
    (box_start_x, box_start_y, box_end_x, box_end_y) = top_left_bottom_right_box(box_start_x, box_start_y, box_end_x, box_end_y)
    return (box_start_x, box_start_y, box_end_x, box_end_y)


def change_bounding_box(box_to_shift, start_x, start_y, end_x, end_y):
    (box_start_x, box_start_y, box_end_x, box_end_y) = top_left_bottom_right_box(box_to_shift[0], box_to_shift[1], end_x, end_y)
    return (box_start_x, box_start_y, box_end_x, box_end_y)


def create_bounding_box(drawing_area, start_x, start_y, end_x, end_y):
    cv2.rectangle(drawing_area, (start_x, start_y), (end_x, end_y), (0, 255, 0), -1)


def create_cross(drawing_area, start_x, start_y, end_x, end_y):
    cv2.line(drawing_area, (end_x - 2, start_y + 2), (end_x - 12, start_y + 12), (0, 0, 255), 2)
    cv2.line(drawing_area, (end_x - 12, start_y + 2), (end_x - 2, start_y + 12), (0, 0, 255), 2)


def create_plus(drawing_area, start_x, start_y, end_x, end_y):
    center_x = (start_x + end_x) // 2
    center_y = (start_y + end_y) // 2
    cv2.arrowedLine(drawing_area, (center_x, center_y - 10), (center_x, center_y + 10), (255, 0, 0), 2, tipLength=0.2)
    cv2.arrowedLine(drawing_area, (center_x - 10, center_y), (center_x + 10, center_y), (255, 0, 0), 2, tipLength=0.2)
    cv2.arrowedLine(drawing_area, (center_x, center_y + 10), (center_x, center_y - 10), (255, 0, 0), 2, tipLength=0.2)
    cv2.arrowedLine(drawing_area, (center_x + 10, center_y), (center_x - 10, center_y), (255, 0, 0), 2, tipLength=0.2)


def create_change_shape(drawing_area, start_x, start_y, end_x, end_y):
    cv2.arrowedLine(drawing_area, (end_x - 12, end_y - 12), (end_x - 2, end_y - 2), (255, 0, 0), 2, tipLength=0.3)
    cv2.arrowedLine(drawing_area, (end_x - 2, end_y - 2), (end_x - 12, end_y - 12), (255, 0, 0), 2, tipLength=0.3)


def draw_bounding_boxes(event, mouse_x, mouse_y, flags, param):
    global start_x, start_y, drawing, end_x, end_y, shifting, box_to_shift, changing_shape
    [drawing_area, boxes] = param

    for box in boxes:
        create_bounding_box(drawing_area, box[0], box[1], box[2], box[3])
        create_cross(drawing_area, box[0], box[1], box[2], box[3])
        create_plus(drawing_area, box[0], box[1], box[2], box[3])
        create_change_shape(drawing_area, box[0], box[1], box[2], box[3])

    if event == cv2.EVENT_LBUTTONDOWN:
        start_x, start_y = mouse_x, mouse_y
        end_x, end_y = mouse_x, mouse_y
        for box in boxes:
            if check_cross_click(start_x, start_y, box):
                drawing_area[box[1]: box[3] + 1, box[0]: box[2] + 1, 0:3] = 0
                boxes.remove(box)
                return
            if check_plus_click(start_x, start_y, box):
                drawing_area[box[1]: box[3] + 1, box[0]: box[2] + 1, 0:3] = 0
                shifting = True
                box_to_shift = box[:]
                boxes.remove(box)
                return
            if check_arrow_click(start_x, start_y, box):
                drawing_area[box[1]: box[3] + 1, box[0]: box[2] + 1, 0:3] = 0
                changing_shape = True
                box_to_shift = box[:]
                boxes.remove(box)
                return
        drawing = True
    elif event == cv2.EVENT_MOUSEMOVE:
        if drawing is True:
            (box_start_x, box_start_y, box_end_x, box_end_y) = top_left_bottom_right_box(start_x, start_y, end_x, end_y)
            drawing_area[box_start_y:box_end_y + 1, box_start_x:box_end_x + 1, 0:3] = 0
            end_x, end_y = mouse_x, mouse_y
            (box_start_x, box_start_y, box_end_x, box_end_y) = fit_bounding_box(start_x, start_y, end_x, end_y, drawing_area.shape[1], drawing_area.shape[0])
            create_bounding_box(drawing_area, box_start_x, box_start_y, box_end_x, box_end_y)
        elif shifting is True:
            (box_start_x, box_start_y, box_end_x, box_end_y) = shift_bounding_box(box_to_shift, start_x, start_y, end_x, end_y)
            (box_start_x, box_start_y, box_end_x, box_end_y) = fit_bounding_box(box_start_x, box_start_y, box_end_x, box_end_y, drawing_area.shape[1], drawing_area.shape[0])
            drawing_area[box_start_y:box_end_y + 1, box_start_x:box_end_x + 1, 0:3] = 0
            end_x, end_y = mouse_x, mouse_y

            (box_start_x, box_start_y, box_end_x, box_end_y) = shift_bounding_box(box_to_shift, start_x, start_y, end_x, end_y)
            (box_start_x, box_start_y, box_end_x, box_end_y) = fit_bounding_box(box_start_x, box_start_y, box_end_x, box_end_y, drawing_area.shape[1], drawing_area.shape[0])
            create_bounding_box(drawing_area, box_start_x, box_start_y, box_end_x, box_end_y)
        elif changing_shape is True:
            (box_start_x, box_start_y, box_end_x, box_end_y) = change_bounding_box(box_to_shift, start_x, start_y, end_x, end_y)
            (box_start_x, box_start_y, box_end_x, box_end_y) = fit_bounding_box(box_start_x, box_start_y, box_end_x, box_end_y, drawing_area.shape[1], drawing_area.shape[0])
            drawing_area[box_start_y:box_end_y + 1, box_start_x:box_end_x + 1, 0:3] = 0
            end_x, end_y = mouse_x, mouse_y
            (box_start_x, box_start_y, box_end_x, box_end_y) = change_bounding_box(box_to_shift, start_x, start_y, end_x, end_y)
            (box_start_x, box_start_y, box_end_x, box_end_y) = fit_bounding_box(box_start_x, box_start_y, box_end_x, box_end_y, drawing_area.shape[1], drawing_area.shape[0])
            create_bounding_box(drawing_area, box_start_x, box_start_y, box_end_x, box_end_y)

    elif event == cv2.EVENT_LBUTTONUP:
        if shifting is True:
            shifting = False
            (box_start_x, box_start_y, box_end_x, box_end_y) = shift_bounding_box(box_to_shift, start_x, start_y, end_x, end_y)
            (box_start_x, box_start_y, box_end_x, box_end_y) = fit_bounding_box(box_start_x, box_start_y, box_end_x, box_end_y, drawing_area.shape[1], drawing_area.shape[0])
            boxes.append([box_start_x, box_start_y, box_end_x, box_end_y])
        elif drawing is True:
            drawing = False
            (start_x, start_y, end_x, end_y) = top_left_bottom_right_box(start_x, start_y, end_x, end_y)
            (box_start_x, box_start_y, box_end_x, box_end_y) = fit_bounding_box(start_x, start_y, end_x, end_y, drawing_area.shape[1], drawing_area.shape[0])
            boxes.append([box_start_x, box_start_y, box_end_x, box_end_y])
        elif changing_shape is True:
            changing_shape = False
            (box_start_x, box_start_y, box_end_x, box_end_y) = change_bounding_box(box_to_shift, start_x, start_y, end_x, end_y)
            (box_start_x, box_start_y, box_end_x, box_end_y) = fit_bounding_box(box_start_x, box_start_y, box_end_x, box_end_y, drawing_area.shape[1], drawing_area.shape[0])
            boxes.append([box_start_x, box_start_y, box_end_x, box_end_y])


# The images are not the same and you want to mark the bounding box.
def get_new_image():
    current_image = images_to_show.pop()
    print("Reading %s" % current_image)
    firefox_screenshot = cv2.imread("data/%s_firefox.png" % current_image)
    chrome_screenshot = cv2.imread("data/%s_chrome.png" % current_image)
    if firefox_screenshot.shape != chrome_screenshot.shape:
        return 0
    drawing_area_firefox = reset_bounding_boxes(firefox_screenshot.shape)
    drawing_area_chrome = reset_bounding_boxes(chrome_screenshot.shape)
    boxes_firefox, boxes_chrome = [], []
    cv2.setMouseCallback('firefox', draw_bounding_boxes, [drawing_area_firefox, boxes_firefox])
    cv2.setMouseCallback('chrome', draw_bounding_boxes, [drawing_area_chrome, boxes_chrome])
    visibility = 1
    while True:
        firefox_window = cv2.addWeighted(drawing_area_firefox, 1 - visibility, firefox_screenshot, visibility, 0)
        chrome_window = cv2.addWeighted(drawing_area_chrome, 1 - visibility, chrome_screenshot, visibility, 0)
        firefox_chrome_overlay = cv2.addWeighted(firefox_screenshot, 0.5, chrome_screenshot, 0.5, 0)
        cv2.imshow('firefox', firefox_window)
        cv2.imshow('chrome', chrome_window)
        cv2.imshow('firefox_chrome_overlay', firefox_chrome_overlay)
        cv2.moveWindow('firefox', 20, 0)
        cv2.moveWindow('chrome', 20 + firefox_window.shape[1], 0)
        cv2.moveWindow('firefox_chrome_overlay', 20 + firefox_window.shape[1] + chrome_window.shape[1], 0)
        k = cv2.waitKey(1) & 0xFF
        # <Escape> quits marking area without saving
        if k == key_map["Escape"]:
            cv2.destroyAllWindows()
            return 1
        # 'r' resets the present selection of bounding boxes
        elif k == key_map["r"]:
            drawing_area_firefox = reset_bounding_boxes(firefox_screenshot.shape)
            drawing_area_chrome = reset_bounding_boxes(chrome_screenshot.shape)
            boxes_chrome, boxes_firefox = [], []
            cv2.setMouseCallback('firefox', draw_bounding_boxes, [drawing_area_firefox, boxes_firefox])
            cv2.setMouseCallback('chrome', draw_bounding_boxes, [drawing_area_chrome, boxes_chrome])
        # <Return> saves the current marking and moves to next image
        elif k == key_map["Enter"]:
            bounding_boxes[current_image + '_firefox'] = boxes_firefox
            bounding_boxes[current_image + '_chrome'] = boxes_chrome
            return 0
        # <Space> skips the labeling of current image
        elif k == key_map["Space"]:
            if current_image not in labels.keys():
                return 0
        elif k == key_map["y"]:
            labels[current_image] = 'y'
            return 0
        elif k == key_map["n"]:
            labels[current_image] = 'n'
            visibility = 0.5
        elif k == key_map["d"]:
            labels[current_image] = 'd'
            visibility = 0.5


def main():
    while len(images_to_show):
        if get_new_image():
            break
    # Store results.
    utils.write_bounding_boxes(bounding_boxes, labels_directory + args.file_name + "_bounding_box.json")
    utils.write_labels(labels, labels_directory + args.file_name + ".csv")


if __name__ == '__main__':
    main()
