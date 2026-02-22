# Proposal: Hybrid GitHub Transition

**Status:** Draft / Action Plan  
**Goal:** Migrate the `nanofolks` project from the `jhonny-cinco-ai` user to a dedicated `nanofolks` user account while preserving all commit history and establishing a clean "Root" repository.

---

## Why the "Hybrid" Approach?

Unlike a standard GitHub transfer, this manual migration ensures:
1. **Standalone Status:** The new repo is a "Root" project, not a fork of another user.
2. **Brand Identity:** The URL becomes `github.com/nanofolks/nanofolks`.
3. **History Preservation:** Every single commit and iterative refinement made during development is kept for forensic and debugging purposes.

---

## Migration Steps

### Phase 1: GitHub Setup
1. Log in to GitHub as the **`nanofolks`** user.
2. Create a **New Repository**.
   - **Name:** `nanofolks`
   - **Privacy:** Select your preference (Public or Private).
   - **CRITICAL:** Do **NOT** check "Initialize with README", "Add .gitignore", or "Choose a license". The repo must be completely empty.
3. Copy the Remote SSH or HTTPS URL (e.g., `https://github.com/nanofolks/nanofolks.git`).

### Phase 2: Local Terminal Update
Run these commands within your local project directory:

```bash
# 1. Rename the old remote for safety (keeps a link to the old repo if needed)
git remote rename origin old-origin

# 2. Add the new nanofolks repo as the primary origin
git remote add origin https://github.com/nanofolks/nanofolks.git

# 3. Push all code, history, and branches to the new account
git push -u origin main
```

> [!NOTE]
> If you have multiple branches you wish to keep, run `git push --all origin` after the main push.

### Phase 3: Verification & Cleanup
1. **Check GitHub:** Refresh the repository page on the `nanofolks` account. Ensure the file tree and commit history are exactly as expected.
2. **Archive Old Repo:** Log back into the `jhonny-cinco-ai` account and go to **Settings > Danger Zone > Archive this repository**. 
   - Update the README of the old repo first to point to the new home: `This project has moved to [github.com/nanofolks/nanofolks](https://github.com/nanofolks/nanofolks)`.
3. **Update Local Access:** If you use SSH keys, ensure your local machine has the SSH key configured for the `nanofolks` user if it differs from your primary account.

---

## Troubleshooting
- **Permission Denied:** If GitHub tries to push using your old credentials, you may need to update your Git credential helper or use an SSH key specifically for the `nanofolks` user.
- **Remote contains work:** If you accidentally initialized the repo with a README, you will get an error on push. You must either re-create the repo as empty or run `git pull origin main --rebase` before pushing.
