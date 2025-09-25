# Base
In the `./base` the folder structure follows 
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
## Requirements
+ Python 3.10 (Verified) or later is required to run the code. The required packages can be installed by running
    ```bash
    pip3 install -r requirements.txt
    ```
+ Rust is required to compile the `stream-replay` tool. The installation can be done by running
    ```bash
    curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
    ```

+ The `stream-replay` tool is used to replay the network traffic. The tool can be compiled by running
    ```bash
    cd ./base/stream-replay
    cargo build --release
    ```

## How to Use
For elaboration convenience, we define a link as tuple of wireless interface name, e.g. `('wlan0', 'wlan1')`, where the first element is the interface name of the transmitter and the second element is the interface name receiver. Such interface name can be obtained by running `iw dev` in the terminal.

NOTICE: Bellowing setup procedure all starts from the root directory of provided code.
1. Setup monitor, assume the ip of monitor wireless interface is `192.168.3.72`
    ```
    cd ./base
    python3 tap.py -s
    ```
2. Setup controlled user equipment with given name, e.g. `STA1`
    ```
    cd ./base
    python3 tap.py -c 192.168.3.72 -n STA1
    ```
3. Setup link configuration based to the file `./base/config/topo/` in format like `STA1 --wlan0-- --wlan1-- STA2`, where `--wlan0--` and `--wlan1--` are the link between `STA1` and `STA2`.

4. The basic setup is then finished, the user can run `cd ./base; python3 ./run_exp.py` to start the experiment.

As a simple example, a single script can be run to transmit a file stream from `STA1` to `STA2`:
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

# Solver

## 功能
Solver是使用rust编写的控制端程序，主要功能为：
- 接收rx端发送的

## 结构
目录 `/solver` 结构如下 
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
## Solver详解
Solver是使用rust编写的传输控制器
+ In the folder `./api` the necessary control socket handler is defined.
+ In the folder `./cores` the core algorithm of the solver is implemented.
+ In the folder `./types` the necessary data structure is defined, specifically the `parameter.rs` defines the hyper parameter of the solver.
+ In the folder `./tests` the test cases of the solver is defined.

### Hyper Parameter
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
+ `throttle_low` and `throttle_high` are the lower and upper bound of the throttle value.
+ `backward_threshold` is the threshold fraction, ranged from 0 to 1, to determine whether the channel can start return to single channel. Specifically, higher value means more aggressive switch.
+ `epsilon_rtt` is the threshold of the RTT difference to determine whether the channel is balanced.
+ `scale_factor` is the factor to scale the adjustment of data transmission fraction between two channels.
+ `degration_threshold` is the threshold of the RTT difference to determine whether the channel is degraded.
+ `degration_tx_part_threshold` is the threshold of the transmission fraction to determine whether the channel is degraded.
+ `wait_slots` is the number of slots to wait before the solver starts to adjust the transmission fraction.
+ `maximum_his_len` is the maximum length of the history of the solver.
+ `ports_tobe_pop` is the ports to be popped, that is, port is not controlled.
+ `running_duration` is the duration of the solver.
+ `ctl_time` is the start control time of the solver.
+ `his_back_time` is the time interval of the history of the solver to determine whether the channel is ever in dual channel mode. The longer the time interval, the more conservative the solver to try to change the channel into dual channel mode from single channel mode.
+ `back_off_rtt_threshold_factor` is the threshold used to determine the reference backoff time, that is the lower factor, the backoff is less likely to happen.
+ `balance_channel_rtt_thres` is the maximum threshold of the RTT difference. If the channel rtt is larger than this threshold, the solver will either choose a maximum change step or decide to do line-fitted-based control.
+ `balance_time_thres` is the history interval used to determine whether the channel is balanced.
+ `balance_tx_part_thres` is the threshold of the transmission fraction. Only the transmission fraction is larger than this threshold, these history will be used in the line-fitted-based control.
+ `balance_rtt_thres` is the threshold of the RTT difference. Only the RTT difference is larger than this threshold, these history will be used in the line-fitted-based control.

## How to Use
The running of solver is highly dependent on the transmission configuration in above section. 

Particularly, the solver command should be generated by following code after the transmission configuration is set up, that is, before the running of `conn  = ctl.start_transmission(graph = topo, DURATION = 100)
thrus = ctl.read_thu( conn )` in above section.
```python
import base64
target_ips, name2ipc = ctl.ipcManager.prepare_ipc(topo)
base_info = ctl.graph_qos_collections(topo)
## Ip addr of the monitor
monitor_ip = "10.16.60.57:6405"
print(f"cargo run -- --target-ips={base64.b64encode( json.dumps(target_ips).encode() ).decode()} --name2ipc={base64.b64encode( json.dumps(name2ipc).encode() ).decode()} --base-info={base64.b64encode( json.dumps(base_info).encode() ).decode()} --monitor-ip {monitor_ip}")
```

Given the solver command, the solver can be run by
```bash
cargo run -- --target-ips=... --name2ipc=... --base-info=... --monitor-ip ...
```

NOTICE: the above command can be run in any device within the same subnet of the monitor, and the monitor ip should be the ip of the monitor wireless interface, where the plotting of the solver result is shown.