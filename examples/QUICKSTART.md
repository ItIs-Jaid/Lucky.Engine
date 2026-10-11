# 🚀 Quick Start Guide

Follow these steps to get Lucky.Engine running in under 5 minutes.

## Step 1: Clone or Copy Files

```bash
# Option A: Clone from GitHub
git clone https://github.com/YOUR_USERNAME/Lucky.Engine.git
cd Lucky.Engine/bridge

# Option B: Download files manually
# Copy these files from the repo:
# - engine.py
# - test_suite.py
# - examples/
```

## Step 2: Set Up Configuration

```bash
# Copy example config and rename
cp examples/example-config.yaml lucky-config.yaml

# Edit lucky-config.yaml and add your settings
# (Open in your preferred text editor)
```

## Step 3: Add Your Memory Files

Create your personal memory files by copying the examples:

```bash
# Create your actual files
cp examples/example-USER.md USER.md
cp examples/example-MEMORY-SSOT.md MEMORY-SSOT.md
cp examples/example-bridge_nodes.json bridge_nodes.json
```

**Then edit these files** to add your actual data!

## Step 4: Run Tests

```bash
python test_suite.py
```

**Expected Output:**
```
Results: 5/5 passed
  ✅ finances: 320 tokens
  ✅ move plan: 1300 tokens
  ...
```

## Step 5: Make Your First Query

```bash
python engine.py "finances"
```

**Expected Output:**
```json
{
  "nodes": [{"label": "Finances (User Budget)", "confidence": 0.95}],
  "budget_used": 320,
  "intent": "financial"
}
```

## 📋 File Checklist

After setup, your folder should look like:

```
bridge/
├── engine.py                # ⚙️ Framework (do not edit)
├── test_suite.py            # ✅ Tests (do not edit)
├── lucky-config.yaml        # ⚙️ Your configuration (edit this)
├── USER.md                  # 📝 Your profile (edit this)
├── MEMORY-SSOT.md           # 📝 Your memory structure (edit this)
├── bridge_nodes.json        # 🔗 Your mappings (edit this)
├── lucky-audit.md           # 📋 Auto-generated (do not edit)
└── examples/                # 📚 Template files
```

## 🆘 Troubleshooting

| Problem | Solution |
|---------|----------|
| `No module named 'engine'` | Make sure you're in the `bridge/` directory |
| `No results found` | Check confidence_threshold in config, ensure bridge_nodes.json has entries |
| `Permission denied` | Check file permissions for lucky-audit.md |
| `Test fails` | Ensure example files have been copied and edited |

## 📚 Next Steps

1. **Read the main README** for deeper understanding
2. **Add more bridge mappings** in bridge_nodes.json
3. **Customize intent detection** in engine.py
4. **Share your improvements** with the community!
