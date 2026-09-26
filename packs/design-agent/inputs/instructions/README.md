# Instructions

Place run-specific user instructions here. Recommended file name pattern: `user_instructions.*`.

These files are parsed as the narrowest context tier and apply only to the current run. They may include free-form directives such as preferred modeling choices, source-use instructions, naming overrides, exclusions, or special output expectations.

The agent parses these files into `user_instructions.json`, breaks free-form content into discrete directives, tracks directive status across stages, and asks for confirmation before applying any instruction that conflicts with higher-tier context or current evidence.

Do not place enterprise, domain, or project guidance here; those belong under root `context/guidance/`.
