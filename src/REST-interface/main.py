import os
import json
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import google.generativeai as genai
from dotenv import load_dotenv

# Konfiguracja srodowiska
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError("Brak klucza GEMINI_API_KEY w pliku .env!")

genai.configure(api_key=api_key)
app = FastAPI()

# ==========================================
# STRUKTURY DANYCH WEJSCIOWYCH
# ==========================================
class Vertex(BaseModel): x: float; y: float; z: float
class Location(BaseModel): x: float; y: float; z: float
class MeshData(BaseModel):
    vertices: list[Vertex]
    faces: list[list[int]]

class SceneObject(BaseModel):
    name: str
    location: Location
    mesh_data: MeshData

class SceneRequest(BaseModel):
    request_type: str
    scene_objects: list[SceneObject]

# ==========================================
# ENDPOINT GLOWNY
# ==========================================
@app.post("/process-scene")
async def process_scene(request: SceneRequest):
    
    scene_data_json = request.model_dump_json()

# === WYDRUK WIERZCHOŁKÓW Z BLENDERA ===
    print("\n[WIDOCZNOSC] --- WERTEKSY ODEBRANE Z BLENDERA ---")
    for obj in request.scene_objects:
        print(f"Obiekt: {obj.name}")
        for i, v in enumerate(obj.mesh_data.vertices):
            print(f"  v[{i}]: x={v.x}, y={v.y}, z={v.z}")
    print("-" * 50 + "\n")

    print(f"Odebrano request. Liczba obiektow: {len(request.scene_objects)}")

    prompt = f"""
    Jestes asystentem 3D. Przeanalizuj ponizsza scene z Blendera:
    {scene_data_json}
    
    Zadanie: Scena zawiera obiekt Schody. Popraw Schody tak by bylo ich 10 i wszystkie byly rownej szerokosci.
    
    Wymagania:
    Zwroc WYLACZNIE czysty JSON. Ma on zawierac liste "modified_objects".
    Kazdy obiekt ma miec "name", "location" (x,y,z), oraz "mesh_data" (vertices, faces).
    Przyklad struktury:
    {{
        "modified_objects": [
            {{
                "name": "Gemini_Platforma",
                "location": {{"x": 0.0, "y": 0.0, "z": 0.0}},
                "mesh_data": {{
                    "vertices": [
                        {{"x": -1.0, "y": -1.0, "z": 0.0}}, 
                        {{"x": 1.0, "y": -1.0, "z": 0.0}}, 
                        {{"x": 1.0, "y": 1.0, "z": 0.0}}, 
                        {{"x": -1.0, "y": 1.0, "z": 0.0}}
                    ],
                    "faces": [[0, 1, 2, 3]]
                }}
            }}
        ]
    }}
    """

    model = genai.GenerativeModel('models/gemini-3.1-pro-preview')
    
    try:
        print("Wysylam zapytanie do Gemini API...")
        
        response = model.generate_content(
            prompt,
            generation_config=genai.GenerationConfig(
                response_mime_type="application/json",
                temperature=0.2
            )
        )
        response = request.model_dump_json()
        raw_response = response.text
        print("Otrzymano odpowiedz z serwera.")
        
        ai_mesh_data = json.loads(raw_response)
        
        print("Przetwarzanie JSON zakonczone sukcesem. Odsylam do Blendera.")
        return ai_mesh_data

    except json.JSONDecodeError:
        print("Blad: Odpowiedz nie jest poprawnym formatem JSON.")
        raise HTTPException(status_code=500, detail="Blad parsowania AI na JSON")
        
    except Exception as e:
        print(f"Blad krytyczny: {e}")
        raise HTTPException(status_code=500, detail=str(e))