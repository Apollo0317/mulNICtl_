import torch
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
import os
import json

# 复用你现有的训练代码组件
from train_expert_model import ExpertRegressor, load_and_process_data_v2, CONFIG, device

def plot_publication_cdf():
    print("=== Generating Publication-Quality CDF Plot ===")
    
    # 1. 加载测试集 (Test Set) —— 最终结果必须在未见过的测试集上跑
    # 注意：这里我们取 load_data 返回的第二组数据 (Test)
    _, X_test, _, y_test_scaled, _, scaler_y = load_and_process_data_v2('merged_data.csv')
    
    # 2. 加载模型
    model = ExpertRegressor(X_test.shape[1], CONFIG['hidden_dim'], CONFIG['dropout_rate']).to(device)
    checkpoint = torch.load(CONFIG['model_path'], map_location=device, weights_only=False)
    model.load_state_dict(checkpoint['model_state_dict'])
    model.eval()
    
    # 3. 加载校正因子 (Bias Correction Factor)
    # 如果没有这个文件，请先运行 evaluate_correction.py
    if os.path.exists("model_correction_config.json"):
        with open("model_correction_config.json", "r") as f:
            corr_config = json.load(f)
        factors = corr_config["correction_factors"]
        skewness = corr_config["skewness"]
        selected_method = corr_config["selected_method"]
        print(f"Loaded Correction Factors: Normal={factors['normal']:.4f}, Duan={factors['duan']:.4f}")
        print(f"Residual Skewness: {skewness:.2f}, Selected: {selected_method}")
    else:
        print("Warning: Correction config not found. Using factor = 1.0")
        factors = {"normal": 1.0, "duan": 1.0}
        selected_method = "None"

    # 4. 推理与校正
    X_tensor = torch.FloatTensor(X_test).to(device)
    with torch.no_grad():
        # A. 预测 Log 值
        pred_scaled = model(X_tensor).cpu().numpy().flatten()
        # B. 反标准化得到 Log 域预测
        pred_log = scaler_y.inverse_transform(pred_scaled.reshape(-1, 1)).flatten()
        
        # C. 为每种校正计算预测
        pred_ms_uncorrected = np.expm1(pred_log)
        pred_ms_uncorrected = np.maximum(pred_ms_uncorrected, 0)
        
        pred_ms_normal = np.exp(pred_log + factors["normal"]) - 1
        pred_ms_normal = np.maximum(pred_ms_normal, 0)
        
        pred_ms_duan = np.exp(pred_log) * factors["duan"] - 1
        pred_ms_duan = np.maximum(pred_ms_duan, 0)
    
    # 5. 获取真实值 (ms)
    # y_test_scaled -> inverse -> log -> expm1 -> ms
    y_true_log = scaler_y.inverse_transform(y_test_scaled.reshape(-1, 1)).flatten()
    y_true_ms = np.expm1(y_true_log)
    
    # 6. 计算绝对误差 (Absolute Error)
    errors_uncorrected = np.abs(y_true_ms - pred_ms_uncorrected)
    errors_normal = np.abs(y_true_ms - pred_ms_normal)
    errors_duan = np.abs(y_true_ms - pred_ms_duan)
    
    # ==========================================
    # 绘图部分 (Publication Style)
    # ==========================================
    # 设置Times New Roman字体 (如果没有安装，会自动回退)
    plt.style.use('seaborn-v0_8-paper')
    plt.rcParams.update({
        "font.family": "serif",
        "font.serif": ["Times New Roman", "DejaVu Serif"],
        "font.size": 12,
        "axes.labelsize": 12,
        "legend.fontsize": 11,
        "xtick.labelsize": 10,
        "ytick.labelsize": 10
    })

    fig, ax = plt.subplots(figsize=(6, 4.5))
    
    # 绘制 CDF 曲线
    # stat='proportion' 对应 0-1 的概率
    sns.ecdfplot(data=errors_uncorrected, ax=ax, linewidth=2.5, color='#2ca02c', label='Uncorrected')
    sns.ecdfplot(data=errors_normal, ax=ax, linewidth=2.5, color='#1f77b4', label='Normal Correction')
    sns.ecdfplot(data=errors_duan, ax=ax, linewidth=2.5, color='#ff7f0e', label="Duan's Correction")
    
    # --- 关键：标注 90% 分位数 ---
    # 计算 90% 的误差线是多少 ms
    p90_error_normal = np.percentile(errors_normal, 90)
    p90_error_duan = np.percentile(errors_duan, 90)
    
    # 画虚线 for selected method
    if selected_method == "Normal":
        ax.axvline(x=p90_error_normal, color='r', linestyle='--', alpha=0.6, linewidth=1.5)
        ax.axhline(y=0.9, color='r', linestyle='--', alpha=0.6, linewidth=1.5)
        ax.annotate(f'90% errors < {p90_error_normal:.1f} ms (Normal)', 
                    xy=(p90_error_normal, 0.9), 
                    xytext=(p90_error_normal + 10, 0.8),
                    arrowprops=dict(facecolor='black', shrink=0.05, width=1.5, headwidth=8),
                    fontsize=11, fontweight='bold', color='#333333')
    else:
        ax.axvline(x=p90_error_duan, color='r', linestyle='--', alpha=0.6, linewidth=1.5)
        ax.axhline(y=0.9, color='r', linestyle='--', alpha=0.6, linewidth=1.5)
        ax.annotate(f'90% errors < {p90_error_duan:.1f} ms (Duan)', 
                    xy=(p90_error_duan, 0.9), 
                    xytext=(p90_error_duan + 10, 0.8),
                    arrowprops=dict(facecolor='black', shrink=0.05, width=1.5, headwidth=8),
                    fontsize=11, fontweight='bold', color='#333333')

    # 添加 95% 文本（可选）
    p90_uncorrected = np.percentile(errors_uncorrected, 90)
    print(f"Stats (Uncorrected): 90% Error < {p90_uncorrected:.2f} ms, 95% < {np.percentile(errors_uncorrected, 95):.2f} ms")
    print(f"Stats (Normal): 90% Error < {p90_error_normal:.2f} ms, 95% < {np.percentile(errors_normal, 95):.2f} ms")
    print(f"Stats (Duan): 90% Error < {p90_error_duan:.2f} ms, 95% < {np.percentile(errors_duan, 95):.2f} ms")
    
    # 坐标轴美化
    ax.set_xlabel('Absolute Prediction Error (ms)', fontweight='bold')
    ax.set_ylabel('Cumulative Probability (CDF)', fontweight='bold')
    ax.set_title('Error Distribution on Test Set', pad=15)
    
    # 设置 x 轴范围，聚焦在 0-50ms 或者根据你的数据分布调整
    # 建议只展示到 99% 的点，切掉极端的 outliers 以保证图的可读性
    all_errors = np.concatenate([errors_uncorrected, errors_normal, errors_duan])
    xlim_max = np.percentile(all_errors, 98) * 1.2 
    ax.set_xlim(0, max(50, xlim_max)) 
    ax.set_ylim(0, 1.05)
    
    ax.grid(True, linestyle='--', alpha=0.4)
    ax.legend(loc='lower right')
    
    plt.tight_layout()
    save_path = os.path.join(CONFIG['save_dir'], 'cdf_error_distribution.pdf')
    plt.savefig(save_path, bbox_inches='tight', dpi=300)
    print(f"CDF Plot saved to: {save_path}")
    plt.show()


