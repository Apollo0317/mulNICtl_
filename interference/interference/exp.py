import os
import json
import time
import util.ctl as ctl
import util.qos as qos
import util.constHead as constHead
import traceback

from tap import Connector
from util import stream
from util.solver import globalSolver, balanceSolver
from util.logger import QosLogger

from util.trans_graph import LINK_NAME_TO_TX_NAME
from tools.read_graph import construct_graph

from typing import List

parseSingleIpDevice = lambda x: [x, x]

# def create_transmission(trans_manifests, topo, arrivalGap = 16):
def create_transmission(trans_manifests, topo):
    [ constHead.traffic_config_schema.validate(manifest) for _, manifest in trans_manifests.items() ]
    streams = []
    for name in trans_manifests:
        trans_manifest = trans_manifests[name]
        if trans_manifest is None:
            continue
        conn            = Connector()
        sender          = LINK_NAME_TO_TX_NAME(trans_manifest['link'])
        file_name       = f'{name}.npy'
        print(f"Creating transmission file {file_name} with {trans_manifest['thru']} at {sender}")
        assert trans_manifest['thru'] > 0
        arrivalGap = trans_manifest['arrivalGap']###########################################
        conn.batch(sender, "create_file", {"thru": trans_manifest['thru'], "arrivalGap": arrivalGap, "name": f'{name}.npy', "num": 20000}).wait(0.5).apply()     
        temp        = stream.stream()
        print(temp.calc_rtt)
        temp.npy_file   = file_name
        temp.links      = trans_manifest['links']
        print(temp.links)
        temp.name       = '{}@{}'.format(trans_manifest['port'], trans_manifest['tos'])
        temp.tx_parts   = trans_manifest['tx_parts']
        temp.port       = trans_manifest['port']
        temp.tos        = trans_manifest['tos']
        temp.throttle   = int(trans_manifest['thru']) + 10
        temp.sampleRate = trans_manifest['sampleRate']
        temp.target_rtt = 0.022
        ## Local test
        temp.channels = trans_manifest['channels']
        topo.ADD_STREAM(trans_manifest['link'], temp, validate = False)
        streams.append(temp)
    return streams

def get_stream_by_name(streams, name):
    for estream in streams:
        if estream.name == name:
            assert isinstance(estream, stream.stream)
            return estream
    raise ValueError(f"Stream {name} not found")

def get_qos_by_name(qoses, name):
    for qos in qoses:
        if qos['name'] == name:
            return qos
    raise ValueError(f"Qos {name} not found")

def apply_control_to_stream_by_name(streams, controls):
    for control in controls:
        estream = get_stream_by_name(streams, control['name'])
        if constHead.TX_PARTS in control:
            estream.tx_parts = control[constHead.TX_PARTS]
        if constHead.THRU_CONTROL in control:
            estream.throttle = control[constHead.THRU_CONTROL]

def print_rtt(qoses, key = constHead.RTT):
    rtts = []
    for qosVal in qoses:
        try:
            constHead.PROJ_QOS_SCHEMA.validate(qosVal)
            rtts.append({qosVal['name'] : qosVal[key]})
        except Exception as e:
            continue
    print(rtts)

