# Lucky.Engine Test Suite

This file tests that Lucky.Engine is working correctly on your system.

## How to Run

```bash
cd <your-project>/memory/graphify-out/bridge
python test_suite.py
```

## Expected Output

```
Results: 5/5 passed
  ✅ finances: 320 tokens
  ✅ move plan: 1300 tokens
  ✅ ssh: 320 tokens
  ✅ unknown_topic_xyz: 1550 tokens
  ✅ hermes: 0 tokens
```

## What Each Test Does

| Query | Expected Intent | Expected Max Tokens |
|-------|-----------------|---------------------|
| `finances` | financial | 500 |
| `move plan` | relocation | 1500 |
| `ssh` | ssh | 500 |
| `unknown_topic_xyz` | general | 2000 |
| `hermes` | agent_config | 1000 |

## Troubleshooting

If tests fail:
1. Check `lucky-config.yaml` exists
2. Check `bridge_nodes.json` has entries
3. Check `audit.log` has write permissions
4. Run `python engine.py "test"` manually
