import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pykalman import KalmanFilter

# Load PMU data from the file
file_path = '/home/jtnorris/Desktop/ecasto/p4-digests-logging/src/pmu_logging/pmu12.csv'
pmu_data = pd.read_csv(file_path, delimiter=',')

# Extract voltage magnitudes and angles
voltage_magnitudes = pmu_data[['Magnitude01', 'Magnitude02', 'Magnitude03']].values
voltage_angles = pmu_data[['Angle01', 'Angle02', 'Angle03']].values

# Create measurement vector z
z = np.hstack([voltage_magnitudes, voltage_angles])

# Define measurement model H and weight matrix W
H = np.identity(z.shape[1])
W = np.identity(z.shape[1])

# Perform Weighted Least Squares estimation
x_hat = np.linalg.inv(H.T @ W @ H) @ H.T @ W @ z.T
x_hat = x_hat.T  # Transpose for easier handling

# Separate estimated magnitudes and angles
estimated_magnitudes = x_hat[:, :3]
estimated_angles = x_hat[:, 3:]

# Calculate statistical properties
mean_magnitudes = np.mean(estimated_magnitudes, axis=0)
std_magnitudes = np.std(estimated_magnitudes, axis=0)

mean_angles = np.mean(estimated_angles, axis=0)
std_angles = np.std(estimated_angles, axis=0)

# Print results
print("Mean Estimated Magnitudes:", mean_magnitudes)
print("Standard Deviation of Estimated Magnitudes:", std_magnitudes)

print("Mean Estimated Angles:", mean_angles)
print("Standard Deviation of Estimated Angles:", std_angles)

# Plot voltage magnitudes over time
time_steps = np.arange(estimated_magnitudes.shape[0])

plt.figure(figsize=(12, 6))
for i in range(3):
    plt.plot(time_steps, estimated_magnitudes[:, i], label=f'Bus {i+1} Magnitude')
plt.xlabel('Time Step')
plt.ylabel('Voltage Magnitude')
plt.title('Estimated Voltage Magnitudes Over Time')
plt.legend()
plt.grid(True)
plt.show()

# Plot voltage angles over time
plt.figure(figsize=(12, 6))
for i in range(3):
    plt.plot(time_steps, estimated_angles[:, i], label=f'Bus {i+1} Angle')
plt.xlabel('Time Step')
plt.ylabel('Voltage Angle (Degrees)')
plt.title('Estimated Voltage Angles Over Time')
plt.legend()
plt.grid(True)
plt.show()

# Define true state vector for validation (replace with actual true values if available)
x_true = np.array([
    [253500, 260000, 255500, -10, -130, 105]
] * estimated_magnitudes.shape[0])  # Repeat for all time steps

# Calculate estimation errors
errors = x_true - x_hat

# Calculate error metrics
mae = np.mean(np.abs(errors), axis=0)
rmse = np.sqrt(np.mean(errors**2, axis=0))

print("Mean Absolute Error (MAE):", mae)
print("Root Mean Squared Error (RMSE):", rmse)

# Add noise to measurements
magnitude_noise_std = 1000  # Adjust standard deviation as needed
angle_noise_std = 1  # Degrees

noisy_magnitudes = voltage_magnitudes + np.random.normal(0, magnitude_noise_std, voltage_magnitudes.shape)
noisy_angles = voltage_angles + np.random.normal(0, angle_noise_std, voltage_angles.shape)

# Create noisy measurement vector
z_noisy = np.hstack([noisy_magnitudes, noisy_angles])

# Perform state estimation with noisy measurements
x_hat_noisy = np.linalg.inv(H.T @ W @ H) @ H.T @ W @ z_noisy.T
x_hat_noisy = x_hat_noisy.T

# Calculate errors with noisy data
errors_noisy = x_true - x_hat_noisy
rmse_noisy = np.sqrt(np.mean(errors_noisy**2, axis=0))

print("RMSE with Noisy Measurements:", rmse_noisy)

# Define a more complex H matrix for a 3-bus system (example)
H = np.array([
    [1, 0, 0, 0, 0, 0],  # Voltage magnitude at Bus 1
    [0, 1, 0, 0, 0, 0],  # Voltage magnitude at Bus 2
    [0, 0, 1, 0, 0, 0],  # Voltage magnitude at Bus 3
    [0, 0, 0, 1, 0, 0],  # Voltage angle at Bus 1
    [0, 0, 0, 0, 1, 0],  # Voltage angle at Bus 2
    [0, 0, 0, 0, 0, 1],  # Voltage angle at Bus 3
    # Additional rows for power flow measurements can be added here
])

W = np.identity(H.shape[0])

x_hat_improved = np.linalg.inv(H.T @ W @ H) @ H.T @ W @ z_noisy.T
x_hat_improved = x_hat_improved.T

# Evaluate performance
errors_improved = x_true - x_hat_improved
rmse_improved = np.sqrt(np.mean(errors_improved**2, axis=0))

print("RMSE with Improved Measurement Model:", rmse_improved)

# Implement Kalman Filter for dynamic estimation
transition_matrix = np.identity(6)
observation_matrix = np.identity(6)

# Correct observation covariance matrix construction
observation_covariance = np.diag([magnitude_noise_std**2]*3 + [angle_noise_std**2]*3)

kf = KalmanFilter(transition_matrices=transition_matrix,
                  observation_matrices=observation_matrix,
                  initial_state_mean=x_hat_noisy[0],
                  observation_covariance=observation_covariance,
                  transition_covariance=np.eye(6) * 0.1)

state_estimates, state_covariances = kf.filter(z_noisy)

# Calculate errors with Kalman Filter
errors_kf = x_true - state_estimates
rmse_kf = np.sqrt(np.mean(errors_kf**2, axis=0))

print("RMSE with Kalman Filter:", rmse_kf)

# Plot error histograms for magnitudes
errors_magnitudes = errors_kf[:, :3]
errors_angles = errors_kf[:, 3:]

# plt.figure(figsize=(12, 6))
# for i in range(3):
#     sns.histplot(errors_magnitudes[:, i], kde=True, label=f'Bus {i+1} Magnitude Error')
# plt.xlabel('Error')
# plt.title('Error Distribution for Voltage Magnitudes')
# plt.legend()
# plt.show()

# Plot error histograms for angles
# plt.figure(figsize=(12, 6))
# for i in range(3):
#     sns.histplot(errors_angles[:, i], kde=True, label=f'Bus {i+1} Angle Error')
# plt.xlabel('Error (Degrees)')
# plt.title('Error Distribution for Voltage Angles')
# plt.legend()
# plt.show()

# Calculate Mean Absolute Percentage Error (MAPE)
mape_magnitudes = np.mean(np.abs(errors_magnitudes / x_true[:, :3])) * 100
mape_angles = np.mean(np.abs(errors_angles / x_true[:, 3:])) * 100

print(f"Mean Absolute Percentage Error (MAPE) for Magnitudes: {mape_magnitudes:.2f}%")
print(f"Mean Absolute Percentage Error (MAPE) for Angles: {mape_angles:.2f}%")
