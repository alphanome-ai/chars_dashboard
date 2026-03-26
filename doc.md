# `chars_dashboard` — Technical Documentation

> **Package version:** 0.0.0  
> **Build type:** `ament_cmake`  
> **License:** Apache-2.0  
> **ROS 2 distro target:** Humble / Iron

---

## 1. Purpose

`chars_dashboard` is a **web-based operator dashboard** for the CHARS (Cognitive Hierarchical Architecture for Robust Swarms) framework. It provides a real-time, browser-rendered view of the swarm's mission state — from incoming task DAGs down to individual robot assignments and event history.

It is the primary human-machine interface of the CHARS system.

### What it shows

| Panel | Description |
|---|---|
| **Task DAG** | Live graph of all tasks in the current mission, with colour-coded status per node and animated dependency edges |
| **Agent Status** | Cards per robot showing IDLE / BUSY state and current task assignment |
| **Event Log** | Timestamped, colour-coded stream of dispatch, completion, and failure events |
| **DAG Summary Bar** | Live counter chips: `X/N done`, `Y active`, `Z failed` |

### Role in CHARS

`chars_dashboard` sits at the intersection of **Layer 3 (Cognitive Planning)** and **Layer 2 (Task Allocation)**:

- The operator types a natural language instruction directly into the dashboard ("Submit Text Input") → the dashboard calls the `/generate_task_dag` service, triggering the LLM + PDDL pipeline.
- Alternatively, the operator can paste a hand-crafted DAG JSON and publish it instantly ("Submit DAG").
- Once a mission is running, the dashboard passively subscribes to allocator state topics and renders the live DAG and robot cards.

---

## 2. Package Structure

```
chars_dashboard/
├── launch/
│   └── dashboard.launch.py       ← starts rosbridge + HTTP server
├── web/
│   └── dashboard.html            ← single-file web app (HTML + CSS + JS)
├── CMakeLists.txt
└── package.xml
```

The package contains **no Python/C++ ROS nodes**. All logic lives in the browser-side JavaScript in `dashboard.html`. ROS communication is bridged via `rosbridge_server`.

---

## 3. Dependencies

### ROS / Build

| Dependency | Role |
|---|---|
| `ament_cmake` | Build toolchain |
| `rosbridge_server` | Exposes ROS 2 topics and services over WebSocket (port 9090) |

### Frontend (CDN — requires internet on first load)

| Library | Version | Role |
|---|---|---|
| **D3.js** | 7.8.5 | SVG rendering and DOM manipulation for the DAG canvas |
| **Dagre** | 0.8.5 | Directed-graph layout engine (computes node positions for the DAG) |
| **roslibjs** | 1.4.1 | JavaScript client for `rosbridge_server`; provides `ROSLIB.Ros`, `ROSLIB.Topic`, `ROSLIB.Service` |
| **Google Fonts (Inter)** | — | UI typography |

---

## 4. Architecture: How It Works

```
┌──────────────────────────────────────────────────────────┐
│                     Browser (dashboard.html)             │
│                                                          │
│  ┌──────────────┐   ┌──────────────┐   ┌─────────────┐  │
│  │   DAG Panel  │   │ Agent Panel  │   │  Event Log  │  │
│  │  (D3+Dagre)  │   │  (HTML cards)│   │  (DOM list) │  │
│  └──────┬───────┘   └──────┬───────┘   └──────┬──────┘  │
│         │                  │                   │         │
│         └──────────────────┴───────────────────┘         │
│                       roslibjs                           │
└──────────────────────────────┬───────────────────────────┘
                               │ WebSocket ws://localhost:9090
                    ┌──────────┴──────────┐
                    │   rosbridge_server   │
                    └──────────┬──────────┘
                               │ ROS 2 intraprocess
              ┌────────────────┼─────────────────┐
              ▼                ▼                  ▼
     /chars/dag_status  /chars/allocator_status  /generate_task_dag
     /chars/task_dag
```

---

## 5. Topics

### Subscribed (read by the dashboard)

