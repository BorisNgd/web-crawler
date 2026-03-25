# Stack open source pour crawling massif et enrichissement vectoriel

**La combinaison Scrapy-Cluster (crawling distribué) + Crawl4AI (extraction LLM-ready) + Docling (parsing multi-format) + Qdrant ou Milvus (stockage vectoriel) constitue aujourd'hui la stack open source la plus robuste pour alimenter une base vectorielle par crawling continu à grande échelle.** Ce rapport analyse en profondeur les composants disponibles, leurs forces et faiblesses, et propose des architectures de production adaptées à un déploiement self-hosted et containerisé.

---

## Deux générations de crawlers coexistent en 2025-2026

Le paysage du crawling Python s'est scindé en deux ères distinctes. Les **frameworks classiques** — Scrapy en tête avec ses **~57 000 étoiles GitHub** et 16 ans de maturité — excellent en débit brut et extraction structurée. Les **frameworks de l'ère LLM** — Crawl4AI (~62 000 étoiles), Firecrawl (~90 000 étoiles, AGPL) — produisent nativement du Markdown propre optimisé pour l'ingestion dans des pipelines RAG.

**Scrapy** reste le pilier incontournable pour le crawling distribué à grande échelle. Basé sur Twisted (réseau asynchrone), il gère des milliers de requêtes concurrentes sans overhead de navigateur. Sa force réside dans son écosystème d'extensions distribuées : **Scrapy-Redis** (~5 500 étoiles) remplace le scheduler par une file Redis partagée entre instances, tandis que **Scrapy-Cluster** (~1 100 étoiles) ajoute Kafka pour une orchestration complète avec throttling coordonné, scaling dynamique et Docker Compose intégré. Le point faible : aucune sortie Markdown native ni intégration vectorielle — il faut construire des pipelines personnalisés.

**Crawl4AI**, le projet à la croissance la plus fulgurante, est conçu spécifiquement pour les pipelines RAG. Basé sur Playwright (navigateur headless asynchrone), il produit du Markdown nettoyé avec filtrage sémantique BM25, extraction LLM ou CSS/XPath, et supporte les stratégies de crawl profond (BFS, DFS, Best-First) avec reprise sur crash via Redis. Son intégration vectorielle est native : connecteurs Milvus, FAISS, Supabase (pgvector). Le compromis : la consommation mémoire de Playwright est significativement plus élevée qu'un crawler HTTP pur, et l'architecture distribuée multi-nœuds n'est pas native — il faut orchestrer manuellement via Docker.

**Crawlee Python** (par Apify, ~7 000 étoiles) mérite attention pour son `AdaptivePlaywrightCrawler` qui détecte automatiquement si le rendu JavaScript est nécessaire page par page, réduisant la consommation de ressources. Ses fonctions anti-blocage (rotation de fingerprints, gestion de sessions et proxies) sont les meilleures du marché. Cependant, il ne supporte ni le crawling distribué ni la sortie Markdown.

| Critère | Scrapy+Cluster | Crawl4AI | Crawlee Python | StormCrawler |
|---------|---------------|----------|----------------|-------------|
| **Langage** | Python | Python | Python | Java |
| **Distribué natif** | Via Redis+Kafka | Orchestration externe | Non | Natif (Storm) |
| **Crawling continu** | Oui | Oui (deep crawl + recovery) | Non | Stream natif |
| **Rendu JS** | Plugin Playwright | Natif Playwright | Natif Playwright | Non |
| **Sortie Markdown** | Non | Oui (cœur du projet) | Non | Non |
| **Intégration vectorielle** | Pipelines custom | Milvus, FAISS, pgvector | Non | Via Elasticsearch |
| **Docker** | Excellent | Excellent | Bon | Complexe |
| **Maturité** | 16+ ans | 2+ ans | 1+ an | 8+ ans (Apache TLP) |

Pour les équipes disposant d'infrastructure Java, **StormCrawler** (Apache Top-Level Project depuis juin 2025) offre la meilleure architecture de crawling continu : un traitement en flux basé sur Apache Storm où récupération, parsing et indexation se font simultanément et en continu, avec un débit nettement supérieur à Apache Nutch.

---

## L'extraction multi-format exige une approche hybride

Aucun outil unique ne gère parfaitement tous les formats. La stratégie optimale combine des extracteurs spécialisés par type de contenu.

