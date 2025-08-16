"""
Example neomodel node definitions for the graph app.

This module demonstrates various node types and their properties.
"""

import logging
from datetime import datetime
from neomodel import (
    StructuredNode, StringProperty, IntegerProperty, 
    DateTimeProperty, BooleanProperty, FloatProperty,
    UniqueIdProperty, RelationshipTo, RelationshipFrom,
    Relationship
)
from .relationships import (
    KnowsRelationship, WorksForRelationship, PartnersWithRelationship,
    AssignedToRelationship, DependsOnRelationship
)

logger = logging.getLogger(__name__)


class BaseNode(StructuredNode):
    """Base node with common properties."""
    
    uid = UniqueIdProperty()
    created_at = DateTimeProperty(default_now=True)
    updated_at = DateTimeProperty(default_now=True)
    
    class Meta:
        abstract = True
    
    def save(self):
        """Override save to update timestamp."""
        self.updated_at = datetime.now()
        super().save()


class Person(BaseNode):
    """Represents a person in the system."""
    
    name = StringProperty(required=True, max_length=100)
    email = StringProperty(unique_index=True, max_length=255)
    age = IntegerProperty()
    is_active = BooleanProperty(default=True)
    
    # Relationships
    knows = RelationshipTo('Person', 'KNOWS', model=KnowsRelationship)
    works_for = RelationshipTo('Organization', 'WORKS_FOR', model=WorksForRelationship)
    lives_in = RelationshipTo('Location', 'LIVES_IN')
    
    def __str__(self):
        return f"Person({self.name})"


class Organization(BaseNode):
    """Represents an organization or company."""
    
    name = StringProperty(required=True, max_length=200)
    description = StringProperty()
    industry = StringProperty(max_length=100)
    employee_count = IntegerProperty()
    website = StringProperty(max_length=255)
    
    # Relationships
    employees = RelationshipFrom('Person', 'WORKS_FOR', model=WorksForRelationship)
    located_in = RelationshipTo('Location', 'LOCATED_IN')
    partners_with = RelationshipTo('Organization', 'PARTNERS_WITH', model=PartnersWithRelationship)
    
    def __str__(self):
        return f"Organization({self.name})"


class Location(BaseNode):
    """Represents a geographical location."""
    
    name = StringProperty(required=True, max_length=100)
    country = StringProperty(max_length=100)
    city = StringProperty(max_length=100)
    latitude = FloatProperty()
    longitude = FloatProperty()
    
    # Relationships
    residents = RelationshipFrom('Person', 'LIVES_IN')
    organizations = RelationshipFrom('Organization', 'LOCATED_IN')
    
    def __str__(self):
        return f"Location({self.name})"


class Project(BaseNode):
    """Represents a project or initiative."""
    
    name = StringProperty(required=True, max_length=200)
    description = StringProperty()
    status = StringProperty(
        choices=['planning', 'active', 'completed', 'cancelled'],
        default='planning'
    )
    budget = FloatProperty()
    start_date = DateTimeProperty()
    end_date = DateTimeProperty()
    
    # Relationships
    owned_by = RelationshipTo('Organization', 'OWNED_BY')
    assigned_to = RelationshipFrom('Person', 'ASSIGNED_TO', model=AssignedToRelationship)
    depends_on = RelationshipTo('Project', 'DEPENDS_ON', model=DependsOnRelationship)
    
    def __str__(self):
        return f"Project({self.name})"


class Tag(BaseNode):
    """Represents a tag or category."""
    
    name = StringProperty(required=True, unique_index=True, max_length=50)
    description = StringProperty()
    color = StringProperty(max_length=7)  # Hex color
    
    def __str__(self):
        return f"Tag({self.name})"