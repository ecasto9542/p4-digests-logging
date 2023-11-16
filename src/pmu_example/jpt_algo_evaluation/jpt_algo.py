import math
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from statistics import mean, stdev
import cmath

wt = 0

def parse_csv_data():
    data = pd.read_csv("pmu12.csv")
    times = list(map(lambda time: time.replace("2014-01-28 23:00:", ""), data["TimeTag"].values))
    magnitudes = [data["Magnitude01"].values, data["Magnitude02"].values, data["Magnitude03"].values]
    phase_angles = [data["Angle01"].values, data["Angle02"].values, data["Angle03"].values]
    return {"times": times, "magnitudes": magnitudes, "phase_angles": phase_angles}

#jpt algorithm
def jpt_algo(kMin1, kMin2, kMin3):
    #to find the measurement at time k, take
    # the 3 measurements prior (kMin1 ... KMin3) and plug it into the following to get
    return 3 * kMin1 - 3 * kMin2 + kMin3

# V = magnitude  * e^(j*(wt + phase_angle)) http://hyperphysics.phy-astr.gsu.edu/hbase/electric/impcom.html#c1
# given the magnitude and phase angle component, we convert he voltage into the form a + bi
def calculate_complex_voltage(magnitude, phase_angle):
    #e^ix = cos x + i sin x #euler's formula
    # V = magnitude * cos(wt + phase_angle) + magnitude * i * sin(wt + phase_angle)
    real_portion = math.cos(math.radians(wt + phase_angle)) * magnitude
    imaginary_portion = math.sin(math.radians(wt + phase_angle)) * magnitude
    voltage = complex(real_portion, imaginary_portion)
    return voltage

# based on a voltage in the form V = a + bi, it extracts the magnitude and the voltage
def phase_angle_and_magnitude_from_complex_voltage(voltage):
    phase_angle = cmath.phase(voltage)
    # phase_angle =  math.atan(voltage.imag / voltage.real) - wt #finds phase angle in radians
    magnitude = math.sqrt(voltage.real**2 + voltage.imag**2)
    return magnitude, math.degrees(phase_angle)

def generate_jpt_predictions(magnitudes, phase_angles):
    predictions = {"magnitudes": [], "phase_angles": []}
    for i in range(len(magnitudes) - 3):
        three_previous = []
        for j in range(i, i + 3):
            three_previous.append({"magnitude": magnitudes[j], "phase_angle": phase_angles[j]})
        k_min = []
        for measurement in three_previous:
            complex_voltage = calculate_complex_voltage(measurement["magnitude"], measurement["phase_angle"])
            k_min.append(complex_voltage)
        complex_voltage_future_approximation = jpt_algo(k_min[2],k_min[1],k_min[0])
        predicted_magnitude, predicted_phase_angle = phase_angle_and_magnitude_from_complex_voltage(complex_voltage_future_approximation)
        predictions["magnitudes"].append(predicted_magnitude)
        predictions["phase_angles"].append(predicted_phase_angle)
    return predictions

#approximation error formula
def calculate_approximation_error(exact, approximate):
    return abs(exact - approximate) / exact * 100

#calculate the average, std deviation, and range of approximation errors
def calculate_approximation_error_statistics(exact_measurements, approximate_measurements, generated_indexes = None):
    approximation_errors = []
    if generated_indexes is not None:
        for i in generated_indexes:
            approximation_errors.append(calculate_approximation_error(exact_measurements[i], approximate_measurements[i]))
    else:
        for i in range(len(exact_measurements)):
            approximation_errors.append(calculate_approximation_error(exact_measurements[i], approximate_measurements[i]))

    return mean(approximation_errors), stdev(approximation_errors), max(approximation_errors)

def calculate_angle_error(exact, approximate):
    ex = np.array([exact.real, exact.imag])
    app = np.array([approximate.real, approximate.imag])
    dot_product = np.dot(ex, app)
    angle =    math.acos(dot_product / (abs(exact) * abs(approximate)))
    return angle

