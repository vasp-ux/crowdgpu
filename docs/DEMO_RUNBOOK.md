# CrowdGPU — Academic Demonstration Runbook

This runbook provides a reliable, reproducible, step-by-step procedure for demonstrating the **CrowdGPU** distributed peer-to-peer GPU computing platform.

---

## 1. System Architecture & Prerequisites

### Architecture Overview
CrowdGPU is composed of three integrated subsystems:
1. **Canonical Coordinator (`apps/coordinator`)**: FastAPI service with PostgreSQL database, Alembic schema versioning, peer capability discovery, and an intelligent VRAM-aware scheduler. Runs on port `8000`.
2. **NVIDIA GPU Worker (`apps/worker`)**: PyNVML GPU hardware detector, state machine (`STARTING` $\rightarrow$ `AVAILABLE` $\rightarrow$ `BUSY`), heartbeat loop, job polling loop, and controlled PyTorch CUDA executor (`matrix_multiply`, `vector_add`, `benchmark`).
3. **React Web Portal (`apps/web`)**: Modern React 18 dashboard built with Vite and Tailwind CSS. Interfaces directly with coordinator REST endpoints via proxy, providing real-time peer telemetry and job execution status. Runs on port `5173`.

```
[ Browser / React Web ] (Port 5173)
           │
      REST │ (Vite Proxy: /api, /health)
           ▼
[ Coordinator & Scheduler ] (Port 8000) ── asyncpg ──▶ [ PostgreSQL DB ] (Port 5432)
           ▲
      REST │ (Register, Heartbeat, Poll, Result)
           │
  [ GPU Worker Daemon ] ── PyNVML / PyTorch ──▶ [ NVIDIA GPU (CUDA) ]
```

### System Prerequisites
- **Operating System**: Windows 10/11 or Linux
- **Python**: 3.11+
- **Node.js**: v18.0+ / npm v9.0+
- **PostgreSQL**: PostgreSQL 15+ running on port `5432` with database `crowdgpu`
- **NVIDIA GPU**: CUDA-capable GPU with drivers installed (e.g., NVIDIA GeForce RTX series) and PyTorch with CUDA support (`torch.cuda.is_available() == True`).

---

## 2. Environment Configuration

### Frontend Configuration (`apps/web/.env.local`)
Create or verify `apps/web/.env.local`:
```ini
# Real backend integration mode
VITE_USE_MOCK=false
VITE_API_BASE_URL=
VITE_DEMO_USER_ID=00000000-0000-0000-0000-000000000001
```

### Coordinator Configuration
Settings are configured in `apps/coordinator/coordinator/config.py` and can be overridden via environment variables:
- `DATABASE_URL`: `postgresql+asyncpg://crowdgpu:changeme@localhost:5432/crowdgpu`
- `DEMO_AUTH_ENABLED`: `False` (header authentication enabled by default)
- `DEMO_USER_ID`: `00000000-0000-0000-0000-000000000001`
- `DEMO_USER_EMAIL`: `demo@crowdgpu.local`
- `COORDINATOR_PORT`: `8000`

### Worker Configuration
Worker loads settings from environment variables with sensible defaults:
- `COORDINATOR_URL`: `http://127.0.0.1:8000`
- `GPU_ID`: `0`
- `HEARTBEAT_INTERVAL`: `5` (seconds)
- `POLL_INTERVAL`: `1.0` (seconds)
- `VRAM_SAFETY_MARGIN_MIB`: `256`

---

## 3. Exact Startup Commands

Open three separate terminal windows in the project directory:

### Terminal 1: Coordinator Server
```powershell
cd "apps\coordinator"
python -m uvicorn coordinator.main:app --host 127.0.0.1 --port 8000
```
*Expected Output:*
```
INFO: Started server process
INFO: Waiting for application startup.
INFO: CrowdGPU Coordinator starting up
INFO: Application startup complete.
INFO: Uvicorn running on http://127.0.0.1:8000
```

### Terminal 2: GPU Worker Daemon
```powershell
cd "apps\worker"
$env:COORDINATOR_URL='http://127.0.0.1:8000'
$env:WORKER_ID='demo-rtx3050-worker'
$env:GPU_ID='0'
$env:HEARTBEAT_INTERVAL='5'
$env:POLL_INTERVAL='1.0'
python -m worker.worker
```
*Expected Output:*
```
[INFO] worker.gpu.detector — GPU detected: NVIDIA GeForce RTX ... — 4096 MiB VRAM
[INFO] worker.coordinator.client — Registering with Coordinator: http://localhost:8000/api/v1/workers/register
[INFO] worker.coordinator.client — Registration successful (assigned peer_id=...)
[INFO] worker.state — State: STARTING -> AVAILABLE
[INFO] Worker is AVAILABLE and ready for jobs.
[INFO] Heartbeat loop started (interval=5s)
[INFO] Job polling loop started (interval=1.0s)
```

### Terminal 3: Vite React Web Portal
```powershell
cd "apps\web"
npm run dev -- --host 127.0.0.1 --port 5173
```
*Expected Output:*
```
  VITE v5.4.21 ready in 650 ms
  ➜ Local: http://127.0.0.1:5173/
```

