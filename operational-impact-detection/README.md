# Runtime detection of the operational impact

This folder provides the implementation of the use case presented in Section 5 of the paper.

# Install Docker & Docker Compose

# Install Requirements:
pip install -r requirements.txt

# Before running the PoC, the lightweight anomaly detection model must be trained for each vehicle and the edge SIEM
Run:
- python vehicle1_onboard/train_model.py 
- python vehicle2_onboard/train_model.py 
- ... 
- python vehicle10_onboard/train_model.py
- python edge_siem/train_model.py

# Generate the objects and the perception messages:
python3 shared/scene.py

# Run the deployment:
docker compose up --build

# Output and Logs:
The deployment generates:
- Local vehicle logs
- Edge SIEM logs
- The disagreement rate of each vehicle <br>

Outputs are available in the logs directories. The result reported in Section 5 is written to `edge_siem/logs/diverging_vehicle.json`.

**Modes**: configured via docker-compose.yml
- Hybrid: local prioritization + critical events forwarded.
- Baseline: all events forwarded.

**Configuration**: the poisoning rates, the GAN setting, the number of objects and the number of objects observed per vehicle are set in `shared/scene.py`.

**Notes**:
- This folder is a research proof-of-concept.
- The models must be trained and the objects generated before execution.
- After any change to `shared/scene.py`, run it again and rebuild with `docker compose up --build`.


