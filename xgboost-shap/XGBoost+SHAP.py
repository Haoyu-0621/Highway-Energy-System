from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]

# Imports
import pandas as pd 
import numpy as np 
import matplotlib.pyplot as plt 
import os  
import warnings 
import re 
from statsmodels.nonparametric.smoothers_lowess import lowess 
import shap
from sklearn.model_selection import train_test_split, GridSearchCV 
from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error 
import matplotlib.colors as mcolors
import matplotlib.gridspec as gridspec
import seaborn as sns
from scipy.stats import gaussian_kde
import warnings
warnings.filterwarnings("ignore")

# User configuration, add your file and target column here 

csv_file_path = REPOSITORY_ROOT / "data" / "processed" / "your_shap_data.csv"
target_column_name = 'your_target' 
sheet_name = None
output_main_folder = r'./dependence_pictures' 
interactions_folder = r'./interactions_pictures'


# Data loading

plt.rcParams['font.serif'] = ['Times New Roman']
plt.rcParams['axes.unicode_minus'] = False

def sanitize_filename(name):
    return re.sub(r'[\\/*?:"<>|]', '_', name)
print("--- Loading data ---")
print(f"Loading data from '{csv_file_path}'...")
file_ext = os.path.splitext(csv_file_path)[1].lower()
if file_ext in ['.xls', '.xlsx']:
    excel_sheet = 0 if sheet_name is None else sheet_name
    df = pd.read_excel(csv_file_path, sheet_name=excel_sheet)
else:
    if sheet_name is not None:
        print("Warning: the input file is not an Excel file, so sheet_name will be ignored.")
    df = pd.read_csv(csv_file_path)

print("Data loaded successfully.")

if target_column_name not in df.columns:
    print(f"Error: target column '{target_column_name}' was not found in the dataset.")
    print(f"Available columns: {df.columns.tolist()}") 
    raise KeyError(f"Target column '{target_column_name}' was not found. Please check the configuration.")


# Features and target variable

y_original = df[target_column_name]
y_min = y_original.min()
offset = abs(y_min) + 1 if y_min <= 0 else 0 
y = np.log(y_original + offset)
X = df.drop(columns=[target_column_name,], errors='ignore')
feature_names = X.columns.tolist()

print("Data transformation completed.")
print(f"Target variable transformed to: log(y + {offset:.2f})")
print(f"Using {len(feature_names)} features for model training:\n{feature_names}")


# Non-numeric feature handling

print("Checking and processing non-numeric features...")
for col in X.columns: 
    if X[col].dtype == 'object':
        print(f"Feature '{col}' is non-numeric and will be processed.")
        X_converted = pd.to_numeric(X[col], errors='coerce')
        if X_converted.isnull().all():
            print(f"Feature '{col}' is a pure text categorical feature and will be factorized.") 
            X[col], _ = pd.factorize(X[col])
        else:
            X[col] = X_converted
            if X[col].isnull().sum() > 0:
                median_val = X[col].median() 
                print(f"Feature '{col}' contains partially invalid values and will be filled with the median ({median_val:.2f}).")
                X[col].fillna(median_val, inplace=True)
print("Data preprocessing completed.")


# Train-test split

print("\nSplitting the dataset into training and test sets...")
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
print(f"Training set: {X_train.shape[0]} samples")
print(f"Test set: {X_test.shape[0]} samples") 


# XGBoost training and evaluation
import xgboost as xgb 
from sklearn.model_selection import KFold

print("\nRunning hyperparameter search for the XGBoost model...")
param_grid = {
    'n_estimators': [1000],
    'learning_rate': [0.01],
    'max_depth': [4],
    'min_child_weight': [10],
    'subsample': [0.6],
    'colsample_bytree': [0.8], 
    'reg_lambda': [30],
    'reg_alpha': [0.1],
}

xgb_model = xgb.XGBRegressor(random_state=0, eval_metric='rmse')
cv = KFold(n_splits=5, shuffle=True, random_state=0)
grid_search = GridSearchCV(estimator=xgb_model, param_grid=param_grid, scoring='neg_mean_squared_error', cv=cv, n_jobs=-1, verbose=1) 

grid_search.fit(X_train, y_train) 
model = grid_search.best_estimator_ 

y_train_pred_log = model.predict(X_train)
y_test_pred_log = model.predict(X_test)

y_train_pred = np.exp(y_train_pred_log) - offset
y_test_pred = np.exp(y_test_pred_log) - offset

y_train_real = np.exp(y_train) - offset
y_test_real = np.exp(y_test) - offset

