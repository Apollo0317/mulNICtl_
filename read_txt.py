import matplotlib.pyplot as plt
import numpy as np
import os
import seaborn as sns
import pandas as pd
import time
import json
import scale

from matplotlib import rcParams
rcParams['font.family'] ='sans-serif'
# rcParams['font.sans-serif'] = ['Arial']
rcParams['font.size'] = 16
def delLastLine(fileName):
    with open(fileName, 'r') as f:
        lines = f.readlines()
    if "@" in lines[-1]:
        print('filename is ', fileName)
        with open(fileName, 'w') as f:
            f.writelines(lines[:-1])
        

def txtRead_multiChannel(fileName):
    from collections import Counter
    file = open(fileName, "r")
    lines = file.readlines()
    rttlist = []
    packetIdx = []
    for idxLine,line in enumerate(lines):
        if idxLine > 1:
            lineList = line.split(" ")
            if len(lineList) < 2:
                break
            packetIdx.append(int(lineList[0]))
            rttlist.append(float(lineList[2]))
    file.close()
    IdxList = list(set(packetIdx))
    IdxList.sort(key=packetIdx.index)
    IdxList.pop()
    # print("IdxList: ",IdxList.type)
    # print("IdxList: ",IdxList)

    Channel1Num = Counter(rttlist)[0]
    Channel2Num = Counter(rttlist)[1]
    print("Channel1Num: ",Channel1Num)
    print("Channel2Num: ",Channel2Num)
    
    data = np.loadtxt(fileName, skiprows=2)
    datachannel1 = np.empty((Channel1Num,2)) #2.4G
    datachannel2 = np.empty((Channel2Num,2)) #5G
    # print("datachannel1 shape: ",datachannel1.shape)
    # print("data shape: ",data.shape)
    # print("data :", data[-1,:],data[0,:])
    data1Idx = 0
    data2Idx = 0
    for idxrow in range(Channel1Num + Channel2Num - 1): 
        if data[idxrow,2] == 0:
            datachannel1[data1Idx,:] = data[idxrow,:2]
            data1Idx += 1
        elif data[idxrow,2] == 1:
            # print(data2Idx) 
            datachannel2[data2Idx,:] = data[idxrow,:2]
            data2Idx += 1
    
    ## max data
    rttArray = np.empty((len(IdxList),2),dtype=float)
    for idxrow,item in enumerate(IdxList):
        # print(item)
        rttArray[idxrow,0] = item
        if item in datachannel1[:,0]:
            a = np.where(datachannel1[:,0]==item)[0][0]
            if item in datachannel2[:,0]:
                b = np.where(datachannel2[:,0]==item)[0][0]
                rttArray[idxrow,1] = np.max((datachannel1[a,1],datachannel2[b,1]))
            else:
                rttArray[idxrow,1] = datachannel1[a,1]     
        else:
            if item in datachannel2[:,0]:
                b = np.where(datachannel2[:,0]==item)[0][0]
                rttArray[idxrow,1] = datachannel2[b,1]
    print("rttArray shape: ",rttArray.shape)
    print("rttArray :", rttArray[-1,:],rttArray[0,:])
    return rttArray    



# def txtRead_multiChannel_port(fileName):
#     from collections import Counter
#     file = open(fileName, "r")
#     lines = file.readlines()
#     rttlist = []
#     packetIdx = []
#     port = lines[1].split("@")[0][-4:]
#     print(port)
#     for idxLine,line in enumerate(lines):
#         if idxLine > 1:
#             lineList = line.split(" ")
#             if len(lineList) < 2:
#                 break
#             packetIdx.append(int(lineList[0]))
#             rttlist.append(float(lineList[2]))
#     file.close()
#     IdxList = list(set(packetIdx))
#     IdxList.sort(key=packetIdx.index)
#     IdxList.pop()
#     # print("IdxList: ",IdxList.type)
#     # print("IdxList: ",IdxList)

#     Channel1Num = Counter(rttlist)[0]
#     Channel2Num = Counter(rttlist)[1]
#     print("Channel1Num: ",Channel1Num)
#     print("Channel2Num: ",Channel2Num)
    
#     data = np.loadtxt(fileName, skiprows=2)
#     datachannel1 = np.empty((Channel1Num,2)) #2.4G
#     datachannel2 = np.empty((Channel2Num,2)) #5G
#     # print("datachannel1 shape: ",datachannel1.shape)
#     # print("data shape: ",data.shape)
#     # print("data :", data[-1,:],data[0,:])
#     data1Idx = 0
#     data2Idx = 0
#     for idxrow in range(Channel1Num + Channel2Num - 1): 
#         if data[idxrow,2] == 0:
#             datachannel1[data1Idx,:] = data[idxrow,:2]
#             data1Idx += 1
#         elif data[idxrow,2] == 1:
#             # print(data2Idx) 
#             datachannel2[data2Idx,:] = data[idxrow,:2]
#             data2Idx += 1
    
#     ## max data
#     rttArray = np.empty((len(IdxList),1),dtype=float)
#     for idxrow,item in enumerate(IdxList):
#         # print(item)
#         rttArray[idxrow,0] = item
#         if item in datachannel1[:,0]:
#             a = np.where(datachannel1[:,0]==item)[0][0]
#             if item in datachannel2[:,0]:
#                 b = np.where(datachannel2[:,0]==item)[0][0]
#                 rttArray[idxrow,0] = np.max((datachannel1[a,1],datachannel2[b,1]))
#             else:
#                 rttArray[idxrow,0] = datachannel1[a,1]     
#         else:
#             if item in datachannel2[:,0]:
#                 b = np.where(datachannel2[:,0]==item)[0][0]
#                 rttArray[idxrow,0] = datachannel2[b,1]
#     print("rttArray shape: ",rttArray.shape)
#     print("rttArray :", rttArray[-1,:],rttArray[0,:])
#     return port,rttArray    

def txtRead(fileName):
    file = open(fileName, "r")
    lines = file.readlines()
    rttlist = []
    for idxLine,line in enumerate(lines):
        if idxLine > 2:
            lineList = line.split(" ")
            if len(lineList) < 2:
                break
            rttlist.append(float(lineList[1]))
    file.close()
    return rttlist

