# Instalasi Genetic

## Termux

```bash
pkg update && pkg upgrade -y
pkg install -y python git
termux-setup-storage
cd ~
git clone https://github.com/USERNAME/genetic.git
cd genetic
python genetic.py
```

## Ubuntu

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3 python3-venv python3-pip git
cd ~
git clone https://github.com/USERNAME/genetic.git
cd genetic
python3 -m venv .venv
source .venv/bin/activate
python genetic.py
```

Kalau Ingin Dipakai Kembali:

```bash
cd genetic
python3 -m venv .venv
source .venv/bin/activate
python genetic.py
```
