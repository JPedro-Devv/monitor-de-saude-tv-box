import time
from datetime import datetime, timezone
from typing import Any, Dict

from .collectors.apps import collect_apps_status
from .collectors.display import collect_display_status
from .collectors.network import collect_network_info
from .collectors.system import collect_system_metrics
from .collectors.temperature import get_temperature_c
from .config import config
from .executors import process_commands
from .sender import send_payload


def build_payload() -> Dict[str, Any]:
    system = collect_system_metrics()
    temperature = get_temperature_c()
    network = collect_network_info()
    display = collect_display_status()
    apps = collect_apps_status(config.watched_apps)

    return {
        "device_id": config.device_id,
        "token": config.device_token,
        "reported_at": datetime.now(timezone.utc).astimezone().isoformat(),
        "interval_seconds": config.interval_seconds,
        "metrics": {
            **system,
            "temperature_c": temperature,
        },
        "network": network,
        "display": display,
        "apps": apps,
    }


def run_once() -> None:
    payload = build_payload()
    print(f"[agent] coletado para {payload['device_id']} em {payload['reported_at']}")
    response = send_payload(payload)

    if not response:
        print("[agent] sem resposta do servidor (falha de rede ou erro). Tentará no próximo ciclo.")
        return

    commands = response.get("commands") or []
    if commands:
        print(f"[agent] {len(commands)} comando(s) recebido(s): {[c.get('type') for c in commands]}")
        results = process_commands(commands)
        print(f"[agent] resultados locais: {results}")
        # Evolução: enviar resultados/ack ao servidor (endpoint dedicado ou no próximo ingest)
    else:
        print("[agent] nenhum comando pendente.")


def main() -> None:
    print("[agent] iniciando monitor")
    print(f"[agent] device_id={config.device_id} server={config.ingest_url} intervalo={config.interval_seconds}s")
    print(f"[agent] apps monitorados={config.watched_apps}")

    while True:
        cycle_start = time.time()
        try:
            run_once()
        except Exception as exc:
            # Não deixa o loop morrer por erro pontual de coleta/envio
            print(f"[agent] erro inesperado no ciclo: {exc}")

        elapsed = time.time() - cycle_start
        sleep_for = max(1, config.interval_seconds - int(elapsed))
        print(f"[agent] próximo ciclo em {sleep_for}s\n")
        time.sleep(sleep_for)


if __name__ == "__main__":
    main()
