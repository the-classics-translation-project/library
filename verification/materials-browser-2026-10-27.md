# Deployed Admin ordered-material check — 2026-10-27

The merged PR #19 Pages workflow [run 40358969727](https://github.com/the-classics-translation-project/library/actions/runs/40358969727)
completed its build and deployment successfully. The browser check below used
the deployed `https://the-classics-translation-project.github.io/library/admin/index.html`
in a real in-app browser. It was not a simulated DOM test or a physical Safari/iPad
check.

1. Loaded Admin. In the Wells Japanese ordered-material selector, added the public editorial
   policy and Wells source notes. The Applied list displayed both in order.
2. Moved the second material above the first, then removed it. The displayed
   order and counts changed accordingly.
3. Reloaded Admin; the unsent material selection reset. Expanded the Wells
   source tree through Book One, selected chapter II (`n0005`), and saw one
   selected source node. No Issue was submitted.
4. Added both public materials again and inspected the prepared link. Its v2 Issue payload pinned
   `policy.editorial@577af62722684df0b70be624e47ee944409afcd552d265c1b16121697c2c55da`
   followed by
   `notes.work.gutenberg-36@185722e402f9b70035a913760c5e736d7e8d6b3b16ed97834fe9bba9daea9c02`.
5. The public Available list contained committed policy and source notes. It
   did not expose the locally imported, uncommitted Wells guides; their public
   guide status still said not generated.

Unsent selection resets on reload. Reusable stacks and cross-reload form
restoration are not part of the initial implementation.

The check verifies deployed UI controls and generated URL data. It does not
verify GitHub Issue submission/intake, relay processing, private full-input
preview, literary quality or physical-device behavior.
