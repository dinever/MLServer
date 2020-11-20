import asyncio

from typing import List
from itertools import chain

from .model import MLModel
from .errors import ModelNotFound
from .types import RepositoryIndexResponse


class SingleModelRegistry:
    """
    Registry for a single model with multiple versions.
    """

    def __init__(self, model: MLModel):
        self._versions = {}
        self._name = model.name

        self._register(model)

    async def index(self) -> RepositoryIndexResponse:
        pass

    async def load(self, model: MLModel):
        await model.load()
        self._register(model)

    async def get_model(self, version: str = None) -> MLModel:
        if version:
            if version not in self._versions:
                raise ModelNotFound(self._name, version)

            return self._versions[version]

        return self._default

    async def get_models(self) -> List[MLModel]:
        models = self._versions.values()

        # Add default if not versioned
        if not self._default.version:
            models.append(self._default)

        return models

    def _register(self, model: MLModel):
        if model.version:
            self._versions[model.version] = model

        # TODO: Support version policies
        self._default = model


class MultiModelRegistry:
    """
    Multiple model registry, where each model can have multiple versions.
    """

    def __init__(self):
        self._models = {}

    async def load(self, model: MLModel):
        if model.name not in self._models:
            self._models[model.name] = SingleModelRegistry(model)

        await self._models[model.name].load(model)

    async def unload(self, name: str):
        if name not in self._models:
            raise ModelNotFound(name)

        del self._models[name]

    async def get_model(self, name: str, version: str = None) -> MLModel:
        if name not in self._models:
            raise ModelNotFound(name, version)

        model = await self._models[name].get_model(version)
        return model

    async def get_models(self) -> List[MLModel]:
        models_list = await asyncio.gather(
            *[model.get_models() for model in self._models.values()]
        )

        return chain.from_iterable(models_list)