def txtRead_multiChannel_port(fileName):

    data = []
    file = open(fileName, "r")
    lines = file.readlines()
    rttlist = []
    packetIdx = []
    port = lines[1].split("@")[0][-4:]
    print(port)
    for idxLine,line in enumerate(lines):
        if idxLine > 1:
            lineList = line.split(" ")
            if len(lineList) < 2:
                break
            packet_id,rtt,flag=int(lineList[0]),float(lineList[1]),int(lineList[2])
            data.append((packet_id,rtt,flag))
    max_rtt_dict={}
    for packet_id,rtt,flag in data:
        if packet_id not in max_rtt_dict:
            max_rtt_dict[packet_id]=rtt
        else:
            max_rtt_dict[packet_id]=max(max_rtt_dict[packet_id],rtt)
    sorted_packet_ids =sorted(max_rtt_dict.keys())
    rttArray=np.array([max_rtt_dict[pid] for pid in sorted_packet_ids])
    rttArray=rttArray.reshape(-1,1)
    print(rttArray.shape)
    return port,rttArray  

import  re
def Stuttering_cal(filename,index=0,part = 0.1):
    delLastLine(filename)
    data = []
    file = open(filename, "r")
    lines = file.readlines()
    port = lines[1].split(".txt")[0][-4:]

    for idxLine,line in enumerate(lines[2:]):
        # lineList = line.split(" ")
        
        lineList = re.split(r'[,\s]+',line)
        # if len(lineList) < 2:
        #     break
        packet_id, packet_size, timesp,=int(lineList[0]),int(lineList[1]),float(lineList[2])
        data.append((packet_id,packet_size,timesp))
    
    # ordered_data = sorted(data, key=lambda x: x[0])
    filtered_data = [(-1,0,0)]
    for x in data:
        if x[0] > filtered_data[-1][0]:
            filtered_data.append(x)
    # print(filtered_data); exit()
    dataArray = [ x[2] for x in filtered_data[1:] ]

    # after_ordered_data = ordered_data[- int(len(dataArray) * 0.3) : ]
    # after_dataArray = np.array(dataArray[ - int(len(dataArray) * 0.3) : ])
    # Adadiff = np.diff(after_dataArray)
    # [ print(after_ordered_data[i]) for i,x in enumerate(list(Adadiff > 9) ) if x]
    # exit()
    # print( list(Adadiff > 0.032).count(True) )
    # print( Adadiff[ Adadiff > 0.032 ] ); exit()

    NoAda_stuttering = 0
    Ada_stuttering = 0
    Ada_index = int((1-part)*(len(dataArray)-1))
    if len(dataArray)>1:
        diff = np.diff(dataArray)[1:] - 0.016
        Noadadiff = diff[:int(len(diff)*part)]
        Adadiff = diff[Ada_index:]
        # for temp in Noadadiff:
        #     if temp > 0.016:
        #         NoAda_stuttering += temp
        # for temp in Adadiff:
        #     if temp > 0.016:
        #         Ada_stuttering += temp
    #     print(np.max(Adadiff))
    #     plt.figure(figsize=(10, 6))
        
    #     packet_index=len(Adadiff)
    #     print(packet_index)
    #     print(Adadiff)

    #     filename_order='order'
    #     # np.savetxt(filename_order,rttArray[:,0])
    #     plt.plot(range(packet_index),Adadiff * 1000)
    #     # plt.title(fileName.split("/")[-1], fontsize=24)
    #     plt.xlabel("PacketIndex", fontsize=16)
    #     plt.ylabel("Diff_RTT (ms)",fontsize=16)
    # # plt.legend([" (avg RTT: %.2f ms)" % rttAverage + " (std: %.2f ms)" % rttstd ], loc='upper right', fontsize=12)
    # # plt.savefig("./"+fileName.split(".")[0] + "Order_time.png")
    #     plt.show()
        Ada_stuttering = sum(Adadiff[Adadiff>0.016])
        # print("wwww",Ada_stuttering)
        # print("aaa",dataArray[-1]-dataArray[Ada_index+1])
        NoAda_stuttering = sum(Noadadiff[Noadadiff>0.016])
    # print(NoAda_stuttering,Ada_stuttering)
    NoAda_stuttering = NoAda_stuttering/(dataArray[int(len(diff)*part-1)]-dataArray[0])
    Ada_stuttering = Ada_stuttering/(dataArray[-1]-dataArray[Ada_index+1])
    # print("Noada stuttering is %.3f, Ada stuttering is %.3f"%(NoAda_stuttering,Ada_stuttering))
    if(NoAda_stuttering==0):
        return port,NoAda_stuttering,Ada_stuttering,0
    else:    
        return port,NoAda_stuttering,Ada_stuttering,(NoAda_stuttering-Ada_stuttering)/NoAda_stuttering

def read_jsonl(file_path):
    json_list = []
    with open(file_path, 'r') as file:
        for line in file:
            data = json.loads(line)
            json_list.append(data)
    return json_list

#画自适应的rtt cdf曲线
def rttArraySinglePlot_cdf(fileName,rttArray,index=0):
    targetRtt = 22
    plt.figure(figsize=(10, 6))   
    rttlist = rttArray[index:,1] * 1000 # convert to ms.
    print("rttlist shape: ",rttlist.shape)
    rttstd = np.std(rttlist)
    print("rttstd: ",rttstd)
    rttAverage = np.mean(rttlist)
    snsplot = sns.ecdfplot(rttlist)       
    plt.axvline(x=targetRtt, color='r', linestyle='--', label='Target RTT')
    plt.title(fileName.split("/")[-1] + ": rttstd: %.2f" % rttstd, fontsize=24)
    plt.xlabel("RTT (ms)", fontsize=16)
    plt.ylabel("CDF",fontsize=16)
    plt.grid()
    plt.legend([" (avg RTT: %.2f ms)" % rttAverage, "Target RTT: %.2f ms" % targetRtt], loc='upper right', fontsize=12)
    plt.savefig("./"+fileName.split(".")[1] + f"_{index}_cdf.png")     
    # plt.savefig("./"+fileName.split(".")[1] + "10s_cdf.png")     

