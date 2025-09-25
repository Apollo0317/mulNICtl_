'''
Author: error: error: git config user.name & please set dead value or install git && error: git config user.email & please set dead value or install git & please set dead value or install git
Date: 2025-06-30 22:20:01
LastEditors: error: error: git config user.name & please set dead value or install git && error: git config user.email & please set dead value or install git & please set dead value or install git
LastEditTime: 2025-07-01 22:36:19
FilePath: /mulNICtl_orignal_2/exp2.py
Description: 这是默认设置,请设置`customMade`, 打开koroFileHeader查看配置 进行设置: https://github.com/OBKoro1/koro1FileHeader/wiki/%E9%85%8D%E7%BD%AE
'''
import sys
import os
import os
import json
import time
import util.ctl as ctl
import util.qos as qos
import util.constHead as constHead
import traceback
import subprocess
import tempfile
import  numpy as np
from tap import Connector
from util.stream import stream 
from util.solver import globalSolver, balanceSolver
from util.logger import QosLogger
from util.trans_graph import LINK_NAME_TO_TX_NAME,LINK_NAME_TO_RX_NAME
from tools.read_graph import construct_graph
from typing import List
import logging
import base64
import socket
import scale
import multiprocessing
import subprocess
from exp.utils.log_utils import setup_logger_if_needed
from exp.utils.topo_utils import load_topology
from exp.utils.stream_builder import *
from exp.utils.parapmeter_defined import params
from exp.utils.controller_lancher import run_command
from exp.utils.stream_replay import *
def cleanall(links):
    """
    从 trans_manifests 创建所有 stream 并添加到拓扑中。
    返回构建好的 stream 列表。
    """

    conn = Connector()
    conn2 = Connector()
    for link_line in links:
        sender1 = LINK_NAME_TO_TX_NAME(link_line)
        sender2 = LINK_NAME_TO_RX_NAME(link_line)
        conn.batch(sender1, "clean_tx", {
        }).wait(0.5).apply()
        conn.batch(sender1, "clean_rx", {
        }).wait(0.5).apply()
        conn2.batch(sender2, "clean_tx", {
        }).wait(0.5).apply()
        conn2.batch(sender2, "clean_rx", {
        }).wait(0.5).apply()

    conn2.batch("SoftAP", "clean_monitor", {
        }).wait(0.5).apply()
    return 

def main():
    
    topo, links, ip_table = load_topology(params["topo_address"], logger = None)

    cleanall(links)

    




main()