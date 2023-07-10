from copy import deepcopy
import tkinter as tk
from typing import Callable


class StateList:
    """
    Master Class of program's state/transaction for Undo/Redo functionality
    """
    def __init__(self, top, callback, fields, ):
        self.top = top
        self.trackedFieldS = fields
        self.callback = callback
        self.transactionS:list = [self.getState()]
        self.iTransaction = 0
        self.currentState = self.getState()

        self.top.bind("<Control-z>", self._undo_redo_event)
        self.top.bind("<Control-Z>", self._undo_redo_event)

    def append(self, transaction: 'ProgramState'):
        """
        Called when an undoable operation is done
        """
        if self.iTransaction < len(self.transactionS) - 1:
            self.transactionS = self.transactionS[:self.iTransaction+1]

        transaction.refresh(self.currentState)
        self.transactionS.append(transaction)
        self.currentState = transaction
        self.iTransaction = len(self.transactionS) - 1

    def undo(self):
        if self.iTransaction > 0:
            self.iTransaction -= 1
            self.currentState = self.transactionS[self.iTransaction]
            self.setState(self.currentState)

    def redo(self):
        if self.iTransaction < len(self.transactionS) - 1:
            self.iTransaction += 1
            self.currentState = self.transactionS[self.iTransaction]
            self.setState(self.currentState)

    def getState(self)->'ProgramState':
        return ProgramState(*self.trackedFieldS)

    def setState(self, state:'ProgramState'):
        for o in Observer.observerS:
            o.unregister()
        state.set()

        for o in Observer.observerS:
            o.register()
        self.callback()

    def _undo_redo_event(self, event):
        SHIFT_KEY = 1
        CAPS_LOCK = 2
        CONTROL_KEY = 4
        NUM_LOCK = 8
        SCROLL_LOCK = 16

        if event.keysym == "z" and event.state & ~(CAPS_LOCK | NUM_LOCK | SCROLL_LOCK) == CONTROL_KEY:
            self.undo()
        if event.keysym == "Z" and event.state & ~(CAPS_LOCK | NUM_LOCK | SCROLL_LOCK) == CONTROL_KEY | SHIFT_KEY:
            self.redo()


class ProgramState:
    """
    Describes a new program state
    """
    def __init__(self, *args):
        self.dict = {VarState(arg).name if VarState(arg).name else VarState(arg).id: VarState(arg) for arg in args}

    def __getitem__(self, item):
        return self.dict[item]

    def __setitem__(self, key, value):
        self.dict[key] = value

    def __delitem__(self, key):
        del self.dict[key]

    def __contains__(self, item):
        return item in self.dict

    def set(self):
        for vs in self.dict.values():
            vs.set()

    def refresh(self, other: 'ProgramState'):
        for k in self.dict:
            if k in other and self.dict[k] == other[k]:
                self.dict[k] = other[k]


class VarState:
    """
    Describes a variable that is saved between transactions
    """
    def __init__(self, var):
        self.var = var
        self.id = id(var)

        if isinstance(var, tk.StringVar):
            self.name = var._name
            self.value = var.get()
        elif isinstance(var, list):
            self.name = None
            self.value = deepcopy(var)

    def set(self):
        if isinstance(self.var, tk.StringVar):
            self.var.set(self.value)
        elif isinstance(self.var, list):
            self.var.clear()
            self.var.extend(self.value)

    def __eq__(self, other:'VarState')->bool:
        return self.value == other.value

    def __repr__(self):
        return ": ".join((self.name if self.name else str(self.id), self.value.__repr__(),))


class Observer:
    observerS = []

    def __init__(self, variable, callback: Callable, mode:str= "w"):
        self.callback = callback
        self.variable = variable
        self.mode = mode
        self.observerS.append(self)
        self.register()

    def register(self):
        self.observer = self.variable.trace(self.mode, self.callback)

    def unregister(self):
        self.variable.trace_vdelete(self.mode, self.observer)
