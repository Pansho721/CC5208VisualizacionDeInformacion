#!/bin/bash

mkdir -p DATA/INPUT
mkdir -p DATA/OUTPUT

mv Spillover_simulator__port-level_impact.csv DATA/INPUT/routes.csv

python3 preproces.py DATA/INPUT/routes.csv DATA/OUTPUT/ports.csv

python 