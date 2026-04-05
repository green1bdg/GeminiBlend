# GeminiBlend
interfacing between Blender 5.1 and Gemini AI

# Idea


The Idea is that we are not sending any texture or shader or animation information inbetween Blender and Gemini. We only deal with vertices and convex geometry polygons.
Each time we want to prompt for modification we are querying Blender and sending that data from Blender in json format via REST API to Gemini for processing.


# running
run this in REST-interface directory to start the server inbetween gemini saas and blender uvicorn main:app --reload
paste GeminiBlend.py into blender script and hit play





















mam pomysł taki żeby napisać w pythonie w blenderze interfejs do tego żeby z tobą się komunikowac inną apką po rest api i wyniki wysyłać do pythona w blenderze, co ty na taką architekturę - jak tego dokonać?



To jest architektura typu **Pro-Level**. Właściwie budujesz własny „most” (bridge) między generatywną inteligencją a silnikiem 3D. Taka konfiguracja pozwoli Ci na projektowanie „rozmową” – mówisz: „dodaj trzy rzędy szaf i zwiększ średnicę rur chłodzących”, a Blender reaguje w czasie rzeczywistym.

Oto jak technicznie spiąć tę konstrukcję:

### **1\. Architektura Systemu**

Potrzebujesz trzech komponentów:

1. **Backend (Twoja Apka):** Serwer (np. w FastAPI lub Flask), który komunikuje się ze mną (API Gemini) i trzyma „stan” Twojego projektu.  
2. **Middleware (REST API):** Punkt styku, gdzie Blender będzie pytał: „Co nowego mam narysować?”.  
3. **Client (Blender Python):** Skrypt wewnątrz Blendera, który działa w pętli (Modal Operator) lub korzysta z biblioteki requests.

### ---

**2\. Jak tego dokonać? (Krok po kroku)**

#### **Krok A: Serwer pośredniczący (Python/FastAPI)**

Blender nie powinien uderzać bezpośrednio do Google API (bezpieczeństwo kluczy, formatowanie danych). Twoja apka powinna przyjmować prompt, wysyłać go do mnie z instrukcją: „zwróć tylko czysty kod BPy”, a następnie wystawiać ten kod pod konkretnym adresem URL (np. localhost:8000/get\_script).

#### **Krok B: Blender jako „Słuchacz”**

Standardowy skrypt w Blenderze wykonuje się raz i kończy. Aby komunikacja była płynna, musisz użyć **Modal Operatora**. To specjalny typ skryptu, który Blender uruchamia w tle i który może np. co 1 sekundę sprawdzać Twój serwer.

**Uproszczony schemat skryptu w Blenderze:**

Python

import bpy  
import requests  
import time

class REST\_Integration\_Operator(bpy.types.Operator):  
    bl\_idname \= "wm.rest\_listener"  
    bl\_label \= "Listen to Gemini API"  
      
    \_timer \= None

    def modal(self, context, event):  
        if event.type \== 'TIMER':  
            \# 1\. Odpytaj swoją apkę  
            try:  
                response \= requests.get("http://localhost:8000/latest\_command")  
                if response.status\_code \== 200:  
                    code \= response.json().get("code")  
                    if code:  
                        exec(code) \# Wykonaj wygenerowany kod 3D  
            except:  
                pass   
        return {'PASS\_THROUGH'}

    def execute(self, context):  
        \# Uruchom licznik odświeżania (np. co 2 sekundy)  
        self.\_timer \= context.window\_manager.event\_timer\_add(2.0, window=context.window)  
        context.window\_manager.modal\_handler\_add(self)  
        return {'RUNNING\_MODAL'}

### ---

**3\. Dlaczego to jest genialne dla Twojego projektu w Bydgoszczy?**

1. **Iteracja parametrów:** Możesz zapytać: „Zwiększ głębokość silosu reaktora o 5 metrów i dostosuj fundamenty do nachylenia skarpy”. Serwer przesyła kod, a Ty widzisz zmianę w 3D bez dotykania klawiatury.  
2. **Baza wiedzy:** Twoja apka może mieć wstrzyknięte dane geologiczne Bydgoszczy, o których rozmawialiśmy. Kiedy powiesz „generuj fundament”, ona doda do mojego promptu: „Pamiętaj o twardych glinach na 15 metrze”.  
3. **Wizualizacja danych:** Możesz przesyłać do Blendera rzeczywiste dane o obciążeniu sieci energetycznej w Bydgoszczy, a skrypt może zmieniać kolor rur (czerwony/niebieski) w zależności od symulowanego przepływu ciepła.

### **4\. Wyzwania (Na co uważać)**

* **Blokowanie UI:** Blender jest jednowątkowy. Jeśli zapytanie do API potrwa zbyt długo, Blender „zamrozi się”. Dlatego requests wewnątrz Blendera musi mieć krótki timeout lub być wywoływane asynchronicznie.  
* **Bezpieczeństwo exec():** Funkcja exec() wykonuje dowolny kod Pythona. Upewnij się, że Twoja apka filtruje to, co wysyła do Blendera, żebyś przypadkiem nie usunął sobie plików z dysku przez halucynację AI.

**Co myślisz o takim przepływie pracy? Jeśli chcesz, możemy teraz dopracować "System Prompt" dla Twojej apki, żeby zawsze generowała kod kompatybilny z tym "mostem".**
