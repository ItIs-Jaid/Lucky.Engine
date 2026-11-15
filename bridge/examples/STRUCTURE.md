# 📦 Repository Structure

```
Lucky.Engine/
├── README.md                      # Main documentation (this file)
├── LICENSE                        # MIT License
├── .gitignore                     # What to exclude from git
│
├── docs/                          # Public documentation
│   └── superpowers/
│       └── specs/
│           ├── SECURITY-CHECKLIST.md
│           └── hlco-public-README.md
│
└── memory/
    └── graphify-out/
        └── bridge/
            ├── engine.py                       # Core framework
            ├── test_suite.py                   # Automated tests
            ├── lucky-config.yaml               # Your configuration
            ├── USER.md                         # Your profile
            ├── MEMORY-SSOT.md                  # Your memory structure
            ├── bridge_nodes.json               # Your skill→memory mappings
            ├── lucky-audit.md                  # Auto-generated audit log
            ├── reference.md                    # Detailed reference
            ├── edge-traversal.md               # Edge traversal docs
            ├── query_helper.py                 # Legacy query tool
            ├── benchmark.py                    # Performance benchmarks
            └── examples/                       # 📚 Templates & samples
                ├── QUICKSTART.md               # Fast setup guide
                ├── example-config.yaml         # Config template
                ├── example-USER.md             # Profile template
                ├── example-MEMORY-SSOT.md      # Memory template
                ├── example-bridge_nodes.json   # Mappings template
                ├── example-audit.md            # Audit template
                └── example-README.md           # Local README template
```

## 📂 What to Commit vs. Not Commit

### ✅ Safe to Commit (Framework)
- `engine.py` - Core code
- `test_suite.py` - Tests
- `examples/` - Templates
- `docs/` - Documentation
- `.gitignore` - Git rules

### ❌ Do NOT Commit (Personal Data)
- `lucky-config.yaml` - Your specific settings (optional: commit empty template)
- `USER.md` - Your personal profile
- `MEMORY-SSOT.md` - Your memory data
- `bridge_nodes.json` - Your specific mappings
- `lucky-audit.md` - Your query history

### ⚠️ Template Files (Commit, then customize)
Create these from templates, then edit with your data:
1. Copy `examples/example-config.yaml` → `lucky-config.yaml`
2. Copy `examples/example-USER.md` → `USER.md`
3. Copy `examples/example-bridge_nodes.json` → `bridge_nodes.json`

## 🔧 Quick Copy Commands

```bash
# On Linux/Mac
cp examples/example-config.yaml lucky-config.yaml
cp examples/example-USER.md USER.md
cp examples/example-bridge_nodes.json bridge_nodes.json

# On Windows (PowerShell)
Copy-Item examples\example-config.yaml .\lucky-config.yaml
Copy-Item examples\example-USER.md .\USER.md
Copy-Item examples\example-bridge_nodes.json .\bridge_nodes.json
```