def rttArrayDictPlot_cdf(fileName,taskrtt,index=0):
    print(fileName)
    targetRtt = 22
    plt.figure(figsize=(10, 6))   
    plt.axvline(x=targetRtt, color='r', linestyle='--', label='Target RTT')
    for port,rttlist in taskrtt.items():
        rttlist = np.array(rttlist) * 1000 # convert to ms.
        rttlist = rttlist[index:]
        rttstd = np.std(rttlist)
        rttAverage = np.mean(rttlist)
        sns.ecdfplot(rttlist, label=port+" (avg RTT: %.2f ms)" % rttAverage + " (std: %.2f ms)" % rttstd)       
        
    plt.title(fileName.split("/")[-1] ,fontsize=24)
    plt.xlabel("RTT (ms)", fontsize=16)
    plt.ylabel("CDF",fontsize=16)
    plt.grid()
    plt.legend(fontsize=12)
    plt.savefig(fileName.split(".txt")[0] + f"_{index}_cdf.png") 
    plt.show()
        
def rttArrayDictPlot_cdf_ada(fileName,taskrtt,index=0,part = 0.45):
    #NoAda and Ada
    # print(fileName)
    # color_list = ['r','b','y','g','k','c','m','w']
    color_list = ['#000000','#FF0000','#00FF00','#0000FF','#FFFF00','#800080','#A52A2A','#808000','#FFD700','#C15500']

    targetRtt = 22
    plt.figure(figsize=(10, 6))   
    plt.axvline(x=targetRtt, color='r', linestyle='--', label='Target RTT')
    for idx, (port,rttlist) in enumerate(taskrtt.items()):
        print("PORT:    ",port)
        TotalLen = len(rttlist)
        NoadaRttList = rttlist[:int(TotalLen*part)]
        AdaRttList = rttlist[-int(TotalLen*part):]
        NoadaRttList = np.array(NoadaRttList) * 1000 # convert to ms.
        AdaRttList = np.array(AdaRttList) * 1000 # convert to ms.
        # rttlist = rttlist[index:]
        Noadarttstd = np.std(NoadaRttList)
        Adarttstd = np.std(AdaRttList)
        NoadarttAverage = np.mean(NoadaRttList)
        AdarttAverage = np.mean(AdaRttList)
        Gain = (NoadarttAverage-AdarttAverage)/NoadarttAverage
        print("Gain: ", Gain)
        print('color :', color_list[idx])
        sns.ecdfplot(NoadaRttList, linestyle = "--",label=port+" (Single avg RTT: %.2f ms)" % NoadarttAverage + " (std: %.2f ms)" % Noadarttstd)
        sns.ecdfplot(AdaRttList, color = color_list[idx],label=port+" (Double: %.2f ms)" % AdarttAverage + " (std: %.2f ms)" % Adarttstd + " (Gain: %.3f )"% Gain) 
    ax = plt.gca()
    colorIdx = 0
    for idx in range(1,len(ax.lines),2):
        ax.lines[idx].set_color(color_list[colorIdx])
        ax.lines[idx+1].set_color(color_list[colorIdx])
        colorIdx += 1  
    plt.title(fileName.split("/")[-1] ,fontsize=24)
    plt.xlabel("RTT (ms)", fontsize=16)
    plt.ylabel("CDF",fontsize=16)
    plt.xlim([0, 80])
    plt.grid()
    plt.legend(fontsize=12)
    plt.savefig(fileName.split(".txt")[0] + f"_{index}_cdf.png") 
    plt.show()

def rttArrayDictPlot_time_ada(fileName,taskrtt,index=0,part = 0.45):
    #NoAda and Ada
    # print(fileName)
    # color_list = ['r','b','y','g','k','c','m','w']
    color_list = ['#000000','#FF0000','#00FF00','#0000FF','#FFFF00','#800080','#A52A2A','#808000','#FFD700','#C15500']

    targetRtt = 22
    plt.figure(figsize=(10, 6))   
    plt.axvline(x=targetRtt, color='r', linestyle='--', label='Target RTT')
    for idx, (port,rttlist) in enumerate(taskrtt.items()):
        print("PORT:    ",port)
        TotalLen = len(rttlist)
        NoadaRttList = rttlist[:int(TotalLen*part)]
        AdaRttList = rttlist[-int(TotalLen*part):]
        LenTotal = len(NoadaRttList) + len(AdaRttList)
        idxList = range(LenTotal)
        NoadaRttList = np.array(NoadaRttList) * 1000 # convert to ms.
        AdaRttList = np.array(AdaRttList) * 1000 # convert to ms.
        NoadaRttconv = np.convolve(NoadaRttList.T[0],np.array([1] * 100), 'same')/100
        AdaRttconv = np.convolve(AdaRttList.T[0],np.array([1] * 100), 'same')/100
        # rttlist = rttlist[index:]
        Noadarttstd = np.std(NoadaRttList)
        Adarttstd = np.std(AdaRttList)
        NoadarttAverage = np.mean(NoadaRttList)
        AdarttAverage = np.mean(AdaRttList)
        Gain = (NoadarttAverage-AdarttAverage)/NoadarttAverage
        print("Gain: ", Gain)
        print('color :', color_list[idx])
        # plt.plot(idxList[:len(NoadaRttList)],NoadaRttList,color = color_list[idx], linestyle = "--",label=port+" (Single avg RTT: %.2f ms)" % NoadarttAverage + " (std: %.2f ms)" % Noadarttstd)
        plt.plot(idxList[:len(NoadaRttList)],NoadaRttconv,color = color_list[idx], linestyle = ":",linewidth = 2, label=port+"conv" )
        # plt.plot(idxList[len(NoadaRttList):],AdaRttList, color = color_list[idx],label=port+" (Double: %.2f ms)" % AdarttAverage + " (std: %.2f ms)" % Adarttstd + " (Gain: %.3f )"% Gain) 
        plt.plot(idxList[len(NoadaRttList):],AdaRttconv,color = color_list[idx], linestyle = "--",linewidth = 2, label=port+"conv" )
    # ax = plt.gca()
    # colorIdx = 0
    # for idx in range(1,len(ax.lines),2):
    #     ax.lines[idx].set_color(color_list[colorIdx])
    #     ax.lines[idx+1].set_color(color_list[colorIdx])
    #     colorIdx += 1  
    plt.title(fileName.split("/")[-1] ,fontsize=24)
    plt.xlabel("Packet Index", fontsize=16)
    plt.ylabel("RTT (ms)",fontsize=16)
    plt.ylim([0, 100])
    plt.grid()
    # plt.legend(fontsize=12)
    plt.savefig(fileName.split(".txt")[0] + f"_{index}_time.png") 
    # plt.show()
    
