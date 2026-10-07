# Phase 4 chat scrolling repair — 2026-10-04

1. **Citizen experience:** mouse-wheel scrolling over action cards now moves the
   conversation, as it does over messages. The composer remains visible.
2. **Root cause:** the shared action panel added a desktop sticky, height-limited
   overflow container with overscroll containment inside the conversation scroller.
   Wheel events over the panel could be trapped instead of moving chat history.
3. **Decision:** remove the panel's nested scrolling/sticky layout; its parent
   conversation viewport or intentionally opened detail pane owns scrolling.
4. **Frontend:** changed only the action panel's layout classes and added a browser
   regression check. Removed the temporary test server's generated tsconfig include;
   retained existing Phase 4 settings and other user changes.
5. **Backend/domain/AI:** none.
6. **Database/storage:** none; mocked synthetic case data, no stored uploads/cases.
7. **API/contracts:** none.
8. **Security/privacy:** existing ownership, facts, action selection and file
   boundaries unchanged. The browser test makes no live model calls.
9. **Tests:** `frontend/__tests__/phase4-scroll.cjs` checks wheel scrolling over an
   action card and message history at 1280px and 390px widths, detail-pane scrolling,
   draft preservation and composer visibility. It failed on the desktop action-card
   assertion before the fix and passed afterward.
10. **Verification:** commands actually run:

    - From `frontend`: `$env:CYBERSOS_BUILD_DIR='.next-scroll'; node node_modules/next/dist/bin/next dev --port 3002`.
      Started an isolated frontend; stopped that session after verification. No user
      service was restarted. Development compilation emitted Newsreader font-override
      warnings; the route compiled and rendered.
    - From the repository root:
      `$env:PLAYWRIGHT_PACKAGE='C:/Users/Ishan Chennupati/AppData/Local/Programs/Python/Python313/Lib/site-packages/playwright/driver/package'; $env:SMOKE_FRONTEND_URL='http://localhost:3002'; node frontend/__tests__/phase4-scroll.cjs`.
      Failed before repair, passed after repair. Headless browser/server subprocesses
      required sandbox escalation. An initial attempt at localhost:3000 found no
      running frontend, so verification used port 3002.
    - From `frontend`: `npm run lint` — passed, no warnings/errors.
    - From the repository root: `git diff --check -- frontend/components/conversation-action-panel.tsx frontend/__tests__/phase4-scroll.cjs frontend/tsconfig.json docs/phase4-scroll-repair.md` — passed.
11. **Live provider:** not run; synthetic mocked API response used for layout checks.
12. **Manual journey:** open a conversation with enough messages/actions to overflow;
    wheel up/down with the pointer over message text and the ACT NOW card. Open View
    case and scroll its details; verify the composer and unsent draft remain usable.
13. **Limitations:** desktop/mobile viewport browser checks do not establish physical
    touchscreen or every browser/device behavior. No full production build or broad
    live AI evaluation was needed for this layout-only repair.
14. **Roadmap impact:** NO CHANGE. Phase 5 enhancements remain separate planned work.
15. **Core check:** preserved chat-first experience, no form-first intake, AI
    investigation, deterministic critical actions, self-building case, truthful
    external status and official-handoff compatibility.
