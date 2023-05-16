import logging
import os
import typing

from flask import Flask
from flask import request

class A:
    def __init__(self):
        self.c = 5
    
    def set_c(self, c):
        self.c = c
    
    def copy(self, new_obj=None):
        if new_obj is None:
            new_obj = A()

        new_obj.set_c(self.c)
        return new_obj 

class B(A):
    def __init__(self):
        super().__init__()
    
    def copy(self):
        new_b = B()
        new_b = super().copy(new_b)
        return new_b


b_1 = B()
b_1.set_c(10)
b_2 = b_1.copy()
print(b_2.c)
print(type(b_2))

a_1 = A()
a_1.set_c(10)
a_2 = a_1.copy()
print(a_2.c)
print(type(a_2))