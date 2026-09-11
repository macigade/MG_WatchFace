# Instrument 480 — Watch Face Build Handoff

Hand this whole file to a fresh Claude Code session. It is the complete spec for turning the
HTML mockup (`Galaxy Watch 7 Face.dc.html` + `Watch Dial.dc.html`) into an installable
Galaxy Watch 7 watch face.

---

## 0. Starting prompt

> Build a Wear OS 5 watch face for the Galaxy Watch 7 (480×480 round) from the spec in
> `HANDOFF-watchface.md`. Use **Watch Face Format (WFF) v2**, declarative XML only — no
> Kotlin runtime code. Produce a Gradle project that assembles a signed APK I can sideload
> with `adb install`. Implement **Layout A** first, then add **Layout C** as a second
> user-style variant. Ask me before inventing any value the spec does not give.

---

## 1. Target & toolchain

| Item | Value |
| --- | --- |
| Device | Galaxy Watch 7, 44 mm — 480 × 480 px round, AMOLED |
| OS | Wear OS 5 (One UI Watch 6) |
| Format | Watch Face Format v2 (`res/raw/watchface.xml`) |
| Alt path | Samsung Watch Face Studio ≥ 1.7 if a GUI build is preferred |
| Min SDK | 33 · target 34 · `com.google.wear.watchface.format.version` = 2 |
| Install | `adb connect <watch-ip>:5555` then `adb install -r face.apk` |

Project skeleton:

```
app/
  src/main/
    AndroidManifest.xml          <!-- WatchFaceService meta-data, no Activity -->
    res/raw/watchface.xml        <!-- the entire face -->
    res/drawable-nodpi/          <!-- pre-rendered curved text + weather glyphs -->
    assets/fonts/Archivo-Bold.ttf
```

---

## 2. Canvas & grid

- Design space **480 × 480**, origin top-left, center `240,240`. All numbers below are px at
  480; scale linearly for other sizes.
- Safe circle for text: **r ≤ 200**. Nothing but tick marks past r 200.
- Type minimum **20 px**; tap targets **≥ 44 px**.

### Fixed chrome (both layouts)

| Layer | Geometry | Token |
| --- | --- | --- |
| Minute track | inset 8 · r 224–232 · 60 marks × 0.5° | `tick` |
| Hour track | inset 8 · r 214–232 · 12 marks × 1.4° | `tick.hour` |
| 12 index | x 239, y 10 · 2 × 22 | `accent` |
| Seconds index | r 222 · ø 8 dot · rotates 6°/s (step, not sweep) | `accent` |
| Bezel focus sector | inset 8 · r 216–232 · 16° | `accent` (editor/select state only) |

---

## 3. Design tokens

Ship **Swiss** as the default; the other four are user styles (`UserStyleSetting` of type
`ListUserStyleSetting`, id `style`).

| Token | Swiss | Mission | Editorial | Bauhaus | Stealth |
| --- | --- | --- | --- | --- | --- |
| `bg` | `#0A0A0B` | `#060806` | `#0B0A08` | `#111110` | `#000000` |
| `ink` | `#F2F2F0` | `#DCE8D4` | `#F6F0E6` | `#F8F5ED` | `#CDD0D3` |
| `dim` | `#8C8F93` | `#8AA283` | `#A29684` | `#B4AEA0` | `#65686B` |
| `track` | `#2A2D31` | `#1E2A1A` | `#332C24` | `#2A2926` | `#16181A` |
| `tick` | `#3E4247` | `#2A3A24` | `#453C30` | `#35342F` | `#1E2124` |
| `tick.hour` | `#6A6E73` | `#4E6644` | `#70624E` | `#5A5850` | `#3A3E41` |
| `accent` | `#4A9EDB` | `#E0A33A` | `#D6B25E` | `#E0623A` | `#EDEFF1` |
| AOD ink / dim | `#8E9195` / `#5E6165` | `#8BA284` / `#5C7256` | `#9C9080` / `#6A6052` | `#A29C90` / `#6E6A60` | `#8A8D90` / `#55585B` |

`low` state warning color, all styles: **`#E0A33A`**.

### Type

Bundle TTFs in `assets/fonts/`. Numerals are a second user style (`ListUserStyleSetting`, id `numerals`).

