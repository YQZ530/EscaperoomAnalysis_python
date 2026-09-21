import socket
import json
import _thread as thread
import time
from Util import ifNeedToCreateFolder

from escaperoom_database import  LoadEyeGazeForUsers2,LoadEventForUsers
from reflex_database import LoadFileForUsers, LoadEyeGazeForUsers,LoadSimpleFile,LoadChunkFileForUsers
import argparse
# from clustermain import Cluster
import threading
# from EyegazeCluster import EyeGazeClusters
from EyegazeCluster_ER import EREyeGazeClusters_ER
# settings
bufferSize = 4194304
python_cmd = 'python'
end_signal = '[]'
exit_cmd = 'exit()'
address = ('127.0.0.1', 7777)  

end_signal_len = len(end_signal.encode('utf-8'))




###########normal###########
maxUser = 27
# path = 'C:/Users/z5308/Desktop/VRTestingProject/data/Reflex_data/simple_3joints/'
# player_database = LoadFileForUsers(path)
#
# path = 'C:/Users/z5308/Desktop/VRTestingProject/data/Reflex_data/simple_3joints/otherInfo'
# chunk_database = LoadChunkFileForUsers(path)
#
# eyegaze_path = "../data/Reflex_data/simple_3joints/otherInfo/"
# eyegaze_df = LoadEyeGazeForUsers(eyegaze_path)
player_database = None
chunk_database = None
eyegaze_df = None
###############################

url = "http://127.0.0.3:8060/"
# mcluster = Cluster(player_database, chunk_database, maxUser)
# eyegaze_cluster = EyeGazeClusters(eyegaze_df, maxUser)

path = 'C:/Users/Administrator/Desktop/VREscapeRoom/EscapeRoomData'
eyegaze_df_ER = LoadEyeGazeForUsers2(path)
event_df_ER = LoadEventForUsers(path)
eyegaze_cluster_ER =  EREyeGazeClusters_ER(eyegaze_df_ER, event_df_ER)
##########Argument parser registration ###############
parser = argparse.ArgumentParser()
parser.add_argument('-c', action='store_true',  help="run clustering")
parser.add_argument('-eyec', action='store_true',  help="run eye gaze clustering")
parser.add_argument('-er_eyec', action='store_true',  help="run eye gaze clustering")
###################################3

def RunClusterInThread(conn, clusterSetting):
	# result = mcluster.RunClusterMain(clusterSetting)
	# print("[Done] send back cluster result")
	# conn.sendall(result.encode('utf-8'))
	print("TODO")

def RunEyeGazeClusterInThread(conn, clusterSetting):
	# result = eyegaze_cluster.RunClusterMain(clusterSetting)
	# print("[Done] send back cluster result")
	# conn.sendall(result.encode('utf-8'))
	print("TODO")
def RunEyeGazeClusterInThread_ER(conn, clusterSetting):
	result = eyegaze_cluster_ER.RunClusterMain(clusterSetting)
	print("[Done] send back escape cluster result")
	conn.sendall(result.encode('utf-8'))

def command(cmd, conn, addr):
	
	args_list = cmd.split()
	args = parser.parse_args(args_list)

	print(f"args {args} ")
	clusterSetting = None
	if(args.c): #cluster
		#open json
		print("clustering")
		with open("./Setting/ClusterSetting.json") as json_file:
			clusterSetting = json.load(json_file)
			#print(clusterSetting['EyeGaze_Metric'])
		
		mthread = threading.Thread(target=RunClusterInThread,args=(conn, clusterSetting))
		mthread.start()
		
	elif(args.eyec):#eye gaze clustering
		print("eye clustering")
		with open("./Setting/ClusterSetting.json") as json_file:
			clusterSetting = json.load(json_file)
		
		mthread = threading.Thread(target=RunEyeGazeClusterInThread,args=(conn, clusterSetting))
		mthread.start()

	elif (args.er_eyec):  # eye gaze clustering
		print("ER Game eye clustering")
		with open("./Setting/ClusterSetting.json") as json_file:
			clusterSetting = json.load(json_file)

		mthread = threading.Thread(target=RunEyeGazeClusterInThread_ER, args=(conn, clusterSetting))
		mthread.start()
		
		

# socket
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind(address) 

print(s)


print("Custom Server Started!")
s.listen(10)

# thread2
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

print("Server Stopped!")



