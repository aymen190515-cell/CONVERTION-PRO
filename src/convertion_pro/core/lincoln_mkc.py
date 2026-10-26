"""Conversion Lincoln MKC 2017, EEPROM 24C32, regle donnee par Aymen.

Octet 0x2D6 (ligne 2D, colonne 06) :
  0x81 = KM, icone frein en symbole
  0x01 = MILES, icone frein en texte BRAKE

Regle : changer uniquement cet octet, rien d'autre.
Aucun recalcul de checksum n'est inclus a ce stade :
checksum non confirme par Aymen a ce jour.
A valider sur banc : lire avec Orange5, convertir, reecrire,
verifier l'unite et l'icone frein affichees.
"""

OFFSET = 0x2D6
KM = 0x81
MILES = 0x01
EEPROM_SIZE = 4096


def _convert(data: bytes, expected: int, target: int) -> bytes:
    if len(data) != EEPROM_SIZE:
        raise ValueError(
            f"Taille EEPROM inattendue : {len(data)} octets, "
            f"attendu {EEPROM_SIZE} pour une 24C32."
        )
    if data[OFFSET] != expected:
        raise ValueError(
            f"Octet 0x2D6 inattendu : 0x{data[OFFSET]:02X}, "
            f"attendu 0x{expected:02X}."
        )
    out = bytearray(data)
    out[OFFSET] = target
    return bytes(out)


def convert_miles_to_km(data: bytes) -> bytes:
    """MILES (0x01) -> KM (0x81), icone frein texte -> symbole."""
    return _convert(data, MILES, KM)


def convert_km_to_miles(data: bytes) -> bytes:
    """KM (0x81) -> MILES (0x01), icone frein symbole -> texte."""
    return _convert(data, KM, MILES)
