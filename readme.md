# Hayes Auto Vision

Hayes Auto Vision est une application dédiée à l'atelier Hayes Auto, offrant des fonctionnalités avancées de capture et de reconnaissance de plaques d'immatriculation pour améliorer la gestion des véhicules.

## Caractéristiques principales

- **Capture automatique des plaques d'immatriculation** : Utilisation de captures d'écran en temps réel pour détecter et extraire les plaques.
- **Reconnaissance OCR précise** : Utilisation de Tesseract OCR pour identifier et convertir les plaques en texte lisible.
- **Interface utilisateur intuitive** : Interface conviviale permettant une saisie rapide des informations client et véhicule.
- **Performances optimisées** : Conçu pour fonctionner efficacement avec des prétraitements d'image avancés.

## Cas d'utilisation

- **Ateliers de réparation automobile**
- **Centres de personnalisation de véhicules**
- **Gestion de flotte de véhicules**

## Installation et configuration

1. **Clonez le dépôt :**
   ```sh
   git clone https://github.com/votre-utilisateur/hayes-auto-vision.git
Accédez au répertoire du projet :

sh

cd hayes-auto-vision
Installez les dépendances :

sh

pip install -r requirements.txt
Créer un fichier setup.py :

python

from cx_Freeze import setup, Executable
import sys
import os

# Dépendances supplémentaires
includes = ["tkinter", "pytesseract", "PIL", "cv2", "numpy", "pygetwindow", "re", "os", "sys"]

# Chemin vers le dossier Tesseract-OCR
tesseract_dir = r'C:\Program Files\Tesseract-OCR'

# Inclure tous les fichiers et sous-dossiers de Tesseract-OCR
include_files = []
for root, dirs, files in os.walk(tesseract_dir):
    for file in files:
        file_path = os.path.join(root, file)
        relative_path = os.path.relpath(file_path, tesseract_dir)
        include_files.append((file_path, os.path.join('Tesseract-OCR', relative_path)))

# Options de build_exe
build_exe_options = {
    "packages": includes,
    "include_files": include_files
}

base = None
if sys.platform == "win32":
    base = "Win32GUI"

setup(
    name="Hayes Auto Vision",
    version="0.1",
    description="Application de capture de plaques d'immatriculation pour Hayes Auto",
    options={"build_exe": build_exe_options},
    executables=[Executable("votre_script.py", base=base)]
)
Compilez l'application avec cx_Freeze :

sh

python setup.py build
Exécution de l'application
Une fois la compilation terminée, exécutez le fichier exécutable généré pour lancer l'application.

Configuration de Tesseract OCR
Assurez-vous que tesseract.exe et le dossier tessdata sont inclus dans le répertoire de build. L'application est configurée pour utiliser les chemins relatifs et inclut automatiquement Tesseract OCR.

Contribution
Les contributions sont les bienvenues ! Veuillez soumettre une pull request ou ouvrir une issue pour discuter des modifications que vous souhaitez apporter.

Acknowledgements
Merci à toutes les bibliothèques open source et aux contributeurs qui ont rendu ce projet possible.

Auteur : Vodrush