import sys
from pathlib import Path
import os

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

# Now that the path is set, we can import and run the main app
from main_app import main

if __name__ == "__main__":
    main()
