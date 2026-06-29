import serial
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import numpy as np
import time

# ================= CONFIGURATION =================
SIMULATION_MODE = True  # Set to False when using real Arduino hardware
SERIAL_PORT = 'COM3'    # Change to your port (e.g., '/dev/ttyUSB0' on Linux/Mac)
BAUD_RATE = 9600
MAX_DISTANCE_CM = 200   # Max range of your ultrasonic sensor
# =================================================

# Attempt to connect to Arduino if not in simulation
if not SIMULATION_MODE:
    try:
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
        time.sleep(2)  # Give Arduino time to reset after serial connection
        print(f"Connected to {SERIAL_PORT}")
    except Exception as e:
        print(f"Failed to connect to {SERIAL_PORT}: {e}")
        exit()

# Setup the Matplotlib figure and polar plot
fig = plt.figure(facecolor='#050505') # Dark background
ax = fig.add_subplot(111, polar=True, facecolor='#050505')

# Style the radar grid
ax.tick_params(axis='x', colors='#00FF00') # Green angle labels
ax.tick_params(axis='y', colors='#00FF00') # Green distance labels
ax.grid(color='#005500', alpha=0.7)        # Dark green grid lines
ax.set_ylim(0, MAX_DISTANCE_CM)
ax.set_thetamin(0)   # Limit plot to a 180-degree semi-circle
ax.set_thetamax(180)

# Initialize arrays to store 181 degrees of data (0 to 180)
# We use np.nan so empty angles don't plot at 0 distance
angles_rad = np.radians(np.arange(0, 181, 1))
distances = np.full(181, np.nan)

# Create the visual elements we will update in the loop
scatter_plot, = ax.plot([], [], marker='o', markersize=5, color='#00FF00', linestyle='None')
sweep_line, = ax.plot([], [], color='red', linewidth=2, alpha=0.8)

# Simulation variables
sim_angle = 0
sim_direction = 1

def get_data():
    """Fetches data from Serial or generates simulation data."""
    global sim_angle, sim_direction
    
    if SIMULATION_MODE:
        # Simulate servo sweeping logic
        sim_angle += sim_direction * 2
        if sim_angle >= 180 or sim_angle <= 0:
            sim_direction *= -1
            
        # Simulate an object placed between 70 and 90 degrees
        if 70 <= sim_angle <= 90:
            dist = 80 + np.random.normal(0, 3) # 80cm away with slight sensor noise
        else:
            dist = 400 # Out of bounds (no object)
            
        time.sleep(0.02) # Simulate servo delay
        return sim_angle, dist
        
    else:
        # Read real Arduino data
        if ser.in_waiting > 0:
            try:
                line = ser.readline().decode('utf-8').strip()
                # Expecting format: "angle,distance"
                ang_str, dist_str = line.split(',')
                return int(ang_str), float(dist_str)
            except:
                return None, None # Ignore corrupted serial lines
        return None, None

def update(frame):
    """Called continuously by FuncAnimation to update the plot."""
    angle_deg, distance = get_data()
    
    if angle_deg is not None and 0 <= angle_deg <= 180:
        # Filter out noisy readings beyond our max distance
        if distance > MAX_DISTANCE_CM or distance <= 0:
            distances[angle_deg] = np.nan 
        else:
            distances[angle_deg] = distance
            
        # 1. Update the red sweeping beam
        current_angle_rad = np.radians(angle_deg)
        sweep_line.set_data([0, current_angle_rad], [0, MAX_DISTANCE_CM])
        
        # 2. Update the green object dots
        scatter_plot.set_data(angles_rad, distances)
        
    return scatter_plot, sweep_line

# Run the real-time animation
ani = animation.FuncAnimation(fig, update, interval=10, blit=True, cache_frame_data=False)
plt.title("2D Spatial Mapping System", color='white', pad=20)
plt.show()

# Cleanup on close
if not SIMULATION_MODE:
    ser.close()