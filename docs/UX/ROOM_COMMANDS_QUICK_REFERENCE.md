# Room Management Commands - Quick Reference

## Overview

Complete guide to managing rooms and teams in nanobot CLI.

---

## Commands at a Glance

| Command | Aliases | Purpose | New? |
|---------|---------|---------|------|
| `/create` | | Create a new room | |
| `/invite` | | Add a bot to current room | |
| `/switch` | | Switch to a different room | ✨ Enhanced |
| `/list-rooms` | `/rooms` | Show all available rooms | |
| `/status` | `/info` | Show current room details | ✨ NEW |
| `/help` | `/help-rooms`, `/?`, `/commands` | Show command help | ✨ NEW |

---

## Detailed Usage

### 1. Create a Room

**Command**: `/create <name> [type]`

**Types**:
- `project` (default) - For collaborative projects
- `direct` - Private chat between specific bots
- `coordination` - Coordinator-only workspace
- `open` - Public workspace

**Examples**:
```bash
[#general] You: /create website-redesign project
[#general] You: /create backend-api
[#general] You: /create research direct
```

**Output**:
```
✅ Created room #website-redesign (project)
   Use: /invite <bot> to add bots
   Use: /switch website-redesign to join
```

---

### 2. Invite a Bot

**Command**: `/invite <bot> [reason]`

**Available Bots**:
- `researcher` - 🧠 Research, analysis, information gathering
- `coder` - 💻 Development, coding, debugging
- `creative` - 🎨 Design, UX/UI, visuals, branding
- `social` - 🤝 Community, social media, engagement
- `auditor` - ✅ Quality assurance, testing, review
- `leader` - 👑 Coordination, leadership (auto-added)

**Examples**:
```bash
[#website-redesign] You: /invite coder help with implementation
[#website-redesign] You: /invite creative design the landing page
[#website-redesign] You: /invite researcher analyze competitors
```

**Output**:
```
✅ coder invited to #website-redesign
   Participants (3): leader, coder, researcher
```

---

### 3. Switch Rooms

**Command**: `/switch [room]`

**Behavior**:
- With room name: Switches immediately, shows team
- Without room: Shows available rooms, prompts for selection

**Examples**:
```bash
[#general] You: /switch
# Shows list of available rooms

[#general] You: /switch website-redesign
# Switches to that room and shows team
```

**Output** (when switching):
```
🔀 Switched to #website-redesign

Room: #website-redesign • Bots: 3

TEAM
→ 💻 coder         Code
→ 🎨 creative      Design
→ 👑 leader        Leader
  🧠 researcher    Research
  🤝 social        Community
  ✅ auditor       Quality
```

---

### 4. List All Rooms

**Command**: `/list-rooms` or `/rooms`

**Output**:
```
Available Rooms

| Room            | Type      | Bots | Status      |
|-----------------|-----------|------|-------------|
| #general        | open      | 1    | 🔵 Idle     |
| #website-design | project   | 4    | 🟢 Active   |

Use /switch <room> to join a room
```

---

### 5. Show Room Status

**Command**: `/status` or `/info`

**Shows**:
- Room name, type, owner, creation date
- Current team roster with in-room indicators
- Status bar with team emoji summary

**Output**:
```
Room: #website-redesign • Team: 3 💻 🎨 👑

Room Details:
  Name: #website-redesign
  Type: project
  Owner: user
  Created: 2026-02-15 14:30

TEAM
→ 💻 coder         Code
→ 🎨 creative      Design
→ 👑 leader        Leader
  🧠 researcher    Research
  🤝 social        Community
  ✅ auditor       Quality
```

---

### 6. Show Command Help

**Command**: `/help`, `/help-rooms`, `/?`, or `/commands`

**Output**: Complete documentation of all room commands with examples

---

## AI-Assisted Room Creation

You can also ask the AI to create rooms and recommend bots:

**Example**:
```bash
[#general] You: I need to create a room for building a website. Can you set it up?

nanobot: I'll help you set up a dedicated room for your website!

🔍 Analyzing task requirements...

For building a website, I recommend:
• 💻 @coder (Development)
• 🎨 @creative (Design)
• 🧠 @researcher (Market research)

Create room #website (project) and invite these bots? [Y/n]: y

✅ Created room #website (project)
  💻 Invited @coder
  🎨 Invited @creative
  🧠 Invited @researcher

Team assembled: @coder, @creative, @researcher

TEAM
→ 💻 coder         Code
→ 🎨 creative      Design
→ 🧠 researcher    Research
→ 👑 leader        Leader
  🤝 social        Community
  ✅ auditor       Quality

🔀 Switched to #website
```

