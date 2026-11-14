# Mac setup for ACORN on UNO Q

## Installed and verified

Setup audit: 2026-11-14, Apple silicon. Run from the repository root:

```sh
bash firmware/check_mac_setup.sh
```

The script only reads state; exit 0 means software prerequisites match, exit 1 means something is missing. It does not compile, install, start ADB, log in, or change the board. USB names can vary: absence from its USB name check does not prove the board is absent. It also queries an already-running ADB server, without starting one; other Android devices can appear there.

| Component | Version | Installation / purpose |
|---|---|---|
| Arduino CLI | 1.5.1 | Homebrew formula, normal `brew --prefix` bin; compile/upload |
| Arduino App Lab | official installer release 0.12.0; bundle reports 1.0.0 | `/Applications/Arduino App Lab.app`; UNO Q onboarding and lab workflow |
| Arduino Zephyr core | 1.1.0 | Default `~/Library/Arduino15/packages`; firmware pin |
| ADB | 32.0.0-8006631, protocol 1.0.41 | Arduino core dependency; symlink in Homebrew bin for shell/file transfer |
| Arduino_RouterBridge | 0.4.4 | Default `~/Documents/Arduino/libraries`; firmware pin |
| Library dependencies | RPClite 0.3.1, ArxContainer 0.7.0, ArxTypeTraits 0.3.2, DebugLog 0.8.4, MsgPack 0.4.2 | Installed by core/library dependency resolution |
| Existing tools, retained | uv 0.12.1; OpenSSH 10.3p1; LibreSSL 3.3.6; openrsync protocol 29 (2.6.9 compatible) | Python workflow; macOS SSH/SCP and rsync |

An earlier compile used a temporary isolated toolchain. This setup uses standard persistent Arduino user directories, with no shell profile changes. No unrelated packages were upgraded, removed, or configured. Homebrew's platform-tools 37.0.2 URL returned 404; it was not installed. Arduino's bundled ADB runs successfully instead. CLI 1.5.1 is the available Homebrew release; the guide's previously tested CLI 1.6.0 is not a required pin.

Verification: a new `zsh -lic` shell ran the exact compile command below successfully: **94,492 bytes flash; 38,924 bytes RAM**. App Lab's universal executable starts and its deep code signature verifies; `--version` opens the application without version output, so the release is recorded from the official download rather than inferred from its bundle's generic 1.0.0 metadata. GUI onboarding, account prompts, and board connection remain to be checked by the owner. No account was used or created. CLI compilation and local ADB/SSH access do not require an Arduino cloud account.

## Reproduce on another Mac

