#!/usr/bin/env python3
"""
Infographic Skill — Architecture Context Parser

Reads CLAUDE.md, project files, directory structure, and any provided text
to extract architecture components and their relationships.

Design principles:
  - Only include real deployable services / infrastructure — not dev tools,
    scripts, assets, or internal tooling directories.
  - Normalize component names: strip project-name prefixes, apply canonical
    display names for known tech stacks.
  - Extract the tech stack from well-known CLAUDE.md patterns (## Stack line,
    ASCII architecture diagrams) rather than naively matching keywords in prose.
  - Apply an architecture-principles filter: each layer must represent a genuine
    architectural concern (presentation, logic, data, infrastructure).

Output: A structured JSON that generate_linkedin_arch.py can consume directly.

Usage:
    python parse_context.py --root /path/to/project --output arch.json
    python parse_context.py --text "FastAPI backend, Flutter frontend, PostgreSQL, Redis, AWS S3" --output arch.json
    python parse_context.py --file CLAUDE.md --output arch.json
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# Category metadata
# ---------------------------------------------------------------------------

CATEGORY_COLORS = {
    "frontend":   {"bg": "#E3F2FD", "border": "#1E88E5", "label_color": "#0D47A1"},
    "mobile":     {"bg": "#EDE7F6", "border": "#7B1FA2", "label_color": "#4A148C"},
    "backend":    {"bg": "#FFF3E0", "border": "#F57C00", "label_color": "#E65100"},
    "database":   {"bg": "#E8F5E9", "border": "#388E3C", "label_color": "#1B5E20"},
    "infra":      {"bg": "#FCE4EC", "border": "#E91E63", "label_color": "#880E4F"},
    "cloud":      {"bg": "#E0F7FA", "border": "#0097A7", "label_color": "#006064"},
    "auth":       {"bg": "#FFF8E1", "border": "#FFC107", "label_color": "#FF6F00"},
    "queue":      {"bg": "#F3E5F5", "border": "#AB47BC", "label_color": "#6A1B9A"},
    "storage":    {"bg": "#E8EAF6", "border": "#3F51B5", "label_color": "#1A237E"},
    "monitoring": {"bg": "#EFEBE9", "border": "#795548", "label_color": "#3E2723"},
    "ci_cd":      {"bg": "#ECEFF1", "border": "#546E7A", "label_color": "#263238"},
    "ai_ml":      {"bg": "#F1F8E9", "border": "#7CB342", "label_color": "#33691E"},
    "other":      {"bg": "#F5F5F5", "border": "#9E9E9E", "label_color": "#212121"},
}

CATEGORY_LABELS = {
    "frontend":   "Frontend",
    "mobile":     "Mobile",
    "backend":    "Backend / API",
    "database":   "Database",
    "infra":      "Infrastructure",
    "cloud":      "Cloud Services",
    "auth":       "Auth",
    "queue":      "Queue / Events",
    "storage":    "Storage",
    "monitoring": "Monitoring",
    "ci_cd":      "CI/CD",
    "ai_ml":      "AI / ML",
    "other":      "Other",
}

LAYER_ORDER = [
    "frontend", "mobile", "auth",
    "backend", "ai_ml", "queue",
    "database", "storage",
    "cloud", "infra",
    "monitoring", "ci_cd",
    "other",
]


# ---------------------------------------------------------------------------
# Category hints — applied to *canonical tech names*, not raw dir names
# ---------------------------------------------------------------------------

CATEGORY_HINTS: dict[str, list[str]] = {
    "mobile":   ["flutter", "react native", "expo", "ionic", "swift", "kotlin",
                 "android", "ios", "mobile"],
    "frontend": ["react", "next.js", "nextjs", "vue", "nuxt", "angular",
                 "svelte", "tailwind", "vite", "remix", "astro", "web frontend",
                 "frontend"],
    "backend":  ["fastapi", "django", "flask", "express", "nestjs", "laravel",
                 "spring", "rails", "actix", "axum", "gin", "fiber",
                 "api", "backend", "server", "uvicorn"],
    "database": ["postgresql", "postgres", "mysql", "sqlite", "mongodb",
                 "dynamodb", "firestore", "cassandra", "supabase", "neon",
                 "planetscale", "redis", "chromadb", "qdrant", "pinecone",
                 "weaviate", "pgvector"],
    "infra":    ["terraform", "pulumi", "cdk", "kubernetes", "k8s", "helm",
                 "docker", "docker compose", "ansible",
                 "infra", "infrastructure"],
    "cloud":    ["aws", "gcp", "google cloud", "azure", "cloudflare",
                 "vercel", "netlify", "render", "railway", "fly.io",
                 # AWS managed services — these are cloud resources, not IaC
                 "ec2", "rds", "elasticache", "s3", "lambda",
                 "cloudfront", "route53", "route 53",
                 "ecs", "eks", "fargate",
                 "sqs", "sns", "cognito", "iam", "vpc", "ssm",
                 "cloud services"],
    "auth":     ["jwt", "oauth", "auth0", "keycloak", "clerk", "firebase auth",
                 "supabase auth", "cognito", "saml", "oidc", "authentication",
                 "authorization"],
    "queue":    ["kafka", "rabbitmq", "sqs", "celery", "bull", "bullmq",
                 "pub/sub", "pubsub", "nats", "eventbus", "message queue",
                 "worker"],
    "storage":  ["s3", "blob storage", "minio", "gcs", "cloudfront", "cdn",
                 "media", "files", "object storage"],
    "monitoring":["grafana", "prometheus", "datadog", "sentry", "cloudwatch",
                  "elk", "kibana", "newrelic", "honeycomb", "opentelemetry",
                  "logging", "observability", "monitoring"],
    "ci_cd":    ["github actions", "gitlab ci", "jenkins", "circleci",
                 "codepipeline", "tekton", "argocd", "ci/cd", "pipeline"],
    "ai_ml":    ["openai", "anthropic", "claude", "gpt", "llama", "ollama",
                 "langchain", "langgraph", "llamaindex", "hugging face",
                 "vector db", "chromadb", "qdrant", "pinecone", "weaviate",
                 "embedding", "rag", "llm", "ai", "ml", "gemini"],
}


def detect_category(name: str) -> str:
    """Classify a canonical tech name into an architecture category."""
    name_lower = name.lower()
    for cat, hints in CATEGORY_HINTS.items():
        for hint in hints:
            if hint in name_lower:
                return cat
    return "other"


# ---------------------------------------------------------------------------
# Known-technology extraction — tech stacks, not dir names
# ---------------------------------------------------------------------------

# Patterns that match *canonical* technology names in prose/Stack lines.
# Order matters: more specific patterns first.
TECH_PATTERNS = [
    # Mobile / Frontend
    r'\b(Flutter)\b',
    r'\b(React Native|Expo)\b',
    r'\b(React|Next\.?js|Nuxt|Angular|Vue\.?js|Svelte|Astro|Remix|Vite)\b',
    r'\b(TailwindCSS|Tailwind CSS|Bootstrap|Material UI|MUI|Ant Design)\b',
    # Backend frameworks
    r'\b(FastAPI|Django|Flask|Rails|Spring Boot|Spring|Express|NestJS|Laravel|Fastify|Gin|Fiber|Axum|Actix)\b',
    r'\b(GraphQL|REST|gRPC|WebSocket)\b',
    # Runtime / language (only when used as a service marker)
    r'\b(Node\.?js)\b',
    # Databases
    r'\b(PostgreSQL|Postgres|MySQL|MariaDB|SQLite|MongoDB|DynamoDB|Firestore|Cassandra|CockroachDB|PlanetScale|Neon|Supabase)\b',
    r'\b(Redis|Memcached|KeyDB)\b',
    r'\b(Prisma|Drizzle|SQLAlchemy|Alembic|TypeORM)\b',
    r'\b(ChromaDB|Qdrant|Pinecone|Weaviate|pgvector)\b',
    # Auth / identity
    r'\b(Auth0|Keycloak|Clerk|Cognito|Firebase Auth|Supabase Auth|Okta)\b',
    r'\b(JWT|OAuth\s*2\.?0?|OIDC|SAML)\b',
    # Queues / workers
    r'\b(Kafka|RabbitMQ|Celery|Bull(?:MQ)?|NATS|Pub/?Sub)\b',
    r'\b(SQS|SNS)\b',
    # AI / ML
    r'\b(OpenAI|GPT-?4o?(?:-mini)?|GPT-?3\.?5?)\b',
    r'\b(Anthropic)\b',
    r'\b(Claude\s+\d+(?:\.\d+)?(?:\s+(?:Opus|Sonnet|Haiku))?)\b',  # "Claude 3.5 Sonnet" etc, NOT bare "Claude"
    r'\b(LangChain|LangGraph|LlamaIndex|Llama\.?Index)\b',
    r'\b(Gemini(?:\s+\d+(?:\.\d+)?(?:\s+Pro|Flash)?)?)\b',
    r'\b(Hugging Face|Ollama|Llama[. ]?2|Mistral|Mixtral)\b',
    # Cloud providers + specific services
    r'\b(AWS|GCP|Google Cloud|Azure|Cloudflare)\b',
    r'\b(EC2|Lambda|ECS|EKS|Fargate|CloudFront|Route\s*53|VPC|IAM|SSM|S3|RDS|ElastiCache)\b',
    r'\b(Vercel|Netlify|Render|Railway|Fly\.io)\b',
    # Infrastructure
    r'\b(Terraform|Pulumi|CDK|Ansible)\b',
    r'\b(Kubernetes|k8s|Helm|Docker(?:\s+Compose)?)\b',
    r'\b(Nginx|Caddy|Traefik|HAProxy)\b',
    r'\b(systemd)\b',
    # Monitoring
    r'\b(Grafana|Prometheus|DataDog|Sentry|CloudWatch|Kibana|OpenTelemetry|New Relic)\b',
    # CI/CD
    r'\b(GitHub Actions|GitLab CI|Jenkins|CircleCI|CodePipeline|ArgoCD|Tekton)\b',
]

# --- Canonical name normalisation map ---
# Raw matched string → normalized display name
_NORMALIZE: dict[str, str] = {
    "postgres":       "PostgreSQL",
    "postgresql":     "PostgreSQL",
    "nextjs":         "Next.js",
    "next.js":        "Next.js",
    "vuejs":          "Vue.js",
    "vue.js":         "Vue.js",
    "nodejs":         "Node.js",
    "node.js":        "Node.js",
    "reactnative":    "React Native",
    "tailwindcss":    "Tailwind CSS",
    "nestjs":         "NestJS",
    "bullmq":         "BullMQ",
    "llamaindex":     "LlamaIndex",
    "langgraph":      "LangGraph",
    "langchain":      "LangChain",
    "chromadb":       "ChromaDB",
    "k8s":            "Kubernetes",
    "gpt-4o-mini":    "GPT-4o-mini",
    "gpt-4o":         "GPT-4o",
    "gpt-4":          "GPT-4",
    "gpt4":           "GPT-4",
    "gpt-3.5":        "GPT-3.5",
    "dockercompose":  "Docker Compose",
    "docker compose": "Docker Compose",
    "docker":         "Docker",
    "github actions": "GitHub Actions",
    "gitlab ci":      "GitLab CI",
    "pub/sub":        "Pub/Sub",
    "pubsub":         "Pub/Sub",
    "oauth2.0":       "OAuth 2.0",
    "oauth 2.0":      "OAuth 2.0",
    "oauth2":         "OAuth 2.0",
    "ec2":            "EC2",
    "rds":            "RDS",
    "vpc":            "VPC",
    "iam":            "IAM",
    "ssm":            "SSM",
    "s3":             "S3",
    "sqs":            "SQS",
    "sns":            "SNS",
    "ecs":            "ECS",
    "eks":            "EKS",
    "jwt":            "JWT",
}

# ---------------------------------------------------------------------------
# Implementation-detail filter
# These are internal libraries / tools that live *inside* a service.
# They are NOT architectural boundaries and should not appear as diagram nodes.
# ---------------------------------------------------------------------------

_IMPL_DETAILS: frozenset[str] = frozenset({
    # ORM / migrations (live inside the backend service)
    "sqlalchemy", "alembic", "prisma", "drizzle", "typeorm", "sequelize",
    # Validation
    "pydantic", "zod", "yup", "marshmallow",
    # Test frameworks
    "pytest", "jest", "vitest", "mocha", "chai", "rspec",
    # Linting / formatting
    "black", "isort", "eslint", "prettier", "ruff",
    # Flutter internal state mgmt / routing
    "riverpod", "bloc", "provider", "gorouter", "go_router",
    # DI containers
    "dependency-injector", "inversify",
    # ASGI/WSGI servers (deployment detail, not an architectural box)
    "uvicorn", "gunicorn", "hypercorn",
    # AWS SDK clients (internal lib, not a service boundary)
    "boto3", "botocore",
    # HTTP clients
    "httpx", "aiohttp", "requests", "axios",
    # Auth utility libs (JWT is the protocol, these are implementations)
    "passlib", "bcrypt", "python-jose", "pyjwt", "python_jose",
    # Cache layer utility (Redis is the actual service; aiocache is the client)
    "aiocache",
    # Process supervisor (operational concern, not a service boundary)
    "systemd",
    # WebSocket is a protocol, not a service
    "websocket", "websockets",
})


def _normalize_name(raw: str) -> str:
    key = raw.lower().replace(" ", "").replace(".", "").replace("-", "")
    # Try exact normalized key first
    for k, v in _NORMALIZE.items():
        if k.replace(" ", "").replace(".", "").replace("-", "").replace("_", "") == key:
            return v
    # Title-case pass for unknown tokens
    return raw.strip()


def _is_impl_detail(name: str) -> bool:
    """Return True if this is an internal implementation detail, not an arch boundary."""
    key = name.lower().replace(" ", "").replace("-", "").replace("_", "").replace(".", "")
    return key in {k.replace(" ", "").replace("-", "").replace("_", "") for k in _IMPL_DETAILS}


def extract_tech_from_text(text: str) -> list[dict]:
    """Extract canonical tech names from free-form text."""
    found = []
    seen: set[str] = set()

    for pattern in TECH_PATTERNS:
        for m in re.finditer(pattern, text, re.IGNORECASE):
            raw = m.group(0).strip()
            name = _normalize_name(raw)
            key = name.lower()
            if key not in seen and len(key) > 1:
                seen.add(key)
                found.append({"name": name, "category": detect_category(name)})

    return found


# ---------------------------------------------------------------------------
# CLAUDE.md / Stack-line parsing
# ---------------------------------------------------------------------------

def parse_stack_line(text: str) -> list[dict]:
    """
    Parse a CLAUDE.md '## Stack' or single-line bullet like:
      Python 3.11 · FastAPI · Dart / Flutter 3.x · Terraform · PostgreSQL 16 · Redis 7
    Splits on · / , and runs each token through tech extraction.
    """
    # Find the stack section
    match = re.search(
        r'(?:^#{1,3}\s*Stack\b[^\n]*\n)(.*?)(?=\n#{1,3}\s|\Z)',
        text, re.IGNORECASE | re.DOTALL | re.MULTILINE
    )
    if not match:
        # Try inline "Stack:" label
        match = re.search(r'Stack\s*[:·—-]\s*([^\n]{10,})', text, re.IGNORECASE)
    if not match:
        return []

    raw_stack = match.group(1)[:500]  # cap to avoid parsing huge sections
    # Replace separators with commas and extract
    normalized = re.sub(r'[·/|•\t]+', ',', raw_stack)
    normalized = re.sub(r'\s+', ' ', normalized)
    return extract_tech_from_text(normalized)


def parse_architecture_diagram(text: str) -> list[dict]:
    """
    Find ASCII/box-drawing architecture diagrams and extract service labels.
    Lines inside box-drawing characters (│, ┌, └, etc.) often name services.
    """
    found = []
    seen: set[str] = set()

    # Lines that are inside ASCII boxes
    box_pattern = re.compile(r'[│┃|].*?[│┃|]|[│┃].*', re.UNICODE)
    for line in text.splitlines():
        if not box_pattern.search(line):
            continue
        # Strip box chars and extract tech
        clean = re.sub(r'[│┃┌└┐┘├┤┬┴┼─╌╍═╒╕╘╛╞╡╤╧╪╫╬╔╗╚╝╠╣╦╩╬|+\-]', ' ', line)
        for comp in extract_tech_from_text(clean):
            key = comp["name"].lower()
            if key not in seen:
                seen.add(key)
                found.append(comp)

    return found


# ---------------------------------------------------------------------------
# Directory service detection — only real deployable services
# ---------------------------------------------------------------------------

# Files that indicate a directory is an actual deployable service / IaC module
_SERVICE_INDICATORS = {
    "main.py":              "backend",
    "app.py":               "backend",
    "manage.py":            "backend",
    "pubspec.yaml":         "mobile",
    "package.json":         "frontend",   # refined below by content
    "go.mod":               "backend",
    "Cargo.toml":           "backend",
    "build.gradle":         "backend",
    "build.gradle.kts":     "backend",
    "Dockerfile":           None,         # category depends on other hints
    "docker-compose.yml":   "infra",
    "docker-compose.yaml":  "infra",
    "pyproject.toml":       "backend",
    # IaC
    "main.tf":              "infra",
    "provider.tf":          "infra",
    "terraform.tf":         "infra",
    "variables.tf":         "infra",
}

# Dirs that are NOT real architectural services — always skip
_EXCLUDED_DIR_NAMES: frozenset[str] = frozenset({
    # VCS / tooling
    ".git", ".github", ".gitlab", ".husky", ".vscode", ".idea", ".claude",
    # Build / cache artefacts
    "node_modules", "__pycache__", ".pytest_cache", ".mypy_cache",
    "venv", ".venv", "env", ".env", "build", "dist", "out", "target",
    "coverage", ".nyc_output", ".next", ".nuxt",
    # Marketing / docs
    "docs", "doc", "wiki", "assets", "static", "public", "media",
    "linkedin_assets", "infographics", "designs",
    # Meta
    "scripts", "scripts_emotionai", "tools", "examples", "samples",
    "tests", "test", "e2e", ".planning",
})

# Regex patterns — dirs whose names match are excluded
_EXCLUDED_DIR_PATTERNS: list[re.Pattern] = [
    re.compile(r'^\.'),                    # any hidden dir
    re.compile(r'_assets?$', re.I),        # *_assets
    re.compile(r'[-_]assets?', re.I),      # *-assets-*, etc.
    re.compile(r'scripts?$', re.I),        # *scripts
    re.compile(r'^scripts?[-_]', re.I),    # scripts-*
    re.compile(r'[-_]scripts?[-_]', re.I), # *scripts*
    re.compile(r'designer$', re.I),        # *-designer (Claude skills / design tools)
    re.compile(r'[-_]designer', re.I),
    re.compile(r'linkedin', re.I),
    re.compile(r'infographic', re.I),
    re.compile(r'template', re.I),
    re.compile(r'boilerplate', re.I),
    re.compile(r'example', re.I),
    re.compile(r'sample', re.I),
    re.compile(r'todo', re.I),
    re.compile(r'playground', re.I),
    re.compile(r'poc$', re.I),
    re.compile(r'sandbox', re.I),
]


def _is_excluded_dir(name: str) -> bool:
    if name in _EXCLUDED_DIR_NAMES:
        return True
    for pat in _EXCLUDED_DIR_PATTERNS:
        if pat.search(name):
            return True
    return False


def _category_from_service_files(dirpath: Path) -> str | None:
    """Return the best-guess category if the dir contains a deployable entry point."""
    for fname, cat in _SERVICE_INDICATORS.items():
        if (dirpath / fname).exists():
            # Refine package.json: could be backend (node) or frontend
            if fname == "package.json":
                try:
                    pkg = json.loads((dirpath / fname).read_text(errors="ignore"))
                    deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}
                    if any(d in deps for d in ["next", "react", "vue", "nuxt", "@angular/core", "svelte"]):
                        return "frontend"
                except Exception:
                    pass
                return "backend"
            return cat
    return None


def _display_name_for_dir(dir_name: str, project_name: str, category: str, dirpath: Path) -> str:
    """
    Convert a raw directory name into a human-readable display name.
    Strips project-name prefix and maps known suffixes to canonical titles.
    """
    name = dir_name

    # Strip project prefix (e.g. emotionai-api → api, myapp_backend → backend)
    if project_name:
        pn = project_name.lower().replace("-", "").replace("_", "")
        slug = name.lower().replace("-", "").replace("_", "")
        if slug.startswith(pn):
            suffix = slug[len(pn):].lstrip("-_")
            if suffix:
                name = suffix
            # else: name == project prefix → keep dir name for now

    # --- Tech-file checks take priority over generic suffix mapping ---

    # Flutter → "Flutter App"
    if (dirpath / "pubspec.yaml").exists():
        return "Flutter App"

    # Terraform IaC → "Terraform IaC"
    if (dirpath / "main.tf").exists() or (dirpath / "provider.tf").exists():
        return "Terraform IaC"

    # FastAPI / Django / Flask backend
    if (dirpath / "main.py").exists() or (dirpath / "app.py").exists():
        req = dirpath / "requirements.txt"
        if req.exists():
            req_text = req.read_text(errors="ignore").lower()
            if "fastapi" in req_text:
                return "FastAPI Backend"
            if "django" in req_text:
                return "Django Backend"
            if "flask" in req_text:
                return "Flask Backend"
        return "Python Backend"

    # Go / Rust / Java services
    for go_marker in ["go.mod", "Cargo.toml", "build.gradle", "build.gradle.kts"]:
        if (dirpath / go_marker).exists():
            suffix_lower = name.lower().replace("-", "_")
            return suffix_lower.replace("_", " ").title() + " Service"

    # Canonical suffix → display name (fallback for ambiguous dirs)
    SUFFIX_MAP: dict[str, str] = {
        "api":      "API Service",
        "backend":  "Backend API",
        "server":   "Backend Server",
        "app":      "Mobile App",
        "mobile":   "Mobile App",
        "web":      "Web Frontend",
        "frontend": "Web Frontend",
        "infra":    "Infrastructure",
    }

    suffix_lower = name.lower().replace("-", "_")
    if suffix_lower in SUFFIX_MAP:
        return SUFFIX_MAP[suffix_lower]

    # Fallback: title-case the dir name after stripping project prefix
    display = name.replace("-", " ").replace("_", " ").title()
    return display


def scan_project_services(root: Path) -> list[dict]:
    """
    Scan top-level directories and return only real deployable services / IaC.
    Skips dev tools, scripts, assets, hidden dirs, and internal tooling.
    """
    project_name = root.name.lower().replace("-", "").replace("_", "")
    services = []
    seen: set[str] = set()

    try:
        entries = sorted(root.iterdir())
    except PermissionError:
        return []

    for entry in entries:
        if not entry.is_dir():
            continue
        if _is_excluded_dir(entry.name):
            continue

        cat = _category_from_service_files(entry)
        if cat is None:
            continue  # Not a real deployable service

        display = _display_name_for_dir(entry.name, project_name, cat, entry)
        key = display.lower()
        if key not in seen:
            seen.add(key)
            services.append({"name": display, "category": cat})

    return services


# ---------------------------------------------------------------------------
# Root-level config files (add canonical tech only, not dir names)
# ---------------------------------------------------------------------------

_ROOT_CONFIG_TECH: dict[str, tuple[str, str]] = {
    "docker-compose.yml":  ("Docker Compose", "infra"),
    "docker-compose.yaml": ("Docker Compose", "infra"),
    "Dockerfile":          ("Docker", "infra"),
    ".github":             ("GitHub Actions", "ci_cd"),
    ".gitlab-ci.yml":      ("GitLab CI", "ci_cd"),
    "Jenkinsfile":         ("Jenkins", "ci_cd"),
    "k8s":                 ("Kubernetes", "infra"),
    "helm":                ("Helm", "infra"),
}


def scan_root_config(root: Path) -> list[dict]:
    found = []
    seen: set[str] = set()
    for fname, (name, cat) in _ROOT_CONFIG_TECH.items():
        p = root / fname
        if p.exists():
            key = name.lower()
            if key not in seen:
                seen.add(key)
                found.append({"name": name, "category": cat})
    return found


# ---------------------------------------------------------------------------
# Garbage filter — remove items that clearly aren't architecture components
# ---------------------------------------------------------------------------

_GARBAGE_PATTERNS = [
    # Very short words that leaked from prose / diff hunks
    re.compile(r'^\s*(?:if|new|old|and|or|in|on|at|to|the|for|of|by|a|an|across|above|below|up|down|left|right|next|prev|back|all|any|some|such|this|that|with|from|into|out|via|per|vs|etc|e\.?g\.?|i\.?e\.?)\s*$', re.I),
    # Raw file-path fragments
    re.compile(r'^[\./\\]'),
    # Items that look like variable names / identifiers with underscores but no real meaning
    re.compile(r'^[a-z_]{2,}_[a-z_]{2,}_[a-z_]{2,}$'),
    # Pure numeric strings
    re.compile(r'^\d+[\d.]*$'),
]


def _is_garbage(name: str) -> bool:
    if len(name.strip()) < 2:
        return True
    for pat in _GARBAGE_PATTERNS:
        if pat.match(name.strip()):
            return True
    return False


# ---------------------------------------------------------------------------
# De-duplication with coverage reasoning
# ---------------------------------------------------------------------------

def _deduplicate(components: list[dict]) -> list[dict]:
    """
    Remove duplicates, implementation details, and redundant sub-strings.

    Priority rules:
    - Implementation details (ORMs, SDKs, internal libs) are filtered out first.
    - More-specific name wins over shorter generic name:
      "Docker Compose" shadows "Docker", "Flutter App" shadows "Flutter".
    - Within a category, if two names are semantically similar, keep the longer/more specific one.
    """
    def _key(n: str) -> str:
        return n.lower().replace(" ", "").replace(".", "").replace("-", "").replace("_", "")

    # Build map: key → component (keep first seen), filtering garbage and impl details
    by_key: dict[str, dict] = {}
    for comp in components:
        if _is_garbage(comp["name"]):
            continue
        if _is_impl_detail(comp["name"]):
            continue
        k = _key(comp["name"])
        if k not in by_key:
            by_key[k] = comp

    # Remove items whose normalized key is a prefix/substring of a longer item's key
    # This ensures "flutter" is dropped when "flutterapp" exists, etc.
    keys = list(by_key.keys())
    survivors = []
    for k, comp in by_key.items():
        shadowed = any(
            k != other and k in other
            for other in keys
        )
        if not shadowed:
            survivors.append(comp)

    return survivors


# ---------------------------------------------------------------------------
# Group into display layers
# ---------------------------------------------------------------------------

def group_into_layers(components: list[dict]) -> list[dict]:
    groups: dict[str, list[str]] = {}
    for comp in components:
        cat = comp.get("category", "other")
        groups.setdefault(cat, []).append(comp["name"])

    # Cap each group at 6 items (diagram readability)
    for cat in groups:
        if len(groups[cat]) > 6:
            groups[cat] = groups[cat][:5] + ["…"]

    layers = []
    for cat in LAYER_ORDER:
        if cat in groups and groups[cat]:
            c = CATEGORY_COLORS[cat]
            layers.append({
                "label": CATEGORY_LABELS[cat],
                "category": cat,
                "items": groups[cat],
                "bg": c["bg"],
                "border": c["border"],
                "label_color": c["label_color"],
            })
    return layers


# ---------------------------------------------------------------------------
# Connection inference (architecture-principle-aware)
# ---------------------------------------------------------------------------

# Canonical data-flow edges (src, dst) following standard layered architecture
_CANONICAL_EDGES = [
    # Presentation → Logic
    ("frontend",  "backend"),
    ("mobile",    "backend"),
    # Logic → Data
    ("backend",   "database"),
    ("backend",   "queue"),
    ("backend",   "storage"),
    # Logic → External services
    ("backend",   "auth"),
    ("backend",   "ai_ml"),
    ("backend",   "monitoring"),
    # Logic ↔ Cloud managed services
    ("backend",   "cloud"),
    # Queue → Logic (workers read queues)
    ("queue",     "backend"),
    # IaC → Cloud
    ("infra",     "cloud"),
    # CI/CD → IaC / Cloud
    ("ci_cd",     "infra"),
    ("ci_cd",     "cloud"),
]


def infer_connections(layers: list[dict]) -> list[dict]:
    present = {l["category"] for l in layers}
    return [
        {"from": src, "to": dst, "label": ""}
        for src, dst in _CANONICAL_EDGES
        if src in present and dst in present
    ]


# ---------------------------------------------------------------------------
# File readers
# ---------------------------------------------------------------------------

def _read_safe(path: Path, max_bytes: int = 80_000) -> str:
    try:
        with path.open(encoding="utf-8", errors="ignore") as f:
            return f.read(max_bytes)
    except Exception:
        return ""


def _find_claude_md(root: Path) -> str:
    for fname in ["CLAUDE.md", "claude.md", "CLAUDE.MD", ".claude/CLAUDE.md"]:
        p = root / fname
        if p.exists():
            return _read_safe(p)
    return ""


def _find_readme(root: Path) -> str:
    for fname in ["README.md", "readme.md", "README.rst", "README.txt"]:
        p = root / fname
        if p.exists():
            return _read_safe(p, max_bytes=20_000)
    return ""


# ---------------------------------------------------------------------------
# Main build function
# ---------------------------------------------------------------------------

def build_arch_json(
    root: Path | None = None,
    extra_text: str = "",
    title: str = "",
    subtitle: str = "",
    author: str = "",
    linkedin_cta: str = "",
) -> dict:
    components: list[dict] = []

    if root:
        # 1. Parse CLAUDE.md — highest signal source
        claude_md = _find_claude_md(root)
        if claude_md:
            # Stack line (most reliable)
            components += parse_stack_line(claude_md)
            # ASCII architecture diagram labels
            components += parse_architecture_diagram(claude_md)
            # General tech mentions in prose
            components += extract_tech_from_text(claude_md)

        # 2. Scan for real deployable service directories
        components += scan_project_services(root)

        # 3. Root-level config files (GitHub Actions, docker-compose, etc.)
        components += scan_root_config(root)

        # 4. README for additional tech mentions
        readme = _find_readme(root)
        if readme:
            components += extract_tech_from_text(readme[:10_000])

        # 5. Architecture docs
        for doc in ["docs/architecture.md", "docs/ARCHITECTURE.md",
                    "architecture.md", "ARCHITECTURE.md"]:
            doc_path = root / doc
            if doc_path.exists():
                components += extract_tech_from_text(_read_safe(doc_path))

    # 6. Extra text / --text / --file argument
    if extra_text:
        components += parse_stack_line(extra_text)
        components += extract_tech_from_text(extra_text)

    # De-duplicate and filter garbage
    components = _deduplicate(components)

    layers = group_into_layers(components)
    connections = infer_connections(layers)

    return {
        "title": title or (f"{root.name.replace('-', ' ').replace('_', ' ').title()} Architecture" if root else "System Architecture"),
        "subtitle": subtitle or "Technical Architecture Overview",
        "author": author or "",
        "linkedin_cta": linkedin_cta or "Follow for more software architecture content",
        "layers": layers,
        "connections": connections,
        "format": "linkedin",
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Parse project context into architecture JSON")
    parser.add_argument("--root",     help="Project root directory")
    parser.add_argument("--text",     help="Free-form text describing the architecture")
    parser.add_argument("--file",     help="Path to a specific file (CLAUDE.md, README, etc.)")
    parser.add_argument("--title",    help="Diagram title override")
    parser.add_argument("--subtitle", help="Diagram subtitle override")
    parser.add_argument("--author",   help="Author name for LinkedIn footer")
    parser.add_argument("--cta",      help="LinkedIn call-to-action text")
    parser.add_argument("--output",   default="arch.json", help="Output JSON file path")
    args = parser.parse_args()

    extra = args.text or ""
    if args.file:
        extra += "\n" + Path(args.file).read_text(encoding="utf-8", errors="ignore")

    root = Path(args.root) if args.root else None

    result = build_arch_json(
        root=root,
        extra_text=extra,
        title=args.title or "",
        subtitle=args.subtitle or "",
        author=args.author or "",
        linkedin_cta=args.cta or "",
    )

    out = Path(args.output)
    out.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(f"✅  Architecture JSON → {out.resolve()}")
    print(f"   {len(result['layers'])} layers, {sum(len(l['items']) for l in result['layers'])} components")
    for layer in result["layers"]:
        print(f"   [{layer['label']}] {', '.join(layer['items'])}")
