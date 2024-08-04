import tkinter as tk
from tkinter import Toplevel
import pytesseract
from PIL import ImageGrab, Image, ImageTk
import cv2
import numpy as np
import pygetwindow as gw
import re

# Initialiser Tesseract
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# Expression régulière pour détecter les numéros de plaque (exactement 8 caractères)
plate_pattern = re.compile(r'\b[A-Z0-9]{8}\b')

class LicensePlateApp:
    def __init__(self, master):
        self.master = master
        self.master.title("Capture de Plaques d'Immatriculation")

        self.create_widgets()
        self.current_capture_type = 'plate'  # Default to capturing license plates
        self.current_plate = None  # Store the current plate
        self.current_model = None  # Store the current car model
        self.current_name = None  # Store the current client name

        # Create a window to display the captured image for the license plate
        self.capture_window_plate = Toplevel(self.master)
        self.capture_window_plate.title("Aperçu de la Capture - Plaque d'Immatriculation")
        self.capture_label_plate = tk.Label(self.capture_window_plate)
        self.capture_label_plate.pack()

        # Create a window to display the captured image for the car model
        self.capture_window_model = Toplevel(self.master)
        self.capture_window_model.title("Aperçu de la Capture - Modèle de Voiture")
        self.capture_label_model = tk.Label(self.capture_window_model)
        self.capture_label_model.pack()

        # Create a window to display the captured image for the client name
        self.capture_window_name = Toplevel(self.master)
        self.capture_window_name.title("Aperçu de la Capture - Nom du Client")
        self.capture_label_name = tk.Label(self.capture_window_name)
        self.capture_label_name.pack()

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
            print("Fenêtre 'FiveM' non trouvée")

        self.master.after(1000, self.capture_screen)  # Continue capturing

    def get_bbox(self, window, capture_type):
        if capture_type == 'plate':
            return (window.left + 20, window.top + 810, window.left + 270, window.top + 850)  # Adjusted width
        elif capture_type == 'model':
            return (window.left + 30, window.top + 20, window.left + 340, window.top + 50)  # Increased width
        elif capture_type == 'name':
            return (window.left + 20, window.top + 810, window.left + 270, window.top + 850)  # Adjusted width
        return None

    def display_captured_image(self, img_cv, capture_type):
        img_pil = Image.fromarray(cv2.cvtColor(img_cv, cv2.COLOR_BGR2RGB))
        img_tk = ImageTk.PhotoImage(image=img_pil)
        if capture_type == 'plate':
            self.capture_label_plate.config(image=img_tk)
            self.capture_label_plate.image = img_tk
            print("Image de la plaque capturée et affichée")
        elif capture_type == 'model':
            self.capture_label_model.config(image=img_tk)
            self.capture_label_model.image = img_tk
            print("Image du modèle capturée et affichée")
        elif capture_type == 'name':
            self.capture_label_name.config(image=img_tk)
            self.capture_label_name.image = img_tk
            print("Image du nom capturée et affichée")

    def process_captured_image(self, img_cv, capture_type):
        text = pytesseract.image_to_string(img_cv)
        print(f"Texte détecté ({capture_type}) : {text}")

        if capture_type == 'plate':
            match = plate_pattern.findall(text)
            if match:
                plate_number = match[0]
                if plate_number != self.current_plate:  # Only update if the plate is different
                    print(f"Nouvelle plaque détectée : {plate_number}")
                    self.current_plate = plate_number
                    self.license_plate_entry_custom.delete(0, tk.END)
                    self.license_plate_entry_custom.insert(0, plate_number)
                    self.license_plate_entry_repair.delete(0, tk.END)
                    self.license_plate_entry_repair.insert(0, plate_number)
            else:
                print("Aucune plaque valide détectée.")
        elif capture_type == 'model':
            if text.startswith("Véhicule:"):
                model_name = text.replace("Véhicule:", "").strip()
                print(f"Modèle détecté avant nettoyage : '{model_name}'")
                if model_name and model_name != self.current_model:  # Only update if the model is different
                    print(f"Nouveau modèle détecté : '{model_name}'")
                    self.current_model = model_name
                    self.car_model_entry.delete(0, tk.END)
                    self.car_model_entry.insert(0, self.current_model)
                    print(f"Modèle inséré dans le champ : '{self.current_model}'")
                else:
                    print("Aucun nouveau modèle détecté ou modèle inchangé.")
            else:
                print("Le texte ne commence pas par 'Véhicule:'")
        elif capture_type == 'name':
            if "a bien payé" in text:
                parts = text.split(" a bien payé ")
                if len(parts) > 1:
                    client_name = parts[0].strip()
                    print(f"Nom détecté avant nettoyage : '{client_name}'")
                    if client_name and client_name != self.current_name:  # Only update if the name is different
                        print(f"Nouveau nom détecté : '{client_name}'")
                        self.current_name = client_name
                        self.client_name_entry.delete(0, tk.END)
                        self.client_name_entry.insert(0, self.current_name)
                        print(f"Nom inséré dans le champ : '{self.current_name}'")
                    else:
                        print("Aucun nouveau nom détecté ou nom inchangé.")
                else:
                    print("Le texte ne contient pas 'a bien payé'")
            else:
                print("Le texte ne contient pas 'a bien payé'")

if __name__ == "__main__":
    root = tk.Tk()
    app = LicensePlateApp(root)
    root.mainloop()
