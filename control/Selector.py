import torch

class Selector:
    def select(self, items:torch.Tensor) -> torch.Tensor:
        pass

class PrioritySelector:
    def __init__(self, priority_list):
        self.priority_list=torch.arange(0,len(priority_list))[priority_list].int()

    def select(self, items: torch.Tensor) -> torch.Tensor:
        i_pri = self.priority_list[items[:,4].int()] #类别->优先级
        idx = i_pri.argmax()
        return items[idx,:]

class ConfSelector:
    def select(self, items: torch.Tensor) -> torch.Tensor:
        idx = items[:,5].argmax()
        return items[idx,:]