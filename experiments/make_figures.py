"""Build manuscript figures and tables from the experiment summaries.

Run after ``experiments/run_all.py``.  Writes vector PDFs to ``paper/figures/``
and Markdown tables to ``paper/tables/`` so the manuscript can read them in.
"""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"
FIGS = ROOT / "paper" / "figures"
TABLES = ROOT / "paper" / "tables"

plt.rcParams.update({
    "font.size": 8.5, "axes.labelsize": 8.5, "axes.titlesize": 9,
    "legend.fontsize": 7.5, "xtick.labelsize": 7.5, "ytick.labelsize": 7.5,
    "axes.grid": True, "grid.alpha": 0.28, "grid.linewidth": 0.5,
    "axes.spines.top": False, "axes.spines.right": False,
    "savefig.bbox": "tight", "savefig.pad_inches": 0.02,
    "lines.linewidth": 1.3, "lines.markersize": 4.5,
})
C = {"blue": "#1f4e8c", "orange": "#c8541f", "green": "#2b7a4b", "red": "#a32020",
     "purple": "#6a3d9a", "grey": "#5a5a5a"}


PRETTY = {
    "fleet_size": "Fleet $n$", "wall_clock_s": "Wall (s)",
    "realtime_factor": "RTF", "device_steps_per_second": "Device-steps s$^{-1}$",
    "telemetry_throughput_msg_s": "Telemetry (msg s$^{-1}$)",
    "peak_rss_mb": "Peak RSS (MB)", "messages_generated": "Generated",
    "messages_delivered": "Delivered", "message_delivery_ratio_pct": "Delivery (\\%)",
    "telemetry_interval_ms": "Period (ms)",
    "scenario": "Scenario", "loss_probability": "Loss $p$",
    "mean_outage_interval_s": "Outage period (s)",
    "transport_latency_ms_mean": "Latency mean (ms)",
    "transport_latency_ms_max": "Latency max (ms)",
    "twin_staleness_p95_s": "p95 staleness (s)",
    "twin_offline_area_s": "Offline area (dev\\,s)",
    "resynchronisations": "Resyncs",
    "fault": "Fault", "family": "Family", "n": "Samples",
    "mean_auc": "Mean AUC", "min_auc": "Min AUC", "max_abs_d": "Max $|d|$",
    "nozzle_temperature_c": "$\\Delta T_{\\mathrm{nozzle}}$",
    "bed_temperature_c": "$\\Delta T_{\\mathrm{bed}}$",
    "chamber_temperature_c": "$\\Delta T_{\\mathrm{cham}}$",
    "power_w": "$\\Delta P$ (W)", "print_speed_mm_s": "$\\Delta v$ (mm/s)",
    "material_used_g": "$\\Delta m$ (g)", "health_score": "$\\Delta$ health",
    "link_down_events": "Link-down", "link_up_events": "Link-up",
    "twin_staleness_p50_s": "p50 staleness (s)",
    "twin_staleness_max_s": "Max staleness (s)",
    "sync_delay_ms_mean": "Sync delay mean (ms)",
    "sync_delay_ms_p95": "Sync delay p95 (ms)",
    "peak_cpu_percent": "Peak CPU (\\%)", "mean_rss_mb": "Mean RSS (MB)",
    "simulated_duration_s": "Simulated (s)",
    "twin_staleness_area_s": "Stale area (dev\\,s)",
    "seed": "Seed",
}

