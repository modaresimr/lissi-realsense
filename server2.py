
from werkzeug.local import Local

from socketserver import ThreadingMixIn
from http.server import HTTPServer, BaseHTTPRequestHandler
import time, threading
import os
from urllib.parse import urlparse
print('starting...')
from realsensewrapper import RealSense

class ThreadingServer(ThreadingMixIn, HTTPServer):
    pass
class Handler(BaseHTTPRequestHandler):
	loc = Local()
	def do_GET(self):
		print("do")
		print(self.path)
		url=urlparse(self.path)
		loc=self.loc
		if url.path=='/start':
			query = url.query
			args = dict(qc.split("=") for qc in query.split("&"))
			path=args.get('path','test')
			os.makedirs(path,exist_ok=True)


			
			loc.camdev=RealSense("usb",debug=1)
			loc.save_path=f'{path}/full.bag'
			loc.camdev.connect(save_path=loc.save_path)

			self.send_response(200)
			self.end_headers()
			msg=f'to end click on <a href="/stop">/stop</a> <pre>{loc.camdev.selected_profiles}</pre>'
			self.loc=loc
			self.wfile.write(bytes(msg,"utf-8"))
		elif url.path=='/stop':
			loc.camdev.stop()
			siz=os.path.getsize(loc.save_path)
			self.send_response(200)
			self.end_headers()
			msg=f'size={self.convert_bytes(siz)}'
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

	def convert_bytes(self,num):
		"""
		this function will convert bytes to MB.... GB... etc
		"""
		for x in ['bytes', 'KB', 'MB', 'GB', 'TB']:
			if num < 1024.0:
				return "%3.1f %s" % (num, x)
			num /= 1024.0

if __name__ == "__main__":
    httpd = HTTPServer( ("0.0.0.0", 8080), Handler)
    httpd.serve_forever()

