from copy import deepcopy

import numpy as np
import os
import sys
import warnings

from .DrawElement import *
from ..recorder.Recorder import Recorder
from .Face2D import *
from .Face3D import *


class Element(DrawElement):
    r"""
    abstract class: representing a single generic element
    """

    COUNT = 0

    def __init__(self, nodes, material, label=None):
        r"""
        :param nodes: list of node pointers
        :param material: a :py:meth:`femedu.materials.Material` object
        """
        super(Element, self).__init__()

        self.ID = Element.COUNT # creates a unique ID for each element
        Element.COUNT += 1      # ensure the next call will create a unique ID as well

        self.label = label
        
        self.nodes    = nodes
        self.transforms = [ None for nd in self.nodes ]
        self.material = material
        self.dof_idx  = {}   # marked for removal

        self._requestDofs( tuple() )

        self.force    = 0.0
        self.Loads    = [ [] for i in range(len(nodes)) ]
        self.Forces   = []
        self.Kt       = []

        self.setRecorder(None)

        self.setLoadFactor(1.0)

    def __str__(self):
        if self.label:
            s = "{} ({}_{}): nodes ( ".format(self.label, self.__class__.__name__, self.ID)
        else:
            s = "{}_{}: nodes ( ".format(self.__class__.__name__, self.ID)
        for node in self.nodes:
            s += "{} ".format(node.getID())
        s += ")"
        s += "\n    material: {}".format(self.material.__class__.__name__)
        return s

    def __repr__(self):
        if self.label:
            fmt = "{}[{}](" + len(self.nodes)*"{}, " + "{})"
            ans = fmt.format(self.__class__.__name__, self.label,
                                    *[ node.getID() for node in self.nodes ],
                                    repr(self.material))
        else:
            fmt = "{}(" + len(self.nodes)*"{}, " + "{})"
            ans = fmt.format(self.__class__.__name__,
                                    *[ node.getID() for node in self.nodes ],
                                    repr(self.material))
        return ans

    def initialize(self, type=DrawElement.UNKNOWN, dofs=[] ):
        r"""
        :param type: define `DrawElement.TYPE` for plotting. See :py:meth:`femedu.elements.DrawElement` under **Inherited methods** for available options.
        :param dofs: list of dofs used by this element. Example: `["ux","uy"]` for 2d-displacements.
        """
        self.element_type = type

        if dofs:
            self._requestDofs(dofs)
        else:
            raise TypeError("mandatory list of dofs is missing for element {}".format(self))

        self.createFaces()

        nnodes = len(self.nodes)
        self.distributed_load = [ 0.0 for i in range(nnodes) ]

        self.reset_matrices()

    def reset_matrices(self):
        r"""
        (re-)initializes element stiffness matrix and element force
        """
        nnodes = len(self.nodes)
        ndofs  = len(self._dof_list)

        self.Forces   = [ np.zeros(ndofs) for k in range(len(self.nodes)) ]
        self.Kt       = [ [ np.zeros((ndofs,ndofs)) for k in range(nnodes) ] for m in range(nnodes) ]

        return (nnodes, ndofs)

    def resetLoads(self):
        r"""
        default implementation for resetting element loads.
        """
        for face in self.faces:
            face.setLoad(0.0, 0.0)

    def createFaces(self):

        self.faces = []

        if self.element_type == self.LINE:
            msg = "** WARNING ** {}.{} not implemented".format(self.__class__.__name__, sys._getframe().f_code.co_name)
            raise NotImplementedError(msg)

        elif self.element_type == self.CURVE :
            msg = "** WARNING ** {}.{} not implemented".format(self.__class__.__name__, sys._getframe().f_code.co_name)
            raise NotImplementedError(msg)

        elif self.element_type == self.TRIANGLE :
            nNds = len(self.nodes)
            if nNds == 3:
                self.faces.append(Face2D(f"{self.ID}.0", self.nodes[0],self.nodes[1]))
                self.faces.append(Face2D(f"{self.ID}.1", self.nodes[1],self.nodes[2]))
                self.faces.append(Face2D(f"{self.ID}.2", self.nodes[2],self.nodes[0]))
            elif nNds == 6:
                self.faces.append(Face2D(f"{self.ID}.0", self.nodes[0],self.nodes[3],self.nodes[1]))
                self.faces.append(Face2D(f"{self.ID}.1", self.nodes[1],self.nodes[4],self.nodes[2]))
                self.faces.append(Face2D(f"{self.ID}.2", self.nodes[2],self.nodes[5],self.nodes[0]))
            else:
                msg = "** WARNING ** {}.{} not implemented".format(self.__class__.__name__, sys._getframe().f_code.co_name)
                raise NotImplementedError(msg)

        elif self.element_type == self.TETRAHEDRON :
            nNds = len(self.nodes)
            if nNds == 4:
                self.faces.append(Face3D(f"{self.ID}.0", self.nodes[0],self.nodes[2],self.nodes[1]))
                self.faces.append(Face3D(f"{self.ID}.1", self.nodes[0],self.nodes[1],self.nodes[3]))
                self.faces.append(Face3D(f"{self.ID}.2", self.nodes[1],self.nodes[2],self.nodes[3]))
                self.faces.append(Face3D(f"{self.ID}.3", self.nodes[2],self.nodes[0],self.nodes[3]))
            elif nNds == 10 :
                self.faces.append(Face3D(f"{self.ID}.0", self.nodes[0],self.nodes[2],self.nodes[1],
                                                         self.nodes[6],self.nodes[5],self.nodes[4]))
                self.faces.append(Face3D(f"{self.ID}.1", self.nodes[0],self.nodes[1],self.nodes[3],
                                                         self.nodes[4],self.nodes[8],self.nodes[7]))
                self.faces.append(Face3D(f"{self.ID}.2", self.nodes[1],self.nodes[2],self.nodes[3],
                                                         self.nodes[5],self.nodes[9],self.nodes[8]))
                self.faces.append(Face3D(f"{self.ID}.3", self.nodes[2],self.nodes[0],self.nodes[3],
                                                         self.nodes[6],self.nodes[7],self.nodes[9]))
            else:
                msg = "** WARNING ** {}.{} not implemented".format(self.__class__.__name__, sys._getframe().f_code.co_name)
                raise NotImplementedError(msg)

        elif self.element_type == self.QUAD :
            nNds = len(self.nodes)
            if nNds == 4:
                self.faces.append(Face2D(f"{self.ID}.0", self.nodes[0],self.nodes[1]))
                self.faces.append(Face2D(f"{self.ID}.1", self.nodes[1],self.nodes[2]))
                self.faces.append(Face2D(f"{self.ID}.2", self.nodes[2],self.nodes[3]))
                self.faces.append(Face2D(f"{self.ID}.3", self.nodes[3],self.nodes[0]))
            elif nNds == 8 or nNds == 9 :
                self.faces.append(Face2D(f"{self.ID}.0", self.nodes[0],self.nodes[4],self.nodes[1]))
                self.faces.append(Face2D(f"{self.ID}.1", self.nodes[1],self.nodes[5],self.nodes[2]))
                self.faces.append(Face2D(f"{self.ID}.2", self.nodes[2],self.nodes[6],self.nodes[3]))
                self.faces.append(Face2D(f"{self.ID}.3", self.nodes[3],self.nodes[7],self.nodes[0]))
            else:
                msg = "** WARNING ** {}.{} not implemented".format(self.__class__.__name__, sys._getframe().f_code.co_name)
                raise NotImplementedError(msg)

        elif self.element_type == self.BRICK :
            nNds = len(self.nodes)
            if nNds == 8:
                self.faces.append(Face3D(f"{self.ID}.0", self.nodes[0],self.nodes[3],self.nodes[2],self.nodes[1]))
                self.faces.append(Face3D(f"{self.ID}.1", self.nodes[0],self.nodes[1],self.nodes[5],self.nodes[4]))
                self.faces.append(Face3D(f"{self.ID}.2", self.nodes[1],self.nodes[2],self.nodes[6],self.nodes[5]))
                self.faces.append(Face3D(f"{self.ID}.3", self.nodes[2],self.nodes[3],self.nodes[7],self.nodes[6]))
                self.faces.append(Face3D(f"{self.ID}.4", self.nodes[3],self.nodes[0],self.nodes[4],self.nodes[7]))
                self.faces.append(Face3D(f"{self.ID}.5", self.nodes[4],self.nodes[5],self.nodes[6],self.nodes[7]))
            elif nNds == 20 :
                self.faces.append(Face3D(f"{self.ID}.0", self.nodes[0],self.nodes[3],self.nodes[2],self.nodes[1],
                                                         self.nodes[11],self.nodes[10],self.nodes[9],self.nodes[8]))
                self.faces.append(Face3D(f"{self.ID}.1", self.nodes[0],self.nodes[1],self.nodes[5],self.nodes[4],
                                                         self.nodes[8],self.nodes[13],self.nodes[16],self.nodes[12]))
                self.faces.append(Face3D(f"{self.ID}.2", self.nodes[1],self.nodes[2],self.nodes[6],self.nodes[5],
                                                         self.nodes[9],self.nodes[14],self.nodes[17],self.nodes[13]))
                self.faces.append(Face3D(f"{self.ID}.3", self.nodes[2],self.nodes[3],self.nodes[7],self.nodes[6],
                                                         self.nodes[10],self.nodes[15],self.nodes[18],self.nodes[14]))
                self.faces.append(Face3D(f"{self.ID}.4", self.nodes[3],self.nodes[0],self.nodes[4],self.nodes[7],
                                                         self.nodes[11],self.nodes[12],self.nodes[19],self.nodes[15]))
                self.faces.append(Face3D(f"{self.ID}.5", self.nodes[4],self.nodes[5],self.nodes[6],self.nodes[7],
                                                         self.nodes[16],self.nodes[17],self.nodes[18],self.nodes[19]))
            elif nNds == 27 :
                self.faces.append(Face3D(f"{self.ID}.0", self.nodes[0],self.nodes[3],self.nodes[2],self.nodes[1],
                                            self.nodes[11],self.nodes[10],self.nodes[9],self.nodes[8],self.nodes[20]))
                self.faces.append(Face3D(f"{self.ID}.1", self.nodes[0],self.nodes[1],self.nodes[5],self.nodes[4],
                                            self.nodes[8],self.nodes[13],self.nodes[16],self.nodes[12],self.nodes[21]))
                self.faces.append(Face3D(f"{self.ID}.2", self.nodes[1],self.nodes[2],self.nodes[6],self.nodes[5],
                                            self.nodes[9],self.nodes[14],self.nodes[17],self.nodes[13],self.nodes[22]))
                self.faces.append(Face3D(f"{self.ID}.3", self.nodes[2],self.nodes[3],self.nodes[7],self.nodes[6],
                                            self.nodes[10],self.nodes[15],self.nodes[18],self.nodes[14],self.nodes[23]))
                self.faces.append(Face3D(f"{self.ID}.4", self.nodes[3],self.nodes[0],self.nodes[4],self.nodes[7],
                                            self.nodes[11],self.nodes[12],self.nodes[19],self.nodes[15],self.nodes[24]))
                self.faces.append(Face3D(f"{self.ID}.5", self.nodes[4],self.nodes[5],self.nodes[6],self.nodes[7],
                                            self.nodes[16],self.nodes[17],self.nodes[18],self.nodes[19],self.nodes[25]))
            else:
                msg = "** WARNING ** {}.{} not implemented".format(self.__class__.__name__, sys._getframe().f_code.co_name)
                raise NotImplementedError(msg)

        else:
            msg = "** WARNING ** {}.{} not implemented".format(self.__class__.__name__, sys._getframe().f_code.co_name)
            raise NotImplementedError(msg)

    def setSurfaceLoad(self, face_idx, pn, ps=0):
        r"""
        .. warning::

            This method needs to be implemented by every element that shall accept a surface load.

        :param face_ix: face index for the loaded face (integer starting at 0)
        :type face_idx: int
        :param pn: magnitude of distributed normal load per unit length. Tension on a surface is positive.
        :param ps: magnitude of distributed shear load per unit length. Positive shear rotates the element counter-clockwise.
        """
        msg = "** WARNING ** {}.{} not implemented".format(self.__class__.__name__, sys._getframe().f_code.co_name)
        raise NotImplementedError(msg)

    def addTransformation(self, T, local_nodes=[]):
        r"""
        Attach a transformation to any node of the element.

        If no **local_nodes** list is given or an empty list is handed to the function,
        the transformation, **T**, will be applied to all nodes in the element.

        A non-empty **local_nodes** list will apply the transformation to those local nodes listed in that list.
        Local nodes start at 0 and go to N-1, where N is the number of elements in this element.

        A transformation can be removed from a node by assigning :code:`T=None` as the transformation.
        """
        if local_nodes:
            for local_id in local_nodes:
                if local_id >= 0 and local_id < len(self.transforms):
                    T.registerClient(self)    # register this Element with the transformation
                    self.transforms[local_id] = T
        else:
            T.registerClient(self)            # register this Element with the transformation
            self.transforms = [ T for nd in self.nodes ]

    def getPos(self, node, **kwargs):
        r"""
        Use this function to get nodal displacements from inside your element implementation.

        This is a wrapper around the :py:meth:`Node.getPos(caller)` method that adds the caller information
        for the node.

        :param node: local node number for which displacements are requested.
        """
        return self.nodes[node].getPos(self, **kwargs)

    def getDisp(self, node, **kwargs):
        r"""
        Use this function to get nodal displacements from inside your element implementation.

        This is a wrapper around the :py:meth:`Node.getDisp(caller)` method that adds the caller information
        for the node.

        :param node: local node number for which displacements are requested.
        """
        return self.nodes[node].getDisp(caller=self, **kwargs)

    def getForce(self):
        r"""
        Request the internal force vector (stress driven force only; **no applied element loads**)

        :return:
        """
        self.updateState()

        # make sure forces are returned in each respective node's local coordinates
        forces = []
        for node, force in zip(self.nodes, self.Forces):
            forces.append(node.v2l(force, self))

        return forces

    def getLoad(self, apply_load_factor=False):
        r"""
        Requesting nodal forces generated by element loads, like

        * line loads on beams of frames
        * surface loads on plates or solids
        * body forces on solids.

        :param apply_load_factor: shall the global load factor be applied by the element.

        :return:  element load vector
        """
        #self.updateState()

        # .. applied element load (reference load)
        self.computeSurfaceLoads()

        if isinstance(self.Loads, (list,tuple,np.ndarray)):
            Loads = []
            for node, load in zip(self.nodes, self.Loads):
                if isinstance(load, np.ndarray):
                    Loads.append(node.v2l(load, self))
                else:
                    Loads.append(None)
            return Loads
        elif self.Loads:
            return self.Loads
        else:
            return [ None for k in self.nodes ]

    def computeSurfaceLoads(self):
        self.Loads = [ None for nd0 in self.nodes ]

    def getLabel(self):
        if self.label:
            return "{}".format(self.label)
        else:
            return self.getID()

    def getID(self):
        return "Elem_{}".format(self.ID)

    def getInternalForce(self, variable=''):
        msg = "** WARNING ** {}.{} not implemented".format(self.__class__.__name__, sys._getframe().f_code.co_name)
        #raise NotImplementedError(msg)
        warnings.warn(msg)
        return (None, None)

    def getStress(self):
        self.updateState()
        return None

    def mapGaussPoints(self, var):
        r"""
        Initiate mapping of Gauss-point values to nodes.
        This method is an internal method and should not be called by the user.
        Calling that method explicitly will cause faulty nodal values.

        :param var: variable code for a variable to be mapped from Gauss-points to nodes
        """
        msg = "** WARNING ** {}.{} not implemented".format(self.__class__.__name__, sys._getframe().f_code.co_name)
        #raise NotImplementedError(msg)
        warnings.warn(msg)

    def getStiffness(self):
        r"""
        :return: the current tangent stiffness matrix
        """
        self.updateState()

        KT = deepcopy(self.Kt)

        for i, ndI in enumerate(self.nodes):
            for j, ndJ in enumerate(self.nodes):
                #
                # this can be an expensive operation.
                # check if really needed and avoid identity operations:
                #
                if (ndI.hasTransform() or ndJ.hasTransform()):
                    KTij = KT[i][j]

                    # transform KTij
                    # ... as a sequence of vector-like transformations
                    KTij = KTij.T
                    if ndJ.hasTransform():
                        KTij = ndJ.m2l(KTij, self)

                    KTij = KTij.T
                    if ndI.hasTransform():
                        KTij = ndI.m2l(KTij, self)

                    KT[i][j] = KTij
        return KT

    def updateState(self):
        """
        """
        msg = "** WARNING ** {}.{} not implemented".format(self.__class__.__name__, sys._getframe().f_code.co_name)
        raise NotImplementedError(msg)

    def _requestDofs(self, dof_requests):
        r"""
        Helper function (internal use) to inform **all** nodes of this element about the needed/used
        degrees of freedom.

        **Remark**: if nodes of different type are to be used by the element, **DO NOT** use this method but
        implement your own overloaded initialization within the constructor of your element.

        :param dof_requests: list of dofs for a typical node in this element
        """
        self._dof_list = dof_requests
        for node in self.nodes:
            dof_idx = node.request(dof_requests, self)
            self.dof_idx[node] = dof_idx   # marked for removal

    def getDofs(self):
        r"""
        returns the dof-codes for this element in a list
        """
        return self._dof_list

    def setLoadFactor(self, lam):
        r"""
        Set the target load factor to **lam**

        .. warning::

            This method should not be called by the user.
            **USE** :code:`System.setLoadFactor(lam)` instead!

        The entered load pattern is considered a reference load,
        to be multiplied by a scalar load factor, :math:`\lambda`.

        If no load factor is set explicitly, a factor of 1.0 is assumed, i.e., the
        entire entered load is applied in full.
        """
        self.loadfactor = lam

    def setRecorder(self, recorder):
        if isinstance(recorder, Recorder):
            self.recorder = recorder
        else:
            self.recorder = None

    def recordThisStep(self, load_level):
        r"""
        record current state of the system
        """
        if self.recorder and self.recorder.isActive():
            data = {}
            for var in self.recorder.getVariables():
                value = self.getValue(var)[0]
                data[var] = value
            self.recorder.addData(data)

    def getValue(self, name, gp='all'):
        ans = []
        return ans
    def startRecorder(self):
        if self.recorder:
            self.recorder.enable()

    def pauseRecorder(self):
        if self.recorder:
            self.recorder.disable()

    def stopRecorder(self):
        if self.recorder:
            self.recorder.disable()

    def on_converged(self):
        r"""
        This method is called by the solver if convergence has been achieved.

        The element shall perform all necessary state updates,
        especially inform it's material instances about the necessary updates.
        """
        pass

    def revert(self):
        r"""
        This method is called by the solver if the current load step failed to converge
        and the system shall be returned to the last converged state.

        The element shall perform all necessary state updates,
        especially inform it's material instances about the necessary updates.
        """
        pass


if __name__ == "__main__":

    sys.path.insert(0, os.path.abspath(".."))

    from ..domain import Node
    from ..materials import Material

    # testing the Element class
    nd0 = Node(0.0, 0.0)
    nd0.index = 0
    nd1 = Node(3.0, 2.0)
    nd1.index = 1
    params = {'E':100, 'A':1.5, 'fy':1.0e20}
    mat = Material(params)
    elem = Element([nd0, nd1], mat)

    print(nd0)
    print(nd1)

    print("force =", elem.getAxialForce())
    print("nodal forces: ", *elem.getForce())
    print("element stiffness: ", elem.getStiffness())

    # change the nodal displacements
    nd0.setDisp(.1, .05)
    nd1.setDisp(.05, .2)

    print(nd0)
    print(nd1)

    print("force =", elem.getAxialForce())
    print("nodal forces: ", *elem.getForce())
    print("element stiffness: ", elem.getStiffness())


