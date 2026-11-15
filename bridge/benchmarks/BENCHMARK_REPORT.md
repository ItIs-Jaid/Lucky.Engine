# Lucky.Engine Benchmark Report

| Graph | Query | Baseline tokens | Lucky tokens | Compression % | Recall@Budget % | Cold ms | Warm ms |
|---|---|---:|---:|---:|---:|---:|---:|
| 34 | finances | 664 | 216 | 67.47 | 100.0 | 24.19 | 0.26 |
| 34 | move plan | 664 | 272 | 59.04 | 100.0 | 15.74 | 0.25 |
| 34 | ssh | 664 | 189 | 71.54 | 100.0 | 14.58 | 0.28 |
| 34 | what can I afford for relocation? | 664 | 203 | 69.43 | 100.0 | 14.83 | 0.26 |
| 34 | check tailscale network | 664 | 135 | 79.67 | 100.0 | 12.75 | 0.24 |
| 1000 | finances | 8382 | 216 | 97.42 | 100.0 | 32.07 | 0.28 |
| 1000 | move plan | 8382 | 272 | 96.75 | 100.0 | 23.94 | 0.25 |
| 1000 | ssh | 8382 | 189 | 97.75 | 100.0 | 19.39 | 0.27 |
| 1000 | what can I afford for relocation? | 8382 | 203 | 97.58 | 100.0 | 21.75 | 0.24 |
| 1000 | check tailscale network | 8382 | 135 | 98.39 | 100.0 | 19.74 | 0.24 |
| 5000 | finances | 40382 | 216 | 99.47 | 100.0 | 57.81 | 0.31 |
| 5000 | move plan | 40382 | 272 | 99.33 | 100.0 | 63.55 | 0.28 |
| 5000 | ssh | 40382 | 189 | 99.53 | 100.0 | 42.13 | 0.41 |
| 5000 | what can I afford for relocation? | 40382 | 203 | 99.5 | 100.0 | 51.85 | 0.27 |
| 5000 | check tailscale network | 40382 | 135 | 99.67 | 100.0 | 31.92 | 0.27 |
