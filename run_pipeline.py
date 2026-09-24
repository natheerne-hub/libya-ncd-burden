"""Entry point: python run_pipeline.py [--fetch]"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from libya_ncd.pipeline import main  # noqa: E402

if __name__ == "__main__":
    main()
