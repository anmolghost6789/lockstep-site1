# Quick start

1. **Add the pack to your repository.** Install it from the Lockstep registry through the extension, or copy the pack folder into the repo root.
2. **Set up gates once.**
   ```bash
   python3 .claude/skills/adlc/scripts/setup_codeowners.py
   ```
   Commit `.github/CODEOWNERS`, then apply the branch protection settings the script prints.
3. **Point roles at your teams.** Edit `config/governance/gate_roles.json > github_teams`, then re-run the script.
4. **Write the intent.** Put the business goal in `inputs/instructions/intent.md`. One or two sentences: the outcome, for whom, and any hard constraint.
   > Cut KYC review from 3 days to same-day, with an analyst signing off every high-risk case.
5. **Run phase 01.** In Copilot Chat: `@lockstep discover`. In Claude Code: `/discover-define`.
6. **Approve it.** A product owner reviews the gate pull request and approves it. Merging passes G1.
7. **Continue.** Run phase 02 the same way, and so on through phase 06.

At any point, `/status` (or `@lockstep status`) shows where the run is and what to do next.

Next: [Phases](../workflow/phases.md).
