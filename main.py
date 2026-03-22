"""Application entrypoint kept at the repository root for simple launches."""

from warnings import filterwarnings

from app.controller import ApplicationController


def main():
    """Start the Fundamental Frequency desktop application."""

    filterwarnings("ignore")
    ApplicationController().run()


if __name__ == "__main__":
    main()
