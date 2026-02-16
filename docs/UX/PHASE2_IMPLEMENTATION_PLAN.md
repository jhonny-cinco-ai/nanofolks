# Phase 2: Medium Effort Improvements - Implementation Plan

**Status**: 🚀 IN PROGRESS  
**Date Started**: February 15, 2026  
**Estimated Duration**: 4-5 hours  
**Priority**: MEDIUM  

---

## Overview

Phase 2 builds on Phase 1 by integrating UI components into the interactive loop and adding visual feedback for better user experience. This phase focuses on **continuous display and feedback** rather than new commands.

---

## Phase 2 Features

### Feature 1: Sidebar Integration in Interactive Loop
**Goal**: Display team roster and room list continuously visible during chat  
**Scope**: Show after commands and room switches  
**Complexity**: Medium  
**Estimated**: 1 hour

**What it does**:
- After switching rooms, show team roster
- After running commands, show status
- Keep user aware of current room context
- Visual confirmation of actions

**Implementation Approach**:
- Use existing `TeamRoster.render()` and `RoomList.render()`
- Display after command execution
- Display after room switch
- No breaking changes to existing flow

### Feature 2: Display Team Roster After Room Switch
**Goal**: Automatically show team when room changes  
**Scope**: Interactive loop room switching  
**Complexity**: Low  
**Estimated**: 30 minutes

**Current Code**: Lines 1429-1440  
**Enhancement**: Already partially done! Just needs verification.

**What needs to be done**:
- Ensure roster displays consistently
- Format matches other displays
- Add to all room-switching scenarios

### Feature 3: Show Current Room in Status Bar
**Goal**: Display room context continuously in main display  
**Scope**: Top of interactive loop output  
**Complexity**: Medium  
**Estimated**: 1 hour

**What it does**:
- Shows current room prominently
- Shows team member count
- Shows emoji indicators
- Updates on room switch
- Part of command output

**Implementation**:
- Use `StatusBar.render()`
- Display after each command
- Display at top of room switch message
- Use compact inline format

### Feature 4: Add Visual Feedback (Spinners/Transitions)
**Goal**: Show activity/progress during operations  
**Scope**: Room creation, switching, etc.  
**Complexity**: Medium  
**Estimated**: 1.5 hours

**What it does**:
- Spinner during room creation
- Progress indicator for bot invites
- Transition message on room switch
- Checkmarks on completion

**Implementation**:
- Use Rich spinners (already available)
- Use `console.status()` for progress
- Add visual separators

### Feature 5: Enhanced Room Creation UX
**Goal**: Better guided room creation experience  
**Scope**: AI-assisted and manual creation  
**Complexity**: Medium  
**Estimated**: 1 hour

**What it does**:
- Room templates (website, api, ml-model, etc.)
- Show bot skills/availability
- Let user customize selections
- Better confirmation flow

---

## Implementation Details

### Task Breakdown

#### Task 1: Sidebar Integration (1 hour)

**File**: `nanofolks/cli/commands.py`  
**Target**: Interactive loop after command execution

**Changes needed**:
1. Create helper function `_display_room_context()`
   - Takes current_room
   - Displays status bar
   - Displays team roster
   - Returns formatted output

2. Call after each command that affects room state
   - After `/switch`
   - After `/invite`
   - After `/create`
   - After room creation from AI

3. Consistency: Use same format everywhere

**Pseudo-code**:
```python
def _display_room_context(room, room_manager):
    """Display current room context (status bar + team roster)."""
    # Status bar
    status_bar = StatusBar()
    bot_emojis = TeamRoster().render_compact_inline(room.participants)
    status = status_bar.render(room.id, len(room.participants), bot_emojis)
    console.print(f"\n{status}\n")
    
    # Team roster
    roster = TeamRoster()
    roster_display = roster.render(room.participants, compact=False)
    console.print(roster_display)
    console.print()
    
    return (status, roster_display)

# Use in commands:
# After switch:
console.print(f"🔀 Switched to #{new_room_id}\n")
_display_room_context(new_room, room_manager)

# After invite:
console.print(f"✅ {bot_name} invited\n")
_display_room_context(current_room, room_manager)
```

