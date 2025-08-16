"""
Example relationship definitions for the graph app.

This module demonstrates various relationship types with properties.
"""

import logging
from datetime import datetime
from neomodel import (
    StructuredRel, StringProperty, IntegerProperty, 
    DateTimeProperty, BooleanProperty, FloatProperty
)

logger = logging.getLogger(__name__)


class BaseRelationship(StructuredRel):
    """Base relationship with common properties."""
    
    created_at = DateTimeProperty(default_now=True)
    updated_at = DateTimeProperty(default_now=True)
    created_by = StringProperty()
    
    def save(self):
        """Override save to update timestamp."""
        self.updated_at = datetime.now()
        super().save()


class KnowsRelationship(BaseRelationship):
    """Relationship between people who know each other."""
    
    since = DateTimeProperty()
    relationship_type = StringProperty(
        choices=['friend', 'colleague', 'family', 'acquaintance'],
        default='acquaintance'
    )
    strength = IntegerProperty(default=1)  # 1-10 scale
    
    def __str__(self):
        return f"Knows({self.relationship_type}, strength={self.strength})"


class WorksForRelationship(BaseRelationship):
    """Relationship between person and organization."""
    
    position = StringProperty(max_length=100)
    department = StringProperty(max_length=100)
    salary = FloatProperty()
    start_date = DateTimeProperty()
    end_date = DateTimeProperty()
    is_current = BooleanProperty(default=True)
    
    def __str__(self):
        return f"WorksFor({self.position})"


class PartnersWithRelationship(BaseRelationship):
    """Partnership relationship between organizations."""
    
    partnership_type = StringProperty(
        choices=['strategic', 'technical', 'financial', 'vendor'],
        default='strategic'
    )
    contract_value = FloatProperty()
    start_date = DateTimeProperty()
    end_date = DateTimeProperty()
    is_active = BooleanProperty(default=True)
    
    def __str__(self):
        return f"PartnersWith({self.partnership_type})"


class AssignedToRelationship(BaseRelationship):
    """Assignment relationship between person and project."""
    
    role = StringProperty(max_length=100)
    allocation_percentage = IntegerProperty(default=100)  # 0-100
    start_date = DateTimeProperty()
    end_date = DateTimeProperty()
    is_lead = BooleanProperty(default=False)
    
    def __str__(self):
        return f"AssignedTo({self.role}, {self.allocation_percentage}%)"


class DependsOnRelationship(BaseRelationship):
    """Dependency relationship between projects."""
    
    dependency_type = StringProperty(
        choices=['blocking', 'related', 'prerequisite'],
        default='related'
    )
    criticality = IntegerProperty(default=1)  # 1-5 scale
    description = StringProperty()
    
    def __str__(self):
        return f"DependsOn({self.dependency_type})"