def calculate_and_save_correction_factor():
    print("=== 1. Loading Validation Data & Model ===")
    # 注意：我们只需要验证集数据来计算因子
    _, X_val, _, y_val_scaled, _, scaler_y = load_and_process_data_v2('merged_data.csv')
    
    # 加载模型
    model = ExpertRegressor(X_val.shape[1], CONFIG['hidden_dim'], CONFIG['dropout_rate']).to(device)
    checkpoint = torch.load(CONFIG['model_path'], weights_only=False)
    model.load_state_dict(checkpoint['model_state_dict'])
    model.eval()
    
    print("=== 2. Computing Residuals on Validation Set ===")
    val_tensor = torch.FloatTensor(X_val).to(device)
    
    with torch.no_grad():
        # 1. 预测 (Scaled Log Space)
        pred_scaled = model(val_tensor).cpu().numpy().flatten()
        
    # 2. 反标准化 -> Log Space
    y_log_pred = scaler_y.inverse_transform(pred_scaled.reshape(-1, 1)).flatten()
    y_log_true = scaler_y.inverse_transform(y_val_scaled.reshape(-1, 1)).flatten()
    
    # 3. 计算残差 (Residuals)
    residuals = y_log_true - y_log_pred
    
    print("=== 3. Calculating Correction Factors ===")
    # 方法 A: Normal Approximation (基于验证集方差)
    sigma_sq_val = np.var(residuals)
    factor_normal = np.exp(sigma_sq_val / 2)
    
    # 方法 B: Duan's Smearing (基于验证集残差的期望) -> 推荐
    factor_duan = np.mean(np.exp(residuals))
    
    print(f"Validation MSE (Sigma^2): {sigma_sq_val:.5f}")
    print(f"Correction Factor (Normal): {factor_normal:.5f}")
    print(f"Correction Factor (Duan's): {factor_duan:.5f}")
    
    # 计算偏度
    skewness = np.abs(np.mean((residuals - np.mean(residuals))**3) / np.std(residuals)**3)
    print(f"Residual Skewness: {skewness:.2f}")
    
    # 检查正态性决定用哪个
    if skewness < 0.5:
        selected_method = "Normal"
    else:
        selected_method = "Duan's Smearing"
        
    print(f"Selection: Using {selected_method} (Skewness={skewness:.2f})")
    
    # === 4. 保存因子 ===
    # 将因子作为一个配置保存，推理时直接读取乘上去
    correction_config = {
        "correction_factors": {
            "normal": float(factor_normal),
            "duan": float(factor_duan)
        },
        "skewness": float(skewness),
        "selected_method": selected_method,
        "source": "validation_set_residuals"
    }
    
    with open("model_correction_config.json", "w") as f:
        json.dump(correction_config, f, indent=4)
    print("-> Correction config saved to model_correction_config.json")


