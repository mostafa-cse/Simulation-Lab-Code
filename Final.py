#!/usr/bin/env python3
"""
Single-server FIFO DES with live matplotlib dashboard
- IID exponential interarrival/service times
- Single server + FIFO queue
- Top panels: Queue State + Avg Waiting Time
- Bottom: Summary inside a neat box
- Explicit IID random variables
"""

import numpy as np, matplotlib.pyplot as plt, time
from collections import deque
from matplotlib.patches import Rectangle
import math

# ---------------- Parameters ----------------
INTERARRIVAL_MEAN = 2.0
SERVICE_MEAN = 1.0
UPDATE_EVERY = 5
EVENT_DELAY = 0.1
SEED = 42

# ---------------- Initialization ----------------
rng = np.random.default_rng(SEED)
t = 0.0
queue = deque()
server_busy = False

# Next events
next_arrival = rng.exponential(INTERARRIVAL_MEAN)  # A_1
next_departure = math.inf

# Statistics
num_arrivals = num_served = 0
delays = []
area_Q = 0.0
last_event_time = 0.0
event_counter = 0

# ---------------- Matplotlib Setup ----------------
plt.ion()
fig = plt.figure(figsize=(10,6))
gs = fig.add_gridspec(3,2, height_ratios=[3,3,1], hspace=0.6)
ax_state = fig.add_subplot(gs[0,0])
ax_avg   = fig.add_subplot(gs[0,1])
ax_summary = fig.add_subplot(gs[1:, :])
ax_summary.axis('off')

# Queue State panel
bars_state = ax_state.bar(['In Service','In Queue'], [0,0], edgecolor='k')
val_texts = [ax_state.text(i,0,'',ha='center',va='bottom',fontsize=11,fontweight='bold') for i in range(2)]
ax_state.set_ylim(0,5); ax_state.set_title("Current Queue State", fontsize=12,fontweight='bold')

# Avg Waiting Time panel
bar_avg = ax_avg.bar(['Avg Waiting Time'], [0], width=0.6, edgecolor='k')
avg_text = ax_avg.text(0,0,'',ha='center',va='center',fontsize=12,fontweight='bold')
ax_avg.set_ylim(0,max(1.0,INTERARRIVAL_MEAN)); ax_avg.set_title("Average Waiting Time d̄(k)", fontsize=12,fontweight='bold')
fig.suptitle("Single-Server FIFO DES — Live Dashboard", fontsize=14,fontweight='bold')

# ---------------- Helper: Update Plots ----------------
def update_plots():
    in_service = 1 if server_busy else 0
    in_queue = len(queue)
    bars_state[0].set_height(in_service)
    bars_state[1].set_height(in_queue)
    val_texts[0].set_text(f'{in_service}'); val_texts[0].set_y(in_service+0.05)
    val_texts[1].set_text(f'{in_queue}'); val_texts[1].set_y(in_queue+0.05)
    ax_state.set_ylim(0,max(2,in_queue+2))

    avg_wait = np.mean(delays) if delays else 0.0
    bar_avg[0].set_height(avg_wait)
    avg_text.set_text(f'{avg_wait:.3f}')
    avg_text.set_y(avg_wait/2 if avg_wait>0 else 0.05)
    ax_avg.set_ylim(0,max(1.0, avg_wait*1.6, INTERARRIVAL_MEAN))

    # Summary in a box
    time_avg_q = area_Q/t if t>0 else 0.0
    lines = [
        f"Time: {t:6.2f}",
        f"Arrivals: {num_arrivals:5d}   Served: {num_served:5d}",
        f"Queue Length: {in_queue:3d}   Server: {'BUSY' if server_busy else 'IDLE'}",
        f"Avg Waiting Time: {avg_wait:6.3f}   Time-Avg Queue: {time_avg_q:6.3f}",
        f"Params: inter_mean={INTERARRIVAL_MEAN}, serv_mean={SERVICE_MEAN}"
    ]
    summary_text = "\n".join(lines)
    ax_summary.clear(); ax_summary.axis('off')
    ax_summary.add_patch(Rectangle((0.01,0.05),0.98,0.9,fill=True,color='lightyellow',zorder=0))
    ax_summary.text(0.01,0.5,summary_text, fontsize=10,family='monospace',va='center')
    plt.pause(0.001)

# ---------------- Main DES Loop ----------------
while plt.fignum_exists(fig.number):
    time.sleep(EVENT_DELAY)

    # Next event selection (explicit DES)
    if next_arrival <= next_departure: event_type, t_next = 'arrival', next_arrival
    else: event_type, t_next = 'departure', next_departure

    # Update area under Q(t)
    delta = t_next - last_event_time
    area_Q += len(queue)*delta
    t = t_next; last_event_time = t

    # Event processing with IID random variables
    if event_type=='arrival':
        num_arrivals += 1
        A_i = rng.exponential(INTERARRIVAL_MEAN)  # next interarrival time
        if not server_busy:
            server_busy = True
            delays.append(0.0)
            S_i = rng.exponential(SERVICE_MEAN)
            next_departure = t + S_i
        else:
            queue.append(t)
        next_arrival = t + A_i
    else:
        num_served += 1
        S_i = rng.exponential(SERVICE_MEAN)  # next service time
        if queue:
            arrival_time = queue.popleft()
            delays.append(t-arrival_time)
            next_departure = t + S_i
        else:
            server_busy = False; next_departure = math.inf

    event_counter += 1
    if event_counter % UPDATE_EVERY == 0: update_plots()

# Final update on window close
plt.ioff(); update_plots()