| Topic | Type | Publisher (expected) | Description |
|---|---|---|---|
| `/chars/dag_status` | `std_msgs/String` | `chars_central_allocator` | JSON-serialised full DAG with per-task status, assigned agent, and task metadata. Triggers full re-render of the DAG panel, agent cards, and summary bar on every message. |
| `/chars/allocator_status` | `std_msgs/String` | `chars_central_allocator` | Human-readable status strings (e.g. `"Dispatching task nav_to_box_A → agent1"`). Parsed by keyword (`Dispatching` / `COMPLETED` / `FAILURE`) and colour-coded in the event log. |

### Published (written by the dashboard)

| Topic | Type | Subscriber (expected) | Description |
|---|---|---|---|
| `/chars/task_dag` | `std_msgs/String` | `chars_central_allocator` | JSON-serialised DAG submitted by the operator via the "Submit DAG" slide panel. Published once per user submission. |

### ROS Service Called (written by the dashboard)

| Service | Type | Server (expected) | Description |
|---|---|---|---|
| `/generate_task_dag` | `plansys2_vlm_planner/srv/GenerateTaskDag` | `plansys2_vlm_planner` API caller node | Called from the "Submit Text Input" panel. Sends a plain-text natural language instruction; the server runs the LLM + PDDL pipeline and returns a generated DAG. |

---

## 6. DAG JSON Schema

Both the `/chars/dag_status` subscriber and the `/chars/task_dag` publisher use the same JSON schema, serialised as a `std_msgs/String`.

### Top-level object

```json
{
  "tasks": [
    {
      "task_id": "pick_box_28",
      "task_type": "pick",
      "frame_id": "aruco_box_28",
      "pose": {},
      "dependencies": []
    },
    {
      "task_id": "place_box_28",
      "task_type": "place",
      "frame_id": "map",
      "pose": {"x": -1.0, "y": 0.0, "z": 0.22},
      "dependencies": ["pick_box_28"],
      "constraints": {"same_agent_as": "pick_box_28"}
    }
  ]
}
```

### TaskObject fields

| Field | Type | Required | Description |
|---|---|---|---|
| `task_id` | `string` | ✅ | Unique identifier for the task (e.g. `"nav_to_box_A"`) |
| `task_type` | `string` | ✅ | One of `"navigate"`, `"pick"`, `"place"` |
| `frame_id` | `string` | ✅ | Reference coordinate frame for the pose (e.g. `"map"`, `"aruco_box_30"`) |
| `pose` | `object` | ✅ | Target pose — keys `x`, `y`, `z`, `qw`, `qx`, `qy`, `qz` (pick tasks may use `{}`) |
| `dependencies` | `string[]` | ✅ | List of `task_id` strings that must complete before this task runs |
| `status` | `string` | ✅ (in dag_status) | One of `PENDING`, `ASSIGNED`, `IN_PROGRESS`, `COMPLETED`, `FAILED` |
| `assigned_agent` | `string \| null` | ✅ (in dag_status) | Robot namespace (e.g. `"agent1"`) or `null` if unassigned |

### Example — 2-task sequential DAG

```json
{
  "tasks": [
    {
      "task_id": "nav_to_object",
      "task_type": "navigate",
      "frame_id": "map",
      "pose": { "x": 1.0, "y": 3.0, "z": 0.0, "qw": 1.0 },
      "dependencies": [],
      "status": "COMPLETED",
      "assigned_agent": "agent1"
    },
    {
      "task_id": "pick_object",
      "task_type": "pick",
      "frame_id": "aruco_box_30",
      "pose": {},
      "dependencies": ["nav_to_object"],
      "status": "IN_PROGRESS",
      "assigned_agent": "agent1"
    }
  ]
}
```

---

## 7. Parameters / Configuration

There are **no ROS parameters** — the package contains no ROS nodes. Runtime configuration constants are defined as JavaScript variables at the top of `dashboard.html`:

| Constant | Default Value | Description |
|---|---|---|
| `ROSBRIDGE_URL` | `ws://<hostname>:9090` | WebSocket URL for `rosbridge_server`. Automatically inferred from `window.location.hostname`, so it works when the page is served from the robot's host machine. Change this if rosbridge runs on a different host. |
| `MAX_LOG_ENTRIES` | `100` | Maximum number of event log entries to keep in memory. Oldest entries are pruned when the limit is reached. |

### DAG Rendering Configuration (in code)

