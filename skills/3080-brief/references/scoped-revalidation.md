# Scoped Revalidation

Use this after a candidate has any independent review result and is then changed. The goal is to preserve valid evidence, rerun only what can have changed, and stop as soon as the affected scope passes.

## Review layers

Keep separate hashes for:

- `source`: source snapshot, inventory, ledger, outline, and excerpts.
- `content`: TLDR and canonical brief/body inputs.
- `visual`: visual specification and the cropped one-picture render.
- `layout_desktop`: desktop full-page render.
- `layout_mobile`: mobile full-page render or targeted mobile evidence.

Geometry reports, replay reports, and reviewer JSON are validation evidence,
not rendered inputs. Put them in the scoped receipt or baseline review record;
otherwise a validator upgrade can be mistaken for a reader-visible layout change.

Do not use the final HTML hash alone to invalidate every prior result. The final file is a package; the layers above determine which reader judgment could have changed.

## Required scope

| Changed layer | Required rerun | Reusable when previously PASS |
| --- | --- | --- |
| Source or content | All deterministic gates, replays, and Reader/Source/Visual audit | None |
| Core visual only | Visual gates/replay, full render, Blind Reader, Reader and Visual audit | Source audit |
| Desktop layout only | Target validator, desktop geometry, full-page replay, desktop visual review | Reader and Source audit |
| Mobile layout only | Target validator, mobile geometry, mobile visual review | Reader, Source, desktop replay, and unchanged core-visual replay |
| Publication placement only | Write preflight and live-target verification | All artifact reviews |

Use the union when multiple layers changed. A failed or missing prior review cannot be reused; add that role to the required scope.

## Executable flow

1. After a review batch, create a baseline manifest with `scripts/plan_review_scope.py snapshot` and attach the available Reader/Source/Visual reports.
2. After editing and rendering, create a current manifest from the same named inputs.
3. Run `plan_review_scope.py plan`. Do not add checks that the plan does not require unless a new concrete risk appears.
4. Record only the required results in a receipt bound to `plan_id`, then run `plan_review_scope.py verify`.
5. When verification passes, stop the review loop and proceed to publication. Do not start a fresh full batch for reassurance.

Example receipt:

```json
{
  "schema_version": 1,
  "plan_id": "<plan id>",
  "checks": {
    "target_validator": "PASS",
    "mobile_geometry": "PASS",
    "mobile_visual_review": "PASS"
  },
  "reviews": {}
}
```

At most two targeted repair rounds may follow the first complete audit batch. If the affected scope still fails, deliver the current version with the unresolved issues and ask the user whether to continue. Missing source, intent, permission, or external state stops immediately rather than consuming a retry.
