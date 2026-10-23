# Repo-ScanGT
Genetic Tools (GT) adalah pemindai keamanan repository. membantu pengguna menilai sebuah repo sebelum memasang atau menjalankannya, menganalisis isinya secara statis dan heuristik untuk menghasilkan persentase bahaya, tingkat risiko, temuan pola mencurigakan. Tempel URL repo (GitHub, GitLab, Bitbucket, Codeberg), tekan ENTER, dan dalam hitungan detik Anda mendapat persentase bahaya, analisa risiko, serta rincian isi repo sebelum memasang atau menjalankannya. Cepat, ringan, tanpa dependency eksternal, dan hasil pemindaian hanyalah indikator risiko, bukan vonis mutlak, sehingga tetap perlu ditinjau secara manual.

# TERMUX
pkg update && pkg upgrade -y
pkg install -y python git
termux-setup-storage
git clone https://github.com/XyasZor/genetic.git
cd genetic
python genetic.py

# UBUNTU
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3 python3-venv python3-pip git
git clone https://github.com/XyasZor/genetic.git
cd genetic
python3 -m venv .venv
source .venv/bin/activate
python genetic.py

# kalo pengen gunain lagi (ubuntu)
deactive
cd genetic
python3 -m venv .venv
source .venv/bin/activate
python genetic.py

Seluruh kodenya sengaja dibiarkan terbuka, tidak dienkripsi maupun disamarkan, karena dibentuk sebagai referensi pembelajaran. Pemilik repo, tidak mengklaim dan menolak untuk sebutan developer dan sejenisnya, Tools ini dibuat hanya untuk efektivitas dalam memeriksa keamanan sebuah repository github dan semacamnya sebelum menggunakannya. Jangan lupa bintangnya, untuk mengingat sebagai kewaspadaan dalam menggunakan repo sembarangan bisa mengundang hal hal yang tidak diinginkan.
