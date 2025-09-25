# mulNICtl user manual

## 1.  项目总览
mulNICtl 是一个多网络接口控制与传输实验工具，支持网络拓扑配置、数据流传输模拟以及实时监控与调度。项目目录结构如下：
```bash
.
├── config
│   ├── stream
│   │   └── ...
│   └── topo   
│       └── ...
├── config_all.py
├── install.py
├── manifest.json
├── mulNICtl.py
├── requirements.txt
├── run_exp.py
├── solver/src
│   ├── api
│   │   └── ...
│   ├── core
│   │   └── ...
│   ├── types
│   │   └── ...
│   ├── tests
│   │   └── ...
├── stream-replay
│   ├── android 
│   │   └── ...
│   ├── Cargo.lock
│   ├── Cargo.toml
│   ├── core
│   │   └── ...
│   ├── data
│   │   └── ...
│   ├── log
│   │   └── ...
│   ├── logs
│   │   └── ...
│   ├── manifest.json.example
│   ├── previews
│   │   └── ...
│   ├── README.md
│   ├── rx
│   │   └── ...
│   ├── tx
│   │   └── ...
│   └── udp_rx.py
├── sync_all.py
├── tap.py
├── tools
│   ├── create_data.py
│   ├── create_STA.py
│   ├── file_rx.py
│   ├── file_tx.py
│   ├── get_channel.py
│   ├── __init__.py
│   ├── ip_extract.py
│   ├── read_graph.py
│   ├── read_mcs.py
│   ├── read_rtt.py
│   └── set_route.py
├── util
│   ├── api
│   │   ├── __init__.py
│   │   └── ipc.py
│   ├── constHead.py
│   ├── ctl.py
│   ├── ifSense.py
│   ├── __init__.py
│   ├── logger.py
│   ├── predictor.py
│   ├── qos.py
│   ├── solver.py
│   ├── stream.py
│   └── trans_graph.py
└── warmup.py
```
项目架构图：

<img src="diagram.png" alt="Workflow Diagram" width="500">

## 2.  Requirements
+ 项目需要3.10及以上版本的python解释器。相关python依赖可以通过以下指令配置：
    ```bash
    pip3 install -r requirements.txt
    ```
+ 项目需要rust环境来编译构建`stream-replay` 工具。相关环境可以通过以下指令配置：
    ```bash
    curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
    ```

+ `stream-replay`是用来进行流量传输模拟的工具，在配置好rust环境后可以通过以下指令编译：
    ```bash
    cd stream-replay
    cargo build --release
    ```

## 3. `Monitor`端

### 3.1  功能
`monitor`端是实验的总控制端，主要功能包括：
- 对模拟传输实验进行总体调度，配置干扰流，数据流等参数
- 接收，存储回传来自`Solver`的统计数据并进行可视化处理(可选)

### 3.2  用法
为了便于说明，我们把两个设备之间的链路记作两个设备无线接口名的元组，例如 `('wlan0', 'wlan1')`, 这样的无线接口名可以通过在设备命令行输入 `iw dev` 来查看.

NOTICE: **以下操作应在项目根目录进行**.
1. 设置 `monitor` 监控端：
    ```bash
    python3 tap.py -s
    ```
    终端会列出所有连接的设备，此时可以对照具体设备配置进行连接检查

2. 设置自定义名称的用户设备，例如设置设备 `STA1`：
    ```bash
    python3 tap.py -c 192.168.3.72 -n STA1
    ```

3. 在config/topo下新建并编写`'{date}.txt'`文件来表示网络拓扑。每个链路占据一行，格式如下：
    ```text
    STA1 --wlan0-- --wlan1-- STA2
    ```
    其中`--wlan0-- --wlan1--`是STA1和STA2之间的链路，含义已在上面介绍

4. `monitor`端的基本配置已经完成，用户可以在`expSrc`下新建并编写实验代码`exp.py`，然后在`run_exp.py`中添加搜索路径即可。 最后，通过`python3 ./run_exp.py` 来开始实验。

