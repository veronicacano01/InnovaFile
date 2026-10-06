# Agente de sincronización automática de InnovaFile

Este agente es la parte que permite que InnovaFile siga detectando documentos aunque el navegador esté cerrado.

## Primera configuración

1. Inicia InnovaFile.
2. Entra con una cuenta que tenga permiso de sincronización.
3. En Documentos, usa **Generar token del agente**.
4. Copia el token. Solo se muestra una vez.
5. Ejecuta `CONFIGURAR_AGENTE.bat`.
6. Escribe la dirección de InnovaFile, pega el token y selecciona la carpeta del cliente.
7. El agente hace una revisión inicial de los documentos existentes.
8. Después queda vigilando la carpeta.

## Qué hace automáticamente

- Detecta archivos nuevos.
- Detecta archivos modificados.
- Revisa subcarpetas.
- Envía los documentos compatibles a InnovaFile.
- Gemini analiza el contenido y decide la categoría.
- Si el documento ya estaba sincronizado y no cambió, no lo vuelve a duplicar.

## Para que siga funcionando

El agente debe estar ejecutándose. Puedes abrir `INICIAR_AGENTE.bat` después de iniciar Windows. Para automatizarlo al encender la computadora, crea un acceso directo de ese archivo en la carpeta de Inicio de Windows.

El navegador no necesita permanecer abierto.
