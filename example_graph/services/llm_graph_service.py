"""
LLM-powered graph node creation service.

This service demonstrates how to use LiteLLM to intelligently create 
and populate graph nodes with AI-generated content.
"""

import json
import logging
from typing import Dict, List, Any, Optional, Union
from decimal import Decimal

from django.conf import settings

logger = logging.getLogger(__name__)


class LLMGraphService:
    """Service for creating graph nodes using LLM intelligence."""
    
    def __init__(self):
        self.litellm_service = None
        self._initialize_litellm()
    
    def _initialize_litellm(self):
        """Initialize LiteLLM service if available."""
        try:
            # Try to import the litellm service
            from superapp.apps.litellm.services.litellm_service import get_litellm_service
            self.litellm_service = get_litellm_service()
            logger.info("LiteLLM service initialized for graph node creation")
        except ImportError:
            logger.warning("LiteLLM service not available. LLM features will be disabled.")
            self.litellm_service = None
    
    def create_person_from_description(self, user, description: str, **additional_properties) -> Dict[str, Any]:
        """
        Create a Person node using LLM to extract structured data from description.
        
        Args:
            user: Django user for LiteLLM tracking
            description: Natural language description of the person
            **additional_properties: Any additional properties to set
            
        Returns:
            Dict containing the extracted person data
        """
        if not self.litellm_service:
            raise ValueError("LiteLLM service not available")
        
        system_prompt = """
        You are an expert at extracting structured data about people from natural language descriptions.
        
        Given a description of a person, extract the following information in JSON format:
        {
            "name": "Full name of the person",
            "email": "Email address if mentioned, otherwise null",
            "age": "Age if mentioned, otherwise null",
            "is_active": true,
            "additional_info": {
                "occupation": "Job/occupation if mentioned",
                "location": "Location/city if mentioned",
                "interests": ["list", "of", "interests", "if", "mentioned"],
                "skills": ["list", "of", "skills", "if", "mentioned"]
            }
        }
        
        Only include fields that are explicitly mentioned or can be reasonably inferred.
        Use null for missing information. Keep names properly capitalized.
        """
        
        user_prompt = f"Extract person information from this description:\n\n{description}"
        
        try:
            response = self.litellm_service.completion(
                user=user,
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.1,
                max_tokens=500
            )
            
            # Extract and parse the response
            content = response['choices'][0]['message']['content']
            person_data = json.loads(content)
            
            # Add any additional properties
            person_data.update(additional_properties)
            
            logger.info(f"Created person data from LLM: {person_data['name']}")
            return person_data
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response as JSON: {e}")
            raise ValueError("LLM returned invalid JSON response")
        except Exception as e:
            logger.error(f"Error creating person from description: {e}")
            raise
    
    def create_organization_from_description(self, user, description: str, **additional_properties) -> Dict[str, Any]:
        """
        Create an Organization node using LLM to extract structured data.
        
        Args:
            user: Django user for LiteLLM tracking
            description: Natural language description of the organization
            **additional_properties: Any additional properties to set
            
        Returns:
            Dict containing the extracted organization data
        """
        if not self.litellm_service:
            raise ValueError("LiteLLM service not available")
        
        system_prompt = """
        You are an expert at extracting structured data about organizations/companies from natural language descriptions.
        
        Given a description of an organization, extract the following information in JSON format:
        {
            "name": "Official name of the organization",
            "description": "Brief description of what they do",
            "industry": "Industry/sector they operate in",
            "employee_count": "Number of employees if mentioned, otherwise null",
            "website": "Website URL if mentioned, otherwise null",
            "additional_info": {
                "founded": "Founding year if mentioned",
                "headquarters": "Location of headquarters if mentioned",
                "specialties": ["list", "of", "specialties", "if", "mentioned"],
                "products": ["list", "of", "products", "if", "mentioned"]
            }
        }
        
        Only include fields that are explicitly mentioned or can be reasonably inferred.
        Use null for missing information. Keep names properly formatted.
        """
        
        user_prompt = f"Extract organization information from this description:\n\n{description}"
        
        try:
            response = self.litellm_service.completion(
                user=user,
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.1,
                max_tokens=500
            )
            
            content = response['choices'][0]['message']['content']
            org_data = json.loads(content)
            
            # Add any additional properties
            org_data.update(additional_properties)
            
            logger.info(f"Created organization data from LLM: {org_data['name']}")
            return org_data
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response as JSON: {e}")
            raise ValueError("LLM returned invalid JSON response")
        except Exception as e:
            logger.error(f"Error creating organization from description: {e}")
            raise
    
    def suggest_relationships(self, user, node1_data: Dict, node2_data: Dict, context: str = "") -> List[Dict[str, Any]]:
        """
        Use LLM to suggest possible relationships between two nodes.
        
        Args:
            user: Django user for LiteLLM tracking
            node1_data: Data for the first node
            node2_data: Data for the second node
            context: Additional context about the relationship
            
        Returns:
            List of suggested relationships with confidence scores
        """
        if not self.litellm_service:
            raise ValueError("LiteLLM service not available")
        
        system_prompt = """
        You are an expert at analyzing relationships between people and organizations.
        
        Given information about two entities, suggest possible relationships between them.
        Return your analysis in JSON format:
        {
            "relationships": [
                {
                    "type": "relationship_type",
                    "direction": "node1_to_node2" or "node2_to_node1" or "bidirectional",
                    "confidence": 0.8,
                    "properties": {
                        "key": "value"
                    },
                    "reasoning": "Why you think this relationship exists"
                }
            ]
        }
        
        Possible relationship types include:
        - WORKS_FOR (person to organization)
        - KNOWS (person to person)
        - PARTNERS_WITH (organization to organization)
        - LOCATED_IN (any to location)
        - ASSIGNED_TO (person to project)
        - OWNS (person/org to project/asset)
        
        Confidence should be between 0.0 and 1.0.
        Only suggest relationships you can reasonably infer from the data.
        """
        
        user_prompt = f"""
        Analyze the relationship between these two entities:
        
        Entity 1: {json.dumps(node1_data, indent=2)}
        Entity 2: {json.dumps(node2_data, indent=2)}
        
        Additional context: {context}
        
        What relationships might exist between them?
        """
        
        try:
            response = self.litellm_service.completion(
                user=user,
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,
                max_tokens=800
            )
            
            content = response['choices'][0]['message']['content']
            relationship_data = json.loads(content)
            
            logger.info(f"Generated {len(relationship_data['relationships'])} relationship suggestions")
            return relationship_data['relationships']
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response as JSON: {e}")
            raise ValueError("LLM returned invalid JSON response")
        except Exception as e:
            logger.error(f"Error suggesting relationships: {e}")
            raise
    
    def enrich_node_data(self, user, node_data: Dict, node_type: str) -> Dict[str, Any]:
        """
        Use LLM to enrich existing node data with additional relevant information.
        
        Args:
            user: Django user for LiteLLM tracking
            node_data: Existing node data
            node_type: Type of node (Person, Organization, etc.)
            
        Returns:
            Enriched node data
        """
        if not self.litellm_service:
            raise ValueError("LiteLLM service not available")
        
        system_prompt = f"""
        You are an expert at enriching {node_type} data with relevant additional information.
        
        Given existing data about a {node_type}, suggest additional properties and tags that would be relevant.
        Return your suggestions in JSON format:
        {{
            "suggested_properties": {{
                "property_name": "suggested_value"
            }},
            "suggested_tags": ["tag1", "tag2", "tag3"],
            "confidence_score": 0.8,
            "reasoning": "Explanation of your suggestions"
        }}
        
        Base your suggestions on common patterns and logical inferences from the existing data.
        Only suggest information that would typically be associated with this type of entity.
        """
        
        user_prompt = f"""
        Enrich this {node_type} data with relevant additional information:
        
        {json.dumps(node_data, indent=2)}
        
        What additional properties and tags would be relevant for this {node_type}?
        """
        
        try:
            response = self.litellm_service.completion(
                user=user,
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.4,
                max_tokens=600
            )
            
            content = response['choices'][0]['message']['content']
            enrichment_data = json.loads(content)
            
            # Merge suggested properties with existing data
            enriched_data = node_data.copy()
            enriched_data.update(enrichment_data.get('suggested_properties', {}))
            
            # Add tags if not already present
            if 'tags' not in enriched_data:
                enriched_data['tags'] = enrichment_data.get('suggested_tags', [])
            
            # Add enrichment metadata
            enriched_data['_enrichment'] = {
                'confidence': enrichment_data.get('confidence_score', 0.0),
                'reasoning': enrichment_data.get('reasoning', ''),
                'enriched_at': str(timezone.now()) if 'timezone' in globals() else None
            }
            
            logger.info(f"Enriched {node_type} data with {len(enrichment_data.get('suggested_properties', {}))} properties")
            return enriched_data
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response as JSON: {e}")
            raise ValueError("LLM returned invalid JSON response")
        except Exception as e:
            logger.error(f"Error enriching node data: {e}")
            raise


# Service instance
_llm_graph_service = None


def get_llm_graph_service() -> LLMGraphService:
    """Get the singleton LLM graph service instance."""
    global _llm_graph_service
    if _llm_graph_service is None:
        _llm_graph_service = LLMGraphService()
    return _llm_graph_service