from ur5py import UR5Robot
import numpy as np
from shape_match import *
from autolab_core import RigidTransform
import pdb
from real_sense_modules import *
from utils import *
import argparse
from gasketRobot import GasketRobot


argparser = argparse.ArgumentParser()
# options for experiment type, either 'no_ends' or 'one_end'
argparser.add_argument('--exp', type=str, default='no_ends_attached')
# options for where to push on channel: 'unidirectional', 'golden', 'binary', 'slide'
argparser.add_argument('--push_mode', type=str, default='unidirectional')
# options for where to pick the cable at: 'unidirectional', 'golden', 'binary', 'slide'
argparser.add_argument('--pick_mode', type=str, default='unidirectional')
    
    
class CameraCalibration():
    def __init__(self):
        pass

    def load_calibration_params(self):
        self.use_pick_pt_depth = False
        self.use_hardcoded_cal = True

        self.x_intercept = 150.1111247
        self.x_coef_on_x = -2.07787301 #* (360-140)/(360-120)
        self.x_coef_on_y = 0.02772887548

        self.y_intercept = -759.9587912
        self.y_coef_on_y = 2.069261384
        self.y_coef_on_x = 0.02158838398

        # UPPER PLANE VALUES
        self.upper_height_value = 1.582
        self.upper_z_value = 150

        self.upper_x_intercept = 72.43845257
        self.upper_x_coef_on_x = -1.665
        self.upper_x_coef_on_y = 0.01

        self.upper_y_intercept = -709.8271378
        self.upper_y_coef_on_y = 1.656541759
        self.upper_y_coef_on_x = 0.03923585725

        self.surface_height_value = 1.255
        self.surface_z_value = -16

        f_x = -0.4818473759
        c_x = 73.77723968

        f_y = 0.4821812388
        c_y = 365.0698399

        self.K = np.array([[f_x, 0, c_x], [0, f_y, c_y], [0, 0, 1]])

        # depth * np.linalg.inv(self.K) * np.r_[pixel, 1.0]

    def image_pt_to_rw_pt(self, image_pt, depth=None):
		#reversed_image_pt = [image_pt[1], image_pt[0]]

		#self.x_intercept = 150.1111247
		#self.x_coef_on_x = -2.07787301
		#self.x_coef_on_y = 0.02772887548

		#self.y_intercept = -759.9587912
		#self.y_coef_on_y = 2.069261384
		#self.y_coef_on_x = 0.02158838398
		
        if depth is not None:
            pass
            # height = 800 - depth

            # height_fraction = height/(self.upper_z_value - self.surface_z_value)

            # print("height fraction:" + str(height_fraction))

            # image_pt_tr = self.cam_scaler.transform([image_pt])
            # rw_pt_surface = self.cam_model.predict(image_pt_tr)

            # rw_pt_upper = [0,0]
            # rw_pt_upper[0] = self.upper_x_intercept + self.upper_x_coef_on_x*image_pt[0] + self.upper_x_coef_on_y*image_pt[1]
            # rw_pt_upper[1] = self.upper_y_intercept + self.upper_y_coef_on_x*image_pt[0] + self.upper_y_coef_on_y*image_pt[1]

            # print(rw_pt_upper)
            # print(rw_pt_surface)

            # rw_pt_surface = np.array(rw_pt_surface)
            # rw_pt_upper = np.array(rw_pt_upper)
            
            # if height_fraction > 0.15:
            #     rw_pt = height_fraction * rw_pt_upper + (1 - height_fraction) * rw_pt_surface
            # else:
            #     rw_pt = rw_pt_surface

        else:
            if self.use_hardcoded_cal:
                rw_pt = [0,0]
                rw_pt[0] = self.x_intercept + self.x_coef_on_x*image_pt[1] + self.x_coef_on_y*image_pt[0]
                rw_pt[1] = self.y_intercept + self.y_coef_on_x*image_pt[1] + self.y_coef_on_y*image_pt[0]

            # else:
            #     image_pt_tr = self.cam_scaler.transform([image_pt])
            #     rw_pt = self.cam_model.predict(image_pt_tr)


        return np.array(rw_pt)

def detect_cable(rgb_img):
    # Detecting the cable
    cable_cnt, cable_mask_hollow  = get_cable(img = rgb_img)
        
    cable_cnt = cable_cnt + np.array([CROP_REGION[2], CROP_REGION[0]])
    cable_mask_binary = np.zeros(rgb_img.shape, np.uint8)
    cv.drawContours(cable_mask_binary, [cable_cnt], -1, (255,255,255), -1)

    cable_skeleton = skeletonize(cable_mask_binary)
    cable_length, cable_endpoints = find_length_and_endpoints(cable_skeleton)
    assert len(cable_endpoints) == 2
    return cable_skeleton, cable_length, cable_endpoints, cable_mask_binary

