"""Thin App Lab entry point for the complete, unchanged ACORN station runtime."""
from dataclasses import replace
from pathlib import Path
import argparse
import getpass
import os
import stat
import tomllib

APP_ROOT = Path(__file__).resolve().parents[1]


def read_secret(data):
    if os.environ.get("ACORN_PANEL_SECRET"):
        secret = os.environ["ACORN_PANEL_SECRET"]
        if len(secret) < 16:
            raise ValueError("Panel password must have at least 16 characters")
        return secret
    path = data / "panel-secret"
    if path.is_symlink() or not path.is_file():
        raise ValueError("Panel password missing. Stop the app; run python3 python/main.py --set-password in its folder.")
    if stat.S_IMODE(path.stat().st_mode) & 0o077:
        raise ValueError("data/panel-secret must be private: chmod 600 data/panel-secret")
    secret = path.read_text().strip()
    if len(secret) < 16:
        raise ValueError("Panel password must have at least 16 characters")
    return secret


def set_password(data):
    secret = getpass.getpass("New panel password (at least 16 characters): ")
    if len(secret) < 16 or secret != secret.strip() or secret != getpass.getpass("Repeat panel password: "):
        raise ValueError("Passwords must match, have at least 16 characters and no surrounding whitespace")
    data.mkdir(mode=0o700, parents=True, exist_ok=True)
    path = data / "panel-secret"
    # Exclusive creation prevents overwriting or following an existing secret/symlink.
    with open(path, "x", opener=lambda p, flags: os.open(p, flags, 0o600)) as output:
        output.write(secret + "\n")
    print("Password saved privately in data/panel-secret. Restart the app; passwords are never logged.")


def station_config(args):
    from station.config import load_config
    from station.mcu_protocol import McuConfig
    data = args.data_dir.resolve()
    settings_file = data / "settings.toml"
    settings = tomllib.loads(settings_file.read_text()) if settings_file.exists() else {}
    base = load_config(APP_ROOT / "python/config.toml")
    cameras = []
    for camera in base.cameras:
        if camera.name == "right":
            cameras.append(replace(camera, active=False))
        elif args.recorded:
            cameras.append(replace(camera, kind="file", source=str((args.recorded / ("smoke.ogv" if camera.name == "left" else "cloud.webm")).resolve()),
                                   width=320, height=240, capture_format="", capture_fps=0))
        else:
            source = settings.get(camera.name, f"/dev/v4l/by-path/REPLACE_{camera.name.upper()}_PORT-video-index0")
            if "REPLACE_" in source:
                raise ValueError("Map both cameras in data/settings.toml using python/settings.example.toml before starting")
            cameras.append(replace(camera, kind="usb", source=source, width=320, height=240,
                                   capture_format="YUYV", capture_fps=5))
    if args.recorded:
        # Simulation is explicit and labelled by the station; no simulated trigger is injected.
        mode = "simulated"
        print("Recorded demo: real file inference; MCU sensor and LED are simulated.", flush=True)
    else:
        mode = settings.get("bridge", "applab")
        if mode not in ("applab", "router", "off"):
            raise ValueError("Live bridge must be applab, router or off")
    return replace(base, cameras=cameras, profile=settings.get("profile", "demo"),
                   input_size=None, confidence=None, analysis_hz=None, event_timeout=None,
                   detector_view="center_crop", model=APP_ROOT / "python/models/smoke.onnx",
                   data_dir=data / ("recorded" if args.recorded else "station"),
                   panel_secret=read_secret(data), mcu=McuConfig(mode=mode))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=APP_ROOT / "data")
    parser.add_argument("--set-password", action="store_true")
    parser.add_argument("--recorded", type=Path, help="Explicit Recorded demo: directory with smoke.ogv and cloud.webm")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8080)
    args = parser.parse_args(argv)
    if args.set_password:
        set_password(args.data_dir)
        return
    config = station_config(args)
    # Reuse source-of-truth checksum even when the app is copied/imported again.
    from fetch_model import digest, MODEL_SHA
    if digest(config.model) != MODEL_SHA:
        raise ValueError("Bundled model checksum mismatch; rebuild the app")
    import logging
    import uvicorn
    from station.runtime import Station
    from station.web import create_app
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    uvicorn.run(create_app(Station(config)), host=args.host, port=args.port)


if __name__ == "__main__":
    main()
