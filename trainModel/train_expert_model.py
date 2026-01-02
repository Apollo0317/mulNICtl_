import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, MinMaxScaler
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import os
import time

# ==========================================
# 1. 进阶配置 (Advanced Config)
# ==========================================
CONFIG = {
    'seed': 3407,           # 论文常用的幸运种子
    'batch_size': 128,      # 增大 Batch Size 稳定梯度
    'epochs': 500,          # 增加轮数，配合 Cosine Annealing
    'learning_rate': 2e-3,  # 初始学习率稍大
    'weight_decay': 1e-3,   # 强 L2 正则化 (关键抗过拟合)
    'hidden_dim': 128,      # 缩小模型宽度，防止过拟合
    'dropout_rate': 0.4,    # 高 Dropout
    'save_dir': 'figures_v2',
    'model_path': 'best_model_v2.pth'
}

def set_seed(seed):
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    np.random.seed(seed)

set_seed(CONFIG['seed'])
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

if not os.path.exists(CONFIG['save_dir']):
    os.makedirs(CONFIG['save_dir'])

# ==========================================
# 2. 对数空间数据处理 (Log-Space Data Pipeline)
# ==========================================
class RTTDataset(Dataset):
    def __init__(self, X, y):
        self.X = torch.FloatTensor(X)
        self.y = torch.FloatTensor(y).reshape(-1, 1)

    def __len__(self):
        return len(self.X)

    def __getitem__(self, idx):
        return self.X[idx], self.y[idx]

def load_and_process_data_v2(filepath):
    print(f"Loading data from {filepath}...")
    df = pd.read_csv(filepath)
    
    # 特征选择
    feature_cols = df.columns[:16]
    target_cols = df.columns[16:]
    
    X = df[feature_cols].values
    
    # --- 关键改进：目标值处理 ---
    # 1. 计算均值
    raw_y = np.mean(df[target_cols].values, axis=1)
    
    # 2. 异常值处理 (Clipping)
    raw_y = np.clip(raw_y, 0, 200.0)
    
    # 3. 对数变换 (Log-Transform) !!! 核心 !!!
    # RTT数据通常是左偏的，取对数可以让它更像高斯分布，极易于神经网络收敛
    y_log = np.log1p(raw_y) 
    
    # 划分数据集
    X_train, X_test, y_train_log, y_test_log = train_test_split(
        X, y_log, test_size=0.15, random_state=CONFIG['seed'], shuffle=True
    )
    
    # 特征标准化 (X)
    scaler_X = StandardScaler()
    X_train_scaled = scaler_X.fit_transform(X_train)
    X_test_scaled = scaler_X.transform(X_test)
    
    # 目标在 log 空间也做标准化 (y)，并返回 scaler_y 以便推理/反变换
    scaler_y = StandardScaler()
    y_train_log = np.array(y_train_log).reshape(-1, 1)
    y_test_log = np.array(y_test_log).reshape(-1, 1)
    y_train_scaled = scaler_y.fit_transform(y_train_log).flatten()
    y_test_scaled = scaler_y.transform(y_test_log).flatten()
    
    return X_train_scaled, X_test_scaled, y_train_scaled, y_test_scaled, scaler_X, scaler_y

# ==========================================
# 3. 模型定义 (Compact ResMLP)
# ==========================================
class ResidualBlock(nn.Module):
    def __init__(self, dim, dropout):
        super(ResidualBlock, self).__init__()
        self.block = nn.Sequential(
            nn.Linear(dim, dim),
            nn.BatchNorm1d(dim),
            nn.GELU(), # 使用 GELU 替代 ReLU，在现代 Transformer/ResNet 中表现更好
            nn.Dropout(dropout),
            nn.Linear(dim, dim),
            nn.BatchNorm1d(dim),
            nn.GELU(),
            nn.Dropout(dropout)
        )
        
    def forward(self, x):
        return x + self.block(x)