CAPTIONS = {
    "table_e1_scalability": ("tab:e1",
        "E1 scalability. Fleet size swept over three orders of magnitude at "
        "3\\,600\\,s simulated duration, $\\Delta t = 1$\\,s, on one core group of "
        "an 11-core laptop. RTF is the real-time factor."),
    "table_e2_telemetry_rate": ("tab:e2",
        "E2 telemetry frequency. $n=100$, 1\\,800\\,s simulated, "
        "$\\Delta t = 0.05$\\,s."),
    "table_e3_network_impairment": ("tab:e3",
        "E3 network impairment. Loss sweep ($p$ varied) and outage sweep (mean "
        "interval between per-device disconnection episodes varied, mean episode "
        "duration 60\\,s). $n=200$, 3\\,600\\,s."),
    "table_e4_separability": ("tab:e4",
        "E4 fault separability. Per-channel Cohen's $d$ between telemetry "
        "recorded while the fault was active during \\texttt{PRINTING} and the "
        "fault-free \\texttt{PRINTING} baseline. Positive $d$ means the fault "
        "raises the channel."),
    "table_e5_outage_recovery": ("tab:e5",
        "E5 outage and recovery. $n=50$, 3\\,600\\,s, mean disconnection interval "
        "300\\,s, mean duration 60\\,s."),
}


def _esc(s: str) -> str:
    return (str(s).replace("_", r"\_").replace("&", r"\&")
            .replace("%", r"\%").replace("#", r"\#").replace("$", r"\$"))


def _cap(s: str) -> str:
    """Capitalise a lowercase label for display in a table cell."""
    return str(s).capitalize()


def _num(x: float) -> str:
    """Format a millisecond latency compactly, keeping thousands readable."""
    return f"{x:,.1f}"


def _md_table(df: pd.DataFrame, name: str, floatfmt: str = ".4g") -> None:
    """Write a booktabs LaTeX float (and a Markdown twin for the README)."""
    TABLES.mkdir(parents=True, exist_ok=True)
    label, caption = CAPTIONS.get(name, (name, name.replace("_", " ").capitalize()))
    cols = list(df.columns)
    head = " & ".join(PRETTY.get(c, _esc(c)) for c in cols)
    body = []
    for _, r in df.iterrows():
        cells = []
        for c in cols:
            v = r[c]
            if isinstance(v, float):
                cells.append(format(v, floatfmt))
            elif isinstance(v, str):
                cells.append(_esc(v))
            else:
                cells.append(str(v))
        body.append(" & ".join(cells) + r" \\")
    ncols = len(cols)
    tex = (
        "\\begin{table}[t]\n"
        "\\centering\\small\\setlength{\\tabcolsep}{4pt}\n"
        "\\caption{" + caption + "}\n"
        "\\label{" + label + "}\n"
        "\\resizebox{\\textwidth}{!}{%\n"
        "\\begin{tabular}{@{}" + "l" + "r" * (ncols - 1) + "@{}}\n"
        "\\toprule\n" + head + " \\\\\n\\midrule\n"
        + "\n".join(body) + "\n"
        "\\bottomrule\n\\end{tabular}}\n\\end{table}\n"
    )
    (TABLES / f"{name}.tex").write_text(tex)
    try:
        (TABLES / f"{name}.md").write_text(
            df.to_markdown(index=False, floatfmt=floatfmt) + "\n")
    except ImportError:
        pass
    print(f"  table {name}.tex  ({len(df)} rows)")


def fig_e1() -> None:
    df = pd.read_csv(RESULTS / "E1_scalability" / "summary.csv")
    fig, ax = plt.subplots(1, 3, figsize=(7.2, 2.25))

    ax[0].plot(df.fleet_size, df.device_steps_per_second, "o-", color=C["blue"],
               label="device steps/s")
    ax[0].plot(df.fleet_size, df.telemetry_throughput_msg_s, "s--", color=C["orange"],
               label="telemetry msg/s")
    ax[0].set_xscale("log", base=10)
    ax[0].set_yscale("log", base=10)
    ax[0].set_xlabel("fleet size (printers)")
    ax[0].set_ylabel("throughput (log)")
    ax[0].set_title("(a) throughput vs. fleet size")
    ax[0].legend(loc="lower left")

    ax[1].plot(df.fleet_size, df.wall_clock_s, "o-", color=C["green"], label="wall clock")
    ax[1].plot(df.fleet_size, df.fleet_size * df.simulated_duration_s / 1e6, ":",
               color=C["grey"], label=r"$10^6$ device-steps")
    ax[1].set_xscale("log", base=10)
    ax[1].set_yscale("log", base=10)
    ax[1].set_xlabel("fleet size (printers)")
    ax[1].set_ylabel("wall-clock time (s, log)")
    ax[1].set_title("(b) wall clock vs. fleet size")
    ax[1].legend()

    ax[2].plot(df.fleet_size, df.peak_rss_mb, "o-", color=C["purple"], label="peak RSS")
    ax[2].plot(df.fleet_size, df.fleet_size * 2.6, ":", color=C["grey"],
               label=r"$2.6\,n$ MB (linear)")
    ax[2].set_xscale("log", base=10)
    ax[2].set_yscale("log", base=10)
    ax[2].set_xlabel("fleet size (printers)")
    ax[2].set_ylabel("peak resident set (MB, log)")
    ax[2].set_title("(c) memory vs. fleet size")
    ax[2].legend(loc="upper left")

    fig.savefig(FIGS / "e1_scalability.pdf")
    plt.close(fig)
    _md_table(df[["fleet_size", "wall_clock_s", "realtime_factor",
                  "device_steps_per_second", "telemetry_throughput_msg_s", "peak_rss_mb",
                  "messages_generated", "message_delivery_ratio_pct"]],
              "table_e1_scalability")


