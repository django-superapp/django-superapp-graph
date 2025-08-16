# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Django SuperApp Graph application that provides Neo4j graph database integration with intelligent node creation using LLM services. The project demonstrates advanced graph modeling, relationship management, and AI-powered content generation within the Django SuperApp framework architecture.

## Key Principles
- Prioritize readability, maintainability, and Django best practices (PEP 8 compliance)
- Modular structure: organize code using Django apps within SuperApp for clear separation and reuse
- Leverage built-in Django features; avoid raw SQL, prefer Django ORM
- Follow strict MVT (Model-View-Template) separation

## Django SuperApp Architecture

### Framework Overview
- Uses a modular architecture where apps extend main SuperApp functionality
- Each app includes independent `settings.py` and `urls.py` automatically integrated by the SuperApp system
- Quickly bootstrap projects using pre-built standalone apps
- Settings are extended via `extend_superapp_settings()` in `settings.py`
- URLs are extended via `extend_superapp_urlpatterns()` and `extend_superapp_admin_urlpatterns()` in `urls.py`

### File Organization Structure
```
superapp/apps/<app_name>/
├── admin/<model_name_slug>.py      # Admin configurations
├── models/<model_name_slug>.py     # Django models
├── views/<view_name>.py            # View functions/classes
├── services/<service_name>.py      # Business logic services
├── signals/<model_name_slug>.py    # Django signals
├── tasks/<task_name>.py            # Celery tasks
├── requirements.txt                # App-specific dependencies
├── settings.py                     # App settings extension
├── urls.py                         # URL patterns extension
└── apps.py                         # Django app configuration
```

Each folder should have an `__init__.py` file to make them packages or to export `__all__` - keep it updated.

## Development Commands

### Backend Commands
- Use `docker-compose exec -ti web python manage.py <command>` to execute Django commands
- Don't launch Python servers on port 8080 (reserved) - use another port or `make web-logs`
- Use `.env.local.example` and `.env.example` for environment variables

## Settings Integration

### App Settings Pattern
`superapp/apps/<app_name>/settings.py`
```python
from django.utils.translation import gettext_lazy as _
from django.urls import reverse_lazy

def extend_superapp_settings(main_settings):
    main_settings['INSTALLED_APPS'] += ['superapp.apps.sample_app']
    
    # Add admin navigation
    main_settings['UNFOLD']['SIDEBAR']['navigation'] = [
        {
            "title": _("Sample App"),
            "icon": "extension",
            "items": [
                {
                    "title": lambda request: _("Sample Models"),
                    "icon": "table_rows",
                    "link": reverse_lazy("admin:sample_app_samplemodel_changelist"),
                    "permission": lambda request: request.user.has_perm("sample_app.view_samplemodel"),
                },
            ]
        },
    ]
```

### URL Integration Pattern
`superapp/apps/<app_name>/urls.py`
```python
from django.urls import path
from superapp.apps.sample_app.views import hello_world

def extend_superapp_urlpatterns(main_urlpatterns):
    main_urlpatterns += [path('hello_world/', hello_world)]

def extend_superapp_admin_urlpatterns(main_admin_urlpatterns):
    main_urlpatterns += [path('hello_world/', hello_world)]
```

## Admin Integration with django-unfold

### Critical Requirements
**IMPORTANT**: When using Django SuperApp with Unfold admin, you MUST:
- Use `from unfold.decorators import action` instead of `@admin.action` for admin actions
- Use `from unfold.decorators import display` instead of `@admin.display` for display methods
- The `attrs` parameter is crucial for action buttons styling and functionality
- Unfold expects additional attributes (`attrs`, `icon`, `variant`) that Django's decorators don't provide

### Admin File Structure
`superapp/apps/<app_name>/admin/<model_name_slug>.py`
```python
from unfold.decorators import action, display
from superapp.apps.admin_portal.admin import SuperAppModelAdmin
from superapp.apps.admin_portal.sites import superapp_admin_site
from django.contrib import admin

@admin.register(SampleModel, site=superapp_admin_site)
class SampleModelAdmin(SuperAppModelAdmin):
    list_display = ['slug', 'name', 'created_at', 'updated_at']  # First column shouldn't be FK
    search_fields = ['name__slug', 'slug']
    autocomplete_fields = ['foreign_key_field']  # Prefer for FK/M2M fields
    list_filter = ('created_at', 'updated_at')
    list_per_page = 20
    ordering = ('-created_at',)
```