#### Task 2: Team Roster After Switch (30 min)

**Status**: Already mostly done in Phase 1!  
**Verification**:
- Check lines 1429-1440 in commands.py
- Confirm roster displays after every switch
- Test all switch scenarios

**What's left**:
- Verify it works in all cases
- Test with empty rooms
- Test with multiple bots

#### Task 3: Status Bar Integration (1 hour)

**File**: `nanofolks/cli/commands.py`  
**Target**: Key output points

**Where to add**:
1. After room creation
   ```python
   console.print(f"\n✅ Created #{room_name}\n")
   _display_room_context(room, room_manager)
   ```

2. After room switch
   ```python
   console.print(f"\n🔀 Switched to #{new_room}\n")
   _display_room_context(room, room_manager)
   ```

3. After inviting bot
   ```python
   console.print(f"\n✅ Invited @{bot}\n")
   _display_room_context(room, room_manager)
   ```

4. In status command (already done)

#### Task 4: Visual Feedback with Spinners (1.5 hours)

**File**: `nanofolks/cli/commands.py`  
**Dependencies**: Rich `Status` and `Progress`

**Add spinners to**:
1. Room creation
   ```python
   with console.status("[cyan]Creating room...[/cyan]", spinner="dots"):
       new_room = room_manager.create_room(...)
   console.print("✅ Room created!")
   ```

2. Bot invitation
   ```python
   with console.status(f"[cyan]Inviting @{bot}...[/cyan]", spinner="dots"):
       result = room_manager.invite_bot(room_id, bot_name)
   console.print(f"✅ @{bot} invited!")
   ```

3. Room switching
   ```python
   with console.status(f"[cyan]Switching to #{room}...[/cyan]", spinner="dots"):
       new_room = room_manager.get_room(room)
   console.print("✅ Switched!")
   ```

#### Task 5: Enhanced Room Creation (1 hour)

**File**: `nanofolks/cli/commands.py`  
**Target**: `_handle_room_creation_intent()` function

**Enhancements**:
1. Room templates
   ```python
   ROOM_TEMPLATES = {
       "website": {
           "type": "project",
           "description": "Build a website",
           "recommended_bots": ["coder", "creative", "researcher"]
       },
       "api": {
           "type": "project",
           "description": "Build an API",
           "recommended_bots": ["coder", "auditor", "researcher"]
       },
       "ml-model": {
           "type": "project",
           "description": "Build an ML model",
           "recommended_bots": ["researcher", "coder", "auditor"]
       },
       # ... more templates
   }
   ```

2. Bot skill display
   ```python
   BOT_SKILLS = {
       "researcher": ["Market research", "Competitive analysis", "Data gathering"],
       "coder": ["Development", "Debugging", "Architecture"],
       # ... etc
   }
   
   # Show skills when recommending
   for bot in recommended_bots:
       console.print(f"  {emoji} @{bot}: {', '.join(BOT_SKILLS[bot])}")
   ```

3. Custom selection option
   ```python
   # After recommendation:
   if Confirm.ask("Customize team selection?", default=False):
       # Show available bots with skills
       # Let user select which to invite
   ```

---

## Implementation Order

### Phase 2a: Quick Integration (1.5 hours)
1. ✅ Create `_display_room_context()` helper
2. ✅ Integrate into room switch
3. ✅ Integrate into room creation
4. ✅ Integrate into invite command
5. ✅ Test all scenarios

### Phase 2b: Visual Feedback (1.5 hours)
6. ✅ Add spinners to room creation
7. ✅ Add spinners to bot invitation
8. ✅ Add spinners to room switching
9. ✅ Test spinners in different terminals
10. ✅ Verify Rich integration