def create_int_trans_manifest(name,ac1_thru, ac2_thru, ac1_num, ac2_num, ac1_link,ac2_link, topo, start_port = 6520,start = 0.0 ,end = 100000.0):
    template = {
        'thru'      : 10,
        'arrivalGap': 16,
        'file_type' : 'file',
        'link'      : ac1_link,
        'port'      : start_port,
        'links'     : [topo.get_link_ips(ac1_link)],
        'tx_parts'  : [1],
        'tos'       : 128,
        'channels'  : [constHead.CHANNEL0,constHead.CHANNEL1],
        'sampleRate': 1,
        'duration'  : [0.0,100000.0]
    }


    trans_manifest = {}
    inter_port_list = []
    ac1_port = start_port
    ac2_port = start_port + 10
    ## Create ac1
    # ac1_thru_pport = ac1_thru / ac1_num; ac2_thru_pport = ac2_thru / ac2_num
    for i in range(ac1_num):
        template['thru'] = ac1_thru
        template['link'] = ac1_link
        template['port'] = ac1_port
        template['links'] = [topo.get_link_ips(ac1_link)]
        template['tos']  = 128
        template['duration']  = [start,end]
        
        trans_manifest.update({f'temp_ac1_{name}_{i}' : template.copy()})
        inter_port_list.append(str(template['port']) +'@'+str(template['tos']))
        ac1_port += 1

    for i in range(ac2_num):
        template['thru'] = ac2_thru
        template['link'] = ac2_link
        template['port'] = ac2_port
        template['links'] = [topo.get_link_ips(ac2_link)]
        template['tos']  = 96
        template['duration']  = [start,end]

        
        trans_manifest.update({f'temp_ac2_{name}_{i}' : template.copy()})
        inter_port_list.append(str(template['port']) +'@'+str(template['tos']))
        ac2_port += 1
    print(inter_port_list)    
    return trans_manifest

def colors_cal(tempcolors):
    colorlist = []
    for _,vallist in tempcolors.items():
        temp = []
        for colorval in vallist:
            match colorval:
                case "Red": temp.append(1)
                case "Yellow": temp.append(0.5)
                case "Green": temp.append(0)
        # print(max(temp))
        colorlist.append(max(temp))
    return colorlist
