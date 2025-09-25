use rand::prelude::*;
use rand::seq::SliceRandom;
use rand::thread_rng;
use rayon::prelude::*; // Rayon 库

/// 拉丁超立方采样
/// `param_ranges`: 参数范围，(low, high)
/// `n_samples`: 样本数量
/// `seed`: 随机种子，保证结果可复现
pub fn latin_hypercube_sampling(param_ranges: &[(f64, f64)], n_samples: usize, seed: u64) -> Vec<Vec<f64>> {
    let n_params = param_ranges.len();

    // 初始化存储每个参数的采样点
    let mut samples = vec![vec![0.0; n_params]; n_samples];

    let samples:Vec<Vec<f64>>=param_ranges.iter().enumerate().map(|(param_idx, &(low, high))| {
        //let mut rng = StdRng::seed_from_u64(seed+param_idx as u64); // 使用指定的随机种子
        //let mut rng=StdRng::seed_from_u64(seed);
        let mut rng=thread_rng();
        // 在 [0, 1] 范围内均匀分布采样点
        let mut intervals: Vec<f64> = (0..n_samples)
            .map(|i| (i as f64 + rng.clone().gen::<f64>()) / n_samples as f64)
            .collect();
        
        // 打乱顺序
        intervals.shuffle(&mut rng);

        // // 映射到实际范围
        // for (sample_idx, &point) in intervals.iter().enumerate() {
        //     samples[sample_idx][param_idx.clone()] = low + point * (high - low);
        // }

        intervals.into_iter().map(|point|low+point*(high-low)).collect::<Vec<f64>>()
    }).collect();

    transpose(samples)
}

/// 获取特定采样点的所有参数值
pub fn get_sample(samples: &[Vec<f64>], sample_index: usize) -> Option<&Vec<f64>> {
    samples.get(sample_index)
}

/// 获取特定采样点的特定维度参数值
pub fn get_sample_value(samples: &[Vec<f64>], sample_index: usize, param_index: usize) -> Option<f64> {
    samples.get(sample_index).and_then(|sample| sample.get(param_index).cloned())
}

fn test() {
    // 参数范围定义
    let param_ranges = vec![(0.0, 10.0), (1.0, 5.0), (0.1, 1.0), (50.0, 100.0)];
    let n_samples = 100; // 样本数量
    let seed = 42; // 随机种子

    // 拉丁超立方采样
    let samples = latin_hypercube_sampling(&param_ranges, n_samples, seed);

    // 获取第 10 个采样点的所有参数值
    if let Some(sample) = get_sample(&samples, 9) {
        println!("Sample 10: {:?}", sample);
    }

    // 获取第 10 个采样点的第 2 个参数值
    if let Some(value) = get_sample_value(&samples, 9, 1) {
        println!("Sample 10, Parameter 2: {}", value);
    }
}


// Sample 10: [5.5, 2.3, 0.85, 75.4]
// Sample 10, Parameter 2: 2.3

/// 转置二维数组
fn transpose(matrix: Vec<Vec<f64>>) -> Vec<Vec<f64>>
{
    if matrix.is_empty() {
        return vec![];
    }

    let n_rows = matrix.len();
    let n_cols = matrix[0].len();
    let a:f64=0 as f64;
    let mut transposed = vec![vec![a; n_rows]; n_cols];
    for i in 0..n_rows {
        for j in 0..n_cols {
            transposed[j][i] = matrix[i][j].clone();
        }
    }

    transposed
}