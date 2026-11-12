# Impact analysis and runtime detection of data poisoning on GAN-based data augmentation techniques

## Paper
This repository contains the code associated with the following paper:
**Poisoning Attacks against Augmented 3D Point Cloud Datasets for Connected and Autonomous Vehicles: Operational Impact and Runtime Detection with a Hybrid SIEM**

This paper is an extended version of our conference paper:
**Assessing the Operational Impact of Poisoning Attacks over Augmented 3D Point Cloud Public Datasets for Connected and Autonomous Vehicles**, SECRYPT 2026.

## Main resources contained in this repository

### 1. Impact Assessment Tool

Source code available at the [operational-impact-assessment folder](./operational-impact-assessment/) 

Follow the instructions below.

#### Install Docker and Docker-Compose

#### Build the docker image

sudo docker build -t bia .

#### Start the service

sudo docker-compose up

#### Test the tool

Open a web browser and go to http://127.0.0.1:8003 to access its GUI

### 2. Datasets and classification process

Open and process the following two files 

[Classification.ipynb](./datasets-and-classification-process/Classification.ipynb)

[process_data.py](./datasets-and-classification-process/process_data.py)

### 3. Runtime detection of the operational impact

Source code available at the [operational-impact-detection folder](./operational-impact-detection/)

This folder contains the hybrid SIEM deployment of Section 5, where ten connected vehicles report the objects they perceive and an augmented edge SIEM compares the classes reported for each object observed by several of them.

Follow the instructions below.

#### Install Docker and Docker-Compose

#### Generate the objects and the perception messages

python3 shared/scene.py

#### Start the deployment

sudo docker compose up --build

#### Read the results

The disagreement rate of each vehicle and the vehicles reported as diverging are written to edge_siem/logs/diverging_vehicle.json

## Acknowledgements
* Impact Assessment tool: The impact assessment tool used in this work is based on our previous work, [the Business Impact Analyser](https://gitlab.com/tsp-soccrates-components/bia).
* Datasets and classification process: The data augmentation and classification process is based on these two projects: [3DGAN](https://github.com/xchhuang/simple-pytorch-3dgan/) and [InceptionNet](https://github.com/fgn02/Advanced-Image-Classification-through-CNNs), with modifications including parameter adjustments and a new function to generate .mat objects as output to train the 3D-GAN and produce new synthetic 3D point clouds.
* Runtime detection of the operational impact: The hybrid SIEM deployment used in this work is based on the proof-of-concept implementation of our previous work, [Hybrid SIEM Architecture for Connected and Automated Vehicles](https://github.com/Marwanlz/Hybrid_SIEM_Architecture_for_CAVs).
