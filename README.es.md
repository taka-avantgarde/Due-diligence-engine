<div align="center">

| 🇬🇧 [![English](https://img.shields.io/badge/English-30363D?style=for-the-badge)](README.md) | 🇯🇵 [![日本語](https://img.shields.io/badge/%E6%97%A5%E6%9C%AC%E8%AA%9E-30363D?style=for-the-badge)](README.ja.md) | 🇪🇸 [![Español](https://img.shields.io/badge/Espa%C3%B1ol-5271FF?style=for-the-badge)](README.es.md) | 🇸🇦 [![العربية](https://img.shields.io/badge/%D8%A7%D9%84%D8%B9%D8%B1%D8%A8%D9%8A%D8%A9-30363D?style=for-the-badge)](README.ar.md) | 🇫🇷 [![Français](https://img.shields.io/badge/Fran%C3%A7ais-30363D?style=for-the-badge)](README.fr.md) | 🇩🇪 [![Deutsch](https://img.shields.io/badge/Deutsch-30363D?style=for-the-badge)](README.de.md) |
|:--:|:--:|:--:|:--:|:--:|:--:|

<sub>👆 Click your language to switch ・ クリックで言語を切り替え</sub>

<sub>🪟 **En Windows:** funciona de forma nativa (Git debe estar en el PATH) — para la garantía de seguridad completa (bloqueo de permisos de archivos temporales), ejecuta con **WSL2**.</sub>

---

# 🔍 Due Diligence Engine

### **La IA de tu IDE → Analista de Due Diligence Técnica de Clase Mundial**

<sub>**Cero claves de API · PDF ante todo · OSS · Auditado con CodeQL**</sub>

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
[![Version](https://img.shields.io/badge/version-v0.4.1-000000?style=flat-square)](https://github.com/Atlas-Associates-Inc/Due-diligence-engine/releases)

[![Repo Views](https://komarev.com/ghpvc/?username=taka-avantgarde&repo=Due-diligence-engine&color=5271FF&style=flat-square&label=Repo+Views)](https://github.com/Atlas-Associates-Inc/Due-diligence-engine)

</div>

---

## ⚡ Inicio Rápido

**Instala una sola vez:**

```bash
python3 -m pip install --no-cache-dir git+https://github.com/Atlas-Associates-Inc/Due-diligence-engine.git
```

**Ejecuta desde el directorio de tu proyecto:**

```bash
dde prompt --pdf
```

Usa cualquier terminal de IDE con IA (Claude Code / Cursor / Copilot). Tu IA lee el código base, lo evalúa como un consultor tecnológico de clase mundial y escribe un PDF de 24 páginas en `~/Downloads/`. **Sin claves de API. Sin nube. Sin costo adicional.**

<details>
<summary><sub>Otras opciones de instalación · nota para macOS Homebrew</sub></summary>

Forma corta para Linux / venv / macOS antiguo:
```bash
pip3 install --no-cache-dir git+https://github.com/Atlas-Associates-Inc/Due-diligence-engine.git
```

Usuarios de macOS Homebrew: usen `python3 -m pip` — el comando `pip` por sí solo ya no viene instalado con Homebrew Python 3.12+.

</details>

---

## 💭 Cómo Obtener los Mejores Resultados

> **TL;DR**: Lanza la IA del nivel más alto al que tengas acceso en la terminal de tu IDE,
> pega el comando y espera de 10 a 20 minutos. Eso es todo.

**Configuración recomendada:**

- **Pon en marcha el modelo más capaz disponible** en tu IDE (Claude Fable 5, GPT-5, Gemini 2.5 Pro, etc.)
- **Pega `dde prompt --pdf`** en la terminal
- **Ve por un café** ☕ — la IA leerá cientos de archivos, evaluará a través de
  9+ dimensiones, investigará de 5 a 10 competidores a nivel global y construirá un PDF de consultoría de 24 páginas
- **Tiempo esperado**: **10-20 minutos** (más para códigos base grandes o modelos más profundos)

**¿Por qué este enfoque?**

| Inquietud | Respuesta |
|---------|--------|
| 🔐 **¿Fuga de datos?** | Ninguna. Todo se ejecuta dentro del sandbox de IA de tu IDE — sin servidores de terceros, sin telemetría. DDE en sí mismo es Python 100% local |
| 💰 **¿Costo?** | $0 adicionales. Usa tu suscripción de IA de IDE existente |
| 🔑 **¿Claves de API?** | No son necesarias. Tu IDE ya gestiona la autenticación de IA |
| ⚙️ **¿Configuración?** | Solo `python3 -m pip install`. Sin configuración, sin cuentas |
| 🎁 **¿Truco?** | No hay ninguno. DDE es un **proyecto por afición** — construido y liberado como código abierto por diversión. Úsalo libremente |

> **Hecho por un desarrollador en solitario como afición.** Si te ayuda, esa es recompensa suficiente. Dale una estrella al repositorio si te gusta ⭐

---

## 💻 Dónde se Ejecuta DDE — Usa la IA que Ya Tienes

DDE genera un prompt estructurado. **Cualquier agente de IA capaz de leer archivos y ejecutar comandos de shell** puede ejecutarlo. No se requiere ninguna integración, complemento ni inicio de sesión específico de DDE.

**Verificado y funcionando** (documentación oficial + probado, 2026-05):
- ✅ [**Claude Code**](https://code.claude.com/docs/en/overview) (CLI / VS Code / JetBrains / Desktop / Web — oficial de Anthropic)
- ✅ [**GitHub Copilot Agent Mode**](https://docs.github.com/en/copilot/using-github-copilot/copilot-chat/asking-github-copilot-questions-in-your-ide) (VS Code / Visual Studio / JetBrains / Xcode / Eclipse — disponibilidad general)

**Debería funcionar** (requisitos: lectura de archivos + ejecución de shell + idealmente búsqueda web):
- Cursor Agent, Gemini Code Assist, Continue.dev, Cody (Sourcegraph), Aider, Windsurf, Amazon Q Developer, JetBrains AI Assistant y terminales agénticas similares.

> ✅ Si ya usas cualquiera de los anteriores, estás a un `pip install` de ejecutar DDE hoy mismo.
> ¿Confirmaste que una terminal específica funciona? Cuéntanoslo en un [issue](https://github.com/Atlas-Associates-Inc/Due-diligence-engine/issues).

### 💰 Cero costo adicional

**Solo pagas por la suscripción de IA que ya tienes.** Claude Code Pro / GitHub Copilot / Cursor Pro / Gemini Advanced — DDE se ejecuta dentro de la asignación de tu IA existente. Sin niveles de precios de DDE, sin claves de API adicionales, sin tarifas ocultas, nunca.

---

## 👥 ¿Para Quién Es Esto?

| Usuario | Caso de Uso | Tiempo Ahorrado |
|------|----------|-----------|
| **Socios Técnicos de VC** | DD técnica previa a la inversión sobre candidatos de cartera | 2-5 días → 30 min |
| **CTOs / Líderes de Ingeniería** | Auditoría técnica interna antes de reuniones de junta | 1 semana → 1 hora |
| **Asesores Técnicos de M&A** | Due diligence sobre objetivos de adquisición | 1-2 semanas → 1 día |
| **Consultores de DD Independientes** | Evaluaciones técnicas de firmas boutique | escala: 1→10 clientes/semana |
| **Fundadores** | Autoevaluación antes de captar fondos | visión objetiva del propio código base |
| **Innovación Corporativa** | Evaluación de alianzas con proveedores / startups | ad-hoc → sistemática |

> Construido para ingenieros y responsables de decisiones técnicas que ya usan IA en su flujo de trabajo diario.

---

## 🆚 vs. Otras Herramientas

|   | DDE | DD Manual | Revisión de Código con IA Genérica | Plataformas DD SaaS |
|---|:---:|:---:|:---:|:---:|
| **Costo** | $0 (usa la IA de tu IDE) | $$$$ (honorarios de consultor) | tarifas de API | $$$$ (suscripción) |
| **Privacidad** | Solo local | Local | Envía el código al proveedor | Envía el código al proveedor |
| **Salida** | PDF de consultoría de 24 páginas | Informe personalizado | Comentarios en línea | Panel web |
| **Frescura de Datos** | ✅ Búsqueda web en vivo (2026) + URLs de fuentes | Depende del analista | Solo datos de entrenamiento (obsoletos) | Actualización controlada por el proveedor |
| **Profundidad Criptográfica** | Nivel PQXDH / Signal Protocol | Depende del consultor | Genérica | Genérica |
| **Gráficos Competitivos** | 7 + Matriz de Implementación | Investigación manual | Ninguno | Limitados |
| **Tiempo de Configuración** | 1 comando | Semanas | Minutos | Días (cuenta/onboarding) |
| **Personalización** | Acceso total al código fuente | Sí | Limitada | Bloqueada por el proveedor |

---

## Qué Hace Diferente a DDE

La mayoría de los "revisores de código con IA" comprueban:
> *"¿Tiene autenticación? ✓ ¿Tiene HTTPS? ✓ ¿Tiene pruebas? ✓"*

Eso es cumplimiento de casillas marcadas. **DDE profundiza más:**

> *"¿La cifrado es Signal Protocol? ¿Es PQXDH con ML-KEM-1024?
> ¿Está construido sobre libsignal/BoringSSL FFI, o es criptografía hecha en casa?
> ¿Publica el equipo investigación criptográfica?"*

Construido sobre la **Filosofía de Ingeniería Atlas**: ingeniería de ciberseguridad seria
a través de cifrado, privacidad, comunicaciones y defensa por capas — leído directamente
del código fuente. El cumplimiento de casillas marcadas (certificaciones SOC2, MFA, WebAuthn)
es solo de referencia, nunca se puntúa.

**🌐 Nuevo en v0.3.2**: Antes de leer cualquier código, la IA ejecuta **búsquedas web en vivo** para obtener el panorama competitivo más reciente (adquisiciones, cierres, nuevos participantes), rondas de financiación de 2026, CVEs recientes y cambios regulatorios. Cada competidor y cada celda de la matriz de implementación lleva una **URL de fuente + fecha de verificación**, y la salida JSON comienza con un bloque `data_freshness` que rastrea cada consulta de búsqueda. **El análisis obsoleto limitado al corte de entrenamiento se elimina estructuralmente.**

---

## 🔒 Filosofía de Ingeniería Atlas (vista paralela enfocada en ciberseguridad)

Un sistema de evaluación paralelo añadido junto a la puntuación estándar de 5 dimensiones.

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

## 📊 Puntuación Estándar de 5 Dimensiones (v0.3 — equilibrada, pesos iguales)

| Dimensión | Peso | Qué Detecta |
|-----------|-------:|-----------------|
| Originalidad Técnica | 20% | Envoltorio de API vs. propiedad intelectual genuina |
| Avance Tecnológico | 20% | Modernidad del stack |
| Profundidad de Implementación | 20% | PoC vs. producción |
| Calidad de Arquitectura (incl. Postura de Seguridad) | 20% | Calidad de la estructura + madurez de seguridad |
| Consistencia de las Afirmaciones | 20% | Discurso vs. realidad |

> **Puntuación Final** = Análisis Heurístico (30%) + Puntuación Promedio de IA (70%)

> **Cambio en v0.3**: La Postura de Seguridad se fusionó con la Calidad de Arquitectura. La seguridad ahora se evalúa como parte integral de una arquitectura de grado de producción, no como un silo separado.

```
Grade Bands:

  0      40       60      75       90     100
  |------|--------|-------|--------|------|
   F      D        C       B        A
   ✗      ⚠        ⚡       ✓        ★
```

| Calificación | Recomendación |
|-------|----------------|
| ★ A (90+)  | Candidato de inversión sólido |
| ✓ B (75-89)| Viable con condiciones |
| ⚡ C (60-74)| Preocupaciones significativas |
| ⚠ D (40-59) | Alto riesgo |
| ✗ F (<40)  | No invertir |

Cada dimensión también se califica de **Nv.1-10** con criterios explícitos.

---

## 🎯 7 Gráficos Competitivos × 6 Mercados

Para cada uno de los 6 mercados globales (Global / EE. UU. / EMEA / Japón / SEA / LATAM):

| # | Gráfico | Qué Muestra |
|---|-------|---------------|
| 1 | **Forrester Wave / Magic Quadrant** | Visión × Ejecución |
| 2 | **Matriz Crecimiento-Participación de BCG** | Crecimiento del mercado × Participación relativa |
| 3 | **Foso Tecnológico de McKinsey** | Posición competitiva × Foso técnico |
| 4 | **Madurez de Seguridad y Privacidad** | Implementación de seguridad × Preparación de privacidad |
| 5 | **Gobernanza de Datos y Transparencia** | Protección de datos × Transparencia de auditoría |
| 6 | **Retorno Ajustado al Riesgo de GS** | Riesgo a la baja × Potencial al alza |
| 7 | **Innovación vs. Comercialización** | Velocidad de I+D × Tracción de ARR (burbuja 3D) |

**6-16 competidores por gráfico** con leyendas que justifican los ejes y explican
*por qué* importa cada eje y *qué* captura la puntuación compuesta.

---

## 🆕 Matriz de Capacidad de Implementación

El 8.º gráfico competitivo — **~30 ítems × 5-10 principales competidores globales**:

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

Los ítems y competidores se **eligen dinámicamente según la industria del objetivo**
(mensajería, fintech, medicina, videojuegos, SaaS, IoT, etc.).

Marcado de 4 estados (estándar japonés de calificación tecnológica):
- **○ verificado** (implementación documentada públicamente)
- **△ afirmado** (declarado, no verificable)
- **× no implementado** (explícitamente ausente)
- **? desconocido** (no se puede determinar — preferible a adivinar)

Además de **justificaciones de selección de competidores** — 3-5 líneas cada una que explican por qué cada
competidor específico fue elegido como objetivo de comparación (sede, posición de mercado, categoría).

---

## 📄 Qué Contiene el PDF de 24 Páginas

| # | Sección | Contenido |
|---|---------|---------|
| 1 | Portada | Negro + acento cielo Arc (#5271FF), nombre del proyecto, puntuación, calificación |
| 2 | Panel de Puntuación | Gráfico de barras horizontales de **5 dimensiones** (20% cada una) + barómetro de puntuación |
| 3 | Resumen Ejecutivo | Resumen empresarial + técnico |
| 4 | Análisis FODA | Cuadrícula visual 2×2 con evidencia + analogías de negocio |
| 5 | Desglose de Puntuación | Justificación y habilitadores por dimensión |
| 6 | Evaluación de Nivel Técnico | Gráfico de barras Nv.1-10 de **5 dimensiones** + indicador general |
| 7 | Perspectiva Futura | Proyecciones a 1/3/5 años con nivel de confianza |
| 8 | Consejo Estratégico | Inmediato, mediano, largo plazo |
| 9 | Tesis de Inversión | Recomendación, riesgos, potencial al alza, comparables |
| 10 | Señales de Alerta | Calificadas por severidad (Crítica/Alta/Media/Baja) |
| 11 | Verificación del Sitio | Auditoría de capacidad técnica de 10 ítems (4 afirmación-vs-código + 6 medidos por código) |
| 12-14 | Análisis Competitivo | 7 gráficos × 6 mercados con justificación de ejes |
| 15 | **🆕 Justificaciones de Selección de Competidores** | Explicación de 3-5 líneas por competidor (por qué se eligió, sede, posición) |
| 16 | **Matriz de Capacidad de Implementación** | ~30 ítems × principales competidores, marcado ○△×? |
| 17 | **Panel de 4 Ejes de Atlas** | Performance / Stability / Lightweight / Security Strength |
| 18 | **Sub-Desglose de Seguridad + Glosario** | 5 sub-ítems con glosario para no ingenieros (MFA/SOC2/libsignal/PQXDH…) |
| 19-24 | Glosario · Consistencia · Costo · Certificado de Purga | Secciones de apéndice estándar |

---

## 🛠️ Uso

> 🌍 **Idiomas del informe (14):** `en` `ja` `es` `fr` `de` `pt` `nl` `it` `id` `zh` `ko` `vi` `th` `ar` — p. ej. `dde prompt --pdf --lang es`. El árabe se renderiza con modelado contextual RTL (el diseño de página sigue siendo LTR).

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

## 🔐 Seguridad y Filosofía OSS

| Garantía | Implementación |
|-----------|----------------|
| **Procesamiento solo local** | `dde prompt` nunca envía datos a ningún lugar |
| **Sin código fuente en los informes** | Los PDFs contienen solo hallazgos |
| **Retención de API 0-day** | `dde analyze` usa endpoints sin retención |
| **CI de seguridad automatizado** | CodeQL · Dependabot · pip-audit · safety · osv-scanner · GitHub Secret Scanning |
| **Protección de ramas** | `main` requiere PR + CI + protección de push de secretos |
| **Acceso a repos privados vía PAT** | Se usa en memoria una vez, nunca se almacena |

Informes de vulnerabilidades: ver [SECURITY.md](SECURITY.md) — SLA de respuesta de 48h.

### Por qué OSS es una característica de seguridad, no un riesgo

Código abierto significa que cada línea es auditable. Sin puertas traseras ocultas. Sin puntuación de caja negra.
Esta es la misma filosofía que Signal y libsignal: **la transparencia *es* confianza**.

---

## ❓ Preguntas Frecuentes

**P: ¿DDE envía mi código a algún lugar?**
R: No. `dde prompt` se ejecuta enteramente de forma local — genera un prompt estructurado que la IA de tu IDE lee. La IA evalúa el código en su lugar. El opcional `dde analyze` (BYOK) envía a proveedores de IA usando únicamente sus endpoints sin retención.

**P: ¿Por qué es gratis? ¿Cuál es el truco?**
R: No hay truco. DDE es OSS (Apache 2.0) y usa tu suscripción de IA de IDE existente (Claude Code / Cursor / Copilot). Sin telemetría, sin ventas adicionales.

**P: ¿Puedo usarlo en CI?**
R: Sí — ver [`action.yml`](action.yml). Añade la GitHub Action a los PRs para puntuación de DD automatizada.

**P: ¿Qué tan precisos son los gráficos competitivos?**
R: Los gráficos son investigados por la IA a partir de fuentes públicas (whitepapers, GitHub, blogs, informes SOC2). La confianza depende de la transparencia del competidor. Usa `?` (desconocido) con generosidad — los falsos positivos dañan la credibilidad más que las lagunas.

**P: ¿No están obsoletos los datos de los competidores? Los cortes de entrenamiento de la IA tienen 6-12 meses de antigüedad.**
R: A partir de v0.3.2, el **STEP 0 "Live Web Research" es obligatorio**. Antes de leer cualquier código, la IA ejecuta WebSearch / WebFetch para los movimientos de competidores de 2025-2026 (adquisiciones, cierres, nuevos participantes), las últimas rondas de financiación, CVEs y cambios regulatorios. Cada competidor y celda de la matriz lleva un campo `sources` (URL) y `last_verified` (fecha), y la salida JSON comienza con un bloque `data_freshness` que rastrea cada consulta de búsqueda ejecutada. Cuando el entorno de ejecución carece de herramientas de búsqueda web, la IA DEBE escribir un `data_cutoff_warning` — **sin salida obsoleta silenciosa por diseño**.

**P: ¿Por qué "Filosofía de Ingeniería Atlas"?**
R: DDE está construido por **Atlas Associates Inc**, la empresa detrás de Arc Messenger (mensajería E2EE con libsignal + PQXDH). La evaluación de 4 ejes refleja lo que realmente buscamos al evaluar tecnología.

**P: ¿Puedo personalizar los pesos de la puntuación?**
R: Los pesos de las 5 dimensiones son iguales, 20% cada uno (equilibrados, simples, interpretables). Los pesos de 4 ejes de Atlas (20/20/5/55) reflejan la filosofía de Atlas y también son fijos. Los pesos de los sub-ítems dentro de Security Strength se ajustan según el contexto de la industria.

**P: ¿Y si mi proyecto no es crítico en seguridad?**
R: La puntuación de 5 dimensiones (la Calidad de Arquitectura incluye la Postura de Seguridad con un 20% equilibrado) es tu puntuación principal. Los 4 ejes de Atlas son una vista de referencia paralela — ambos se muestran.

**P: Recibo `command not found: pip` — ¿cómo instalo?**
R: Usa `python3 -m pip install ...` en su lugar. macOS Homebrew Python 3.12+ ya no incluye un comando `pip` por sí solo. La forma `python3 -m pip` funciona en todas las plataformas (macOS / Linux / Windows / venv / pyenv / conda).

**P: ¿Por qué las certificaciones de terceros (SOC2, ISO, HIPAA) no afectan la puntuación?**
R: DDE evalúa el código fuente, no la insignia. Un servicio de almacenamiento en texto plano certificado SOC2 sigue teniendo almacenamiento en texto plano. Un servicio libsignal+PQXDH sin certificar sigue siendo criptográficamente sólido. Las certificaciones se muestran como contexto pero nunca se puntúan — ver la página de Sub-Desglose de Seguridad.

---

## 🗺️ Hoja de Ruta

**Lanzado recientemente (v0.3.x)**
- ✅ **Informes PDF en 14 idiomas** (2026-06, v0.4.0): el PDF de consultoría se genera en 14 idiomas mediante `--lang` — English / 日本語 / Español / Français / Deutsch / Português / Nederlands / Italiano / Bahasa Indonesia / 简体中文 / 한국어 / Tiếng Việt / ไทย / العربية (árabe con modelado contextual RTL). Fuentes Noto incluidas, sin configuración.
- ✅ **Correcciones de compatibilidad con Windows** (2026-06, v0.3.8): ruta temporal multiplataforma para el flujo de consultoría `--pdf` (antes un `/tmp` fijo) y soporte de portapapeles en Windows (`clip`) para `--copy`
- ✅ **READMEs en 6 idiomas** (2026-06, v0.3.7): selector de idioma en la parte superior de la página con el idioma activo resaltado — English / 日本語 / Español / العربية / Français / Deutsch, cada uno un `README.<lang>.md` separado
- ✅ **Actualización a Claude Fable 5** (2026-06, v0.3.6): el nivel de juez pasó de Opus 4.8 → **Fable 5** (`claude-fable-5`, el modelo de lanzamiento amplio más capaz de Anthropic, GA 2026-06-09). La clave del nivel se renombró `opus` → `fable`. Precios de $10/$50 por MTok (2× Opus 4.8, priorizando la calidad del veredicto final)
- ✅ **Pulido de gráficos del PDF + corrección de superposición de etiquetas** (2026-05, v0.3.5): todas las barras de los gráficos de Panel de Puntuación / Nivel Técnico / Competitivo / Matriz rediseñadas como modernas formas de píldora redondeadas. Las etiquetas largas en japonés (p. ej. 「アーキテクチャ品質（セキュリティ含む）」) que se superponían a las barras se corrigieron ampliando el área de etiquetas (verificado renderizando + inspeccionando visualmente cada página del PDF)
- ✅ **Actualización a Claude Opus 4.8** (2026-05, v0.3.3–4): el nivel de juez pasó de Opus 4.7→4.8 (Sonnet 4.6 / Haiku 4.5 también actualizados). Evita la retirada del 2026-06-15 de los antiguos Opus 4 / Sonnet 4 (20250514) y refleja la bajada de precio de Opus ($15→$5 de entrada)
- ✅ **Transferencia a la organización Atlas-Associates-Inc** (2026-05, v0.3.4–5): el repositorio se trasladó de taka-avantgarde → Atlas-Associates-Inc. Todas las URLs actualizadas, crédito de autor unificado a Takayuki Miyano (@taka-avantgarde) + Atlas Associates Inc, gitleaks → GitHub native Secret Scanning
- ✅ **Mandato de Investigación Web en Vivo** (2026-05, STEP 0): se añadió `_WEB_RESEARCH_MANDATE` en la parte superior de cada prompt de consultoría — la IA DEBE ejecutar WebSearch/WebFetch sobre el panorama de competidores, financiación, tendencias tecnológicas, CVEs y regulación **antes** de leer el código. La salida JSON ahora incluye un bloque `data_freshness` (fecha de búsqueda, consultas ejecutadas, fuentes consultadas) más campos `sources` / `last_verified` por competidor y por celda de la matriz. Elimina el análisis obsoleto limitado al corte de entrenamiento
- ✅ **Correcciones de erratas en el prompt**: "6 dimensions" → "5 dimensions" y "5つのチャート" → "7つのチャート" en el prompt de consultoría en JA
- ✅ **Corrección de la Auto-Prueba de CI** (2026-05): el `grep -c` de `action.yml` devolvía el código de salida 1 cuando no había coincidencias, lo cual `set -e` + `pipefail` propagaba como un fallo del trabajo. Corregido con el patrón `|| FALLBACK="0"`. **La Auto-Prueba de DDE ahora está en verde por primera vez**
- ✅ **Fórmula de puntuación explicitada en el README** (Puntuación Final = Heurística 30% + Promedio de IA 70%)
- ✅ **Dependabot completamente conectado**: se crearon las etiquetas `dependencies` / `security` / `ci` y se fusionaron los PR #23 (checkout v6) / #24 (upload-artifact v7) / #25 (osv-scanner-action v2.3.8)
- ✅ **Salvaguardas anti-sesgo propio**: advertencias explícitas de "el objetivo NO es DDE en sí mismo" en el encabezado del prompt (evita la confusión de la IA cuando DDE se ejecuta sobre otro proyecto)
- ✅ **Señales de alerta clarificadas**: se muestran como ítems accionables para la mejora del código (NO se factorizan en la puntuación)
- ✅ **Inicio Rápido simplificado** en el README (un solo comando de instalación + alternativas plegables)
- ✅ **Filosofía Atlas replanteada** como "defensa de ciberseguridad en general" (no solo cifrado — el cifrado es el mayor sub-peso con 35%)
- ✅ **Verificación del Sitio reenfocada a la pura capacidad técnica** (10 ítems: 4 afirmación-vs-código + 6 medidos por código — profundidad criptográfica, modelo de concurrencia, patrón de E/S, caché, escalabilidad, profundidad de ML)
- ✅ Pesos de Atlas reequilibrados a **20 / 20 / 5 / 55** (núcleo de cifrado subido a 35%)
- ✅ **Evaluación solo de código fuente**: las certificaciones de terceros (SOC2 / ISO / HIPAA) son solo de referencia, no se puntúan
- ✅ **Alineación 1:1 de competidores** entre la matriz y las justificaciones (puntuación estimada por competidor + descargo sobre información pública)
- ✅ Puntuación de 5 dimensiones (pesos iguales de 20%, Seguridad fusionada en Arquitectura)
- ✅ Justificaciones de Selección de Competidores (explicación de 3-5 líneas por competidor)
- ✅ Glosario para no ingenieros en la página de Sub-Desglose de Seguridad (MFA/SOC2/libsignal/PQXDH)
- ✅ Postura de la era AIDD: sin penalización por uso de IA o commits de alta velocidad
- ✅ Guía de `python3 -m pip` + insignias de contador de visitantes
- ✅ Correcciones de diseño del PDF: KeepTogether, KeepInFrame (FODA), descripciones envueltas en 2 líneas

**Lanzado previamente (v0.2.0)**
- ✅ Evaluación de Optimización de 4 Ejes de Atlas (originalmente 25/20/5/50, ahora 20/20/5/55)
- ✅ Matriz de Capacidad de Implementación (8.º gráfico competitivo)
- ✅ Panel web completamente eliminado (solo CLI + PDF)
- ✅ Identidad de marca Negro + cielo Arc (#5271FF)
- ✅ Renovación del sistema tipográfico (interlineado, jerarquía)
- ✅ Endurecimiento del CI de seguridad (CodeQL, Dependabot, gitleaks)

**Planificado (v0.4.0+)**
- 🚧 Modo por lotes — analizar una cartera de repositorios en un solo comando
- 🚧 Seguimiento histórico — reanalizar y mostrar deltas de puntuación a lo largo del tiempo
- 🚧 Adaptador de notificaciones Slack/Discord
- 🚧 Paquetes de evaluación específicos por industria (preajustes para medicina, fintech, videojuegos)
- 🚧 Distribución por PyPI / Homebrew

Abre un [issue](https://github.com/Atlas-Associates-Inc/Due-diligence-engine/issues) para sugerir funciones o reportar errores.

---

## 🤝 Contribuir

¡Las contribuciones son bienvenidas! El código base es pequeño y está bien probado:

```bash
git clone https://github.com/Atlas-Associates-Inc/Due-diligence-engine
cd Due-diligence-engine
python3 -m pip install -e ".[dev]"
pytest
```

- **Informes de errores**: por favor incluye la salida de `dde --version` y una reproducción mínima
- **Solicitudes de funciones**: abre primero una GitHub Discussion para medir el interés
- **Pull requests**: asegúrate de que todas las pruebas pasen + añade nuevas pruebas para las nuevas funciones

---

## 📜 Licencia

[Apache License 2.0](LICENSE) — Copyright © 2026 [Takayuki Miyano](https://github.com/taka-avantgarde) / [Atlas Associates Inc](https://github.com/Atlas-Associates-Inc)

---

<div align="center">

**Powered by Due Diligence Engine**

Created by [Takayuki Miyano](https://github.com/taka-avantgarde) — [Atlas Associates Inc](https://github.com/Atlas-Associates-Inc)

`v0.4.1` — 🌍 READMEs en 6 idiomas · 🆕 Claude Fable 5 / Sonnet 4.6 / Haiku 4.5 · 🌐 Investigación web en vivo · puntuación de 5 dimensiones

</div>
