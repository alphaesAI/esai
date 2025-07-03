import os

try:
    import pandas as pd

    PANDAS = True
except ImportError:
    PANDAS = False

class Tabular:
    def __init__(self, idcolumn=None, textcolumns=None, content=False):
        if not PANDAS:
            raise ImportError("install pandas")
        
        self.idcolumn = idcolumn
        self.textcolumns = textcolumns
        self.content = content

    def process(self, df):
        rows = []
        columns = self.textcolumns
        
        if not columns:
            columns = list(df.columns)
            if self.idcolumn:
                columns.remove(self.idcolumn)
            
        for index, row in df.iterrows():
            uid = row[self.idcolumn] if self.idcolumn else index
            uid = uid if uid is not None else index
            text = self.concat(row, columns)

    
    def concat(self, row, columns):
        pass