| Style id | Family | Weight | Tracking |
| --- | --- | --- | --- |
| `archivo` (default) | Archivo | 700 | −0.04em |
| `barlow` | Barlow Condensed | 500 | +0.01em |
| `saira` | Saira | 600 | −0.02em |
| `jet` | JetBrains Mono | 600 | −0.02em |
| `bebas` | Bebas Neue | 400 | +0.01em |
| `playfair` | Playfair Display | 600 | −0.015em |

UI/label text is always **Archivo** regardless of numeral style. Label convention: uppercase,
letter-spacing 0.10–0.16em, weight 500–600.

---

## 4. Slot model

Eight user-configurable slots. Each is a WFF **ComplicationSlot** where a real data source
exists, otherwise a bound data expression.

| # | Zone name | Default | Data |
| --- | --- | --- | --- |
| 0 | Top strip | Day / date | `[DAY_OF_WEEK_F] [DAY]` → "FRIDAY 11", uppercase |
| 1 | Below time | Weather forecast strip | 3 × complication, see §6 |
| 2 | Primary A | Steps | `[STEP_COUNT]`, goal 10 000 |
| 3 | Primary B | Battery % | `[BATTERY_PERCENT]` |
| 4 | Secondary A | Alarm | `[ALARM_TIME]` / SHORT_TEXT complication |
| 5 | Secondary B | Timer | SHORT_TEXT complication (Clock) |
| 6 | Minor | Sunset | SHORT_TEXT complication (Weather) |
| 7 | Icon tile | Wallet | SMALL_IMAGE, tap → user-set URI |

Swappable catalog for every slot: day/date, weather, steps, battery %, heart rate, alarm,
wallet, timer, sunrise/sunset, next event, sleep score, alerts.

Abbreviations used on the rim (3 chars): `DAY WX STP BAT HR ALM PAY TMR SUN CAL SLP ALR`.

---

## 5. Layout A — "Instrument" (default)

| Layer | Geometry | Type |
| --- | --- | --- |
| Arc gauge, slot 2 | inset 40 · r 192–200 · 60° sweep starting **240°** | fill `accent` on `track` |
| Arc gauge, slot 3 | inset 40 · r 192–200 · 60° sweep starting **60°** | fill `accent` on `track` |
| Arc readout, slot 2 | curved on r 176, centered at 9 o'clock | label 13/500/1.4px + value 19/700 |
| Arc readout, slot 3 | curved on r 176, centered at 3 o'clock | same |
| Rim readout, slot 4 | curved on r 198, centered at **315°** | abbr 12/600/1.6px `dim` + value 14/700 `ink` |
| Rim readout, slot 5 | curved on r 198, centered at **45°** | same |
| Top strip, slot 0 | y 64, centered | 23 / 600 / 0.16em caps, `ink` |
| Hairline | x 166, y 106 · 148 × 1 | `track` |
| Time | y 118, centered · line-height 1.16 | 100 / weight per style / tracking per style |
| Colon | — | `dim` while digits are `ink` |
| Forecast strip, slot 1 | y 248 · 3 items · gap 26 | icon 26 + temp 17/700 + hour 11/500/0.1em |
| Minor row, slot 6 | y 334, centered · gap 9 | label 14/500/0.14em `dim` + value 19/700 `ink` |
| Icon tile, slot 7 | x 216, y 366 · 48 × 48 · radius 14 · 1px `track` border | glyph 28 wide, `accent` |
| Status band | y 412 · pill · pad 8/18 · radius 999 | 13 / 600 / 0.14em caps |

Arc fill fraction = value ÷ goal, clamped 0–1, mapped onto the 60° sweep.

## 6. Layout C — "Orbit" (second variant)

Same chrome; all four secondary readouts move to the rim, center holds time only.

| Layer | Geometry | Type |
| --- | --- | --- |
| Rim, slot 2 | r 198 · centered **315°** | abbr 13/600 + value 16/700 |
| Rim, slot 3 | r 198 · centered **45°** | same |
| Rim, slot 4 | r 198 · centered **225°**, glyphs upright (reversed path) | same |
| Rim, slot 5 | r 198 · centered **135°**, reversed path | same |
| Top strip, slot 0 | y 130, centered | 21 / 600 / 0.16em caps |
| Time | y 162, centered · line-height 1.14 | 96 / style weight |
| Forecast strip, slot 1 | y 284 · 3 items · gap 24 | icon 20 + temp 15/700 (no hour label) |
| Minor row, slot 6 | y 326, centered · gap 9 | label 12/500/0.14em + value 17/700 |
| Icon tile, slot 7 | x 216, y 358 · 48 × 48 · radius 14 | glyph 28, `accent` |

