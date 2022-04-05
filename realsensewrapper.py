import pyrealsense2 as rs


class RealSense:

    def __init__(self,ip,debug=0):
        self.debug=debug;
        self.ip=ip


    def connect(self,save_path=None):
        ctx = rs.context()

        debug=self.debug
        ip=self.ip

        if debug:print ('Connecting to ' + ip)
        if (ip=='usb'):
            dev=rs.device();
            if debug: print(list(ctx.query_devices()));
            dev=ctx.query_devices()[0];
        else:
            dev = rsnet.net_device(ip)
            dev.add_to(ctx)

        if debug: print ('Connected')
        if debug: print ('Using device 0,', dev.get_info(rs.camera_info.name), ' Serial number: ', dev.get_info(rs.camera_info.serial_number))

        self.selected_profiles=self.find_profiles(dev)
        color_profile=self.selected_profiles['Color']
        depth_profile=self.selected_profiles['Depth']
        infrared_profile1=self.selected_profiles['Infrared1']
        infrared_profile2=self.selected_profiles['Infrared2']
        
        if debug: print(f'selected profiles: {color_profile} {depth_profile} {infrared_profile1} {infrared_profile2}')


        self.pipeline = rs.pipeline(ctx)
        config = rs.config()

        config.enable_stream(rs.stream.depth, depth_profile['width'], depth_profile['height'], depth_profile['format'], depth_profile['fps'])
        # config.enable_stream(rs.stream.depth, depth_profile['width'], depth_profile['height'], rs.format.z16, depth_profile['fps'])
        config.enable_stream(rs.stream.color, color_profile['width'], color_profile['height'], color_profile['format'], color_profile['fps'])
        config.enable_stream(rs.stream.infrared,1, infrared_profile1['width'], infrared_profile1['height'], infrared_profile1['format'], infrared_profile1['fps'])
        config.enable_stream(rs.stream.infrared,2, infrared_profile2['width'], infrared_profile2['height'], infrared_profile2['format'], infrared_profile2['fps'])

        if save_path:
            config.enable_record_to_file(save_path)

        self.profile= self.pipeline.start(config)


    def waitForFrame(self):
        import numpy as np
        import cv2
        frames = self.pipeline.wait_for_frames()
        depth_frame = frames.get_depth_frame()
        color_frame = frames.get_color_frame()
        infrared_frame1 = frames.get_infrared_frame(1)
        infrared_frame2 = frames.get_infrared_frame(2)

        if not depth_frame or not color_frame:
            if self.debug:print('error color or depth frame not received')
            return

        depth_image = np.asanyarray(depth_frame.get_data())
        color_image = np.asanyarray(color_frame.get_data())
        infrared_image1 = np.asanyarray(infrared_frame1.get_data())
        infrared_image2 = np.asanyarray(infrared_frame2.get_data())

        # Apply colormap on depth image (image must be converted to 8-bit per pixel first)
        depth_colormap = cv2.applyColorMap(cv2.convertScaleAbs(depth_image, alpha=0.03), cv2.COLORMAP_JET)

        return {'Depth':depth_colormap, 'Color':color_image,
                'Infrared1':infrared_image1,'Infrared2':infrared_image2
                }


    def stop(self):
        self.pipeline.stop();
        # rs.context().close();

    def find_profiles(self,dev):
        
        raw_profiles=[p.as_video_stream_profile() for s in dev.query_sensors() for p in s.get_stream_profiles()]
        all_profiles=[{'width':p.width(),'height':p.height(),'fps':p.fps(),'format':p.format(),'res':p.height()*p.width(),'type':p.stream_name()} for p in raw_profiles]
        # if debug: print(f"available profiles: ${self.info_profiles}")
        
        color_profile=self.get_best_profile(all_profiles,'Color')
        depth_profile=self.get_best_profile(all_profiles,'Depth')
        infrared_profile1=self.get_best_profile(all_profiles,'Infrared 1',depth_profile)
        infrared_profile2=self.get_best_profile(all_profiles,'Infrared 2',depth_profile)
        
        return {'Color':color_profile,'Depth':depth_profile,
                                'Infrared1':infrared_profile1,'Infrared2':infrared_profile2
                                }
    def get_best_profile(self,all_profiles,typ,match_profile=None):
        best=None
        for p in all_profiles:
            if not (typ in p['type']):continue
            if match_profile!=None and ( p['width']!=match_profile['width'] or p['height']!=match_profile['height']):
                continue
            if best==None or best['res']<p['res'] or best['res']==p['res'] and best['fps']<p['fps']:
                best=p
        return best