# Instalasi Genetic

## Termux

```bash
pkg update && pkg upgrade -y
python -m pip install requests colorama
pkg install -y python git
termux-setup-storage
cd ~
git clone https://github.com/XyasZor/Repo-ScanGT.git
cd Genetic
python main.py
```

## Ubuntu

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3 python3-venv python3-pip git
cd ~
git clone https://github.com/USERNAME/genetic.git
cd Genetic
python3 -m venv .venv
source .venv/bin/activate
python main.py
```

Kalau Ingin Dipakai Kembali:

## Ubuntu
```bash
cd ~
cd Genetic
python3 -m venv .venv
source .venv/bin/activate
python main.py
```

## Termux
```bash
pkg update && pkg upgrade -y
cd ~
cd Genetic
python main.py
```
