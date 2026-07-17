# Holobot — AI Vision Interface

Holobot is a real-time, browser-based Vision-Language Model (VLM) interface for a physical pan-tilt camera robot. It streams live video over WebRTC, sends frames to a VLM for scene description, and lets the model (or a user) steer a physical camera mount via an Arduino-controlled pan-tilt bracket.

It is built on top of NVIDIA's open-source [**live-vlm-webui**](https://github.com/NVIDIA-AI-IOT/live-vlm-webui) (Apache-2.0), with the following original additions:

- **Physical pan-tilt control** (`pantilt_server.py`) — a Flask microservice that talks to an Arduino over serial to physically move the camera.
- **RTSP / IP camera support** (`rtsp_track.py`) — lets Holobot process feeds from network IP cameras, not just a local webcam, with automatic reconnection and exponential backoff.
- **Extended GPU monitoring** (`gpu_monitor.py`) — platform detection and stats across NVIDIA (NVML), Jetson Thor, Jetson Orin, and Apple Silicon.
- **Custom "Holobot" web UI** (`index.html`) — a themed frontend with its own branding and controls layered over the base interface.

## Architecture

```
Browser (WebRTC) ──► server.py (aiohttp)
                          │
                          ├── video_processor.py ── frames ──► vlm_service.py ──► VLM API (vLLM / OpenAI-compatible)
                          │
                          ├── rtsp_track.py ── (optional) IP camera input instead of webcam
                          │
                          ├── gpu_monitor.py ── periodic hardware stats ──► WebSocket ──► browser
                          │
                          └── /pantilt endpoint ──► pantilt_server.py ──► Arduino (serial) ──► physical pan-tilt mount
```

- **`server.py`** — Main aiohttp application. Handles the WebRTC offer/answer exchange, WebSocket updates (VLM text + GPU stats), model/service auto-detection, and RTSP start/stop/status endpoints.
- **`video_processor.py`** — Wraps the incoming video track, samples every *N* frames, forwards them to the VLM service asynchronously (non-blocking), and passes video through with zero-copy.
- **`vlm_service.py`** — Thin async client for any OpenAI-compatible VLM endpoint (vLLM, SGLang, Ollama, hosted APIs). Encodes frames to base64 JPEG and tracks inference latency/throughput metrics.
- **`rtsp_track.py`** — `aiortc`-compatible video track that reads from an RTSP URL instead of a webcam, with automatic reconnect on stream failure.
- **`gpu_monitor.py`** — Abstract `GPUMonitor` base class with concrete implementations per platform, auto-selected at startup.
- **`pantilt_server.py`** — Standalone Flask service exposing `POST /pantilt` (`{"pan": -100..100, "tilt": -100..100}`), which maps to servo angles and writes them to an Arduino over serial.

## Setup

1. Install the base project dependencies (see NVIDIA's live-vlm-webui repo for the full list — aiohttp, aiortc, opencv-python, openai, pillow, etc.), plus:
   ```bash
   pip install pyserial flask flask-cors
   ```

2. Configure your VLM endpoint (vLLM/SGLang/OpenAI-compatible) — see `vlm_service.py`'s constructor for `model`, `api_base`, `api_key`.

3. Connect your Arduino pan-tilt controller and update the serial port in `pantilt_server.py` (currently hardcoded to `/dev/ttyACM0` — change this to match your setup, e.g. `COM3` on Windows).

4. Run the main server:
   ```bash
   python -m holobot.server
   ```

5. (Optional, separate process) Run the pan-tilt bridge:
   ```bash
   python pantilt_server.py
   ```

6. Open the WebUI in a browser and point it at your local server.

## Attribution & License

This project is derived from [NVIDIA's live-vlm-webui](https://github.com/NVIDIA-AI-IOT/live-vlm-webui), licensed under Apache License 2.0. Original copyright and license headers from NVIDIA-authored files are preserved as required by the license. See `LICENSE` for the full Apache-2.0 text, and individual file headers for original copyright notices.

Original additions in this repository (pan-tilt control, RTSP support extensions, GPU monitor platform additions, and the Holobot UI) are contributed under the same Apache-2.0 license unless otherwise noted.

## Notes / known constraints

- The Arduino serial port in `pantilt_server.py` is currently hardcoded — parameterize this (env var or config file) before deploying on a different machine.
- `pantilt_server.py` enables CORS from `*` (all origins) — fine for local/lab use, but tighten this before exposing the service beyond a trusted local network.
