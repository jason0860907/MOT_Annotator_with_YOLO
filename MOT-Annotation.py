import cv2, numpy as np
import argparse
import os

# Construct the argument parser
ap = argparse.ArgumentParser()

# Add the arguments to the parser
ap.add_argument("-l", "--location", required=True, help="Path of the input video")
args = vars(ap.parse_args())

# Click on one corner of the image,
# then, click on the other corner on the image.
# The coordinates will be saved in gt/gt.txt

# Press 'esc' to quit
# Press 'n' for next frame

# Before you begin, change the path to you own video:
cap = cv2.VideoCapture(args['location'])

# Create a folder "det" for the detections in the same location as input video:
path_to_detection_folder, video_name = os.path.split(args['location']) 


# new_path = os.path.join(path_to_detection_folder, 'gt') 
video_name = video_name.split('.')[0]
new_path = './gt/'
yolo_det_path = './yolo_det/labels/{}'.format(video_name)


def check_point_in_bbx(points, bbx):
  '''
  points = [123, 456]  type: int
  bbx = [124.297, 141.75, 156.391, 221.625]  type: float
  '''
  x, y = points
  x1, y1, x2, y2 = bbx
  return (x1 < x < x2) and (y1 < y < y2)


if not os.path.exists(new_path):
  os.mkdir(new_path)


# mouse callback function
global click_list
global positions
global yolo_det_bbxes
global click_list2
positions, click_list, click_list2 = [], [], []

def callback(event, x, y, flags, param):
    if event == cv2.EVENT_MBUTTONDOWN: click_list.append((x,y))
    if event == cv2.EVENT_LBUTTONDOWN: click_list2.extend([x,y])
    positions.append((x,y))
    
cv2.namedWindow('img')
cv2.setMouseCallback('img', callback)

frame_number = 1
object_id = 1 # cannot be 0 or negative



#### read first image ####
ret, img_p = cap.read()

total_frame_num = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
cv2.putText(img_p, '1/{}'.format(total_frame_num), (100, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (36,255,12), 2)

with open("{}/1.txt".format(yolo_det_path), 'r') as det_file:
  yolo_det_bbxes = det_file.readlines()
  for bbx in yolo_det_bbxes:
    line = bbx.strip().split(' ')
    frame, tmp_id, obj_cls, x1, y1, x2, y2 = line
    x1, y1, x2, y2 = float(x1), float(y1), float(x2), float(y2)
    point1 = (int(x1), int(y1))
    point2 = (int(x2), int(y2))
    cv2.rectangle(img_p, point1, point2, (255, 0, 0), 2)
#### read first image ####



# get width and height of the original frame
w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

# calculate resize factor, this will be used to correct the bounding boxes
# as we are drawing them on a resized scale
rf_w = w/1280   # original fame width / rescaled width
rf_h = h/720  # original fame height / rescaled height

img_p = cv2.resize(img_p, (1280,720))

with open('{}/{}.txt'.format(new_path, video_name),'a') as out_file:
  while (cap.isOpened()):

    img = img_p.copy()

    if len(click_list)>0:

      mouse_position = positions[-1]

      a = click_list[-1][0], click_list[-1][1]
      b = mouse_position[0], click_list[-1][1]
      cv2.line(img, a, b, (123,234,123), 3)

      a = click_list[-1][0], mouse_position[1]
      b = mouse_position[0], mouse_position[1]
      cv2.line(img, a, b, (123,234,123), 3)

      a = mouse_position[0], click_list[-1][1]
      b = mouse_position[0], mouse_position[1]
      cv2.line(img, a, b, (123,234,123), 3)

      a = click_list[-1][0], mouse_position[1]
      b = click_list[-1][0], click_list[-1][1]
      cv2.line(img, a, b, (123,234,123), 3)

    '''
    mouse middle button (click two points) to get the bounding box
    '''
    if len(click_list) == 2: 

      #get the top left and bottom right
      a,b  = click_list

      # MOT 16 det,tx format
      # frame id, -1, xmin, ymin, width, height
      xmin = min(a[0],b[0])*rf_w
      ymin = min(a[1],b[1])*rf_h
      xmax = max(a[0],b[0])*rf_w
      ymax = max(a[1],b[1])*rf_h
      width = xmax-xmin
      height = ymax-ymin

      write_line = '%d,%d,%d,%d,%d,%d'%(frame_number,object_id,xmin,ymin,width,height)
      print(write_line,file=out_file)
      print(write_line)

      #reset the click list
      click_list = []
    
    '''
    mouse left button to map the yolo detection bounding box
    '''
    if len(click_list2) > 0:  # mouse left button
      x, y  = click_list2
      x = x * rf_w
      y = y * rf_h

      for bbx in yolo_det_bbxes:
        line = bbx.strip().split(' ')
        frame, tmp_id, obj_cls, x1, y1, x2, y2 = line
        x1, y1, x2, y2 = float(x1), float(y1), float(x2), float(y2)
        if check_point_in_bbx([x, y], [x1, y1, x2, y2]):
          width = x2 - x1
          height = y2 - y1
          write_line = '%d,%d,%d,%d,%d,%d,1,1,1'%(frame_number,object_id,x1,y1,width,height)
          print(write_line,file=out_file)
          print(write_line)
      click_list2 = []
    

    # show the image and wait
    cv2.imshow('img', img)
    k = cv2.waitKey(1)
    


    '''
    # escape if 'esc' is pressed
    # 27 is the ascii code for 'esc'
    '''
    if k == 27: break



    '''
    next image and show all the yolo detection bounding box 
    # read next image if 'n' is pressed
    # 110 is the ascii code for 'n'
    '''
    if k == 110:
      ret, img = cap.read()
      frame_number += 1
      
      cv2.putText(img, '{}/{}'.format(frame_number, total_frame_num), (100, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (36,255,12), 2)
      
      with open("{}/{}.txt".format(yolo_det_path, frame_number), 'r') as det_file:
        # print(det_file.readlines())
        yolo_det_bbxes = det_file.readlines()
        for bbx in yolo_det_bbxes:
          line = bbx.strip().split(' ')
          frame, tmp_id, obj_cls, x1, y1, x2, y2 = line
          point1 = (int(float(x1)), int(float(y1)))
          point2 = (int(float(x2)), int(float(y2)))
          cv2.rectangle(img, point1, point2, (255, 0, 0), 2)
          
      if not ret:
        break
      img_p = cv2.resize(img, (1280,720))



    '''
    # code to increment object id
    # press 'i' to increment object ID
    # 105 is ascii code for 'i'
    '''  
    if k == 105:
         object_id += 1
         print("object_id incremented to %d" %(object_id))
         


    '''
    # code to decrement object id
    # press 'd' to decrement object ID
    # 100 is ascii code for 'd'
    '''  
    if k == 100:
         object_id -= 1
         print("object_id decremented to %d" %(object_id))



cap.release()
cv2.destroyAllWindows()
