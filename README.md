# MG_WatchFace

Wear OS watch faces for the **Samsung Galaxy Watch 7**, written in
**Watch Face Format (WFF)** and sideloaded over ADB.

## Why WFF

Wear OS 5 — the version the Galaxy Watch 7 shipped with — renders *only*
Watch Face Format faces. Legacy AndroidX/canvas watch faces and
Facer/WatchMaker-style faces cannot be installed on it. WFF is declarative
XML: the APK contains no executable code (`android:hasCode="false"`) and the
platform does the rendering.

Format version used here: **4** (`com.google.wear.watchface.format.version`),
which maps to Wear OS 6 / One UI 8 Watch — the update the Galaxy Watch 7
received in October 2025. Version 4 is required because `Font`, `Fill`,
`Stroke` and `tintColor` colours only became transformable in 4, and the five
palettes drive all of them from one expression. `minSdk` deliberately stays at
34: the property above is the real gate, and raising `minSdk` to 36 would pull
the whole toolchain up to AGP 9.

## Layout

```
watchface/src/main/
├── AndroidManifest.xml                 no code, declares the WFF version
└── res/
    ├── raw/watchface.xml               the watch face itself
    ├── xml/watch_face_info.xml         preview declaration
    ├── values/strings.xml               face name shown in the picker
    ├── drawable-nodpi/preview.png      picker thumbnail (450x450)
    ├── drawable/                        (add images here)
    └── font/                            (add .ttf/.otf here)
```

## Design space vs. physical panel

`watchface.xml` declares a **450 x 450** design space. That space is
resolution-independent — the renderer scales it to the panel:

| Model                  | Panel     |
|------------------------|-----------|
| Galaxy Watch 7, 44 mm  | 480 x 480 |
| Galaxy Watch 7, 40 mm  | 432 x 432 |

Keep all coordinates in the 450 x 450 space and one file covers both sizes.

## Build

Two routes produce the same APK. Both sign with `~/.android/debug.keystore`,
so an APK from either updates over one from the other without an uninstall.

**Without Android Studio** — a Watch Face Format face is resource-only, so the
legacy `aapt` that Debian/Ubuntu package is enough:

```bash
sudo apt-get install aapt apksigner zipalign android-sdk-platform-23
./tools/build_apk.sh
# -> build/watchface-debug.apk
```

The script reads `applicationId`, `minSdk`, `targetSdk`, `versionCode` and
`versionName` from `watchface/build.gradle.kts` so there is one source of
truth, injects the package name into a scratch copy of the manifest the way AGP
does, packages with `--no-crunch` so the alpha-mask PNGs are stored untouched,
zipaligns, signs, and verifies. `res/raw/watchface.xml` lands in the APK
byte-identical to the source. The API-23 `android.jar` is only used to
resolve `android:` attribute ids — every attribute in the manifest predates
API 23, and the sdk versions are stamped from the flags.

**With Android Studio** — JDK 17, Android SDK platform 34 + build-tools:

```bash
./gradlew :watchface:assembleDebug
# -> watchface/build/outputs/apk/debug/watchface-debug.apk
```

## Put it on the watch

On the watch, once:

1. Settings → About watch → Software info → tap **Software version** repeatedly
   until "Developer mode turned on" appears.
2. Settings → Developer options → enable **ADB debugging** and
   **Wireless debugging**.
3. Connect the watch to the same Wi-Fi network as the PC.

Then, from the PC:

```bash
# Watch: Developer options → Wireless debugging → Pair new device
adb pair <watch-ip>:<pairing-port> <6-digit-code>

# Watch: Developer options → Wireless debugging (the port shown there,
# which is NOT the pairing port)
adb connect <watch-ip>:<port>

adb install -r build/watchface-debug.apk        # or watchface/build/outputs/apk/debug/…
```

Activate it by long-pressing the current face and picking it from the list, or
directly:

```bash
adb shell am broadcast -a com.google.android.wearable.app.DEBUG_SURFACE \
  --es operation set-watchface \
  --es watchFaceId com.macigade.mgwatchface
```

`./gradlew installDebug` does build + install in one step once `adb connect`
has succeeded.

## Validate the XML before building

The official validator catches schema errors that the Gradle build will not:

```bash
# jar from the releases of github.com/google/watchface
java -jar tools/wff-validator.jar 4 watchface/src/main/res/raw/watchface.xml
```

