"""
Graph models discovery utility for Django SuperApp.

This module provides functionality to dynamically discover and import 
graph models from all apps in the SuperApp ecosystem.
"""

import importlib
import logging
import os
from pathlib import Path
from typing import Dict, List, Any

from django.apps import apps
from django.conf import settings

logger = logging.getLogger(__name__)


class GraphModelDiscovery:
    """Discovers and imports graph models from all SuperApp apps."""
    
    def __init__(self):
        self.discovered_models = {}
        self.discovered_relationships = {}
        
    def discover_graph_models(self) -> Dict[str, Any]:
        """
        Dynamically discover and import graph models from all apps.
        
        Returns:
            Dict containing discovered models organized by app name
        """
        logger.debug("Starting graph models discovery")
        discovered = {}
        
        # Get all installed apps
        for app_config in apps.get_app_configs():
            app_name = app_config.name
            
            # Only process SuperApp apps
            if 'superapp.apps.' in app_name:
                logger.debug(f"Checking app: {app_name}")
                models = self._discover_app_graph_models(app_config)
                if models:
                    discovered[app_name] = models
                    
        self.discovered_models = discovered
        logger.info(f"Discovered graph models in {len(discovered)} apps")
        return discovered
    
    def _discover_app_graph_models(self, app_config) -> Dict[str, Any]:
        """
        Discover graph models in a specific app.
        
        Args:
            app_config: Django app configuration
            
        Returns:
            Dict of discovered models for this app
        """
        app_models = {}
        app_path = Path(app_config.path)
        graph_path = app_path / 'graph'
        
        # Check if app has a graph folder
        if not graph_path.exists():
            logger.debug(f"No graph folder found in {app_config.name}")
            return app_models
            
        # Look for Python files in the graph folder
        for py_file in graph_path.glob('*.py'):
            if py_file.name.startswith('__'):
                continue
                
            module_name = py_file.stem
            try:
                # Import the module
                full_module_path = f"{app_config.name}.graph.{module_name}"
                module = importlib.import_module(full_module_path)
                
                # Extract neomodel classes
                models = self._extract_neomodel_classes(module)
                if models:
                    app_models[module_name] = models
                    logger.debug(f"Found {len(models)} graph models in {full_module_path}")
                    
            except ImportError as e:
                logger.warning(f"Failed to import {full_module_path}: {e}")
            except Exception as e:
                logger.error(f"Error processing {full_module_path}: {e}")
                
        return app_models
    
    def _extract_neomodel_classes(self, module) -> Dict[str, Any]:
        """
        Extract neomodel classes from a module.
        
        Args:
            module: The imported Python module
            
        Returns:
            Dict of neomodel classes found in the module
        """
        models = {}
        
        for attr_name in dir(module):
            attr = getattr(module, attr_name)
            
            # Check if it's a neomodel class
            if (hasattr(attr, '__bases__') and 
                any('neomodel' in str(base) for base in attr.__bases__)):
                models[attr_name] = attr
                logger.debug(f"Found neomodel class: {attr_name}")
                
        return models
    
    def get_all_models(self) -> Dict[str, Any]:
        """Get all discovered models."""
        return self.discovered_models
    
    def get_models_by_app(self, app_name: str) -> Dict[str, Any]:
        """Get models for a specific app."""
        return self.discovered_models.get(app_name, {})
    
    def register_models(self):
        """Register all discovered models with the graph system."""
        for app_name, app_models in self.discovered_models.items():
            for module_name, models in app_models.items():
                for model_name, model_class in models.items():
                    logger.info(f"Registered graph model: {app_name}.{module_name}.{model_name}")


# Global instance
graph_discovery = GraphModelDiscovery()


def discover_and_register_graph_models():
    """
    Convenience function to discover and register all graph models.
    Call this in your Django app's ready() method.
    """
    graph_discovery.discover_graph_models()
    graph_discovery.register_models()


def get_graph_models() -> Dict[str, Any]:
    """Get all discovered graph models."""
    return graph_discovery.get_all_models()