def detect_channel(rgb_img, cable_mask_binary):
    # Detecting the channel
    matched_template, matched_results, channel_cnt, _ = get_channel(img = rgb_img, cable_mask=cable_mask_binary)
    
    if matched_template == 'curved':
        template_mask = curved_template_mask
    elif matched_template == 'straight':
        template_mask = straight_template_mask
    elif matched_template == 'trapezoid':
        template_mask = trapezoid_template_mask
    aligned_channel_mask = align_channel(template_mask, matched_results, rgb_img, channel_cnt, matched_template) 
    # making it 3 channels
    aligned_channel_mask = cv2.merge((aligned_channel_mask, aligned_channel_mask, aligned_channel_mask))
    aligned_channel_mask = aligned_channel_mask.astype('uint8')
    plt.imshow(rgb_img)
    plt.imshow(aligned_channel_mask, alpha=0.5)
    plt.show()

    # skeletonizing the channel
    channel_skeleton = skeletonize(aligned_channel_mask)
    plt.imshow(rgb_img)
    plt.imshow(channel_skeleton, alpha=0.5, cmap='jet')
    plt.show()
    #getting the length and endpoints of the channel
    channel_length, channel_endpoints = find_length_and_endpoints(channel_skeleton)
    if len(channel_endpoints) == 1:
        print("We have a loop!")
    return channel_skeleton, channel_length, channel_endpoints, matched_template

def find_closest_point(point_list, point_b):
    # Convert the input lists to NumPy arrays for easier computation
    points = np.array(point_list)
    b = np.array(point_b)
    
    # Calculate the Euclidean distance between point B and each point in the list
    distances = np.linalg.norm(points - b, axis=1)
    
    # Find the index of the point with the smallest distance
    closest_index = np.argmin(distances)
    
    # Retrieve the closest point from the original list
    closest_point = point_list[closest_index]
    
    return closest_point

def get_sorted_pts(cable_endpoints, channel_endpoints, cable_skeleton, depth_img = None):
    # just pick an endpoint to be the one that we'll use as our in point
    cable_endpoint_in = cable_endpoints[0]
    channel_endpoint_in, channel_endpoint_out = get_closest_channel_endpoint(cable_endpoint_in, channel_endpoints)
    sorted_channel_pts = sort_skeleton_pts(channel_skeleton, channel_endpoint_in)
    sorted_cable_pts = sort_skeleton_pts(cable_skeleton, cable_endpoint_in)

    # filter out points that are invalid/unreasonable in the depth image
    if depth_img is not None:
        pass
        # # WARNING: seems like the depth are expecting the x and y to be flipped!!!!
        # swapped_sorted_cable_pts = [(pt[1], pt[0]) for pt in sorted_cable_pts]
        # swapped_sorted_channel_pts = [(pt[1], pt[0]) for pt in sorted_channel_pts]
        # filtered_cable_pts = filter_points(swapped_sorted_channel_pts, depth_img)
        # filtered_channel_pts = filter_points(swapped_sorted_channel_pts, depth_img)
        # # NOTICE THAT THTESE ARE NOW SWAPPED!!!

    # these are aslo now swapped!
    channel_endpoint_in = sorted_channel_pts[0]
    channel_endpoint_out = sorted_channel_pts[-1]

    cable_endpoint_in = sorted_cable_pts[0]
    cable_endpoint_out = sorted_cable_pts[-1]

    # TODO CHECK IF THIS IS WORKING PROPERLY!!!!
    # IDEA: update the channel startpoint to be the closest point on the channel skeleton to the cable endpoint
    # then actually delete the indices before that point from sorted_channel_pts
    
    # channel_endpoint_in = find_closest_point(sorted_channel_pts, cable_endpoint_in)
    # sorted_channel_pts = sorted_channel_pts[sorted_channel_pts.index(channel_endpoint_in):]

    return sorted_cable_pts, sorted_channel_pts

def find_nth_nearest_point(point, sorted_points, n):
    # print(endpoint)
    # print(np.array(sorted_points).shape, np.array(endpoint).shape)
    # np.linalg.norm(np.array(sorted_points) - np.array(endpoint))
    if point == sorted_points[0]:
        return sorted_points[n - 1]
    elif point == sorted_points[-1]:
        return sorted_points[-n]
    idx = sorted_points.index(point)
    if np.linalg.norm(np.array(point)-np.array(sorted_points[0])) < np.linalg.norm(np.array(point)-np.array(sorted_points[-1])):
        return sorted_points[idx + n - 1]
    else:
        return sorted_points[idx - n]

def get_rotation(point1, point2):
    direction = np.array(point2) - np.array(point1)
    direction = direction / np.linalg.norm(direction) #unit vector

    reference_direction = np.array([1,0])
    cos_theta = np.dot(direction, reference_direction)
    sin_theta = np.sqrt(1 - cos_theta**2)
    dz = np.arctan2(sin_theta, cos_theta)
    return np.array([-np.pi, 0, dz])



