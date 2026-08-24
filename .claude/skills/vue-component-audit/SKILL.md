---
name: vue-component-audit
description: Analyzes Vue 3 component structure across client/src and reports performance and code-reuse optimization opportunities. Use when the user asks to analyze, audit, or review Vue components/composables for performance issues, unnecessary re-renders, prop drilling, or duplicated logic/markup that could be extracted into a shared component or composable.
---

# Vue Component Structure Audit

Produces a **read-only findings report** on Vue component structure. This skill never edits files — if the user wants fixes applied afterward, hand the accepted findings to the `vue-expert` subagent (CLAUDE.md requires any `.vue` create/edit go through it).

## Scope

Default scope, unless the user names specific files:
- `client/src/views/*.vue`
- `client/src/components/*.vue`
- `client/src/composables/*.js`

Skip `node_modules`, build output, and test files.

## Procedure

1. List the files in scope and read each one fully (don't rely on partial reads — truncated reads miss issues in the tail of larger files).
2. Run the checks below across all files. Prefer `grep -n` for the mechanical patterns, then read the surrounding context to confirm it's a real issue (not a false positive, e.g. a deliberate `watch` with side effects).
3. For **Code Reuse**, compare files against each other, not just within one file — duplication only shows up cross-file (e.g. `client/src/components/*Modal.vue` often share layout/logic worth pulling into a base modal component or a composable).
4. Rank findings by severity and report using the format in "Output" below. Do not modify any files.

## Performance Checks

| Check | How to spot it | Why it matters |
|---|---|---|
| Index as `:key` in `v-for` | `grep -n ':key="index"\|:key="i"\|v-for="(.*, i)'` | Breaks reordering/insertion; use a stable id (`item.sku`, `item.id`) |
| Method calls in template instead of `computed` | `{{ someMethod() }}` or `:prop="calc()"` in `<template>` | Re-runs every render instead of caching; convert to `computed()` |
| Derived arrays/objects built in template or in `onMounted` instead of `computed` | filtering/mapping/sorting logic inline in template, or written once into a `ref` that never reacts to source changes | Loses reactivity or wastes cycles recomputing when it should be cached |
| Missing loading/error state handling | component fetches data but template has no `v-if="loading"` / `v-else-if="error"` | Matches project pattern in CLAUDE.md; absence usually means janky UX during async work, not just style |
| Unvalidated date parsing | `new Date(x).getMonth()` etc. without an `isNaN(date.getTime())` guard first | Crashes/NaN propagation on bad data (documented project pitfall) |
| Prop mutation | `props.x.push(...)`, `props.x.value = ...`, direct assignment to a prop | Breaks one-way data flow; should `emit` instead |
| Watchers doing work a computed should do | `watch(source, () => { derived.value = ... })` where `derived` is purely a function of `source` | Extra indirection and a render lag vs. `computed` |
| Large inline SVG/chart logic recomputed without memoization | chart coordinate math inline in template rather than `computed` | Recalculated every re-render for no reason |
| Oversized single-file component | file > ~300 lines, or `<script setup>` mixing 3+ unrelated concerns | Harder to reason about; usually reuse or split opportunity below applies |

## Code Reuse Checks

| Check | How to spot it | Why it matters |
|---|---|---|
| Duplicated markup across components | similar `<template>` blocks (e.g. modal shells in `components/*Modal.vue`, filter chips, table headers) appearing in 2+ files | Candidate for a shared component (e.g. `BaseModal.vue`) |
| Duplicated logic across views/components | same fetch/error/loading boilerplate, same filter-computed pattern, same formatting helper reimplemented per file | Candidate for a `composables/use*.js` extraction, alongside existing ones like `useFilters`, `useSidebar` |
| Ad hoc formatting instead of shared util | inline `.toFixed(2)`, manual currency/number formatting instead of using `utils/currency.js` | Should reuse the existing utility instead of reimplementing |
| Repeated API-shape handling | same `getCurrentFilters()` + try/catch/loading dance copy-pasted per view | Extract into a small composable (e.g. `useAsyncData(fetcher)`) |
| Local state duplicating a composable's job | component-local `ref` reimplementing something `useFilters`/`useAuth`/`useI18n` already exposes | Should consume the existing composable instead |

## Output

Report findings grouped into **Performance** and **Code Reuse**, most severe first. For each finding include:

- `file:line`
- One-sentence summary of the problem
- Why it matters (concrete consequence, not just "best practice")
- A short suggested fix (code snippet or one-line description)

End with a one-line count summary (e.g. "6 performance, 3 reuse — 2 high severity"). Do not pad the report with issues that don't reproduce a real consequence — a `v-for` over a hardcoded 3-item static array with an index key is not worth flagging.

If the user then asks to apply fixes, do not edit `.vue` files directly — delegate to the `vue-expert` subagent with the specific accepted findings.
