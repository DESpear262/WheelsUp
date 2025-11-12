# Commit Policy - NEVER SEND GIT COMMANDS

## Core Rule

**Agents NEVER send git commands for any reason.** Instead, agents prepare commit information that the user executes.

## How Commits Work

Rather than touch git directly, agents follow this process:

1. **Select an Agent Name** (A, B, C, etc.)
2. **Create directory** `.\commits\[AgentName]` (if it doesn't exist)
3. **Create add.txt** with list of files to commit (one per line)
4. **Create commit.txt** with commit message (single line)
5. **User executes:** `git add $(cat .\commits\[AgentName]\add.txt) && git commit -m "$(cat .\commits\[AgentName]\commit.txt)"`

## Auto-Commit Files

Agents may prepare commits for these coordination files without asking permission:
- `docs/prd.md`
- `docs/task-list.md`
- `.claude/agent-identity.lock`
- `docs/memory/*.md` (all memory bank files)

## Permission-Required Files

For ALL other files, agents MUST ask permission first:
- Implementation code (`.ts`, `.py`, `.rs`, `.go`, etc.)
- Tests (any file in `tests/`, `__tests__/`, `*_test.py`, etc.)
- Configuration files (`.json`, `.yaml`, `.toml`, `.env.example`, etc.)
- Documentation (`.md` files other than planning docs)
- Build files (`package.json`, `Cargo.toml`, `go.mod`, etc.)

## Commit Message Format

### For Coordination Files:
```
[AgentName] PR-XXX: OldStatus → NewStatus [affected files]
Brief explanation of the change
```

### For Implementation Files:
```
feat|fix|docs|refactor(scope): description

- Detailed explanation
- What changed and why
- Any breaking changes
```

## Examples

### Coordination Commit:
**add.txt:**
```
docs/task-list.md
.claude/agent-identity.lock
```

**commit.txt:**
```
[White] PR-005: Planning → In Progress [AuthService.ts, UserModel.ts]

Completed planning for user authentication feature. No conflicts detected.
```

### Implementation Commit:
**add.txt:**
```
src/auth/AuthService.ts
src/models/UserModel.ts
src/types/auth.ts
```

**commit.txt:**
```
feat(auth): implement JWT token refresh

- Add refresh endpoint to AuthService
- Add refreshToken field to UserModel
- Define RefreshTokenResponse type
- Implements PR-005
```

## When to Ask Permission

**Always ask before preparing implementation commits:**
- "I've completed the authentication feature. Would you like me to prepare a commit for these changes?"
- Wait for user approval: "Yes, please prepare the commit"
- Only then create the add.txt and commit.txt files

## Emergency Commits

In rare cases where immediate commit is needed (e.g., fixing a critical bug), still follow the process:
1. Alert user to the urgency
2. Ask for immediate approval
3. Prepare commit information
4. User can execute immediately

## Directory Structure

```
.\commits\
├── A\
│   ├── add.txt
│   └── commit.txt
├── B\
│   ├── add.txt
│   └── commit.txt
└── C\
    ├── add.txt
    └── commit.txt
```

## Why This Approach?

- **Security:** Prevents agents from accidentally running destructive git commands
- **Control:** User maintains full control over what gets committed
- **Auditability:** Clear record of what each agent prepared for commit
- **Safety:** No risk of agents committing sensitive files or incorrect changes
