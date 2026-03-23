import sys
from PySide6.QtWidgets import QApplication
from ui.main_window import MainWindow
from core.llm_client import LLMClient

app = QApplication(sys.argv)
app.setApplicationName("RayAI")
app.setOrganizationName("RayAI")
app.setStyle("Fusion")

mw = MainWindow(model_service=LLMClient())
mw.show()

sys.exit(app.exec())