r2_train = r2_score(y_train_real, y_train_pred)
rmse_train = np.sqrt(mean_squared_error(y_train_real, y_train_pred))
mae_train = mean_absolute_error(y_train_real, y_train_pred)

r2_test = r2_score(y_test_real, y_test_pred)
rmse_test = np.sqrt(mean_squared_error(y_test_real, y_test_pred))
mae_test = mean_absolute_error(y_test_real, y_test_pred)

print("*"*100)
print(f"Best parameters: {grid_search.best_params_}")
print(f"Training metrics: R2={r2_train:.4f}, RMSE={rmse_train:.4f}, MAE={mae_train:.4f}")
print(f"Test metrics: R2={r2_test:.4f}, RMSE={rmse_test:.4f}, MAE={mae_test:.4f}")


feature_importances = model.feature_importances_
# Feature importance
importance_df = pd.DataFrame({'Feature': X.columns, 'Importance': feature_importances})
importance_df = importance_df.sort_values(by='Importance', ascending=False)
plt.figure(figsize=(12, 8))
colors = plt.cm.viridis(np.linspace(0.3, 1, len(importance_df)))
plt.barh(importance_df['Feature'], importance_df['Importance'], color=colors)
plt.xlabel('Characteristic importance')
plt.title('Visualization of the importance of XGBoost features')
plt.gca().invert_yaxis()
plt.xlim(0, importance_df['Importance'].max() + 0.1)
for index, value in enumerate(importance_df['Importance']):
    plt.text(value+0.03, index, f'{value:.4f}', va='center')
ax = plt.gca()
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
plt.show()


importance_df = pd.DataFrame({'Feature': X.columns, 'Importance': feature_importances})
importance_df = importance_df.sort_values(by='Importance', ascending=False)

# Ranked feature importance table
importance_df


# SHAP main effects

explainer = shap.Explainer(model)
shap_values_obj = explainer(X_test)
shap_values = shap_values_obj.values
base_value_log = float(np.asarray(explainer.expected_value).reshape(-1)[0])
mean_shap = np.abs(shap_values).mean(axis=0)
shap_df = pd.DataFrame({
    "feature": feature_names,
    "mean_shap": mean_shap
}).sort_values("mean_shap", ascending=False)
sorted_features = shap_df["feature"].values
X_test_sorted = X_test[sorted_features]
orig_index = [feature_names.index(f) for f in sorted_features]
shap_values_sorted = shap_values[:, orig_index]
print("SHAP main-effect values computed successfully.")
X_test_sorted


# SHAP beeswarm and bar-style summary plot

import math
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from matplotlib.cm import ScalarMappable
import matplotlib.ticker as ticker
import shap
import shap.plots.colors

# Plot style
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.sans-serif'] = ['Arial']
plt.rcParams['axes.unicode_minus'] = False

LABEL_FONT_SIZE = 14
TICK_FONT_SIZE = 12
AXIS_LINE_WIDTH = 1.5
FONT_WEIGHT = 'normal'

custom_colors_rgb = [
    (57, 81, 162),   # Deep Blue
    (114, 170, 207), # Light Blue
    (202, 232, 242), # Pale Blue
    (254, 251, 186), # Pale Yellow
    (253, 185, 107), # Orange
    (236, 93, 59),   # Red Orange
    (168, 3, 38)     # Deep Red
]
custom_colors_norm = [(r/255, g/255, b/255) for r, g, b in custom_colors_rgb]

custom_cmap = mcolors.LinearSegmentedColormap.from_list("custom_shap", custom_colors_norm)

# Convert SHAP values back to the original scale
def forward_scale(x):
    limit = 1.0  
    compression = 0.5 
    if x > limit:
        return limit + (x - limit) * compression
    elif x < -limit:
        return -limit + (x + limit) * compression
    return x


y_pred_log = base_value_log + shap_values.sum(axis=1)

shap_values_original = []
for i in range(shap_values.shape[1]):
    y_pred_minus_i_log = y_pred_log - shap_values[:, i]
    impact_original = np.exp(y_pred_log) - np.exp(y_pred_minus_i_log)
    shap_values_original.append(impact_original)

shap_values_original = np.array(shap_values_original).T
mean_abs_shap = np.abs(shap_values_original).mean(axis=0)

shap_series = pd.Series(mean_abs_shap, index=feature_names)
shap_series.sort_values(ascending=False, inplace=True)
sorted_features_list = shap_series.index.tolist()
sorted_shap_values_abs = shap_series.values

