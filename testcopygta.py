import tkinter as tk
from tkinter import Toplevel
import pytesseract
from PIL import ImageGrab, Image, ImageTk, ImageEnhance
import cv2
import numpy as np
import pygetwindow as gw
import re
import os
import sys
import threading
import time
import requests
from bs4 import BeautifulSoup
import pyperclip  # Pour copier dans le presse-papier

# Fonction pour charger le model_mapping depuis un fichier
def load_model_mapping_from_file(filepath):
    model_mapping = {}
    try:
        with open(filepath, 'r') as file:
            for line in file:
                if '=' in line:
                    alias, full_name = line.strip().split('=', 1)
                    model_mapping[alias.strip().lower()] = full_name.strip()
    except FileNotFoundError:
        print(f"Fichier {filepath} non trouvé.")
    return model_mapping

# Charger le model_mapping depuis le fichier modele.txt
model_mapping = load_model_mapping_from_file('modele.txt')

# Fonction pour trouver l'exécutable Tesseract
def find_tesseract():
    if getattr(sys, 'frozen', False):
        base_path = sys._MEIPASS if hasattr(sys, '_MEIPASS') else os.path.dirname(sys.executable)
        tesseract_path = os.path.join(base_path, 'Tesseract-OCR', 'tesseract.exe')
    else:
        tesseract_path = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
    
    if not os.path.isfile(tesseract_path):
        raise FileNotFoundError("Tesseract not found. Please install Tesseract OCR from https://github.com/tesseract-ocr/tesseract and add it to your PATH.")
    return tesseract_path

# Définir la commande Tesseract
pytesseract.pytesseract.tesseract_cmd = find_tesseract()

# Expression régulière pour détecter les numéros de plaque (exactement 8 caractères)
plate_pattern = re.compile(r'\b[A-Z0-9]{8}\b')

# Définir l'URL de la page GTA Wiki
url = "https://gta.fandom.com/wiki/Vehicles_in_GTA_V"

# Fonction pour récupérer les modèles de voitures depuis GTA Wiki
def get_gta_v_car_models():
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    
    car_models = set()

    # Trouver tous les liens dans la page qui mènent à des pages de modèles de voitures
    for link in soup.find_all('a', href=True):
        if '/wiki/' in link['href']:
            car_model = link.text.strip().lower()
            if car_model and car_model.isalnum():
                car_models.add(car_model)
    
    return list(car_models)

# Charger la liste des modèles de voitures valides
valid_car_models = get_gta_v_car_models()

# Ajouter les modèles du model_mapping à la liste des modèles valides
valid_car_models.extend([model.lower() for model in model_mapping.values()])

