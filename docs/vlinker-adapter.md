# Connexion vLinker : adaptateur uniquement

Le transport Web Serial de l'aperçu ouvre le port choisi par l'utilisateur.
Le débit proposé est 115200 bit/s côté PC, modifiable explicitement ; aucun débit
CAN n'est sélectionné. Une seule commande peut être active. Les réponses sont
accumulées jusqu'au prompt `>`, avec retrait de l'écho, limite de 8192 caractères
et délai de 3 secondes. Un timeout ferme la session : reconnecter avant de
réessayer, pour ne pas attribuer une réponse tardive à une autre commande.

Seules `ATI` (identité déclarée) et `ATRV` (tension déclarée à l'entrée de
l'adaptateur, sur clic) sont autorisées. Ces commandes locales sont documentées
par Elm Electronics : https://www.elmelectronics.com/wp-content/uploads/2016/07/ELM327DS.pdf
Une réponse ELM327 ne prouve pas le modèle FS ni l'authenticité du matériel.
Aucune commande OBD, sélection de protocole, reset, adresse CAN ou commande de
cluster n'est émise. Le journal JSON contient les fragments RX, commandes TX,
états et erreurs (2000 événements récents au maximum). Il reste dans le navigateur
jusqu'à son export ; aucun contenu mémoire de cluster n'y est collecté.

Le pilote de cluster est un contrat distinct (`ClusterDriver`). Son implémentation
actuelle refuse identification et lecture. Une future implémentation devra
résoudre le véhicule et la variante, documenter le protocole et la région,
qualifier le mode de lecture au banc et fournir une provenance séparée.
La 93C76 est une cible déclarée par l'utilisateur, pas une puce confirmée pour
l'ensemble des Wrangler 2012–2018. Toyota reste désactivé.

## Essai Windows sans cluster

1. Laisser le GODIAG et toute prise de module déconnectés. Brancher uniquement
   l'USB du vLinker au PC. Fermer FORScan, terminaux série et applications qui
   utilisent le même port. Si nécessaire, installer le pilote VCP FTDI recommandé
   par le guide constructeur depuis https://ftdichip.com/drivers/vcp-drivers/.
2. Avec le projet et ses dépendances sur le PC, lancer `python preview.py` depuis
   sa racine, sans `CP_FILE_ORIGIN`. Ouvrir `http://127.0.0.1:8000` dans Chrome ou
   Edge. Autre possibilité : l'aperçu véhicule du Codespace en HTTPS, dans Chrome
   ou Edge sur le PC ; Web Serial accède au PC, pas au serveur. Le serveur
   `CP_FILE_ORIGIN` fichiers uniquement ne présente pas ce panneau.
3. Cliquer « Connecter le vLinker USB », choisir son port COM. Une réponse ATI
   reconnue affiche « Adaptateur : connecté ». Les deux états cluster/EEPROM
   restent NON. Un refus de permission, port occupé, erreur ou absence de prompt
   est affiché ; aucune donnée simulée ne remplace une réponse absente.
4. Facultativement cliquer « Tension adaptateur ». ATRV ne valide ni alimentation
   du cluster ni identité de sa puce. Débrancher l'USB pour vérifier le retour à
   déconnecté ; reconnecter puis refaire la sélection du port.
5. Exporter le journal JSON, puis cliquer « Déconnecter » pour libérer le port.

Le guide vLinker FS USB décrit les voyants lors du branchement USB au PC et
recommande 115.2 kbit/s ; son parcours de diagnostic complet ajoute ensuite
l'OBD et le contact véhicule :
https://m.media-amazon.com/images/I/B1NcSBW-rSL.pdf
La fiche Vgate annonce les systèmes automobiles 12 V/24 V :
https://vgatemall.com/products-detail/i-19/
Ces documents ne garantissent pas toutes les réponses ATI/ATRV avec l'USB seul
et ne spécifient pas le montage GODIAG de l'utilisateur. Commencer par l'USB seul ;
un timeout ne prouve pas à lui seul un manque d'alimentation. Avant toute
alimentation externe de banc, obtenir la référence exacte et la notice GODIAG,
ainsi que les exigences Vgate correspondantes. Aucun brochage, pontage ou
branchement d'alimentation externe n'est prescrit ici. Le 12.0 V du Connection
Guide Jeep reste une donnée de ce guide, pas une instruction d'alimentation de
l'adaptateur ou de la puce.

Tests : `pytest -q tests/test_vlinker_transport.py` lance les scénarios Web Serial
synthétiques sous Node.js, sans périphérique. Aucun essai matériel Windows n'a
été effectué dans le Codespace.
