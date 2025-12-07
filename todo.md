# Todo List

## Calendar Page
- [x] Fix filter reset: when returning to tasks page from archive filter, URL remains `/?team=archive` instead of resetting or switching to `/?mode=active`
- [x] Enhance team filter: show tasks for all team members, not just tasks assigned to the team entity (affects week view and members view)
- [x] Fix styling: add border line between Sunday and Monday

## Tasks Page
- [x] Style: avatars quick filter should float to the left
- [x] UX: when hovering the "notes" icon, show tooltip with task notes (truncate to 5 lines + "..." if long)

## Print Page
- [x] Logic: do not display archived tasks in print view
- [x] Feature: allow printing tasks of a specific team (add team filter to print page)

## Layout & Design
- [x] Navbar: remove live clock, display date in dd/mm/yyyy format instead
- [x] UI: improve archive button design (current blue/red combination is unreadable when active)