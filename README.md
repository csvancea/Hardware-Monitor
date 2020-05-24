# hwmon - Proiect Achiziții de Date 2020

## Descrierea funcționalității

Aplicația are scopul de a monitoriza unii parametri ai calculatorului. În stagiul actual, aplicația verifică temperatura procesorului și temperatura unității de stocare, iar dacă una dintre acestea depășește o valoare setată de utilizator, atunci programul va avertiza utilizatorul printr-un sunet și/sau va lua o decizie precum închiderea sistemului pentru a preveni o pierdere a datelor.

## Implementare

- Aplicația este dezvoltată pentru Windows în Python3. Întrucât sistemul de operare nu dispune de API/utilitare proprii pentru afișarea valorilor citite de la senzori, scriptul utilizează biblioteca [OpenHardwareMonitor](https://openhardwaremonitor.org/wordpress/wp-content/uploads/2011/04/OpenHardwareMonitor-WMI.pdf) pentru a citi datele. Interfațarea cu biblioteca se face cu ajutorul pachetului [pythonnet](https://pythonnet.github.io/).
- Pentru realizarea interfeței cu utilizatorul am folosit pachetele [tkinter](https://docs.python.org/3/library/tkinter.html) și [tk-tools](https://tk-tools.readthedocs.io/en/latest/) care permit crearea unei interfețe grafice cu elemente intuitive și ușor de înțeles – afișaj cu ac indicator + slider de stabilire a valorii maxime admise pentru fiecare senzor în parte.
- În cazul în care un senzor raportează o valoare mai mare decât cea setată de utilizator, atunci se va reda un sunet de eroare și se va afișa un mesaj de avertizare în consolă.
- Citirea senzorilor se face interacționând direct cu hardware-ul. Pentru aceasta, biblioteca OpenHardwareMonitor încarcă un driver în sistem pentru a putea accesa senzorii, deci din această cauză interpretorul Python trebuie sa fie lansat cu **drepturi de administrator**. Imediat după începerea rulării scriptului, acesta verifică dacă deține drepturi de administrator, iar în caz negativ va încerca să se repornească automat cu drepturi de administrator.
- În codul sursă am lăsat comentarii care indică în detaliu logica din spatele programului.

## Cerințe

- Windows
- Python3
- Drepturi de administrator (run-as admin)
  - OpenHardwareMonitor citește datele de la hardware printr-un driver
  - Încărcarea unui driver necesită drepturi de administrator
- Următoarele pachete Python:
  - `pip install tk-tools`
    - folosit pentru GUI
  - `pip install pythonnet`
    - folosit pentru comunicarea cu biblioteca OpenHardwareMonitor

## Rulare

- Lansarea programului se face executând comanda `python3 hwmon.py` într-un Command Prompt elevat.

## Exemplu

- Normal usage:

![Normal usage](https://i.imgur.com/LibaI8O.png)

- High temperature:

![High temperature](https://i.imgur.com/uKMfJil.png)
