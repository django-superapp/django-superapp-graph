"""
Graph search service for Neo4j-based graph database operations.

This service provides comprehensive search capabilities across the graph,
including traversal queries, pattern matching, and aggregation operations.
"""

import logging
from typing import Dict, List, Any, Optional, Union, Tuple
from decimal import Decimal

from neomodel import db, StructuredNode
from neomodel.exceptions import UniqueProperty, RequiredProperty

logger = logging.getLogger(__name__)


class GraphSearchService:
    """Service for searching and querying the Neo4j graph database."""
    
    def __init__(self):
        self.node_cache = {}
        
    def search_nodes_by_type(self, node_type: str, filters: Optional[Dict] = None, limit: int = 100) -> List[Dict]:
        """
        Search for nodes of a specific type with optional filters.
        
        Args:
            node_type: The node label/type to search for
            filters: Dictionary of property filters
            limit: Maximum number of results to return
            
        Returns:
            List of nodes matching the criteria
        """
        filters = filters or {}
        
        # Build WHERE clause
        where_conditions = []
        params = {'limit': limit}
        
        for key, value in filters.items():
            param_name = f"filter_{key}"
            where_conditions.append(f"n.{key} = ${param_name}")
            params[param_name] = value
        
        where_clause = f"WHERE {' AND '.join(where_conditions)}" if where_conditions else ""
        
        query = f"""
        MATCH (n:{node_type})
        {where_clause}
        RETURN n
        LIMIT $limit
        """
        
        try:
            results, meta = db.cypher_query(query, params)
            nodes = []
            
            for row in results:
                node = row[0]
                node_dict = dict(node)
                node_dict['_id'] = node.id
                node_dict['_labels'] = list(node.labels)
                nodes.append(node_dict)
            
            logger.debug(f"Found {len(nodes)} nodes of type {node_type}")
            return nodes
            
        except Exception as e:
            logger.error(f"Error searching nodes by type {node_type}: {e}")
            raise
    
    def search_nodes_by_text(self, search_text: str, node_types: Optional[List[str]] = None, 
                           properties: Optional[List[str]] = None, limit: int = 50) -> List[Dict]:
        """
        Full-text search across node properties.
        
        Args:
            search_text: Text to search for
            node_types: List of node types to search in (optional)
            properties: List of properties to search in (optional)
            limit: Maximum number of results to return
            
        Returns:
            List of nodes matching the search text
        """
        node_types = node_types or []
        properties = properties or ['name', 'description', 'title']
        
        # Build node type filter
        if node_types:
            type_filter = ":" + ":".join(node_types)
        else:
            type_filter = ""
        
        # Build text search conditions
        search_conditions = []
        params = {'search_text': f"(?i).*{search_text}.*", 'limit': limit}
        
        for prop in properties:
            search_conditions.append(f"n.{prop} =~ $search_text")
        
        search_clause = " OR ".join(search_conditions)
        
        query = f"""
        MATCH (n{type_filter})
        WHERE {search_clause}
        RETURN n, 
               CASE 
                 WHEN n.name =~ $search_text THEN 10
                 WHEN n.description =~ $search_text THEN 5
                 ELSE 1
               END as relevance_score
        ORDER BY relevance_score DESC
        LIMIT $limit
        """
        
        try:
            results, meta = db.cypher_query(query, params)
            nodes = []
            
            for row in results:
                node = row[0]
                relevance_score = row[1]
                
                node_dict = dict(node)
                node_dict['_id'] = node.id
                node_dict['_labels'] = list(node.labels)
                node_dict['_relevance_score'] = relevance_score
                nodes.append(node_dict)
            
            logger.debug(f"Found {len(nodes)} nodes matching text '{search_text}'")
            return nodes
            
        except Exception as e:
            logger.error(f"Error in text search for '{search_text}': {e}")
            raise
    
    def find_shortest_path(self, start_node_id: int, end_node_id: int, 
                          max_depth: int = 6, relationship_types: Optional[List[str]] = None) -> Optional[Dict]:
        """
        Find the shortest path between two nodes.
        
        Args:
            start_node_id: ID of the starting node
            end_node_id: ID of the ending node
            max_depth: Maximum depth to search
            relationship_types: List of relationship types to consider
            
        Returns:
            Dictionary containing path information or None if no path found
        """
        # Build relationship type filter
        if relationship_types:
            rel_filter = "|".join(relationship_types)
            rel_clause = f"[r:{rel_filter}*1..{max_depth}]"
        else:
            rel_clause = f"[r*1..{max_depth}]"
        
        query = f"""
        MATCH path = shortestPath((start)-{rel_clause}-(end))
        WHERE id(start) = $start_id AND id(end) = $end_id
        RETURN path, length(path) as path_length
        """
        
        params = {
            'start_id': start_node_id,
            'end_id': end_node_id
        }
        
        try:
            results, meta = db.cypher_query(query, params)
            
            if not results:
                logger.debug(f"No path found between nodes {start_node_id} and {end_node_id}")
                return None
            
            path = results[0][0]
            path_length = results[0][1]
            
            # Extract nodes and relationships from path
            path_nodes = []
            path_relationships = []
            
            for i, node in enumerate(path.nodes):
                node_dict = dict(node)
                node_dict['_id'] = node.id
                node_dict['_labels'] = list(node.labels)
                path_nodes.append(node_dict)
            
            for relationship in path.relationships:
                rel_dict = dict(relationship)
                rel_dict['_id'] = relationship.id
                rel_dict['_type'] = relationship.type
                rel_dict['_start_node'] = relationship.start_node.id
                rel_dict['_end_node'] = relationship.end_node.id
                path_relationships.append(rel_dict)
            
            result = {
                'path_length': path_length,
                'nodes': path_nodes,
                'relationships': path_relationships
            }
            
            logger.debug(f"Found path of length {path_length} between nodes {start_node_id} and {end_node_id}")
            return result
            
        except Exception as e:
            logger.error(f"Error finding shortest path: {e}")
            raise
    
    def find_neighbors(self, node_id: int, depth: int = 1, 
                      relationship_types: Optional[List[str]] = None,
                      direction: str = 'both') -> Dict:
        """
        Find all neighbors of a node within a given depth.
        
        Args:
            node_id: ID of the central node
            depth: Depth of traversal (1 = direct neighbors, 2 = neighbors of neighbors, etc.)
            relationship_types: List of relationship types to follow
            direction: 'incoming', 'outgoing', or 'both'
            
        Returns:
            Dictionary containing neighbors organized by depth
        """
        # Build relationship direction
        if direction == 'incoming':
            rel_direction = '<-'
            rel_end = '-'
        elif direction == 'outgoing':
            rel_direction = '-'
            rel_end = '->'
        else:  # both
            rel_direction = '-'
            rel_end = '-'
        
        # Build relationship type filter
        if relationship_types:
            rel_types = "|".join(relationship_types)
            rel_pattern = f"{rel_direction}[r:{rel_types}*1..{depth}]{rel_end}"
        else:
            rel_pattern = f"{rel_direction}[r*1..{depth}]{rel_end}"
        
        query = f"""
        MATCH path = (center){rel_pattern}(neighbor)
        WHERE id(center) = $node_id
        RETURN neighbor, length(path) as distance, r
        ORDER BY distance, neighbor.name
        """
        
        params = {'node_id': node_id}
        
        try:
            results, meta = db.cypher_query(query, params)
            
            neighbors_by_depth = {}
            
            for row in results:
                neighbor = row[0]
                distance = row[1]
                relationships = row[2] if row[2] else []
                
                if distance not in neighbors_by_depth:
                    neighbors_by_depth[distance] = []
                
                neighbor_dict = dict(neighbor)
                neighbor_dict['_id'] = neighbor.id
                neighbor_dict['_labels'] = list(neighbor.labels)
                neighbor_dict['_distance'] = distance
                
                neighbors_by_depth[distance].append(neighbor_dict)
            
            logger.debug(f"Found neighbors at {len(neighbors_by_depth)} depth levels for node {node_id}")
            return neighbors_by_depth
            
        except Exception as e:
            logger.error(f"Error finding neighbors for node {node_id}: {e}")
            raise
    
    def get_node_statistics(self, node_id: int) -> Dict:
        """
        Get comprehensive statistics about a node.
        
        Args:
            node_id: ID of the node to analyze
            
        Returns:
            Dictionary containing various statistics about the node
        """
        query = """
        MATCH (n)
        WHERE id(n) = $node_id
        OPTIONAL MATCH (n)-[r_out]->()
        OPTIONAL MATCH (n)<-[r_in]-()
        RETURN n,
               count(DISTINCT r_out) as outgoing_relationships,
               count(DISTINCT r_in) as incoming_relationships,
               count(DISTINCT type(r_out)) as outgoing_relationship_types,
               count(DISTINCT type(r_in)) as incoming_relationship_types,
               collect(DISTINCT type(r_out)) as outgoing_types,
               collect(DISTINCT type(r_in)) as incoming_types
        """
        
        params = {'node_id': node_id}
        
        try:
            results, meta = db.cypher_query(query, params)
            
            if not results:
                raise ValueError(f"Node with ID {node_id} not found")
            
            row = results[0]
            node = row[0]
            
            node_dict = dict(node)
            node_dict['_id'] = node.id
            node_dict['_labels'] = list(node.labels)
            
            statistics = {
                'node': node_dict,
                'outgoing_relationships': row[1],
                'incoming_relationships': row[2],
                'outgoing_relationship_types': row[3],
                'incoming_relationship_types': row[4],
                'outgoing_types': [t for t in row[5] if t],
                'incoming_types': [t for t in row[6] if t],
                'total_relationships': row[1] + row[2]
            }
            
            logger.debug(f"Generated statistics for node {node_id}")
            return statistics
            
        except Exception as e:
            logger.error(f"Error getting statistics for node {node_id}: {e}")
            raise
    
    def aggregate_by_relationship(self, relationship_type: str, 
                                aggregation: str = 'count') -> List[Dict]:
        """
        Aggregate data across relationships of a specific type.
        
        Args:
            relationship_type: Type of relationship to aggregate
            aggregation: Type of aggregation ('count', 'avg', 'sum', 'min', 'max')
            
        Returns:
            List of aggregation results
        """
        if aggregation not in ['count', 'avg', 'sum', 'min', 'max']:
            raise ValueError(f"Unsupported aggregation type: {aggregation}")
        
        query = f"""
        MATCH (start)-[r:{relationship_type}]->(end)
        RETURN start, end, count(r) as relationship_count
        ORDER BY relationship_count DESC
        LIMIT 100
        """
        
        try:
            results, meta = db.cypher_query(query)
            
            aggregations = []
            for row in results:
                start_node = row[0]
                end_node = row[1]
                count = row[2]
                
                start_dict = dict(start_node)
                start_dict['_id'] = start_node.id
                start_dict['_labels'] = list(start_node.labels)
                
                end_dict = dict(end_node)
                end_dict['_id'] = end_node.id
                end_dict['_labels'] = list(end_node.labels)
                
                aggregations.append({
                    'start_node': start_dict,
                    'end_node': end_dict,
                    'relationship_count': count
                })
            
            logger.debug(f"Generated {len(aggregations)} aggregations for {relationship_type}")
            return aggregations
            
        except Exception as e:
            logger.error(f"Error in aggregation for relationship {relationship_type}: {e}")
            raise
    
    def execute_custom_query(self, query: str, params: Optional[Dict] = None) -> Tuple[List, List]:
        """
        Execute a custom Cypher query.
        
        Args:
            query: Cypher query string
            params: Query parameters
            
        Returns:
            Tuple of (results, column_names)
        """
        params = params or {}
        
        try:
            results, meta = db.cypher_query(query, params)
            columns = meta.get('columns', []) if meta else []
            
            logger.debug(f"Executed custom query, returned {len(results)} rows")
            return results, columns
            
        except Exception as e:
            logger.error(f"Error executing custom query: {e}")
            raise


# Service instance
_graph_search_service = None


def get_graph_search_service() -> GraphSearchService:
    """Get the singleton graph search service instance."""
    global _graph_search_service
    if _graph_search_service is None:
        _graph_search_service = GraphSearchService()
    return _graph_search_service