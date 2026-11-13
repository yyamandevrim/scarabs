#!/bin/bash
# Read-only: no installs, compilation, daemon startup, or board shell commands.
set -u
missing=0
report() { printf '%s\n' "$*"; }
check() {
  if command -v "$1" >/dev/null 2>&1; then
    report "PRESENT $1: $("$@" 2>&1 | head -n 2)"
  else report "MISSING $1"; missing=1; fi
}
check arduino-cli version
check adb version
check ssh -V
check uv --version
check rsync --version
for tool in "$HOME/Library/Arduino15/packages/arduino/tools/remoteocd/0.1.1/remoteocd" "$HOME/Library/Arduino15/packages/zephyr/tools/arm-zephyr-eabi/1.0.1/bin/arm-zephyr-eabi-gcc"; do
  if [ -x "$tool" ]; then
    case "$tool" in
      */remoteocd) report "PRESENT uploader: $("$tool" version 2>&1)" ;;
      *) report "PRESENT compiler: $("$tool" --version 2>&1 | head -n 1)" ;;
    esac
  else report "MISSING bundled tool: ${tool##*/}"; missing=1; fi
done
if command -v scp >/dev/null 2>&1; then
  report 'PRESENT scp: part of OpenSSH (version above)'
else report 'MISSING scp'; missing=1; fi
app=''
for candidate in '/Applications/Arduino App Lab.app' "$HOME/Applications/Arduino App Lab.app"; do
  if [ -d "$candidate" ]; then app="$candidate"; break; fi
done
if [ -n "$app" ]; then
  report "PRESENT App Lab: bundle $(/usr/libexec/PlistBuddy -c 'Print :CFBundleShortVersionString' "$app/Contents/Info.plist") (installer release may differ; see MAC_SETUP.md)"
else report 'MISSING Arduino App Lab'; missing=1; fi
if command -v arduino-cli >/dev/null 2>&1; then
  cores=$(arduino-cli core list 2>&1)
  if printf '%s\n' "$cores" | awk '$1=="arduino:zephyr" && $2=="1.1.0" {found=1} END {exit !found}'; then
    report 'PRESENT arduino:zephyr 1.1.0'
  else report "MISSING pinned arduino:zephyr 1.1.0: $cores"; missing=1; fi
  libs=$(arduino-cli lib list 2>&1)
  for entry in Arduino_RouterBridge:0.4.4 Arduino_RPClite:0.3.1 ArxContainer:0.7.0 ArxTypeTraits:0.3.2 DebugLog:0.8.4 MsgPack:0.4.2; do
    name=${entry%:*}; version=${entry#*:}
    if printf '%s\n' "$libs" | awk -v n="$name" -v v="$version" '$1==n && $2==v {found=1} END {exit !found}'; then
      report "PRESENT $name $version"
    else report "MISSING expected $name $version"; missing=1; fi
  done
fi
# USB enumeration avoids `adb devices`, which starts a daemon when absent.
usb=$(/usr/sbin/ioreg -r -c IOUSBHostDevice -l -w 0 2>/dev/null)
if printf '%s\n' "$usb" | /usr/bin/grep -Eiq 'UNO.?Q'; then
  report 'DETECTED USB UNO Q; next: adb devices -l'
  report 'Then: adb -s SERIAL_FROM_LIST shell'
else
  report 'No USB device named UNO Q detected (USB naming can vary).'
  report 'After connecting directly and allowing the accessory, wait 60 seconds; run: adb devices -l'
fi
# Query only an already-running local ADB server; never start one.
devices=$(printf '000ehost:devices-l' | /usr/bin/nc -w 1 127.0.0.1 5037 2>/dev/null || true)
if [ -n "$devices" ]; then
  report "Existing ADB server response (may include other devices): $devices"
  report 'For a confirmed UNO Q serial: adb -s SERIAL_FROM_LIST shell'
fi
report 'Network alternative after App Lab onboarding: ssh arduino@BOARD_NAME.local'
report 'See firmware/MAC_SETUP.md for copying files, building, uploading and opening the panel.'
exit "$missing"
