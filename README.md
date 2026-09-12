# MG_WatchFace

Wear OS watch faces for the **Samsung Galaxy Watch 7**, written in
**Watch Face Format (WFF)** and sideloaded over ADB.

## Why WFF

Wear OS 5 — the version the Galaxy Watch 7 shipped with — renders *only*
Watch Face Format faces. Legacy AndroidX/canvas watch faces and
Facer/WatchMaker-style faces cannot be installed on it. WFF is declarative
XML: the APK contains no executable code (`android:hasCode="false"`) and the
platform does the rendering.

Format version used here: **2** (`com.google.wear.watchface.format.version`),
which maps to Wear OS 5 / API 34. Raise it only when you need elements from a
later version (3 = Wear OS 5.1, 4 = Wear OS 6).

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

Requirements: JDK 17, Android SDK platform 34 + build-tools, `adb`.
Android Studio installs all of them.

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

adb install -r watchface/build/outputs/apk/debug/watchface-debug.apk
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
java -jar tools/wff-validator.jar 2 watchface/src/main/res/raw/watchface.xml
```

The `2` is the WFF version and must match the value in `AndroidManifest.xml`.

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

## Regenerating the assets

```bash
python3 tools/render_preview.py      # preview.png + the two editor option icons
python3 tools/verify.py              # 43 structural checks, exits non-zero on failure
```

## Alternative: Watch Face Studio

Samsung's GUI tool (free, Windows/macOS) exports the same WFF output and
pushes straight to the watch over ADB. Faster for pure visual work; no
version control, no diffs, no text editing. This repo is the code route —
pick one, mixing them means hand-edits get overwritten on the next WFS export.
