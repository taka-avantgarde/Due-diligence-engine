<div align="center">

### 🌐 Langue

| 🇬🇧 [![English](https://img.shields.io/badge/English-EEF2F7?style=for-the-badge)](README.md) | 🇯🇵 [![日本語](https://img.shields.io/badge/%E6%97%A5%E6%9C%AC%E8%AA%9E-EEF2F7?style=for-the-badge)](README.ja.md) | 🇪🇸 [![Español](https://img.shields.io/badge/Espa%C3%B1ol-EEF2F7?style=for-the-badge)](README.es.md) | 🇸🇦 [![العربية](https://img.shields.io/badge/%D8%A7%D9%84%D8%B9%D8%B1%D8%A8%D9%8A%D8%A9-EEF2F7?style=for-the-badge)](README.ar.md) | 🇫🇷 [![● Français](https://img.shields.io/badge/%E2%97%8F%20Fran%C3%A7ais-5271FF?style=for-the-badge)](README.fr.md) | 🇩🇪 [![Deutsch](https://img.shields.io/badge/Deutsch-EEF2F7?style=for-the-badge)](README.de.md) |
|:--:|:--:|:--:|:--:|:--:|:--:|

<sub>👆 Click your language to switch ・ クリックで言語を切り替え</sub>

<sub>🪟 **Sous Windows :** fonctionne nativement (Git requis dans le PATH) — pour la garantie de sécurité complète (verrouillage des permissions des fichiers temporaires), utilisez **WSL2**.</sub>

---

# 🔍 Due Diligence Engine

### **L'IA de votre IDE → Analyste DD technique de classe mondiale**

<sub>**Aucune clé API · PDF d'abord · OSS · audité par CodeQL**</sub>

<br/>

```
┌─────────────────────────────────────────────────────────────┐
│  $ dde prompt --pdf                                         │
│                                                             │
│  🌐 Live web research (2026 competitors, funding, CVEs)...  │
│  Reading codebase...                                        │
│  Evaluating across 5 dimensions (equal 20% weights)...      │
│  Building competitive landscape (7 charts × 6 markets)...   │
│  Researching implementation matrix (30 items × 10 cos.)...  │
│  Writing competitor selection rationales (with sources)...  │
│                                                             │
│  Score:  [■■■■■■■■■■■■■■■■■■■■■■■■■■□□□□] 82/100  Lv.8     │
│  Grade:  B  →  Viable with conditions                       │
│                                                             │
│  → ~/Downloads/dde_consulting_<project>_<date>.pdf  (24 p.) │
└─────────────────────────────────────────────────────────────┘
```

<br/>

[![License](https://img.shields.io/badge/License-Apache_2.0-000000.svg?style=for-the-badge)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.11+-5271FF.svg?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![CodeQL](https://img.shields.io/badge/Security-CodeQL_·_Dependabot_·_pip--audit-5271FF.svg?style=for-the-badge&logo=github&logoColor=white)](SECURITY.md)
[![PDF](https://img.shields.io/badge/Output-PDF_First-000000.svg?style=for-the-badge&logo=adobeacrobatreader&logoColor=white)](#)

[![GitHub stars](https://img.shields.io/github/stars/Atlas-Associates-Inc/Due-diligence-engine?style=flat-square&color=5271FF)](https://github.com/Atlas-Associates-Inc/Due-diligence-engine/stargazers)
[![GitHub issues](https://img.shields.io/github/issues/Atlas-Associates-Inc/Due-diligence-engine?style=flat-square&color=000000)](https://github.com/Atlas-Associates-Inc/Due-diligence-engine/issues)
[![Last Commit](https://img.shields.io/github/last-commit/Atlas-Associates-Inc/Due-diligence-engine?style=flat-square&color=5271FF)](https://github.com/Atlas-Associates-Inc/Due-diligence-engine/commits/main)
[![Version](https://img.shields.io/badge/version-v0.4.0-000000?style=flat-square)](https://github.com/Atlas-Associates-Inc/Due-diligence-engine/releases)

[![Repo Views](https://komarev.com/ghpvc/?username=taka-avantgarde&repo=Due-diligence-engine&color=5271FF&style=flat-square&label=Repo+Views)](https://github.com/Atlas-Associates-Inc/Due-diligence-engine)

</div>

---

## ⚡ Démarrage rapide

**Installez une seule fois :**

```bash
python3 -m pip install --no-cache-dir git+https://github.com/Atlas-Associates-Inc/Due-diligence-engine.git
```

**Lancez depuis le répertoire de votre projet :**

```bash
dde prompt --pdf
```

Utilisez n'importe quel terminal d'IDE doté de l'IA (Claude Code / Cursor / Copilot). Votre IA lit la base de code, l'évalue comme un consultant technologique de classe mondiale, puis rédige un PDF de 24 pages dans `~/Downloads/`. **Aucune clé API. Aucun cloud. Aucun coût supplémentaire.**

<details>
<summary><sub>Autres options d'installation · note macOS Homebrew</sub></summary>

Forme courte pour Linux / venv / anciennes versions de macOS :
```bash
pip3 install --no-cache-dir git+https://github.com/Atlas-Associates-Inc/Due-diligence-engine.git
```

Utilisateurs de macOS Homebrew : utilisez `python3 -m pip` — la commande `pip` seule n'est plus installée par Homebrew Python 3.12+.

</details>

---

## 💭 Comment obtenir les meilleurs résultats

> **En bref** : lancez l'IA la plus performante à laquelle vous avez accès dans le terminal de votre IDE,
> collez la commande, et patientez 10 à 20 minutes. C'est tout.

**Configuration recommandée :**

- **Démarrez le modèle le plus capable disponible** dans votre IDE (Claude Fable 5, GPT-5, Gemini 2.5 Pro, etc.)
- **Collez `dde prompt --pdf`** dans le terminal
- **Allez chercher un café** ☕ — l'IA lira des centaines de fichiers, évaluera selon
  9+ dimensions, étudiera 5 à 10 concurrents au niveau mondial, et bâtira un PDF de conseil de 24 pages
- **Durée prévue** : **10 à 20 minutes** (plus longtemps pour les grandes bases de code ou les modèles plus poussés)

**Pourquoi cette approche ?**

| Préoccupation | Réponse |
|---------|--------|
| 🔐 **Fuite de données ?** | Aucune. Tout s'exécute dans le bac à sable de l'IA de votre IDE — aucun serveur tiers, aucune télémétrie. DDE lui-même est du Python 100 % local |
| 💰 **Coût ?** | 0 € de plus. Utilise votre abonnement IA d'IDE existant |
| 🔑 **Clés API ?** | Inutiles. Votre IDE gère déjà l'authentification de l'IA |
| ⚙️ **Configuration ?** | Juste `python3 -m pip install`. Aucune config, aucun compte |
| 🎁 **Piège ?** | Il n'y en a pas. DDE est un **projet personnel** — créé et ouvert en open source pour le plaisir. Utilisez-le librement |

> **Réalisé par un développeur solo, en tant que loisir.** S'il vous est utile, c'est une récompense suffisante. Mettez une étoile au dépôt si vous l'appréciez ⭐

---

## 💻 Où DDE s'exécute-t-il — utilisez l'IA que vous avez déjà

DDE génère un prompt structuré. **Tout agent IA capable de lire des fichiers et d'exécuter des commandes shell** peut le lancer. Aucune intégration, aucun plugin ni connexion spécifique à DDE n'est requis.

**Fonctionnement vérifié** (docs officielles + testé, 2026-05) :
- ✅ [**Claude Code**](https://code.claude.com/docs/en/overview) (CLI / VS Code / JetBrains / Desktop / Web — officiel Anthropic)
- ✅ [**GitHub Copilot Agent Mode**](https://docs.github.com/en/copilot/using-github-copilot/copilot-chat/asking-github-copilot-questions-in-your-ide) (VS Code / Visual Studio / JetBrains / Xcode / Eclipse — disponibilité générale)

**Devrait fonctionner** (prérequis : lecture de fichiers + exécution shell + idéalement recherche web) :
- Cursor Agent, Gemini Code Assist, Continue.dev, Cody (Sourcegraph), Aider, Windsurf, Amazon Q Developer, JetBrains AI Assistant, et terminaux agentiques similaires.

> ✅ Si vous utilisez déjà l'un des outils ci-dessus, vous n'êtes qu'à un `pip install` de lancer DDE dès aujourd'hui.
> Vous avez confirmé qu'un terminal donné fonctionne ? Faites-le-nous savoir dans une [issue](https://github.com/Atlas-Associates-Inc/Due-diligence-engine/issues).

### 💰 Aucun coût supplémentaire

**Vous ne payez que l'abonnement IA que vous possédez déjà.** Claude Code Pro / GitHub Copilot / Cursor Pro / Gemini Advanced — DDE s'exécute dans le quota de votre IA existante. Aucun palier tarifaire DDE, aucune clé API supplémentaire, aucuns frais cachés, jamais.

---

## 👥 Pour qui est-ce ?

| Utilisateur | Cas d'usage | Temps gagné |
|------|----------|-----------|
| **Partenaires techniques VC** | DD technique pré-investissement sur les candidats du portefeuille | 2-5 jours → 30 min |
| **CTO / responsables d'ingénierie** | Audit technique interne avant les conseils d'administration | 1 semaine → 1 heure |
| **Conseillers techniques M&A** | Due diligence sur les cibles d'acquisition | 1-2 semaines → 1 jour |
| **Consultants DD indépendants** | Évaluations techniques de cabinets boutique | échelle : 1→10 clients/semaine |
| **Fondateurs** | Auto-évaluation avant une levée de fonds | vue objective de sa propre base de code |
| **Innovation en entreprise** | Évaluation de partenariats fournisseurs / startups | ponctuel → systématique |

> Conçu pour les ingénieurs et les décideurs techniques qui utilisent déjà l'IA dans leur travail quotidien.

---

## 🆚 vs. les autres outils

|   | DDE | DD manuelle | Revue de code IA générique | Plateformes DD SaaS |
|---|:---:|:---:|:---:|:---:|
| **Coût** | 0 € (utilise l'IA de votre IDE) | $$$$ (honoraires de consultant) | frais d'API | $$$$ (abonnement) |
| **Confidentialité** | Local uniquement | Local | Envoie le code au fournisseur | Envoie le code au fournisseur |
| **Sortie** | PDF de conseil de 24 pages | Rapport sur mesure | Commentaires en ligne | Tableau de bord web |
| **Fraîcheur des données** | ✅ Recherche web en direct (2026) + URLs des sources | Dépend de l'analyste | Données d'entraînement uniquement (périmées) | Actualisation contrôlée par le fournisseur |
| **Profondeur cryptographique** | Niveau PQXDH / Signal Protocol | Dépend du consultant | Générique | Générique |
| **Graphiques concurrentiels** | 7 + matrice d'implémentation | Recherche manuelle | Aucun | Limité |
| **Temps de configuration** | 1 commande | Semaines | Minutes | Jours (compte/onboarding) |
| **Personnalisation** | Accès complet au code source | Oui | Limitée | Verrouillée par le fournisseur |

---

## Ce qui rend DDE différent

La plupart des « relecteurs de code IA » vérifient :
> *« A-t-il une authentification ? ✓ A-t-il HTTPS ? ✓ A-t-il des tests ? ✓ »*

C'est de la conformité par cases à cocher. **DDE va plus loin :**

> *« Le chiffrement est-il du Signal Protocol ? Est-ce du PQXDH avec ML-KEM-1024 ?
> Est-il bâti sur le FFI de libsignal/BoringSSL, ou s'agit-il de crypto maison ?
> L'équipe publie-t-elle des recherches cryptographiques ? »*

Bâti sur la **philosophie d'ingénierie Atlas** : une ingénierie de cybersécurité sérieuse
couvrant le chiffrement, la confidentialité, les communications et la défense en couches — lue directement
depuis le code source. La conformité par cases à cocher (certifications SOC2, MFA, WebAuthn)
est purement indicative, jamais notée.

**🌐 Nouveau dans la v0.3.2** : avant de lire le moindre code, l'IA effectue des **recherches web en direct** pour obtenir le dernier paysage concurrentiel (acquisitions, fermetures, nouveaux entrants), les tours de financement 2026, les CVE récentes et les évolutions réglementaires. Chaque concurrent et chaque cellule de la matrice d'implémentation porte une **URL de source + une date de vérification**, et la sortie JSON débute par un bloc `data_freshness` qui suit chaque requête de recherche. **L'analyse périmée fondée uniquement sur la date de coupure d'entraînement est structurellement éliminée.**

---

## 🔒 Philosophie d'ingénierie Atlas (vue parallèle axée cybersécurité)

Un système d'évaluation parallèle ajouté à côté de la notation standard à 5 dimensions.

```
4 axes — weights sum to 100%

  Performance        20%  ██████████░░░░░░░░░░░░░░░░░░░░░░
  Stability          20%  ██████████░░░░░░░░░░░░░░░░░░░░░░
  Lightweight         5%  ███░░░░░░░░░░░░░░░░░░░░░░░░░░░░░
  Security Strength 55%  ███████████████████████████░░░░░  ← THE CORE

  Cybersecurity sub-breakdown (within 55% — defense across all layers):
    Cryptographic Sophistication  35%  ← largest: Signal Protocol, PQXDH, libsignal
    Privacy Protection             8%
    Communication Safety           7%
    Layer Composition              3%
    Basic Hygiene (MFA/WebAuthn)   2%  ← code-only; certs are reference-only
```

---

## 📊 Notation standard à 5 dimensions (v0.3 — équilibrée, poids égaux)

| Dimension | Poids | Ce qu'elle détecte |
|-----------|-------:|-----------------|
| Originalité technique | 20 % | Wrapper d'API vs. véritable PI |
| Avancée technologique | 20 % | Modernité de la stack |
| Profondeur d'implémentation | 20 % | PoC vs. production |
| Qualité d'architecture (y compris posture de sécurité) | 20 % | Qualité de la structure + maturité de la sécurité |
| Cohérence des affirmations | 20 % | Pitch vs. réalité |

> **Score final** = Analyse heuristique (30 %) + Score moyen de l'IA (70 %)

> **Changement v0.3** : la posture de sécurité a été fusionnée dans la qualité d'architecture. La sécurité est désormais évaluée comme une partie intégrante d'une architecture de qualité production, et non comme un silo distinct.

```
Grade Bands:

  0      40       60      75       90     100
  |------|--------|-------|--------|------|
   F      D        C       B        A
   ✗      ⚠        ⚡       ✓        ★
```

| Note | Recommandation |
|-------|----------------|
| ★ A (90+)  | Candidat d'investissement solide |
| ✓ B (75-89)| Viable sous conditions |
| ⚡ C (60-74)| Préoccupations importantes |
| ⚠ D (40-59) | Risque élevé |
| ✗ F (<40)  | Ne pas investir |

Chaque dimension est aussi notée **Niv.1-10** selon des critères explicites.

---

## 🎯 7 graphiques concurrentiels × 6 marchés

Pour chacun des 6 marchés mondiaux (Global / US / EMEA / Japon / SEA / LATAM) :

| # | Graphique | Ce qu'il montre |
|---|-------|---------------|
| 1 | **Forrester Wave / Magic Quadrant** | Vision × Exécution |
| 2 | **Matrice de croissance-part BCG** | Croissance du marché × Part relative |
| 3 | **Douve technologique McKinsey** | Position concurrentielle × Douve technique |
| 4 | **Maturité sécurité & confidentialité** | Implémentation de la sécurité × Préparation à la confidentialité |
| 5 | **Gouvernance des données & transparence** | Protection des données × Transparence des audits |
| 6 | **Rendement ajusté au risque GS** | Risque de baisse × Potentiel de hausse |
| 7 | **Innovation vs. commercialisation** | Vélocité R&D × Traction ARR (bulle 3D) |

**6 à 16 concurrents par graphique** avec des légendes de justification des axes expliquant
*pourquoi* chaque axe compte et *ce que* le score composite capture.

---

## 🆕 Matrice de capacité d'implémentation

Le 8e graphique concurrentiel — **~30 éléments × 5 à 10 grands concurrents mondiaux** :

```
                        Target   Comp. A   Comp. B   Comp. C   Comp. D   ...
Encryption (core differentiator)
  Feature 1              ○        ○         ×         △         ○
  Feature 2              ○        ○         ×         ×         ○
  Feature 3              ○        ○         ○         ×         ○
  Feature 4              ○        ×         ×         △         △
  ...
Privacy & Compliance
  Feature 1              ○        △         ○         ×         △
  Feature 2              ○        ○         △         ×         ×
  ...
```

Les éléments et les concurrents sont **choisis dynamiquement selon le secteur de la cible**
(messagerie, fintech, médical, jeu vidéo, SaaS, IoT, etc.).

Marquage à 4 états (norme japonaise d'évaluation technologique) :
- **○ vérifié** (implémentation publiquement documentée)
- **△ revendiqué** (affirmé, non vérifiable)
- **× non implémenté** (explicitement absent)
- **? inconnu** (impossible à déterminer — préféré aux suppositions)

Plus des **justifications de sélection des concurrents** — 3 à 5 lignes chacune expliquant pourquoi chaque
concurrent précis a été retenu comme cible de comparaison (siège, position de marché, catégorie).

---

## 📄 Que contient le PDF de 24 pages

| # | Section | Contenu |
|---|---------|---------|
| 1 | Couverture | Accent noir + ciel Arc (#5271FF), nom du projet, score, note |
| 2 | Tableau de bord des scores | Graphique à barres horizontales **5 dim.** (20 % chacune) + baromètre de score |
| 3 | Résumé exécutif | Synthèse métier + technique |
| 4 | Analyse SWOT | Grille visuelle 2×2 avec preuves + analogies métier |
| 5 | Détail des scores | Justification par dimension & facteurs favorables |
| 6 | Évaluation du niveau technique | Graphique à barres **5 dim.** Niv.1-10 + jauge globale |
| 7 | Perspectives d'avenir | Projections à 1/3/5 ans avec niveau de confiance |
| 8 | Conseils stratégiques | Court, moyen, long terme |
| 9 | Thèse d'investissement | Recommandation, risques, potentiel de hausse, comparables |
| 10 | Signaux d'alerte | Notés par gravité (Critique/Élevé/Moyen/Faible) |
| 11 | Vérification du site | Audit de capacité technique à 10 éléments (4 affirmation-vs-code + 6 mesurés sur le code) |
| 12-14 | Analyse concurrentielle | 7 graphiques × 6 marchés avec justification des axes |
| 15 | **🆕 Justifications de sélection des concurrents** | Explication de 3 à 5 lignes par concurrent (pourquoi choisi, siège, position) |
| 16 | **Matrice de capacité d'implémentation** | ~30 éléments × grands concurrents, marquage ○△×? |
| 17 | **Tableau de bord 4 axes Atlas** | Performance / Stabilité / Légèreté / Force de sécurité |
| 18 | **Détail de la sous-sécurité + glossaire** | 5 sous-éléments avec glossaire pour non-ingénieurs (MFA/SOC2/libsignal/PQXDH…) |
| 19-24 | Glossaire · Cohérence · Coût · Certificat de purge | Sections d'annexe standard |

---

## 🛠️ Utilisation

```bash
# Current directory, English PDF
dde prompt --pdf

# Japanese PDF
dde prompt --pdf --lang ja

# GitHub repo with stage context
dde prompt owner/repo --pdf --lang ja --stage seed

# Non-interactive (for AI terminals without prompt support)
dde prompt --pdf --lang ja \
  --url https://example.com \
  --url https://docs.example.com

# Direct BYOK multi-AI cross-verification (optional)
export ANTHROPIC_API_KEY=sk-ant-...
export GOOGLE_AI_API_KEY=AIza...
export OPENAI_API_KEY=sk-...
dde analyze owner/repo
```

---

## 🔐 Philosophie de sécurité & open source

| Garantie | Implémentation |
|-----------|----------------|
| **Traitement local uniquement** | `dde prompt` n'envoie jamais de données où que ce soit |
| **Aucun code source dans les rapports** | Les PDFs ne contiennent que les conclusions |
| **Rétention API à 0 jour** | `dde analyze` utilise des points d'accès sans rétention |
| **CI de sécurité automatisée** | CodeQL · Dependabot · pip-audit · safety · osv-scanner · GitHub Secret Scanning |
| **Protection des branches** | `main` exige PR + CI + protection contre les push de secrets |
| **Accès aux dépôts privés via PAT** | Utilisé une fois en mémoire, jamais stocké |

Rapports de vulnérabilité : voir [SECURITY.md](SECURITY.md) — SLA de réponse de 48 h.

### Pourquoi l'open source est une fonctionnalité de sécurité, pas un risque

L'open source signifie que chaque ligne est auditable. Aucune porte dérobée cachée. Aucune notation en boîte noire.
C'est la même philosophie que Signal et libsignal : **la transparence *est* la confiance**.

---

## ❓ FAQ

**Q : DDE envoie-t-il mon code quelque part ?**
R : Non. `dde prompt` s'exécute entièrement en local — il génère un prompt structuré que l'IA de votre IDE lit. L'IA évalue le code sur place. L'option `dde analyze` (BYOK) envoie aux fournisseurs d'IA en utilisant uniquement leurs points d'accès sans rétention.

**Q : Pourquoi est-ce gratuit ? Quel est le piège ?**
R : Il n'y a aucun piège. DDE est open source (Apache 2.0) et utilise votre abonnement IA d'IDE existant (Claude Code / Cursor / Copilot). Aucune télémétrie, aucune montée en gamme.

**Q : Puis-je l'utiliser en CI ?**
R : Oui — voir [`action.yml`](action.yml). Ajoutez la GitHub Action aux PRs pour une notation DD automatisée.

**Q : Quelle est la précision des graphiques concurrentiels ?**
R : Les graphiques sont étudiés par l'IA à partir de sources publiques (livres blancs, GitHub, blogs, rapports SOC2). La confiance dépend de la transparence du concurrent. Utilisez `?` (inconnu) sans hésiter — les faux positifs nuisent à la crédibilité plus que les lacunes.

**Q : Les données sur les concurrents ne sont-elles pas périmées ? Les dates de coupure d'entraînement des IA ont 6 à 12 mois.**
R : Depuis la v0.3.2, l'**ÉTAPE 0 « Recherche web en direct » est obligatoire**. Avant de lire le moindre code, l'IA exécute WebSearch / WebFetch pour les mouvements des concurrents 2025-2026 (acquisitions, fermetures, nouveaux entrants), les derniers tours de financement, les CVE et les évolutions réglementaires. Chaque concurrent et chaque cellule de la matrice porte un champ `sources` (URL) et `last_verified` (date), et la sortie JSON débute par un bloc `data_freshness` qui suit chaque requête de recherche exécutée. Lorsque l'environnement d'exécution ne dispose pas d'outils de recherche web, l'IA DOIT écrire un `data_cutoff_warning` — **aucune sortie périmée silencieuse, par conception**.

**Q : Pourquoi « philosophie d'ingénierie Atlas » ?**
R : DDE est créé par **Atlas Associates Inc**, l'entreprise derrière Arc Messenger (messagerie E2EE avec libsignal + PQXDH). L'évaluation à 4 axes reflète ce que nous recherchons réellement lorsque nous évaluons une technologie.

**Q : Puis-je personnaliser les poids de notation ?**
R : Les poids des 5 dimensions sont égaux à 20 % chacun (équilibré, simple, interprétable). Les poids des 4 axes Atlas (20/20/5/55) reflètent la philosophie Atlas et sont également fixes. Les poids des sous-éléments au sein de la force de sécurité s'ajustent selon le contexte sectoriel.

**Q : Et si mon projet n'est pas critique en matière de sécurité ?**
R : Le score à 5 dimensions (la qualité d'architecture inclut la posture de sécurité à un niveau équilibré de 20 %) est votre score principal. Les 4 axes Atlas constituent une vue de référence parallèle — les deux sont affichés.

**Q : J'obtiens `command not found: pip` — comment installer ?**
R : Utilisez plutôt `python3 -m pip install ...`. macOS Homebrew Python 3.12+ ne fournit plus de commande `pip` seule. La forme `python3 -m pip` fonctionne sur toutes les plateformes (macOS / Linux / Windows / venv / pyenv / conda).

**Q : Pourquoi les certifications tierces (SOC2, ISO, HIPAA) n'affectent-elles pas le score ?**
R : DDE évalue le code source, pas le badge. Un service de stockage en clair certifié SOC2 stocke toujours en clair. Un service libsignal+PQXDH non certifié reste cryptographiquement solide. Les certifications sont affichées à titre contextuel mais jamais notées — voir la page Détail de la sous-sécurité.

---

## 🗺️ Feuille de route

**Livré récemment (v0.3.x)**
- ✅ **Rapports PDF en 14 langues** (2026-06, v0.4.0) : le PDF de conseil se génère en 14 langues via `--lang` — English / 日本語 / Español / Français / Deutsch / Português / Nederlands / Italiano / Bahasa Indonesia / 简体中文 / 한국어 / Tiếng Việt / ไทย / العربية (arabe avec mise en forme contextuelle RTL). Polices Noto incluses, sans configuration.
- ✅ **Corrections de compatibilité Windows** (2026-06, v0.3.8) : chemin temporaire multiplateforme pour le flux de conseil `--pdf` (auparavant un `/tmp` codé en dur) et prise en charge du presse-papiers Windows (`clip`) pour `--copy`
- ✅ **READMEs en 6 langues** (2026-06, v0.3.7) : sélecteur de langue en haut de page avec la langue active mise en évidence — English / 日本語 / Español / العربية / Français / Deutsch, chacun étant un fichier `README.<lang>.md` distinct
- ✅ **Mise à niveau vers Claude Fable 5** (2026-06, v0.3.6) : le palier juge est passé d'Opus 4.8 → **Fable 5** (`claude-fable-5`, le modèle le plus capable largement diffusé d'Anthropic, GA 2026-06-09). Clé de palier renommée `opus` → `fable`. Tarif 10 $/50 $ par MTok (2× Opus 4.8, priorité à la qualité du verdict final)
- ✅ **Peaufinage des graphiques PDF + correction du chevauchement des libellés** (2026-05, v0.3.5) : toutes les barres des graphiques Tableau de bord des scores / Niveau technique / Concurrentiel / Matrice ont été redessinées en pilules arrondies modernes. Les longs libellés japonais (par ex. « アーキテクチャ品質（セキュリティ含む） ») qui chevauchaient les barres sont corrigés en élargissant la zone des libellés (vérifié par rendu + inspection visuelle de chaque page PDF)
- ✅ **Mise à niveau vers Claude Opus 4.8** (2026-05, v0.3.3–4) : le palier juge est passé d'Opus 4.7→4.8 (Sonnet 4.6 / Haiku 4.5 également rafraîchis). Évite le retrait du 2026-06-15 des anciens Opus 4 / Sonnet 4 (20250514) et reflète la baisse de prix d'Opus (15 $→5 $ en entrée)
- ✅ **Transfert vers l'org Atlas-Associates-Inc** (2026-05, v0.3.4–5) : le dépôt est passé de taka-avantgarde → Atlas-Associates-Inc. Toutes les URLs mises à jour, crédit auteur unifié à Takayuki Miyano (@taka-avantgarde) + Atlas Associates Inc, gitleaks → GitHub native Secret Scanning
- ✅ **Mandat de recherche web en direct** (2026-05, ÉTAPE 0) : ajout de `_WEB_RESEARCH_MANDATE` en tête de chaque prompt de conseil — l'IA DOIT exécuter WebSearch/WebFetch sur le paysage concurrentiel, le financement, les tendances technologiques, les CVE et la réglementation **avant** de lire le code. La sortie JSON inclut désormais un bloc `data_freshness` (date de recherche, requêtes exécutées, sources consultées) ainsi que des champs `sources` / `last_verified` par concurrent et par cellule de matrice. Élimine l'analyse périmée fondée uniquement sur la date de coupure d'entraînement
- ✅ **Corrections de coquilles dans le prompt** : « 6 dimensions » → « 5 dimensions » et « 5つのチャート » → « 7つのチャート » dans le prompt de conseil JA
- ✅ **Correction de l'auto-test CI** (2026-05) : le `grep -c` d'`action.yml` renvoyait le code de sortie 1 en l'absence de correspondance, que `set -e` + `pipefail` propageaient comme un échec du job. Corrigé avec le motif `|| FALLBACK="0"`. **L'auto-test DDE est désormais vert pour la première fois**
- ✅ **Formule de notation explicitée dans le README** (Score final = Heuristique 30 % + Moyenne IA 70 %)
- ✅ **Dependabot entièrement câblé** : création des labels `dependencies` / `security` / `ci` et fusion des PR #23 (checkout v6) / #24 (upload-artifact v7) / #25 (osv-scanner-action v2.3.8)
- ✅ **Garde-fous anti-auto-biais** : avertissements explicites « la cible n'est PAS DDE lui-même » dans l'en-tête du prompt (évite la confusion de l'IA lorsque DDE est exécuté sur un autre projet)
- ✅ **Signaux d'alerte clarifiés** : présentés comme des éléments exploitables pour l'amélioration du code (NON pris en compte dans le score)
- ✅ **Démarrage rapide simplifié** dans le README (commande d'installation unique + alternatives repliables)
- ✅ **Philosophie Atlas reformulée** en « défense de cybersécurité globale » (pas seulement le chiffrement — le chiffrement est le plus grand sous-poids à 35 %)
- ✅ **Vérification du site recentrée sur la pure capacité technique** (10 éléments : 4 affirmation-vs-code + 6 mesurés sur le code — profondeur crypto, modèle de concurrence, schéma d'E/S, mise en cache, scalabilité, profondeur ML)
- ✅ Poids Atlas rééquilibrés à **20 / 20 / 5 / 55** (cœur chiffrement relevé à 35 %)
- ✅ **Évaluation fondée uniquement sur le code source** : les certifications tierces (SOC2 / ISO / HIPAA) sont indicatives uniquement, non notées
- ✅ **Alignement 1:1 des concurrents** entre la matrice et les justifications (score estimé par concurrent + avertissement sur les informations publiques)
- ✅ Notation à 5 dimensions (poids égaux de 20 %, sécurité fusionnée dans l'architecture)
- ✅ Justifications de sélection des concurrents (explication de 3 à 5 lignes par concurrent)
- ✅ Glossaire pour non-ingénieurs sur la page Détail de la sous-sécurité (MFA/SOC2/libsignal/PQXDH)
- ✅ Posture de l'ère AIDD : aucune pénalité pour l'usage de l'IA ou les commits à forte vélocité
- ✅ Guide `python3 -m pip` + badges de compteur de visiteurs
- ✅ Corrections de mise en page PDF : KeepTogether, KeepInFrame (SWOT), descriptions enveloppées sur 2 lignes

**Livré précédemment (v0.2.0)**
- ✅ Évaluation d'optimisation à 4 axes Atlas (à l'origine 25/20/5/50, désormais 20/20/5/55)
- ✅ Matrice de capacité d'implémentation (8e graphique concurrentiel)
- ✅ Tableau de bord web entièrement supprimé (CLI + PDF uniquement)
- ✅ Identité de marque noir + ciel Arc (#5271FF)
- ✅ Refonte du système typographique (interlignage, hiérarchie)
- ✅ Renforcement de la CI de sécurité (CodeQL, Dependabot, gitleaks)

**Prévu (v0.4.0+)**
- 🚧 Mode batch — analyser un portefeuille de dépôts en une seule commande
- 🚧 Suivi historique — réanalyser et afficher les écarts de score dans le temps
- 🚧 Adaptateur de notification Slack/Discord
- 🚧 Packs d'évaluation sectoriels (préréglages médical, fintech, jeu vidéo)
- 🚧 Distribution PyPI / Homebrew

Ouvrez une [issue](https://github.com/Atlas-Associates-Inc/Due-diligence-engine/issues) pour suggérer des fonctionnalités ou signaler des bugs.

---

## 🤝 Contribuer

Les contributions sont les bienvenues ! La base de code est petite et bien testée :

```bash
git clone https://github.com/Atlas-Associates-Inc/Due-diligence-engine
cd Due-diligence-engine
python3 -m pip install -e ".[dev]"
pytest
```

- **Rapports de bugs** : merci d'inclure la sortie de `dde --version` et une reproduction minimale
- **Demandes de fonctionnalités** : ouvrez d'abord une GitHub Discussion pour jauger l'intérêt
- **Pull requests** : assurez-vous que tous les tests passent + ajoutez de nouveaux tests pour les nouvelles fonctionnalités

---

## 📜 Licence

[Apache License 2.0](LICENSE) — Copyright © 2026 [Takayuki Miyano](https://github.com/taka-avantgarde) / [Atlas Associates Inc](https://github.com/Atlas-Associates-Inc)

---

<div align="center">

**Powered by Due Diligence Engine**

Created by [Takayuki Miyano](https://github.com/taka-avantgarde) — [Atlas Associates Inc](https://github.com/Atlas-Associates-Inc)

`v0.4.0` — 🌍 READMEs en 6 langues · 🆕 Claude Fable 5 / Sonnet 4.6 / Haiku 4.5 · 🌐 Recherche web en direct · notation à 5 dimensions

</div>