def fig_e2() -> None:
    df = pd.read_csv(RESULTS / "E2_telemetry_rate" / "summary.csv")
    df = df.sort_values("telemetry_interval_ms")
    fig, ax = plt.subplots(1, 2, figsize=(4.9, 2.25))
    ax[0].plot(df.telemetry_interval_ms / 1000, df.telemetry_throughput_msg_s, "o-",
               color=C["blue"], label="delivered msg/s")
    ax[0].plot(df.telemetry_interval_ms / 1000,
               df.messages_generated / df.simulated_duration_s, "s--", color=C["orange"],
               label="generated msg/s")
    ax[0].set_xscale("log", base=10)
    ax[0].set_yscale("log", base=10)
    ax[0].set_xlabel("telemetry period (s, log)")
    ax[0].set_ylabel("rate (log)")
    ax[0].set_title("(a) telemetry throughput")
    ax[0].legend()

    ax[1].plot(df.telemetry_interval_ms / 1000, df.wall_clock_s, "o-", color=C["green"])
    ax[1].set_xscale("log", base=10)
    ax[1].set_xlabel("telemetry period (s, log)")
    ax[1].set_ylabel("wall clock (s)")
    ax[1].set_title("(b) simulation cost")

    fig.savefig(FIGS / "e2_telemetry_rate.pdf")
    plt.close(fig)
    _md_table(df[["telemetry_interval_ms", "messages_generated", "messages_delivered",
                  "telemetry_throughput_msg_s", "wall_clock_s", "peak_rss_mb",
                  "sync_delay_ms_mean", "sync_delay_ms_p95"]], "table_e2_telemetry_rate")


def fig_e3() -> None:
    df = pd.read_csv(RESULTS / "E3_network_impairment" / "summary.csv")
    loss = df[df.scenario == "loss"].sort_values("loss_probability")
    out = df[df.scenario == "outage"].sort_values("mean_outage_interval_s", ascending=False)
    fig, ax = plt.subplots(1, 2, figsize=(4.9, 2.25))

    ax[0].plot(100 * loss.loss_probability, loss.message_delivery_ratio_pct, "o-",
               color=C["blue"], label="delivered (%)")
    ax[0].plot(100 * loss.loss_probability, 100 * (1 - loss.loss_probability), ":", color=C["grey"],
               label=r"$100(1-p)$ (ideal)")
    ax[0].plot(100 * loss.loss_probability, loss.twin_staleness_p95_s, "s--", color=C["orange"],
               label="p95 staleness (s)")
    ax[0].set_xlabel("configured packet loss (%)")
    ax[0].set_ylabel("delivery (%) / staleness (s)")
    ax[0].set_title("(a) loss sweep")
    ax[0].legend(loc="center left")

    x = np.arange(len(out))
    ax[1].plot(x, out.resynchronisations, "o-", color=C["red"], label="resynchronisations")
    ax[1].set_xlabel("outage period (s)")
    ax[1].set_ylabel("resynchronisations")
    ax[1].set_xticks(x)
    ax[1].set_xticklabels([f"{int(v):d}" for v in out.mean_outage_interval_s])
    ax[1].set_title("(b) outage frequency")
    ax2 = ax[1].twinx()
    ax2.plot(x, out.twin_offline_area_s, "s--", color=C["purple"], label="offline area (dev*s)")
    ax2.set_ylabel("offline area (dev*s)")
    ax2.grid(False)
    h1, l1 = ax[1].get_legend_handles_labels()
    h2, l2 = ax2.get_legend_handles_labels()
    ax[1].legend(h1 + h2, l1 + l2, loc="upper left")

    fig.savefig(FIGS / "e3_network_impairment.pdf")
    plt.close(fig)
    _md_table(df[["scenario", "loss_probability", "mean_outage_interval_s", "messages_generated",
                  "messages_delivered", "message_delivery_ratio_pct",
                  "transport_latency_ms_mean", "transport_latency_ms_max",
                  "twin_staleness_p95_s", "twin_offline_area_s", "resynchronisations"]],
              "table_e3_network_impairment")


