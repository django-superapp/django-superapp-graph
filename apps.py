from django.apps import AppConfig

class GraphAppConfig(AppConfig):
    name = 'superapp.apps.graph'
    default = True
    verbose_name = 'Graph App'
    
    def ready(self):
        """Called when the app is ready. Discover graph models."""
        try:
            from .utils.graph_discovery import discover_and_register_graph_models
            discover_and_register_graph_models()
        except ImportError:
            # Handle case where neomodel is not installed
            pass

