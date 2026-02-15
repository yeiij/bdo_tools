"""Main entry point."""

import os

from domain.models import AppSettings
from infrastructure.gpu import NvidiaGpuService
from infrastructure.network import TcpNetworkService
from infrastructure.system import PsutilProcessService, PsutilSystemService
from ui.viewmodels.main_viewmodel import MainViewModel
from ui.views.main_window import start_app


def main():
    # 1. Configuration
    settings = AppSettings.load()
    settings_path = AppSettings.default_path()
    if not os.path.exists(settings_path):
        settings.save(settings_path)

    # 2. Infrastructure Services
    process_service = PsutilProcessService()
    system_service = PsutilSystemService()
    network_service = TcpNetworkService()
    gpu_service = NvidiaGpuService()

    # 3. ViewModels
    vm = MainViewModel(
        process_service=process_service,
        network_service=network_service,
        system_service=system_service,
        gpu_service=gpu_service,
        settings=settings,
        persist_settings_on_init=False,
    )

    # 4. Start UI
    try:
        start_app(vm)
    finally:
        gpu_service.shutdown()


if __name__ == "__main__":
    main()
