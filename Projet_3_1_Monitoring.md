## Reconstruction de l'Infrastructure

Votre mission est de recréer l'orchestration complète. Pour vous aider, voici les concepts clés et les extraits de configuration que vous devrez implémenter et lier entre eux.

Le projet aura l'allure suivante:
```plaintext
PROJET_MONITORING/
├── .env                          # Variables (FASTAPI_PORT, DB_PASSWORD, etc.)
├── docker-compose.yml            # Orchestration des 5 services
├── logs/                         # Volume partagé pour les logs Loguru
│   ├── api.log
│   └── streamlit.log
├── fastapi_app/                  # Dossier source de l'API
│   ├── Dockerfile                # À générer (base uv-alpine conseillée)
│   ├── pyproject.toml            # Dépendances (FastAPI, python-multipart, etc.)
│   ├── uv.lock                   # Lockfile généré par uv
│   └── main.py                   # Code de l'API avec endpoint /metrics
├── streamlit_app/                # Dossier source du Frontend
│   ├── Dockerfile                # À générer
│   ├── pyproject.toml            # Dépendances (Streamlit, requests)
│   ├── uv.lock
│   └── app.py                    # Interface utilisateur
├── prometheus/                   # Configuration du serveur de métriques
│   └── prometheus.yml            # Scrape configs (targets: api et node-exporter)
└── grafana/                      # Configuration de la visualisation
    └── provisioning/             # Dossier scanné par Grafana au démarrage
        ├── datasources/
        │   └── datasources.yml   # Connexion automatique à Prometheus
        └── dashboards/
            ├── dashboards.yml    # Déclaration du provider de JSON
            └── system_health.json # (Optionnel) Export du dashboard 1860
```

---

## Stack Monitoring & MLOps

Avant de vous lancer dans le code, suivez rigoureusement ces étapes pour garantir le succès de votre déploiement :

1. **Exploration Globale** : Lisez le `README.md` jusqu'au bout. Cela vous donnera une vision claire de l'architecture finale et de l'ampleur du travail à accomplir.
2. **Analyse des Directives** : Lisez attentivement le fichier `exercice.md` pour bien assimiler les contraintes techniques et les livrables attendus.
3. **Documentation & Compréhension** : Pour les codes concernant **Streamlit** et **FastAPI**, vous devez dans un premier temps ajouter tous les **docstrings** (norme Google) et les **commentaires** nécessaires. Cette étape est cruciale : elle vous permettra de comprendre réellement le fonctionnement de **Loguru**, l'exposition des métriques **Prometheus** et la logique des réseaux **Docker** [cite: 2026-02-23].
4. **Préparation de l'Environnement** : Avant de lancer les conteneurs, assurez-vous que le dossier `/logs` ainsi que l'arborescence complète de `/prometheus` et `/grafana` (sous-dossiers et fichiers de configuration) sont bien créés sur votre machine.
5. **Validation** : Suivez les directives pas à pas du `README.md` pour tester chaque service et vous assurer que le flux de données est opérationnel.

---

### 1. Architecture du Docker Compose (L'Architecte)

Le fichier `docker-compose.yml` définit comment les services communiquent et comment ils conservent leurs données. Vous devez configurer les blocs suivants :

* **Communication Inter-Services (`networks`)** :
Sans réseau commun, les conteneurs sont isolés. En utilisant `app_network`, vous permettez à Streamlit de contacter l'API via son nom de service.
* **Persistance et Partage (`volumes`)** :
Les volumes permettent de sortir les logs des conteneurs vers votre machine hôte et d'injecter vos configurations.

#### Configuration cible pour l'API et Streamlit :

```yaml
  api:
    ...
    volumes:
      - ./logs:/logs
    networks:
      - app_network
```
```yaml
  streamlit:
    ...
    volumes:
      - ./logs:/logs
    networks:
      - app_network

```

#### Monitoring de l'hôte (Node Exporter) :

Ce service extrait les métriques de votre PC (CPU, RAM) pour les mettre à disposition du réseau.

```yaml
  node-exporter:
    image: prom/node-exporter:latest
    networks:
      - app_network

```

#### (Global) Déclaration indispensable du réseau :

```yaml
networks:
  app_network:

```

---

### 2. Configuration du Scraping (Prometheus)

Prometheus est un "aspirateur" de données. Il doit être configuré pour savoir **qui** interroger et **à quelle fréquence**.

