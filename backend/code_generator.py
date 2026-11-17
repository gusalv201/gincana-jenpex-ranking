import secrets

_CHARACTERS = "23456789ABCDEFGHJKLMNPQRSTUVWXYZ"
PARTICIPANT_CODE_LENGTH = 6


def participant_code_generator() -> str:
    return "".join(
        secrets.choice(_CHARACTERS) for _ in range(PARTICIPANT_CODE_LENGTH)
    )