#画自适应的rtt曲线
def rttArraySinglePlot_time(fileName,rttArray):
    plt.figure(figsize=(10, 6))
    # rttArray= txtRead_multiChannel(fileName)
    rttlist = rttArray[:,1] * 1000 # convert to ms.
    print("rttlist shape: ",rttlist.shape)
    rttAverage = np.mean(rttlist)
    plt.plot(rttlist)
    plt.title(fileName.split("/")[-1], fontsize=24)
    plt.xlabel("PacketIndex", fontsize=16)
    plt.ylabel("RTT (ms)",fontsize=16)
    plt.legend([" (avg RTT: %.2f ms)" % rttAverage], loc='upper right', fontsize=12)
    plt.savefig("./"+fileName.split(".")[1] + "_time.png") 
    plt.show()
        
def rttPlot(scenario):
    path_files = os.listdir("./"+scenario)
    loop = round(len(path_files)/5)
    print(loop)
    for idx_loop in range(loop):
        fileList = ["output"+str(i)+".txt" for i in range(idx_loop*5, (idx_loop+1)*5)]
        througputList = ["50Mbps","40Mbps","30Mbps","20Mbps","10Mbps"]
        lengendList = []
        duration = 10 #sum is 10s
        plt.figure(figsize=(10, 6))
        df = pd.DataFrame()
        for idx,fileName in enumerate(fileList):
            file = "./"+scenario + "/" + fileName
            rttlist = txtRead(file)
            rttlist = np.array(rttlist) * 1000 # convert to ms.
            # rttlist = outlier_removal(rttlist,50)
            # print("max RTT: ",max(rttlist))
            rttAverage = np.mean(rttlist)
            lengendList.append([througputList[idx] + " (avg RTT: %.2f ms)" % rttAverage])
            idxtime = np.arange(0, duration, duration/len(rttlist))
            snsplot = sns.ecdfplot(rttlist)
        
        plt.title(scenario, fontsize=24)
        plt.xlabel("RTT (ms)", fontsize=16)
        plt.ylabel("CDF",fontsize=16)
        plt.grid()
        plt.legend(lengendList, loc='upper right', fontsize=12)
        plt.savefig("./"+fileName.split(".")[1] + "_cdf.png")

def outlier_removal(data, thresh=100):
    for idx,data_point in enumerate(data):
        if data_point > thresh:
            data[idx] = np.mean(data[:idx])
    return data

#画单空口的rtt cdf曲线
def rttSinglePlot_cdf(fileName):
    targetRtt = 22
    plt.figure(figsize=(10, 6))
    duration = 20 #sum is 10s
    rttlist = txtRead(fileName)
    rttlist = np.array(rttlist) * 1000 # convert to ms.
    print("rttlist shape: ",rttlist.shape)
    # rttlist = outlier_removal(rttlist,50)
    # print("max RTT: ",max(rttlist))
    rttAverage = np.mean(rttlist)
    idxtime = np.arange(0, duration, duration/len(rttlist))
    # print(lengendList[idx])
    # df[througputList[idx]] = rttlist
    snsplot = sns.ecdfplot(rttlist)      
    plt.axvline(x=targetRtt, color='r', linestyle='--', label='Target RTT') 
    plt.title(fileName.split("/")[-1], fontsize=24)
    plt.xlabel("RTT (ms)", fontsize=16)
    plt.ylabel("CDF",fontsize=16)
    plt.grid()
    plt.legend([" (avg RTT: %.2f ms)" % rttAverage], loc='upper right', fontsize=12)
    plt.savefig("./"+fileName.split(".")[1] + "_cdf.png")

