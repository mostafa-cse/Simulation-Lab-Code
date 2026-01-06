import random
import matplotlib.pyplot as plt
import collections
import matplotlib.gridspec as gridspec

# ==========================================
# 1. SYSTEM CONFIGURATION
# ==========================================
# (Lambda) Average Arrivals per second
# e.g., 0.9 = 1 customer every ~1.1 seconds on average
ARRIVAL_RATE = 0.9

# (Mu) Average Service Rate per second
# e.g., 1.0 = 1 service finished every ~1.0 second on average
SERVICE_RATE = 1.0

# Visualization speed (Lower is faster)
SIMULATION_SPEED = 0.05

plt.style.use('bmh')

# ==========================================
# 2. RANDOM GENERATORS (IID)
# ==========================================
def get_interarrival_time():
    """
    Generates a Random Inter-Arrival Time.
    Distribution: Exponential (Markovian)
    """
    return random.expovariate(ARRIVAL_RATE)

def get_service_time():
    """
    Generates a Random Service Duration.
    Distribution: Exponential (Markovian)
    """
    return random.expovariate(SERVICE_RATE)

# ==========================================
# 3. VISUALIZATION SETUP
# ==========================================
def init_dashboard():
    fig = plt.figure(figsize=(14, 9))
    fig.canvas.manager.set_window_title("Simulation: M/M/1 (Random Arrivals & Service)")

    gs = gridspec.GridSpec(2, 2, height_ratios=[2, 1])

    ax_status = fig.add_subplot(gs[0, 0])
    ax_history = fig.add_subplot(gs[0, 1])
    ax_metrics = fig.add_subplot(gs[1, :])
    ax_metrics.axis('off')

    return fig, ax_status, ax_history, ax_metrics

# ==========================================
# 4. MAIN SIMULATION LOOP
# ==========================================
def main():
    fig, ax_status, ax_history, ax_metrics = init_dashboard()

    # System State
    clock = 0.0
    queue_arrival_times = collections.deque()
    server_busy = False

    # Statistics
    stats = {
        "total_arrivals": 0, "total_served": 0,
        "total_wait_time": 0.0, "current_queue_len": 0,
        "current_in_service": 0, "avg_wait": 0.0
    }

    # Graph Data
    wait_time_data = []
    customer_indices = []

    # Initialize First Events
    next_arrival = get_interarrival_time()
    next_departure = float('inf')

    print(f"Simulation Started. M/M/1 Model.")
    print(f"Arrivals: Random (Exp), Service: Random (Exp)")

    try:
        while plt.fignum_exists(fig.number):

            # --- Logic Step: Determine Next Event ---
            if next_arrival <= next_departure:
                # === EVENT: CUSTOMER ARRIVAL ===
                clock = next_arrival
                stats["total_arrivals"] += 1

                # Schedule next arrival (IID Random)
                next_arrival = clock + get_interarrival_time()

                if not server_busy:
                    server_busy = True
                    stats["current_in_service"] = 1

                    # No wait time for immediate service
                    wait_time_data.append(0.0)
                    customer_indices.append(stats["total_arrivals"])

                    # Schedule departure (IID Random Service Time)
                    next_departure = clock + get_service_time()
                else:
                    # Join Queue
                    queue_arrival_times.append(clock)
                    stats["current_queue_len"] += 1

            else:
                # === EVENT: SERVICE COMPLETION ===
                clock = next_departure
                stats["total_served"] += 1

                if stats["current_queue_len"] > 0:
                    # Process next in line
                    arrival_time = queue_arrival_times.popleft()
                    stats["current_queue_len"] -= 1

                    # Calculate how long they waited
                    wait = clock - arrival_time
                    stats["total_wait_time"] += wait
                    wait_time_data.append(wait)
                    customer_indices.append(stats["total_arrivals"])

                    # Schedule next departure (IID Random Service Time)
                    next_departure = clock + get_service_time()
                else:
                    # Server goes idle
                    server_busy = False
                    stats["current_in_service"] = 0
                    next_departure = float('inf')

            # --- Visual Update ---
            if len(wait_time_data) > 0:
                stats["avg_wait"] = stats["total_wait_time"] / len(wait_time_data)

            # 1. Queue Status (Bar Chart)
            ax_status.clear()
            bars = ax_status.bar(['Service', 'Queue'],
                                 [stats["current_in_service"], stats["current_queue_len"]],
                                 color=['#2E8B57', '#DC143C'])
            ax_status.set_title("Live System Status", fontweight='bold')
            # Dynamic Y-axis to handle random queue spikes
            ax_status.set_ylim(0, max(5, stats["current_queue_len"] + 5))

            for bar in bars:
                height = bar.get_height()
                ax_status.text(bar.get_x() + bar.get_width()/2, height,
                               f'{int(height)}', ha='center', va='bottom', fontweight='bold')

            # 2. Wait History (Scatter/Bar)
            ax_history.clear()
            # Plot individual wait times
            ax_history.bar(customer_indices, wait_time_data, color='#4682B4', alpha=0.6, width=1.0, label='Individual Wait')
            # Plot Average Line
            ax_history.axhline(y=stats["avg_wait"], color='red', linestyle='-', linewidth=2, label='Avg Wait')

            ax_history.set_title("Wait Time History (Stochastic)", fontweight='bold')
            ax_history.set_xlabel("Customer #")
            ax_history.set_ylabel("Time Waited (s)")
            ax_history.legend(loc='upper left')

            # 3. Dashboard Text
            ax_metrics.clear()
            ax_metrics.axis('off')

            dashboard_text = (
                f"⏱ CLOCK: {clock:6.2f}s  |  MODE: M/M/1 (Random Arrival & Service)\n"
                f"────────────────────────────────────────────────────────\n"
                f"🎲 Arrival Rate (λ): {ARRIVAL_RATE}  |  🎲 Service Rate (μ): {SERVICE_RATE}\n"
                f"👥 Total Arrivals: {stats['total_arrivals']:<4}  |  ✅ Total Served: {stats['total_served']:<4}\n"
                f"📥 Current Queue:  {stats['current_queue_len']:<4}  |  ⏳ Avg Wait Time: {stats['avg_wait']:.2f}s"
            )

            ax_metrics.text(0.5, 0.5, dashboard_text, transform=ax_metrics.transAxes,
                            ha='center', va='center', fontsize=11, family='monospace',
                            bbox=dict(boxstyle="round,pad=1", fc="#fff9c4", ec="#fbc02d"))

            plt.tight_layout()
            plt.draw()
            plt.pause(SIMULATION_SPEED)

    except KeyboardInterrupt:
        pass
    plt.ioff(); plt.show()

if __name__ == "__main__":
    main()
