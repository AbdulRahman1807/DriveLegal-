from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
from backend.models.jurisdiction import Jurisdiction
from backend.jurisdiction.hierarchy import JurisdictionHierarchy, JurisdictionNode

class JurisdictionResolver:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.hierarchy = JurisdictionHierarchy()
        self._is_loaded = False
        
    async def load_hierarchy(self):
        if self._is_loaded:
            return
            
        stmt = select(Jurisdiction)
        result = await self.session.execute(stmt)
        jurisdictions = result.scalars().all()
        
        for j in jurisdictions:
            node = JurisdictionNode(
                id=j.id,
                name=j.name,
                type=j.type,
                parent_id=j.parent_id,
                code=j.code
            )
            self.hierarchy.add_node(node)
            
        self._is_loaded = True
        
    async def resolve_by_id(self, jurisdiction_id: UUID) -> list[JurisdictionNode]:
        await self.load_hierarchy()
        return self.hierarchy.get_chain(jurisdiction_id)

    async def resolve_by_name(self, name: str) -> list[JurisdictionNode]:
        await self.load_hierarchy()
        # Find the node matching the name
        for node in self.hierarchy._nodes.values():
            if node.name.lower() == name.lower() or (node.code and node.code.lower() == name.lower()):
                return self.hierarchy.get_chain(node.id)
        return []