def plot_rtt_stuttering(fileName,taskrtt,taskstuttering,index=0,part = 0.1):
    #NoAda and Ada
    # color_list = ['r','b','y','g','k','c','m', '#afeeff','#bfdfff','#cfcfff']
    # color_list = ['#000000','#FF0000','#00FF00','#0000FF','#FFFF00','#800080','#A52A2A','#808000','#FFD700','#C15500']
    color_list = ['#000000','#FF0000','#00FF00','#0000FF','#FFFF00','#800080','#A52A2A','#FFA500','#ADD8E6','#C0C0C0', 'b']
    targetRtt = 22
    plt.figure(figsize=(15, 15))
    plt.subplot(2,1,1)   
    RttAvg = {"NoAda":[],"Ada":[]}
    plt.axvline(x=targetRtt, color='r', linestyle='--', label='Target RTT')
    for idx, (port,rttlist) in enumerate(taskrtt.items()):
        print("PORT:    ",port)
        rttlist = rttlist[index:]
        TotalLen = len(rttlist)
        NoadaRttList = rttlist[:int(TotalLen*part)]
        RttAvg["NoAda"].extend(NoadaRttList)
        AdaRttList = rttlist[-int(TotalLen*part):]
        RttAvg["Ada"].extend(AdaRttList)
        NoadaRttList = np.array(NoadaRttList) * 1000 # convert to ms.
        AdaRttList = np.array(AdaRttList) * 1000 # convert to ms.
        # rttlist = rttlist[index:]
        Noadarttstd = np.std(NoadaRttList)
        Adarttstd = np.std(AdaRttList)
        NoadarttAverage = np.mean(NoadaRttList)
        AdarttAverage = np.mean(AdaRttList)
        Gain = (NoadarttAverage-AdarttAverage)/NoadarttAverage
        # print("Gain: ", Gain)
        # print('color :', color_list[idx])
        sns.ecdfplot(NoadaRttList, linestyle = "--", label=port+" (Single avg RTT: %.2f ms)" % NoadarttAverage + " (std: %.2f ms)" % Noadarttstd)
        sns.ecdfplot(AdaRttList, color = color_list[idx], label=port+" (Double: %.2f ms)" % AdarttAverage + " (std: %.2f ms)" % Adarttstd + " (Gain: %.3f )"% Gain) 
    ax = plt.gca()
    colorIdx = 0
    for idx in range(1,len(ax.lines),2):
        ax.lines[idx].set_color(color_list[colorIdx])
        ax.lines[idx+1].set_color(color_list[colorIdx])
        colorIdx += 1  
    RttAvg["Ada avg rtt"] = np.mean(np.array(RttAvg["Ada"])*1000)
    RttAvg["Noada avg rtt"] = np.mean(np.array(RttAvg["NoAda"])*1000)
    RttAvg["avg gain"] = (RttAvg["Noada avg rtt"]-RttAvg["Ada avg rtt"])/RttAvg["Noada avg rtt"]    
    rtt_text = "rtt avg:"+" (Noada: %.3f)"%RttAvg["Noada avg rtt"]+ " (Ada: %.3f)"%RttAvg["Ada avg rtt"] + " (Gain: %.3f)"%RttAvg["avg gain"]
    plt.text(22,0.1,rtt_text,fontsize = 14)
    # ax[0].title(fileName.split("/")[-1] ,fontsize=24)
    plt.xlabel("RTT (ms)", fontsize=16)
    plt.ylabel("CDF",fontsize=16)
    plt.xlim([0, 80])
    plt.grid()
    plt.tight_layout()
    plt.legend(fontsize=12)

############# time
    plt.subplot(2,1,2)
    stutter_avg = {"Noada":[],"Ada":[]}
    for idx, (port,rttlist) in enumerate(taskrtt.items()):
        print("PORT:    ",port)
        TotalLen = len(rttlist)
        NoadaRttList = rttlist[:int(TotalLen*part)]
        AdaRttList = rttlist[-int(TotalLen*part):]
        LenTotal = len(NoadaRttList) + len(AdaRttList)
        idxList = range(LenTotal)
        NoadaRttList = np.array(NoadaRttList) * 1000 # convert to ms.
        AdaRttList = np.array(AdaRttList) * 1000 # convert to ms.
        NoadaRttconv = np.convolve(NoadaRttList.T[0],np.array([1] * 100), 'same')/100
        AdaRttconv = np.convolve(AdaRttList.T[0],np.array([1] * 100), 'same')/100
        Noadarttstd = np.std(NoadaRttList)
        Adarttstd = np.std(AdaRttList)
        NoadarttAverage = np.mean(NoadaRttList)
        AdarttAverage = np.mean(AdaRttList)
        Gain = (NoadarttAverage-AdarttAverage)/NoadarttAverage
        stutter_avg["Noada"].append(taskstuttering[port][0])
        print(taskstuttering)
        stutter_avg["Ada"].append(taskstuttering[port][1])
        print("Gain: ", Gain)
        print('color :', color_list[idx])
        plt.plot(idxList[:len(NoadaRttList)],NoadaRttconv,color = color_list[idx], linestyle = ":",linewidth = 2,
                  label=port+" (Noada stuttering: %.3f)"%taskstuttering[port][0])
        plt.plot(idxList[len(NoadaRttList):],AdaRttconv,color = color_list[idx], linestyle = "-",linewidth = 2, 
                 label=port+" (Ada stuttering: %.3f)"%taskstuttering[port][1] + " (Gain: %.3f) "%taskstuttering[port][2])
    stutter_avg["NoadaAvg"] = np.mean(stutter_avg["Noada"])
    stutter_avg["AdaAvg"] = np.mean(stutter_avg["Ada"])
    stutter_avg["Gain"] = (stutter_avg["NoadaAvg"]-stutter_avg["AdaAvg"])/stutter_avg["NoadaAvg"]
    plt.axhline(y=targetRtt, color='r', linestyle='--', label='Target RTT')
    stutter_text = "stuttering avg:"+" (Noada: %.3f)"%stutter_avg["NoadaAvg"]+ " (Ada: %.3f)"%stutter_avg["AdaAvg"] + " (Gain: %.3f)"%(stutter_avg["Gain"])
    plt.text(idxList[len(NoadaRttList)]*0.5,90,stutter_text,fontsize = 14)
    plt.yscale('custom', threshold=60)
    plt.xlabel("Packet Index", fontsize=16)
    plt.ylabel("RTT (ms)",fontsize=16)
    plt.ylim([0, 100])
    plt.grid()
    plt.legend(fontsize=12)
    plt.tight_layout()
    plt.savefig(fileName.split(".txt")[0]+'.png') 
    plt.show()


#画单空口的rtt曲线
def rttSinglePlot_time(fileName):
    plt.figure(figsize=(10, 6))
    duration = 20 #sum is 10s
    rttlist = txtRead(fileName)
    rttlist = np.array(rttlist) * 1000 # convert to ms.
    # rttlist = outlier_removal(rttlist,50)
    # print("max RTT: ",max(rttlist))
    rttAverage = np.mean(rttlist)
    rttstd = np.std(rttlist)
    # idxtime = np.arange(0, duration, duration/len(rttlist))
    plt.plot(rttlist)
    plt.title(fileName.split("/")[-1], fontsize=24)
    plt.xlabel("PacketIndex", fontsize=16)
    plt.ylabel("RTT (ms)",fontsize=16)
    plt.legend([" (avg RTT: %.2f ms)" % rttAverage + " (std: %.2f ms)" % rttstd ], loc='upper right', fontsize=12)
    plt.savefig("./"+fileName.split(".")[0] + "_time.png")