**Curved text in WFF:** there is no arc-text primitive. Either (a) pre-render each readout to a
PNG per style/value — only viable for static labels — or (b) place the abbreviation as a
rotated `PartText` per character along the arc, or (c) build this face in Watch Face Studio,
which has a native curved-text element. Recommended: **(c) for curved text, WFF for the rest**,
or fall back to straight text tangent to the rim if the build must stay pure WFF. Flag the
choice back to me before implementing.

---

## 7. Weather forecast strip (slot 1)

Three upcoming hours, left → right: hour +1, +2, +3.

- Icon set matches the stock watch weather app: **filled sun disc with 8 rays**, **outlined
  cloud**, **cloud + 3 diagonal rain strokes**, **sun peeking behind cloud**. Sun disc and rain
  strokes take `accent`; cloud outlines take `ink`, 2 px stroke, round caps/joins.
- Each item: icon (26 px in A, 20 px in C) · temp `17/700` · hour `11/500/0.1em` `dim`.
- Whole strip is one tap target → weather app.
- No standard WFF forecast data source exists. Use three SHORT_TEXT + SMALL_IMAGE
  complication slots bound to the system weather provider, or read the provider's own
  complication if Samsung Weather exposes one. If neither is available, degrade to a single
  current-conditions complication and tell me.

If slot 1 is switched away from weather, render a single value instead: value `32/700` + label
`15/500/0.12em`, centered, at y 262 (A) / y 284 (C).

---

## 8. Tap targets

Every readout is tappable. Tap opens the app directly on device; the mockup's detail card is a
presentation device, not a requirement.

| Slot | Launch target |
| --- | --- |
| Forecast strip | `com.samsung.android.watch.weather` |
| Alarm | `android.intent.action.SHOW_ALARMS` · `com.google.android.deskclock` |
| Timer | `android.intent.action.SHOW_TIMERS` · `com.google.android.deskclock` |
| Steps | `com.sec.android.app.shealth` |
| Battery | battery screen · `com.samsung.android.watch.settings` |
| Day / date | `com.samsung.android.calendar` |
| Icon tile | user-supplied URI, default `https://pay.google.com/` |

Implement as `<Launch>` inside each `PartText`/`PartImage` tap area, or as complication slots
with the provider's own tap action where one exists. Minimum tap area 44 × 44 even when the
glyph is smaller.

---

## 9. States

**Always-on** (`<AnalogClock>`/`<DigitalClock>` ambient variant)
- Keep: hour track, 12 index, date, time, one summary line.
- Drop: minute track, seconds dot, all arcs, all rim readouts, forecast, icon tile.
- Colors switch to AOD ink/dim; accent goes flat `dim`.
- Layout: date y 128 (22/600/0.16em), time y 160 (104 px), summary y 300 (20/500/0.14em,
  `82% · 8,412 STEPS`).
- Budget ≈ 11 % lit pixels; nothing below 20 px.

**Charging** — status band at y 412 reading `CHARGING · 82%` in `accent`; hides the minor row
and icon tile.

**Low power** — band reads `LOW POWER · 9%` in `#E0A33A`; the battery readout **and** its arc
recolor to the same amber wherever battery is slotted; every other token holds.

**Bezel select** — rotating the bezel highlights one slot: 16° accent sector at the slot's
angle, its rule/border switches to `accent`, band shows `SELECT · <LABEL>`.

---

## 10. Acceptance checklist

- [ ] Installs via `adb install` and appears in the watch face picker.
- [ ] Layout A and Layout C both selectable as styles; switching preserves slot assignments.
- [ ] All five color styles and six numeral fonts selectable.
- [ ] Every one of the 8 slots reassignable from the catalog in §4.
- [ ] Steps arc and battery arc track their real values; battery shows `%`.
- [ ] Alarm and timer open Google Clock at the right screen; steps opens Health; battery opens
      the battery screen; tile opens the configured URI.
- [ ] AOD renders within the lit-pixel budget, no element under 20 px.
- [ ] Low-power state recolors only the battery readout + arc.
- [ ] Nothing clips outside r 200 at 480 px; verified on a real 44 mm device.

---

## 11. Reference mockup

`Galaxy Watch 7 Face.dc.html` — open in a browser. The picker drives layout, style, numeral
font, accent, all eight slots and the pay URL; the states gallery shows AOD, charging, low
power, tap detail and bezel select. Treat the rendered pixels as authoritative wherever this
document is silent.
