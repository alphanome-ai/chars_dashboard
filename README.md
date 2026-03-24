# chars_dashboard

Web-based dashboard for visualizing CHARS task allocation and DAG execution in real time.

This package launches a browser dashboard that connects to ROS 2 through rosbridge and displays:

- Global task DAG state
- Agent status (idle/busy)
- Dispatch, completion, and failure events

## Role in CHARS

`chars_dashboard` is the operator-facing entry point in Layer 3/Layer 2 monitoring:

- Shows the global plan progression generated from the cognitive planning pipeline.
- Visualizes allocator decisions as tasks are dispatched to swarm agents.
- Provides live visibility into success/failure events and reallocation behavior.

## Package Structure

```text
chars_dashboard/
  launch/
    dashboard.launch.py
  web/
    dashboard.html
  CMakeLists.txt
  package.xml
```

## Dependencies

Declared in `package.xml`:

- `ament_cmake`
- `rosbridge_server`

Frontend libraries are loaded from CDN in `web/dashboard.html`:

- D3.js
- Dagre
- roslibjs

## Build

From your ROS 2 workspace root:

```bash
colcon build --packages-select chars_dashboard
source install/setup.bash
```

## Run

```bash
ros2 launch chars_dashboard dashboard.launch.py
```

This launch file starts:

- `rosbridge_websocket` (WebSocket bridge, default port `9090`)
- Python HTTP server for static dashboard files (default port `8080`)

Open in browser:

```text
http://localhost:8080/dashboard.html
```

## Runtime Architecture

1. ROS 2 nodes publish planner/allocator/execution state.
2. `rosbridge_server` exposes ROS topics/services to web clients.
3. Dashboard (via `roslibjs`) subscribes to runtime data and updates UI.
4. DAG rendering uses D3 + Dagre for graph layout and status coloring.

## Expected Runtime Environment

- ROS 2 environment sourced.
- `rosbridge_server` available in your installation.
- Browser access to local ports `8080` and `9090`.

If running on another machine or container, update host/port references in the dashboard JS as needed.

## Troubleshooting

- Dashboard page opens but no live data:
  - Confirm `rosbridge_websocket` is running.
  - Verify WebSocket endpoint is reachable on port `9090`.
- Launch fails with missing package:
  - Install `rosbridge_server` for your ROS 2 distribution.
- Blank page or broken layout:
  - Check internet connectivity for CDN-hosted JS libraries.
  - Open browser developer tools for script/network errors.

## Notes for GitHub Publishing

Recommended screenshot assets:

- Full dashboard with DAG + agent panel + event log.
- Connection state indicator (connected/disconnected).
- Example run showing task transitions.

A short GIF of task dispatch and completion events improves repository readability.

## License

Apache-2.0
