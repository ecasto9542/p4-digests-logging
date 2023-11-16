import pandas as pd

def parse_csv_data(file_path, time_header_name, magnitude_header_names, angle_header_names):
    data = pd.read_csv(file_path)
    times = data[time_header_name].values
    magnitudes = list(map(
        lambda magnitude_header: data[magnitude_header].values, magnitude_header_names))
    phase_angles = list(
        map(lambda angle_header: data[angle_header].values, angle_header_names))
    return {"times": times, "magnitudes": magnitudes, "phase_angles": phase_angles}
