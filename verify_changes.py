
import sys
import os
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path.cwd() / 'clip_typer_pro_ai'))

try:
    from ui.system_tray import SystemTrayApp
    print("Successfully imported SystemTrayApp")

    # Check attributes
    import pystray
    from PIL import Image

    print("Dependencies (pystray, PIL) are importable")

    # Check if methods exist
    if hasattr(SystemTrayApp, 'create_image') and hasattr(SystemTrayApp, 'setup_tray'):
        print("Required methods exist")
    else:
        print("Missing methods")
        sys.exit(1)

except ImportError as e:
    print(f"ImportError: {e}")
    sys.exit(1)
except Exception as e:
    print(f"Error: {e}")
    sys.exit(1)
