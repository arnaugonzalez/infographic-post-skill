#!/usr/bin/env python3
"""
Infographic Skill — Architecture Context Parser

Reads CLAUDE.md, project files, directory structure, and any provided text
to extract architecture components and their relationships.

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
# Heuristics: map file/folder names → component categories
# ---------------------------------------------------------------------------

CATEGORY_HINTS = {
    "frontend": ["frontend", "web", "ui", "client", "app", "flutter", "react",
                 "angular", "vue", "next", "nuxt", "svelte", "ionic"],
    "backend": ["backend", "api", "server", "service", "fastapi", "django",
                "flask", "express", "rails", "spring", "nest", "laravel"],
    "database": ["database", "db", "postgres", "postgresql", "mysql", "sqlite",
                 "mongo", "mongodb", "redis", "cassandra", "dynamodb", "supabase",
                 "firestore", "prisma", "drizzle"],
    "infra": ["infra", "infrastructure", "terraform", "pulumi", "cdk",
              "kubernetes", "k8s", "helm", "docker", "compose"],
    "cloud": ["aws", "gcp", "azure", "s3", "lambda", "ec2", "rds", "cloudfront",
              "route53", "vpc", "ecs", "eks", "sqs", "sns", "cognito", "iam"],
    "auth": ["auth", "authentication", "authorization", "oauth", "jwt",
             "keycloak", "auth0", "cognito"],
    "queue": ["queue", "kafka", "rabbitmq", "sqs", "celery", "bull", "worker",
              "broker", "pubsub", "eventbus"],
    "storage": ["storage", "s3", "blob", "minio", "cdn", "cloudfront",
                "files", "media", "assets"],
    "monitoring": ["monitoring", "logging", "observability", "grafana",
                   "prometheus", "datadog", "sentry", "cloudwatch", "elk"],
    "ci_cd": ["ci", "cd", "cicd", "pipeline", "github-actions", "gitlab-ci",
              "jenkins", "codepipeline", "deploy"],
    "mobile": ["mobile", "android", "ios", "flutter", "react-native", "expo"],
    "ai_ml": ["ai", "ml", "model", "llm", "openai", "anthropic", "langchain",
              "vector", "embedding", "rag"],
}

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


# ---------------------------------------------------------------------------
# Component detection
# ---------------------------------------------------------------------------

def detect_category(name: str) -> str:
    name_lower = name.lower().replace("-", "").replace("_", "").replace(" ", "")
    for cat, hints in CATEGORY_HINTS.items():
        for hint in hints:
            if hint.replace("-", "").replace("_", "") in name_lower:
                return cat
    return "other"


def extract_components_from_text(text: str) -> list[dict]:
    """Extract components from free-form text (CLAUDE.md, architecture notes, etc.)."""
    components = []
    seen = set()

    # Patterns to find component mentions
    patterns = [
        # "X service", "X backend", "X frontend", etc.
        r'\b([A-Z][a-zA-Z0-9\-_]+(?:\s+[A-Z][a-zA-Z0-9\-_]+){0,2})\s+(?:service|server|backend|frontend|api|worker|job|queue|database|db|store|cache|layer|module|component|system)\b',
        # Technologies: FastAPI, Flutter, PostgreSQL, Redis, etc.
        r'\b(FastAPI|Django|Flask|Rails|Spring|Express|NestJS|Laravel|Fastify)\b',
        r'\b(React|Angular|Vue|Next\.?js|Nuxt|Svelte|Flutter|Ionic|React Native)\b',
        r'\b(PostgreSQL|Postgres|MySQL|SQLite|MongoDB|Redis|DynamoDB|Firestore|Cassandra|Supabase)\b',
        r'\b(AWS|GCP|Azure|Cloudflare|Vercel|Netlify|Render|Railway|Fly\.io)\b',
        r'\b(S3|Lambda|EC2|RDS|CloudFront|Route53|ECS|EKS|SQS|SNS|Cognito|IAM|VPC)\b',
        r'\b(Kafka|RabbitMQ|Celery|Bull|BullMQ|Pub[/ ]?Sub)\b',
        r'\b(Kubernetes|k8s|Docker|Helm|Terraform|Pulumi|CDK)\b',
        r'\b(Grafana|Prometheus|DataDog|Sentry|CloudWatch|ELK|Kibana)\b',
        r'\b(GitHub Actions|GitLab CI|Jenkins|CircleCI|CodePipeline)\b',
        r'\b(Auth0|Keycloak|Cognito|Clerk|Supabase Auth|Firebase Auth)\b',
        r'\b(LangChain|LangGraph|OpenAI|Anthropic|Claude|GPT|Llama|Ollama)\b',
    ]

    for pattern in patterns:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            name = match.group(1).strip()
            key = name.lower()
            if key not in seen and len(name) > 2:
                seen.add(key)
                cat = detect_category(name)
                components.append({
                    "name": name,
                    "category": cat,
                    "description": "",
                })

    return components


def scan_project_dirs(root: Path) -> list[dict]:
    """Scan top-level directories and known config files to detect components."""
    components = []
    seen = set()

    # Top-level dirs
    try:
        for entry in sorted(root.iterdir()):
            if entry.is_dir() and not entry.name.startswith(".") and entry.name not in (
                "node_modules", "__pycache__", ".git", "venv", ".venv", "dist", "build",
                "coverage", ".pytest_cache", ".mypy_cache"
            ):
                name = entry.name
                cat = detect_category(name)
                key = name.lower()
                if key not in seen:
                    seen.add(key)
                    components.append({"name": name, "category": cat, "description": ""})
    except PermissionError:
        pass

    # package.json, pyproject.toml, pubspec.yaml — detect tech stack
    tech_files = {
        "package.json":     ("Node/JS", "backend"),
        "pyproject.toml":   ("Python",  "backend"),
        "pubspec.yaml":     ("Flutter", "mobile"),
        "go.mod":           ("Go",      "backend"),
        "Cargo.toml":       ("Rust",    "backend"),
        "build.gradle":     ("Java/Kotlin", "backend"),
        "Dockerfile":       ("Docker",  "infra"),
        "docker-compose.yml": ("Docker Compose", "infra"),
        "terraform.tf":     ("Terraform", "infra"),
        "k8s":              ("Kubernetes", "infra"),
        ".github":          ("GitHub Actions", "ci_cd"),
    }
    for fname, (label, cat) in tech_files.items():
        p = root / fname
        if p.exists() and label.lower() not in seen:
            seen.add(label.lower())
            components.append({"name": label, "category": cat, "description": ""})

    return components


def read_claude_md(root: Path) -> str:
    """Read CLAUDE.md from project root."""
    for fname in ["CLAUDE.md", "claude.md", "CLAUDE.MD", ".claude/CLAUDE.md"]:
        p = root / fname
        if p.exists():
            return p.read_text(encoding="utf-8", errors="ignore")
    return ""


def read_file(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return ""


# ---------------------------------------------------------------------------
# Group into layers
# ---------------------------------------------------------------------------

LAYER_ORDER = [
    "frontend", "mobile", "auth",
    "backend", "ai_ml", "queue",
    "database", "storage",
    "cloud", "infra",
    "monitoring", "ci_cd",
    "other",
]


def group_into_layers(components: list[dict]) -> list[dict]:
    """Group components by category into display layers."""
    groups = {}
    for comp in components:
        cat = comp["category"]
        if cat not in groups:
            groups[cat] = []
        groups[cat].append(comp["name"])

    layers = []
    for cat in LAYER_ORDER:
        if cat in groups:
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
# Infer connections between layers
# ---------------------------------------------------------------------------

COMMON_CONNECTIONS = [
    ("frontend", "backend"),
    ("mobile",   "backend"),
    ("backend",  "database"),
    ("backend",  "auth"),
    ("backend",  "queue"),
    ("backend",  "storage"),
    ("backend",  "ai_ml"),
    ("backend",  "cloud"),
    ("queue",    "backend"),
    ("backend",  "monitoring"),
    ("ci_cd",    "infra"),
    ("infra",    "cloud"),
]


def infer_connections(layers: list[dict]) -> list[dict]:
    present = {l["category"] for l in layers}
    connections = []
    for src, dst in COMMON_CONNECTIONS:
        if src in present and dst in present:
            connections.append({"from": src, "to": dst, "label": ""})
    return connections


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
    components = []

    if root:
        # 1. Read CLAUDE.md
        claude_md = read_claude_md(root)
        if claude_md:
            components += extract_components_from_text(claude_md)

        # 2. Scan directories
        components += scan_project_dirs(root)

        # 3. Check for README / architecture docs
        for doc in ["README.md", "docs/architecture.md", "docs/ARCHITECTURE.md",
                    "architecture.md", "ARCHITECTURE.md"]:
            doc_path = root / doc
            if doc_path.exists():
                components += extract_components_from_text(read_file(doc_path))

    # 4. Extra text provided directly
    if extra_text:
        components += extract_components_from_text(extra_text)

    # Deduplicate: remove shorter names that are substrings of longer names
    # e.g. "Flutter" is dropped if "Flutter mobile" already exists
    names_lower = [c["name"].lower() for c in components]
    seen = set()
    unique = []
    for i, c in enumerate(components):
        key = c["name"].lower()
        # Skip if this is a pure substring of another component already collected
        is_redundant = any(
            key != names_lower[j] and key in names_lower[j]
            for j in range(len(components))
            if j != i
        )
        if key not in seen and not is_redundant:
            seen.add(key)
            unique.append(c)
    components = unique

    layers = group_into_layers(components)
    connections = infer_connections(layers)

    return {
        "title": title or (f"{root.name} Architecture" if root else "System Architecture"),
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
    parser.add_argument("--root",   help="Project root directory")
    parser.add_argument("--text",   help="Free-form text describing the architecture")
    parser.add_argument("--file",   help="Path to a specific file (CLAUDE.md, README, etc.)")
    parser.add_argument("--title",  help="Diagram title override")
    parser.add_argument("--subtitle", help="Diagram subtitle override")
    parser.add_argument("--author", help="Author name for LinkedIn footer")
    parser.add_argument("--cta",    help="LinkedIn call-to-action text")
    parser.add_argument("--output", default="arch.json", help="Output JSON file path")
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
    print(f"✅ Architecture JSON → {out.resolve()}")
    print(f"   Detected {len(result['layers'])} layers, {sum(len(l['items']) for l in result['layers'])} components")
    for layer in result["layers"]:
        print(f"   [{layer['label']}] {', '.join(layer['items'])}")
