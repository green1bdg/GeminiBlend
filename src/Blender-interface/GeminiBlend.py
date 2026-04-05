import bpy
import urllib.request
import json

url = "http://127.0.0.1:8000/process-scene"

print("\n--- ROZPOCZYNAM WYSYŁKĘ DO FAST API ---")

# 1. Pobieramy mesh data ze WSZYSTKICH obiektów na scenie
scene_objects_data = []
mesh_count = 0

for obj in bpy.context.scene.objects:
    if obj.type == 'MESH':
        mesh = obj.data
        vertices = [{"x": v.co.x, "y": v.co.y, "z": v.co.z} for v in mesh.vertices]
        faces = [[v for v in p.vertices] for p in mesh.polygons]
        
        scene_objects_data.append({
            "name": obj.name,
            "location": {"x": obj.location.x, "y": obj.location.y, "z": obj.location.z},
            "mesh_data": {
                "vertices": vertices,
                "faces": faces
            }
        })
        mesh_count += 1

if mesh_count == 0:
    print("❌ BŁĄD: Brak obiektów MESH na scenie. Dodaj chociaż sześcian!")
else:
    # 2. Pakujemy do JSONa
    payload_dict = {
        "request_type": "scene_analysis",
        "scene_objects": scene_objects_data
    }
    payload_bytes = json.dumps(payload_dict).encode('utf-8')
    
    print(f"📦 Pakuję {mesh_count} obiektów. Wysyłam do {url}...")
    
    req = urllib.request.Request(
        url, 
        data=payload_bytes, 
        headers={'Content-Type': 'application/json'}, 
        method='POST'
    )
    
    try:
        # 3. Wysyłamy i czekamy (Blender na chwilę "zamrozi" interfejs - to normalne)
        response = urllib.request.urlopen(req, timeout=30)
        response_data = json.loads(response.read().decode())
        
        print("✅ Odebrano odpowiedź z FastAPI!")
        
        # 4. Aktualizujemy scenę
        modified_objects = response_data.get("modified_objects", [])
        
        if modified_objects:
            for mod_obj in modified_objects:
                obj_name = mod_obj.get("name", "Gemini_Object")
                new_mesh_data = mod_obj.get("mesh_data", {})
                
                if new_mesh_data:
                    new_verts = [(v['x'], v['y'], v['z']) for v in new_mesh_data.get('vertices', [])]
                    new_faces = new_mesh_data.get('faces', [])
                    
                    new_mesh = bpy.data.meshes.new(name=f"{obj_name}_AI_Mesh")
                    new_mesh.from_pydata(new_verts, [], new_faces)
                    new_mesh.update()
                    
                    new_blender_obj = bpy.data.objects.new(f"{obj_name}_AI", new_mesh)
                    
                    loc = mod_obj.get("location")
                    if loc:
                        new_blender_obj.location = (loc['x'], loc['y'], loc['z'])
                        
                    bpy.context.collection.objects.link(new_blender_obj)
            
            print(f"✅ SUKCES! Zaktualizowano scenę. Dodano {len(modified_objects)} obiektów.")
        else:
            print("⚠️ FastAPI nie zwróciło nowych obiektów.")

    except urllib.error.URLError as e:
        print(f"❌ BŁĄD POŁĄCZENIA: {e}")
        print("Upewnij się, że Uvicorn działa i nasłuchuje na porcie 8000!")
    except Exception as e:
        print(f"❌ BŁĄD KRYTYCZNY: {e}")

print("--- ZAKOŃCZONO ---")