* **Le Volume de Configuration** : Vous devez lier votre fichier local au chemin interne de Prometheus.

```yaml
  prometheus:
    image: prom/prometheus:latest
    ports:
      - "${PROMETHEUS_PORT}:9090"
    volumes:
      - ./prometheus/prometheus.yml:/etc/prometheus/prometheus.yml
    networks:
      - app_network

```

* **Le fichier `prometheus.yml`** :
Notez l'utilisation des noms de services (`api`, `node-exporter`) comme adresses IP grâce au DNS interne de Docker.

```yaml
global:
  scrape_interval: 5s

scrape_configs:
  - job_name: 'fastapi'
    static_configs:
      - targets: ['api:8080']
  - job_name: 'node'
    static_configs:
      - targets: ['node-exporter:9100']

```

---

### 3. Automatisation de Grafana (Provisioning)

Grafana utilise le **Provisioning** pour charger automatiquement sa configuration et ses tableaux de bord au démarrage.

* **Le Volume de Provisioning** :

```yaml
  grafana:
    image: grafana/grafana:latest
    ports:
      - "${GRAFANA_PORT}:3000"
    volumes:
      - ./grafana/provisioning:/etc/grafana/provisioning
    networks:
      - app_network

```

* **Source de données (`datasources.yml`)** :
Ce fichier indique à Grafana où se trouve la base de données Prometheus.

```yaml
apiVersion: 1
datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true

```

* **Chargement des Dashboards (`dashboards.yml`)** :
Ce bloc permet à Grafana de surveiller un dossier spécifique pour y charger tous les fichiers JSON de tableaux de bord qu'il contient.

```yaml
apiVersion: 1
providers:
  - name: "FastAPI Dashboards"
    type: file
    disableDeletion: false
    editable: true
    updateIntervalSeconds: 10
    options:
      path: "/etc/grafana/provisioning/dashboards"

```

---

### Indices de survie pour l'exercice :

1. **Le DNS Docker** : Dans vos fichiers `.yml`, n'utilisez jamais `localhost` pour désigner un autre conteneur. Utilisez le nom du service défini dans le Compose.
2. **Cycle de vie** : Si vous modifiez un fichier de configuration (`.yml`), vous devez souvent redémarrer le service concerné pour que les changements soient pris en compte.
3. **8GB de RAM** : Surveillez votre consommation. Si le système ralentit, fermez les interfaces graphiques inutiles.

Pour aider tes apprenants à ne pas saturer leurs **8 GB de RAM**, il est crucial d'imposer des limites strictes au niveau du moteur Docker. Sans cela, WSL2 ou Docker Desktop peuvent consommer la quasi-totalité de la mémoire disponible, provoquant des gels du système.

### Le code à insérer dans le `docker-compose.yml`

Pour chaque service, la limite se définit sous la clé `deploy`. Voici la syntaxe exacte à utiliser :

```yaml
services:
  nom_du_service:
    # ... reste de la config ...
    deploy:
      resources:
        limits:
          memory: 256M  # Limite de RAM maximale
          cpus: '0.50'   # Limite à 50% d'un cœur CPU

```

---

### Tableau des limites recommandées (Config 8GB)

Voici une proposition de limites "serrées mais fonctionnelles" pour permettre à la stack complète de tourner sur un vieux i5 avec 8 GB de RAM.

| Service | Limite RAM | Pourquoi ce choix ? |
| --- | --- | --- |
| **API (FastAPI)** | **512M** | Confortable pour Python, sauf si on charge un énorme modèle ML en RAM. |
| **Streamlit** | **512M** | Streamlit est assez gourmand car il recharge le script à chaque interaction. |
| **Prometheus** | **256M** | Suffisant pour stocker quelques métriques sur une courte période. |
| **Grafana** | **256M** | L'interface est légère tant qu'on n'ouvre pas 50 dashboards en même temps. |
| **Node Exporter** | **64M** | Service extrêmement léger, il ne fait que lire des fichiers système . |


**Total cumulé : ~1.5 GB.** Cela laisse environ 6.5 GB pour Windows, VS Code et quelques onglets de navigateur, ce qui est la zone de sécurité pour un PC de 8 GB.

Pour vérifier que vos limites de RAM sont bien appliquées et ne pas saturer votre ordi, utilisez :
```bash
docker stats
```

---
