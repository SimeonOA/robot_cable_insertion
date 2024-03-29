from ur5py import UR5Robot
import numpy as np
from autolab_core import RigidTransform
import pdb
from real_sense_modules import *
import matplotlib.pyplot as plt
from calibration.image_robot import ImageRobot

    
    
class GasketAssembly():
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


        return rw_pt

if __name__=='__main__':
    ur = UR5Robot()
    rot = np.array([[-1, 0, 0],
                    [0, 1, 0],
                    [0, 0, -1]])
    # trans = np.array([52.3, -473.5, -30])/ 1000
    
    # input('enter to enter freedrive')
    # ur.start_teach()
    # input('enter tro end freedrive')
    # ur.stop_teach()
    

    pipeline, colorizer, align, depth_scale = setup_rs_camera()
    rs_color_image, scaled_depth_image, aligned_depth_frame = get_rs_image(pipeline, align, depth_scale, use_depth=False)
    # rs_color_image = cv2.resize(rs_color_image, (640, 480))
    CROP_REGION = [120, 360, 130, 460]
    x_crop = [120, 360]
    y_crop = [130, 460]
    CROP_REGION = [136, 600, 321, 940]
    x_crop = [136, 600]
    y_crop = [321, 940]
    color_image = rs_color_image[x_crop[0]:x_crop[1], y_crop[0]:y_crop[1]]
    color_image = cv2.cvtColor(color_image, cv2.COLOR_BGR2RGB)

    ir = ImageRobot()
    ir.train_model()
    image_pt = [269.4,184]
    
    plt.scatter(y=image_pt[1], x=image_pt[0])
    plt.imshow(color_image)
    plt.show()
    rw_pt  = ir.image_pt_to_rw_pt(image_pt)
    trans = np.array([rw_pt[0], rw_pt[1], -15])/ 1000
    rt_pose = RigidTransform(rotation=rot, translation=trans)
    ur.move_pose(rt_pose)

    # 4
    gasket = GasketAssembly()
    gasket.load_calibration_params()
    # y,x format
    #this should ideally have the robot go to marker 11 on the workspace
    image_pt = [138, 49]
    rw_pt = gasket.image_pt_to_rw_pt(image_pt)
    breakpoint()
    trans = np.array([rw_pt[0], rw_pt[1], -15])/ 1000
    rt_pose = RigidTransform(rotation=rot, translation=trans)
    ur.move_pose(rt_pose)
    