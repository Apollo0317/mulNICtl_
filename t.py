import os
date = f"12-5-s1"
filepath = f"dpScript/2024-{date}/"       #############################################
import read_txt as rt

taskList = []
taskRttlist = {}
Stutteringlist = {}
jsonlfilename = filepath+f"Qos_20.jsonl"
Taskallfilename = filepath+f"TaskAll_131.jsonl"
for idxstream in range(0,1):
    taskList.append(f"output{idxstream}.txt")
for txtName in taskList:
    temptxtName = filepath+ 'rtt/' + txtName
    tempstutteringfileName = filepath + "stuttering/" + txtName
    rt.rttSinglePlot_time(temptxtName)
    if os.path.exists(temptxtName):
        rt.delLastLine(temptxtName)
        port,temprttArray = rt.txtRead_multiChannel_port(temptxtName)
        taskRttlist[port] = temprttArray
        rt.rttPacket(temptxtName,temprttArray)
    if os.path.exists(tempstutteringfileName):
        port,NA_stuttering,Ada_stuttering,stuttering_gain = rt.Stuttering_cal(filename=tempstutteringfileName,part= 0.3)
        print( port,NA_stuttering,Ada_stuttering,stuttering_gain)
        Stutteringlist[port] = [NA_stuttering,Ada_stuttering,stuttering_gain]
# rt.rttSinglePlot_time(temptxtName)
rt.plot_rtt_stuttering(temptxtName,taskRttlist,Stutteringlist,part = 0.3)
rt.plot_json(jsonlfilename)
# rt.plot_Taskalljson(Taskallfilename)