---

## Visual Indicators

### Team Roster Display

```
TEAM
→ 💻 coder         Code        ← In current room (→ marker)
→ 🎨 creative      Design      ← In current room
  🧠 researcher    Research    ← Not in current room
  👑 leader        Leader      ← System bot
```

### Room List Display

```
ROOMS
  🌐 general           (1)     ← Open room
→ 📁 website-design    (4)     ← Current room (→ marker)
  💬 dm-with-coder     (2)     ← Direct message
```

### Status Bar

```
Room: #website-redesign • Team: 3 💻 🎨 👑
│                           │    │    │  └─ Coder
│                           │    │    └──── Creative
│                           │    └───────── Leader
│                           └─ Participant count
└──────────────────────────── Current room
```

---

## Common Workflows

### Workflow 1: Create Room + Invite Bots

```bash
[#general] You: /create marketing-campaign
✅ Created room #marketing-campaign

[#marketing-campaign] You: /invite researcher analyze market
✅ researcher invited

[#marketing-campaign] You: /invite creative design campaign
✅ creative invited

[#marketing-campaign] You: /status
Room: #marketing-campaign • Team: 3 👑 🧠 🎨

# Start working with the team
[#marketing-campaign] You: Let's brainstorm campaign ideas...
```

### Workflow 2: AI-Assisted Room Creation

```bash
[#general] You: I need to build an API for my mobile app

nanobot: 🔍 Analyzing task requirements...
Recommended: @coder, @researcher, @auditor
Create room #mobile-api? [Y/n]: y

✅ Team assembled: @coder, @researcher, @auditor
🔀 Switched to #mobile-api

[#mobile-api] You: What's the best approach for the API design?
```

### Workflow 3: Switch Between Projects

```bash
[#website-redesign] You: /switch marketing-campaign
🔀 Switched to #marketing-campaign

[#marketing-campaign] You: How's the campaign looking?
nanobot: The campaign is ready. The team has prepared...

[#marketing-campaign] You: /switch website-redesign
🔀 Switched to #website-redesign

[#website-redesign] You: Status check on the redesign
nanobot: The website redesign is progressing well...
```

---

## Tips & Tricks

1. **Quick Room Lookup**
   ```bash
   [#general] You: /switch
   # Displays available rooms without switching
   ```

2. **Get Help Anytime**
   ```bash
   [#any-room] You: /help
   # Shows all available room commands
   ```

3. **AI Recommendations**
   - Use natural language: "Create a room for..." 
   - AI analyzes your request and recommends bots
   - Accept or modify the recommendation

4. **Team Status**
   ```bash
   [#project] You: /status
   # See everyone in the current room
   ```

5. **Create Room Without Speaking**
   ```bash
   [#general] You: /create new-feature project
   [#new-feature] You: /invite coder
   # Manual room creation when AI isn't needed
   ```

---

## Keyboard Shortcuts

- **Arrow Up/Down** - Navigate command history
- **Ctrl+R** - Search command history
- **Ctrl+A** - Move to start of line
- **Ctrl+E** - Move to end of line
- **Ctrl+U** - Clear line
- **Ctrl+W** - Delete word

---

## FAQ

**Q: Can I create private rooms?**
A: Use `/create <name> direct` for private rooms between specific bots.

**Q: How do I remove a bot from a room?**
A: Currently not supported. You can create a new room without that bot.

**Q: Can I delete a room?**
A: The general room cannot be deleted. Other rooms are archived when empty.

**Q: How many bots can be in a room?**
A: All 6 bots can work together in a room.

**Q: Do rooms persist after closing the CLI?**
A: Yes! Rooms are saved and available the next time you start nanobot.

---

## Related Documentation

- **Design Document**: ADVANCED_CLI_UX_DESIGN.md
- **Implementation Status**: CLI_UX_IMPLEMENTATION_STATUS.md
- **Phase 1 Improvements**: PHASE1_IMPROVEMENTS.md

---

## Version

This guide covers nanobot with Phase 1 UI improvements (Feb 2026).

For the latest, run: `nanobot chat` and type `/help`
