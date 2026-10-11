# GitHub Authentication Guide

**Your GitHub Username:** ItIs-Jaid

## Step 1: Create a Personal Access Token

1.  Go to: **https://github.com/settings/tokens**
2.  Click **"Generate new token"** → **"Generate new token (classic)"**
3.  Fill in:
    - **Note:** `Lucky.Engine - ItIs-Jaid`
    - **Expiration:** `90 days` (or your preference)
    - **Select Scopes:**
        - ✅ `repo` (Full control of private repositories)
        - ✅ `workflow` (Update GitHub Action workflows)
4.  Click **"Generate token"**
5.  **IMPORTANT:** Copy the token **immediately** - you'll only see it once!
6.  Save it somewhere secure (e.g., password manager)

## Step 2: Initialize Git Repository

Open a terminal (Git Bash) and run:

```bash
# Navigate to the bridge folder
cd "REDACTED_LOCAL_PATH/memory/graphify-out/bridge"

# Initialize git repo
git init

# Add all files
git add .

# Commit
git commit -m "Initial Lucky.Engine framework"
```

## Step 3: Authenticate to GitHub

You'll use your **Personal Access Token** as your password.

```bash
# Test git with your credentials
git ls-remote https://github.com/ItIs-Jaid/Lucky.Engine.git

# Enter when prompted:
# Username: ItIs-Jaid
# Password: <paste the token you copied above>
```

This will save your credentials locally for future operations.

## Step 4: Push the Repository

```bash
# Add the remote repository
git remote add origin https://github.com/ItIs-Jaid/Lucky.Engine.git

# Push to GitHub
git push -u origin main
```

**Note:** You may need to create the empty repository first on GitHub.com (https://github.com/new) before pushing.

---

**Troubleshooting:**
- If you get "Permission denied" - your token may need the `repo` scope
- If git asks for password again - your credentials weren't saved, run `git config --global credential.helper store` again