### Admin Best Practices
- Register using `superapp_admin_site` from `superapp.apps.admin_portal.sites`
- Use `SuperAppModelAdmin` based on `unfold.admin.ModelAdmin`
- Prefer `autocomplete_fields` for `ForeignKey` and `ManyToManyField`
- First column in `list_display` should NOT be a foreign key - use a field that opens the model detail

## Django Development Guidelines

### Views and Logic
- Use CBVs (Class-Based Views) for complex logic, FBVs (Function-Based Views) for simple tasks
- Keep business logic in models/forms; views should handle requests/responses only
- Utilize built-in authentication and forms/models validation
- Implement middleware strategically for authentication, logging, caching

### Models and Database
- All models should include `created_at` and `updated_at` timestamp fields
- Use Django ORM; avoid raw SQL
- Optimize queries with `select_related` and `prefetch_related`
- Do NOT update migrations in the `migrations` folder unless there are exceptions or issues

### Services Pattern
- Business logic should live in `superapp/apps/<app_name>/services/<service_name>.py`
- Try to have just two operations: upsert and delete in services
- Keep services focused and reusable

### Error Handling and Signals
- Use built-in error handling mechanisms; customize error pages
- Leverage signals for decoupled logging/error handling
- Signals should live in `superapp/apps/<app_name>/signals/<model_name_slug>.py`

## Frontend Development
- Implement components with dark mode support
- All components should be mobile responsive
- Keep files small and reuse code components
- Organize components correctly and group them logically

## Dependencies and Performance
- Django, Django REST Framework (APIs)
- Celery (background tasks), Redis (caching/task queues)
- PostgreSQL/MySQL (production databases)
- django-unfold (admin UI)
- Use caching framework (Redis/Memcached)
- Apply async views/background tasks (Celery)
- Enforce Django security best practices (CSRF, XSS, SQL injection protections)

## Translation and Internationalization
- Every user-facing string must use `_('XXX')` from Django translation
- Import: `from django.utils.translation import gettext_lazy as _`

## Development Setup

Bootstrap this app into an existing Django SuperApp project:

```bash
cd my_superapp
cd superapp/apps
django_superapp bootstrap-app \
    --template-repo https://github.com/django-superapp/django-superapp-sample-app ./sample_app
cd ../../
```

## Graph App Features

### Core Capabilities
- **Neo4j Integration**: Full neomodel integration for graph database operations
- **Dynamic Model Discovery**: Automatically discovers graph models from all SuperApp apps
- **LLM-Powered Node Creation**: Uses LiteLLM service to intelligently create nodes from natural language
- **Advanced Search**: Comprehensive graph search and traversal capabilities
- **Relationship Management**: Rich relationship modeling with custom properties

### Graph Model Structure
- **Nodes**: Person, Organization, Location, Project, Tag
- **Relationships**: Custom relationship classes with properties
- **Dynamic Discovery**: Automatically imports graph models from `graph/` folders in all apps

### Services
- **LLMGraphService**: AI-powered node creation and relationship suggestion
- **GraphSearchService**: Advanced search, traversal, and analytics
- **GraphModelDiscovery**: Dynamic model discovery and registration

### Usage Examples
```python
# Create nodes using LLM
from superapp.apps.graph.example_graph.services.llm_graph_service import get_llm_graph_service
llm_service = get_llm_graph_service()
person_data = llm_service.create_person_from_description(user, "John is a 30-year-old developer")

# Search the graph
from superapp.apps.graph.example_graph.services.graph_search_service import get_graph_search_service
search_service = get_graph_search_service()
results = search_service.search_nodes_by_text("developer")

# Create your own views
# Add views in views.py and extend URL patterns in urls.py
```

## Template Project
This is a Copier template project based on `copier.yml` and Jinja template files. The actual implementation is generated from this template.