| Constant | Value | Description |
|---|---|---|
| `STATUS_COLORS` | See below | Fill and stroke colours per task status |
| `TYPE_COLORS` | See below | Badge accent colour per task type |
| `NODE_W` | `140` px | DAG node width |
| `NODE_H` | `58` px | DAG node height |
| Dagre `rankdir` | `'LR'` | Graph flows left-to-right |
| Dagre `nodesep` | `30` | Vertical spacing between nodes in the same rank |
| Dagre `ranksep` | `60` | Horizontal spacing between DAG ranks |
| Reconnect interval | `3000` ms | Auto-reconnect delay if rosbridge connection drops |

**Status colour map:**

| Status | Fill | Stroke |
|---|---|---|
| `PENDING` | `#1e2740` | `#3d4660` (grey) |
| `ASSIGNED` | `#2d2410` | `#f59e0b` (amber) |
| `IN_PROGRESS` | `#0f1a3d` | `#638cff` (blue, with glow filter) |
| `COMPLETED` | `#0a2616` | `#22c55e` (green) |
| `FAILED` | `#2a0f0f` | `#ef4444` (red) |

**Task type badge colour map:**

| Task Type | Colour |
|---|---|
| `navigate` | `#60a5fa` (light blue) |
| `pick` | `#f59e0b` (amber) |
| `place` | `#a78bfa` (violet) |

---

## 8. UI Features

### DAG Panel

- Full-canvas SVG rendered with **D3.js**, layout computed by **Dagre** (left-to-right flow).
- Each node shows: task type badge (colour-coded), task ID (truncated at 18 chars), and assigned agent name.
- Nodes glow (SVG `feGaussianBlur` filter) when `IN_PROGRESS`.
- Edges glow blue when connecting a `COMPLETED` node to an `IN_PROGRESS` or `ASSIGNED` node (indicating the "active frontier" of execution).
- Responsive: re-renders on window resize.
- Status legend at bottom-left; summary chips at top-right.

### Agent Panel (right column, top)

- Derives agent list from tasks that have `assigned_agent` set.
- Each card shows: robot name, IDLE/BUSY badge, current or last-known task, and task type.
- Cards highlight with a blue border when the agent is busy (`IN_PROGRESS` or `ASSIGNED`).
- Updates whenever a new `/chars/dag_status` message arrives.

### Event Log (right column, bottom)

- Prepends new entries (newest at top), limited to `MAX_LOG_ENTRIES = 100`.
- Colour classes:
  - **Blue** (`dispatch`): messages containing `"Dispatching"`
  - **Green** (`complete`): messages containing `"COMPLETED"`, also connection events
  - **Red** (`failure`): messages containing `"FAILURE"`, also disconnection events
- Timestamps formatted as `HH:MM:SS`.

### Submit DAG Panel (slide-in from right)

- Opened via `+ Submit DAG` button in the header.
- **Templates** available: `⚡ 2-Chain Parallel`, `→ Sequential Pick-Place`, `📄 Empty`.
- **Preview** button: validates JSON and renders the DAG locally (all tasks shown as PENDING) without publishing to ROS.
- **Submit** button: validates, then publishes the JSON string to `/chars/task_dag`.
- Keyboard shortcut: `Ctrl+Enter` submits.
- Client-side validation checks:
  - Valid JSON syntax
  - Non-empty `tasks` array
  - Each task has `task_id` and `task_type`
  - No duplicate `task_id` values
  - All listed `dependencies` refer to known `task_id` values

### Submit Text Input Panel (slide-in from right)

- Opened via `+ Submit Text Input` button in the header.
- Accepts free-text natural language instructions (e.g. *"Pick up box A and place it at the assembly zone"*).
- On submit: calls the `/generate_task_dag` ROS service with the text as the request field.
- The service returns; success/failure is reported in the event log.
- Keyboard shortcut: `Ctrl+Enter` submits.

---

## 9. Building the Package

From the root of your ROS 2 workspace:

```bash
# Copy or symlink into workspace
cp -r /path/to/chars_dashboard ~/swarm_ws/src/

cd ~/swarm_ws

# Build
colcon build --packages-select chars_dashboard

# Source
source install/setup.bash
```

> This is a **resource-only** package (no compiled code). `colcon build` purely installs the `web/` and `launch/` directories into `install/share/chars_dashboard/`.

---

## 10. Launching the Dashboard

### Standard launch (recommended)

