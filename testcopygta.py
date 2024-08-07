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

# Fonction pour trouver l'exécutable Tesseract
def find_tesseract():
    if getattr(sys, 'frozen', False):
        base_path = os.path.dirname(sys.executable)
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

# Expression régulière pour détecter le nom et prénom
name_pattern = re.compile(r'Nom\s*:\s*(\w+)\s*Prénom\s*:\s*(\w+)', re.IGNORECASE)

def preprocess_image(img, capture_type):
    """Prétraiter l'image pour améliorer la qualité de l'OCR."""
    # Convertir en niveaux de gris
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    if capture_type == 'name':
        # Ajuster le contraste et la netteté spécifiquement pour le type 'name'
        enhancer = ImageEnhance.Contrast(Image.fromarray(gray))
        gray = np.array(enhancer.enhance(2))
        
        kernel = np.array([[0, -1, 0], [-1, 15, -1], [0, -1, 0]])
        gray = cv2.filter2D(gray, -1, kernel)
        
        gray = cv2.fastNlMeansDenoising(gray, None, 30, 7, 21)

        _, binary = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    else:
        # Appliquer un filtre bilatéral pour débruiter tout en conservant les bords
        gray = cv2.bilateralFilter(gray, 11, 17, 17)

        # Appliquer un filtre de netteté renforcée
        kernel = np.array([[0, -1, 0], [-1, 10, -1], [0, -1, 0]])
        gray = cv2.filter2D(gray, -1, kernel)

        # Appliquer un filtre de débruitage
        gray = cv2.fastNlMeansDenoising(gray, None, 30, 7, 21)

        # Binarisation avec un seuil global
        _, binary = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    return binary

class LicensePlateApp:
    def __init__(self, master):
        self.master = master
        self.master.title("Capture de Plaques d'Immatriculation")

        self.create_widgets()
        self.current_plate = None
        self.current_model = None
        self.current_name = None

        # Start capturing immediately
        self.capture_screen()

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

    def capture_screen(self):
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

        self.master.after(5000, self.capture_screen)  # Continue capturing every 5 seconds

    def get_bbox(self, window, capture_type):
        if capture_type == 'plate':
            return (window.left + 30, window.top + 810, window.left + 180, window.top + 850)
        elif capture_type == 'model':
            return (window.left + 131, window.top + 20, window.left + 340, window.top + 60)
        elif capture_type == 'name':
            return (window.left + 1600, window.top + 110, window.left + 1700, window.top + 135)
        return None

    def display_captured_image(self, img_cv, capture_type):
        """Affiche l'image capturée et l'image prétraitée dans la fenêtre principale."""
        img_rgb = cv2.cvtColor(img_cv, cv2.COLOR_BGR2RGB)
        img_pil = Image.fromarray(img_rgb)
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

        # Configurer les paramètres OCR
        if capture_type == 'plate':
            custom_config = r'--oem 3 --psm 7 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
        elif capture_type == 'model' or capture_type == 'name':
            custom_config = r'--oem 3 --psm 6'

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
            if text.strip() and text.strip() != self.current_model:
                print(f"Nouveau modèle détecté : {text.strip()}")
                self.current_model = text.strip()
                self.car_model_entry.delete(0, tk.END)
                self.car_model_entry.insert(0, text.strip())
            else:
                print("Modèle inchangé.")
        elif capture_type == 'name':
            match = name_pattern.search(text)
            if match:
                full_name = f"{match.group(1)} {match.group(2)}"
                if full_name != self.current_name:
                    print(f"Nouveau nom détecté : {full_name}")
                    self.current_name = full_name
                    self.client_name_entry.delete(0, tk.END)
                    self.client_name_entry.insert(0, full_name)
            else:
                print("Aucun nom valide détecté.")

if __name__ == "__main__":
    root = tk.Tk()
    app = LicensePlateApp(root)
    root.mainloop()