### Phase 2c: Enhanced Room Creation (1 hour)
11. ✅ Add room templates
12. ✅ Add bot skills display
13. ✅ Add custom selection option
14. ✅ Update documentation

### Phase 2d: Polish & Testing (30 min)
15. ✅ End-to-end testing
16. ✅ Edge case handling
17. ✅ Documentation updates
18. ✅ Create Phase 2 improvements document

---

## Testing Checklist

### Feature 1: Sidebar Integration
- [ ] Team roster displays after `/switch`
- [ ] Team roster displays after `/create`
- [ ] Team roster displays after `/invite`
- [ ] Status bar shows correct room and count
- [ ] Status bar updates on room change
- [ ] Empty rooms handle correctly
- [ ] Many bots handle correctly

### Feature 2: Team Roster Display
- [ ] Shows after every room switch
- [ ] Shows current room marker (→)
- [ ] Shows emoji indicators
- [ ] Format is consistent
- [ ] Works with 1-6 bots

### Feature 3: Status Bar
- [ ] Shows room name
- [ ] Shows participant count
- [ ] Shows emoji indicators
- [ ] Updates correctly
- [ ] Formatting is clean

### Feature 4: Visual Feedback
- [ ] Spinner shows during room creation
- [ ] Spinner shows during invite
- [ ] Spinner shows during switch
- [ ] Spinner disappears on completion
- [ ] Works in multiple terminals
- [ ] Works with slow operations

### Feature 5: Enhanced Creation
- [ ] Templates show in recommendations
- [ ] Bot skills display correctly
- [ ] Custom selection works
- [ ] Selection updates team
- [ ] Templates are useful

---

## Code Locations

### New Functions to Add
- `_display_room_context(room, room_manager)` - Sidebar display helper
- `_show_spinner()` - Visual feedback helper (optional, use console.status)

### Files to Modify
- `nanofolks/cli/commands.py` - Main implementation

### Existing Components to Leverage
- `TeamRoster.render()` - Team display
- `StatusBar.render()` - Status display
- Rich `Status` - Spinners
- Rich `Console.status()` - Progress indication

---

## Documentation Plan

### Create:
- `PHASE2_IMPROVEMENTS.md` - Detailed implementation notes
- `PHASE2_TESTING_RESULTS.md` - Testing verification

### Update:
- `CLI_UX_IMPLEMENTATION_STATUS.md` - Mark Phase 2 complete
- `ROOM_COMMANDS_QUICK_REFERENCE.md` - New visual examples

---

## Success Criteria

✅ All 5 features implemented  
✅ Team roster shows on room operations  
✅ Status bar displays correctly  
✅ Spinners show during operations  
✅ Room templates work  
✅ All tests pass  
✅ Documentation updated  
✅ No breaking changes  
✅ Backward compatible  

---

## Risk Assessment

**Risk Level**: LOW

**Why**:
- Uses existing UI components
- No new dependencies
- All code in single file
- Easy to test
- Can rollback easily

**Potential Issues**:
- Terminal compatibility with spinners → Handled by Rich
- Performance during status display → Minimal impact
- Format consistency → Use helper functions

---

## Timeline

| Phase | Duration | Start | End |
|-------|----------|-------|-----|
| 2a: Integration | 1.5 h | Now | ~30 min |
| 2b: Visual Feedback | 1.5 h | ~30 min | ~1.5 h |
| 2c: Enhanced Creation | 1 h | ~1.5 h | ~2.5 h |
| 2d: Polish & Test | 30 min | ~2.5 h | ~3 h |
| **Total** | **~3 hours** | | |

Could be done in 3-4 hours with 1-2 person team.

---

## Next: Let's Build Phase 2!

Ready to implement? Here's the plan:

1. Create `_display_room_context()` helper
2. Integrate into room operations
3. Add spinners for visual feedback
4. Enhance room creation
5. Test everything
6. Document results

Should we start with Task 1 (Sidebar Integration)?