def fig_e4() -> None:
    df = pd.read_csv(RESULTS / "E4_fault_injection" / "separability.csv")
    rows = []
    feats: list[str] = []
    for _, r in df.iterrows():
        det = json.loads(r["detail"])
        feats = list(det)
        rows.append({"fault": r["fault"], "family": r["family"], "n": int(r["n_samples"]),
                     "mean_auc": float(r["mean_auc"]), "min_auc": float(r["min_auc"]),
                     **det})
    long = pd.DataFrame(rows)
    mat = long[feats].to_numpy(dtype=float)
    order = np.argsort(-np.nanmax(np.abs(mat), axis=1))
    long, mat = long.iloc[order], mat[order]

    fig, ax = plt.subplots(figsize=(4.9, 3.2))
    im = ax.imshow(mat, cmap="coolwarm", vmin=-2.5, vmax=2.5, aspect="auto")
    ax.set_xticks(range(len(feats)))
    ax.set_xticklabels([f.replace("_", "\n") for f in feats], fontsize=6.2)
    ax.set_yticks(range(len(long)))
    ax.set_yticklabels(long.fault.to_list(), fontsize=7)
    for i in range(mat.shape[0]):
        for j in range(mat.shape[1]):
            if np.isfinite(mat[i, j]):
                ax.text(j, i, f"{mat[i, j]:.1f}", ha="center", va="center", fontsize=5.6,
                        color="white" if abs(mat[i, j]) > 1.6 else "black")
    ax.set_title(r"Cohen's $d$: faulted vs. healthy printing telemetry")
    ax.grid(False)
    fig.colorbar(im, ax=ax, pad=0.02, label=r"$d$")
    fig.savefig(FIGS / "e4_separability.pdf")
    plt.close(fig)

    long["max_abs_d"] = np.nanmax(np.abs(mat), axis=1)
    long["mean_abs_d"] = np.nanmean(np.abs(mat), axis=1)
    keep = ["fault", "n", "max_abs_d", "nozzle_temperature_c", "bed_temperature_c",
            "power_w", "print_speed_mm_s", "material_used_g", "health_score"]
    out = long[keep].sort_values("max_abs_d", ascending=False)
    _md_table(out, "table_e4_separability", ".2f")


def fig_e5() -> None:
    df = pd.read_csv(RESULTS / "E5_outage_recovery" / "summary.csv")
    _md_table(df[["fleet_size", "simulated_duration_s", "message_delivery_ratio_pct",
                  "transport_latency_ms_mean", "transport_latency_ms_max",
                  "twin_staleness_p50_s", "twin_staleness_max_s",
                  "twin_staleness_area_s", "twin_offline_area_s",
                  "resynchronisations", "seed"]],
              "table_e5_outage_recovery", ".4g")