5. `exp.py`是进行数据采集实验的脚本，主要流程为:
   - 根据topo文件加载网络拓扑结构
   - 配置业务流，干扰流的参数，包括数量，吞吐量，运行时间等
   - 创建传输流，对tx进行指令下发
   - 启动控制器(`Solver`端)
   - 启动通信进程(通过`start_comm_process`实现)，接收回传的统计数据以及结果文件
   - 分析数据并进行可视化处理(可选)
  
以下是一个简单的`exp.py`实验脚本的示例，用来根据topo文件构建链路并控制STA1向STA2发送文件数据流：
```python
import util.ctl as ctl
from tools.read_graph import construct_graph

## Create Link
topo, links = construct_graph("./config/topo/lo.txt")
ip_table    = ctl._ip_extract_all(topo)
ctl._ip_associate(topo, ip_table)

## Create Stream
temp  = stream.stream()
temp  = temp.read_from_manifest('./config/stream/file.json')
topo.ADD_STREAM(trans_manifest['link'], temp, validate = False)

## Start Transmission
conn  = ctl.start_transmission(graph = topo, DURATION = 100)
thrus = ctl.read_thu( conn )
print(thrus)
```

### *注意事项*
对于每次实验：
1. 自行配置当天的拓扑文件
2. 修改exp.py中的`date`变量，并在`exp.py`新建启动函数
3. 在`dpScript`按实验日期新建数据目录


## 4. `Solver`端

### 4.1  Function
Solver是使用rust编写的控制端程序，主要功能为：
- 收集与回传数据： 使用`qos_collect`接收受控设备回传的统计数据(例如`rtt,channel_rtt,tx_part`),简单处理格式后回传给监控端(`monitor`)
- 决策生成与控制：   根据接收到的统计数据以及决策算法进行决策(相关决策算法位于`./cores`目录)，生成action command,将控制命令发送给`受控设备`

### 4.2  Structure
目录 `/solver` 结构如下所示：
```bash
.
├── Cargo.lock
├── Cargo.toml
└── src
    ├── api
    │   ├── ipc.rs
    │   └── mod.rs
    ├── cores
    │   ├── back_switch_solver.rs
    │   ├── channel_balancer.rs
    │   ├── checker.rs
    │   ├── file_restrict.rs
    │   ├── forward_switch_solver.rs
    │   ├── green_solver.rs
    │   ├── mod.rs
    │   └── prediction.rs
    ├── lib.rs
    ├── tests
    │   ├── mod.rs
    │   ├── test_ipc.rs
    │   └── test_prediction.rs
    └── types
        ├── action.rs
        ├── mod.rs
        ├── parameter.rs
        ├── qos.rs
        ├── state.rs
        └── static_value.rs
```
solver可以通过以下指令编译：
```bash
cd ./solver
cargo build --release
```
### 4.3  Solver详解
以下来说明Solver各个子目录的功能：
+  `./api` ：子文件为`ipc.rs`，定义了负责和单个`受控设备`通信的结构体`ipc_controller`以及和多个`受控设备`通信的结构体`ipc_Manager`，包括了一系列收集数据、发送指令的方法
+ `./cores`：该目录定义了一系列根据统计数据生成动作的决策方法。主进程根据实时统计数据在`./cores`中进行不同的的算法选择。决策实现如下：
    | 文件   | 决策方法 |
    |------|------|
    | `back_switch_solver.rs` | `BackSwitchSolver` | 
    | `file_restrict.rs`| `FileSolver` | 
    |  `green_solver.rs`| `GSolver`  |
    | `prediction.rs` | `定义了一系列线性回归的方法，被以上三个方法调用` |
+ `./types`：该目录定义了一系列必要的数据结构和参数，其中，  `parameter.rs` 定义了`Solver`的超参数。
+ `./tests`：该目录定义了一系列测试用例，分别对ipc和线性回归函数进行测试。

