# Single-server, single FIFO queue DES + live matplotlib dashboard
# Uses IID sequences A_i (interarrival) and S_i (service), independent. [file:1]

from collections import deque
import numpy as np
import matplotlib.pyplot as plt

INF = float("inf")

def main(N=120, mean_inter=1.0, mean_serv=0.8, seed=42, redraw_every=1):
    rng = np.random.default_rng(seed)

    # Pre-generate IID sequences (independent streams) [file:1]
    # Generate more than needed to avoid running out.
    M = 10 * N + 1000
    A = rng.exponential(scale=mean_inter, size=M)  # A1, A2, ... IID
    S = rng.exponential(scale=mean_serv,  size=M)  # S1, S2, ... IID (independent)
    ia_i = 0
    sv_i = 0

    # --- State ---
    t = 0.0
    server_busy = False
    q = deque()

    # First arrival at time A1 (>0), not at time 0 [file:1]
    next_arrival = float(A[ia_i]); ia_i += 1
    next_departure = INF

    arrivals = 0
    served = 0

    sum_wait = 0.0
    count_started = 0

    area_q = 0.0
    last_t = 0.0
    last_event = "INIT"

    # --- Plot ---
    plt.ion()
    fig = plt.figure(figsize=(10.5, 6.2))
    gs = fig.add_gridspec(2, 2, height_ratios=[2.0, 1.1])
    ax_state = fig.add_subplot(gs[0, 0])
    ax_avg = fig.add_subplot(gs[0, 1])
    ax_txt = fig.add_subplot(gs[1, :])
    ax_txt.axis("off")

    ax_state.set_title("Current Queue State")
    bars_state = ax_state.bar(["In Service", "In Queue"], [0, 0])
    ax_state.set_ylabel("Count")

    ax_avg.set_title("Average Waiting Time")
    bar_avg = ax_avg.bar(["Avg wait"], [0.0])[0]
    ax_avg.set_ylabel("Time (minutes)")
    txt_avg = ax_avg.text(0.5, 0.9, "Current avg: 0.000 min", transform=ax_avg.transAxes,
                          ha="center", va="top")

    txt = ax_txt.text(0.01, 0.95, "", transform=ax_txt.transAxes,
                      ha="left", va="top", family="monospace")

    def update_plot():
        in_service = 1 if server_busy else 0
        in_queue = len(q)
        avg_wait = (sum_wait / count_started) if count_started else 0.0
        qhat = (area_q / t) if t > 0 else 0.0

        ax_state.set_ylim(0, max(5, in_queue + 2, in_service + 2))
        bars_state[0].set_height(in_service)
        bars_state[1].set_height(in_queue)

        for old in list(ax_state.texts):
            old.remove()
        for b in bars_state:
            ax_state.text(b.get_x() + b.get_width()/2, b.get_height(), f"{int(b.get_height())}",
                          ha="center", va="bottom", fontsize=10)

        bar_avg.set_height(avg_wait)
        ax_avg.set_ylim(0, max(1.0, avg_wait * 1.7 + 0.1))
        txt_avg.set_text(f"Current avg: {avg_wait:.3f} min")

        nxt_type = "ARRIVAL" if next_arrival <= next_departure else "DEPARTURE"
        nxt_time = min(next_arrival, next_departure)
        nxt_str = f"{nxt_type} @ {nxt_time:.3f}" if nxt_time < INF else f"{nxt_type} @ INF"

        txt.set_text(
            "Simulation Summary\n"
            "------------------\n"
            f"Time (t):                 {t:.3f} min\n"
            f"Last event:               {last_event}\n"
            f"Next event:               {nxt_str}\n"
            f"Total arrivals:           {arrivals}\n"
            f"Started service:          {count_started}\n"
            f"Completed service:        {served} / {N}\n"
            f"Queue length Q(t):        {len(q)}   (excludes in-service) [file:1]\n"
            f"Avg waiting d_hat:        {avg_wait:.3f} min (arrival->service start) [file:1]\n"
            f"Time-avg queue q_hat:     {qhat:.3f} [file:1]\n"
            f"Params: inter={mean_inter}, serv={mean_serv}, seed={seed}\n"
        )

        fig.canvas.draw_idle()
        fig.canvas.flush_events()
        plt.pause(0.001)

    # --- DES loop ---
    events = 0
    while served < N:
        ev, te = ("ARRIVAL", next_arrival) if next_arrival <= next_departure else ("DEPARTURE", next_departure)

        # accumulate area under Q(t) between events [file:1]
        area_q += len(q) * (te - last_t)
        last_t = te
        t = te

        if ev == "ARRIVAL":
            arrivals += 1

            # schedule next arrival using next IID interarrival time [file:1]
            next_arrival = t + float(A[ia_i]); ia_i += 1

            if not server_busy:
                server_busy = True
                sum_wait += 0.0
                count_started += 1

                # schedule departure using next IID service time [file:1]
                next_departure = t + float(S[sv_i]); sv_i += 1
            else:
                q.append(t)

        else:  # DEPARTURE
            served += 1
            if served >= N:
                server_busy = False
                next_departure = INF
            else:
                if q:
                    a = q.popleft()
                    delay = max(0.0, t - a)  # delay in queue [file:1]
                    sum_wait += delay
                    count_started += 1

                    next_departure = t + float(S[sv_i]); sv_i += 1
                    server_busy = True
                else:
                    server_busy = False
                    next_departure = INF

        last_event = ev
        events += 1
        if events % redraw_every == 0:
            update_plot()

    update_plot()
    plt.ioff()
    plt.show()

if __name__ == "__main__":
    main()