```bash
ros2 launch chars_dashboard dashboard.launch.py
```

This starts two processes:

| Process | Command | Port |
|---|---|---|
| `rosbridge_websocket` | via `rosbridge_websocket_launch.xml` | **9090** (WebSocket) |
| `dashboard_http_server` | `python3 -m http.server 8080 --directory <web_dir>` | **8080** (HTTP) |

Then open in your browser:

```
http://localhost:8080/dashboard.html
```

### Manual launch (for debugging individual components)

**Start rosbridge only:**
```bash
ros2 launch rosbridge_server rosbridge_websocket_launch.xml
```

**Start HTTP server only** (from the installed share directory):
```bash
python3 -m http.server 8080 --directory \
  $(ros2 pkg prefix chars_dashboard)/share/chars_dashboard/web
```

**Or serve directly from source:**
```bash
cd /path/to/chars_dashboard/web
python3 -m http.server 8080
```

---

## 11. Building Without a ROS Workspace

Because the dashboard is a static HTML file, it can be previewed without any ROS at all:

```bash
cd /path/to/chars_dashboard/web
python3 -m http.server 8080
# Open http://localhost:8080/dashboard.html
```

The page will load but show `Disconnected` (no rosbridge). The **Preview** function in the Submit DAG panel will still work for offline DAG visualization.

---

## 12. Verifying the Live Connection

Once the launch is running and the browser is open:

1. **Connection indicator** in the top-right header should turn **green** and show `Connected`.
2. Check rosbridge is running:
   ```bash
   ros2 node list | grep rosbridge
   ```
3. Verify the dashboard can see the expected topics are available:
   ```bash
   ros2 topic list | grep chars
   ```
4. Manually publish a test DAG:
   ```bash
   ros2 topic pub --once /chars/task_dag std_msgs/String \
     'data: "{\"tasks\":[{\"task_id\":\"test\",\"task_type\":\"navigate\",\"frame_id\":\"map\",\"pose\":{\"x\":0,\"y\":0,\"z\":0,\"qw\":1},\"dependencies\":[],\"status\":\"PENDING\",\"assigned_agent\":null}]}"'
   ```
   The DAG canvas should render a single `test` node.

---

## 13. Troubleshooting

| Symptom | Likely Cause | Fix |
|---|---|---|
| Connection dot stays red / `Disconnected` | `rosbridge_server` not running or wrong port | Confirm `ros2 launch chars_dashboard dashboard.launch.py` is running; check port 9090 is not blocked |
| Blank page or broken layout | CDN libraries failed to load | Check internet connectivity; open browser DevTools → Network tab for failed requests |
| DAG canvas stays at "Waiting for DAG…" | `/chars/dag_status` not being published | Confirm the allocator node is running and publishing; test with `ros2 topic echo /chars/dag_status` |
| Submit DAG has no effect | rosbridge not connected at submit time | Wait for green `Connected` indicator before submitting |
| "Service call failed" on text submit | `/generate_task_dag` service not available | Ensure `plansys2_vlm_planner` (API caller node) is running; check with `ros2 service list` |
| Dashboard shows stale agent data | Allocator stopped publishing | Agents are derived from live DAG messages; they disappear if publishing stops |
| Wrong host in WebSocket URL | Running dashboard from a remote machine | Edit `ROSBRIDGE_URL` in `dashboard.html` to point to the correct hostname/IP |

---

## 14. Integration Notes for CHARS

- The dashboard connects to `ws://<hostname>:9090` where `<hostname>` is inferred from the browser's URL bar. If you open the dashboard from a different machine than where rosbridge runs, edit the `ROSBRIDGE_URL` constant in `dashboard.html`.
- The package installs `dashboard.html` into `share/chars_dashboard/web/`. The HTTP server in the launch file serves from this installed path. If you edit `dashboard.html` in-source after building, **rebuild the package** to copy the changes into install.
- The `/chars/task_dag` topic should be set to **latched** (or use a transient-local QoS) on the ROS side so the allocator picks up DAGs published before it starts. The dashboard publishes with roslibjs defaults (non-latched); this is handled by the allocator's subscriber QoS.
- The dashboard discovers agents dynamically from the `assigned_agent` field in DAG status messages — there is no separate agent registry. Agents only appear in the Agent Panel once they have been assigned at least one task.