Prerequisites: Homebrew and a data-capable USB-C cable. Use the official [macOS App Lab setup](https://docs.arduino.cc/software/app-lab/setup/macos/), [UNO Q manual](https://docs.arduino.cc/tutorials/uno-q/user-manual/), [ADB guide](https://docs.arduino.cc/tutorials/uno-q/adb/), and [SSH guide](https://docs.arduino.cc/tutorials/uno-q/ssh/). App Lab is required for the lab/onboarding workflow; Arduino IDE is optional because CLI handles this sketch. No separate USB driver, system extension, flasher, or host `arduino-app-cli` is needed for this workflow. `arduino-app-cli` runs on the board. Linux udev rules do not apply to macOS.

```sh
HOMEBREW_NO_AUTO_UPDATE=1 HOMEBREW_NO_INSTALL_UPGRADE=1 HOMEBREW_NO_INSTALL_CLEANUP=1 brew install arduino-cli
arduino-cli core update-index --additional-urls https://downloads.arduino.cc/packages/package_zephyr_index.json
arduino-cli core install arduino:zephyr@1.1.0 --additional-urls https://downloads.arduino.cc/packages/package_zephyr_index.json
arduino-cli lib install 'Arduino_RouterBridge@0.4.4'
# Expose the installed Arduino ADB without replacing any existing adb:
test -e "$(brew --prefix)/bin/adb" || ln -s "$HOME/Library/Arduino15/packages/arduino/tools/adb/32.0.0/adb" "$(brew --prefix)/bin/adb"
arduino-cli version
adb version
arduino-cli core list
arduino-cli lib list
arduino-cli compile --fqbn arduino:zephyr:unoq --build-path /tmp/acorn-unoq-build firmware/acorn_mcu
bash firmware/check_mac_setup.sh
```

Download [App Lab 0.12.0](https://downloads.arduino.cc/AppLab/Stable/ArduinoAppLab_0.12.0.dmg), open the DMG, and drag Arduino App Lab into Applications. Open the app normally. If macOS asks for an administrator password or security approval, the owner must supply it; do not bypass Gatekeeper. When connecting the board, click **Allow** if macOS asks to allow the USB accessory. No administrator password or approval was needed for the installations performed here. First launch and connection may still show owner-only prompts. Local-network access should be allowed if requested for network discovery. If a cloud feature asks for an account, the owner must decide whether to use it; it is outside the standalone ACORN workflow.

`uv` is only needed on this Mac for local station development; installing Linux station dependencies happens on the board. Do not install Debian packages on macOS or copy the Mac `.venv`.

## First ten minutes with the board

1. Connect directly by USB-C; allow the accessory and wait up to 60 seconds. Open App Lab, select the board, and complete its hostname/password/Wi-Fi setup. Record these privately. Do not blindly update a borrowed board's image; check the core/library compatibility guidance in [firmware build/upload](README.md#build-and-upload).
2. Run the check script, then `adb devices -l`. Select the actual UNO Q serial; use `adb -s SERIAL shell`. If several devices appear, never use an unqualified shell/upload command. If unauthorized/offline, resolve the board's setup/approval first. Network alternative after onboarding: `ssh arduino@BOARD_NAME.local`; verify the host identity before accepting its key. Use the actual board IP if mDNS fails. `hostname -I` in the board shell shows its IP.
3. Copy the repository to the board. For example, from its parent directory, `scp -r junction arduino@BOARD_NAME.local:~/acorn` (replace the local repository directory name as needed). Prefer excluding `.venv`, `.git`, caches and build output with rsync; rebuild the Python environment on Linux. Optional existing `station/models/` and `station/media/` assets can be copied to avoid re-downloading. USB-only alternative: `adb -s SERIAL push station /home/arduino/acorn/` and similarly `firmware`, after creating the destination in the board shell; ensure the logged-in board user owns it.
4. In the board shell follow [station cold start](../station/README.md#cold-start-on-uno-q-linux): Linux packages, uv/Python, model/media, tests and benchmark. This needs internet initially and may require the board's sudo password. Stop the station before flashing and follow [firmware first-time checklist](README.md#install-on-the-arduino-uno-q--first-time-checklist), including disconnected external parts and voltage gates.
5. Compile on the Mac with the command above. Run `arduino-cli board list`, then use its actual address in the [documented upload command](README.md#arduino-cli-alternative). Upload replaces the MCU sketch: agree on restoration with a borrowed board's owner. Stop App Lab apps that could overwrite it. Do not use an assumed serial port or manually flash memory addresses.
6. Follow the firmware real-router-mode and bring-up sections, plus the station camera mapping guide. Start the station on Linux with `--host 0.0.0.0 --port 8080`; open `http://BOARD_LOCAL_IP:8080` on the Mac's browser on the same local demo network. USB-only alternative: `adb -s SERIAL forward tcp:8080 tcp:8080`, then open `http://127.0.0.1:8080`. Forwarding is an explicit owner command, never performed by the check script. Shut Linux down normally before removing power.

A UNO Q was connected near the end of setup: Arduino CLI identified it and the existing ADB server listed a device. During subsequent bring-up, ADB shell access, upload with `LED_EXTERNAL=0`, Linux dependency installation, local panel login, router protocol 1, fresh MCU sensor telemetry and the MCU-reported green LED state were verified. Physical LED appearance, sensor calibration, USB cameras, sustained performance and reboot persistence remain unverified. These are bring-up steps, not a guarantee of a ten-minute installation.

## Download record

Only Homebrew, Arduino sources and upstream utility sources were used. The table below records artifact versions and URLs (including core-required tools for other supported boards, installed automatically by Arduino). Indexes are mutable metadata; the selected core and library versions above are pinned.

| Artifact | Version | URL |
|---|---|---|
| Arduino CLI Homebrew bottle | 1.5.1 | https://ghcr.io/v2/homebrew/core/arduino-cli/blobs/sha256:73f9ac3a217106f72597c2d2ecf900958e5806fde396add4b188209c1650f39c |
| Arduino CLI bottle manifest | 1.5.1 | https://ghcr.io/v2/homebrew/core/arduino-cli/manifests/1.5.1 |
| App Lab | 0.12.0 | https://downloads.arduino.cc/AppLab/Stable/ArduinoAppLab_0.12.0.dmg |
| Failed Homebrew ADB download (not installed) | 37.0.2 | https://dl.google.com/android/repository/platform-tools_r37.0.2-darwin.zip |
| Package index + signature | current | https://downloads.arduino.cc/packages/package_index.tar.bz2 |
| Zephyr index + signature | current | https://downloads.arduino.cc/packages/package_zephyr_index.json ; https://downloads.arduino.cc/packages/package_zephyr_index.json.sig |
| Library index + signature | current | https://downloads.arduino.cc/libraries/library_index.tar.bz2 |
| Arduino_RPClite | 0.3.1 | https://downloads.arduino.cc/libraries/github.com/arduino-libraries/Arduino_RPClite-0.3.1.zip |
| Arduino_RouterBridge | 0.4.4 | https://downloads.arduino.cc/libraries/github.com/arduino-libraries/Arduino_RouterBridge-0.4.4.zip |
| ArxContainer | 0.7.0 | https://downloads.arduino.cc/libraries/github.com/hideakitai/ArxContainer-0.7.0.zip |
| ArxTypeTraits | 0.3.2 | https://downloads.arduino.cc/libraries/github.com/hideakitai/ArxTypeTraits-0.3.2.zip |
| DebugLog | 0.8.4 | https://downloads.arduino.cc/libraries/github.com/hideakitai/DebugLog-0.8.4.zip |
| MsgPack | 0.4.2 | https://downloads.arduino.cc/libraries/github.com/hideakitai/MsgPack-0.4.2.zip |
| SiliconLabs:openocd | 0.12.0-arduino1-static | https://downloads.arduino.cc/tools/openocd-0.12.0-arduino1-static-x86_64-apple-darwin19.tar.bz2 |
| arduino:adb | 32.0.0 | https://downloads.arduino.cc/tools/android/platform-tools_r32.0.0-darwin.zip |
| arduino:bin2uf2 | 0.1.0 | https://downloads.arduino.cc/tools/bin2uf2-0.1.0-arm64-apple-darwin.tar.gz |
| arduino:bossac | 1.9.1-arduino2 | https://downloads.arduino.cc/tools/bossac-1.9.1-arduino2-osx.tar.gz |
| arduino:dfu-util | 0.11.0-arduino5 | https://downloads.arduino.cc/tools/dfu-util-0.11-arduino5-darwin_amd64.tar.gz |
| arduino:gen-rodata-ld | 0.1.1 | https://downloads.arduino.cc/tools/gen-rodata-ld-0.1.1-arm64-apple-darwin.tar.gz |
| arduino:remoteocd | 0.1.1 | https://downloads.arduino.cc/tools/remoteocd-0.1.1-darwin-arm64.tar.gz |
| arduino:rp2040tools | 1.1.0-rc1 | https://downloads.arduino.cc/tools/rp2040tools-1.1.0-rc1-darwin_amd64.tar.bz2 |
| arduino:scripting-tools | 0.0.7 | https://downloads.arduino.cc/scripting-tools/scripting-tools_v0.0.7_macOS_ARM64.tar.gz |
| arduino:sync-zephyr-artifacts | 0.2.4 | https://downloads.arduino.cc/tools/sync-zephyr-artifacts-0.2.4-arm64-apple-darwin.tar.gz |
| arduino:zephyr | 1.1.0 | https://downloads.arduino.cc/cores/zephyr/ArduinoCore-zephyr_unoq-f07865dd.tar.bz2 |
| arduino:zephyr-check-size | 0.1.0 | https://downloads.arduino.cc/tools/zephyr-check-size-0.1.0-arm64-apple-darwin.tar.gz |
| arduino:zephyr-sketch-tool | 0.4.2 | https://downloads.arduino.cc/tools/zephyr-sketch-tool-0.4.2-arm64-apple-darwin.tar.gz |
| builtin:ctags | 5.8-arduino11 | https://downloads.arduino.cc/tools/ctags-5.8-arduino11-pm-x86_64-apple-darwin.zip |
| builtin:dfu-discovery | 0.1.2 | https://downloads.arduino.cc/discovery/dfu-discovery/dfu-discovery_v0.1.2_macOS_ARM64.tar.gz |
| builtin:mdns-discovery | 1.1.0 | https://downloads.arduino.cc/discovery/mdns-discovery/mdns-discovery_v1.1.0_macOS_ARM64.tar.gz |
| builtin:serial-discovery | 1.5.2 | https://downloads.arduino.cc/discovery/serial-discovery/serial-discovery_v1.5.2_macOS_ARM64.tar.gz |
| builtin:serial-monitor | 0.15.0 | https://downloads.arduino.cc/monitor/serial-monitor/serial-monitor_v0.15.0_macOS_ARM64.tar.gz |
| zephyr:arm-zephyr-eabi | 1.0.1 | https://github.com/zephyrproject-rtos/sdk-ng/releases/download/v1.0.1/toolchain_gnu_macos-aarch64_arm-zephyr-eabi.tar.xz |

Documentation and installer discovery used the official software page https://www.arduino.cc/en/software/, its public Gatsby page data/JavaScript, the Arduino App Lab release API https://api.github.com/repos/arduino/arduino-app-lab/releases/latest (0.11.0 there; the software page offers 0.12.0), and Arduino docs source at https://github.com/arduino/docs-content/tree/main. No downloaded code from outside the allowed sources was executed.

## Subsequent board bring-up

The station and firmware were copied to `~/acorn` on the board, with a fresh ARM64 Python 3.11 environment. The existing model hash was verified. Board-local `station/board.local.toml` selects the real router and recorded video inputs, using a separate `data-board-bringup` directory. No USB cameras are configured yet. The sketch was compiled and uploaded using `--build-property 'compiler.cpp.extra_flags=-DLED_EXTERNAL=0'`: 93,260 bytes flash and 38,264 bytes RAM. This overrides the external LED setting without editing the checked-in sketch.

The panel listens on board loopback, with a local password stored only on the board in a mode-0600 file; no password is stored in this repository. To start it again from the board shell, run `~/acorn/start-station.sh`. On the Mac, run `adb -s SERIAL forward tcp:8080 tcp:8080` and open `http://127.0.0.1:8080`. Startup is manual; no automatic station service was added.

Observed issue: the board image includes a failed `arduino-burn-bootloader.service`, which tries the image's older core 0.55.2 at first boot because its completion flag is absent. After power cycling, the MCU RPC method was unavailable. Re-uploading the pinned 1.1.0 sketch restored real MCU protocol 1 and fresh sensor readings. This does **not** resolve reboot persistence. Before relying on unattended restarts, follow Arduino's system update/compatibility recovery guidance linked above; do not create a success flag or disable the service to hide the failure. No bootloader recovery through sudo was attempted.

Board test result: 149 passed, 1 skipped, 3 real-video integration tests timed out at their fixed 16-second deadline. Those tests overlapped an attempted benchmark, so they are not clean performance measurements. The benchmark was interrupted and no benchmark result is claimed. Live panel API, two recorded-video feeds and MCU telemetry subsequently responded successfully; inference throughput is below the nominal 1 Hz target on the initial board run. Physical sensor triggering still needs an owner-observed stimulus check.