class LicensePlateApp:
    def __init__(self, master):
        self.master = master
        self.master.title("Hayes Auto Plate Capture")

        self.create_widgets()
        self.current_plate = None
        self.current_model = None
        self.current_name = None
        self.unvalidated_models = []

        # Start capturing in a separate thread
        self.capture_thread = threading.Thread(target=self.capture_screen)
        self.capture_thread.daemon = True
        self.capture_thread.start()

    def create_widgets(self):
        # Cadre pour la section Custom
        self.custom_frame = tk.LabelFrame(self.master, text="Custom", padx=10, pady=10)
        self.custom_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

        # Cadre pour la section Réparation
        self.repair_frame = tk.LabelFrame(self.master, text="Réparation", padx=10, pady=10)
        self.repair_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")

        # Champs de saisie pour Custom
        tk.Label(self.custom_frame, text="Nom du Client").grid(row=0, column=0, pady=5)
        self.client_name_entry = tk.Entry(self.custom_frame)
        self.client_name_entry.grid(row=0, column=1, pady=5)

        tk.Label(self.custom_frame, text="Modèle de Voiture").grid(row=1, column=0, pady=5)
        self.car_model_entry = tk.Entry(self.custom_frame)
        self.car_model_entry.grid(row=1, column=1, pady=5)

        tk.Label(self.custom_frame, text="Plaque d'Immatriculation").grid(row=2, column=0, pady=5)
        self.license_plate_entry_custom = tk.Entry(self.custom_frame)
        self.license_plate_entry_custom.grid(row=2, column=1, pady=5)

        # Champs de saisie pour Réparation
        tk.Label(self.repair_frame, text="Plaque d'Immatriculation").grid(row=0, column=0, pady=5)
        self.license_plate_entry_repair = tk.Entry(self.repair_frame)
        self.license_plate_entry_repair.grid(row=0, column=1, pady=5)

        # Cadre pour l'aperçu des images capturées
        self.preview_frame = tk.LabelFrame(self.master, text="Aperçus des Captures", padx=10, pady=10)
        self.preview_frame.grid(row=1, column=0, columnspan=2, padx=10, pady=10, sticky="nsew")

        self.capture_label_plate = tk.Label(self.preview_frame, text="Plaque d'Immatriculation (Capturée)")
        self.capture_label_plate.grid(row=0, column=0, padx=5, pady=5)
        self.preview_label_plate = tk.Label(self.preview_frame)
        self.preview_label_plate.grid(row=1, column=0, padx=5, pady=5)

        self.capture_label_model = tk.Label(self.preview_frame, text="Modèle de Voiture (Capturé)")
        self.capture_label_model.grid(row=0, column=1, padx=5, pady=5)
        self.preview_label_model = tk.Label(self.preview_frame)
        self.preview_label_model.grid(row=1, column=1, padx=5, pady=5)

        self.capture_label_name = tk.Label(self.preview_frame, text="Nom du Client (Capturé)")
        self.capture_label_name.grid(row=0, column=2, padx=5, pady=5)
        self.preview_label_name = tk.Label(self.preview_frame)
        self.preview_label_name.grid(row=1, column=2, padx=5, pady=5)

        # Section pour les modèles non validés
        self.unvalidated_frame = tk.LabelFrame(self.master, text="Modèles Non Validés", padx=10, pady=10)
        self.unvalidated_frame.grid(row=2, column=0, columnspan=2, padx=10, pady=10, sticky="nsew")

        self.unvalidated_listbox = tk.Listbox(self.unvalidated_frame)
        self.unvalidated_listbox.grid(row=0, column=0, padx=5, pady=5)
        self.unvalidated_listbox.bind('<Double-1>', self.copy_to_clipboard)

    def capture_screen(self):
        while True:
            windows = gw.getWindowsWithTitle('FiveM')
            if windows:
                window = windows[0]
                print(f"Fenêtre trouvée : {window}")

                # Capture license plate
                bbox_plate = self.get_bbox(window, 'plate')
                if bbox_plate:
                    print(f"Capture des coordonnées (Plaque) : {bbox_plate}")
                    img_plate = ImageGrab.grab(bbox_plate)
                    img_cv_plate = cv2.cvtColor(np.array(img_plate), cv2.COLOR_RGB2BGR)
                    self.display_captured_image(img_cv_plate, 'plate')
                    self.process_captured_image(img_cv_plate, 'plate')
                else:
                    print("Type de capture non défini pour la plaque.")

                # Capture car model
                bbox_model = self.get_bbox(window, 'model')
                if bbox_model:
                    print(f"Capture des coordonnées (Modèle) : {bbox_model}")
                    img_model = ImageGrab.grab(bbox_model)
                    img_cv_model = cv2.cvtColor(np.array(img_model), cv2.COLOR_RGB2BGR)
                    self.display_captured_image(img_cv_model, 'model')
                    self.process_captured_image(img_cv_model, 'model')
                else:
                    print("Type de capture non défini pour le modèle.")

                # Capture client name
                bbox_name = self.get_bbox(window, 'name')
                if bbox_name:
                    print(f"Capture des coordonnées (Nom) : {bbox_name}")
                    img_name = ImageGrab.grab(bbox_name)
                    img_cv_name = cv2.cvtColor(np.array(img_name), cv2.COLOR_RGB2BGR)
                    self.display_captured_image(img_cv_name, 'name')
                    self.process_captured_image(img_cv_name, 'name')
                else:
                    print("Type de capture non défini pour le nom.")
            else:
                print("Fenêtre 'FiveM' non trouvée.")
            
            # Petite pause pour éviter une utilisation excessive du CPU
            time.sleep(0.1)

    def get_bbox(self, window, capture_type):
        if capture_type == 'plate':
            return (window.left + 30, window.top + 810, window.left + 180, window.top + 850)
        elif capture_type == 'model':
            return (window.left + 135, window.top + 20, window.left + 340, window.top + 60)
        elif capture_type == 'name':
            return (window.left + 1600, window.top + 110, window.left + 1700, window.top + 135)
        return None

    def display_captured_image(self, img_cv, capture_type):
        """Affiche l'image capturée et l'image prétraitée dans la fenêtre principale."""
        # Redimensionner l'image pour l'aperçu
        img_rgb = cv2.cvtColor(img_cv, cv2.COLOR_BGR2RGB)
        img_pil = Image.fromarray(img_rgb)
        img_pil = img_pil.resize((200, 50))  # Redimensionner l'image à 200x50 pixels pour l'aperçu
        img_tk = ImageTk.PhotoImage(img_pil)

        if capture_type == 'plate':
            self.capture_label_plate.config(image=img_tk)
            self.capture_label_plate.img = img_tk
        elif capture_type == 'model':
            self.capture_label_model.config(image=img_tk)
            self.capture_label_model.img = img_tk
        elif capture_type == 'name':
            self.capture_label_name.config(image=img_tk)
            self.capture_label_name.img = img_tk

        # Afficher également les images prétraitées
        preprocessed_img = preprocess_image(img_cv, capture_type)
        preprocessed_pil = Image.fromarray(cv2.cvtColor(preprocessed_img, cv2.COLOR_BGR2RGB))
        preprocessed_pil = preprocessed_pil.resize((200, 50))  # Redimensionner l'image à 200x50 pixels pour l'aperçu
        preprocessed_tk = ImageTk.PhotoImage(preprocessed_pil)

        if capture_type == 'plate':
            self.preview_label_plate.config(image=preprocessed_tk)
            self.preview_label_plate.img = preprocessed_tk
        elif capture_type == 'model':
            self.preview_label_model.config(image=preprocessed_tk)
            self.preview_label_model.img = preprocessed_tk
        elif capture_type == 'name':
            self.preview_label_name.config(image=preprocessed_tk)
            self.preview_label_name.img = preprocessed_tk

    def process_captured_image(self, img_cv, capture_type):
        # Prétraiter l'image pour améliorer la précision de l'OCR
        preprocessed_img = preprocess_image(img_cv, capture_type)

        # Configurer l'OCR
        if capture_type == 'plate':
            custom_config = r'--oem 3 --psm 6'
        elif capture_type == 'model' or capture_type == 'name':
            custom_config = r'--oem 3 --psm 6'

        # Appliquer OCR
        text = pytesseract.image_to_string(preprocessed_img, config=custom_config)
        print(f"Texte détecté ({capture_type}) : {text}")

        if capture_type == 'plate':
            match = plate_pattern.findall(text)
            if match:
                plate_number = match[0]
                if plate_number != self.current_plate:
                    print(f"Nouvelle plaque détectée : {plate_number}")
                    self.current_plate = plate_number
                    self.license_plate_entry_custom.delete(0, tk.END)
                    self.license_plate_entry_custom.insert(0, plate_number)
                    self.license_plate_entry_repair.delete(0, tk.END)
                    self.license_plate_entry_repair.insert(0, plate_number)
                else:
                    print("Plaque inchangée.")
            else:
                print("Aucune plaque valide détectée.")
        
        elif capture_type == 'model':
            # Correspondance du modèle
            matched_model = match_model(text)
            print(f"Modèle détecté après correspondance : {matched_model}")

            # Vérification et ajout à la liste des non-validés si nécessaire
            if matched_model.lower() in valid_car_models:
                self.current_model = matched_model
                self.car_model_entry.delete(0, tk.END)
                self.car_model_entry.insert(0, matched_model)
            else:
                if matched_model not in self.unvalidated_models:
                    self.unvalidated_models.append(matched_model)
                    self.unvalidated_listbox.insert(tk.END, matched_model)
                print("Modèle non validé, ajouté à la liste pour vérification.")
        
        elif capture_type == 'name':
            name_text = self.extract_name(text)
            if name_text.strip():
                # Vérifier que le nom contient uniquement des lettres
                if all(char.isalpha() or char.isspace() for char in name_text):
                    name_parts = name_text.split(' ', 1)
                    if len(name_parts) == 2:
                        full_name = f"{name_parts[0]} {name_parts[1]}"
                        if full_name != self.current_name:
                            print(f"Nouveau nom détecté : {full_name}")
                            self.current_name = full_name
                            self.client_name_entry.delete(0, tk.END)
                            self.client_name_entry.insert(0, full_name)
                    else:
                        print("Nom valide détecté mais non complet.")
                else:
                    print("Nom non valide, contient des caractères non autorisés.")
            else:
                print("Aucun nom valide détecté.")

    def extract_name(self, text):
        """Extrait le texte après les deux-points pour les noms des clients."""
        lines = text.split('\n')
        extracted_text = []
        for line in lines:
            parts = line.split(':', 1)
            if len(parts) > 1:
                extracted_text.append(parts[1].strip())
        return ' '.join(extracted_text)

    def copy_to_clipboard(self, event):
        """Copier le texte sélectionné dans la liste des modèles non validés."""
        selection = self.unvalidated_listbox.curselection()
        if selection:
            selected_text = self.unvalidated_listbox.get(selection[0])
            pyperclip.copy(selected_text)
            print(f"'{selected_text}' copié dans le presse-papier.")

def preprocess_image(img, capture_type):
    """Prétraiter l'image pour améliorer la qualité de l'OCR."""
    # Convertir en niveaux de gris
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # Agrandir l'image
    scale_factor = 4  # Facteur d'agrandissement plus élevé pour plus de précision
    width = int(gray.shape[1] * scale_factor)
    height = int(gray.shape[0] * scale_factor)
    dim = (width, height)
    resized = cv2.resize(gray, dim, interpolation=cv2.INTER_LINEAR)

    # Améliorer le contraste et la netteté
    enhanced = ImageEnhance.Contrast(Image.fromarray(resized)).enhance(2.0)
    enhanced = np.array(ImageEnhance.Sharpness(enhanced).enhance(2.0))

    return enhanced

def match_model(text):
    """Correspondance du texte OCR avec le modèle complet."""
    simplified_text = re.sub(r'\s+', '', text.lower())

    for alias, full_name in model_mapping.items():
        if alias in simplified_text:
            return full_name
    return text

if __name__ == "__main__":
    root = tk.Tk()
    app = LicensePlateApp(root)
    root.mainloop()

