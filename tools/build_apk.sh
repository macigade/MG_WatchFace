#!/usr/bin/env bash
# Build and sign the watch face APK without Android Studio or Google's Maven.
#
# A Watch Face Format face is resource-only (hasCode="false"), so the legacy
# aapt that Debian/Ubuntu package is enough to produce the same APK layout AGP
# would. Needs: aapt, zipalign, apksigner, keytool, and an android.jar.
#   Ubuntu: apt-get install aapt apksigner zipalign android-sdk-platform-23
#
# The debug key defaults to ~/.android/debug.keystore - the same file Android
# Studio uses - so an APK from this script and one from ./gradlew installDebug
# carry the same signature and update over each other without an uninstall.
set -euo pipefail
cd "$(dirname "$0")/.."

SRC=watchface/src/main
OUT=${OUT:-build}
PLATFORM=${ANDROID_JAR:-/usr/lib/android-sdk/platforms/android-23/android.jar}
KS=${KEYSTORE:-$HOME/.android/debug.keystore}

# single source of truth: the Gradle module file
g() { sed -n "s/^ *$1 *= *\"\{0,1\}\([^\"]*\)\"\{0,1\}.*/\1/p" watchface/build.gradle.kts | head -1; }
PKG=$(g applicationId); MIN=$(g minSdk); TGT=$(g targetSdk); VC=$(g versionCode); VN=$(g versionName)
[ -n "$PKG" ] && [ -n "$MIN" ] && [ -n "$TGT" ] && [ -n "$VC" ] && [ -n "$VN" ] || { echo "could not read build.gradle.kts" >&2; exit 1; }

mkdir -p "$OUT" "$(dirname "$KS")"
# AGP injects the namespace as the manifest package attribute; legacy aapt wants it in the file.
sed "s|<manifest xmlns:android=\"http://schemas.android.com/apk/res/android\">|<manifest xmlns:android=\"http://schemas.android.com/apk/res/android\"\n    package=\"$PKG\">|" \
    "$SRC/AndroidManifest.xml" > "$OUT/AndroidManifest.xml"
grep -q "package=\"$PKG\"" "$OUT/AndroidManifest.xml"

aapt package -f --no-crunch \
    -M "$OUT/AndroidManifest.xml" -S "$SRC/res" -I "$PLATFORM" \
    --min-sdk-version "$MIN" --target-sdk-version "$TGT" \
    --version-code "$VC" --version-name "$VN" \
    -F "$OUT/unsigned.apk"
zipalign -f 4 "$OUT/unsigned.apk" "$OUT/aligned.apk"

if [ ! -f "$KS" ]; then
    keytool -genkeypair -keystore "$KS" -alias androiddebugkey \
        -storepass android -keypass android -keyalg RSA -keysize 2048 -validity 10000 \
        -dname "CN=Android Debug,O=Android,C=US" >/dev/null 2>&1
    echo "created debug keystore $KS"
fi
apksigner sign --ks "$KS" --ks-key-alias androiddebugkey \
    --ks-pass pass:android --key-pass pass:android \
    --out "$OUT/watchface-debug.apk" "$OUT/aligned.apk"
apksigner verify "$OUT/watchface-debug.apk"
rm -f "$OUT/aligned.apk" "$OUT/watchface-debug.apk.idsig"
echo "built $OUT/watchface-debug.apk  $(stat -c%s "$OUT/watchface-debug.apk") bytes  $PKG v$VN ($VC)  sdk $MIN/$TGT"
