import socket

import json
import _thread as thread
import time
from Util import ifNeedToCreateFolder
from database import LoadAllUsers, LoadEventFile
from GraphAnalyzer import GraphAnalyzer
import argparse
from WebApp import MDash
from selenium import webdriver

# settings
bufferSize = 4194304
python_cmd = 'python'
end_signal = '[]'
exit_cmd = 'exit()'
address = ('127.0.0.1', 7777)  

end_signal_len = len(end_signal.encode('utf-8'))

# ########### Small test1##########
# maxLevel = 2
# maxUser = 5

# path = 'C:/Users/z5308/Desktop/VRTestingProject/data/small/'

# df = LoadAllUsers(maxUser, path)


# ########## Small test2 ##########
# maxLevel = 1
# maxUser = 5

# path = 'C:/Users/z5308/Desktop/VRTestingProject/data/small2/'

# df = LoadAllUsers(maxUser, path)


###########normal###########
maxLevel = 16
maxUser = 2
df = LoadAllUsers(maxUser, None)
###############################

url = "http://127.0.0.3:8060/"
driver = webdriver.Chrome()

app = MDash(maxUser, maxLevel)
analyzer =  GraphAnalyzer(df, maxLevel)


##########Argument parser registration ###############
parser = argparse.ArgumentParser()
parser.add_argument('-g', action='store_true',  help="run discrete graph")
parser.add_argument('-ContinuousGraph', action='store_true',  help="run cluster graph")
parser.add_argument('-ClusterGraph', action= 'store_true')
parser.add_argument('-EventGraph', action= 'store_true')
###################################3


def command(cmd, conn, addr):
	
	args_list = cmd.split()
	
	args = parser.parse_args(args_list)

	if(not app.isRun):
		app.StartApp()
	
	print(f"args {args} ")
	graphSetting = None
	if(args.g): #discreteGraph
		#open json
	
		with open("./graphSetting/SimpleGraph.json") as json_file:
			graphSetting = json.load(json_file)
			#graphSetting = data
		
		fig, graphType, callbackArr  = analyzer.DiscreteGraph(graphSetting)
		app.LoadDiscreteFig(fig, conn,graphType, callbackArr )
		
		
	elif(args.ContinuousGraph):
		
		
		with open("./graphSetting/ContinuousGraph.json") as json_file:
			graphSetting = json.load(json_file)
		if(graphSetting == None):
			print("Unable to open json file")
		
		fig, levelCallback, graphUpdateCallback = analyzer.ContinuousGraph(graphSetting, df)
		
		app.LoadContinFig(fig, conn, levelCallback, graphUpdateCallback )
	
	
	elif(args.ClusterGraph):
		
		with open("./graphSetting/ClusterGraph.json") as json_file:
			graphSetting = json.load(json_file)
		fig = analyzer.RunCluster(graphSetting, df)
		app.LoadClusterFig(fig, conn)
	elif(args.EventGraph):
		with open("./graphSetting/EventGraph.json") as json_file:
			graphSetting = json.load(json_file)
		edf = LoadEventFile()
		fig = analyzer.RunEventGraph(graphSetting,edf)
		#app.EventGraph(fig, conn)
	driver.get(url)
	driver.refresh()

# socket
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind(address) 

print(s)


print("Custom Server Started!")
s.listen(10)

# thread
def client_accept():
    while True:
        print("Listening...")
        try:
            conn, addr = s.accept()
            print('[+] Connected with', addr)
            thread.start_new_thread(client_handle, (conn, addr))
        except:
            break

def recvall(conn):
    # Helper function to recv n bytes or return None if EOF is hit
    data = bytearray()
    try:
        while len(data) < bufferSize:
            packet = conn.recv(bufferSize)
            if not packet:
                break
            if len(packet) == 0:
                break
            if len(packet) == end_signal_len:
                if packet.decode('utf-8') == end_signal: # end signal
                    # print(end_signal)
                    break
            print('Packet size: ' + str(len(packet)))
            data.extend(packet)
            print('Received:    ' + str(len(data)))
    except:
       print("[Error]")
    return data


def result_error(conn, addr):
    try:
        print("Result: [Error]")
        send = "[Error]".encode('utf-8')
        print("Send size: "+str(len(send)))
        conn.sendall(send)
    except:
        print(addr, "Disconnected.")

def client_handle(conn, addr):
	while True:
		try:
			# decode the network content
			data = recvall(conn).decode('utf-8')
		except:
			# result_error(conn, addr)
			break

		if not data:
			continue

		print('data: '+data)
		print("data size: "+str(len(data)))

		# exit cmd
		if(data == exit_cmd):
			print(data)
			break
		
		# run command
		print('command: ' + data)

		command(data, conn, addr)

		time.sleep(0.05) # setting: reduce the traffic load

	conn.close()
	print('[-] Disconnected with', addr)
	print()



thread.start_new_thread(client_accept, ())

while True:
	cmd = input()
	if(cmd == exit_cmd):
		break

s.close()
driver.quit()
print("Server Stopped!")