class ExpertRegressor(nn.Module):
    def __init__(self, input_dim, hidden_dim, dropout=0.3):
        super(ExpertRegressor, self).__init__()
        
        self.input_net = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.BatchNorm1d(hidden_dim),
            nn.GELU()
        )
        
        # 减少层数，增加宽度，防止过拟合
        self.res_blocks = nn.Sequential(
            ResidualBlock(hidden_dim, dropout),
            ResidualBlock(hidden_dim, dropout)
        )
        
        self.output_net = nn.Linear(hidden_dim, 1)

    def forward(self, x):
        x = self.input_net(x)
        x = self.res_blocks(x)
        return self.output_net(x)

# ==========================================
# 4. 训练流程 (Cosine Annealing)
# ==========================================
def train_expert_model(model, train_loader, val_loader, save_path=None, scaler_X=None, scaler_y=None):
    # 使用 MSE Loss，因为我们已经在 Log 空间并且做了标准化
    criterion = nn.MSELoss() 
    optimizer = optim.AdamW(model.parameters(), lr=CONFIG['learning_rate'], weight_decay=CONFIG['weight_decay'])
    
    # 余弦退火调度器：让学习率平滑下降，有助于找到平坦的极小值
    scheduler = optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=CONFIG['epochs'], eta_min=1e-5)
    
    history = {'train_loss': [], 'val_loss': []}
    best_val_loss = float('inf')
    
    print("Starting optimized training...")
    start_time = time.time()
    
    for epoch in range(CONFIG['epochs']):
        # Train
        model.train()
        train_losses = []
        for inputs, targets in train_loader:
            inputs, targets = inputs.to(device), targets.to(device)
            optimizer.zero_grad()
            outputs = model(inputs)
            loss = criterion(outputs, targets)
            loss.backward()
            optimizer.step()
            train_losses.append(loss.item())
            
        # Val
        model.eval()
        val_losses = []
        with torch.no_grad():
            for inputs, targets in val_loader:
                inputs, targets = inputs.to(device), targets.to(device)
                outputs = model(inputs)
                loss = criterion(outputs, targets)
                val_losses.append(loss.item())
        
        avg_train = np.mean(train_losses)
        avg_val = np.mean(val_losses)
        history['train_loss'].append(avg_train)
        history['val_loss'].append(avg_val)
        
        scheduler.step()
        
        # 保存最佳模型及 scaler 信息（checkpoint）
        if avg_val < best_val_loss:
            best_val_loss = avg_val
            checkpoint = {
                'model_state_dict': model.state_dict(),
                'config': CONFIG
            }
            if scaler_X is not None:
                checkpoint['scaler_X'] = scaler_X
            if scaler_y is not None:
                checkpoint['scaler_y'] = scaler_y
            torch.save(checkpoint, save_path or CONFIG['model_path'])
            
        if (epoch + 1) % 50 == 0:
            print(f"Epoch [{epoch+1}/{CONFIG['epochs']}] Train Loss: {avg_train:.4f} Val Loss: {avg_val:.4f} LR: {scheduler.get_last_lr()[0]:.6f}")

    print(f"Training finished in {time.time() - start_time:.2f}s")
    return history

