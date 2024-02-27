from abc import ABC, abstractmethod
from typing import Dict

from insurance.domains.policy.model import Policy


class GetSavePolicyPayloadStrategyABC(ABC):

    @abstractmethod
    async def get_save_policy_payload(self, policy: Policy) -> Dict:
        pass
