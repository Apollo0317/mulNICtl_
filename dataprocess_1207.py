import matplotlib.pyplot as plt
import numpy as np
import os
import seaborn as sns
import pandas as pd
import time
import json
# import scale

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
        lineList = line.split(" ")
        
        # lineList = re.split(r'[,\s]+',line)
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
    NoAda_stuttering = 0
    Ada_stuttering = 0
    Ada_index = int((1-part)*(len(dataArray)-1))
    if len(dataArray)>1:
        diff = np.diff(dataArray)[1:] - 0.016
        Noadadiff = diff[:int(len(diff)*part)]
        Adadiff = diff[Ada_index:]
        Ada_stuttering = sum(Adadiff[Adadiff>0.016])
        NoAda_stuttering = sum(Noadadiff[Noadadiff>0.016])
    # print(NoAda_stuttering,Ada_stuttering)
    NoAda_stuttering = NoAda_stuttering/(dataArray[int(len(diff)*part-1)]-dataArray[0])
    Ada_stuttering = Ada_stuttering/(dataArray[-1]-dataArray[Ada_index+1])
    # print("Noada stuttering is %.3f, Ada stuttering is %.3f"%(NoAda_stuttering,Ada_stuttering))
    return port,NoAda_stuttering,Ada_stuttering,(NoAda_stuttering-Ada_stuttering)/NoAda_stuttering

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
    # plt.yscale('custom', threshold=60)
    plt.xlabel("Packet Index", fontsize=16)
    plt.ylabel("RTT (ms)",fontsize=16)
    plt.ylim([0, 100])
    plt.grid()
    plt.legend(fontsize=12)
    plt.tight_layout()
    plt.savefig(fileName.split(".txt")[0]+'.png') 
    plt.show()

def main():

    filepath = f"dpScript/2024-12-5-s3/"      

    taskList = []
    taskRttlist = {}
    Stutteringlist = {}
    for idxstream in range(23,28):
        taskList.append(f"output{idxstream}.txt")
    for txtName in taskList:
        temptxtName = filepath+ 'rtt/' + txtName
        tempstutteringfileName = filepath + "stuttering/" + txtName
        if os.path.exists(temptxtName):
            delLastLine(temptxtName)
            port,temprttArray = txtRead_multiChannel_port(temptxtName)
            taskRttlist[port] = temprttArray
        if os.path.exists(tempstutteringfileName):
            port,NA_stuttering,Ada_stuttering,stuttering_gain = Stuttering_cal(filename=tempstutteringfileName,part= 0.2)
            print( port,NA_stuttering,Ada_stuttering,stuttering_gain)
            Stutteringlist[port] = [NA_stuttering,Ada_stuttering,stuttering_gain]
    plot_rtt_stuttering(temptxtName,taskRttlist,Stutteringlist,part = 0.2)



if __name__ == "__main__":
    main()
