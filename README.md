# Django SuperApp - Graph App

Django SuperApp with Neo4j integration and LLM-powered node creation.

## Installation

```bash
cd my_superapp/superapp/apps
django_superapp bootstrap-app \
    --template-repo https://github.com/django-superapp/django-superapp-graph-app ./graph
```

## Neo4j Setup

Incorporate the Neo4j service from `docker-compose.yml` into your SuperApp's docker-compose:

```bash
docker-compose up -d neo4j
```

Access Neo4j browser at http://localhost:7474 (neo4j/neo4j)

## Creating Graph Models

Add a `graph/` folder in any SuperApp app:

```python
# superapp/apps/your_app/graph/models.py
from neomodel import StructuredNode, StringProperty, RelationshipTo

class Person(StructuredNode):
    name = StringProperty(required=True)
    knows = RelationshipTo('Person', 'KNOWS')
```

Models are auto-discovered and registered by the graph app. See `example_graph/` for complete examples.

For detailed documentation, visit [https://django-superapp.bringes.io](https://django-superapp.bringes.io).
