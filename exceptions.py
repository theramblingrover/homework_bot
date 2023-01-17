class InfoError(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)

class SilentError(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)
