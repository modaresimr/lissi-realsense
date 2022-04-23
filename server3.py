from dataclasses import replace
import psutil

from http.server import BaseHTTPRequestHandler, HTTPServer
import time, threading
from multiprocessing import Process, JoinableQueue
import os
from urllib.parse import urlparse
print('starting...')
from realsensewrapper import RealSense
loc = {}
print('x')
import cv2
print('y')

def video_recorder(name,q,save_path,profile):
	if profile['type']=='Color':psutil.Process().cpu_affinity([2,3])
	if profile['type']=='Depth':psutil.Process().cpu_affinity([4,5])
	if 'Infrared' in profile['type']: psutil.Process().cpu_affinity([6,7])

	print(f'start recording {name} in cpu={psutil.Process().cpu_affinity()}')
	import numpy as np
	# codec = cv2.VideoWriter.fourcc(*'avc1')
	# codec = cv2.VideoWriter.fourcc(*'MJPG')
	codec = cv2.VideoWriter.fourcc(*'DIVX')
	
	vw=cv2.VideoWriter(f'{save_path}/{name}.avi',codec, profile['fps'], (profile['width'], profile['height']),profile['is_color'])
	# vw.write(np.zeros(profile['width'], profile['height'],3))
	while True:
	
		n,img = q.get()
		
		if n==-1:
			q.task_done()
			break
		# cv2.imshow(name,img)
		if name=='Depth':
			img = cv2.applyColorMap(cv2.convertScaleAbs(img, alpha=0.03), cv2.COLORMAP_JET)
		vw.write(img)
		q.task_done()
		
	vw.release()

class VideoCapture:
	def __init__(self,save_path):
		self.save_path=save_path
		import  shutil
		if os.path.exists(save_path):shutil.rmtree(save_path)
		os.makedirs(save_path,exist_ok=True)		
		# cam=RealSense("usb",debug=1,infrared=0,depth=1)
		self.cam=RealSense("usb",debug=1,infrared=0,depth=0)
		# self.cam.connect()
		self.streams=self.cam.selected_profiles
		
		# prcs={s: Process(target=video_recorder, args=(None,None,None,None)) for s in streams}
		self.info={
				'recorded_frame':0,
				'camera_frame':0,
				'current_time':0,
				'fps':0,
				'frame_in_q':0,
				'frame_loss':0,
				'size':0
		}
	
	
	def start(self):
		self.qs={s:JoinableQueue(1000) for s in self.streams}
		self.prcs={s: Process(name=s,target=video_recorder, args=(s,self.qs[s],self.save_path,self.streams[s])) for s in self.streams}
		for p in self.prcs:
			self.prcs[p].daemon=True
			self.prcs[p].start()
		self.working=True
		self.thread = threading.Thread(target=self.worker, name='VideoCapture', args=())
		self.thread.daemon = True
		self.thread.start()
		
		return self

	def stop(self):
		self.working=False
		self.cam.stop()	
		for s in self.streams:self.qs[s].put((-1,'eof')) 
		self.thread.join()
	def kill(self):
		self.cam.stop()	
		for s in self.streams:self.prcs[s].terminate() 

		
	def worker(self):
		cam=self.cam;qs=self.qs;prcs=self.prcs;streams=self.cam.selected_profiles
		i=0
		import time
		start_time = time.time()
		while self.working:
			frames = cam.waitForFrame(colorize=False)
			
			if frames is None:
				time.sleep(0.1)
				continue
			i+=1
			n=frames['frame']
			self.info={
				'recorded_frame':i,
				'camera_frame':n,
				'current_time':int(time.time() - start_time),
				'fps':int(i/(time.time() - start_time)),
				'frame_in_q':sum([qs[s].qsize() for s in qs]),
				'frame_loss':max(0,(n-i))*100/max(1,n),
				'size':convert_bytes(get_folder_size(self.save_path))
			}
			
			if i%30==0 or i<10:
				print(f"{self.info['current_time']:0.0f}s \tframe={n} \tqueue={self.info['frame_in_q']} \tframe_loss={self.info['frame_loss']:.0f}% size={self.info['size']}",end='\r')
			for s in streams:
				qs[s].put((n,frames[s]))	
		
		# for s in streams: qs[s].join()
		for s in streams:prcs[s].join()
		



