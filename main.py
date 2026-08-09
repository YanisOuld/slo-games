"""Entry point. Run: uv run python main.py"""
import logging

from engine.app import App
from games.menu.scene import MenuScene


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
    App(title="SLO Games", first_scene=MenuScene).run()


if __name__ == "__main__":
    main()