sort_indices = [list(feature_names).index(f) for f in sorted_features_list]
shap_values_sorted = shap_values_original[:, sort_indices]
X_test_sorted = X_test.iloc[:, sort_indices]

shap_values_mapped = np.vectorize(forward_scale)(shap_values_sorted)

# Figure layout
fig = plt.figure(figsize=(15, 9))

bottom_margin = 0.15 
plot_height = 0.75

left_plot_width = 0.36
center_width = 0.12
right_plot_width = 0.36
cbar_width = 0.015

ax_cbar_l_rect    = [0.02, bottom_margin, cbar_width, plot_height]
ax_left_rect      = [0.08, bottom_margin, left_plot_width, plot_height] 
ax_center_rect    = [0.08 + left_plot_width, bottom_margin, center_width, plot_height]
ax_right_rect     = [0.08 + left_plot_width + center_width, bottom_margin, right_plot_width, plot_height]
ax_cbar_r_rect    = [0.08 + left_plot_width + center_width + right_plot_width + 0.01, bottom_margin, cbar_width, plot_height]

ax_left   = fig.add_axes(ax_left_rect)
ax_center = fig.add_axes(ax_center_rect)
ax_right  = fig.add_axes(ax_right_rect)
ax_cbar_l = fig.add_axes(ax_cbar_l_rect)
ax_cbar_r = fig.add_axes(ax_cbar_r_rect)

# Left bar chart
color_norm = mcolors.Normalize(vmin=sorted_shap_values_abs.min(), vmax=sorted_shap_values_abs.max())
colors_mapped = custom_cmap(color_norm(sorted_shap_values_abs))

ax_left.barh(y=range(len(sorted_features_list)), width=sorted_shap_values_abs, color=colors_mapped, height=0.6)

ax_left.set_xlim(0, 0.7)
ax_left.invert_xaxis() 
ax_left.invert_yaxis()

ax_left.set_xlabel('Mean |SHAP| value (Million CNY)', size=LABEL_FONT_SIZE, fontweight=FONT_WEIGHT, labelpad=10)

ax_left.set_yticks([]) 
ax_left.grid(False)
ax_left.spines['left'].set_visible(False)
ax_left.spines['top'].set_visible(False)
ax_left.spines['right'].set_visible(True)
ax_left.spines['right'].set_linewidth(AXIS_LINE_WIDTH) 
ax_left.spines['right'].set_color('black')
ax_left.spines['bottom'].set_linewidth(AXIS_LINE_WIDTH)

ax_left.tick_params(axis='x', direction='out', labelsize=TICK_FONT_SIZE, width=AXIS_LINE_WIDTH, length=5)
for label in ax_left.get_xticklabels():
    label.set_fontweight(FONT_WEIGHT)

# Radial chart
inset_size = 0.5 
inset_left_pos = ax_left_rect[0] - 0.1 
inset_bottom_pos = ax_left_rect[1] - 0.02
ax_radial = fig.add_axes([inset_left_pos, inset_bottom_pos, inset_size, inset_size], projection='polar')
ax_radial.patch.set_alpha(0)

