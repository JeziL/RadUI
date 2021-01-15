import pandas as pd
from PyQt5.QtCore import *


class PandasModel(QAbstractTableModel):
    def __init__(self, df=pd.DataFrame, parent=None):
        QAbstractTableModel.__init__(self, parent=parent)
        self._df = df

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role != Qt.DisplayRole:
            return QVariant()

        if orientation == Qt.Horizontal:
            try:
                return self._df.columns.tolist()[section]
            except (IndexError, ):
                return QVariant()
        elif orientation == Qt.Vertical:
            try:
                return self._df.index.tolist()[section]
            except (IndexError, ):
                return QVariant()

    def data(self, index, role=Qt.DisplayRole):
        if role != Qt.DisplayRole:
            return QVariant()

        if not index.isValid():
            return QVariant()

        return QVariant(str(self._df.iloc[index.row(), index.column()]))

    def rowCount(self, parent=QModelIndex(), *args, **kwargs):
        return len(self._df.index)

    def columnCount(self, parent=QModelIndex(), *args, **kwargs):
        return len(self._df.columns)