def plot_residual_diagnostics():
    print("=== Generating Residual Diagnostic Plots (Appendix) ===")
    
    # 1. 加载验证集数据 (Validation Set)
    # 诊断通常在验证集上做，用来确定校正策略
    _, X_val, _, y_val_scaled, _, scaler_y = load_and_process_data_v2('merged_data.csv')
    
    # 2. 加载模型
    model = ExpertRegressor(X_val.shape[1], CONFIG['hidden_dim'], CONFIG['dropout_rate']).to(device)
    checkpoint = torch.load(CONFIG['model_path'], map_location=device, weights_only=False)
    model.load_state_dict(checkpoint['model_state_dict'])
    model.eval()
    
    # 3. 计算残差 (Log Space)
    # 因为我们的假设是 Log-Normal，所以要在 Log 域检查正态性
    X_tensor = torch.FloatTensor(X_val).to(device)
    with torch.no_grad():
        pred_scaled = model(X_tensor).cpu().numpy().flatten()
        
    y_log_pred = scaler_y.inverse_transform(pred_scaled.reshape(-1, 1)).flatten()
    y_log_true = scaler_y.inverse_transform(y_val_scaled.reshape(-1, 1)).flatten()
    
    residuals = y_log_true - y_log_pred
    
    # 计算统计量
    mu, std = stats.norm.fit(residuals)
    skewness = stats.skew(residuals)
    kurtosis = stats.kurtosis(residuals)
    
    print(f"Residual Statistics: Mean={mu:.4f}, Std={std:.4f}, Skew={skewness:.4f}, Kurt={kurtosis:.4f}")

    # ==========================================
    # 绘图配置 (顶刊风格)
    # ==========================================
    plt.style.use('seaborn-v0_8-paper')
    plt.rcParams.update({
        "font.family": "serif",
        "font.serif": ["Times New Roman", "DejaVu Serif"],
        "font.size": 12,
        "axes.titlesize": 12,
        "axes.labelsize": 11
    })

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4.5))
    
    # --- 图 (a): 残差分布直方图 (Residual Histogram) ---
    # 绘制直方图和 KDE 曲线
    sns.histplot(residuals, bins=50, kde=True, stat="density", 
                 color='#1f77b4', edgecolor='white', alpha=0.6, ax=ax1, label='Residuals')
    
    # 绘制理想正态分布曲线 (红线)
    xmin, xmax = ax1.get_xlim()
    x = np.linspace(xmin, xmax, 100)
    p = stats.norm.pdf(x, mu, std)
    ax1.plot(x, p, 'r--', linewidth=2, label='Normal Fit')
    
    ax1.set_title('(a) Residual Distribution')
    ax1.set_xlabel('Log-Error Residuals')
    ax1.set_ylabel('Density')
    ax1.legend()
    ax1.grid(True, linestyle='--', alpha=0.3)
    
    # 添加统计文本框
    stats_text = f"Skewness = {skewness:.2f}\nKurtosis = {kurtosis:.2f}"
    props = dict(boxstyle='round', facecolor='white', alpha=0.9)
    ax1.text(0.05, 0.95, stats_text, transform=ax1.transAxes, verticalalignment='top', bbox=props)

    # --- 图 (b): Q-Q Plot (Quantile-Quantile Plot) ---
    # 这是检验正态性的金标准
    # 如果点都在红线上，就是正态分布；如果两头翘起，说明是长尾
    stats.probplot(residuals, dist="norm", plot=ax2)
    
    # 美化 Q-Q Plot
    ax2.get_lines()[0].set_markerfacecolor('#1f77b4') # 点的颜色
    ax2.get_lines()[0].set_markeredgecolor('none')
    ax2.get_lines()[0].set_alpha(0.6)
    ax2.get_lines()[0].set_markersize(4.0)
    
    ax2.get_lines()[1].set_color('r') # 线的颜色
    ax2.get_lines()[1].set_linewidth(2.0)
    
    ax2.set_title('(b) Q-Q Plot')
    ax2.set_xlabel('Theoretical Quantiles')
    ax2.set_ylabel('Ordered Residuals')
    ax2.grid(True, linestyle='--', alpha=0.3)

    plt.tight_layout()
    
    # 保存图片
    save_path = os.path.join(CONFIG['save_dir'], 'residual_diagnostics.pdf')
    plt.savefig(save_path, bbox_inches='tight', dpi=300)
    print(f"Diagnostic plot saved to: {save_path}")
    plt.show()

if __name__ == "__main__":
    calculate_and_save_correction_factor()
    plot_residual_diagnostics()
    plot_publication_cdf()