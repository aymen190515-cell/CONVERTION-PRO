# Espace fichiers dans un Codespace privé

Correctif de b139cd5 : /chips refusait le Host du proxy Codespaces. Le mode
localhost reste le défaut. Aucune lecture matérielle réelle n'est ajoutée.

## Périmètre à approuver avant activation

CP_FILE_ORIGIN sélectionne un serveur **fichiers uniquement**, avec une unique
origine HTTPS explicite. Il remplace l'aperçu véhicule sur ce processus : /chips,
import, simulation, sauvegarde ZIP et comparaison seulement. /api/convert et les
anciennes routes véhicule ne sont pas montées. La route matériel refuse l'hôte
Codespaces ; aucune commande de périphérique n'est accessible.

Les fichiers sélectionnés sont transmis au serveur du Codespace, pas traités
uniquement dans le navigateur. Les données restent en mémoire, plafonnées à
16 snapshots / 32 Mio au total, 8 Mio par import. Un cookie signé, HttpOnly,
Secure et SameSite=Strict lie les snapshots à un navigateur ; un autre navigateur
ne peut ni lire, ni exporter, ni comparer, ni fermer un snapshot, même avec son ID.
Il ne s'agit pas de comptes utilisateurs applicatifs : les onglets partageant le
même cookie partagent cette identité. L'authentification d'entrée reste celle du
port **Private** GitHub. Aucune confiance dans un en-tête de nom d'utilisateur.

Les cookies expirent après 8 heures ; les snapshots expirés deviennent
inaccessibles et sont purgés lors de la prochaine opération de session.
Un arrêt du serveur efface toute la mémoire ; exporter avant redémarrage.
Un seul processus/worker est requis. Pas de stockage permanent ni de CORS permissif.

Le serveur exige le pair TCP loopback et le Host exact configuré. Le lanceur
désactive la réinterprétation des en-têtes proxy par Uvicorn. Les origines de
mutation doivent être identiques à CP_FILE_ORIGIN, avec X-Chip-Workspace: 1.
X-Forwarded-Host/For/Proto n'accordent aucun accès. Pas de wildcard app.github.dev.
Le proxy termine HTTPS ; son lien interne au serveur est HTTP loopback.

## Après validation et intégration du correctif uniquement

Dans Ports, vérifier que 8000 est déjà **Private**. Ne pas le rendre public ni
changer le protocole interne HTTP. Le code ne peut pas attester la visibilité
GitHub et ne modifie aucun réglage réseau ou d'authentification.
Arrêter uniquement son ancien preview avec Ctrl+C dans son terminal, puis,
depuis la racine du dépôt et l'environnement Python installé :

```bash
CP_FILE_ORIGIN='https://literate-bassoon-jr444r9q554p3qwrv-8000.app.github.dev' python preview.py
```

Cette variable vaut uniquement pour ce processus. Ouvrir ensuite /chips sur cette
origine précise. La page doit annoncer « Serveur Codespaces » ; importer un petit
fichier synthétique, exporter le ZIP et comparer memory.bin. Aucune connexion
matérielle n'est nécessaire. Ctrl+C arrête proprement ce serveur.

Si le Codespace ou le port change, utiliser sa nouvelle origine exacte. Si le
proxy ne présente pas le Host externe attendu ou n'arrive pas depuis loopback,
le serveur refuse : relever le code/message sans désactiver les contrôles.
Aucune observation du proxy réel de l'utilisateur n'est revendiquée ici.

Retour au mode local : lancer python preview.py sans CP_FILE_ORIGIN.
L'API fichiers locale exige désormais aussi le cookie initialisé par GET /chips
et l'en-tête X-Chip-Workspace: 1 pour les mutations ; l'interface les gère.
Ne pas utiliser uvicorn preview:app pour ce mode : cette application conserve
son contrôle localhost. Pour un lanceur ASGI explicite utiliser files_app avec
--host 127.0.0.1 --no-proxy-headers et un seul worker.

## Validation reproductible

```bash
python -m pytest -q
```

Les tests reproduisent le Host exact fourni, HTTPS navigateur / HTTP interne,
les cookies Secure, deux navigateurs, import/ZIP/compare/fermeture, expiration,
origines/Host/clients non autorisés et mauvaise configuration proxy. Les octets
sont synthétiques. Cela ne remplace pas la validation finale dans le Codespace.

Sources de configuration :
- https://docs.github.com/en/codespaces/developing-in-a-codespace/forwarding-ports-in-your-codespace
- https://www.uvicorn.org/settings/#http