#### Hyper Parameter
```Rust
pub struct HyperParameter<'a> {
    pub throttle_low: f64,
    pub throttle_high: f64,
    pub backward_threshold: f64,
    pub epsilon_rtt: f64,
    pub scale_factor: f64,
    pub degration_threshold: f64,
    pub degration_tx_part_threshold: f64,
    pub wait_slots: usize,
    pub maximum_his_len: usize,
    pub ports_tobe_pop: [&'a str; 3],
    pub running_duration: usize,
    pub ctl_time: usize,

    pub his_back_time: usize,
    pub back_off_rtt_threshold_factor: f64, // Threshold used to determine the reference backoff time  
    
    pub balance_channel_rtt_thres: f64,
    pub balance_time_thres: usize,
    pub balance_tx_part_thres: f64,
    pub balance_rtt_thres: f64,
}
```

+ `throttle_low` 和 `throttle_high` 分别是节流值`throttle`的下限和上限。
+ `backward_threshold` 是一个范围在 0 到 1 之间的阈值比例，用于确定信道是否可以开始切换回单信道模式。具体来说，更高的值意味着更激进的切换。
+ `epsilon_rtt` 是用于确定信道是否平衡的 RTT 差值的阈值。
+ `scale_factor` 是用于调整两个信道之间数据`tx_part`的缩放因子。
+ `degration_threshold` 是用于确定信道是否退化的 RTT 差值的阈值。
+ `degration_tx_part_threshold` 是用于确定信道是否退化的`tx_part`的阈值。
+ `wait_slots` 是在`Solver`开始调整`tx_part`之前需要等待的时隙数量。
+ `maximum_his_len` 是`Solver`历史记录的最大长度。
+ `ports_tobe_pop` 是待移除的端口，即这些端口不受控制。
+ `running_duration` 是`Solver`的运行时长。
+ `ctl_time` 是`Solver`开始控制的时间。
+ `his_back_time` 是用于确定信道是否曾经处于双信道模式的`Solver`历史的时间间隔。时间间隔越长，`Solver`从单信道模式切换到双信道模式就越保守。
+ `back_off_rtt_threshold_factor` 是用于确定参考回退时间的阈值，即该因子越低，回退越不可能发生。
+ `balance_channel_rtt_thres` 是 RTT 差值的最大阈值。如果信道的 RTT 大于此阈值，`Solver`将选择最大变化步长或决定执行基于线性拟合的控制。
+ `balance_time_thres` 是用于确定信道是否平衡的历史时间间隔。
+ `balance_tx_part_thres` 是`tx_part`的阈值。只有当`tx_part`大于此阈值时，这些历史记录才会用于基于线性拟合的控制。
+ `balance_rtt_thres` 是 RTT 差值的阈值。只有当 RTT 差值大于此阈值时，这些历史记录才会用于基于线性拟合的控制。

### 4.4  用法
`Solver`的运行状态高度依赖于以上的超参数集，超参数可以通过设置`HYPER_PARAMETER`。

使用这种方法启动控制器时必须指定以下命令行参数：
- `target-ips`:link_name(`tos@port`)到链路ipc地址(`ip:ipc_port`)的映射
- `name2ipc`：stream_name(`tos@port`)到link_name(`wlan_PC_phone`)的映射
- `base-info`:所有stream的配置信息
- `monitor-ip`：监控端的ip地址

`Solver`可以通过构建命令行字符串+`subprocess`启动，但是一般通过监控脚本`exp.py`调用`conn.batch()`的形式启动，如以下代码所示：

```python
import base64
from tap import Connector

conn=Connector()

conn.batch(control, "control-info", 
    {
        "target-ips" : base64.b64encode( json.dumps(target_ips).encode() ).decode(),
        "name2ipc" : base64.b64encode( json.dumps(name2ipc).encode() ).decode(),
        "base-info" : base64.b64encode( json.dumps(base_info).encode() ).decode(),
        "monitor-ip" : monitor_ip,
    }).wait(0.5).apply()
```