percentages = (sorted_shap_values_abs / sorted_shap_values_abs.sum()) * 100
widths = (sorted_shap_values_abs / sorted_shap_values_abs.sum()) * 2 * np.pi
num_vars = len(sorted_features_list)
base_length, fixed_increment, colored_ring_width = 3.0, 0.5, 2.0
total_lengths = [base_length + i * fixed_increment for i in range(num_vars)]
inner_heights = [max(0, tl - colored_ring_width) for tl in total_lengths]
inner_colors = (['#EAEAEA', '#FFFFFF'] * (num_vars // 2 + 1))[:num_vars]
one_oclock_offset = np.pi / 21
thetas = np.cumsum([0] + widths[:-1].tolist()) - one_oclock_offset

ax_radial.bar(x=thetas, height=inner_heights, width=widths, color=inner_colors, align='edge', edgecolor='white', linewidth=1.5)
ax_radial.bar(x=thetas, height=[colored_ring_width] * num_vars, width=widths, bottom=inner_heights, color=colors_mapped, align='edge', edgecolor='white', linewidth=1.5)

for i in range(min(num_vars, 10)): 
    label_angle_rad = thetas[i] + widths[i] / 2
    label_radius = total_lengths[i] + 0.5
    ax_radial.text(label_angle_rad, label_radius, f'{percentages[i]:.1f}%', ha='center', va='center', fontsize=8, fontweight=FONT_WEIGHT) 

ax_radial.set_theta_zero_location('N')
ax_radial.set_theta_direction(-1)      
ax_radial.axis('off')                  

# Left color bar
sm = ScalarMappable(cmap=custom_cmap, norm=color_norm)
cbar_l = fig.colorbar(sm, cax=ax_cbar_l, orientation='vertical')
cbar_l.set_ticks([])
cbar_l.outline.set_visible(False)

ax_cbar_l.text(0.5, 1.02, 'High', transform=ax_cbar_l.transAxes, ha='center', va='bottom', fontsize=TICK_FONT_SIZE, fontweight=FONT_WEIGHT)
ax_cbar_l.text(0.5, -0.02, 'Low', transform=ax_cbar_l.transAxes, ha='center', va='top', fontsize=TICK_FONT_SIZE, fontweight=FONT_WEIGHT)
ax_cbar_l.text(-2.0, 0.5, 'Contribution level', transform=ax_cbar_l.transAxes, fontsize=LABEL_FONT_SIZE, fontweight=FONT_WEIGHT, rotation=90, va='center')

# Center feature labels
ax_center.set_ylim(ax_left.get_ylim()) 
ax_center.axis('off') 


color_loads = custom_colors_norm[6]   
color_pv = custom_colors_norm[1]      
color_weather = custom_colors_norm[0] 
color_price = custom_colors_norm[5]   

label_colors = {
    "Building_Load": color_loads, "Charging_Load": color_loads, "Tunnel_Load": color_loads,
    "PV_Cap": color_pv,
    "GHI": color_weather, "CDD": color_weather, "HDD": color_weather,
    "Sell_Price": color_price, "Average_Price": color_price, "ΔPrice": color_price
}

for i, feature in enumerate(sorted_features_list):
    text_color = label_colors.get(feature.strip(), 'black')
    ax_center.text(0.5, i, feature, ha='center', va='center', 
                   fontsize=15, fontweight=FONT_WEIGHT, color=text_color, transform=ax_center.transData)

# Right beeswarm plot
expl_mapped = shap.Explanation(
    values=shap_values_mapped,
    data=X_test_sorted.values,
    feature_names=list(sorted_features_list),
    base_values=forward_scale(np.exp(base_value_log))
)

shap.plots.beeswarm(expl_mapped, max_display=len(sorted_features_list), ax=ax_right, show=False, plot_size=None, color_bar=False, color=custom_cmap)

logic_ticks = np.array([-3.0,-2.0,-1.0,-0.5,0,0.5,1.0, 2.0, 3.0,4.0,5.0, 6.0,7.0]) 
mapped_ticks = [forward_scale(t) for t in logic_ticks]

ax_right.set_xlim(forward_scale(-3.5), forward_scale(7.5))
ax_right.set_xticks(mapped_ticks)
ax_right.set_xticklabels([f"{t:.1f}" for t in logic_ticks])

ax_right.set_xlabel("SHAP Value: Impact on Cost (Million CNY)", size=LABEL_FONT_SIZE, fontweight=FONT_WEIGHT, labelpad=10)

ax_right.set_yticks([])
ax_right.set_yticklabels([])
ax_right.spines['left'].set_visible(False) 
ax_right.spines['top'].set_visible(False)
ax_right.spines['right'].set_visible(False)
ax_right.spines['bottom'].set_linewidth(AXIS_LINE_WIDTH)

ax_right.tick_params(axis='x', labelsize=TICK_FONT_SIZE, width=AXIS_LINE_WIDTH, length=5)
for label in ax_right.get_xticklabels():
    label.set_fontweight(FONT_WEIGHT)

ax_right.axvline(0, color='gray', linestyle='-', linewidth=0.5, alpha=0.5, zorder=-1)

# Right color bar
sm_right = plt.cm.ScalarMappable(cmap=custom_cmap, norm=plt.Normalize(vmin=0, vmax=1))
sm_right.set_array([])

cbar_r = fig.colorbar(sm_right, cax=ax_cbar_r)
cbar_r.set_ticks([])
cbar_r.outline.set_visible(False)

ax_cbar_r.text(0.5, 1.02, 'High', transform=ax_cbar_r.transAxes, ha='center', va='bottom', fontsize=TICK_FONT_SIZE, fontweight=FONT_WEIGHT)
ax_cbar_r.text(0.5, -0.02, 'Low', transform=ax_cbar_r.transAxes, ha='center', va='top', fontsize=TICK_FONT_SIZE, fontweight=FONT_WEIGHT)
ax_cbar_r.text(2.0, 0.5, 'Feature value', transform=ax_cbar_r.transAxes, fontsize=LABEL_FONT_SIZE, fontweight=FONT_WEIGHT, rotation=90, va='center')

# Save and display
plt.savefig('shap_butterfly_final_custom_color.png', dpi=300, bbox_inches='tight')
plt.show()


import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
import numpy as np

# SHAP dependence plots

plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.sans-serif'] = ['Arial']
plt.rcParams['axes.unicode_minus'] = False 

LABEL_FONT_SIZE = 14
TICK_FONT_SIZE = 12
AXIS_LINE_WIDTH = 1.5
FONT_WEIGHT = 'normal'

custom_colors_rgb = [
    (57, 81, 162),   # Deep Blue [0] - Weather
    (114, 170, 207), # Light Blue [1]
    (202, 232, 242), # Pale Blue [2]
    (254, 251, 186), # Pale Yellow [3]
    (253, 185, 107), # Orange [4] - PV
    (236, 93, 59),   # Red Orange [5] - Price
    (168, 3, 38)     # Deep Red [6] - Loads
]
custom_colors_norm = [(r/255, g/255, b/255) for r, g, b in custom_colors_rgb]

color_loads = custom_colors_norm[6]   # Deep Red
color_pv = custom_colors_norm[1]      # Pale Yellow
color_weather = custom_colors_norm[0] # Deep Blue
color_price = custom_colors_norm[5]   # Red Orange

label_colors = {
    "Building_Load": color_loads, "Charging_Load": color_loads, "Tunnel_Load": color_loads,
    "PV_Cap": color_pv,
    "GHI": color_weather, "CDD": color_weather, "HDD": color_weather,
    "Sell_Price": color_price, "Average_Price": color_price, "ΔPrice": color_price
}

base_value_log = float(np.asarray(explainer.expected_value).reshape(-1)[0])
shap_values_log = shap_values_obj.values

y_pred_log = base_value_log + shap_values_log.sum(axis=1)

shap_values_original_list = []
for i in range(shap_values_log.shape[1]):
    y_pred_minus_i_log = y_pred_log - shap_values_log[:, i]
    impact_original = np.exp(y_pred_log) - np.exp(y_pred_minus_i_log)
    shap_values_original_list.append(impact_original)

shap_values_original = np.array(shap_values_original_list).T
shap_values_df = pd.DataFrame(shap_values_original, columns=X_test.columns)

output_dir = 'shap_individual_plots_real_cost'
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

print("Generating SHAP dependence plots in the original cost space...")

for feature in X_test.columns:
    fig = plt.figure(figsize=(8, 6))
    ax = plt.gca()
    
    feature_color = label_colors.get(feature.strip(), 'black')
    
    plt.scatter(X_test[feature], shap_values_df[feature], 
                s=30,                
                color=feature_color,
                edgecolor=feature_color,
                alpha=0.6,          
                linewidth=0.8,      
                label='SHAP values')
    
    plt.axhline(y=0, color='gray', linestyle='-.', linewidth=1.5, alpha=0.8, label='SHAP = 0')
    
    ax.set_xlabel(feature, fontsize=LABEL_FONT_SIZE, fontweight=FONT_WEIGHT, labelpad=10)
    ax.set_ylabel('SHAP Value: Impact on Cost (Million CNY)', fontsize=LABEL_FONT_SIZE, fontweight=FONT_WEIGHT, labelpad=10)
    
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['bottom'].set_linewidth(AXIS_LINE_WIDTH)
    ax.spines['left'].set_linewidth(AXIS_LINE_WIDTH)
    
    ax.tick_params(axis='both', which='major', 
                   labelsize=TICK_FONT_SIZE, 
                   width=AXIS_LINE_WIDTH, 
                   length=6, 
                   direction='out')
    
    for label in ax.get_xticklabels() + ax.get_yticklabels():
        label.set_fontweight(FONT_WEIGHT)
        
    offset_x = ax.xaxis.get_offset_text()
    offset_x.set_fontweight(FONT_WEIGHT)
    offset_x.set_fontsize(TICK_FONT_SIZE)

    plt.tight_layout()
    
    safe_filename = "".join([c for c in feature if c.isalnum() or c in (' ', '_', '-')]).strip()
    save_path = os.path.join(output_dir, f'shap_real_{safe_filename}.png')
    plt.savefig(save_path, dpi=300)
    plt.close()

print(f"All dependence plots have been saved to: {output_dir}")
