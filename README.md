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

`res/raw/watchface.xml` is **Layout A "Instrument"**, Swiss palette, Archivo numerals,
built from `HANDOFF-watchface.md`. Design space 480 x 480.

| HANDOFF | Implemented as |
| --- | --- |
| Minute / hour tracks | `track_minute.png` / `track_hour.png` alpha masks, tinted per token |
| 12 index, seconds dot | `PartDraw` Rectangle / Ellipse; dot steps via `Transform [SECOND] * 6` |
| Slot 0 day / date | `PartText` + `Upper`, `[DAY_OF_WEEK_F] [DAY]`, taps to CALENDAR |
| Time | two `TimeText` (`hh`, `mm`) + a separate dim colon `PartText` |
| Slot 2 / 3 arcs | `Arc` r 196 stroke 8, `endAngle` transformed by `[STEP_PERCENT]` / `[BATTERY_PERCENT]` |
| Slot 2 / 3 readouts | `TextCircular` r 176, label and value as two `Font` runs on one arc |
| Slot 4 / 5 rim | `ComplicationSlot` SHORT_TEXT, `TextCircular` r 198 at 315 / 45 deg |
| Slot 1 forecast | native `[WEATHER.HOURS.1..3]`, condition code mapped to 4 two-layer glyphs |
| Slot 6 minor row | `ComplicationSlot` SHORT_TEXT, TITLE + TEXT |
| Slot 7 icon tile | `RoundRectangle` border + tinted `tile_wallet` glyph |
| Charging / low power | `Condition` on `[BATTERY_CHARGING_STATUS]` / `[BATTERY_IS_LOW]` |
| Always-on | paired `Group`s with `Variant mode="AMBIENT" target="alpha"` |

Angles follow the WFF convention, 0 degrees = 12 o'clock clockwise. That is the same
convention HANDOFF uses: a 60 degree sweep from 240 is centred on 9 o'clock, and from
60 on 3 o'clock, exactly as its arc readout rows state.

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
python3 tools/render_preview.py      # preview.png from the Layout A geometry
```

## Alternative: Watch Face Studio

Samsung's GUI tool (free, Windows/macOS) exports the same WFF output and
pushes straight to the watch over ADB. Faster for pure visual work; no
version control, no diffs, no text editing. This repo is the code route —
pick one, mixing them means hand-edits get overwritten on the next WFS export.
