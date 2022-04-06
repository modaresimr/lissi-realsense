

from http.server import BaseHTTPRequestHandler, HTTPServer
import time, threading
from multiprocessing import Process, JoinableQueue
import os
from urllib.parse import urlparse
print('starting...')
from realsensewrapper import RealSense
loc = {}



def video_recorder(name,q,save_path,profile):
	import cv2
	codec = cv2.VideoWriter.fourcc(*'h264')
	vw=cv2.VideoWriter(f'{save_path}/{name}.mp4',codec, profile['fps'], (profile['width'], profile['height']),profile['is_color'])
	i=0
	while True:
		n,img = q.get()
		
		if n==-1:
			q.task_done()
			break
		i+=1
		if name=='Depth':
			img = cv2.applyColorMap(cv2.convertScaleAbs(img, alpha=0.03), cv2.COLORMAP_JET)
		vw.write(img)
		q.task_done()
		if i%1000==0:
			print(f'{name} frame loss={max(0,(n-i))*100/n:.0f}')
	vw.release()


def worker():
	streams=loc['camdev'].selected_profiles

	qs={s:JoinableQueue(1000) for s in streams}
	prcs={s: Process(target=video_recorder, args=(s,qs[s],loc['save_path'],streams[s])) for s in streams}
	for p in prcs:
		prcs[p].daemon=True
		prcs[p].start()

	while loc['working']:
		frames = loc['camdev'].waitForFrame(colorize=False)
		
		for s in streams:
			qs[s].put((frames['frame'],frames[s]))	
	
	for s in streams:qs[s].put((-1,'eof')) 
	for s in streams: qs[s].join()
	for s in streams:prcs[s].join()



def stopRecording():
	loc['working']=0
	if 'camdev' in loc:
		loc['camdev'].stop()
		#for closing old file
		try:
			loc['camdev'].debug=0
			loc['camdev'].connect(save_path='nul')
			loc['camdev'].stop();
		except:pass

	if 'thread' in loc:
		loc['thread'].join()
		del loc['thread']


def startRecording(path):
	import  shutil
	if os.path.exists(path):
		shutil.rmtree(path)
	os.makedirs(path,exist_ok=True)	
	loc['working']=1
	loc['camdev']=RealSense("usb",debug=1)
	loc['save_path']=f'{path}'
	loc['camdev'].connect()#save_path=f'{path}/full.bag')
	
	# Turn-on the worker thread.\
	loc['working']=1
	loc['thread']=threading.Thread(target=worker, daemon=True)
	loc['thread'].start()

class Handler(BaseHTTPRequestHandler):
	
	def do_GET(self):
		try:
			print("do")
			print(self.path)
			url=urlparse(self.path)
			# loc=self.loc
			if url.path=='/start':
				if 'thread' in loc: stopRecording()
				query = url.query
				args = dict(qc.split("=") for qc in query.split("&"))
				path=args.get('path','test')
				
				startRecording(path)
				self.send_response(200)
				self.send_header("Content-type", "text/html")
				self.end_headers()
				msg=f"to end click on <a href='/stop'>/stop</a> <pre>{loc['camdev'].selected_profiles}</pre>"
				self.loc=loc
				self.wfile.write(bytes(msg,"utf-8"))
			elif url.path=='/stop':
				stopRecording()
				siz=get_folder_size(loc['save_path'])
				self.send_response(200)
				self.end_headers()
				msg=f'size={convert_bytes(siz)}'
				self.wfile.write(bytes(msg,"utf-8"))
			elif url.path=='/ping':
				self.send_response(200)
				self.send_header("Content-type", "text/html")
				self.end_headers()
				msg=f'ok'
				self.wfile.write(bytes(msg,"utf-8"))
			else:
				self.send_response(200)
				self.end_headers()
				msg="""
					<a href="/start?path=test">/start?path=test</a> 
					<br/>
					<a href="/stop">/stop</a>
				"""
				self.wfile.write(bytes(msg,"utf-8"))
		except Exception as e:
				import traceback
				self.send_response(500)
				self.end_headers()
				msg=f"""
<pre>
error: {e!r}
{traceback.format_exc()}
</pre>
				"""
				self.wfile.write(bytes(msg,"utf-8"))


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

if __name__ == "__main__":
	httpd = HTTPServer( ("0.0.0.0", 8080), Handler)
	try:
		httpd.serve_forever()
	except KeyboardInterrupt:
		exit()
		# stopRecording()
		
	httpd.server_close()


