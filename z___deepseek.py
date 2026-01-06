"""
Single-Server Single-Queue Discrete Event Simulation
M/M/1 Queue System with Exponential IID Random Variables
Clean and Well-Organized Version
"""

import random
import numpy as np
import matplotlib.pyplot as plt
from collections import deque
from matplotlib.animation import FuncAnimation
import sys

class SingleServerQueueSimulation:
    """Discrete Event Simulation of M/M/1 Queue System"""

    def __init__(self, interarrival_mean=2.5, service_mean=2.0):
        """Initialize simulation with exponential distributions"""
        # Distribution parameters
        self.interarrival_mean = interarrival_mean
        self.service_mean = service_mean

        # Calculate rates
        self.arrival_rate = 1.0 / interarrival_mean if interarrival_mean > 0 else 0
        self.service_rate = 1.0 / service_mean if service_mean > 0 else 0

        # Discrete Event Simulation components
        self.clock = 0.0
        self.server_status = 'IDLE'
        self.queue = deque()
        self.event_list = []

        # Statistics
        self.total_arrivals = 0
        self.total_served = 0
        self.delays = []
        self.total_delay = 0.0

        # Queue length
        self.Q_area = 0.0
        self.last_event_time = 0.0
        self.current_Q = 0

        # Performance metrics
        self.avg_wait = 0.0

        # Initialize and setup
        self.initialize_simulation()
        self.setup_visualization()
        self.running = True

    def initialize_simulation(self):
        """Initialize simulation as per PDF specifications"""
        self.clock = 0.0
        self.server_status = 'IDLE'
        self.queue.clear()
        self.current_Q = 0
        self.last_event_time = 0.0
        self.Q_area = 0.0

        self.total_arrivals = 0
        self.total_served = 0
        self.delays = []
        self.total_delay = 0.0
        self.avg_wait = 0.0

        first_arrival = self.generate_interarrival()
        self.event_list = [('ARRIVAL', first_arrival)]

    def generate_interarrival(self):
        """Generate IID exponential interarrival time"""
        if self.arrival_rate <= 0:
            return float('inf')
        return random.expovariate(self.arrival_rate)

    def generate_service(self):
        """Generate IID exponential service time"""
        if self.service_rate <= 0:
            return 1.0
        return random.expovariate(self.service_rate)

    def update_queue_area(self, current_time):
        """Update area under Q(t) curve between events"""
        delta_t = current_time - self.last_event_time
        self.Q_area += self.current_Q * delta_t
        self.last_event_time = current_time

    def timing_routine(self):
        """Find next event and advance clock"""
        if not self.event_list:
            return 'NONE', float('inf')

        event_type, event_time = min(self.event_list, key=lambda x: x[1])
        self.clock = event_time
        self.event_list.remove((event_type, event_time))
        self.update_queue_area(self.clock)

        return event_type, event_time

    def process_arrival(self):
        """Process customer arrival event"""
        self.total_arrivals += 1

        next_arrival_time = self.clock + self.generate_interarrival()
        self.event_list.append(('ARRIVAL', next_arrival_time))

        if self.server_status == 'IDLE':
            self.server_status = 'BUSY'
            self.delays.append(0.0)
            self.total_delay += 0.0
            self.total_served += 1

            service_time = self.generate_service()
            departure_time = self.clock + service_time
            self.event_list.append(('DEPARTURE', departure_time))
        else:
            self.queue.append(self.clock)
            self.current_Q = len(self.queue)

    def process_departure(self):
        """Process customer departure event"""
        self.total_served += 1

        if self.queue:
            arrival_time = self.queue.popleft()
            self.current_Q = len(self.queue)

            wait_time = self.clock - arrival_time
            self.delays.append(wait_time)
            self.total_delay += wait_time

            service_time = self.generate_service()
            departure_time = self.clock + service_time
            self.event_list.append(('DEPARTURE', departure_time))
        else:
            self.server_status = 'IDLE'
            self.current_Q = 0

    def update_metrics(self):
        """Update performance metrics"""
        if self.total_served > 0:
            self.avg_wait = self.total_delay / self.total_served
        else:
            self.avg_wait = 0.0

    def setup_visualization(self):
        """Setup clean matplotlib figure"""
        self.fig = plt.figure(figsize=(10, 8))
        self.fig.suptitle('Single Server Queue Simulation', fontsize=16, fontweight='bold')

        # Create subplots
        self.ax_queue = plt.subplot2grid((2, 2), (0, 0))
        self.ax_wait = plt.subplot2grid((2, 2), (0, 1))
        self.ax_summary = plt.subplot2grid((2, 2), (1, 0), colspan=2)
        self.ax_summary.axis('off')

        plt.tight_layout(rect=[0, 0.03, 1, 0.95])

    def update_queue_chart(self):
        """Update Current Queue State chart"""
        self.ax_queue.clear()

        categories = ['Service', 'Queue']
        values = [1 if self.server_status == 'BUSY' else 0, self.current_Q]
        colors = ['#3498db', '#e74c3c']

        bars = self.ax_queue.bar(categories, values, color=colors, width=0.6)

        self.ax_queue.set_title('Current Queue State', fontsize=12, fontweight='bold')
        self.ax_queue.set_ylabel('Customers', fontsize=10)
        self.ax_queue.set_ylim(0, max(5, max(values) + 1))

        for bar, value in zip(bars, values):
            height = bar.get_height()
            self.ax_queue.text(bar.get_x() + bar.get_width()/2, height + 0.1,
                             str(value), ha='center', fontweight='bold', fontsize=12)

        self.ax_queue.grid(axis='y', alpha=0.3)

    def update_wait_chart(self):
        """Update Average Waiting Time chart"""
        self.ax_wait.clear()

        value = self.avg_wait

        # Color coding
        if value < self.service_mean * 0.5:
            color = '#27ae60'  # Green
        elif value < self.service_mean:
            color = '#f39c12'  # Orange
        else:
            color = '#c0392b'  # Red

        bar = self.ax_wait.bar(['Average Wait'], [value], color=color, width=0.5)

        self.ax_wait.set_title('Average Waiting Time', fontsize=12, fontweight='bold')
        self.ax_wait.set_ylabel('Time (seconds)', fontsize=10)
        self.ax_wait.set_ylim(0, max(value * 1.2, self.service_mean * 1.5, 5))

        height = bar[0].get_height()
        self.ax_wait.text(bar[0].get_x() + bar[0].get_width()/2, height + 0.05,
                         f'{height:.2f}', ha='center', fontweight='bold', fontsize=12)

        self.ax_wait.text(0.5, -0.15, f'Current: {value:.2f} s',
                         ha='center', transform=self.ax_wait.transAxes,
                         fontsize=11, fontweight='bold')

        self.ax_wait.grid(axis='y', alpha=0.3)

    def update_summary(self):
        """Update Simulation Summary panel"""
        self.ax_summary.clear()
        self.ax_summary.axis('off')

        # Clean table format without box characters
        summary_text = f"""
        SIMULATION SUMMARY

        Simulation Time:         {self.clock:8.2f} s
        Current Queue Length:    {self.current_Q:8d}
        In Service Customer:     {1 if self.server_status == 'BUSY' else 0:8d}
        Served Customers:        {self.total_served:8d}
        Average Waiting Time:    {self.avg_wait:8.2f} s
        """

        # Display with clean formatting
        self.ax_summary.text(0.1, 0.9, summary_text, fontsize=11,
                           verticalalignment='top',
                           bbox=dict(boxstyle='round', facecolor='#ecf0f1',
                                   alpha=0.9, edgecolor='#7f8c8d'))

        # Add parameter info at bottom
        param_text = f"λ = {1/self.interarrival_mean:.2f}, μ = {1/self.service_mean:.2f}"
        self.ax_summary.text(0.5, 0.05, param_text, ha='center', fontsize=10,
                           bbox=dict(boxstyle='round', facecolor='#bdc3c7', alpha=0.7))

    def simulation_step(self, frame=None):
        """Execute one simulation step"""
        if not self.running:
            return False

        events_per_frame = 3

        for _ in range(events_per_frame):
            event_type, _ = self.timing_routine()

            if event_type == 'NONE':
                self.running = False
                break
            elif event_type == 'ARRIVAL':
                self.process_arrival()
            elif event_type == 'DEPARTURE':
                self.process_departure()

        self.update_metrics()

        self.update_queue_chart()
        self.update_wait_chart()
        self.update_summary()

        return True

    def start(self):
        """Start the simulation animation"""
        self.anim = FuncAnimation(
            self.fig,
            self.simulation_step,
            interval=200,
            blit=False,
            cache_frame_data=False
        )

        plt.show()


def main():
    """Main function"""
    print("=" * 50)
    print("Single Server Queue Simulation")
    print("=" * 50)

    interarrival_mean = 2.5
    service_mean = 2.0

    print(f"\nParameters:")
    print(f"Mean Interarrival Time: {interarrival_mean:.1f}s")
    print(f"Mean Service Time:      {service_mean:.1f}s")
    print("\nStarting simulation...")

    simulation = SingleServerQueueSimulation(
        interarrival_mean=interarrival_mean,
        service_mean=service_mean
    )

    simulation.start()


if __name__ == "__main__":
    try:
        import numpy as np
        import matplotlib.pyplot as plt
    except ImportError as e:
        print(f"Error: {e}")
        print("Install: pip install numpy matplotlib")
        sys.exit(1)

    main()
