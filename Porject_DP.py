import pandas as pd
from datetime import datetime, timedelta

# Load Excel data
file_path = 'C:/Users/Yijie Zhang/Desktop/各项目行程时间.xlsx'  # Replace with your file path
travel_times = pd.read_excel(file_path, sheet_name='各项目行程时间', index_col=0)
queue_times = pd.read_excel(file_path, sheet_name='项目排队时间')
play_times = pd.read_excel(file_path, sheet_name='项目游玩时间', index_col=0)

# Ensure the index of queue_times is of datetime type
queue_times['Time'] = pd.to_datetime(queue_times.iloc[:, 0], format='%H:%M:%S').dt.time
queue_times.set_index('Time', inplace=True)
queue_times.drop(columns=queue_times.columns[0], inplace=True)

# Convert play_times to a dictionary
play_times_dict = play_times.iloc[0].to_dict()

# Define entrance and attractions
entrance = "Universal City PlazaEntrence"
attractions = list(travel_times.columns)
attractions.remove(entrance)

# Remove "Water World"
if "Water World" in attractions:
    attractions.remove("Water World")
    travel_times = travel_times.drop("Water World", axis=0).drop("Water World", axis=1)
    queue_times = queue_times.drop(columns=["Water World"], errors="ignore")
    play_times_dict.pop("Water World", None)

# Get the closest time point
def get_closest_queue_time(queue_times, target_time):
    """
    Find the queue time record closest to the target time.
    target_time is of type datetime.time, and the index of queue_times is also datetime.time.
    """
    available_times = queue_times.index
    for time in available_times:
        if time >= target_time:
            return time
    return available_times[-1]

# Dynamic programming algorithm
def dp_schedule(locations, travel_times, queue_times, play_times, start_time, end_time):
    num_locations = len(locations)
    dp = [{} for _ in range(num_locations)]  # DP array, each position stores a dictionary {current time: (number of attractions, path)}

    # Initial state: from the entrance to each attraction
    for idx, location in enumerate(locations):
        travel_time = int(travel_times.loc[entrance, location])
        queue_lookup_time = get_closest_queue_time(queue_times, start_time.time())
        queue_time = int(queue_times.loc[queue_lookup_time, location])
        play_time = int(play_times.get(location, 0))
        total_time = travel_time + queue_time + play_time
        if total_time <= (end_time - start_time).total_seconds() / 60:
            dp[idx][start_time + timedelta(minutes=total_time)] = (1, [(entrance, location)])

    # Dynamic programming to update all possible paths
    for idx, location in enumerate(locations):
        for time, (count, path) in dp[idx].items():
            for next_idx, next_location in enumerate(locations):
                if next_location == location or any(next_location in p for p in path):
                    continue
                travel_time = int(travel_times.loc[location, next_location])
                queue_lookup_time = get_closest_queue_time(queue_times, time.time())
                queue_time = int(queue_times.loc[queue_lookup_time, next_location])
                play_time = int(play_times.get(next_location, 0))
                total_time = travel_time + queue_time + play_time
                next_time = time + timedelta(minutes=total_time)

                if next_time <= end_time:
                    new_count = count + 1
                    new_path = path + [(location, next_location)]
                    if next_time not in dp[next_idx] or dp[next_idx][next_time][0] < new_count:
                        dp[next_idx][next_time] = (new_count, new_path)

    # Find the path that covers all attractions
    best_path = []
    for idx in range(num_locations):
        for time, (count, path) in dp[idx].items():
            if count == num_locations:
                best_path = path
                break
        if best_path:
            break

    # If unable to cover all attractions, return the path covering the most attractions
    if not best_path:
        max_count = 0
        for idx in range(num_locations):
            for time, (count, path) in dp[idx].items():
                if count > max_count:
                    max_count = count
                    best_path = path

    # Convert the path to a timetable
    itinerary = []
    current_time = start_time
    for from_location, to_location in best_path:
        travel_time = int(travel_times.loc[from_location, to_location])
        queue_lookup_time = get_closest_queue_time(queue_times, current_time.time())
        queue_time = int(queue_times.loc[queue_lookup_time, to_location])
        play_time = int(play_times.get(to_location, 0))

        itinerary.append({
            "Time": current_time.time(),
            "From": from_location,
            "To": to_location,
            "Queue Time": queue_time,
            "Play Time": play_time,
            "Travel Time": travel_time
        })

        current_time += timedelta(minutes=travel_time + queue_time + play_time)

    return itinerary

# Set time range
start_time = datetime.strptime("08:00", "%H:%M")
end_time = datetime.strptime("20:00", "%H:%M")

# Execute dynamic programming algorithm
itinerary = dp_schedule(attractions, travel_times, queue_times, play_times_dict, start_time, end_time)

# Output results
itinerary_df = pd.DataFrame(itinerary)
print(itinerary_df)