**Browser Demo URL:** Open [http://localhost:5173](http://localhost:5173) in Chrome or Edge.

---

## 4. Five-Minute Reliable Demo Sequence

### Step 1: Platform Health & Discovery (Dashboard `/`)
1. Open [http://localhost:5173/](http://localhost:5173/).
2. Point out the top header:
   - Green indicator badge: **Coordinator Online v0.1.0** (fetched live from `GET /health`).
3. Highlight platform statistics cards:
   - **Active Peers**: Shows count of currently registered providers in `available` state.
   - **Available GPUs**: Total physical GPUs detected.
   - **Available VRAM**: Total compute memory across connected provider peers.

### Step 2: GPU Hardware Inspection (`/peers`)
1. Click **GPU Resources** in the top navigation bar (or *View all resources*).
2. Point out the registered provider card:
   - **Hostname**: Displays worker ID/hostname.
   - **Status Badge**: Green `Available` pill.
   - **Primary GPU**: `NVIDIA GeForce RTX 3050 Laptop GPU` (or detected model).
   - **Total VRAM**: e.g., `4 GB` (4,096 MiB).
   - **Last Seen**: Dynamic relative timestamp updated via live heartbeats.
3. Click the expand toggle (**▼**) on the card:
   - Reveals hardware telemetry: Driver version, CUDA version, compute capability, registration date, and UUID.

### Step 3: Workload Submission (`/jobs/submit`)
1. Click **+ Submit Job** in the navigation bar.
2. Under **Workload Type**, select **Matrix Multiplication (CUDA)** preset:
   - Notice the form pre-populates safe defaults:
     - Job Name: `CUDA Matrix Multiplication`
     - Command / Target: `matrix_multiply`
     - Minimum VRAM Required: `512 MiB — Lightweight`
3. Click **Submit Job** (`#btn-submit-job`).

### Step 4: Live GPU Execution & Real-Time Tracking (`/jobs/:id`)
1. The browser immediately redirects to `/jobs/<job-id>`.
2. Walk the audience through the real-time execution lifecycle:
   - Status begins as `Queued` or `Assigned` with the assigned worker hostname.
   - Worker retrieves the job via `GET /jobs/next`, marks status `RUNNING`, and claims local GPU.
   - PyTorch CUDA executor executes synchronized matrix multiplication on GPU.
   - Worker posts structured output back to coordinator.
   - Live frontend polling detects completion: badge transitions to **Completed** (green).
3. Review the **Execution Result** section:
   - **Duration**: ~`1.6s - 2.1s` (physical execution time).
   - **Exit Code**: `0`.
   - **Structured JSON Result**: Displays actual computed tensor statistics:
     ```json
     {
       "device": "cuda:0",
       "execution_time_s": 1.629,
       "output": {
         "matrix_dim": 1024,
         "result_mean": -0.0173,
         "result_shape": [1024, 1024],
         "result_std": 32.034
       },
       "success": true,
       "workload_type": "matrix_multiply"
     }
     ```

### Step 5: Capacity Constraints & Job Cancellation Demo (`/jobs/submit` $\rightarrow$ `/jobs/:id`)
1. Click **+ Submit Job** again.
2. Enter Job Name: `Overcapacity Job — Cancellation Test`.
3. Select Minimum VRAM Required: **16 GB — 16,384 MiB** (exceeding individual provider capacity).
4. Click **Submit Job**.
5. On the Job Detail page:
   - Notice the job status is **Queued** because no single worker has $\ge 16\text{ GB}$ VRAM.
   - The message reads: *"Searching for a provider that meets the VRAM requirement."*
6. Click the red **Cancel Job** button.
7. Observe immediate feedback:
   - Status badge transitions to **Cancelled**.
   - Cancellation message appears: *"Cancelled by user."*

### Step 6: Audit History & Filterable Job List (`/jobs`)
1. Click **Jobs** in the top navigation bar.
2. Confirm the centralized job table displays all jobs from the session:
   - Both the completed CUDA run and the cancelled run are listed.
3. Demonstrate instant client-side filtering by clicking the **Completed** and **Cancelled** filter pills.

---

## 5. Troubleshooting & Recovery Procedures

### 1. Port 8000 or 5173 Conflict
If a port is already in use from a prior session:
```powershell
# Identify processes using port 8000 or 5173
netstat -ano | findstr "8000 5173"

# Terminate process by PID (replace <PID> with output number)
taskkill /F /PID <PID>
```

### 2. Database Connectivity Failure
If coordinator fails with `OperationalError: connection to server on port 5432 failed`:
1. Check that PostgreSQL service is running:
   ```powershell
   Get-Service -Name "*postgres*"
   ```
2. Verify connectivity with credentials:
   ```powershell
   python -c "import psycopg2; conn = psycopg2.connect('postgresql://crowdgpu:changeme@localhost:5432/crowdgpu'); print('Connected'); conn.close()"
   ```

### 3. Worker Registration Fails (`Connection refused`)
If the worker logs show `Registration attempt 1/3 failed`:
- Ensure the Coordinator server in Terminal 1 is started **before** starting the Worker daemon.
- Verify `COORDINATOR_URL` is set to `http://127.0.0.1:8000`.

### 4. GPU / CUDA Unavailable
If PyTorch reports CUDA is unavailable (`torch.cuda.is_available() == False`):
- Verify NVIDIA driver installation using `nvidia-smi`.
- Confirm PyTorch is installed with CUDA support (`pip install torch --index-url https://download.pytorch.org/whl/cu121`).

---

## 6. Offline / Fallback Demonstration Mode

If presenting in an environment without access to a physical NVIDIA GPU or without a running PostgreSQL backend, the React frontend supports a complete **Mock Preview Mode**:

1. Edit `apps/web/.env.local`:
   ```ini
   VITE_USE_MOCK=true
   VITE_API_BASE_URL=
   ```
2. Restart Vite dev server:
   ```powershell
   cd "apps\web"
   npm run dev
   ```
3. Open `http://localhost:5173/`.
   - The UI simulates 7 provider peers (RTX 4090, A100 SXM4 80GB, RTX 3090, etc.) and full job lifecycle management using browser `sessionStorage`.
   - **Labeling Notice**: Clearly inform observers that *Mock Preview Mode* is enabled when running in this configuration.
