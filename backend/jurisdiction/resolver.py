from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
from backend.models.jurisdiction import Jurisdiction
from backend.jurisdiction.hierarchy import JurisdictionHierarchy, JurisdictionNode
from backend.core.cache import cache_service
from backend.config import settings
import json

class JurisdictionResolver:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.hierarchy = JurisdictionHierarchy()
        self._is_loaded = False
        
    async def load_hierarchy(self):
        if self._is_loaded:
            return
            
        cache_key = "drivelegal:jurisdictions:all"
        cached_data = await cache_service.get(cache_key)
        
        if cached_data:
            for item in cached_data:
                node = JurisdictionNode(**item)
                self.hierarchy.add_node(node)
            self._is_loaded = True
            return

        stmt = select(Jurisdiction)
        result = await self.session.execute(stmt)
        jurisdictions = result.scalars().all()
        
        cache_payload = []
        for j in jurisdictions:
            node = JurisdictionNode(
                id=j.id,
                name=j.name,
                type=j.type,
                parent_id=j.parent_id,
                code=j.code
            )
            self.hierarchy.add_node(node)
            # Serialize for cache
            cache_payload.append({
                "id": str(node.id),
                "name": node.name,
                "type": node.type,
                "parent_id": str(node.parent_id) if node.parent_id else None,
                "code": node.code
            })
            
        # Store in cache
        await cache_service.set(cache_key, cache_payload, ttl=settings.CACHE_TTL_LONG)
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
