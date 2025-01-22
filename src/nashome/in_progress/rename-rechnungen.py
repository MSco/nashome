import os
import re

directory = "/home/mschober/Schreibtisch/"
for filename in os.listdir(directory):
    match_rechnung = re.match(r"Rechnung-vom-(\d{2})\.(\d{2})\.(\d{4})\.pdf", filename) # Otelo
    match_document = re.match(r"(.*)_(\d{4})\.(\d{2})\.(\d{2})\.pdf", filename) # Vodafone
    if match_rechnung is not None:
        new_filename = f"{match_rechnung.group(3)}-{match_rechnung.group(2)}-{match_rechnung.group(1)}_Otelo-Rechnung.pdf"
    elif match_document is not None:
        new_filename = f"{match_document.group(2)}-{match_document.group(3)}-{match_document.group(4)}-{match_document.group(1)}.pdf"
    else:
        print(f"Do not rename {filename}")
        continue

    print(f"{filename} -> {new_filename}")
    os.rename(os.path.join(directory,filename), os.path.join(directory, new_filename))
   
    
