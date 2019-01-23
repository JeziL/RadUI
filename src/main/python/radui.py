from RDData import *
from PyQt5.QtGui import *
from PandasModel import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *

import datetime
import matplotlib
from scipy.io import savemat
from matplotlib.figure import Figure
from mpl_toolkits.mplot3d import axes3d, Axes3D
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar


class RadUIForm(QMainWindow):
    def __init__(self, app_context, parent=None):
        QMainWindow.__init__(self, parent)
        self.app_context = app_context
        self.adv_x = "radialDistance"
        self.adv_y = "x"
        self.adv_fit = False
        self.init_main_frame()

    def init_main_frame(self):
        self.main_frame = QSplitter()
        self.left_frame = QWidget()
        self.right_frame = QWidget()

        self.init_menu()
        self.init_open_file_frame()
        self.init_rad_select_frame()
        self.init_table_frame()
        self.init_fit_frame()
        self.init_plot_setting_frame()
        self.init_figure_frame()

        layout = QVBoxLayout()
        layout.addWidget(self.open_file_frame)
        layout.addWidget(self.rad_select_frame)
        layout.addWidget(self.table_frame)
        layout.addWidget(self.fit_frame)
        self.left_frame.setLayout(layout)

        layout = QVBoxLayout()
        layout.addWidget(self.plot_setting_frame)
        layout.addWidget(self.figure_frame)
        self.right_frame.setLayout(layout)

        self.main_frame.addWidget(self.left_frame)
        self.main_frame.addWidget(self.right_frame)

        self.main_frame.setChildrenCollapsible(True)
        self.main_frame.setHandleWidth(2)
        self.main_frame.setStyleSheet("""
            QSplitter::handle {
                width: 2px;
                margin-left: 8px;
                margin-right: 8px;
                background-color: darkgrey;
            }
        """)

        self.setCentralWidget(self.main_frame)
        self.setAcceptDrops(True)
    
    def init_open_file_frame(self):
        f = QWidget()
        f.filename_label = QLineEdit()
        f.filename_label.setReadOnly(True)
        f.browse_button = QPushButton("浏览...")
        f.browse_button.clicked.connect(self.select_file)

        layout = QHBoxLayout()
        layout.addWidget(QLabel("数据文件："))
        layout.addWidget(f.filename_label)
        layout.addWidget(f.browse_button)
        f.setLayout(layout)
        self.open_file_frame = f
    
    def select_file(self):
        dlg = QFileDialog()
        dlg.setFileMode(QFileDialog.ExistingFile)
        dlg.setNameFilter("雷达数据 (*.txt *.csv)")
        dlg.setDirectory(QDir.home())
        if dlg.exec() and len(dlg.selectedFiles()):  # 打开文件
            self.load_file(dlg.selectedFiles()[0])

    def load_file(self, filename):
        self.filename = filename
        self.open_file_frame.filename_label.setText(self.filename)
        self.rad = RDData(self.filename)  # 载入雷达数据
        # 还原所有选项
        ## 还原雷达选择
        self.rad_select_frame.rad_button_group.setExclusive(False)
        for i, b in enumerate(self.rad_select_frame.rad_button_group.buttons()):
            b.setText("{0} 号雷达".format(i + 1))
            b.setChecked(False)
            b.setEnabled(False)
        self.rad_select_frame.rad_button_group.setExclusive(True)
        ## 清空数据表
        self.table_frame.setModel(None)
        ## 还原绘图设置
        self.plot_setting_frame.plot_button_group.setExclusive(False)
        for b in self.plot_setting_frame.plot_button_group.buttons():
            b.setChecked(False)
            b.setEnabled(False)
        self.plot_setting_frame.plot_button_group.setExclusive(True)
        self.plot_setting_frame.redraw_button.setEnabled(False)
        self.plot_setting_frame.plot_fit_checkbox.setChecked(False)
        self.plot_setting_frame.plot_fit_checkbox.setEnabled(False)
        self.plot_menu.actions()[0].setEnabled(False)
        ## 清空图象
        self.fig.clear()
        # 更新各雷达点数
        for i in self.rad.available_radar:
            b = self.rad_select_frame.rad_button_group.button(i)
            b.setText("{0} 号雷达 ({1} 点)".format(i, len(self.rad.data[i].index)))
            b.setEnabled(True)
        # 开启导出至 MATLAB 选项
        self.data_menu.actions()[0].setEnabled(True)
    
    def init_rad_select_frame(self):
        f = QGroupBox("雷达选择")

        f.rad_button_group = QButtonGroup()
        r1 = QRadioButton("1 号雷达")
        r2 = QRadioButton("2 号雷达")
        r3 = QRadioButton("3 号雷达")
        r4 = QRadioButton("4 号雷达")
        f.rad_button_group.addButton(r1, id=1)
        f.rad_button_group.addButton(r2, id=2)
        f.rad_button_group.addButton(r3, id=3)
        f.rad_button_group.addButton(r4, id=4)
        f.rad_button_group.buttonClicked.connect(self.on_radar_select)

        layout = QGridLayout()
        for i, b in enumerate(f.rad_button_group.buttons()):
            b.setEnabled(False)
            if i < 2:
                r = 1
                c = i + 1
            else:
                r = 2
                c = i - 1
            layout.addWidget(b, r, c)
        f.setLayout(layout)
        self.rad_select_frame = f

    def init_table_frame(self):
        f = QTableView()
        self.table_frame = f

    def on_radar_select(self):  # 选择雷达
        rad_id = self.rad_select_frame.rad_button_group.checkedId()
        self.table_frame.setModel(PandasModel(self.rad.data[rad_id]))  # 显示表格
        # 绘图选项启用
        for b in self.plot_setting_frame.plot_button_group.buttons():
            b.setEnabled(True)
        self.plot_setting_frame.redraw_button.setEnabled(True)
        # 高级绘图选项菜单启用
        self.plot_menu.actions()[0].setEnabled(True)

    def init_fit_frame(self):
        f = QWidget()

        f.r_label = QDoubleSpinBox()
        f.r_label.setMinimum(0)
        f.r_label.setMaximum(1)
        f.r_label.setSingleStep(0.01)
        f.r_label.setDecimals(3)
        f.r_label.setValue(1)
        f.fit_button = QPushButton("拟合")
        f.fit_button.clicked.connect(self.on_fit)

        layout = QHBoxLayout()
        layout.addWidget(QLabel("遗忘系数："))
        layout.addWidget(f.r_label)
        layout.addWidget(f.fit_button)
        f.setLayout(layout)
        self.fit_frame = f

    def on_fit(self):  # 拟合
        rad_id = self.rad_select_frame.rad_button_group.checkedId()
        r = self.fit_frame.r_label.value()
        self.rad.fit(rad_id, r=r)
        # 绘制拟合曲线功能启用
        self.plot_setting_frame.plot_fit_checkbox.setEnabled(True)

    def init_plot_setting_frame(self):
        f = QGroupBox("快速绘图选项")

        f.plot_button_group = QButtonGroup()
        r1 = QRadioButton("距离-俯仰")
        r2 = QRadioButton("距离-水平")
        r3 = QRadioButton("3D")
        f.plot_button_group.addButton(r1, id=1)
        f.plot_button_group.addButton(r2, id=2)
        f.plot_button_group.addButton(r3, id=3)
        f.plot_button_group.buttonClicked.connect(self.on_plot)

        f.plot_fit_checkbox = QCheckBox("显示拟合结果")
        f.plot_fit_checkbox.setEnabled(False)
        f.plot_fit_checkbox.clicked.connect(self.on_plot)

        f.redraw_button = QPushButton("重绘")
        f.redraw_button.setEnabled(False)
        f.redraw_button.clicked.connect(self.on_plot)

        layout = QHBoxLayout()
        for b in f.plot_button_group.buttons():
            b.setEnabled(False)
            layout.addWidget(b)
        layout.addWidget(f.plot_fit_checkbox)
        layout.addWidget(f.redraw_button)
        f.setLayout(layout)
        f.setMaximumHeight(80)
        self.plot_setting_frame = f

    def init_figure_frame(self):
        self.fig = Figure((15, 10), dpi=100)
        self.figure_frame = QWidget()
        self.canvas = FigureCanvas(self.fig)
        self.mpl_toolbar = NavigationToolbar(self.canvas, self.main_frame)
        layout = QVBoxLayout()
        layout.addWidget(self.mpl_toolbar)
        layout.addWidget(self.canvas)
        self.figure_frame.setLayout(layout)

    def on_plot(self):
        plot_type = self.plot_setting_frame.plot_button_group.checkedId()
        plot_fit = self.plot_setting_frame.plot_fit_checkbox.isChecked()
        rad_id = self.rad_select_frame.rad_button_group.checkedId()
        data = self.rad.data[rad_id]
        if plot_fit and rad_id not in self.rad.fit_param:
            self.on_fit()
        if plot_type == 1:  # 距离-俯仰
            self.axes = self.fig.add_subplot(111)
            self.axes.clear()
            self.axes.invert_xaxis()
            self.axes.set_xlabel(AX_LABEL["radialDistance"])
            self.axes.set_ylabel(AX_LABEL["elevation"])
            self.axes.scatter(data.radialDistance, data.elevation, s=5)
            if plot_fit:
                self.rad.plot_fitting("elevation", self.axes, rad_id)
        elif plot_type == 2:  # 距离-水平
            self.axes = self.fig.add_subplot(111)
            self.axes.clear()
            self.axes.invert_xaxis()
            self.axes.set_xlabel(AX_LABEL["radialDistance"])
            self.axes.set_ylabel(AX_LABEL["azimuth"])
            self.axes.scatter(data.radialDistance, data.azimuth, s=5)
            if plot_fit:
                self.rad.plot_fitting("azimuth", self.axes, rad_id)
        else:  # 3D
            self.axes = self.fig.add_subplot(111, projection="3d")
            self.axes.clear()
            self.axes.set_xlabel(AX_LABEL["x"])
            self.axes.set_ylabel(AX_LABEL["y"])
            self.axes.set_zlabel(AX_LABEL["z"])
            self.axes.scatter(data.x, data.y, data.z, s=5)
            if plot_fit:
                self.rad.plot_fitting("3d", self.axes, rad_id)

        self.axes.set_title("{0} 号雷达".format(rad_id))
        self.canvas.draw()

    def adv_fig_dialog(self):
        dialog = QDialog(self, Qt.WindowTitleHint | Qt.WindowCloseButtonHint)
        dialog.setWindowTitle("高级绘图选项")

        rad_id = self.rad_select_frame.rad_button_group.checkedId()
        columns = self.rad.data[rad_id].columns.values

        x_frame = QWidget()
        x_axes = QComboBox()
        x_axes.setEditable(False)
        x_axes.addItems(columns)
        x_axes.setCurrentText(self.adv_x)
        x_axes.currentTextChanged.connect(self.adv_axes_changed)
        layout = QHBoxLayout()
        layout.addWidget(QLabel("x 轴："))
        layout.addWidget(x_axes)
        x_frame.setLayout(layout)

        y_frame = QWidget()
        y_axes = QComboBox()
        y_axes.setEditable(False)
        y_axes.addItems(columns)
        y_axes.setCurrentText(self.adv_y)
        y_axes.currentTextChanged.connect(self.adv_axes_changed)
        layout = QHBoxLayout()
        layout.addWidget(QLabel("y 轴："))
        layout.addWidget(y_axes)
        y_frame.setLayout(layout)

        adv_fit_checkbox = QCheckBox("显示拟合结果")
        adv_fit_checkbox.setChecked(self.adv_fit)
        adv_fit_checkbox.setEnabled(True)

        btn_frame = QWidget()
        ok_btn = QPushButton("确定")
        ok_btn.setAutoDefault(False)
        ok_btn.setDefault(True)
        ok_btn.clicked.connect(dialog.accept)
        cancel_btn = QPushButton("取消")
        cancel_btn.setAutoDefault(False)
        cancel_btn.setDefault(False)
        cancel_btn.clicked.connect(dialog.reject)
        layout = QHBoxLayout()
        layout.addWidget(cancel_btn)
        layout.addWidget(ok_btn)
        btn_frame.setLayout(layout)

        layout = QVBoxLayout()
        layout.addWidget(x_frame)
        layout.addWidget(y_frame)
        layout.addWidget(adv_fit_checkbox)
        layout.addWidget(btn_frame)
        dialog.setLayout(layout)

        dialog.finished.connect(self.on_adv_dialog_finished)
        dialog.x_axes = x_axes
        dialog.y_axes = y_axes
        dialog.adv_fit_checkbox = adv_fit_checkbox
        self.adv_dialog = dialog
        dialog.exec()

    def adv_axes_changed(self):
        self.adv_x = self.adv_dialog.x_axes.currentText()
        self.adv_y = self.adv_dialog.y_axes.currentText()
        if self.adv_x == "radialDistance" and self.adv_y in ["azimuth", "elevation", "x", "y", "z"]:
            self.adv_dialog.adv_fit_checkbox.setEnabled(True)
        elif self.adv_x in ["x", "y", "z"] and self.adv_y in ["x", "y", "z"]:
            self.adv_dialog.adv_fit_checkbox.setEnabled(True)
        else:
            self.adv_dialog.adv_fit_checkbox.setEnabled(False)

    def on_adv_dialog_finished(self, result):
        if result != QDialog.Accepted:
            return
        rad_id = self.rad_select_frame.rad_button_group.checkedId()
        data = self.rad.data[rad_id]
        self.adv_x = self.adv_dialog.x_axes.currentText()
        self.adv_y = self.adv_dialog.y_axes.currentText()
        self.adv_fit = self.adv_dialog.adv_fit_checkbox.isChecked()
        if self.adv_fit and rad_id not in self.rad.fit_param:
            self.on_fit()
        self.axes = self.fig.add_subplot(111)
        self.axes.clear()
        if self.adv_x == "radialDistance":
            self.axes.invert_xaxis()
        self.axes.set_xlabel(AX_LABEL[self.adv_x])
        self.axes.set_ylabel(AX_LABEL[self.adv_y])
        self.axes.scatter(data[self.adv_x], data[self.adv_y], s=5)
        if self.adv_fit:
            if self.adv_x == "radialDistance" and self.adv_y in ["azimuth", "elevation", "x", "y", "z"]:
                self.rad.plot_fitting(self.adv_y, self.axes, rad_id)
            elif self.adv_x in ["x", "y", "z"] and self.adv_y in ["x", "y", "z"]:
                self.rad.plot_fitting(self.adv_y, self.axes, rad_id, x=self.adv_x)

        self.axes.set_title("{0} 号雷达".format(rad_id))
        self.canvas.draw()

    def save_fig(self):
        file_choices = "便携式网络图形 (*.png)"
        path, ext = QFileDialog.getSaveFileName(self, "保存图象", "", file_choices)
        path = path.encode("utf-8")
        if path:
            if not path[-4:] == ".png".encode("utf-8"):
                path += ".png".encode("utf-8")
            self.canvas.print_figure(path.decode(), dpi=100)

    def init_menu(self):
        self.menuBar().setNativeMenuBar(True)

        self.file_menu = self.menuBar().addMenu("&文件")

        load_file_action = QAction("&打开...", self)
        load_file_action.setShortcut("Ctrl+O")
        load_file_action.setStatusTip("打开雷达数据文件")
        load_file_action.triggered.connect(self.select_file)
        self.file_menu.addAction(load_file_action)

        quit_action = QAction("&退出", self)
        quit_action.setShortcut("Ctrl+Q")
        quit_action.setStatusTip("退出应用")
        quit_action.triggered.connect(self.close)
        self.file_menu.addAction(quit_action)

        self.data_menu = self.menuBar().addMenu("&数据")

        save_mat_action = QAction("&导出至 MATLAB...", self)
        save_mat_action.setShortcut("Ctrl+E")
        save_mat_action.setStatusTip("导出当前雷达数据至 MATLAB 数据文件")
        save_mat_action.triggered.connect(self.save_mat)
        save_mat_action.setEnabled(False)
        self.data_menu.addAction(save_mat_action)

        self.plot_menu = self.menuBar().addMenu("&绘图")

        adv_figure_action = QAction("&高级...", self)
        adv_figure_action.setStatusTip("自定义绘图选项")
        adv_figure_action.triggered.connect(self.adv_fig_dialog)
        adv_figure_action.setEnabled(False)
        self.plot_menu.addAction(adv_figure_action)

        save_figure_action = QAction("&保存当前图象...", self)
        save_figure_action.setShortcut("Ctrl+S")
        save_figure_action.setStatusTip("保存当前图象为 PNG 文件")
        save_figure_action.triggered.connect(self.save_fig)
        self.plot_menu.addAction(save_figure_action)

        self.help_menu = self.menuBar().addMenu("&帮助")

        about_action = QAction("&关于", self)
        about_action.setStatusTip("关于 RadUI")
        about_action.triggered.connect(self.about_dialog)
        self.help_menu.addAction(about_action)

    def save_mat(self):
        dic_array = []
        for rad_id in self.rad.available_radar:
            data = self.rad.data[rad_id]
            data_dic = {col_name: data[col_name].values for col_name in data.columns.values}
            data_dic["radID"] = rad_id
            dic_array.append(data_dic)
        file_choices = "MAT 文件 (*.mat)"
        path, ext = QFileDialog.getSaveFileName(self, "导出雷达数据", "", file_choices)
        path = path.encode("utf-8")
        if path:
            if not path[-4:] == ".mat".encode("utf-8"):
                path += ".mat".encode("utf-8")
            savemat(path.decode(), {'rad': dic_array}, oned_as="column", do_compression=True)

    def about_dialog(self):
        dialog = QDialog(self, Qt.WindowTitleHint | Qt.WindowCloseButtonHint)
        dialog.setWindowTitle("关于 RadUI")
        text_label = QLabel(dialog)
        text_label.setFrameStyle(QFrame.NoFrame)

        html = open(self.app_context.get_resource("about.html"), encoding="utf8").read()
        html = html.replace("$APP_VER$", self.app_context.build_settings["version"])
        until_year = ""
        now_year = datetime.datetime.now().year
        if now_year > 2019:
            until_year = " - {0}".format(now_year)
        html = html.replace("$UNTIL_YEAR$", until_year)
        text_label.setTextFormat(Qt.RichText)
        text_label.setText(html)
        text_label.setOpenExternalLinks(True)

        layout = QVBoxLayout()
        layout.addWidget(text_label)
        dialog.setLayout(layout)
        dialog.show()

    def dragEnterEvent(self, e):
        if e.mimeData().hasUrls:
            e.accept()
        else:
            e.ignore()

    def dropEvent(self, e):
        if e.mimeData().hasUrls:
            e.accept()
            filename = ""
            for url in e.mimeData().urls():
                filename = str(url.toLocalFile())
            if filename != "":
                self.load_file(filename)
        else:
            e.ignore()