#画单空口的rtt曲线
def rttPacket(fileName,rttArray):
    plt.figure(figsize=(10, 6))
    duration = 20 #sum is 10s
    packet_index=rttArray.shape[0]
    # print(packet_index)
    # print(rttArray[:,0])

    filename_order='order'
    np.savetxt(filename_order,rttArray[:,0])
    plt.plot(range(packet_index),rttArray[:,0] * 1000)
    plt.title(fileName.split("/")[-1], fontsize=24)
    plt.xlabel("PacketIndex", fontsize=16)
    plt.ylabel("RTT (ms)",fontsize=16)
    # plt.legend([" (avg RTT: %.2f ms)" % rttAverage + " (std: %.2f ms)" % rttstd ], loc='upper right', fontsize=12)
    plt.savefig("./"+fileName.split(".")[0] + "Order_time.png")
    # plt.show()

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


# def plot_json(filename):
#     datas = read_jsonl(filename)
#     task_list = []
#     channel_rtts = {}
#     rtts = {}
#     tx_parts = {}
#     TimeIndexlist= {}
#     channel_colors = {"2.4G":[],"5G":[],"Index":[]}
#     TimeIndex = 0
#     fig, axs = plt.subplots(4,1, figsize=(15, 15))
#     # print(axs)
#     portlist = ["6211@96","6212@96"]
#     for tasks in datas:
#         dataidx = 0
#         tempcolors = {"2.4G":[],"5G":[]}
#         # for port in portlist:
#         #     tasks.pop(port, None)
#         for task, vals in tasks.items(): 
#             if task not in task_list:
#                 task_list.append(task)
#             # print("task",task,vals)
#             if "channel_colors" in vals:
#                 try:
#                     tempcolors["2.4G"].append(vals['channel_colors'][0])
#                     tempcolors["5G"].append(vals['channel_colors'][1])
#                 except:
#                     continue

#             elif "channel_rtts" in vals:
#                 if dataidx == 0:
#                     TimeIndex += 1
#                     dataidx += 1
#                 if task not in channel_rtts:
#                     channel_rtts[task] = []
#                 # print(vals['channel_rtts'])
#                 channel_rtts[task].append(np.array(vals['channel_rtts']) * 1000)
#                 if task not in rtts:
#                     rtts[task] = []
#                 rtts[task].append(np.array(vals['rtt']) * 1000)

#                 if task not in tx_parts:
#                     tx_parts[task] = []
#                 tx_parts[task].append(np.array(vals['tx_parts']))

#                 if task not in TimeIndexlist:
#                     TimeIndexlist[task] = []
#                 TimeIndexlist[task].append(TimeIndex)
#                             # print("datasindexList:", datasindexList)
#             # exit()
#         if tempcolors["2.4G"]:
#             color = colors_cal(tempcolors)
#             channel_colors["2.4G"].append(color[0])
#             channel_colors["5G"].append(color[1])
#             channel_colors["Index"].append(TimeIndex)
#     # labelList = []
#     channel_idx = ['2.4GHz', '5GHz']
#     # color_list = ['b','y','g','k','c','m','r']
#     # color_list = ['#000000','#FF0000','#00FF00','#0000FF','#FFFF00','#800080','#A52A2A','#808000','#FFD700','#C15500']
#     # print("channel rtts",channel_rtts)
#     color_list = ['#000000','#FF0000','#00FF00','#0000FF','#FFFF00','#800080','#A52A2A','#FFA500','#ADD8E6','#C0C0C0','b']
#     # Plot channel RTTs
#     for _, (task, c_rtts) in enumerate(channel_rtts.items()):
#         task_idx = task_list.index(task)
#         c_rtts = np.array(c_rtts).T
#         for idx, rtt in enumerate(c_rtts):
#             # IdxTimertt1 = range(0,len(rtt),1)
#             IdxTimertt1 = TimeIndexlist[task]
#             if idx == 0:
#                 axs[0].plot(IdxTimertt1,rtt, '-+',color = color_list[task_idx],  label=task + ' channel ' + channel_idx[idx])
#             else:
#                 axs[0].plot(IdxTimertt1,rtt, ':o',color = color_list[task_idx],  label=task + ' channel ' + channel_idx[idx])
#         # if index == 0:
#         #     axs[0].legend(loc = "upper center",bbox_to_anchor=(0.5, 1.1),
#         #         ncol=4, fancybox=True, shadow=True)
#     axs[0].set_yscale('custom', threshold=60)
#     axs[0].grid(linestyle='--')
#     axs[0].set_ylabel('Channel RTT (ms)')
#     axs[0].set_xlabel('Time (s)')
#     axs[0].set_xlim(0, TimeIndex+5)
#     # axs[0].legend(loc = "upper center",bbox_to_anchor=(0.5, 1.1),
#     #     ncol=4, fancybox=True, shadow=True)


#     targetRtt = 22
#     # # Plot RTTs
#     for _idx, (task, rtt) in enumerate(rtts.items()):
#         task_idx = task_list.index(task)
#         # Idxrtt = range(0,len(rtt),1)
#         Idxrtt = TimeIndexlist[task]
#         rtt = np.array(rtt)
#         axs[1].plot(Idxrtt,rtt, '-+',color=color_list[task_idx], label=task_list[task_idx])
#     axs[1].axhline(y=targetRtt, color = 'r',linestyle = '--', label='Target RTT (22ms)')
#     axs[1].set_yscale('custom', threshold=60)
#     axs[1].grid(linestyle='--')
#     axs[1].set_xlim(0, TimeIndex+5)
#     axs[1].set_ylim(0, 1000)
#     axs[1].set_ylabel('RTT (ms)')
#     axs[1].set_xlabel('Time (s)')
    
#     # # Plot TX Parts

#     for idx, (task, tx_part) in enumerate(tx_parts.items()):
#         task_idx = task_list.index(task)
#         IdxTxPart = TimeIndexlist[task]
#         tx_part = np.array(tx_part) * 100
#         # axs[2].plot(IdxTxPart,tx_part[:,1].T, '--',color=color_list[task_idx], label=task_list[task_idx])
#         # tx_part[:,1] = 100 - tx_part[:, 1]
#         tx_part = tx_part.T
#         axs[2].plot(IdxTxPart,tx_part[1,:], '-+',color=color_list[task_idx], label=task_list[task_idx])
#     axs[2].grid(linestyle='--')
#     axs[2].set_ylabel('TX Parts')
#     axs[2].set(ylim=(0,100))
#     axs[2].set_xlim(0, TimeIndex+5)
#     axs[2].set_xlabel('Time (s)')
#     axs[2].legend()