def get_rw_pose(orig_pt, sorted_pixels, n, ratio, camCal, use_depth = False):
    next_point = find_nth_nearest_point(orig_pt, sorted_pixels, n)
    offset_point = find_nth_nearest_point(orig_pt, sorted_pixels, int(len(sorted_pixels)*ratio))
    breakpoint()
    orig_rw_xy = camCal.image_pt_to_rw_pt(orig_pt) 
    next_rw_xy = camCal.image_pt_to_rw_pt(next_point)   
    offset_rw_xy = camCal.image_pt_to_rw_pt(offset_point)
    rot = get_rotation(orig_rw_xy, next_rw_xy)
    orig_rw_xy = orig_rw_xy / 1000

    # want this z height to have the gripper when closed be just barely above the table
    # will need to tune!
    if not use_depth:
        hardcoded_z = -30
        orig_rw = np.array([orig_rw_xy[0], orig_rw_xy[1],hardcoded_z/1000])
    else:
        print("haven't implemented using depth for pick/place!")
        raise ValueError()
    # converting pose to rigid transform to use with ur5py library
    orig_rt_pose = RigidTransform(rotation=rot, translation=orig_rw)
    return orig_rt_pose

# gets rigid transform given pose

def no_ends_attached(cable_mask_binary, cable_endpoints, channel_endpoints, camCal, use_depth = False):
    cable_skeleton = skeletonize(cable_mask_binary)
    plt.imshow(cable_skeleton)
    plt.show()
    cable_length, cable_endpoints = find_length_and_endpoints(cable_skeleton)
    plt.scatter(x=[i[1] for i in cable_endpoints], y=[i[0] for i in cable_endpoints])
    plt.imshow(rgb_img)
    plt.show()

    plt.imshow(rgb_img)
    plt.imshow(cable_skeleton, alpha=0.5)
    plt.show()


    
    sorted_cable_pts, sorted_channel_pts = get_sorted_pts(cable_endpoints, channel_endpoints, cable_skeleton)


    pick_pt = sorted_cable_pts[0]
    place_pt = sorted_channel_pts[0]
    plt.scatter(x=pick_pt[0], y=pick_pt[1], c='r')
    plt.scatter(x=place_pt[0], y=place_pt[1], c='b')
    plt.imshow(rgb_img)
    plt.show()

    pick_pose = get_rw_pose(pick_pt, sorted_cable_pts, 20, 0.1, camCal)


    breakpoint()
    robot.move_pose(pick_pose)
    
    place_pose = get_rw_pose(place_pt, sorted_channel_pts, 20, 0.1, camCal)
    # only do this when no ends attached cause we dont care about dragging the rope
    # z offset for height of channel 
    place_pose[2] += TEMPLATE_HEIGHT[matched_template]
    robot.move_pose(place_pose)
    robot.close_grippers()

    robot.move_to_channel_overhead(transformed_channel_end, rotation)
    robot.push(transformed_channel_end, rotation)
    robot.go_home()
    robot.open_grippers()

def one_end_attached(cable_mask_binary, cable_endpoints, channel_endpoints, camCal):
    pass



curved_template_mask = cv.imread('template_masks/processed_new_curved_mask.jpg')
# curved_template_mask = cv.imread('template_masks/master_curved_fill_template.png')
straight_template_mask = cv.imread('template_masks/master_straight_channel_template.png')
trapezoid_template_mask = cv.imread('template_masks/master_trapezoid_channel_template.png')

TEMPLATES = {0:'curved', 1:'straight', 2:'trapezoid'}
# curved is 2.54cm high, straight is 1.5cm high, trapezoid is 2cm high
TEMPLATE_HEIGHT = {'curved':0.0254, 'straight':0.015, 'trapezoid':0.02}
# first elem is currved width/height, second elem is straight width/height, third elem is trapezoid width/height
TEMPLATE_RECTS = [(587.4852905273438, 168.0382080078125),(2.75, 26.5), (12, 5.75)]
TEMPLATE_RATIOS = [max(t)/min(t) for t in TEMPLATE_RECTS]
# [minY, maxY, minX, maxX]
CROP_REGION = [82, 392, 110, 492]
TOTAL_PICK_PLACE = 5


if __name__=='__main__':
    args = argparser.parse_args()
    PUSH_MODE = args.push_mode
    PICK_MODE = args.pick_mode
    EXP_MODE = args.exp
    robot = GasketRobot()

    # Sets up the realsense and gets us an image
    pipeline, colorizer, align, depth_scale = setup_rs_camera()
    color_img, scaled_depth_image, aligned_depth_frame = get_rs_image(pipeline, align, depth_scale, use_depth=False)
    rgb_img = cv2.cvtColor(color_img, cv2.COLOR_BGR2RGB)

    # loads parameters for camera calibration
    camCal = CameraCalibration()
    camCal.load_calibration_params()

    # gets initial state of cable and channel
    cable_skeleton, cable_length, cable_endpoints, cable_mask_binary = detect_cable(rgb_img)
    channel_skeleton, channel_length, channel_endpoints, matched_template = detect_channel(rgb_img, cable_mask_binary)

    # performs the experiment given no ends are attached to the channel
    if EXP_MODE == 'no_ends':
        no_ends_attached(cable_mask_binary, cable_endpoints, channel_endpoints, camCal)
    # even if we are doing no_ends_attached we simply 
    # need to attach one end then we can run the program as if it was always just one end attached        
    one_end_attached(cable_mask_binary, cable_endpoints, channel_endpoints, camCal)