def stopRecording():
	loc['videocapture'].stop()
	del loc['videocapture']



def startRecording(path):
	loc['videocapture']=VideoCapture(path).start()	
	loc['save_path']=f'{path}'

class Handler(BaseHTTPRequestHandler):
	def reply(self,msg,type="text/html"):
		self.send_response(200)
		self.send_header("Content-type", type)
		self.end_headers()
		self.wfile.write(bytes(msg,"utf-8"))

	def do_GET(self):
		try:
			
			url=urlparse(self.path)
			# if url.path!='/status':print(self.path)
			# loc=self.loc
			if url.path=='/start':
				if 'videocapture' in loc: stopRecording()
				query = url.query
				args = dict(qc.split("=") for qc in query.split("&"))
				path=args.get('path','test')
				startRecording(path)
				self.reply(f"<a href='/status'>/status</a> to end click on <a href='/stop'>/stop</a> ")
			elif url.path=='/status':
				if 'videocapture' not in loc: 
					self.reply('not started')
					return
				import json
				self.reply(json.dumps(loc['videocapture'].info),'application/json')
			elif url.path=='/image':
				import base64
				cam=RealSense("usb",debug=1,infrared=0,depth=0)
				cam.start()
				frames=cam.waitForFrame(colorize=True)
				cam.stop()
				resp=''
				for s in cam.selected_profiles:
					_,img = cv2.imencode('.jpeg', frames[s])
					bimg=base64.b64encode(img.tobytes()).decode("ascii")
					resp+=f'<div>{s}<br/><img src="data:image/jpeg;base64,{bimg}"/></div>'
				self.reply(resp)
			elif url.path=='/stop':
				if 'videocapture' not in loc: 
					self.reply('not started')
					return
				stopRecording()
				siz=get_folder_size(loc['save_path'])
				self.reply(f'size={convert_bytes(siz)}')
				
			elif url.path=='/ping':
				self.reply(f'ok')
			elif url.path=='/update':
				import os
				import sys
				output = os.popen('git pull').read()
				print(output)
				self.reply(output)
				self.wfile.flush()
				httpd.server_close()
				os.execl(sys.executable, os.path.abspath(__file__),*sys.argv)
				import time
				time.sleep(1)
				kill()
			else:
				self.reply("""
					<a href="/start?path=test">/start?path=test</a> <br/>
					<a href="/status">/status</a><br/>
					<a href="/stop">/stop</a><br/>
					<a href="/stop">/update</a><br/>
					<a href="/image">/image</a><br/>
				""")
				
		except Exception as e:
				import traceback
				self.reply(f"""<pre>
error: {e!r}
{traceback.format_exc()}
</pre>""")
		self.wfile.flush()

def get_folder_size(start_path):
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(start_path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            # skip if it is symbolic link
            if not os.path.islink(fp):
                total_size += os.path.getsize(fp)

    return total_size
def convert_bytes(num):
	"""
	this function will convert bytes to MB.... GB... etc
	"""
	for x in ['bytes', 'KB', 'MB', 'GB', 'TB']:
		if num < 1024.0:
			return "%3.1f %s" % (num, x)
		num /= 1024.0

def kill():
	if 'videocapture' in loc:
		loc['videocapture'].kill()
	psutil.Process().kill()
if __name__ == "__main__":
	psutil.Process().cpu_affinity([0,1])
	
	print('a')
	httpd = HTTPServer( ("0.0.0.0", 8080), Handler)
	print('b')
	try:
		httpd.serve_forever()
		print('c')
	except KeyboardInterrupt as e2:
		print(e2)
		# psutil.Process().kill()
		kill()
		# stopRecording()

		
	except Exception as e:
		print(e)
	print('d')
	httpd.server_close()


