from domain.models import AppSettings
from infrastructure.system import PsutilProcessService
from infrastructure.network import TcpNetworkService
from ui.viewmodels.main_viewmodel import MainViewModel
from ui.views.main_window import start_app


def main():
    # 1. Configuration
    settings = AppSettings.load()
    
    # 2. Infrastructure Services
    process_service = PsutilProcessService()
    network_service = TcpNetworkService()
    
    # 3. ViewModels
    vm = MainViewModel(process_service, network_service, settings)
    
    # 4. Start UI
    start_app(vm)


if __name__ == "__main__":
    main()
