# EyeTrack Lab online demo

URL: https://eyetrack-lab-demo-hathairat.hathairat-sss.chatgpt.site

Source: https://github.com/hathairat-sgw/eyetrack-lab (existing private repository; visibility unchanged).

## Behavior

The static browser demo is separate from the Python/FastAPI/Tobii research runtime. It uses the original track table, questionnaire configuration, Practice and QuestionnaireForm components. It supports P001-P030, explicit demo consent, five-point calibration rehearsal, four practice interactions, Pre-test, four native playground tasks, Post-test, browser-local progress/draft resume and ZIP export of the nine required files.

No gaze samples are synthesized. gaze.csv contains a header only. Mouse coordinates are real DOM click/down/up events inside the playground, in viewport CSS pixels. Experiment controls and practice are excluded. The native playground is the same engineering fixture across rounds, not a validated recreation of every Figma condition. Figma links are reference-only, unverified and not instrumented. Do not use this version for research collection.

Only localStorage is used for answers/progress (`eyetrack-lab-online-demo-v1`). Each visitor has a separate browser dataset; it is not a central research database. Use fictitious answers. The Site is owner-private by default and may require the owner's ChatGPT sign-in. Participant data, backups and runtime credentials are not in GitHub or the published bundle.

## Local preview/build

```powershell
cd frontend
npm.cmd ci
npm.cmd run demo
# http://127.0.0.1:5180
npm.cmd run build:demo
# static output: ../web-dist
```

The regular `npm run build` and VS Code Run All still build/run the original research system.

## Tests

```powershell
node --test tests/test_web_demo.mjs
node scripts/ui-web-demo.mjs
```

Node tests cover guards, all 30 participants completing four trials, no fabricated gaze, nine-file exports and draft conflict/reload. Chrome test covers the complete participant flow, ZIP download, reload and 390px mobile layout. ZIP files are also checked with Python zipfile.

## Hosting

GitHub Pages setup returned HTTP 422: the account's current plan does not support Pages for this private repository. Repository visibility was not changed. The optional `.github/workflows/demo-pages.yml` is manual-only for future use when Pages is enabled; it does not publish by pushing code.

Current hosting is a static Sites project. Site identity: `appgprj_6b014ee2dac88191b8c8460073467e09`. Dedicated deployment checkout is under `work/sites/eyetrack-lab-demo-20261121` and is ignored by the main Git repository. It contains only the static demo build and hosting manifest. Rebuild the demo and publish a new Sites version to update the deployed copy. Short-lived deployment credentials are never committed.

## Research system

For real Tobii collection use the local Windows application and approved protocol, calibrated device, independently verified mapping/timing and storage backup. Online Demo never claims a connected or calibrated hardware device.
