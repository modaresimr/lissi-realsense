import pickle
import pyrealsense2 as rs
import os
import cv2
import json
import math
import utils

class MyReader:

    def __init__(self, path):
        with open(f'{path}/meta.pkl', 'rb') as f:
            self.meta = pickle.load(f)
        self.color_path = f'{path}/{self.meta["color_folder"]}'
        self.depth_path = f'{path}/{self.meta["depth_folder"]}'
        self.intrinsics=utils.intrinsics_from_obj(self.meta['profiles']['Color']['intrinsics'])
        self.max_frame = max(
            [int(d.split('.')[0]) for d in os.listdir(self.color_path)])
        self.current_frame = 0

    def current_path(self, type):
        if type == 'color':
            return f'{self.color_path}/{self.current_frame}{self.meta["color_ext"]}'
        return f'{self.depth_path}/{self.current_frame}{self.meta["depth_ext"]}'

    def eof(self):
        return self.current_frame > self.max_frame
    
    def seek(self,frame):
        self.current_frame=frame
        self.current_color = None
        self.current_depth = None
        
        cpath=self.current_path('color')
        dpath=self.current_path('depth')
        
        if os.path.exists(cpath):
            self.current_color = cv2.imread(cpath, -1)
        if os.path.exists(dpath):
            self.current_depth = cv2.imread(dpath, -1)
        return not (self.current_depth is None or self.current_color  is None)

    def next(self):
        self.current_frame += 1
        
        while not self.eof() and not self.seek(self.current_frame):
            
        # while not self.eof() and (
        #         not os.path.exists(self.current_path('color'))
        #         or not os.path.exists(self.current_path('depth'))):
            # print(f'missing frame={self.current_frame}',end='\r')
            self.current_frame += 1

        if self.eof():
            self.current_color = None
            self.current_depth = None

        return self.current_color, self.current_depth

    def colorize_current_depth(self):
       absdepth=cv2.convertScaleAbs(self.current_depth, alpha=0.025)
       return cv2.applyColorMap(absdepth, cv2.COLORMAP_JET)

	def get_depth(self,x,y):
		return self.current_depth[y][x] * self.meta['depth_scale'] 
		
    def get_point(self, x, y):
        d = self.get_depth(x,y)
        return rs.rs2_deproject_pixel_to_point(
            self.intrinsics, [x, y], d)

    def get_distance(self, x1, y1, x2, y2):
        point1 = self.get_point(x1, y1)
        point2 = self.get_point(x2, y2)

        return math.sqrt(
            math.pow(point1[0] - point2[0], 2) +
            math.pow(point1[1] - point2[1], 2) +
            math.pow(point1[2] - point2[2], 2))

    def to_point_cloud(self):
        pc = rs.pointcloud()
        pc.map_to(self.current_color)
        pointcloud = pc.calculate(self.current_depth)
        return pointcloud