def datatransfer():
    print("data transfer")
    import socket
    import scale
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.bind(("192.168.3.72",6305)) 
    import matplotlib.pyplot as plt
    from matplotlib import rcParams
    import numpy as np
    rcParams['font.family'] ='sans-serif'
    rcParams['font.size'] = 16
    task_list = []
    channel_colors = {"2.4G":[0],"5G":[0],"Index":[0]}
    channel_rtts = {}
    rtts = {}
    tx_parts = {}
    TimeIndexlist= {}
    TimeIndex = 0
    fig, axs = plt.subplots(4, 1, figsize=(15, 15))
    plt.ion()
    index = 0
    zeroIndex = 0
    data_idx = 0
    ## 删除文件流信息
    portlist = ["6212@96","6213@96","6214@96","6215@96","6216@96","6217@96","6218@96","6219@96","6220@96","6221@96","6222@96","6223@96","6224@96","6225@96","6226@96","6227@96","6228@96","6229@96","6230@96","6231@96","6501@128","6502@128","6503@128","6504@128","6505@128","6506@128","6511@96","6512@96","6513@96","6514@96","6515@96","6516@96","6521@128","6522@128","6523@128","6524@128","6525@128","6526@128","6527@128","6528@128","6531@96","6532@96","6533@96","6534@96"]###############################################
    while zeroIndex < 10:
        print('ZEROiNDEX:',zeroIndex)
        data  = s.recvfrom(10240)
        data_idx += 1
        tempcolors = {"2.4G":[],"5G":[]}
        if type(data) == bytes:
            zeroIndex += 1  #控制未开始
        elif type(data) == tuple:
            # print("tuple:", data[0],'\n')
            datas = json.loads(data[0].decode("utf-8"))
            logger1.write(json.dumps(datas) + '\n') #记录Qos数据
            # print("datas",datas)
            if len(datas) == 0:
                zeroIndex += 1
            else:
                for port in portlist:
                    datas.pop(port, None) #删除无效端口数据
                #sort task_name
                sorted(datas)
                #################
                logger2.write(json.dumps(datas) + '\n')
                datasindex = 0
                for task, vals in datas.items():
                    if task not in task_list:
                        task_list.append(task)
                    # print("task",task,vals)
                    if "channel_rtts" not in vals:
                        try:
                            tempcolors["2.4G"].append(vals['channel_colors'][1])
                            tempcolors["5G"].append(vals['channel_colors'][0])
                        except:
                            continue
                    elif "channel_rtts" in vals:
                        if datasindex == 0:
                            TimeIndex += 1
                        if task not in channel_rtts:
                            channel_rtts[task] = []
                        channel_rtts[task].append(np.array(vals['channel_rtts']) * 1000)
                        if task not in rtts:
                            rtts[task] = []
                        rtts[task].append(np.array(vals['rtt']) * 1000)

                        if task not in tx_parts:
                            tx_parts[task] = []
                        tx_parts[task].append(np.array(vals['tx_parts']))

                        if task not in TimeIndexlist:
                            TimeIndexlist[task] = []
                        TimeIndexlist[task].append(TimeIndex)
                        datasindex += 1
        if tempcolors["2.4G"]:
            color = colors_cal(tempcolors)
            channel_colors["2.4G"].append(color[1])
            channel_colors["5G"].append(color[0])
            channel_colors["Index"].append(TimeIndex)
        channel_idx = ['5GHz', '2.4GHz']
        color_list = ['#000000','#FF0000','#00FF00','#0000FF','#FFFF00','#800080','#A52A2A','#FFA500','#ADD8E6','#C0C0C0']

        axs[0].cla()
        axs[1].cla()
        axs[2].cla()
        axs[3].cla()
        # Plot channel RTTs
        targetRtt = 22
        for _, (task, c_rtts) in enumerate(channel_rtts.items()):
            task_idx = task_list.index(task)
            c_rtts = np.array(c_rtts).T
            for idx, rtt in enumerate(c_rtts):
                # IdxTimertt1 = range(0,len(rtt),1)
                IdxTimertt1 = TimeIndexlist[task]
                if idx == 0:
                    axs[0].plot(IdxTimertt1,rtt, '-+',color = color_list[task_idx],  label=task + ' channel ' + channel_idx[idx])
                else:
                    axs[0].plot(IdxTimertt1,rtt, ':o',color = color_list[task_idx],  label=task + ' channel ' + channel_idx[idx])
            # if index == 0:
        axs[0].axhline(y=targetRtt, color = 'r',linestyle = '--', label='Target RTT (22ms)')
        axs[0].set_yscale('custom', threshold=60) #压缩y轴刻度，超过阈值部分取log
        axs[0].grid(linestyle='--')
        axs[0].set_ylabel('Channel RTT (ms)')
        axs[0].set_xlabel('Time (s)')
        axs[0].set_xlim(0, ctrller.duration)
        axs[0].set_ylim(0, 300)

        
        # # Plot RTTs
        for _idx, (task, rtt) in enumerate(rtts.items()):
            task_idx = task_list.index(task)
            # Idxrtt = range(0,len(rtt),1)
            Idxrtt = TimeIndexlist[task]
            rtt = np.array(rtt)
            axs[1].plot(Idxrtt,rtt, '-+',color=color_list[task_idx], label=task_list[task_idx])
        axs[1].axhline(y=targetRtt, color = 'r',linestyle = '--', label='Target RTT (22ms)')
        axs[1].set_yscale('custom', threshold=60)
        axs[1].grid(linestyle='--')
        axs[1].set_xlim(0, ctrller.duration)
        # axs[1].set_ylim(0, 100)
        axs[1].set_ylim(0, 300)
        axs[1].set_ylabel('RTT (ms)')
        axs[1].set_xlabel('Time (s)')
        # axs[1].legend(loc = "upper center",bbox_to_anchor=(0.5, 1.1),
        #     ncol=4, fancybox=True, shadow=True)
        
        # # Plot TX Parts
        for idx, (task, tx_part) in enumerate(tx_parts.items()):
            task_idx = task_list.index(task)
            IdxTxPart = TimeIndexlist[task]
            tx_part = np.array(tx_part) * 100
            tx_part = tx_part.T
            axs[2].plot(IdxTxPart,tx_part[1,:], '-+',color=color_list[task_idx], label=task_list[task_idx])
            

        axs[2].grid(linestyle='--')
        axs[2].set_ylabel('TX Parts')
        axs[2].set(ylim=(0,100))
        axs[2].set_xlim(0, ctrller.duration)
        axs[2].set_xlabel('Time (s)')
        # if index == 0:
        axs[2].legend()

        axs[3].plot(channel_colors["Index"],channel_colors["2.4G"],'--', marker = 'v', color='r', linewidth = 1, label="2.4G")
        axs[3].plot(channel_colors["Index"],channel_colors["5G"],'-',marker = "o", color='g',linewidth = 1, label="5G")
        axs[3].grid(linestyle='--')
        axs[3].set_ylabel('Channel color')
        axs[3].set_yticks([0,0.5,1])
        axs[3].set(ylim=(-0.1,1.1))
        axs[3].set_xlabel('Time (s)')
        axs[3].set_xlim(0, ctrller.duration)
        axs[3].legend()
        # plt.tight_layout()
        plt.pause(0.01)
        index += 1
        plt.savefig(f"dpScript/{date}/rtt_{txtIndex}.png")  
    plt.ioff()
    # plt.close()
    