The `4` is the WFF version and must match the value in `AndroidManifest.xml`.

Runtime errors (missing resources, bad expressions) show up in logcat:

```bash
adb logcat | grep -i runtime
```

## Data source tokens

Used inside `<Template>` via `<Parameter expression="[TOKEN]" />`:

| Token              | Type   | Example      |
|--------------------|--------|--------------|
| `BATTERY_PERCENT`  | int    | `72`         |
| `DAY`              | int    | `11`         |
| `DAY_Z`            | string | `11` padded  |
| `DAY_OF_WEEK`      | int    | 1 = Sunday   |
| `DAY_OF_WEEK_S`    | string | `Fri`        |
| `DAY_OF_WEEK_F`    | string | `Friday`     |
| `MONTH` / `MONTH_Z`| int/str| `9` / `09`   |
| `MONTH_S`/`MONTH_F`| string | `Sep`/`September` |
| `YEAR`             | int    | `2026`       |
| `STEP_COUNT`       | int    | `8421`       |
| `HEART_RATE`       | float  | `61`         |

## What is implemented

Both layouts from `HANDOFF-watchface.md`, selectable in the watch face editor
under **Layout** (`ListConfiguration id="layout"`, default **Instrument**):

| | Layout A "Instrument" | Layout C "Orbit" |
| --- | --- | --- |
| Time | y 118, 100 px | y 162, 96 px |
| Day / date | y 64, 23 px | y 130, 21 px |
| Steps | arc r 192-200 from 240 deg + curved readout r 176 | rim r 198 at 315 deg |
| Battery | arc r 192-200 from 60 deg + curved readout r 176 | rim r 198 at 45 deg |
| Alarm / timer | rim r 198 at 315 / 45 deg | rim r 198 at 225 / 135 deg, reversed path |
| Forecast | y 248, icon 26, hour labels | y 284, icon 20, no hour label |
| Minor row | y 334 | y 326 |
| Icon tile | y 366 | y 358 |

Both carry the same complication slot ids (4 alarm, 5 timer, 6 minor row), so
switching layout keeps every assignment, as section 10 requires.

Shared across both: the chrome from section 2 (tick tracks, 12 index, seconds
dot stepping 6 deg/s), the charging and low-power status bands, and the
always-on group. Curved text is `TextCircular`; the forecast reads native
`[WEATHER.HOURS.1..3]` and maps the condition code onto four two-layer
tintable glyphs. Tap targets are separate transparent parts, all at least
44 x 44, so the full-face parts that carry curved text never capture a tap.

### Slots

All eight section 4 slots are `ComplicationSlot`s in both layouts, reassignable
from the watch face editor to anything the user has installed.

Each slot's section 4 default is carried by its `EMPTY` complication block, so
an unassigned slot renders exactly what the spec specifies — the day/date
expression, the native three-hour weather strip, the steps and battery arcs,
the wallet tile — and assigning a provider replaces it:

| Slot | `EMPTY` (the section 4 default) | Also renders |
| --- | --- | --- |
| 0 top strip | `[DAY_OF_WEEK_F] [DAY]`, uppercase | `SHORT_TEXT` |
| 1 forecast | native `[WEATHER.HOURS.1..3]` strip | `SHORT_TEXT` — section 7's single value + label at y 262 (A) / y 284 (C) |
| 2 steps | arc from `[STEP_PERCENT]` + curved readout | `RANGED_VALUE` (arc follows the complication's range), `SHORT_TEXT` (track only) |
| 3 battery | arc from `[BATTERY_PERCENT]`, amber when low | `RANGED_VALUE`, `SHORT_TEXT` |
| 4 alarm | — | `SHORT_TEXT` |
| 5 timer | — | `SHORT_TEXT` |
| 6 minor row | — (defaults to the `SUNRISE_SUNSET` system provider) | `SHORT_TEXT` |
| 7 icon tile | wallet glyph, taps the configured URI | `MONOCHROMATIC_IMAGE`, `SMALL_IMAGE` |

Slot 6 is the only section 4 default with a matching system data source, so it
is the only slot carrying a `DefaultProviderPolicy`. The others start empty on
purpose — that is what makes their built-in default render.

`RANGED_VALUE` arcs fill on
`clamp((VALUE - MIN) / (MAX - MIN), 0, 1)` with a zero-range guard.

Tap targets live inside the slot they belong to, so an assigned complication
uses its provider's own tap action instead of the built-in launch.

**Unverified:** that a `Complication` of `type="EMPTY"` renders its content
when no provider is assigned. The type is in the documented enum and the
element takes inner content, but no example in the reference shows content
under `EMPTY`. If it turns out not to render, each slot needs a
`DefaultProviderPolicy` instead and the built-in defaults are lost for
slots 0-3 and 7. The validator and a first install settle it.

### Palette (`style`) and numerals

Five palettes from section 3 — Swiss, Mission, Editorial, Bauhaus, Stealth —
plus the always-on ink/dim pair for each. One set of elements serves all five:
every colour-bearing attribute carries

```
<Transform target="color" value="extractColorFromColors(&quot;<5 hex values>&quot;, false, ...)" />
```

where the index comes from `[CONFIGURATION.style]`. The Swiss value stays on
the attribute as the static fallback. 159 such transforms; adding a sixth
palette means appending one hex value to each of nine rows.

Six numeral styles, also section 3. `Font family` is not transformable in any
WFF version, so these are `Condition` branches on `[CONFIGURATION.numerals]` —
six per clock, across Layout A, Layout C and the always-on group. Each
branch's colon box is that font's own colon advance centred on x 240, read
from the TTF, so the colon does not move when the style changes.

Angles follow the WFF convention, 0 degrees = 12 o'clock clockwise. That is the
same convention HANDOFF uses: a 60 degree sweep from 240 is centred on 9
o'clock, and from 60 on 3 o'clock, exactly as its arc readout rows state.

## Where HANDOFF and the platform disagree

Four items in `HANDOFF-watchface.md` section 1 and 6-7 do not match Watch Face Format.
The platform behaviour was followed in each case:

| HANDOFF says | Platform | What was built |
| --- | --- | --- |
| `min SDK 33` with format version 2 | WFF 2 needs Wear OS 5 = API 34 | `minSdk 34` |
| manifest declares a `WatchFaceService` | WFF is resource-only | `hasCode="false"`, no service |
| fonts in `assets/fonts/` | WFF reads `res/font/` | `res/font/*.ttf` |
| "no arc-text primitive", use Watch Face Studio | `TextCircular` draws text on an arc | pure WFF, no WFS |
| "no standard WFF forecast data source" | WFF 2 has 8 h hourly weather | native `[WEATHER.HOURS.*]` |
| `format.version = 2` | colours are only transformable from 4 | **version 4**, so five palettes need one set of elements instead of five copies |
| bezel select state (section 9) | no rotary/bezel/focus data source, no interaction element beyond `Launch`; and the Watch 7 has no rotating bezel | **not built** — see below |

## Bezel select is not buildable

Section 2's `Bezel focus sector` row and section 9's **Bezel select** state are the
one part of the spec that cannot be built in Watch Face Format, for two separate
reasons:

1. **No input.** The complete WFF element index carries exactly two interaction
   elements — `Launch` (tap, which only starts an app) and `Gyro` (accelerometer
   parallax). There is no rotary, bezel, crown, focus, selection or editor-state
   element, no such data source in `SourceType`, and nothing in the version 2-5
   release notes. A watch face cannot read the bezel, and it has no way to hold a
   "currently selected slot" value between renders.
2. **No bezel.** The Galaxy Watch 7 does not have a rotating bezel. The Watch 6
   Classic was the last model with one; the Watch 7 has a capacitive touch bezel
   used for scrolling system UI, which is not exposed to watch faces either.

The 16 degree accent sector could be drawn, but nothing can drive which slot it
points at, so it is left unbuilt rather than shipped as decoration.

What the platform gives instead: while a user edits the watch face, the system
draws its own highlight around the complication slot being assigned. That is
rendered by Wear OS, not by the face, and needs nothing in `watchface.xml`.

## Regenerating the assets

```bash
python3 tools/render_preview.py      # preview.png + all 13 editor option icons
python3 tools/verify.py              # 68 structural checks, exits non-zero on failure
```

## Alternative: Watch Face Studio

Samsung's GUI tool (free, Windows/macOS) exports the same WFF output and
pushes straight to the watch over ADB. Faster for pure visual work; no
version control, no diffs, no text editing. This repo is the code route —
pick one, mixing them means hand-edits get overwritten on the next WFS export.
