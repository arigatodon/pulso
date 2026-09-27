#!/usr/bin/env python3
"""Diagnóstico del ECG del Polar H10 sin navegador.

Uso:  pip install bleak
      python diagnostico_ecg.py [segundos]

Busca el sensor, activa el ECG por el servicio PMD y muestra lo que responde.
Funciona en Windows, macOS y Linux. Cierra la app web y Polar Flow antes (una sola conexión a la vez).
"""
import asyncio, sys, struct, time

try:
    from bleak import BleakScanner, BleakClient
except ImportError:
    print("Falta la librería bleak. Instálala con:  pip install bleak")
    sys.exit(1)

PMD_CONTROL = "fb005c81-02e7-f387-1cad-8acd2d8df0c8"
PMD_DATA    = "fb005c82-02e7-f387-1cad-8acd2d8df0c8"
HR_MEAS     = "00002a37-0000-1000-8000-00805f9b34fb"
ECG_START   = bytes([0x02, 0x00, 0x00, 0x01, 0x82, 0x00, 0x01, 0x01, 0x0E, 0x00])
ECG_STOP    = bytes([0x03, 0x00])
SETTINGS_Q  = bytes([0x01, 0x00])
STATUS = ["OK", "op inválido", "tipo inválido", "no soportado", "longitud inválida", "parámetro inválido",
          "ya en ese estado", "resolución inválida", "frecuencia inválida", "rango inválido", "MTU inválido",
          "canales inválidos", "estado inválido", "en el cargador"]

def hx(b): return " ".join(f"{x:02x}" for x in b)

async def main(seconds):
    print("Buscando Polar H10 (llévalo puesto con los electrodos húmedos)…")
    dev = await BleakScanner.find_device_by_filter(lambda d, a: (d.name or "").startswith("Polar"), timeout=15)
    if not dev:
        print("No se encontró ningún sensor Polar. ¿Está puesto? ¿Otra app lo tiene conectado?")
        return
    print(f"Encontrado: {dev.name} [{dev.address}]")
    frames = {"n": 0, "bytes": 0, "samples": 0, "first": None, "types": {}}
    hr = {"n": 0, "last": None}

    def on_ctrl(_, data):
        b = bytes(data)
        if b and b[0] == 0xF0 and len(b) >= 4:
            print(f"  respuesta PMD op={b[1]} tipo={b[2]} estado={b[3]} ({STATUS[b[3]] if b[3] < len(STATUS) else '?'})  [{hx(b)}]")
        else:
            print(f"  notificación PMD: {hx(b)}")

    def on_data(_, data):
        b = bytes(data)
        frames["n"] += 1; frames["bytes"] += len(b)
        if frames["first"] is None:
            frames["first"] = hx(b[:14])
            print(f"  primer paquete de datos ({len(b)} bytes): {frames['first']}…")
        if len(b) >= 10:
            key = (b[0], b[9]); frames["types"][key] = frames["types"].get(key, 0) + 1
            if b[0] == 0 and b[9] == 0:
                n = (len(b) - 10) // 3
                frames["samples"] += n
                if frames["n"] % 20 == 1:
                    v = int.from_bytes(b[10:13], "little", signed=True)
                    print(f"  {frames['n']:4d} paquetes · {frames['samples']} muestras · primera de este paquete {v} µV")

    def on_hr(_, data):
        b = bytes(data); hr["n"] += 1
        hr["last"] = b[1] if not (b[0] & 1) else struct.unpack_from("<H", b, 1)[0]

    async with BleakClient(dev, timeout=20) as client:
        print(f"Conectado. MTU={getattr(client, 'mtu_size', '?')}")
        svcs = client.services
        names = [s.uuid for s in svcs]
        print("Servicios:", ", ".join(u[4:8] if u.startswith("0000") else u for u in names))
        if not any(u.startswith("fb005c80") for u in names):
            print("¡El sensor NO expone el servicio PMD! No es un H10 o el firmware es muy antiguo → actualiza con Polar Flow.")
            return
        try:
            feat = await client.read_gatt_char(PMD_CONTROL)
            print(f"Características PMD: {hx(feat)}  → ECG {'soportado' if len(feat) > 1 and feat[1] & 1 else 'NO soportado'}")
        except Exception as e:
            print("No se pudo leer el punto de control:", e)
        await client.start_notify(HR_MEAS, on_hr)
        await client.start_notify(PMD_CONTROL, on_ctrl)
        await client.start_notify(PMD_DATA, on_data)
        print("Consultando ajustes ECG admitidos…")
        await client.write_gatt_char(PMD_CONTROL, SETTINGS_Q, response=True)
        await asyncio.sleep(1)
        print("Enviando orden de inicio ECG 130 Hz…")
        await client.write_gatt_char(PMD_CONTROL, ECG_START, response=True)
        t0 = time.time()
        while time.time() - t0 < seconds:
            await asyncio.sleep(1)
        print("Deteniendo ECG…")
        try: await client.write_gatt_char(PMD_CONTROL, ECG_STOP, response=True)
        except Exception: pass
        await asyncio.sleep(0.5)
    print("\n=== RESUMEN ===")
    print(f"Pulso: {hr['n']} notificaciones, último {hr['last']} lpm")
    print(f"ECG: {frames['n']} paquetes, {frames['bytes']} bytes, {frames['samples']} muestras (~{frames['samples']/max(seconds,1):.0f} Hz)")
    print(f"Tipos de paquete (tipo, frame): {frames['types']}")
    if frames["n"] == 0:
        print("→ El sensor no envió datos ECG. Si la orden fue aceptada (estado 0) revisa contacto con la piel y firmware.")
    elif frames["samples"] == 0:
        print("→ Llegan paquetes pero con un formato distinto al esperado. Comparte esta salida.")
    else:
        print("→ El ECG funciona a nivel Bluetooth: el problema está en el navegador. Comparte esta salida y el diagnóstico de la app.")

if __name__ == "__main__":
    secs = int(sys.argv[1]) if len(sys.argv) > 1 else 10
    try:
        asyncio.run(main(secs))
    except KeyboardInterrupt:
        pass
