"""
Memory organization helpers.

CONVERTION-PRO uses X16 as the canonical internal
representation for 93C76 Jeep Wrangler conversion.

For supported X8 dumps, bytes are swapped inside
each 16-bit word before conversion, then restored
to the original organization afterwards.
"""


class MemoryOrganizationError(RuntimeError):
    pass


def normalize_organization(
    organization: str,
) -> str:
    value = organization.upper().strip()

    if value not in {"X8", "X16"}:
        raise MemoryOrganizationError(
            "Unsupported memory organization. "
            "Expected X8 or X16."
        )

    return value


def swap_word_bytes(data: bytes) -> bytes:
    """
    Swap the two bytes inside every 16-bit word.

    Example:
        12 34 56 78
    becomes:
        34 12 78 56
    """

    if not isinstance(data, (bytes, bytearray)):
        raise TypeError(
            "Memory data must be bytes."
        )

    if len(data) % 2:
        raise MemoryOrganizationError(
            "16-bit word conversion requires "
            "an even number of bytes."
        )

    result = bytearray(data)

    for index in range(
        0,
        len(result),
        2,
    ):
        result[index], result[index + 1] = (
            result[index + 1],
            result[index],
        )

    return bytes(result)


def to_canonical_x16(
    data: bytes,
    organization: str,
) -> bytes:
    """
    Convert supported input organization to
    CONVERTION-PRO's canonical X16 representation.
    """

    organization = normalize_organization(
        organization
    )

    if organization == "X16":
        return bytes(data)

    return swap_word_bytes(data)


def from_canonical_x16(
    data: bytes,
    organization: str,
) -> bytes:
    """
    Restore canonical X16 memory back to the
    organization used by the original input file.
    """

    organization = normalize_organization(
        organization
    )

    if organization == "X16":
        return bytes(data)

    # Swapping twice restores the original layout.
    return swap_word_bytes(data)


def detect_memory_organization(
    data: bytes,
) -> dict:
    """
    Conservatively detect the organization of a supported
    Jeep Wrangler 93C76 dump.

    Detection compares known structural signatures in the
    raw dump and in its pair-swapped representation.

    It never silently guesses when evidence is ambiguous.
    """

    if not isinstance(data, (bytes, bytearray)):
        raise TypeError(
            "Memory data must be bytes."
        )

    if len(data) != 1024:
        raise MemoryOrganizationError(
            "Automatic organization detection currently "
            "supports 1024-byte 93C76 dumps only."
        )

    raw = bytes(data)
    swapped = swap_word_bytes(raw)

    # Known structural strings observed in validated
    # Wrangler 93C76 data.
    #
    # More signatures can be added as additional
    # confirmed vehicle dumps are collected.
    signatures = (
        b"CONTACT",
        b"DEALER",
    )

    raw_matches = [
        signature.decode("ascii")
        for signature in signatures
        if signature in raw
    ]

    swapped_matches = [
        signature.decode("ascii")
        for signature in signatures
        if signature in swapped
    ]

    raw_score = len(raw_matches)
    swapped_score = len(swapped_matches)

    # In our supported Wrangler representation:
    #
    # readable structures directly in the file -> X8
    # readable structures after pair swap       -> X16
    if raw_score > 0 and swapped_score == 0:
        return {
            "organization": "X8",
            "confidence": "HIGH",
            "detected": True,
            "reason": (
                "Known Wrangler structures were found "
                "in the raw byte organization."
            ),
            "raw_matches": raw_matches,
            "swapped_matches": swapped_matches,
        }

    if swapped_score > 0 and raw_score == 0:
        return {
            "organization": "X16",
            "confidence": "HIGH",
            "detected": True,
            "reason": (
                "Known Wrangler structures became valid "
                "after 16-bit word byte swapping."
            ),
            "raw_matches": raw_matches,
            "swapped_matches": swapped_matches,
        }

    return {
        "organization": None,
        "confidence": "AMBIGUOUS",
        "detected": False,
        "reason": (
            "Memory organization could not be determined "
            "with sufficient confidence."
        ),
        "raw_matches": raw_matches,
        "swapped_matches": swapped_matches,
    }