import multiprocessing
def start_comm_process():
    result_queue = multiprocessing.Queue()
    comm_process = multiprocessing.Process(target=ctrller._communication_thread, args=(topo,result_queue,))
    datatransfer_process = multiprocessing.Process(target=datatransfer)
    comm_process.start()
    datatransfer_process.start()
    return result_queue.get()
def fileTransfer(targetIP,filepath):
    portlist = [x for x in range(6205,6205+taskNum)]  #需要回收rtt和shutter的项目端口
    linkList = [links[0],links[2],links[4],links[6]] #其对应的'link'地址
    for linkidx,port in enumerate(portlist):
        print("port: ", port)
        ctl.RxfileTransfer(topo, targetIP,  filepath+"stuttering/", f"../stream-replay/logs/stuttering-{port}.txt" , linkList[linkidx])
        time.sleep(5)
        ctl.fileTransfer(topo, targetIP,  filepath+"rtt/", f"../stream-replay/logs/rtt-{port}*128.txt" , linkList[linkidx])
        time.sleep(5)
    print("file transfer done")
def start_control(command):
    import os
    os.system(f"gnome-terminal -e 'bash -c \"cd ./solver;{command}; exec bash\"'")
    
################################################# Main Function ##############################################################################################################3
date = "inter"
filepath = "./dpScript/inter/"      #存储文件路径 #############################################
fileList = os.listdir(f'{filepath}rtt/') 
txtIndex = 0   ####################################################
tempTxtName = f'output{txtIndex}.txt'  ###存储文件名，rtt和shutter名一致，文件夹不同


############### Transmit Parmeters #####       
taskNum = 1 #任务数量
run_time = 30 #运行时间
thru = 24  #流量
monitor_ip = "192.168.3.72:6305" #监控IP

while tempTxtName in fileList:
    txtIndex += 1
    tempTxtName = f'output{txtIndex}.txt' ###存储文件名，rtt和shutter名一致，文件夹不同,自动更新文件名

topo,links = construct_graph(f"./config/topo/{date}.txt") ####拓扑结构文件名
ip_table    = ctl._ip_extract_all(topo)
ctl._ip_associate(topo, ip_table)

trans_manifests = {  #传输参数
    'proj1': {  #传输项目名（会生成同名传输文件，需要唯一）
        'thru'      : thru,  # #吞吐量
        'arrivalGap': 16, #发包间隔
        'file_type' : 'proj', #传输类型，file表示文件，proj表示投屏流
        'link'      : links[0], #links[0]对应第1个topo结构，默认2.4G，指令传输信道
        'port'      : 6205, #传输端口
        'links'     : [topo.get_link_ips(links[1]), topo.get_link_ips(links[0])], #links[1]对应第2个topo结构，默认5G， 目标传输信道
        'tx_parts'  : [1, 1], #传输初始分配比例，1表示全部在'links'所对应的第一项
        'tos'       : 128, #128代表AC1，96代表AC2
        'channels'  : [constHead.CHANNEL0, constHead.CHANNEL1],
        'sampleRate': 1,
        'duration'  : [0.0,10000.0]
    },
}
##########################Interference 1 干扰流定义 ################
inter_proj_thru_5g = 32 #5G 投屏流吞吐量
inter_file_thru_5g = 32 #5G 文件流吞吐量
inter_proj_num_5g  = 6 #5G 投屏流数量
inter_file_num_5g  = 6 #5G 文件流数量

