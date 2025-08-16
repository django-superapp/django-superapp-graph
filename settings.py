def extend_superapp_settings(main_settings):
    main_settings['INSTALLED_APPS'] += [
        'superapp.apps.graph',
        'django_neomodel',
    ]
    
    # Neo4j configuration
    main_settings['NEOMODEL_NEO4J_BOLT_URL'] = main_settings.get(
        'NEO4J_BOLT_URL', 
        'bolt://neo4j:neo4j@localhost:7687'
    )
