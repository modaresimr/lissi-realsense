from realsensewrapper import RealSense
import cv2
def convert(bagfile):
    from pathlib import Path
    dst=Path(bagfile).parent.absolute()
    bag=RealSense('file',1)
    bag.readFromFile(bagfile)
    streams=bag.selected_profiles
    print(streams)
    # fourcc=cv2.VideoWriter_fourcc('F','M','P','4')
    fourcc=cv2.VideoWriter_fourcc(*'mp4v')
    videos={s:cv2.VideoWriter(f'{dst}/{s}.avi',fourcc, streams[s]['fps'], (streams[s]['width'], streams[s]['height']),'Infrared' not in s) for s in streams}

    try:
        i=0
        while True:
            i+=1
            if i%120:print(i,end='\r') 
            # Wait for a coherent pair of frames: depth and color
            frames=bag.waitForFrame()

            for img_key in frames:
                img=frames[img_key]
                videos[img_key].write(img)

    except (KeyboardInterrupt, Exception) as e:
        if not (type(e) is KeyboardInterrupt):
            import traceback
            traceback.print_exc()
    finally:
        bag.stop()
        cv2.destroyAllWindows()
        [videos[k].release() for k in videos]



convert('C:/D/Projects/lissi/lissi-realsense/test/full.bag')