#     axs[3].plot(channel_colors["Index"],channel_colors["2.4G"],linewidth = 2, label="channel 1")
#     axs[3].plot(channel_colors["Index"],channel_colors["5G"],linewidth = 2, label="channel 2")
#     axs[3].grid(linestyle='--')
#     axs[3].set_ylabel('Channel color')
#     axs[3].set_yticks([0,0.5,1])
#     axs[3].set(ylim=(-0.1,1.1))
#     axs[3].set_xlim(0, TimeIndex+5)
#     axs[3].set_xlabel('Time (s)')
#     axs[3].legend()
#     plt.tight_layout()
#     plt.savefig(filename.split(".jsonl")[0]+'.png') 
#     plt.show()


def plot_json(filename):
    datas = read_jsonl(filename)
    task_list = []
    channel_rtts = {}
    rtts = {}
    tx_parts = {}
    TimeIndexlist= {}
    channel_colors = {"2.4G":[],"5G":[],"Index":[]}
    TimeIndex = 0
    fig, axs = plt.subplots(4,1, figsize=(15, 15))
    # print(axs)
    portlist = ["6211@96","6212@96"]
    for tasks in datas:
        dataidx = 0
        tempcolors = {"2.4G":[],"5G":[]}
        # for port in portlist:
        #     tasks.pop(port, None)
        for task, vals in tasks.items(): 
            if task not in task_list:
                task_list.append(task)
            # print("task",task,vals)
            if "channel_colors" in vals:
                try:
                    tempcolors["2.4G"].append(vals['channel_colors'][0])
                    tempcolors["5G"].append(vals['channel_colors'][1])
                except:
                    continue

            elif "channel_rtts" in vals:
                if dataidx == 0:
                    TimeIndex += 1
                    dataidx += 1
                if task not in channel_rtts:
                    channel_rtts[task] = []
                # print(vals['channel_rtts'])
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
                            # print("datasindexList:", datasindexList)
            # exit()
        if tempcolors["2.4G"]:
            color = colors_cal(tempcolors)
            channel_colors["2.4G"].append(color[0])
            channel_colors["5G"].append(color[1])
            channel_colors["Index"].append(TimeIndex)
    # labelList = []
    channel_idx = ['2.4GHz', '5GHz']
    # color_list = ['b','y','g','k','c','m','r']
    # color_list = ['#000000','#FF0000','#00FF00','#0000FF','#FFFF00','#800080','#A52A2A','#808000','#FFD700','#C15500']
    # print("channel rtts",channel_rtts)
    color_list = ['#000000','#FF0000','#00FF00','#0000FF','#FFFF00','#800080','#A52A2A','#FFA500','#ADD8E6','#C0C0C0','b']
    # Plot channel RTTs
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
        #     axs[0].legend(loc = "upper center",bbox_to_anchor=(0.5, 1.1),
        #         ncol=4, fancybox=True, shadow=True)
    axs[0].set_yscale('custom', threshold=60)
    axs[0].grid(linestyle='--')
    axs[0].set_ylabel('Channel RTT (ms)')
    axs[0].set_xlabel('Time (s)')
    axs[0].set_xlim(0, TimeIndex+5)
    # axs[0].legend(loc = "upper center",bbox_to_anchor=(0.5, 1.1),
    #     ncol=4, fancybox=True, shadow=True)


    targetRtt = 22
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
    axs[1].set_xlim(0, TimeIndex+5)
    axs[1].set_ylim(0, 1000)
    axs[1].set_ylabel('RTT (ms)')
    axs[1].set_xlabel('Time (s)')
    
    # # Plot TX Parts

    for idx, (task, tx_part) in enumerate(tx_parts.items()):
        task_idx = task_list.index(task)
        IdxTxPart = TimeIndexlist[task]
        tx_part = np.array(tx_part) * 100
        # axs[2].plot(IdxTxPart,tx_part[:,1].T, '--',color=color_list[task_idx], label=task_list[task_idx])
        # tx_part[:,1] = 100 - tx_part[:, 1]
        tx_part = tx_part.T
        axs[2].plot(IdxTxPart,tx_part[1,:], '-+',color=color_list[task_idx], label=task_list[task_idx])
    axs[2].grid(linestyle='--')
    axs[2].set_ylabel('TX Parts')
    axs[2].set(ylim=(0,100))
    axs[2].set_xlim(0, TimeIndex+5)
    axs[2].set_xlabel('Time (s)')
    axs[2].legend()


    axs[3].plot(channel_colors["Index"],channel_colors["2.4G"],linewidth = 2, label="channel 1")
    axs[3].plot(channel_colors["Index"],channel_colors["5G"],linewidth = 2, label="channel 2")
    axs[3].grid(linestyle='--')
    axs[3].set_ylabel('Channel color')
    axs[3].set_yticks([0,0.5,1])
    axs[3].set(ylim=(-0.1,1.1))
    axs[3].set_xlim(0, TimeIndex+5)
    axs[3].set_xlabel('Time (s)')
    axs[3].legend()
    plt.tight_layout()
    plt.savefig(filename.split(".jsonl")[0]+'.png') 
    plt.show()


