import pandas as pd
import math, random, copy, datetime

# ===============================
# LOAD DATA FROM CSV FILES
# ===============================

# 1. Travel Times
travel_df = pd.read_csv('Universal Studios.xlsx - travel time(mins).csv', index_col=0)
# Convert the DataFrame to a nested dict: travel_times[from][to] = time
travel_times = {}
for from_loc in travel_df.index:
    travel_times[from_loc] = {}
    for to_loc in travel_df.columns:
        travel_times[from_loc][to_loc] = travel_df.loc[from_loc, to_loc]

# 2. Play Times
play_df = pd.read_csv('Universal Studios.xlsx - play time(mins).csv', 
                      header=None, # No header in the file
                      names=["Attraction", "PlayTime"], # Assign your own column names
                      sep=",") # or sep="\t" if tab-separated
ride_durations = {}
for idx, row in play_df.iterrows():
    attraction = row["Attraction"]
    duration = row["PlayTime"] # Adjust column name if needed
    ride_durations[attraction] = duration

# 3. Wait Times
wait_df = pd.read_csv('Universal Studios.xlsx - 11.9data.csv')

# Parse the timestamps from the columns (excluding 'Ride Name')
time_cols = [c for c in wait_df.columns if c != "Ride Name"]

# Assuming park opening = 2024-11-09 08:00:00 (adjust if necessary)
opening_time = datetime.datetime(2024, 11, 9, 8, 0, 0)
time_mappings = []
for col in time_cols:
    # Parse the datetime from the column name
    col_dt = pd.to_datetime(col)
    delta = col_dt - opening_time
    minutes_from_8am = int(delta.total_seconds() // 60)
    time_mappings.append((col, minutes_from_8am))

# Build a dictionary: wait_data[attraction][minutes_from_8am] = wait_time
wait_data = {}
for idx, row in wait_df.iterrows():
    ride_name = row["Ride Name"]
    wait_data[ride_name] = {}
    for (col, minutes_from_8am) in time_mappings:
        wait_data[ride_name][minutes_from_8am] = row[col]

# If there's an 'Entrance' not in play times or wait times, just ensure it is defined
if "Universal City Plaza Entrence" not in travel_times:
    travel_times["Universal City Plaza Entrence"] = {}
    # Fill missing entrance travel times if not included above

# Limit the attractions to the specified list
attractions = [
    "Despicable Me Minion Mayhem",
    "Flight of the Hippogriff",
    "Harry Potter and the Forbidden Journey",
    "Kung Fu Panda Adventure",
    "Mario Kart Bowsers Challenge",
    "Ollivanders",
    "Revenge of the Mummy The Ride",
    "Studio Tour",
    "TRANSFORMERS The Ride3D",
    "The Secret Life of Pets Off the Leash",
    "The Simpsons Ride"
]

# ===============================
# TIME-DEPENDENT WAIT TIME LOOKUP
# ===============================
def get_wait_time(attraction, arrival_time):
    """
    arrival_time: minutes from 8:00 AM
    This function finds the closest recorded wait time at or before arrival_time.
    If exact match not found, we'll interpolate linearly between known time points.
    """
    if attraction not in wait_data:
        return 0  # If not available, assume 0.

    times = sorted(wait_data[attraction].keys())
    if len(times) == 0:
        return 0
    if arrival_time <= times[0]:
        return wait_data[attraction][times[0]]
    if arrival_time >= times[-1]:
        return wait_data[attraction][times[-1]]

    # Find closest times for interpolation
    for i in range(len(times)-1):
        if times[i] <= arrival_time < times[i+1]:
            t1, t2 = times[i], times[i+1]
            w1, w2 = wait_data[attraction][t1], wait_data[attraction][t2]
            # Linear interpolation
            ratio = (arrival_time - t1) / (t2 - t1)
            return w1 + (w2 - w1)*ratio

    return 0

# ===============================
# EVALUATION FUNCTION
# ===============================
def evaluate_route(route):
    current_location = "Universal City Plaza Entrence"
    current_time = 0  # minutes from 8:00 AM

    for att in route:
        # Travel
        current_time += travel_times[current_location][att]
        # Wait
        w = get_wait_time(att, current_time)
        current_time += w
        # Ride duration
        current_time += ride_durations[att]
        current_location = att

    return current_time



# ===============================
# GENETIC ALGORITHM
# ===============================
def ga_optimize(attractions_list, pop_size=50, generations=200, mutation_rate=0.1):
    def fitness(r):
        return evaluate_route(r)

    # Initialize population
    population = []
    for _ in range(pop_size):
        route = attractions_list[:]
        random.shuffle(route)
        population.append(route)

    for gen in range(generations):
        scored = [(fitness(r), r) for r in population]
        scored.sort(key=lambda x: x[0])
        population = [x[1] for x in scored[:pop_size//2]]

        # Crossover
        while len(population) < pop_size:
            p1 = random.choice(population)
            p2 = random.choice(population)
            cut1, cut2 = sorted(random.sample(range(len(p1)), 2))
            child = [None]*len(p1)
            child[cut1:cut2] = p1[cut1:cut2]
            fill = [x for x in p2 if x not in child]
            idx = 0
            for i in range(len(child)):
                if child[i] is None:
                    child[i] = fill[idx]
                    idx += 1
            # Mutation
            if random.random() < mutation_rate:
                i, j = random.sample(range(len(child)), 2)
                child[i], child[j] = child[j], child[i]
            population.append(child)

    scored = [(fitness(r), r) for r in population]
    scored.sort(key=lambda x: x[0])
    return scored[0][1], scored[0][0]


# ===============================
# MAIN EXECUTION
# ===============================
if __name__ == "__main__":
    # Run GA
    ga_route, ga_score = ga_optimize(attractions, pop_size=50, generations=200)
    print("GA Route:", ga_route)
    print("GA Score:", ga_score)
