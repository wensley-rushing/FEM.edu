import numpy as np

class Record():
    """
    container class for recording time history data
    """

    def __init__(self):
        self.data  = []
        self.key   = ''
        self.label = ''

    def __str__(self):
        if len(self.data) > 3:
            s = "{}:{}:{}".format(self.label,self.key,self.data[:3])
        else:
            s = "{}:{}:{}".format(self.label,self.key,self.data)
        return s

    def __len__(self):
        """
        :return: the length of the collected data array
        """
        return len(self.data)

    def isKey(self, key):
        return (key and key == self.key)

    def getData(self):
        """
        :return: tuple (label, data.asarray())
        """
        return (self.label, np.array(self.data))