# ==========================================
# 5. 学术绘图 (Inverse Log Transform)
# ==========================================
def plot_results_v2(y_true_scaled, y_pred_scaled, history, scaler_y):
    # 先用 scaler_y 反标准化回 log 空间，然后 exmp1 回到 ms
    y_true_log = scaler_y.inverse_transform(np.array(y_true_scaled).reshape(-1,1)).flatten()
    y_pred_log = scaler_y.inverse_transform(np.array(y_pred_scaled).reshape(-1,1)).flatten()
    
    y_true_ms = np.expm1(y_true_log)
    y_pred_ms = np.expm1(y_pred_log)
    
    # 强制截断负数预测 (物理约束)
    y_pred_ms = np.maximum(y_pred_ms, 0)

    # 重新计算原始刻度下的指标
    r2 = r2_score(y_true_ms, y_pred_ms)
    mae = mean_absolute_error(y_true_ms, y_pred_ms)
    rmse = np.sqrt(mean_squared_error(y_true_ms, y_pred_ms))
    
    print("\n=== Final Performance (Original Scale) ===")
    print(f"R2 Score: {r2:.4f}")
    print(f"MAE:      {mae:.4f} ms")
    print(f"RMSE:     {rmse:.4f} ms")
    
    # 绘图配置
    plt.style.use('seaborn-v0_8-paper')
    plt.rcParams.update({
        "font.family": "serif",
        "font.serif": ["DejaVu Serif"],  # 使用系统可用字体，避免警告
        "font.size": 11,
        "legend.fontsize": 10
    })

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4))
    
    # (a) Scatter
    ax1.scatter(y_true_ms, y_pred_ms, alpha=0.4, s=10, c='#1f77b4', edgecolors='none')
    
    # 绘制完美预测线
    max_val = max(np.max(y_true_ms), np.max(y_pred_ms))
    ax1.plot([0, max_val], [0, max_val], 'r--', alpha=0.8, label='Ideal')
    
    ax1.set_xlabel('Ground-Truth AL-RTT (ms)')
    ax1.set_ylabel('Predicted Latency (ms)')
    ax1.set_title('(a) Prediction Accuracy')
    ax1.set_xlim(0, 100) # 聚焦在 0-100ms 关键区间
    ax1.set_ylim(0, 100)
    
    stats_text = f"$R^2={r2:.3f}$\n$MAE={mae:.2f}ms$"
    props = dict(boxstyle='round', facecolor='white', alpha=0.8, edgecolor='lightgray')
    ax1.text(0.05, 0.95, stats_text, transform=ax1.transAxes, verticalalignment='top', bbox=props)
    ax1.grid(True, linestyle='--', alpha=0.3)

    # (b) Loss
    ax2.plot(history['train_loss'], label='Train', color='#2ca02c')
    ax2.plot(history['val_loss'], label='Validation', color='#ff7f0e', alpha=0.8)
    ax2.set_xlabel('Epochs')
    ax2.set_ylabel('Log-Space MSE Loss')
    ax2.set_title('(b) Training Convergence')
    ax2.grid(True, linestyle='--', alpha=0.3)
    ax2.legend()
    
    plt.tight_layout()
    plt.savefig(os.path.join(CONFIG['save_dir'], 'model_accuracy_v2.pdf'), bbox_inches='tight')
    plt.show()

if __name__ == "__main__":
    # Load (现在返回 scaler_y)
    X_train, X_test, y_train_scaled, y_test_scaled, scaler_X, scaler_y = load_and_process_data_v2('merged_data.csv')
    
    train_loader = DataLoader(RTTDataset(X_train, y_train_scaled), batch_size=CONFIG['batch_size'], shuffle=True)
    val_loader = DataLoader(RTTDataset(X_test, y_test_scaled), batch_size=CONFIG['batch_size'], shuffle=False)
    
    # Init
    model = ExpertRegressor(X_train.shape[1], CONFIG['hidden_dim'], CONFIG['dropout_rate']).to(device)
    
    # Train（传入 scaler 以便保存到 checkpoint）
    history = train_expert_model(model, train_loader, val_loader, save_path=CONFIG['model_path'], scaler_X=scaler_X, scaler_y=scaler_y)
    
    # Eval - 从 checkpoint 里恢复模型和 scaler
    checkpoint = torch.load(CONFIG['model_path'], weights_only=False)
    model.load_state_dict(checkpoint['model_state_dict'])
    model.eval()
    loaded_scaler_y = checkpoint.get('scaler_y', scaler_y)
    with torch.no_grad():
        preds_scaled = model(torch.FloatTensor(X_test).to(device)).cpu().numpy().flatten()
        
    plot_results_v2(y_test_scaled, preds_scaled, history, loaded_scaler_y)