def fig_e6() -> None:
    df = pd.read_csv(RESULTS / "E6_reproducibility" / "summary.csv")
    TABLES.mkdir(parents=True, exist_ok=True)
    rows = []
    for r in df.itertuples():
        if "run" in r.trial:
            label = r.trial.replace("run1", "run 1").replace("run2", "run 2")
            label = label.replace("seed=", "seed~")
            rows.append(f"{label} & \\texttt{{{r.sha256[:16]}}}$\\ldots$"
                        f"\\texttt{{{r.sha256[-8:]}}} \\\\")
        else:
            label = r.trial.replace("_", " ").capitalize()
            rows.append(f"\\emph{{{label}}} & \\texttt{{{r.sha256}}} \\\\")
    body = "\n".join(rows)
    tex = (
        "\\begin{table}[t]\n"
        "\\centering\\small\n"
        "\\caption{E6 reproducibility. SHA-256 of the telemetry artifact. Two runs "
        "at the same seed are byte-identical; changing the seed changes the "
        "artifact.}\n"
        "\\label{tab:e6}\n"
        "\\begin{tabular}{@{}ll@{}}\n\\toprule\nRun & Telemetry SHA-256 \\\\\n"
        "\\midrule\n" + body + "\n\\bottomrule\n\\end{tabular}\n\\end{table}\n"
    )
    (TABLES / "table_e6_reproducibility.tex").write_text(tex)
    (TABLES / "table_e6_reproducibility.md").write_text(
        "\n".join(f"| {r.trial} | `{r.sha256}` |" for r in df.itertuples()) + "\n")
    print("  table table_e6_reproducibility.tex")


def fig_e7() -> None:
    path = RESULTS / "E7_broker_fidelity" / "summary.csv"
    TABLES.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        return
    df = pd.read_csv(path)
    if "transport" not in df.columns:
        return
    body = []
    for r in df.itertuples():
        body.append(
            f"{_cap(r.transport)} & {int(r.qos)} & {r.configured_loss:.2f} & "
            f"{int(r.generated)} & {int(r.delivered)} & {r.delivery_pct:.2f} & "
            f"{_num(r.latency_ms_mean)} & {_num(r.latency_ms_max)} & "
            f"{r.staleness_p95_s:.2f} & {r.staleness_max_s:.2f} \\\\")
    tex = (
        "\\begin{table}[t]\n"
        "\\centering\\small\\setlength{\\tabcolsep}{4pt}\n"
        "\\caption{E7 broker fidelity. The same 20-device fleet, the same topics "
        "and the same message objects, run through a real Mosquitto~2.1.2 broker "
        "on loopback and through the in-process transport. QoS~1 blocks on "
        "\\texttt{PUBACK}, which applies back-pressure and keeps the twin fresh; "
        "QoS~0 is fire-and-forget, so the simulated clock outruns the broker and "
        "staleness grows by an order of magnitude. The broker path is lossless over "
        "TCP at both QoS levels: the configured loss is an additive impairment the "
        "in-process model applies, not a property of the broker.}\n"
        "\\label{tab:e7}\n"
        "\\resizebox{\\textwidth}{!}{%\n"
        "\\begin{tabular}{@{}llrrrrrrrr@{}}\n\\toprule\nTransport & QoS &Cfg.\\ loss & "
        "Gen. & Deliv. & Deliv.\\ (\\%) & Lat.\\ mean (ms) & Lat.\\ max (ms) & "
        "Stale p95 (s) & Stale max (s) \\\\\n\\midrule\n"
        + "\n".join(body) + "\n\\bottomrule\n\\end{tabular}}\n\\end{table}\n"
    )
    (TABLES / "table_e7_broker_fidelity.tex").write_text(tex)
    df.to_markdown(TABLES / "table_e7_broker_fidelity.md", index=False)
    print("  table table_e7_broker_fidelity.tex  "
          f"({len(df)} rows)")


def main() -> int:
    FIGS.mkdir(parents=True, exist_ok=True)
    for fn in (fig_e1, fig_e2, fig_e3, fig_e4, fig_e5, fig_e6, fig_e7):
        fn()
    print(f"figures -> {FIGS}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

