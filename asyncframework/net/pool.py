# -*- coding:utf-8 -*-
from typing import Union, Optional, List, TypeVar, Generic, Any
from asyncio import Task, sleep, CancelledError
from abc import ABCMeta, abstractmethod
from ..log.log import get_logger


__all__ = ['StaticPool']


_DEFAULT_TIMEOUT_CREATION = [0.5, 0.75, 1, 1.5, 2, 3, 5, 8, 10, 15, 30, 60]

T = TypeVar('T')


class StaticPool(Generic[T], metaclass=ABCMeta):
    """Static pool class
    The next element is fetched consequently and created lazily.
    The same element might be returned several times.
    """
    log = get_logger('StaticPool')
    acquire_repeat_cnt: Optional[int] = None
    timeout_creation: Union[float, List[float]] = _DEFAULT_TIMEOUT_CREATION
    queue: List[Any]

    def __init__(self, pool_size: int = 1):
        """Constructor

        Args:
            pool_size (int, optional): the pool size. Defaults to 1.

        Raises:
            ValueError: if pool size is less or equal to zero
        """
        if pool_size <= 0:
            raise ValueError('Pool size must be positive non-0')
        self.queue = [None] * pool_size
        self.index = 0

    async def stop(self):
        """Stop the pool completely"""
        for elem in self.queue:
            if elem is None:
                continue
            elif isinstance(elem, Task):
                elem.cancel()
                await elem
            else:
                await self.destroy(elem)

    async def acquire(self, *args, **kwargs) -> Optional[T]:
        """Acquire next element from pool

        Returns:
            Optional[T]: element or None if creation was cancelled
        """
        idx, self.index = self.index, self.index + 1
        self.index %= len(self.queue)
        elem = self.queue[idx]
        if not elem:
            elem = await self._create(*args, **kwargs)
            self.queue[idx] = elem
        return elem

    async def _create(self, *args, **kwargs) -> Optional[T]:
        elem = None
        curr_attempt = 1
        while not elem:
            try:
                elem = await self.create(*args, **kwargs)
            except CancelledError as e:
                self.log.warning(f'Cancelled')
                return None
            except Exception as e:
                self.log.error(f'Error creating pool element {e}')
                if self.acquire_repeat_cnt is not None and curr_attempt >= self.acquire_repeat_cnt:
                    raise e
                tm: float
                if isinstance(self.timeout_creation, list):
                    idx = curr_attempt - 1 if len(self.timeout_creation) > curr_attempt else -1
                    tm = self.timeout_creation[idx]
                else:
                    tm = self.timeout_creation
                curr_attempt += 1

                self.log.warning(f'Waiting for {tm} seconds to next ({curr_attempt}) try.')
                await sleep(tm)
            else:
                if self.check(elem):
                    return elem

    @abstractmethod
    async def create(self, *args, **kwargs) -> T:
        """Abstract method for creating the next element.
        Method should be implemented in child
        
        Returns:
            T: the next created element
        """
        pass

    def check(self, elem: T) -> bool:
        """Check if element created correctly.
        Might be reimplemented in child

        Args:
            elem (T): the created element

        Returns:
            bool: True if ok
        """
        return bool(elem)

    async def destroy(self, elem: T) -> None:
        """Destroy element callback

        Args:
            elem (T): the element need to be destroyed
        """
        pass