inter_proj_thru_24g = 8 #2.4G 
inter_file_thru_24g = 8
inter_proj_num_24g  = 4
inter_file_num_24g  = 4

# ## 干扰流生成
# inter_2_4g_manifests = create_int_trans_manifest(24,inter_proj_thru_24g, inter_file_thru_24g, inter_proj_num_24g, inter_file_num_24g, links[2],links[3],topo, 6521)
# trans_manifests.update(inter_2_4g_manifests)

inter_5g_manifests = create_int_trans_manifest(5,inter_proj_thru_5g, inter_file_thru_5g, inter_proj_num_5g, inter_file_num_5g, links[2],links[3],topo, 6501)
trans_manifests.update(inter_5g_manifests)


#######

print(trans_manifests)
logger1 = open(f'dpScript/{date}/TaskAll_{txtIndex}.jsonl', 'w')  #日志文件
logger2 = open(f'dpScript/{date}/Qos_{txtIndex}.jsonl', 'w')  #QoS文件
logger1.write("trans_manifests: "+str(trans_manifests)+'\n') 

# ================
streams = create_transmission(trans_manifests, topo)  #创建传输流
topo.show()
print("trans_manifests: ",trans_manifests)
# exit()
ctrller = ctl.CtlManager()
ctrller.duration = run_time
target_ips, name2ipc = ctl.ipcManager.prepare_ipc(topo)
base_info = ctl.graph_qos_collections(topo)

conn = Connector()
monitor_ip = "192.168.3.72:6305"
import base64
ips = base64.b64encode( json.dumps(target_ips).encode() ).decode()
command = f"cargo run -- --target-ips={ips} --name2ipc={base64.b64encode( json.dumps(name2ipc).encode() ).decode()} --base-info={base64.b64encode( json.dumps(base_info).encode() ).decode()} --monitor-ip {monitor_ip}"
print(f"cargo run -- --target-ips={ips} --name2ipc={base64.b64encode( json.dumps(name2ipc).encode() ).decode()} --base-info={base64.b64encode( json.dumps(base_info).encode() ).decode()} --monitor-ip {monitor_ip}")
#复制命令到新的terminal 启动控制器
start_control(command) 

queueResult = start_comm_process()  #返回传输结果 
print("queueResult",queueResult)

sumval = 0
for val in queueResult:
    if 'throughput' in val: 
        sumval += eval(val['throughput'])

print("summation value", sumval)  #总吞吐量

# exit()

logger1.write("queueResult: "+str(queueResult)+'\n')
logger1.write("summation value: "+str(sumval)+'\n')
time.sleep(5)
targetIP = monitor_ip.split(":")[0]

fileTransfer(targetIP,filepath) 

### 根据回传结果 绘图并保存
import read_txt as rt
taskList = []
taskRttlist = {}
Stutteringlist = {}
for idxstream in range(txtIndex,txtIndex+taskNum):
    taskList.append(f"output{idxstream}.txt")
for txtName in taskList:
    temptxtName = filepath+ 'rtt/' + txtName
    tempstutteringfileName = filepath + "stuttering/" + txtName
    if os.path.exists(temptxtName):
        rt.delLastLine(temptxtName)
        port,temprttArray = rt.txtRead_multiChannel_port(temptxtName)
        taskRttlist[port] = temprttArray
    if os.path.exists(tempstutteringfileName):
        port,NA_stuttering,Ada_stuttering,stuttering_gain = rt.Stuttering_cal(filename=tempstutteringfileName,part= 1)
        Stutteringlist[port] = [NA_stuttering,Ada_stuttering,stuttering_gain]
rt.rttSinglePlot_time(temptxtName)
rt.plot_rtt_stuttering(temptxtName,taskRttlist,Stutteringlist,part = 1) #part表示控制和不控制的分配比例，没有就1，图两边对称



