"""
Nós para Behavior Trees: Selector, Sequence, Action, Condition.
"""
from typing import List, Callable
from .behavior_tree import BehaviorNode, NodeStatus


class Selector(BehaviorNode):
    """Selector: Executa filhos até um retornar SUCCESS."""
    
    def __init__(self, name: str, children: List[BehaviorNode]):
        super().__init__(name)
        self.children = children
    
    def tick(self, context: dict) -> NodeStatus:
        """Executa filhos em ordem até sucesso."""
        for child in self.children:
            status = child.tick(context)
            
            if status == NodeStatus.SUCCESS:
                return NodeStatus.SUCCESS
            elif status == NodeStatus.RUNNING:
                return NodeStatus.RUNNING
        
        return NodeStatus.FAILURE


class Sequence(BehaviorNode):
    """Sequence: Executa filhos até um retornar FAILURE."""
    
    def __init__(self, name: str, children: List[BehaviorNode]):
        super().__init__(name)
        self.children = children
    
    def tick(self, context: dict) -> NodeStatus:
        """Executa filhos em ordem até falha."""
        for child in self.children:
            status = child.tick(context)
            
            if status == NodeStatus.FAILURE:
                return NodeStatus.FAILURE
            elif status == NodeStatus.RUNNING:
                return NodeStatus.RUNNING
        
        return NodeStatus.SUCCESS


class Action(BehaviorNode):
    """Action: Executa uma ação."""
    
    def __init__(self, name: str, action: Callable):
        super().__init__(name)
        self.action = action
    
    def tick(self, context: dict) -> NodeStatus:
        """Executa ação."""
        try:
            result = self.action(context)
            
            if result is True:
                return NodeStatus.SUCCESS
            elif result is False:
                return NodeStatus.FAILURE
            else:
                return NodeStatus.RUNNING
        except Exception as e:
            self._log.error(f"Erro em action '{self.name}': {e}")
            return NodeStatus.FAILURE


class Condition(BehaviorNode):
    """Condition: Verifica uma condição."""
    
    def __init__(self, name: str, condition: Callable):
        super().__init__(name)
        self.condition = condition
    
    def tick(self, context: dict) -> NodeStatus:
        """Verifica condição."""
        try:
            result = self.condition(context)
            return NodeStatus.SUCCESS if result else NodeStatus.FAILURE
        except Exception as e:
            self._log.error(f"Erro em condition '{self.name}': {e}")
            return NodeStatus.FAILURE


class Inverter(BehaviorNode):
    """Inverter: Inverte resultado do filho."""
    
    def __init__(self, name: str, child: BehaviorNode):
        super().__init__(name)
        self.child = child
    
    def tick(self, context: dict) -> NodeStatus:
        """Inverte resultado."""
        status = self.child.tick(context)
        
        if status == NodeStatus.SUCCESS:
            return NodeStatus.FAILURE
        elif status == NodeStatus.FAILURE:
            return NodeStatus.SUCCESS
        else:
            return status


class Repeater(BehaviorNode):
    """Repeater: Repete filho N vezes."""
    
    def __init__(self, name: str, child: BehaviorNode, times: int = -1):
        super().__init__(name)
        self.child = child
        self.times = times  # -1 = infinito
        self.count = 0
    
    def tick(self, context: dict) -> NodeStatus:
        """Repete execução."""
        if self.times > 0 and self.count >= self.times:
            self.count = 0
            return NodeStatus.SUCCESS
        
        status = self.child.tick(context)
        
        if status == NodeStatus.SUCCESS or status == NodeStatus.FAILURE:
            self.count += 1
        
        if self.times == -1:
            return NodeStatus.RUNNING
        
        return status if self.count < self.times else NodeStatus.SUCCESS
