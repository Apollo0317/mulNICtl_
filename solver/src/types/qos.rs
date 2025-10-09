use serde::{Deserialize, Serialize};

use crate::api::ipc::Statistics;

use super::static_value::StaticValue;

type Link = (String, String);

#[derive(Deserialize, Clone, Debug, Serialize)]
pub struct Qos {
    pub rtt: Option<f64>,
    pub channel_rtts: Option<Vec<f64>>,
    pub outage_rate : Option<f64>,
    pub ch_outage_rates: Option<Vec<f64>>,
    pub tx_parts: Vec<f64>,
    pub channel_probabilities:Option<Vec<f64>>,
    pub target_rtt: f64,
    pub links : Vec<Link>,
    pub channels: Vec<String>,
    pub throttle: f64,
    pub throughput: f64,
    pub rssi_wifi: Option<i64>,
    pub link_speed: Option<i64>,
    pub rssi_p2p: Option<i64>,
}

impl From<(&Statistics, &StaticValue)> for Qos {
    fn from((stats, static_value): (&Statistics, &StaticValue)) -> Self {
        Qos {
            rtt: stats.rtt,
            channel_rtts: stats.channel_rtts.clone(),
            outage_rate: stats.outage_rate,
            ch_outage_rates: stats.ch_outage_rates.clone(),
            tx_parts: stats.tx_parts.clone(),
            channel_probabilities: None, // Assuming channel probabilities need to be calculated separately
            target_rtt: static_value.target_rtt,
            links: static_value.links.clone(),
            channels: static_value.channels.clone(),
            throttle: stats.throttle,
            throughput: stats.throughput,
            rssi_wifi: Some(stats.rssi_wifi),
            link_speed: Some(stats.link_speed),
            rssi_p2p: Some(stats.rssi_p2p),
        }
    }
}

impl Qos{
    pub fn is_single_channel(&self) -> bool {
        self.tx_parts.iter().all(|&x| x == 1.0 || x == 0.0)
    }
}