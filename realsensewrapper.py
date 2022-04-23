import pyrealsense2 as rs


class RealSense:

    def __init__(self,ip,debug=0,infrared=0,depth=0):
        self.debug=debug;
        self.ip=ip
        self.infrared=infrared
        self.depth=depth
        self.connect()

    def connect(self):
        ctx = rs.context()

        debug=self.debug
        ip=self.ip

        if debug:print ('Connecting to ' + ip)
        if (ip=='webcam'):
            import cv2
            self.cam=cv2.VideoCapture(0)
            # self.cam=cv2.VideoCapture("C:/data-ar/kmoulouel/walking/06-04-2022-16-23-07/cam2/Color.mp4")
            _,f=self.cam.read()
            w = f.shape[1]
            h = f.shape[0]

            self.selected_profiles={'Color':{
            'width':w,
            'height':h,
            'fps':30,
            'format':0,
            'res':w*h,
            'type':'Color',
            'is_color':True
            }}
            print(self.selected_profiles)
            return
        elif (ip=='usb'):
            dev=rs.device();
            if debug: print(list(ctx.query_devices()));
            dev=ctx.query_devices()[0];
        else:
            import pyrealsense_net as rsnet
            dev = rsnet.net_device(ip)
            dev.add_to(ctx)

        if debug: print ('Connected')
        if debug: print ('Using device 0,', dev.get_info(rs.camera_info.name), ' Serial number: ', dev.get_info(rs.camera_info.serial_number))

        self.selected_profiles=self.find_profiles(dev)
        
        
        if debug: print(f'selected profiles: {self.selected_profiles}')

    def start(self):
        if self.ip=="webcam":return
        ctx = rs.context()
        self.pipeline = rs.pipeline(ctx)
        config = rs.config()
        color_profile=self.selected_profiles['Color']
        if self.depth:
            depth_profile=self.selected_profiles['Depth']
        if self.infrared:
            infrared_profile1=self.selected_profiles['Infrared1']
            infrared_profile2=self.selected_profiles['Infrared2']
        config.enable_stream(rs.stream.color, color_profile['width'], color_profile['height'], color_profile['format'], color_profile['fps'])
        


        if self.depth:
            config.enable_stream(rs.stream.depth, depth_profile['width'], depth_profile['height'], depth_profile['format'], depth_profile['fps'])
        if self.infrared:
            config.enable_stream(rs.stream.infrared,1, infrared_profile1['width'], infrared_profile1['height'], infrared_profile1['format'], infrared_profile1['fps'])
            config.enable_stream(rs.stream.infrared,2, infrared_profile2['width'], infrared_profile2['height'], infrared_profile2['format'], infrared_profile2['fps'])

        # if save_path:config.enable_record_to_file(save_path)
        
        
        self.profile= self.pipeline.start(config)
        # sensor_color = self.profile.get_device().first_color_sensor()
        # sensor_color.set_option(rs.option.enable_auto_exposure, True)
        # self.colorizer=rs.colorizer()
        # holefilter=rs.temporal_filter()
        # holefilter.set_option(rs.option.holes_fill, 1);
        # self.filters = [
        #     # rs.decimation_filter (),
        #     rs.spatial_filter(),
        #     rs.temporal_filter(),
        #     holefilter
        # ]
        

    def readFromFile(self,bagfile):
        self.pipeline = rs.pipeline()
        # Create a config object
        config = rs.config()
        rs.config.enable_device_from_file(config,bagfile)
        config.enable_all_streams()
        self.pipeline.start(config)
        self.colorizer=rs.colorizer()
        self.selected_profiles=self.find_profiles(pipeline=self.pipeline)

    def waitForFrame(self,colorize=True):
        if self.ip=='webcam':
            _,c=self.cam.read()
            return {'Color':c,'frame':1}
        import numpy as np
        try:
            frames = self.pipeline.wait_for_frames(100)
        except:
            return 
        
        # print(f"{frames}")
        if self.depth:
            depth_frame = frames.get_depth_frame()
        color_frame = frames.get_color_frame()
        if self.infrared:
            infrared_frame1 = frames.get_infrared_frame(1)
            infrared_frame2 = frames.get_infrared_frame(2)
        
        if self.depth and not depth_frame:
            if self.debug:print(f'error depth {depth_frame} frame not received')
        if not color_frame:
            if self.debug:print(f'error color {color_frame} frame not received')
            return
        # depth_frame = self.post_processing_depth(depth_frame)
        if self.depth:
            if colorize:
                depth_color_frame = self.colorizer.colorize(depth_frame)
            else: 
                depth_color_frame = depth_frame
        

        res={}
        if self.depth:
            res['Depth'] = np.asanyarray(depth_color_frame.get_data())
        
        res['Color'] = np.asanyarray(color_frame.get_data())
        if self.infrared:
            res['Infrared1'] = np.asanyarray(infrared_frame1.get_data())
            res['Infrared2'] = np.asanyarray(infrared_frame2.get_data())

        res['frame']=frames.get_frame_number()

        
        # Apply colormap on depth image (image must be converted to 8-bit per pixel first)
        # depth_colormap = cv2.applyColorMap(cv2.convertScaleAbs(depth_image, alpha=0.03), cv2.COLORMAP_JET)

        return res

    def post_processing_depth(self,input):
        processed = input;
        for f in self.filters:
            processed=f.process(processed)
        
        return processed;


    def stop(self):
        if self.ip=='webcam':
            self.cam.release()
        else:
            self.pipeline.stop();
        # rs.context().close();

    def find_profiles(self,dev=None,pipeline=None):
        if pipeline is None:
            raw_profiles=[p.as_video_stream_profile() for s in dev.query_sensors() for p in s.get_stream_profiles()]
        else:
            raw_profiles=[p.as_video_stream_profile()  for p in pipeline.get_active_profile().get_streams()]
        all_profiles=[{
            'width':p.width(),
            'height':p.height(),
            'fps':p.fps(),
            'format':p.format(),
            'res':p.height()*p.width(),
            'type':p.stream_name(),
            'is_color':'Infrared' not in p.stream_name()
            } for p in raw_profiles]

        # if debug: print(f"available profiles: ${self.info_profiles}")
        
        res={}
        res['Color']=self.get_best_profile(all_profiles,'Color')
        dep_p=None
        if self.depth:
            res['Depth']=self.get_best_profile(all_profiles,'Depth')
            dep_p=res['Depth']
        if self.infrared:
            res['Infrared1']=self.get_best_profile(all_profiles,'Infrared 1',dep_p)
            res['Infrared2']=self.get_best_profile(all_profiles,'Infrared 2',dep_p)
        print(res)
        return res

    def get_best_profile(self,all_profiles,typ,match_profile=None):
        best=None
        for p in all_profiles:
            if not (typ in p['type']):continue
            if match_profile!=None and ( p['width']!=match_profile['width'] or p['height']!=match_profile['height']):
                continue
            if best==None or best['res']<p['res'] or best['res']==p['res'] and best['fps']<p['fps']:
                best=p
        return best