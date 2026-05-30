from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel

class JurisdictionNode(BaseModel):
    id: UUID
    name: str
    type: str
    parent_id: Optional[UUID] = None
    code: Optional[str] = None

class JurisdictionHierarchy:
    def __init__(self):
        self._nodes: dict[UUID, JurisdictionNode] = {}
        self._children: dict[UUID, List[UUID]] = {}
        
    def add_node(self, node: JurisdictionNode):
        self._nodes[node.id] = node
        if node.parent_id:
            if node.parent_id not in self._children:
                self._children[node.parent_id] = []
            self._children[node.parent_id].append(node.id)
            
    def get_node(self, node_id: UUID) -> Optional[JurisdictionNode]:
        return self._nodes.get(node_id)
        
    def get_chain(self, node_id: UUID) -> List[JurisdictionNode]:
        """Returns the chain of jurisdictions from the given node up to National level."""
        chain = []
        current = self.get_node(node_id)
        while current:
            chain.append(current)
            if not current.parent_id:
                break
            current = self.get_node(current.parent_id)
        return chain