def calculate_angle_statistics(exact_measurements, approximate_measurements, generated_indexes = None):
    angle_deviations = []
    if generated_indexes is not None:
        for i in generated_indexes:
            ex = np.array([exact_measurements[i].real, exact_measurements[i].imag])
            app = np.array([approximate_measurements[i].real, approximate_measurements[i].imag])
            dot_product = np.dot(ex, app)
            if dot_product / (np.linalg.norm(ex) * np.linalg.norm(app)) > 1:
                angle = 0
            else:
                angle =  math.degrees(math.acos(dot_product / (np.linalg.norm(ex) * np.linalg.norm(app))))
            angle_deviations.append(angle)
            if angle > 50:
                print("issue with: ")
    else:
        for i in range(len(approximate_measurements)):
            ex = np.array([exact_measurements[i].real, exact_measurements[i].imag])
            app = np.array([approximate_measurements[i].real, approximate_measurements[i].imag])
            dot_product = np.dot(ex, app)
            if dot_product / (np.linalg.norm(ex) * np.linalg.norm(app)) > 1:
                angle = 0
            else:
                angle =  math.degrees(math.acos(dot_product / (np.linalg.norm(ex) * np.linalg.norm(app))))
            angle_deviations.append(angle)
    return mean(angle_deviations), stdev(angle_deviations), max(angle_deviations)

def calculate_complex_voltage_set(magnitudes, phase_angles):
    complex_voltage_set = []
    for i in range(len(magnitudes)):
        complex_voltage_set.append(calculate_complex_voltage(magnitudes[i], phase_angles[i]))
    return complex_voltage_set

if __name__ == "__main__":
    pmu_raw_data = parse_csv_data()
    x = pmu_raw_data["times"][3:]
    fig, ax = plt.subplots(2, 2)
    """
    y1 = pmu_raw_data["magnitudes"][0][3:]
    ax[0][0].plot(x, y1, color="g", label="actual")
    y2 = generate_jpt_predictions(pmu_raw_data["magnitudes"][0], pmu_raw_data["phase_angles"][0])["magnitudes"]
    ax[0][0].plot(x, y2, color="r", label="predicted")
    print("Approximation error average (mag1): ")
    print(calculate_approximation_error_statistics(y1, y2))
    y1 = pmu_raw_data["magnitudes"][1][3:]
    y2 = generate_jpt_predictions(pmu_raw_data["magnitudes"][1], pmu_raw_data["phase_angles"][1])["magnitudes"]
    ax[0][1].plot(x, y1, color="g", label="actual")
    ax[0][1].plot(x, y2, color="r", label="predicted")
    print("Approximation error average (mag2): ")
    print(calculate_approximation_error_statistics(y1, y2))
    y1 = pmu_raw_data["magnitudes"][2][3:]
    y2 = generate_jpt_predictions(pmu_raw_data["magnitudes"][2], pmu_raw_data["phase_angles"][2])["magnitudes"]
    ax[1][0].plot(x, y1, color="g", label="actual")
    ax[1][0].plot(x, y2, color="r", label="predicted")
    print("Approximation error average (mag3): ")
    print(calculate_approximation_error_statistics(y1, y2))
    plt.show()
    """
    #good shit
    jpt_predictions1 = generate_jpt_predictions(pmu_raw_data["magnitudes"][0], pmu_raw_data["phase_angles"][0])
    y1 = pmu_raw_data["phase_angles"][0][3:]
    ax[0][0].plot(x, y1, color="g", label="actual")
    y2 = jpt_predictions1["phase_angles"]
    ax[0][0].plot(x, y2, color="r", label="predicted")
    complex_phasors1 = calculate_complex_voltage_set(pmu_raw_data["magnitudes"][0], pmu_raw_data["phase_angles"][0])
    complex_JPT1 = calculate_complex_voltage_set(jpt_predictions1["magnitudes"], jpt_predictions1["phase_angles"])
    print(calculate_angle_statistics(complex_phasors1, complex_JPT1))

    """
    y1 = pmu_raw_data["phase_angles"][1][3:]
    y2 = generate_jpt_predictions(pmu_raw_data["magnitudes"][1], pmu_raw_data["phase_angles"][1])["phase_angles"]
    ax[0][1].plot(x, y1, color="g", label="actual")
    ax[0][1].plot(x, y2, color="r", label="predicted")
    print("Approximation error average (mag2): ")
    print(calculate_approximation_error_statistics(y1, y2))
    y1 = pmu_raw_data["phase_angles"][2][3:]
    y2 = generate_jpt_predictions(pmu_raw_data["magnitudes"][2], pmu_raw_data["phase_angles"][2])["phase_angles"]
    ax[1][0].plot(x, y1, color="g", label="actual")
    ax[1][0].plot(x, y2, color="r", label="predicted")
    print("Approximation error average (mag3): ")
    print(calculate_approximation_error_statistics(y1, y2))
    plt.show()
    """

"""
todo:
- work with yanfeng to implement simplified algorithm on p4 switch => compare difference between switch and control
- p4 => if else but no for loop, onrly simple addition
- research operations that can be done on the p4 switch and how they can be used for the following
"""