def plot_Taskalljson(filename):
    datas = read_jsonl(filename)
    task_list = []
    channel_rtts = {}
    rtts = {}
    tx_parts = {}
    throttle = {}
    TimeIndexlist= {}
    channel_colors = {"2.4G":[],"5G":[],"Index":[]}
    TimeIndex = 0
    fig, axs = plt.subplots(5,1, figsize=(15, 15))
    # print(axs)
    portlist = ["6212@96","6213@96","6214@96","6215@96","6216@96","6217@96"]
    for tasks in datas:
        dataidx = 0
        tempcolors = {"2.4G":[],"5G":[]}
        # for port in portlist:
        #     tasks.pop(port, None)
        for task, vals in tasks.items(): 
            if task not in task_list:
                task_list.append(task)
            # print("task",task,vals)
            if "channel_colors" in vals:
                try:
                    tempcolors["2.4G"].append(vals['channel_colors'][0])
                    tempcolors["5G"].append(vals['channel_colors'][1])
                except:
                    continue

            elif "channel_rtts" in vals:
                if dataidx == 0:
                    TimeIndex += 1
                    dataidx += 1
                if task in portlist:
                    if task not in throttle:
                        throttle[task] = []
                    throttle[task].append(np.array(vals['throttle']))
                else:
                    if task not in channel_rtts:
                        channel_rtts[task] = []
                    # print(vals['channel_rtts'])
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
                            # print("datasindexList:", datasindexList)
            # exit()
        if tempcolors["2.4G"]:
            color = colors_cal(tempcolors)
            channel_colors["2.4G"].append(color[0])
            channel_colors["5G"].append(color[1])
            channel_colors["Index"].append(TimeIndex)
    # labelList = []
    channel_idx = ['2.4GHz', '5GHz']
    # color_list = ['b','y','g','k','c','m','r']
    color_list = ['#000000','#FF0000','#00FF00','#0000FF','#FFFF00','#800080','#A52A2A','#808000','#FFD700','#C15500']
    # print("channel rtts",channel_rtts)

    # Plot channel RTTs
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
        #     axs[0].legend(loc = "upper center",bbox_to_anchor=(0.5, 1.1),
        #         ncol=4, fancybox=True, shadow=True)
    axs[0].set_yscale('custom', threshold=60)
    axs[0].grid(linestyle='--')
    axs[0].set_ylabel('Channel RTT (ms)')
    axs[0].set_xlabel('Time (s)')
    axs[0].set_xlim(0, TimeIndex+5)
    # axs[0].legend(loc = "upper center",bbox_to_anchor=(0.5, 1.1),
    #     ncol=4, fancybox=True, shadow=True)


    targetRtt = 22
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
    axs[1].set_xlim(0, TimeIndex+5)
    axs[1].set_ylim(0, 1000)
    axs[1].set_ylabel('RTT (ms)')
    axs[1].set_xlabel('Time (s)')
    
    # # Plot TX Parts

    for idx, (task, tx_part) in enumerate(tx_parts.items()):
        task_idx = task_list.index(task)
        IdxTxPart = TimeIndexlist[task]
        tx_part = np.array(tx_part) * 100
        # axs[2].plot(IdxTxPart,tx_part[:,1].T, '--',color=color_list[task_idx], label=task_list[task_idx])
        # tx_part[:,1] = tx_part[:, 1]
        tx_part = tx_part.T
        axs[2].plot(IdxTxPart,tx_part[1,:], '-+',color=color_list[task_idx], label=task_list[task_idx])
    axs[2].grid(linestyle='--')
    axs[2].set_ylabel('TX Parts')
    axs[2].set(ylim=(0,100))
    axs[2].set_xlim(0, TimeIndex+5)
    axs[2].set_xlabel('Time (s)')
    axs[2].legend()


    axs[3].plot(channel_colors["Index"],channel_colors["2.4G"],linewidth = 2, label="channel 1")
    axs[3].plot(channel_colors["Index"],channel_colors["5G"],linewidth = 2, label="channel 2")
    axs[3].grid(linestyle='--')
    axs[3].set_ylabel('Channel color')
    axs[3].set_yticks([0,0.5,1])
    axs[3].set(ylim=(-0.1,1.1))
    axs[3].set_xlim(0, TimeIndex+5)
    axs[3].set_xlabel('Time (s)')
    axs[3].legend()

    for _idx, (task, throttle_v) in enumerate(throttle.items()):
        task_idx = task_list.index(task)
        # Idxrtt = range(0,len(rtt),1)
        Idxrtt = TimeIndexlist[task]
        throttle_v = np.array(throttle_v)
        axs[4].plot(Idxrtt,throttle_v, '-+',color=color_list[task_idx], label=task_list[task_idx])
    # axs[4].axhline(y=targetRtt, color = 'r',linestyle = '--', label='Target RTT (22ms)')
    # axs[4].set_yscale('custom', threshold=60)
    axs[4].grid(linestyle='--')
    axs[4].set_xlim(0, TimeIndex+5)
    axs[4].set_ylim(0, 1000)
    axs[4].set_ylabel('throttle (Mbps)')
    axs[4].set_xlabel('Time (s)')

    plt.tight_layout()
    plt.savefig(filename.split(".jsonl")[0]+'.png') 
    plt.show()


def main():

    taskList = []
    taskRttlist = {}
    Stutteringlist = {}
    txtIndex = 4
    taskNum = 4
    filepath = "dpScript/2024-8-2/"
    stuttering_filepath = filepath + "stuttering/"
    jsonlfilename = filepath+f"Qos_{txtIndex}.jsonl"
    # task = read_jsonl(jsonlfilename)[10]
    for idxstream in range(txtIndex,txtIndex+taskNum):
        taskList.append(f"output{idxstream}.txt")
    for txtName in taskList:
        temptxtName = filepath+ 'rtt/' + txtName
        tempstutteringfileName = stuttering_filepath + txtName
        if os.path.exists(temptxtName):
            delLastLine(temptxtName)
            port,temprttArray = txtRead_multiChannel_port(temptxtName)
            taskRttlist[port] = temprttArray
        if os.path.exists(tempstutteringfileName):
            port,NA_stuttering,Ada_stuttering,stuttering_gain = Stuttering_cal(filename=tempstutteringfileName)
            Stutteringlist[port] = [NA_stuttering,Ada_stuttering,stuttering_gain]
    print("filename:", temptxtName.split('.txt')[0])
    plot_rtt_stuttering(temptxtName,taskRttlist,Stutteringlist,index=100,part = 0.48)
    plot_json(jsonlfilename)



       



if __name__ == "__main__":
    main()
