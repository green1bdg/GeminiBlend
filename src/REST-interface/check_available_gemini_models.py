import os
import json
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError("Brak klucza GEMINI_API_KEY w pliku .env!")

genai.configure(api_key=api_key)
app = FastAPI()

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

@app.post("/process-scene")
async def process_scene(request: SceneRequest):
    
    scene_data_json = request.model_dump_json(indent=4)
    
    # === [WIDOCZNOŚĆ 1 B]: JSON odebrany przez FastAPI z Blendera ===
    print("\n" + "="*60)
    print("[FASTAPI ODEBRAŁO] <- [BLENDER]:")
    print(scene_data_json)
    print("="*60 + "\n")

    prompt = f"""
    Jestes asystentem 3D. Przeanalizuj ponizsza scene z Blendera w formacie JSON:
    {scene_data_json}
    
    Zadanie:
    1. Znajdz w powyzszych danych obiekt, ktorego klucz "name" to "Schody" (lub zawiera slowo schody).
    2. Przeanalizuj jego polozenie (location) oraz siatke wierzcholkow (vertices).
    3. Wygeneruj jeden nowy obiekt typu MESH. Wyrownaj schody tak zeby byly tej samej glebokosci.
    4. Zwroc obiekt ktory ma taka sama nazwe.
    
    Wymagania:
    Zwroc WYLACZNIE czysty JSON. Ma on zawierac liste "modified_objects".
    Kazdy obiekt ma miec "name", "location" (x,y,z), oraz "mesh_data" (vertices, faces).
    Przyklad struktury:
    {{
        "modified_objects": [
            {{
                "name": "Gemini_Nowy_Stopien",
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

    # === [WIDOCZNOŚĆ 2]: Treść przekazywana do SaaS Gemini ===
    print("="*60)
    print("[FASTAPI WYSYŁA] -> [GEMINI SAAS] (Treść Prompta):")
    print(prompt)
    print("="*60 + "\n")

    model = genai.GenerativeModel('gemini-3.1-pro-preview')
    
    try:
        response = model.generate_content(
            prompt,
            generation_config=genai.GenerationConfig(
                response_mime_type="application/json",
                temperature=0.2
            )
        )
        
        raw_response = response.text
        
        # === [WIDOCZNOŚĆ 3]: JSON odebrany przez FastAPI z SaaS Gemini ===
        print("="*60)
        print("[FASTAPI ODEBRAŁO] <- [GEMINI SAAS] (Raw Response):")
        print(raw_response)
        print("="*60 + "\n")
        
        ai_mesh_data = json.loads(raw_response)
        
        # === [WIDOCZNOŚĆ 4]: JSON wysyłany do Blendera ===
        print("="*60)
        print("[FASTAPI WYSYŁA] -> [BLENDER] (Zwracany JSON):")
        print(json.dumps(ai_mesh_data, indent=4))
        print("="*60 + "\n")
        
        return ai_mesh_data

    except json.JSONDecodeError:
        print("Blad parsowania AI na JSON. Surowa odpowiedz:")
        print(raw_response)
        raise HTTPException(status_code=500, detail="Blad parsowania AI na JSON")
        
    except Exception as e:
        print(f"Blad krytyczny: {e}")
        raise HTTPException(status_code=500, detail=str(e))