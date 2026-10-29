# Self-Healing Infrastructure with Prometheus, Alertmanager & Ansible

Automatically detects a failed service and recovers it, with no human involved.

```
NGINX stops
   -> Blackbox exporter probe fails        (probe_success == 0)
   -> Prometheus rule NginxDown fires      (after 10 s)
   -> Alertmanager sends a webhook         (http://healer:5001/alert)
   -> healer runs the Ansible playbook     (ansible/heal.yml)
   -> playbook restarts NGINX and checks it answers HTTP 200
```

## Requirements
- Docker Desktop (running) on Windows, macOS or Linux. No cloud account needed.

## Start
```powershell
docker compose up -d --build
docker compose ps
```
Open: Prometheus http://localhost:9090 | Alertmanager http://localhost:9093 | NGINX http://localhost:8080

In Prometheus, open Status > Targets. `blackbox-nginx` and `node` should be UP.

## Demo 1: NGINX failure heals itself
Open two PowerShell windows.

Window 1 (watch the healing log):
```powershell
Get-Content .\logs\healing.log -Wait
```
Window 2 (break the service):
```powershell
docker stop nginx
docker ps -a --filter name=nginx
```
Wait about 15 to 30 seconds. You should see in window 1: `ALERT firing: NginxDown`, then Ansible tasks, then `HEAL OK`.
Check that it is back:
```powershell
curl.exe -I http://localhost:8080
docker ps --filter name=nginx
```
Screenshots to take: Prometheus Alerts page (NginxDown pending/firing), Alertmanager page, healing log, `docker ps` before and after.

## Demo 2: runaway CPU is stopped
```powershell
docker compose --profile demo up -d cpu-stress
```
After about 30 to 60 seconds the `HighCpuUsage` alert fires and the playbook stops the `cpu-stress` container. Check with `docker ps -a --filter name=cpu-stress`.
(CPU is measured for the whole Docker VM. If it never passes 90 percent, lower the threshold in `prometheus/alert.rules.yml` to 60 for the demo, then run `docker compose restart prometheus`.)

## Where each deliverable is
| Deliverable | File |
|---|---|
| Prometheus config | `prometheus/prometheus.yml`, `prometheus/alert.rules.yml` |
| Alertmanager webhook setup | `alertmanager/alertmanager.yml`, `healer/webhook.py` |
| Ansible playbook | `ansible/heal.yml` |
| Demo logs | `logs/healing.log` |
| Screenshots | take them during the two demos |

## Troubleshooting
- Port already in use (8080, 9090, 9093, 5001): change the left number in `ports:` in `docker-compose.yml`.
- No healing happens: `docker compose logs healer` and check http://localhost:9090/alerts.
- Healer cannot reach Docker: make sure Docker Desktop is running and the `/var/run/docker.sock` volume is in `docker-compose.yml`.
- Changed the playbook or webhook: `docker compose up -d --build healer`.

## Stop and clean up
```powershell
docker compose down
```

## Interview topics this project covers
Self-healing infrastructure (Q43), monitoring and logging (Q19, Q20, Q42), Ansible (Q23, Q27), Docker and Compose (Q9, Q10), system failures and downtime (Q40), alerting and automation.

## Report outline (max 2 pages)
Introduction, Abstract, Tools Used (Docker, Prometheus, Blackbox exporter, Alertmanager, Ansible, Python), Steps (architecture, configs, rules, webhook, playbook, tests), Conclusion (recovery time, limits, future work such as Slack notifications).
