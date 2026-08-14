# SmartFarm Demonstration Walkthrough

This script provides a step-by-step scenario to demonstrate the SmartFarm system: multi-page server-rendered UI, microservices architecture, service isolation, database ownership, and fault tolerance.

---

## Preparation: Start the Application

Open a terminal at the root of the workspace and run:
```bash
docker compose up --build
```
Ensure all 6 containers start and their health checks report healthy:
```bash
docker compose ps
```

---

## Scenario 1: Access the Command Center & Check Health

1. Open your browser and navigate to **[http://localhost:3000](http://localhost:3000)**.
2. The **Command Center** shows:
   * **System Pulse** cards for all three services (`user-service`, `farm-service`, `monitoring-service`) — all should be ONLINE.
   * **Domain snapshot** stats: registered farmers, managed farms, tracked crops.
3. Check the aggregated health endpoint: [http://localhost:3000/health](http://localhost:3000/health) — it pings all three services and reports `healthy`.
4. The system is fully operational and has seeded default sample data.

---

## Scenario 2: Create a Farmer Profile

1. Click **Farmers** in the top navigation → the registry page (`/farmers`) lists seeded profiles.
2. Click **+ Register farmer** → fill the form on `/farmers/new`:
   * **Name**: `Jane Doe`
   * **Email**: `jane@example.com`
   * **Password**: `secure123`
   * **Phone**: `+1-555-8888`
3. Click **Create profile**. The gateway posts to the User Service, then redirects you back to `/farmers` with a green success banner and the new profile in the list.
4. Click Jane's profile to open `/farmers/1` — the profile page even shows farms owned by her (fetched from the Farm Service).

---

## Scenario 3: Create a Farm (Service-to-Service Verification)

1. Go to **Farms & crops** (`/farms`) → **+ Create farm**.
2. The form's **Farmer owner** dropdown is populated from the User Service's API. Select `Jane Doe`.
3. Fill in:
   * **Farm Name**: `Sunny Acres`
   * **Location**: `Oregon, USA`
   * **Area in acres**: `120`
4. Click **Create farm**.
5. **Behind the scenes**: the Farm Service (8002) calls the User Service (8001) over the network to verify Farmer ID `2` exists. Since it does, the farm is created in `smartfarm_farms`.
6. You are redirected to `/farms` with the new farm card showing its owner name.

---

## Scenario 4: Add a Crop to the Farm

1. Click **Sunny Acres** to open the farm workspace (`/farms/2`).
2. Click **+ Add crop** → the crop form (`/farms/2/crops/new`).
3. Fill in:
   * **Crop Name**: `Potato`
   * **Crop Type**: `Tuber`
   * **Sowing Date**: *(choose today)*
   * **Expected Harvest**: *(choose 4 months from now)*
   * **Status**: `Growing`
4. Click **Add crop**. The farm workspace now shows the crop row in its table.

---

## Scenario 5: Submit & Display Sensor Readings (NoSQL Document Store)

1. Open **Monitoring** (`/monitoring`). Select `Sunny Acres` from the **Active farm** dropdown.
2. With JavaScript enabled, the panel refreshes instantly via AJAX (`/ajax/monitoring/2`). With it disabled, click the noscript **Load** button — the page simply reloads server-rendered.
3. Initially all metrics show `--` (no readings for this farm yet).
4. Click **+ Record reading** (`/monitoring/readings/new`) and submit:
   * **Farm**: `Sunny Acres`
   * **Sensor ID**: `SENSOR-OREGON-1`
   * **Temp**: `24.5`, **Humidity**: `58`, **Soil moisture**: `36.5`, **Rainfall**: `0.0`
   * **Battery**: `98`, **Signal**: `94`
5. **Behind the scenes**: the Monitoring Service (8003) calls the Farm Service (8002) to verify the farm exists, then stores the reading document in MongoDB.
6. Back on `/monitoring?farm_id=2`, the metrics show `24.5 °C`, the MongoDB aggregation summary updates (`readings: 1`, `avg temp 24.5 °C`), and **Reading history** (`/monitoring/history`) lists the raw document.
7. Submit a second reading (e.g. Temp `25.5`, Humidity `60`, Rain `2.0`). The latest metrics update, while the aggregation summary now averages **both** records.

---

## Scenario 6: Verify Database Contents

To prove that the databases work independently, inspect their contents.

### A. Inspect Relational Data in MySQL
```bash
docker exec -it smartfarm_mysql mysql -u root -proot@123
```
```sql
-- Check User database
USE smartfarm_users;
SELECT * FROM farmers;

-- Check Farm database
USE smartfarm_farms;
SELECT * FROM farms;
SELECT * FROM crops;
exit;
```
Notice that `farmers` live in `smartfarm_users`, while `farms` / `crops` live in `smartfarm_farms`.

### B. Inspect Telemetry Documents in MongoDB
```bash
docker exec -it smartfarm_mongodb mongosh
```
```javascript
use smartfarm_monitoring;
db.sensor_readings.find().pretty();
exit;
```
Observe the flexible JSON documents containing the raw sensor streams.

---

## Scenario 7: Demonstrate Microservices Fault Tolerance

1. Stop the **User Service**:
   ```bash
   docker compose stop user-service
   ```
2. Open `/` (Command Center): the **user-service** health card turns OFFLINE while farm and monitoring stay ONLINE.
3. Try to register a farmer at `/farmers/new` → the gateway shows the error banner *"user-service is unavailable"*.
4. Try to create a farm → the Farm Service contacts the stopped User Service, fails the verification, and rejects the request with *"Unable to verify farmer ID because User Service is unavailable"*.
5. **Key Insight**: the rest of the application still works! You can still submit sensor readings for existing farms, compute MongoDB averages, and browse farms and crops, because Farm and Monitoring services are decoupled from the User Service database.

---

## Scenario 8: Restart and Recover

1. Start the User Service again:
   ```bash
   docker compose start user-service
   ```
2. Wait a few seconds for the health check to complete.
3. Refresh the Command Center: **user-service** is ONLINE again. Creating a farm now succeeds — the system has fully recovered.

---

## Scenario 9: Review Container Logs

To debug or trace microservices communication, inspect container logs:
* View all logs: `docker compose logs`
* Follow logs for the Farm Service to see incoming verification calls:
  ```bash
  docker compose logs -f farm-service
  ```
* Follow logs for the Gateway to see page requests:
  ```bash
  docker compose logs -f gateway-service
  ```
Observe the logs printing incoming requests, methods, endpoints, and status codes.
