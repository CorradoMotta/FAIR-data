from PySide6.QtCore import (QAbstractListModel, QByteArray, QModelIndex, Qt,Slot)
from PySide6.QtQml import QmlElement
import os
from os import path
from os.path import dirname, abspath
import configparser
import sys
sys.path.append(dirname(dirname(abspath(__file__))))
# To interact with the database
from fairdata import metadataDB

# To be used on the @QmlElement decorator
# (QML_IMPORT_MINOR_VERSION is optional)
QML_IMPORT_NAME = "BaseModel"
QML_IMPORT_MAJOR_VERSION = 1

@QmlElement
class BaseModel(QAbstractListModel):

    # create my roles
    nameRole = Qt.UserRole + 1
    acddNameRole = Qt.UserRole + 2
    valueRole = Qt.UserRole + 3
    defaultValueRole = Qt.UserRole + 4
    levelRole = Qt.UserRole + 5
    autoRole = Qt.UserRole + 6
    descriptionRole = Qt.UserRole + 7

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.metadata_list = self.populateFromDb()

    # return the number of rows
    def rowCount(self, parent=QModelIndex()):
        return len(self.metadata_list)

    # If your model is used within QML and requires roles other than the default ones 
    # provided by the roleNames() function, you must override it.
    def roleNames(self):
        default = super().roleNames()
        default[self.nameRole] = QByteArray(b"name")
        default[self.acddNameRole] = QByteArray(b"acdd_name")
        default[self.valueRole] = QByteArray(b"value")
        default[self.defaultValueRole] = QByteArray(b"defaultValue")
        default[self.levelRole] = QByteArray(b"isMandatory")
        default[self.autoRole] = QByteArray(b"isAuto")
        default[self.descriptionRole] = QByteArray(b"description")
        return default

    # function to retrieve items from the list.
    def data(self, index, role: int):

        if not self.metadata_list:
            ret = None
        elif not index.isValid():
            ret = None
        elif role == self.nameRole:
            ret = self.metadata_list[index.row()]["name"]
        elif role == self.acddNameRole:
            ret = self.metadata_list[index.row()]["acdd_name"]
        elif role == self.valueRole:
            ret = self.metadata_list[index.row()]["value"]
        elif role == self.defaultValueRole:
            ret = self.metadata_list[index.row()]["defaultValue"]
        elif role == self.levelRole:
            ret = self.metadata_list[index.row()]["isMandatory"]
        elif role == self.autoRole:
            ret = self.metadata_list[index.row()]["isAuto"]
        elif role == self.descriptionRole:
            ret = self.metadata_list[index.row()]["description"]

        else:
            ret = None
        return ret

    def setData(self, index, value, role):

        if not index.isValid():
            return False
        if role == self.valueRole:
            self.metadata_list[index.row()]["value"] = value
        return True
    
    def populateFromDb(self):
        
        metadata_list = []
        # Opening JSON file
        global_db = metadataDB.metadataDB('../database/global_metadata.json')
        for key, value in global_db.getAll().items():
            if(not value["auto"]):
                metadata_list.append({"name": value["name"], 
                                      "acdd_name": value["ACDD"], 
                                      "value": "", 
                                      "defaultValue": value["default"],
                                      "isMandatory": value["required"],
                                      "isAuto": value["auto"], 
                                      "description": value["description"]})
        return metadata_list
                
    @Slot()
    def reset(self):
        self.beginResetModel()
        self.metadata_list = self.populateFromDb()  # should work without calling it ?
        self.endResetModel()
        return True

    @Slot()
    def default(self):
        for idx, data in enumerate(self.metadata_list):
            self.metadata_list[idx]["value"] = data["defaultValue"]
            self.dataChanged.emit(self.index(idx,0),self.index(idx,0), [self.valueRole])

    @Slot()
    def generateINI(self):

        config = configparser.ConfigParser()
        config.read('FILE.INI')
        config.add_section('mandatory_global_attributes')
        config.add_section('optional_global_attributes')
        for idx, data in enumerate(self.metadata_list):
            if(data["value"]):
                if(data["isMandatory"]):
                    config['mandatory_global_attributes'][data["acdd_name"]] = data["value"]   # create
                else:
                    config['optional_global_attributes'][data["acdd_name"]] = data["value"]

        with open('FILE.INI', 'w') as configfile:    # save
            config.write(configfile)
