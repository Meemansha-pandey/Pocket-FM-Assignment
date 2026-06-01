# PRD: Priority Micro-Adjust

**Source:** Linear (linear.app)  
**Author:** Nan Yu, Product Manager at Linear  
**Original:** https://www.linkedin.com/feed/update/urn:li:activity:7264312237106860033/  
**Status:** Shipped  

---

## Context

**Customer Messaging:** Make fine-grained adjustments to priority levels within basic categories. If you implement a stack-ranking system for your tasks and projects, this is specifically made for you.

---

## Problem

A very common use case we encounter is global stack-ranking: customers want to form a stable, opinionated order of priority across all of their backlog items. Today, we provide a global manual ordering feature, which we recommend for these cases.

There are several key issues with the current manual ordering system:

1. **Instability.** Manual sort is often unstable. Users often do not treat this ordering with care because it feels low-stakes. They often make changes without realising someone is relying on the ordering.
2. **Local vs. Global Sorting.** In other apps, manual sort is often local. Users are often surprised Linear has global manual ordering.
3. **Redundancy with Priority Field.** Linear currently has both a manual sort and a priority field. If the goal is to create a global priority stack rank, it is awkward to have a priority field that does not agree with your sort.

When users express these problems, it is often through indirect feature requests:

1. Requests for "custom priority levels" — because the 4 basic buckets (Urgent, High, Medium, Low) don't offer enough granularity.
2. Requests for custom fields to add a "ranking" column — essentially a numerical stack-rank.

---

## Solution

Priority levels are a natural fit for this, but today they are broad buckets and do not offer enough control for customers who want to literally rank every single item.

**We will allow users to adjust and rearrange the relative priority of their issues within a priority bucket, through drag-and-drop.**

Once shipped, we will strongly recommend that all stack-ranking use cases be achieved through priority + micro-adjust, replacing the current manual sort recommendation.

---

## Options Considered and Rejected

1. **Custom priority levels.** Does not solve for stack-ranking, and would encourage stack-rankers to create too many distinct categories — increasing cognitive load for teams.
2. **Custom fields.** Would solve for stack-ranking and many other asks, but is out of character for Linear. Linear's ease-of-use comes from opinionated defaults that reliably work the same everywhere.

---

## Prior Art

No other tool currently offers manual adjustment within priorities. Competing tools all take one of the two rejected options above. This is an opportunity to differentiate. Priority + micro-adjust tells a more compelling and cohesive story than either alternative.

---

## Usage Scenarios

### Scenario A — Project Priority Organisation

**User A** asks for priority on projects and more priority categories.

*With priority micro-adjust:* When User A wants to organise according to very specific priorities, she can drag issues and projects into the exact order she wants within the same priority level. This avoids the complexity of defining new priority levels and educating her team on what those levels mean. She can simply say: "this issue is higher priority than the other high-priority issues."

### Scenario B — Importance Ranking Without Custom Fields

**User B** proposes a mockup of issues ordered by a custom field called "importance" — an integer value defined per issue.

*With priority micro-adjust:* When User B wants to be specific about the relative importance of issues, he can rearrange them visually. This is less mentally taxing than assigning arbitrary integers and does not require explaining what those numbers mean to the rest of the team.

---

## Functional Requirements

### Drag-and-Drop Within Priority Buckets

- **FR-1:** When ordering by priority, users can drag and drop issues within the same priority bucket to determine fine-grained ordering.
- **FR-2:** The relative order within a priority bucket must persist across sessions, page refreshes, and devices.
- **FR-3:** Changes to micro-adjust ordering must be visible to all team members in real time.

### Cross-Priority Drag Behaviour

- **FR-4:** When an issue is dropped into a set of items with a different priority bucket, its priority changes to match the destination bucket.
- **FR-5:** When dropping an issue in between two priority buckets:
  - If the movement was upward, assign the lower priority of the two adjacent buckets.
  - If the movement was downward, assign the higher priority of the two adjacent buckets.

### Initialisation and Migration

- **FR-6:** On release, each user's initial micro-adjust ordering is bootstrapped from their existing manual sort index.
- **FR-7:** After bootstrapping, the manual sort index is deprecated as the primary stack-ranking mechanism.

### Coexistence with Priority Field

- **FR-8:** The priority field (Urgent / High / Medium / Low / No Priority) continues to function as the primary bucket.
- **FR-9:** Within each bucket, micro-adjust ordering is a secondary sort key.
- **FR-10:** The priority field and micro-adjust ordering must always be consistent — there must be no state where the two contradict each other.

---

## Non-Functional Requirements

- **NFR-1:** Drag-and-drop interactions must feel responsive — visual feedback must appear within 16ms of initiating a drag (60fps target).
- **NFR-2:** Order changes must be persisted to the server within 500ms of drop completion.
- **NFR-3:** Real-time sync of ordering changes to other active team members must occur within 2 seconds.
- **NFR-4:** The feature must support issue lists of up to 10,000 items without UI degradation.

---

## Milestones

### MS1 — Internal
- Implement drag-and-drop within a priority bucket.
- Handle priority changes when dropping between priority buckets (cross-priority drag rules).
- Internal testing with mockups and prototypes.

### MS2 — Beta
- Bootstrap initial micro-adjust ordering from existing manual sort index.
- Release to a limited set of beta users for validation.

### MS3 — General Availability + Changelog
- Release priority micro-adjust alongside project-level priorities.
- Announce together in a single changelog entry to tell a cohesive story about Linear's priority system.

---

## Out of Scope

- Custom priority level names or additional priority buckets beyond the current four.
- A numeric "rank" field visible on issue cards.
- Micro-adjust ordering on views other than the priority-sorted backlog (to be evaluated post-GA).