**Pour le HTML**, **Trafilatura** domine avec un F1 de **0.958** dans les benchmarks d'extraction d'articles — le meilleur score parmi tous les extracteurs open source. Il inclut une logique de crawling intégrée (sitemaps, flux RSS, déduplication d'URLs) et produit du texte, Markdown, CSV, JSON ou XML. Utilisé par HuggingFace, IBM et Microsoft Research, c'est le choix par défaut pour toute extraction d'articles web.

**Pour les PDFs et documents**, deux projets dominent le marché :

**Docling** (IBM, hébergé par la Linux Foundation, **~37 000 étoiles**, licence MIT) est le leader multi-format. Il traite PDFs, DOCX, PPTX, XLSX, HTML et images avec une précision de **97,9%** sur l'extraction de tableaux complexes grâce à ses modèles DocLayNet (analyse de layout) et TableFormer (structure de tableaux). Son intégration native avec LangChain, LlamaIndex et Haystack en fait le choix idéal pour les pipelines RAG. Inconvénient : installation de **1 Go+** et difficultés avec les documents manuscrits.

**MinerU** (OpenDataLab, ~25 000 étoiles) offre la **meilleure précision pour les PDFs scientifiques** (97,5 mAP en détection de layout, support LaTeX pour les formules, OCR en 109 langues via PaddleOCR). Son backend hybride VLM+pipeline atteint **0,21 sec/page sur GPU**. La contrainte majeure : sa licence **AGPL** impose la publication du code source en cas de redistribution.

**Kreuzberg** (~3 000 étoiles, MIT) émerge comme alternative légère : **91+ formats supportés en seulement 71 Mo** (contre 1 Go+ pour Docling), avec API async/sync et 35 fichiers/seconde. Idéal pour les déploiements containerisés où les ressources comptent.

**MarkItDown** (Microsoft, ~40 000 étoiles, MIT) couvre un spectre de formats exceptionnellement large (PDF, DOCX, PPTX, XLSX, HTML, images, audio, CSV) avec une conversion légère vers Markdown, mais sans analyse de layout par IA.

**Pour l'OCR**, **PaddleOCR** (~48 000 étoiles, Apache 2.0) a dépassé Tesseract en précision dans les benchmarks 2025-2026, avec support de 100+ langues et analyse de layout intégrée. Tesseract reste pertinent pour le traitement CPU rapide de texte imprimé propre. **EasyOCR n'est plus recommandé** pour la production en raison de problèmes de précision systématiques (confusion de symboles monétaires, développement ralenti).

### Stack d'extraction recommandée

```
HTML/Articles     → Trafilatura (F1=0.958, crawling intégré)
PDFs généraux     → Docling (MIT, multi-format, intégration RAG native)
PDFs scientifiques→ MinerU (meilleure précision, GPU recommandé)
Documents Office  → Docling (DOCX, PPTX, XLSX)
OCR/Images        → PaddleOCR (précision) ou Tesseract (vitesse CPU)
Tableaux HTML     → Docling ou Pandas read_html()
Tableaux PDF      → Camelot (grilles) + Docling (complexes)
```

---

## Des projets open source complets bridgent crawling et vectorisation

Plusieurs projets GitHub assemblent déjà la chaîne complète crawl → chunk → embed → store, évitant de construire chaque brique from scratch.

**MCP-Crawl4AI-RAG** (par coleam00) offre un serveur MCP complet : Crawl4AI crawle et extrait le contenu, le découpe en chunks, génère des embeddings, et stocke dans **Supabase (pgvector)**. Il expose des outils `crawl_single_page`, `smart_crawl_url` et `perform_rag_query`, conçus pour les assistants IA de codage.

**Qdrant-Neo4j-Crawl4AI-MCP** (par BjornMelin) va plus loin avec une architecture de production : Crawl4AI alimentant simultanément **Qdrant** (recherche vectorielle) et **Neo4j** (graphe de connaissances), avec authentification JWT, rate limiting, monitoring Prometheus/Grafana, error tracking Sentry, et déploiement Kubernetes complet avec scripts de backup/recovery.

**VectorFlow** propose un pipeline d'embedding tolérant aux pannes avec une API HTTP : envoyez des fichiers bruts (TXT, PDF, HTML, DOCX), ils sont automatiquement découpés, vectorisés et stockés dans Qdrant, Weaviate, Milvus ou Pinecone. Son architecture utilise **RabbitMQ** pour le queuing, PostgreSQL pour les métadonnées, et MinIO pour le stockage objet — le tout déployable via Docker Compose.

**txtai** mérite une mention spéciale comme framework tout-en-un : base vectorielle + factory d'embeddings + orchestrateur LLM + agents, avec recherche dense et sparse, analytique de graphes, et requêtes SQL sur les vecteurs. Licence Apache 2.0.

Du côté des bases vectorielles, **Weaviate** est la seule à offrir une vectorisation intégrée (modules OpenAI, Cohere, HuggingFace) sans service d'embedding externe. **Milvus** excelle pour les volumes massifs (milliards de vecteurs) avec son architecture compute/stockage désagrégée. **Qdrant** (Rust) offre les meilleures performances en recherche filtrée avec une empreinte mémoire minimale.

---

## L'orchestration distribuée détermine la capacité à passer à l'échelle

Pour un crawling continu de milliers de pages, le choix du système de files d'attente est structurant.

**Redis + Celery** représente le chemin de moindre résistance pour l'écosystème Python : Scrapy-Redis partage la file d'URLs entre instances, Celery Beat planifie les crawls récurrents, et les retry automatiques gèrent les échecs transitoires. Cette combinaison supporte facilement **50 000+ crawls quotidiens**. Limitation : Redis étant en mémoire, les files très volumineuses posent problème.

**Apache Kafka** (utilisé par Scrapy-Cluster) offre le meilleur débit avec tolérance aux pannes, replay de données, et Schema Registry. C'est le choix pour les architectures à plusieurs millions de pages, mais avec une complexité opérationnelle significative (Zookeeper, partitions, consumer groups).

**RabbitMQ** (utilisé par VectorFlow) offre un excellent compromis : routage flexible, files prioritaires, et vitesse en mémoire, sans la complexité de Kafka. Idéal pour les pipelines d'embedding où le débit est important mais pas critique.

Le pattern de containerisation standard pour cette stack se structure ainsi :

```yaml
services:
  crawler:      # Scrapy-Cluster ou Crawl4AI (multiples replicas)
  queue:        # Redis (coordination) + Kafka ou RabbitMQ (données)
  extractor:    # Workers Docling/Trafilatura pour parsing multi-format
  embedder:     # Workers sentence-transformers (GPU si disponible)
  vectordb:     # Qdrant, Milvus ou Weaviate
  api:          # FastAPI pour requêtes RAG
  monitoring:   # Prometheus + Grafana
```

**Crawlab** (~12 000 étoiles) fournit une plateforme de gestion de crawlers distribués avec architecture Master/Worker, MongoDB + Redis, et démarrage one-click via `docker-compose up -d`. Il supporte Scrapy, Puppeteer et Selenium, avec une interface web pour le monitoring.

Pour Kubernetes en production, le pattern recommandé inclut le horizontal pod autoscaling sur les workers de crawling et d'embedding, des health checks sur chaque service, et des volumes persistants pour Redis et la base vectorielle.

---

## Trois architectures de référence selon l'échelle visée

**Architecture Prototype** (< 10 000 pages, machine unique) : Crawl4AI + LangChain `RecursiveCharacterTextSplitter` + sentence-transformers `all-MiniLM-L6-v2` + ChromaDB. Déployable sur un seul conteneur Docker. Idéal pour valider le concept avant de passer à l'échelle.

**Architecture Production Intermédiaire** (10 000–100 000 pages, crawling continu) : Crawl4AI en mode Docker multi-replicas avec Redis partagé + Docling pour le parsing multi-format + Qdrant (single-node) + RabbitMQ pour le queuing entre composants. Docker Compose suffit. Le modèle d'embedding `BAAI/bge-large-en-v1.5` (1024 dimensions) offre le meilleur rapport qualité/coût pour le RAG.

**Architecture Production Grande Échelle** (100 000+ pages, crawling distribué continu) : Scrapy-Cluster (Redis + Kafka) pour la découverte et coordination d'URLs → Workers Crawl4AI pour l'extraction Markdown des pages JS-rendered, Trafilatura pour les pages statiques, Docling pour les PDFs/documents → Pipeline d'embedding distribué via Celery workers GPU → **Milvus** (architecture distribuée, milliards de vecteurs) → API FastAPI pour les requêtes RAG. Déploiement Kubernetes avec autoscaling et monitoring Prometheus/Grafana.

---

## Conclusion

L'écosystème open source pour le crawling massif orienté RAG a considérablement mûri entre 2024 et 2026. **Crawl4AI a démocratisé l'extraction web LLM-ready**, mais Scrapy reste indispensable pour la distribution et le débit à grande échelle — l'approche hybride combinant les deux est la plus pragmatique. **Docling s'est imposé comme le standard de facto** pour l'extraction multi-format (MIT, 37k+ étoiles, Linux Foundation), supplantant progressivement Unstructured.io en qualité perçue. Les bases vectorielles Qdrant et Milvus dominent le segment self-hosted, avec Weaviate comme seule option offrant la vectorisation intégrée.

La clé d'une architecture réussie réside moins dans le choix d'un outil unique que dans l'assemblage intelligent de composants spécialisés : un crawler distribué pour le débit, des extracteurs dédiés par format pour la qualité, un système de queuing pour la résilience, et une base vectorielle adaptée au volume cible. Les projets comme VectorFlow et le stack Qdrant-Neo4j-Crawl4AI-MCP montrent la voie vers des solutions intégrées prêtes pour la production.