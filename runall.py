

cams={
'cam1':'10.12.20.211',
'cam2':'127.0.0.1',
 'cam3':'10.12.20.76',
 'cam4':'10.12.20.102',
}


import sys
if len(sys.argv)==1:
	print(f'usage: \n{sys.argv[0]} start user act prefix_path\n{sys.argv[0]} stop')
	sys.exit(1)

#     print(p)




from datetime import datetime
dt_string = datetime.now().strftime("%d-%m-%Y-%H-%M-%S")




def record_remote_start(cam):
	import requests

	try:
		path=f'{prefix_path}/{user}/{act}/{dt_string}/{cam}'
		r = requests.get(url = f"http://{cams[cam]}:8080/start?path={path}")
		print(f'{cam}-{r.content}')
		# return f'{cam}-{r}'
	except Exception as e:
		print(f'{cam}-{e}')
		

def record_remote_stop(cam):
	import requests
	try:
		r = requests.get(url = f"http://{cams[cam]}:8080/stop")
		print(f'{cam}-{r.content}')
	except Exception as e:
		print(f'{cam}-{e}')

	# return f'{cam}-{r}'

def record_remote_test(cam):

		import requests
		try:
			r = requests.get(url = f"http://{cams[cam]}:8080/")
			print(f'{cam}-{r.content}')
		except Exception as e:
			print(f'{cam}-{e}')

import multiprocessing
def parallelRunner(parallel, runner, items):
    if parallel:
        from multiprocessing.pool import ThreadPool

        pool = ThreadPool(min(8,len(items)))
        result = pool.imap(runner, items)
        try:
            for _ in items:
                res = result.next()
                yield res
        except KeyboardInterrupt:
            pool.terminate()
            pool.join()
            pool.close()
            raise
    else:
        for item in items:
            res = runner(item)
            yield res


from multiprocessing import Process, freeze_support
freeze_support()
if sys.argv[1]=="start":
	user=sys.argv[2]
	act=sys.argv[3]
	prefix_path=sys.argv[4]
	for p in parallelRunner(1,record_remote_start,cams.keys()):
		print(f'ok {p}')

if sys.argv[1]=="stop":
	for p in parallelRunner(1,record_remote_stop,cams.keys()):
		print(f'ok {p}')


if sys.argv[1]=="test":
	for p in parallelRunner(1,record_remote_test,cams.keys()):
		print(f'ok {p}')
