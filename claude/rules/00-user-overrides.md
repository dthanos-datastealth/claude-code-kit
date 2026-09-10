# Your overrides

This file is yours. The kit seeds it once, empty, and never writes it again —
not on upgrade, not on reinstall.

Every kit rule file ends by saying that whatever is in here wins. So to change
how the kit behaves, state the change here rather than editing a kit rule file:
an edit to a kit file is overwritten on the next upgrade, and an instruction
here is not.

Be specific about what you are overriding. "Skip the V+O loop for docs-only
changes" is actionable. "Be less strict" is not.

<!-- Example:
## Quality loop
- Docs-only changes skip the V+O loop. Code changes never do.
-->
