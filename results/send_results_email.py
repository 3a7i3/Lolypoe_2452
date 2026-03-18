import smtplib
from email.message import EmailMessage
import os

# Configuration (à adapter)
EMAIL_ADDRESS = "your_email@example.com"
EMAIL_PASSWORD = "your_password"
RECIPIENT = "recipient@example.com"

ATTACHMENTS = [
    "evolution_scores.png",
    "param_distribution.png",
    "param_heatmap.png",
    "evolution_params.csv"
]


def send_results():
    msg = EmailMessage()
    msg["Subject"] = "Résultats Evolution Trading Ecosystem"
    msg["From"] = EMAIL_ADDRESS
    msg["To"] = RECIPIENT
    msg.set_content("Veuillez trouver en pièce jointe les résultats d'analyse de l'écosystème quant.")

    for filename in ATTACHMENTS:
        path = os.path.join(os.path.dirname(__file__), filename)
        if os.path.exists(path):
            with open(path, "rb") as f:
                file_data = f.read()
                msg.add_attachment(file_data, maintype="application", subtype="octet-stream", filename=filename)
        else:
            print(f"Fichier non trouvé : {filename}")

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        smtp.send_message(msg)
        print("Email envoyé avec les résultats.")

if __name__ == "__main__":
    send_results()
