# Plateforme multi-puces — premier jalon

Base : `d8c99a47d28b9ad5fd8360cf38513acdb37b5271`. Développement original en
copie isolée, sans code propriétaire, licence ou algorithme Orange5 réutilisé.

## Utilisation et couverture

Lancer l'aperçu selon le README et ouvrir `/chips` (bouton « Espace puces »).
Le parcours nécessite le serveur local, pas un serveur Codespaces. Aucun
navigateur ni périphérique ne s'ouvre automatiquement.

- Catalogue initial : ST M24C32 documentée mais non qualifiée, fichier brut sans
  identification physique et familles futures indiquées « référence seulement ».
- Fichier ou simulation choisis explicitement ; aucun buffer chargé par défaut.
  Provenance, taille, région, SHA-256, aperçu hexadécimal limité à 256 octets.
- Taille contrôlée : 4096 octets pour M24C32, 8 Mio maximum pour un fichier brut.
  Une taille correcte ne prouve pas la puce d'origine.
- Sauvegarde ZIP : memory.bin intégral, manifest.json avec provenance et journal.
  L'archive est vérifiée avant transfert ; son enregistrement sur le disque de
  l'utilisateur n'est pas confirmé par l'application.
- Comparaison de fichiers : nombre exact de différences et 64 premières positions,
  y compris les octets manquants/supplémentaires. Aucune relecture matérielle.
- Journal local non signé, limité à 100 événements. Sessions temporaires : 16 au
  maximum et 32 Mio au total. Redémarrer perd les sessions non exportées. Une
  fermeture supprime uniquement la session mémoire, aucun fichier utilisateur.
- Un seul worker serveur requis. Routes locales, contrôles d'origine, requêtes
  bornées ; aucun chemin utilisateur ouvert ni fichier écrit sur le serveur.

## Registre et sécurité des modes

Clé : puce, interface, transport, variante du contrôleur, mode, package et mask.
Aucune compatibilité n'est héritée automatiquement d'une autre combinaison.
Le registre distingue documentation, qualification de banc, identité confirmée,
préconditions et effets : UNKNOWN, NO_NONVOLATILE_WRITE, MAY_ERASE_OR_WRITE.
Une capacité même qualifiée est bloquée si le mode peut effacer/écrire ou si
ses effets sont inconnus. Les préconditions doivent être confirmées avant pilote.

Le nom « Read » ne garantit pas une opération non destructive : le
[manuel officiel SRS Renesas](https://www.scorpio-lk.com/downloads/Orange5/Read_Write_SRS_MCU_CAN_eng.pdf)
décrit des modes dont les effets dépassent une simple lecture. Aucun protocole
SRS de ce manuel n'est implémenté ici.

| Domaine | État |
| --- | --- |
| Parcours véhicules antérieur | Conservé ; faux Read Memory matériel corrigé |
| Fichier, simulation, backup, hash, diff, journal | Implémentés et testés sans matériel |
| Catalogue Orange5 complet | Dataset séparé, non intégré |
| Orange5 et ses adaptateurs/contrôles électriques | Non intégrés ; API autorisée à obtenir |
| vLinker/CAN EEPROM | Non implémenté ; protocole manquant |
| ST M24C32 direct I2C | Routine expérimentale héritée, sans qualification physique |
| Autres EEPROM, SPI, MicroWire, MCU/debug/boot | Références de planification, aucun pilote |
| Écriture, effacement, déverrouillage | Bloqués, aucun endpoint exécutable |
| Terminal, analyseur, oscilloscope, générateur | Non implémentés ; matériel/API spécifiques requis |

Le vLinker ne remplace pas le programmateur Orange5. Les licences et adaptateurs
sont distincts ; aucun CFG/HPL/HPX n'est importé. Les références de catalogue ne
sont pas des drivers Conversion Pro. Les 2150 lignes brutes annoncées de
l'inventaire ne sont pas 2150 puces uniques ni des compatibilités acquises.

Sources officielles : https://www.scorpio-lk.com/orange5.html,
https://www.scorpio-lk.com/orange5-eeprom.html,
https://www.scorpio-lk.com/orange5-mcu.html,
https://www.scorpio-lk.com/orange5-motorola.html,
https://www.scorpio-lk.com/orange5-renesas.html.

Dataset Library fourni séparément, **non matérialisé et non intégré** :
`Orange5-reference-inventory.json`, `libfile_e7880b6cbbe481918fd18455510dcdd8`.
Son import futur doit conserver URLs/date/hash/libellés bruts/doublons et
REFERENCE_ONLY, sans créer de capacité VALIDATED.

## Plan et décisions bloquantes

1. Comparer les modifications actives du Codespace avant intégration.
2. Importer les références avec attribution et variantes explicites, sans code
   ni fichiers de licence propriétaires.
3. Choisir un matériel réellement documenté. Pour Orange5 : API/SDK autorisée et
   conditions de licence à obtenir ; sinon backend original pour un autre matériel.
4. Documenter chaque puce/mode/zone/package/mask : brochage et tensions exacts,
   identification, sémantique des opérations, erreurs et limites. Ne rien deviner.
5. Qualifier un banc autorisé contre des données connues et des cas d'erreur.
   Les tests à doublures ne suffisent jamais à déclarer une capacité matérielle.
6. Ajouter ensuite l'exécution locale qualifiée. Écriture/effacement restent une
   portée séparée. Aucune équivalence complète Orange5 ni lecture universelle promise.

L'absence de SDK/protocole bloque le matériel, pas ce jalon fichier et registre.
