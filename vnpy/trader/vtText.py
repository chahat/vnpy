# encoding: UTF-8

from vnpy.trader.language import text

# Add a constant definition to vtText.py Local dictionary
d = locals()
for name in dir(text):
    if '__' not in name:
        d[name] = text.__getattribute__(name)
