import os
from dotenv import load_dotenv
from google import genai

# Cargar la clave desde el archivo .env
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    print("❌ ERROR: No se encontró GEMINI_API_KEY en el archivo .env")
    exit(1)

print(f"🔑 Clave API encontrada: {api_key[:10]}...")

# Inicializar el cliente (usando la misma librería que InnovaFile)
try:
    client = genai.Client(api_key=api_key)
    print("✅ Cliente de Gemini inicializado correctamente.")
except Exception as e:
    print(f"❌ ERROR al inicializar el cliente: {e}")
    exit(1)

# Hacer una petición de prueba muy simple
try:
    print("\n🧪 Enviando petición de prueba al modelo...")
    response = client.models.generate_content(
        model="gemini-3.1-flash-lite",  # <-- CAMBIO AQUÍ
        contents="Responde solo con la palabra 'FUNCIONA' si puedes leer esto."
    )
    
    # Mostrar la respuesta
    print("\n--- RESPUESTA DEL MODELO ---")
    print(response.text)
    print("----------------------------")
    
    if "FUNCIONA" in response.text.upper():
        print("\n🎉 ¡ÉXITO! Gemini está funcionando correctamente.")
    else:
        print("\n⚠️ El modelo respondió, pero no con la palabra esperada. Revisa la respuesta.")

except Exception as e:
    print(f"\n❌ ERROR durante la petición: {e}")
    print("Esto puede ser por un problema de cuota, un modelo no disponible o un error temporal del servidor de Google.")