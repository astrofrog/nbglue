import os
import tempfile

from IPython.display import display, Image

from qtpy import QtWidgets
from qtpy.QtCore import Qt

from glue.utils.qt import get_qapp
from glue.core.data_factories import load_data
from glue.core.application_base import Application
from glue.viewers.scatter.qt.viewer_widget import ScatterWidget
from glue.viewers.histogram.qt.viewer_widget import HistogramWidget
# from glue_vispy_viewers.scatter.scatter_viewer import VispyScatterViewer
from glue.app.qt.edit_subset_mode_toolbar import EditSubsetModeToolBar
from glue.app.qt.layer_tree_widget import LayerTreeWidget


class GlueController(QtWidgets.QMainWindow):

    def __init__(self, session, parent=None):
        super(GlueController, self).__init__(parent=parent)

        self.layer_widget = LayerTreeWidget()
        self.layer_widget.set_checkable(False)
        self.layer_widget.setup(session.data_collection)

        self.setCentralWidget(self.layer_widget)

        self.tbar = EditSubsetModeToolBar()
        self.addToolBar(self.tbar)

        self.layer_widget.bind_selection_to_edit_subset()


class CLIApplication(Application):

    def __init__(self, *args, **kwargs):
        super(CLIApplication, self).__init__(*args, **kwargs)
        self._controller = GlueController(self.session)
        self._mode_toolbar = self._controller.tbar
        self._controller.show()
        self._controller.raise_()

    @staticmethod
    def _choose_merge(data, other):
        return None, None

    def _update_undo_redo_enabled(self):
        pass

    def new_data_viewer(self, viewer_class, data=None):

        if viewer_class is None:
            return

        c = viewer_class(self._session)
        c.register_to_hub(self._session.hub)

        if data and not c.add_data(data):
            c.close(warn=False)
            return

        return c

    def scatter(self, data, x, y):
        scatter = self.new_data_viewer(ScatterWidget, data)
        scatter.xatt = data.id[x]
        scatter.yatt = data.id[y]
        return scatter

    def histogram(self, data, x):
        histogram = self.new_data_viewer(HistogramWidget, data)
        histogram.component = data.id[x]
        return histogram

    def load_data(self, path):
        # FIXME: patch this in the core package
        d = load_data(path)
        self.add_datasets(self.data_collection, d)
        return d

    def add_data(self, *args, **kwargs):

        datasets = []

        for path in args:
            datasets.append(load_data(path))

        links = kwargs.pop('links', None)

        from glue.qglue import parse_data, parse_links

        for label, data in kwargs.items():
            datasets.extend(parse_data(data, label))

        self.add_datasets(self.data_collection, datasets)

        if links is not None:
            self.data_collection.add_link(parse_links(self.data_collection, links))

        return datasets

    # def scatter_3d(self, data, x, y, z):
    #     scatter = self.new_data_viewer(VispyScatterViewer, data)
    #     options = scatter.options_widget()
    #     options.x_att = data.id[x]
    #     options.y_att = data.id[y]
    #     options.z_att = data.id[z]
    #     return scatter

    def show(self, *viewers):

        splitter = QtWidgets.QSplitter()
        splitter.setOrientation(Qt.Vertical)
        for viewer in viewers:
            splitter.addWidget(viewer)

        window = QtWidgets.QDialog()
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(splitter)
        window.setLayout(layout)

        window.show()
        window.raise_()
        window.exec_()

        tmpdir = tempfile.mkdtemp()
        filename = os.path.join(tmpdir, 'tmp.png')
        for viewer in viewers:
            viewer.axes.figure.savefig(filename, dpi=150)
            display(Image(filename=filename, width=500, height=500))


def start_nbglue():
    app = get_qapp()
    return CLIApplication()


# def show(viewer):
#
#     viewer.show()
#     viewer.raise_()

    # from qtpy.QtWidgets import QDialog, QVBoxLayout
    #
    # layout = QVBoxLayout()
    # layout.addWidget(viewer)
    #
    # # TODO: fix to just make original viewer modal insead of doing this nonsense
    # dialog = QDialog()
    # dialog.setLayout(layout)
    #
    # dialog.show()
    # dialog.raise_()
    # dialog.exec_()
    #
    # import os
    # import tempfile
    # from IPython.display import Image
    # tmpdir = tempfile.mkdtemp()
    # filename = os.path.join(tmpdir, 'tmp.png')
    # viewer.axes.figure.savefig(filename)
    # image = Image(filename=filename)
    # return image, image
