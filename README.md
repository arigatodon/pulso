# Pulso · monitor cardíaco para Polar H10

Aplicación web de un solo archivo (`index.html`) que se conecta al Polar H10 por
Web Bluetooth y muestra en vivo pulsaciones, ECG, variabilidad cardíaca y más.
No necesita instalación ni conexión a Internet.

## Arranque rápido

| Sistema | Qué hacer |
|---|---|
| **Windows** | Doble clic en `start.bat`. Se abre el navegador en `http://localhost:8765`. |
| **macOS / Linux** | Ejecuta `./start.sh` en una terminal (o doble clic si tu gestor de archivos lo permite). |
| **Sin Python** | Abre `index.html` directamente con Chrome o Edge. También funciona. |
| **Android** | Chrome soporta Web Bluetooth. Sirve la carpeta con HTTPS o copia `index.html` al móvil y ábrelo con Chrome. |
| **iPhone / iPad** | Safari no soporta Web Bluetooth. Usa el navegador **Bluefy** (App Store) y abre `index.html`. |

Después:

1. Ponte la banda con los electrodos humedecidos. El H10 solo emite cuando detecta piel.
2. Pulsa **Conectar Polar H10** y elige el sensor en el diálogo del navegador.
3. El ECG se activa solo. Si no aparece, mira el apartado *Solución de problemas*.

Sin sensor a mano, **Modo demo** genera datos simulados para probar la interfaz.

## Requisitos del navegador

- **Chrome** o **Edge** (también Opera, Brave y Chrome para Android). Firefox y Safari no soportan Web Bluetooth.
- **Windows 10/11 y macOS**: funciona sin configurar nada.
- **Linux**: activa `chrome://flags/#enable-experimental-web-platform-features` y reinicia el navegador. Necesita BlueZ 5.41 o superior.
- La página debe abrirse por `http://localhost`, por `https` o como archivo local (`file://`).
- El H10 solo admite **una conexión Bluetooth a la vez**: cierra Polar Flow, Polar Beat o cualquier app que esté usando el sensor.

## Qué muestra

**Del Polar H10**

- Pulsaciones en tiempo real con un corazón que late al ritmo real (intervalos RR).
- Zona de entrenamiento (6 zonas) según tu frecuencia máxima, y tiempo acumulado en cada zona.
- Gráfica de frecuencia cardíaca con ventana de 1, 5 o 15 minutos o sesión completa.
- ECG en vivo a 130 Hz con rejilla tipo papel a 25 mm/s.
- Nivel de batería y reconexión automática.

**Variabilidad cardíaca (HRV), calculada de los intervalos RR**

| Métrica | Qué es |
|---|---|
| RMSSD | Variabilidad a corto plazo (actividad parasimpática). Más alto suele indicar mejor recuperación. |
| SDNN | Variabilidad global de la sesión. |
| pNN50 | Porcentaje de latidos consecutivos que difieren más de 50 ms. |
| SD1 / SD2 | Ejes del diagrama de Poincaré: variabilidad rápida y lenta. |
| Respiración | Frecuencia respiratoria estimada a partir de la arritmia sinusal respiratoria (necesita ~40 s). |
| Índice de estrés | Índice de Baevsky sobre los últimos 5 min. Menos de 150 es normal en reposo. |
| Balance LF/HF | Reparto espectral entre baja (0,04–0,15 Hz) y alta frecuencia (0,15–0,40 Hz). Necesita 2 min. |
| Energía | Kilocalorías estimadas con la fórmula de Keytel (requiere peso, edad y sexo). |

**Oxígeno en sangre (SpO₂)**

El Polar H10 **no tiene sensor de oxígeno**: es una banda de ECG y solo mide actividad
eléctrica del corazón. Para ver SpO₂ la app puede conectar un segundo dispositivo:
cualquier **oxímetro de dedo Bluetooth que implemente el perfil estándar
*Pulse Oximeter* (PLX, servicio 0x1822)**. Pulsa **Conectar oxímetro** y elige el dispositivo.
Muchos oxímetros baratos usan protocolos propietarios y no aparecerán en la lista; los que
anuncian compatibilidad con "Bluetooth SIG PLX" o "estándar BLE" sí funcionan.

**Exportación**: CSV de pulso/RR/SpO₂ por segundo y CSV del ECG completo (hasta 1 h en memoria).

## Solución de problemas

**El ECG no aparece**

La app prueba cuatro estrategias de arranque seguidas (orden normal, detener y reiniciar,
reactivar notificaciones, consultar ajustes). En la tarjeta del ECG hay una línea de diagnóstico
y, abajo en *Ajustes*, un registro con lo que responde el sensor. El botón **Copiar diagnóstico**
copia todo al portapapeles para compartirlo.

Para saber si el problema está en el sensor o en el navegador, ejecuta el diagnóstico sin navegador
(cierra antes la app web y Polar Flow):

```bash
pip install bleak
python diagnostico_ecg.py 10
```

Imprime las respuestas del sensor y cuántas muestras de ECG llegan en 10 segundos.

Casos típicos:

- *"ECG SIN PAQUETES"* con la orden aceptada: el sensor no tiene buen contacto con la piel.
  Humedece los electrodos y ajusta la banda. En Linux, comprueba que BlueZ esté actualizado.
- *"ya estaba en ese estado"*: el ECG seguía activo de una conexión anterior. Pulsa
  **Detener ECG** y luego **Activar ECG**.
- *"estado inválido"*: la app detiene y reintenta sola; si persiste, apaga y enciende el sensor
  (quítalo de la banda 10 s).
- *"servicio PMD no encontrado"*: el sensor conectado no es un H10 o su firmware es muy antiguo.
  Actualiza el firmware con la app Polar Flow.
- El registro muestra *"Frame ECG de tipo 0x…"*: envíanos esa línea; el firmware usa un
  formato distinto del esperado.

**No aparece el sensor al conectar**

- Cierra Polar Flow / Beat y cualquier reloj emparejado con el H10.
- Asegúrate de llevar la banda puesta: apagado, el H10 no se anuncia.
- En Windows, no empareges el H10 desde *Configuración → Bluetooth*; deja que lo gestione el navegador.

**Se desconecta**

La app reintenta 5 veces. Si el sensor está lejos o la batería baja (menos del 20 %), cámbiala (CR2025).

## Notas técnicas

- Frecuencia cardíaca: servicio estándar `0x180D`, característica `0x2A37` (incluye RR en 1/1024 s).
- Batería: servicio `0x180F`.
- ECG: servicio PMD `fb005c80-02e7-f387-1cad-8acd2d8df0c8`, control `…c81`, datos `…c82`.
  Orden de inicio `02 00 00 01 82 00 01 01 0E 00` (130 Hz, 14 bits). Muestras de 24 bits con
  signo en microvoltios, cabecera de 10 bytes (tipo, marca de tiempo, tipo de frame).
- Oxímetro: perfil PLX, características *Continuous Measurement* (0x2A5F) y *Spot-check* (0x2A5E),
  valores en formato SFLOAT IEEE‑11073.
- Todo se procesa en el navegador; no se envía ningún dato a Internet.

No es un dispositivo médico: los valores son orientativos y no sustituyen una valoración clínica.

## Pruébalo en línea

https://arigatodon.github.io/pulso/ (Chrome o Edge, con Bluetooth activado).

## Licencia

MIT. Ver `LICENSE`.