NOTICE：**Solver可以在监控设备所在子网内的任何设备上运行，命令行参数中，监控设备的 IP 地址`moniter-ip`应为监控设备无线网卡的 IP 地址，该地址对应的监控设备显示`Solver`结果的绘图。**

## 5.  Stream-Replay传输系统

### 简介
Stream-Replay是一个数据传输系统，包括tx端（数据发送端）和rx端（数据接收端），用于模拟真实网络环境下的wifi传输

### 5.1 Requirements

- [Rust toolchain](https://www.rust-lang.org/learn/get-started)

- Python3, numpy

### 5.2 特性

-  根据`*.npy`文件生成UDP stream.

- 可以通过改变`manifest.json` 文件参数实现改变stream的配置. 以下是一个`manifest.json`的示例：
```json
{
    "use_agg_socket": false,
    "orchestrator": "",
    "window_size": 1000,

    "streams":[
        {
            "type":"UDP",
            "npy_file": "data/temp.npy",
            "port": 12345,
            "duration": [0.0, 10.0],
            "tos": 0,
            "throttle": 0,
            "priority": "",
            "calc_rtt": true,
            "no_logging": false
        }
    ]
}
```

- 支持 IPC（进程间通信）以实现对网络的实时监控和控制。

### 5.3 用法

可以通过以下指令编译运行TX和RX端程序

**Tx:**
```bash
cargo run --bin stream-replay <manifest_file> <target_ip_address> <duration> [--ipc-port <IPC_PORT>]
```

**Rx:** 
```bash
cargo run --bin stream-replay-rx <port> <duration> [calc-rtt]
```

### 5.4  数据实时图


Stream-Replay系统对多个live stream进行IPC节流控制(throttle contorl)，并获得RTT数据反馈

![screenshot](screenshot.png)


## 6 `TX`端

### 6.1 简介
TX端是数据传输实验的发射端，功能包括：
- 向RX端传输数据
- 接受Solver端发来的tx_part,throttle调度
- 向Solver端回传平均rtt等统计数据

### 6.2 文件结构
- src/
  - statistic/
    - mod.rs
    - rtt_records.rs
  - broker.rs
  - conf.rs
  - dispatcher.rs
  - ipc.rs
  - lib.rs
  - link.rs
  - main.rs
  - rtt.rs
  - source.rs
  - throttle.rs
  - tx_part_ctl.rs
- Cargo.toml

### 6.3 主要文件介绍

#### `statistic/rtt_recoder.rs`
- 实现了RTT的记录与管理功能
- 结构
  - 定义了单条RTT记录结构`RTTEntry`以及管理多条`RTTEntry`的结构`RTTRecord`
- 函数
  - 实现了`statistic`方法用于计算当前设备的平均RTT及信道平均RTT等参数

#### `rtt.rs`
- 实现了RTT数据的记录与管理
- 结构
  - 定义了管理RTT测量记录的结构体`RttRecorder`，包含`rtt_records`、端口、服务名称，以及维护记录线程和接收线程
- 函数
  - 定义了线程函数`record_thread`，负责记录发送包的序列号
  - 定义了线程函数`pong_recv_thread`，负责接收ACK并计算RTT，将结果记录至`rtt_records`及日志文件

#### `conf.rs`
- 实现了发射流参数的配置管理
- 结构
  - 定义了单条流发射配置结构体`StreamParams`
  - 定义了管理`TX`端全局发射配置的结构体`Manifest`，该结构由所有`StreamParams`集合及其他配置参数组成
- 函数
  -实现了对配置合法性进行校验的方法`conf::validate` 

#### `dispatcher.rs`
- 实现了网络数据包的分发逻辑，为每个链路创建了数据发送通道
- 函数
  - 定义了分发器函数`dispatch()`，为多个网络链路创建UDPsocket，并通过`socket_thread()`为每条链路创建独立发送线程，返回将`tx_ipaddr`映射至发送通道(`flume::Sender<PacketStruct>`)的哈希表，并为数据发送socket设置了防阻塞机制

#### `link.rs`
- 实现了网络链路配置管理
- 结构
  - 定义了数据结构`Link`，存储tx端和rx端的IP地址，并实现其反序列化trait

#### `source.rs`
- 实现了流数据的管理与传输
- 结构
  - 定义了流管理器`SourceManager`
- 函数
  - 实现方法`start()`用于开始数据传输
  - 实现方法`set_tx_parts()`用于接受控制指令
  - 实现方法`Statistic()`用于收集统计数据
  - **以上三个方法用于响应`Solver`端的控制指令**
  - 定义了线程函数`stream_thread`，模拟实时数据发送（如投屏流）
  - 定义了线程函数`source_thread`，处理预定义静态数据发送（如文件流）
  - `SourceManager::start`根据`npy`文件协议头选择并启动相应线程

#### `ipc.rs`
- 实现了tx端的IPC通信机制
- 结构
  - 定义了IPC守护进程`IPCDaemon`，负责处理来自其他进程的请求并返回结果
- 函数
  - `handle_requests`方法接收请求并根据枚举类型处理，目前支持`Solver`的三类请求：throttle调节、tx_part调节、Statistics统计信息请求
  - `start_loop`方法启动IPC守护进程，监听`Solver`的请求

#### `main.rs`
- 实现了发送端主进程逻辑
- 结构
  - 定义了命令行参数结构体`ProgArgs`，封装TX端运行所需参数，包括`manifest`配置文件路径、IPC守护进程循环时间`duration`及监听端口`ipc_port`
- 函数
  - 定义了tx端的入口函数`main()`，该函数通过`ProgArgs`解析命令行参数并执行TX端流程：
    - 读取`manifest`清单，构造`StreamParam`列表并启动发射线程
    - 根据`duration`和`ipc_port`启动IPC守护进程，监听`Solver`请求

## 7 `RX`端

### 7.1 简介
RX端是数据传输实验的接收端，功能包括：
- 接收来自TX的数据包，并返回ACK
- 本地记录rtt和stuttering等统计数据 


### 7.2 文件结构

  - src/
    - statistic/
      - mod.rs
      - stuttering.rs
      - destination.rs
    - lib.rs
    - main.rs
    - record.rs
  - Cargo.toml

### 7.3 主要文件介绍

#### `stuttering.rs`
- 实现了ACK时间戳的记录以及抖动率的计算
- 结构
  - 定义了`Stutter`结构来维护所有ACK packet的发送时间戳
- 函数
  - 为`Stutter`实现了`update`方法来更新ACK时间戳,实现了`get_stuttering`方法来计算抖动率

#### `record.rs`
- 实现了数据包的记录，处理，以及接收状态的检查
- 结构
  - 定义了对单个数据包进行记录的结构`RecvRecord`以及对全局数据进行记录的结构`RecvData`，后者以seq号为索引存储必要的`RecvData`
- 函数
  - `RecvRecord::record`实现了对数据包(packet)进行记录
  - `RecvRecord::determine_complete`负责对各个链路传输状态（传输完成情况）进行评估
  - `RecvRecord::gather`实现了对离散的packet进行聚合

#### `destination.rs`
- 实现了数据包接收逻辑，包括：
  - 创建接受数据的udp socket，监听指定端口
  - 接收数据包并存储到`RecvData`中
  - 创建pong socket并发送ACK
  - 数据包完整时进行数据重组
- 结构
  - 定义了命令行参数结构体`Args`，包含了监听端口，持续时间等参数，用于设置接收线程`recv_thread`的工作状态
- 函数
  - 定义了接收线程函数`recv_thread`，实现了rx端的接收数据逻辑，用于持续接收数据包。通过调用`handle_rtt`记录并处理rtt数据，调用`send_ack`向数据源发送ACK确认

#### `main.rs`
`main`函数是rx端的入口函数，实现了以下流程：
- 从命令行中提取参数，包括监听端口以及休眠间隔
- 开启接收线程`destination::recv_thread`
- 计算并记录丢包率，抖动率等数据