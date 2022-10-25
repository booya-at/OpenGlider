from openglider.gui.app.state.list import SelectionList
from openglider.utils.dataclass import dataclass
from typing import Any, List, TypeVar, Generic, Dict

ListType = TypeVar("ListType")
CacheListType = TypeVar("CacheListType")

@dataclass
class ChangeSet(Generic[ListType]):
    active: List[ListType]

    added: List[ListType]
    removed: List[ListType]


class Cache(Generic[ListType, CacheListType]):
    elements: SelectionList[ListType]
    cache: Dict[str, CacheListType]
    cache_hashes: Dict[str, int]
    cache_last_active: List[str]

    update_on_color_change = True
    update_on_name_change = True

    def __init__(self, elements: SelectionList[ListType]):
        self.elements = elements

        self.cache = {}
        self.cache_hashes = {}
        self.cache_last_active = []

    def clear(self):
        self.cache = {}
        self.cache_hashes = {}

    def get_object(self, element: str):
        """
        Get the cached object
        """
        raise NotImplementedError()
    
    def _get_object(self, element: str):
        hash_workload: List[Any] = [self.elements[element].element]
        if self.update_on_color_change:
            hash_workload += self.elements[element].color
        if self.update_on_name_change:
            hash_workload += self.elements[element].name

        obj_hash = hash(tuple(hash_workload))
        
        is_outdated = element not in self.cache_hashes or obj_hash != self.cache_hashes[element]

        if is_outdated:
            obj = self.get_object(element)
            self.cache[element] = obj
            self.cache_hashes[element] = obj_hash
        
        return self.cache[element], is_outdated

    
    def get_selected(self):
        return self._get_object(self.elements.selected_element)[0]
    
    def get_update(self) -> ChangeSet[CacheListType]:
        changeset: ChangeSet[CacheListType] = ChangeSet([],[],[])
        active_names = []
        
        for element_name, element in self.elements.elements.items():
            old_obj = self.cache.get(element_name)
            is_active = element.active or self.elements.selected_element == element_name

            if is_active:
                active_names.append(element_name)
                obj, outdated = self._get_object(element_name)

                changeset.active.append(obj)

                if outdated:
                    changeset.added.append(obj)
                    if old_obj is not None:
                        changeset.removed.append(old_obj)
                elif element_name not in self.cache_last_active:
                    changeset.added.append(obj)
            
            else:
                if element_name in self.cache_last_active and old_obj is not None:
                    changeset.removed.append(old_obj)
        
        existing_names = list(self.elements.elements.keys())
        cached_names = list(self.cache)

        for name in cached_names:
            if name not in existing_names:
                elem = self.cache.pop(name)
                changeset.removed.append(elem)
                self.cache_hashes.pop(name)
        
        self.cache_last_active = active_names

        return changeset            
