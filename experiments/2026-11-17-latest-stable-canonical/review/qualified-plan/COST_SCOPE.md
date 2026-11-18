# Initial R0 and README cost scope

This is an operator planning estimate, not a paper result or an API bill. The queue has 10639 minimum generation calls: 10614 API-level requests plus 25 whole-corpus distillation chunks. Retries and separate pilots add calls.

Gemini 3.1 Flash-Lite Standard text prices checked November 17, 2026 are $0.25 per million input tokens and $1.50 per million output tokens, including thinking. [Official pricing](https://ai.google.dev/gemini-api/docs/pricing). These queued jobs use ordinary requests, not the discounted Google Batch API.

| Assumed author input per entry | Assumed average output per call | Estimated initial cost |
|---:|---:|---:|
| 4,000 tokens | 1,000 tokens | $25.93 |
| 8,000 tokens | 2,500 tokens | $55.17 |
| 16,000 tokens | 8,192 tokens | $156.62 |

R0 and distillation input estimates use exact rendered text lengths divided by four. Generated summaries and README responses do not exist yet, so author-entry input and output averages remain assumptions. The 8,192-token request cap is not a total spending ceiling. Actual provider usage replaces these estimates after the pilots. The remaining conditions, repairs, aliases, hints, puzzles and deep dive are excluded. No reliable completion-time estimate exists for the new model/scope before the pilots. [Detailed per-bank scope](COST_SCOPE.json).
