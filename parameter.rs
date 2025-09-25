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
    pub ports_tobe_pop: [&'a str; 6],
    pub running_duration: usize,
    pub ctl_time: usize,

    pub his_back_time: usize,
    pub back_off_rtt_threshold_factor: f64, // Threshold used to determine the reference backoff time  
    
    pub balance_channel_rtt_thres: f64,//determine maximum step size in tx_parts
    pub balance_time_thres: usize,
    pub balance_tx_part_thres: f64,
    pub balance_rtt_thres: f64,
}

pub(crate) static HYPER_PARAMETER: HyperParameter = {
    let throttle_high = 180.0;
    let throttle_low = throttle_high * 0.7;
    HyperParameter {
        throttle_low,
        throttle_high,
        backward_threshold: 0.8,
        epsilon_rtt: 0.002,
        scale_factor: 1.0,
        degration_threshold: 1.5,
        degration_tx_part_threshold: 0.8,
        wait_slots: 5,
        maximum_his_len: 10,
        ports_tobe_pop: ["6209@128", "6210@128", "6211@128","6219@128", "6220@128", "6221@128"],
        running_duration: 60,
        ctl_time: 0,

        his_back_time: 5,
        back_off_rtt_threshold_factor: 0.6,

        balance_channel_rtt_thres: 0.005,

        balance_time_thres: 3,
        balance_tx_part_thres: 0.5,
        balance_rtt_thres: 0.01,
    }
};
