import numpy as np
import pandas as pd
import os, sys
from typing import Dict
from sklearn.neighbors import LocalOutlierFactor
from PyQt5.QtCore import Qt
import pyqtgraph as pg
from PyQt5 import QtCore, QtGui, QtWidgets
import tkinter
import matplotlib.pyplot as plt
import math
from datetime import datetime,timedelta

plt.rcParams['font.family'] = 'SimHei'  # 使用中文字体
plt.rcParams['axes.unicode_minus'] = False #显示负号
pg.setConfigOption('background','w')
pg.setConfigOption('foreground','k')



class RotateAxisItem(pg.AxisItem):
    def drawPicture(self, p, axisSpec, tickSpecs, textSpecs):
        p.setRenderHint(p.Antialiasing,False)
        p.setRenderHint(p.TextAntialiasing,True)
        ## draw long line along axis
        pen,p1,p2 = axisSpec
        p.setPen(pen)
        p.drawLine(p1,p2)
        p.translate(0.5,0)  ## resolves some damn pixel ambiguity
        ## draw ticks
        for pen,p1,p2 in tickSpecs:
            p.setPen(pen)
            p.drawLine(p1,p2)
        ## draw all text
        # if self.tickFont is not None:
        #     p.setFont(self.tickFont)
        p.setPen(self.pen())
        for rect,flags,text in textSpecs:
            # this is the important part
            p.save()
            p.translate(rect.x(),rect.y())
            p.rotate(-30)
            p.drawText(int(-rect.width()),int(rect.height()),int(rect.width()),int(rect.height()),flags,text)
            # restoring the painter is *required*!!!
            p.restore()


class GraphWidget(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.init_data()
        self.init_ui()
        self.target_color_list = []  # 初始化target_color_list属性
    def init_data(self):
        self.whole_data: Dict = None
        self.whole_xtick: list = []
        self.whole_x: list = []
        self.color_line = (30, 144, 255)
        self.cur_len = 20
        # 最多20条
        self.color_map = {
            '道奇蓝': (30, 144, 255),
            '橙色': (255, 165, 0),
            '深紫罗兰色': (148, 0, 211),
            '春天的绿色': (60, 179, 113),
            '热情的粉红': (255, 105, 180),
            '暗淡的灰色': (105, 105, 105),
            '番茄': (255, 99, 71)
        }
        self.color_16bit_map = {
            '道奇蓝': '#1E90FF',
            '橙色': '#FFA500',
            '深紫罗兰色': '#9400D3',
            '春天的绿色': '#3CB371',
            '热情的粉红': '#FF69B4',
            '暗淡的灰色': '#696969',
            '番茄': '#FF6347'
        }
        pass

    def init_ui(self):
        self.duration_label = QtWidgets.QLabel('左边界~右边界')

        self.left_label = QtWidgets.QLabel('左边：')
        self.left_slider = QtWidgets.QSlider(Qt.Horizontal)
        self.left_slider.valueChanged.connect(self.left_slider_valueChanged)
        self.right_slider = QtWidgets.QSlider(Qt.Horizontal)
        self.right_slider.valueChanged.connect(self.right_slider_valueChanged)
        self.right_label = QtWidgets.QLabel(':右边')

        check_btn = QtWidgets.QPushButton('确定')
        check_btn.clicked.connect(self.check_btn_clicked)

        layout_top = QtWidgets.QHBoxLayout()
        layout_top.addWidget(self.duration_label)
        layout_top.addWidget(self.left_label)
        layout_top.addWidget(self.left_slider)
        layout_top.addWidget(self.right_slider)
        layout_top.addWidget(self.right_label)
        layout_top.addWidget(check_btn)
        # layout_top.addStretch(1)

        xax = RotateAxisItem(orientation='bottom')
        xax.setHeight(h=50)
        self.pw = pg.PlotWidget(axisItems={'bottom': xax})
        self.pw.setMouseEnabled(x=True, y=False)
        # self.pw.enableAutoRange(x=False,y=True)
        self.pw.setAutoVisible(x=False, y=True)

        layout = QtWidgets.QVBoxLayout()
        layout.addLayout(layout_top)
        layout.addWidget(self.pw)
        self.setLayout(layout)
        pass

    def first_setData(self, data: Dict):
        self.whole_data = data
        self.whole_x = data['x']
        self.whole_xtick = data['xTick']
        self.left_slider.setMinimum(0)
        self.left_slider.setMaximum(self.whole_x[-1])
        self.right_slider.setMinimum(0)
        self.right_slider.setMaximum(self.whole_x[-1])
        self.left_slider.setValue(0)
        self.right_slider.setValue(self.whole_x[-1])
        self.left_label.setText(f"左边:{self.whole_xtick[0]}")
        self.right_label.setText(f"{self.whole_xtick[-1]}:右边")

        self.set_data(data)
        pass

    def set_data(self, data: Dict):
        self.pw.clear()
        self.pw.addLegend()
        xTick = [data['xTick00']]
        x = data['x']
        y_list = data['y_list']
        y_names = data['y_names']

        self.x_Tick = data['xTick']
        self.y_data = y_list
        self.y_names = y_names
        self.duration_label.setText(f"{self.x_Tick[0]}~{self.x_Tick[-1]}")

        xax = self.pw.getAxis('bottom')
        xax.setTicks(xTick)

        # 更新 target_color_list
        self.target_color_list = []
        color_keys_list = list(self.color_map.keys())
        for i in range(len(y_names)):
            t_i = i % len(color_keys_list)
            t_key = color_keys_list[t_i]
            self.target_color_list.append(t_key)

        self.plots = {}
        for i, (y, name) in enumerate(zip(y_list, y_names)):
            plot = self.pw.plot(x, y, connect='finite', pen=pg.mkPen({'color': self.color_map[self.target_color_list[i]], 'width': 2}), name=name)
            self.plots[name] = plot

        self.vLine = pg.InfiniteLine(angle=90, movable=False)
        self.hLine = pg.InfiniteLine(angle=0, movable=False)
        self.label = pg.TextItem()

        self.pw.addItem(self.vLine, ignoreBounds=True)
        self.pw.addItem(self.hLine, ignoreBounds=True)
        self.pw.addItem(self.label, ignoreBounds=True)
        self.vb = self.pw.getViewBox()
        self.proxy = pg.SignalProxy(self.pw.scene().sigMouseMoved, rateLimit=60, slot=self.mouseMoved)

        # 显示整条折线图
        self.pw.enableAutoRange()

    def set_empty(self):
        self.pw.clear()
        pass

    def mouseMoved(self, evt):
        pos = evt[0]  # 当前鼠标位置
        if self.pw.sceneBoundingRect().contains(pos):
            mousePoint = self.vb.mapSceneToView(pos)
            index = int(mousePoint.x())
            if 0 <= index < len(self.x_Tick):
                x_str = self.x_Tick[index]

                y_str_html = ''
                for i in range(len(self.target_color_list)):
                    y_str = f"<br><font color='{self.color_16bit_map[self.target_color_list[i]]}'>{self.y_names[i]}: {self.y_data[i][index]}</font>"
                    y_str_html += y_str

                html_str = f'<p style="color:black;font-size:18px;font-weight:bold;">&nbsp;{x_str}&nbsp;{y_str_html}</p>'
                self.label.setHtml(html_str)

                # 调整标签位置
                label_bounds = self.label.mapRectToView(self.label.boundingRect())
                new_x = mousePoint.x()
                new_y = mousePoint.y()
                if label_bounds.right() > self.vb.viewRect().right():
                    new_x -= label_bounds.width()
                if label_bounds.bottom() > self.vb.viewRect().bottom():
                    new_y -= label_bounds.height()

                self.label.setPos(new_x, new_y)

            self.vLine.setPos(mousePoint.x())
            self.hLine.setPos(mousePoint.y())

    def left_slider_valueChanged(self):
        left_value = self.left_slider.value()
        self.left_label.setText(f"左边:{self.whole_xtick[left_value]}")
        pass

    def right_slider_valueChanged(self):
        right_value = self.right_slider.value()
        self.right_label.setText(f"{self.whole_xtick[right_value]}:右边")

    def remove_plot(self, plot_name):
        if plot_name in self.plots:
            self.pw.removeItem(self.plots[plot_name])  # 从图表中移除折线
            del self.plots[plot_name]  # 从字典中移除折线引用

    def check_btn_clicked(self):
        left_value = self.left_slider.value()
        right_value = self.right_slider.value()

        if right_value <= left_value:
            QtWidgets.QMessageBox.information(
                self,
                '提示',
                '左边界不能大于右边界',
                QtWidgets.QMessageBox.Yes
            )
            return
        xTick = self.whole_data['xTick'][left_value:right_value]
        xTick00 = []
        dur_num = int(len(xTick) / float(self.cur_len))
        if dur_num >= 2:
            for i in range(0, len(xTick), dur_num):
                xTick00.append((i, xTick[i]))
        else:
            for i in range(0, len(xTick)):
                xTick00.append((i, xTick[i]))
        y_list00 = []
        y_list = self.whole_data['y_list']
        for item in y_list:
            item00 = item[left_value:right_value]
            y_list00.append(item00)
        x = [i for i in range(len(xTick))]
        line_data = {
            'xTick00': xTick00,
            'xTick': xTick,
            'x': x,
            'y_list': y_list00,
            'y_names': self.whole_data['y_names']
        }
        self.set_data(line_data)
        pass

    pass


class LineMainWidget(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.init_data()
        self.init_ui()
        pass

    def init_data(self):
        self.please_selected_str: str = '-- 请选择 --'
        self.field_list: list = []
        self.x_field: str = ''
        self.current_filename: str = ''
        self.whole_df: pd.DataFrame = None
        self.cur_len: int = 20
        pass

    def init_ui(self):
        self.setWindowTitle('数据分析平台')

        tip_label1 = QtWidgets.QLabel('横坐标字段:')
        self.x_lineedit = QtWidgets.QLineEdit()

        self.file_name_label = QtWidgets.QLabel('文件名')
        self.file_name_label.setWordWrap(True)
        open_file_btn = QtWidgets.QPushButton('打开excel文件')
        open_file_btn.clicked.connect(self.open_file_btn_clicked)

        tip_label = QtWidgets.QLabel('表头下拉列表:')
        self.head_combox = QtWidgets.QComboBox()
        self.head_combox.addItem(self.please_selected_str)
        self.head_combox.currentTextChanged.connect(self.head_combox_currentTextChanged)

        self.list_widget = QtWidgets.QListWidget()
        self.list_widget.setFixedHeight(200)
        check_btn = QtWidgets.QPushButton('确定')
        check_btn.clicked.connect(self.check_btn_clicked)

        self.plot_remove_combobox = QtWidgets.QComboBox()
        self.plot_remove_combobox.addItem("-- 选择要删除的折线 --")
        remove_plot_btn = QtWidgets.QPushButton("删除折线")
        remove_plot_btn.clicked.connect(self.remove_selected_plot)

        delete_btn0 = QtWidgets.QPushButton('删除选中的表头')
        delete_btn0.clicked.connect(self.delete_selected_header)
        clear_btn = QtWidgets.QPushButton('清空')
        clear_btn.clicked.connect(self.clear_btn_clicked)

        #tackle_label = QtWidgets.QLabel('要处理的文件横坐标字段:')
        #self.textEdit = QtWidgets.QTextEdit()
        #self.textEdit.setFixedHeight(40)
        #self.x_lineedit1 = QtWidgets.QLineEdit()

        #self.file_name_label1 = QtWidgets.QLabel('文件名')
        #self.file_name_label1.setWordWrap(True)
        #open_file_btn1 = QtWidgets.QPushButton('打开excel文件')
        #open_file_btn1.clicked.connect(self.open_file_btn_clicked1)

        tip_label2 = QtWidgets.QLabel('选择要处理的表头:')
        self.body_combox = QtWidgets.QComboBox()
        self.body_combox.addItem(self.please_selected_str)
        self.body_combox.currentTextChanged.connect(self.body_combox_currentTextChanged)

        self.list_widget2 = QtWidgets.QListWidget()
        self.list_widget2.setFixedHeight(200)

        clear_btn2 = QtWidgets.QPushButton('清空')
        clear_btn2.clicked.connect(self.clear_btn_clicked1)

        delete_btn = QtWidgets.QPushButton('删除选中的表头')
        delete_btn.clicked.connect(self.delete_selected_header)

        normal0_btn = QtWidgets.QPushButton('Z-SCORE标准化')
        normal0_btn.clicked.connect(self.ZSCORE)
        normal_btn = QtWidgets.QPushButton('MAX-MIN标准化')
        normal_btn.clicked.connect(self.tab1)
        losses_btn = QtWidgets.QPushButton('缺失值处理')
        losses_btn.clicked.connect(self.tab2)
        anomaly_btn = QtWidgets.QPushButton('异常值处理')
        anomaly_btn.clicked.connect(self.handle_anomaly_lof)
        move_btn = QtWidgets.QPushButton('移动平均滤波')
        move_btn.clicked.connect(self.tab4_1)
        mean_btn = QtWidgets.QPushButton('均值滤波')
        mean_btn.clicked.connect(self.tab4_2)

        getwighte_btn = QtWidgets.QPushButton('变化值')
        getwighte_btn.clicked.connect(self.tab5_1)
        rate_btn = QtWidgets.QPushButton('蒸腾速率')
        rate_btn.clicked.connect(self.tab5_2)

        layout_left = QtWidgets.QVBoxLayout()
        layout_left.addWidget(tip_label1)
        layout_left.addWidget(self.x_lineedit)
        layout_left.addWidget(self.file_name_label)
        layout_left.addWidget(open_file_btn)
        layout_left.addWidget(tip_label)
        layout_left.addWidget(self.head_combox)
        layout_left.addWidget(self.list_widget)
        layout_left.addWidget(check_btn)

        layout_left.addWidget(self.plot_remove_combobox)
        layout_left.addWidget(remove_plot_btn)

        #layout_left.addWidget(delete_btn0)
        layout_left.addWidget(clear_btn)

        #layout_left.addWidget(tackle_label)
        #layout_left.addWidget(self.x_lineedit1)
        #layout_left.addWidget(self.file_name_label1)
        #layout_left.addWidget(open_file_btn1)
        layout_left.addWidget(tip_label2)
        layout_left.addWidget(self.body_combox)
        layout_left.addWidget(self.list_widget2)
        #layout_left.addWidget(delete_btn)
        layout_left.addWidget(clear_btn2)
        # layout_left.addWidget(self.textEdit)



        layout_left.addWidget(losses_btn)
        layout_left.addWidget(anomaly_btn)
        layout_left.addWidget(move_btn)
        layout_left.addWidget(mean_btn)

        layout_left.addWidget(normal0_btn)
        layout_left.addWidget(normal_btn)
       #layout_left.addWidget(self.textEdit)
        layout_left.addWidget(getwighte_btn)
        layout_left.addWidget(rate_btn)

        layout_left.addStretch(1)

        self.title_label = QtWidgets.QLabel('数据分析平台')
        self.title_label.setAlignment(QtCore.Qt.AlignCenter)
        self.title_label.setStyleSheet('QLabel{font-size:16px;font-weight:bold}')

        self.line_widget = GraphWidget()

        layout_right = QtWidgets.QVBoxLayout()
        layout_right.addWidget(self.title_label)
        layout_right.addWidget(self.line_widget)

        layout = QtWidgets.QHBoxLayout()
        layout.addLayout(layout_left, 1)
        layout.addLayout(layout_right, 9)

        self.setLayout(layout)
        pass

    def update_plot_remove_combobox(self):
        self.plot_remove_combobox.clear()
        self.plot_remove_combobox.addItem("-- 选择要删除的折线 --")
        if hasattr(self.line_widget, 'plots'):
            self.plot_remove_combobox.addItems(self.line_widget.plots.keys())

    def remove_selected_plot(self):
        selected_plot = self.plot_remove_combobox.currentText()
        if selected_plot and selected_plot != "-- 选择要删除的折线 --":
            self.line_widget.remove_plot(selected_plot)
            self.update_plot_remove_combobox()  # 更新下拉列表

    def open_file_btn_clicked(self):
        x_str = self.x_lineedit.text()
        x_str = x_str.strip()
        if len(x_str) <= 0:
            QtWidgets.QMessageBox.information(
                self,
                '提示',
                '请先输入横坐标字段名',
                QtWidgets.QMessageBox.Yes
            )
            return
        path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self,
            '打开Excel文件或csv文件',
            '.',
            'Excel或CSV(*.xlsx *.csv)'
        )
        if not path:
            return
        if path.endswith('.xlsx'):
            df = pd.read_excel(path, engine='openpyxl')
            pass
        elif path.endswith('.csv'):
            df = pd.read_csv(path, encoding='GB2312')

            pass
        else:
            QtWidgets.QMessageBox.information(
                self,
                '提示',
                '只能上传Excel文件或CSV文件',
                QtWidgets.QMessageBox.Yes
            )
            return
        self.file_name_label.setText(path)
        self.field_list.clear()
        cols = df.columns
        if x_str not in cols:
            QtWidgets.QMessageBox.information(
                self,
                '提示',
                '横坐标字段不在文件中',
                QtWidgets.QMessageBox.Yes
            )
            return
        for col in cols:
            if str(df[col].dtype) == 'object':
                continue
            self.field_list.append(col)
        self.x_field = x_str
        self.current_filename = os.path.basename(path)
        self.whole_df = df.copy()

        self.head_combox.clear()
        self.head_combox.addItem(self.please_selected_str)
        self.head_combox.addItems(self.field_list)

        self.body_combox.clear()
        self.body_combox.addItem(self.please_selected_str)
        self.body_combox.addItems(self.field_list)
        pass
    def open_file_btn_clicked1(self):
        x_str = self.x_lineedit1.text()
        x_str = x_str.strip()
        if len(x_str) <= 0:
            QtWidgets.QMessageBox.information(
                self,
                '提示',
                '请先输入横坐标字段名',
                QtWidgets.QMessageBox.Yes
            )
            return
        path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self,
            '打开Excel文件或csv文件',
            '.',
            'Excel或CSV(*.xlsx *.csv)'
        )
        if not path:
            return
        if path.endswith('.xlsx'):
            df = pd.read_excel(path, engine='openpyxl')
            pass
        elif path.endswith('.csv'):
            df = pd.read_csv(path, encoding='GB2312')

            pass
        else:
            QtWidgets.QMessageBox.information(
                self,
                '提示',
                '只能上传Excel文件或CSV文件',
                QtWidgets.QMessageBox.Yes
            )
            return
        self.file_name_label1.setText(path)
        self.field_list.clear()
        cols = df.columns
        if x_str not in cols:
            QtWidgets.QMessageBox.information(
                self,
                '提示',
                '横坐标字段不在文件中',
                QtWidgets.QMessageBox.Yes
            )
            return
        for col in cols:
            if str(df[col].dtype) == 'object':
                continue
            self.field_list.append(col)
        self.x_field = x_str
        self.current_filename = os.path.basename(path)
        self.whole_df = df.copy()

        self.body_combox.clear()
        self.body_combox.addItem(self.please_selected_str)
        self.body_combox.addItems(self.field_list)
        pass
    def head_combox_currentTextChanged(self, txt):
        cur_txt = self.head_combox.currentText()
        if len(cur_txt.strip()) <= 0:
            return
        if cur_txt == self.please_selected_str:
            return
        self.list_widget.addItem(cur_txt)
        pass
    def body_combox_currentTextChanged(self, txt):
        cur_txt = self.body_combox.currentText()
        if len(cur_txt.strip()) <= 0:
            return
        if cur_txt == self.please_selected_str:
            return
        self.list_widget2.addItem(cur_txt)

        pass

    def delete_selected_header(self):
        path_rawdata = self.file_name_label.text()  # 读取原始数据文件路径
        df = pd.read_excel(path_rawdata)
        column_name=self.list_widget2.item(0).text()
        if column_name in df.columns:
            # 从 DataFrame 中删除该列
            df.drop(columns=[column_name], inplace=True)

            # 将修改后的 DataFrame 保存回原 Excel 文件
            df.to_excel(path_rawdata, index=False)
        else:
            print(f"列 '{column_name}' 不存在于文件中。")
    def check_btn_clicked(self):
        # 确保已经选择了一些列名
        total_count = self.list_widget.count()
        if total_count > 20 or total_count <= 0:
            QtWidgets.QMessageBox.information(
                self, '提示', '选择的字段在1个到20个之间', QtWidgets.QMessageBox.Yes)
            return

        selected_list = []
        for i in range(total_count):
            item = self.list_widget.item(i)
            selected_list.append(item.text())

        df = self.whole_df.copy()

        xTick_tmp = df[self.x_field].values.tolist()
        xTick = []
        for item in xTick_tmp:
            if isinstance(item, int):
                # 假设 item 是以纳秒为单位的 Unix 时间戳
                # 将纳秒转换为秒
                timestamp_in_seconds = item / 1e9
                date = datetime.fromtimestamp(timestamp_in_seconds).strftime('%Y-%m-%d')
            elif isinstance(item, str):
                # 检查字符串格式并解析
                if '-' in item:
                    date_format = '%Y-%m-%d'
                elif '/' in item:
                    date_format = '%Y/%m/%d'
                else:
                    raise ValueError("Unknown date format")

                date = datetime.strptime(item, date_format).strftime('%Y-%m-%d')
            else:
                raise TypeError("Unsupported type in xTick_tmp")

            xTick.append(date)
        #print('xTick', xTick)
        xTick00 = []
        dur_num = int(len(xTick) / float(self.cur_len))
        if dur_num >= 2:
            for i in range(0, len(xTick), dur_num):
                xTick00.append((i, xTick[i]))
        else:
            for i in range(0, len(xTick)):
                xTick00.append((i, xTick[i]))

        y_list = []
        for item in selected_list:
            y_one = df[item].values.tolist()
            y_list.append(y_one)

        if total_count <= 1:
            title_str = f"{self.current_filename}_{selected_list[0]}"
        else:
            title_str = f"{self.current_filename}_多列"
        line_data = {
            'xTick00': xTick00,
            'xTick': xTick,
            'x': list(range(len(xTick))),
            'y_list': y_list,
            'y_names': selected_list
        }
        self.title_label.setText("数据分析平台")
        self.line_widget.first_setData(line_data)



        self.line_widget.first_setData(line_data)  # 绘制图表
        self.update_plot_remove_combobox()  # 更新下拉列表以反映当前图表中的折线名称

    def clear_btn_clicked(self):
        self.list_widget.clear()
    def clear_btn_clicked1(self):
        self.list_widget2.clear()

    def ZSCORE(self):
        root = tkinter.Tk()
        root.withdraw()
        path_rawdata = self.file_name_label.text()  # 读取原始数据文件路径
        content00 = self.list_widget2.item(0).text()
        content00 = str(content00)
        data1 = pd.read_excel(path_rawdata)

        # 计算 z-score 标准化，并添加 content00 值作为列名的前缀
        new_column_name = content00 + '_z-score标准化'
        data1[new_column_name] = (data1[content00] - data1[content00].mean()) / data1[content00].std()

        # 将更改保存回原始文件
        data1.to_excel(path_rawdata, index=False)

        # 绘图部分
        x_labels = data1['日期'].astype(str)  # 将日期转换为字符串以用作标签
        x_ticks = range(len(x_labels))  # 创建一个用于标记的索引范围
        plt.plot(x_ticks, data1[new_column_name].tolist(), marker='o', label='z-score标准化')
        plt.legend()
        plt.xticks(x_ticks, x_labels, rotation=45)  # 设置X轴标签和旋转角度
        plt.xlabel('日期')
        plt.grid(True)
        plt.show()

    def tab1(self):
        root = tkinter.Tk()
        root.withdraw()
        path_rawdata = self.file_name_label.text()  # 读取原始数据文件路径
        content00 = self.list_widget2.item(0).text()
        content00 = str(content00)
        data1 = pd.read_excel(path_rawdata)

        # 计算标准化数据
        normalized_column_name = content00 + '_最大最小标准化'  # 新列名，加上content00的值作为前缀
        data1[normalized_column_name] = (data1[content00] - data1[content00].min()) / (
                data1[content00].max() - data1[content00].min())

        # 将更改保存回原始文件
        data1.to_excel(path_rawdata, index=False)

        # 绘图部分
        x_labels = data1['日期'].astype(str)  # 将日期转换为字符串以用作标签
        x_ticks = range(len(x_labels))  # 创建一个用于标记的索引范围
        plt.plot(x_ticks, data1[normalized_column_name].tolist(), marker='o', label='最大最小标准化')
        plt.legend()
        plt.xticks(x_ticks, x_labels, rotation=45)  # 设置X轴标签和旋转角度
        plt.xlabel('日期')
        plt.grid(True)
        plt.show()

    def tab2(self):
        root = tkinter.Tk()
        root.withdraw()
        path_rawdata = self.file_name_label.text()  # 读取原始数据文件路径
        content00 = self.list_widget2.item(0).text()  # 获取选中的列名
        data1 = pd.read_excel(path_rawdata)

        # 创建新列名，以表示这是处理后的数据
        new_column_name = content00 + '_缺失值处理'

        # 复制原始列的数据到新列
        data1[new_column_name] = data1[content00].copy()

        # 替换新列中的0为NaN，并处理缺失值
        data1[new_column_name].replace(0, np.nan, inplace=True)
        for i in range(len(data1)):
            if pd.isnull(data1.loc[i, new_column_name]):
                # 获取前后4个非NaN和非0的值
                valid_indices = [j for j in range(max(0, i - 4), min(len(data1), i + 5)) if
                                 j != i and not pd.isnull(data1.loc[j, new_column_name]) and data1.loc[j, new_column_name] != 0]
                if valid_indices:
                    mean_val = data1.loc[valid_indices, new_column_name].mean()
                else:
                    mean_val = data1[new_column_name].mean()
                data1.loc[i, new_column_name] = mean_val

        # 将DataFrame保存回原始文件，这样原始数据列保持不变，只是新增了处理后的列
        data1.to_excel(path_rawdata, index=False)

        # 绘图部分
        x_labels = data1['日期'].astype(str)  # 将日期转换为字符串以用作标签
        x_ticks = range(len(x_labels))  # 创建一个用于标记的索引范围
        plt.figure(figsize=(10, 6))  # 设置图形大小
        plt.plot(x_ticks, data1[content00].tolist(), marker='o', linestyle='-', label='原始数据')
        plt.plot(x_ticks, data1[new_column_name].tolist(), marker='x', linestyle='--', label='缺失值处理后')
        plt.legend()
        plt.xticks(x_ticks, x_labels, rotation=45)  # 设置X轴标签和旋转角度
        plt.xlabel('日期')
        plt.ylabel('值')
        plt.title('缺失值处理前后对比')
        plt.grid(True)
        plt.tight_layout()  # 调整整体空白
        plt.show()


    def handle_anomaly_lof(self):
        root = tkinter.Tk()
        root.withdraw()
        path_rawdata = self.file_name_label.text()  # 读取原始数据文件路径
        selected_column = self.list_widget2.item(0).text()  # 获取选中的列名
        data1 = pd.read_excel(path_rawdata)

        # 创建新列名，表示这是处理后的数据
        new_column_name = selected_column + '_LOF异常值处理'

        # LOF算法需要一个二维数组作为输入，因此将选中的列转换为二维数组
        X = data1[[selected_column]].values

        # 初始化LOF检测器
        lof = LocalOutlierFactor(n_neighbors=20, novelty=False, contamination='auto')
        y_pred = lof.fit_predict(X)

        # 复制原始列的数据到新列
        data1[new_column_name] = data1[selected_column].copy()

        # 标记被LOF算法识别为异常的值
        # LOF返回-1表示异常值，1表示正常值
        data1.loc[y_pred == -1, new_column_name] = np.nan  # 将异常值替换为NaN

        # 将DataFrame保存回原始文件，这样原始数据列保持不变，只是新增了处理后的列
        data1.to_excel(path_rawdata, index=False)

        # 绘图部分，对比原始数据和异常值处理后的数据
        x_labels = data1['日期'].astype(str)  # 将日期转换为字符串以用作标签
        x_ticks = range(len(x_labels))  # 创建一个用于标记的索引范围
        plt.figure(figsize=(10, 6))  # 设置图形大小
        plt.plot(x_ticks, data1[selected_column].tolist(), marker='o', linestyle='-', label='原始数据')
        plt.plot(x_ticks, data1[new_column_name].tolist(), marker='x', linestyle='--', label='LOF异常值处理后')
        plt.legend()
        plt.xticks(x_ticks, x_labels, rotation=45)  # 设置X轴标签和旋转角度
        plt.xlabel('日期')
        plt.ylabel('值')
        plt.title('LOF异常值处理前后对比')
        plt.grid(True)
        plt.tight_layout()  # 调整整体空白
        plt.show()


    def tab4_1(self):
        root = tkinter.Tk()
        root.withdraw()
        path_rawdata = self.file_name_label.text()  # 读取原始数据文件路径
        content00 = self.list_widget2.item(0).text()
        content00 = str(content00)
        data1 = pd.read_excel(path_rawdata)

        window_size = 3  # 移动窗口大小

        # 新列名，加上content00的值作为前缀
        new_column_name = content00 + '_移动平均滤波'
        data1[new_column_name] = data1[content00].rolling(window=window_size).mean()

        # 将更改保存回原始文件
        data1.to_excel(path_rawdata, index=False)

        # 绘图部分
        x_labels = data1['日期'].astype(str)  # 将日期转换为字符串以用作标签
        x_ticks = range(len(x_labels))  # 创建一个用于标记的索引范围

        plt.plot(x_ticks, data1[new_column_name].tolist(), marker='o', label='移动平均滤波')
        plt.legend()
        plt.xticks(x_ticks, x_labels, rotation=45)  # 设置X轴标签和旋转角度
        plt.xlabel('日期')
        plt.grid(True)
        plt.show()

    def tab4_2(self):
        root = tkinter.Tk()
        root.withdraw()
        path_rawdata = self.file_name_label.text()  # 读取原始数据文件路径
        content00 = self.list_widget2.item(0).text()
        content00 = str(content00)
        data1 = pd.read_excel(path_rawdata)

        alpha = 0.2  # 平滑参数
        x_labels = data1['日期'].astype(str)  # 将日期转换为字符串以用作标签
        x_ticks = range(len(x_labels))  # 创建一个用于标记的索引范围

        # 新列名，加上content00的值作为前缀
        new_column_name = content00 + '_均值滤波'
        data1[new_column_name] = data1[content00].ewm(alpha=alpha).mean()

        # 将更改保存回原始文件
        data1.to_excel(path_rawdata, index=False)

        x_labels = data1['日期'].astype(str)  # 将日期转换为字符串以用作标签
        x_ticks = range(len(x_labels))  # 创建一个用于标记的索引范围

        plt.plot(x_ticks, data1[new_column_name].tolist(), marker='o', label='均值滤波')
        plt.legend()
        plt.xticks(x_ticks, x_labels, rotation=45)  # 设置X轴标签和旋转角度
        plt.xlabel('日期')
        plt.grid(True)
        plt.show()

    def tab5_1(self):
        path_rawdata = self.file_name_label.text()
        print(path_rawdata)
        data = pd.read_excel(path_rawdata, header=None)

        data.columns = data.iloc[0]
        data = data.iloc[1:]
        m = self.body_combox.itemText(self.body_combox.currentIndex())
        print(m)  # 重力1

        df_first = data.drop_duplicates(subset=['日期'], keep='first')
        print(df_first)

        # 3. 计算相邻两天的数据差异
        content00 = m  # 假设content00为m的值
        new_column_name = content00 + '_变化值'
        df_subset = df_first.copy()
        df_subset[new_column_name] = df_subset[m].diff()  # 使用带前缀的列名

        df_subset.to_excel(path_rawdata, index=False)

        plt.plot(df_subset['日期'], df_subset[new_column_name], marker='o', label='变化值')
        plt.legend()
        plt.xlabel('日期')
        plt.ylabel('变化值(克/日)')
        plt.title('每日数据差异')
        plt.grid(True)
        plt.show()

    def tab5_2(self):
        path_rawdata = self.file_name_label.text()
        print(path_rawdata)
        data = pd.read_excel(path_rawdata, header=None)
        data.columns = data.iloc[0]
        data = data.iloc[1:]
        m = self.body_combox.itemText(self.body_combox.currentIndex())

        # 创建时间戳列
        data['timestamp'] = pd.to_datetime(data['日期'].astype(str) + ' ' + data['时间'].astype(str))
        data.sort_values(by='timestamp', inplace=True)

        # 选择每个小时的第一条记录
        data['hour'] = data['timestamp'].dt.floor('H')
        df_first = data.drop_duplicates(subset=['hour'], keep='first')

        # 获取content00的值作为列名前缀
        content00 = self.textEdit.toPlainText()
        new_column_name = content00 + '_蒸腾速率'

        # 计算相邻小时内数据的差异
        df_first[new_column_name] = df_first[m].diff()

        df_first.to_excel(path_rawdata, index=False)

        plt.plot(df_first['hour'], df_first[new_column_name], marker='o')
        hour_labels = df_first['hour'].dt.strftime('%Y-%m-%d %H:%M:%S').tolist()
        plt.xticks(df_first['hour'], hour_labels, rotation=45)
        plt.xlabel('Hour')
        plt.ylabel('蒸腾速率(g/h)')
        plt.grid(True)
        plt.show()

    def tab5_3(self):
        path_rawdata = self.file_name_label.text()
        print(path_rawdata)
        data = pd.read_excel(path_rawdata, header=None)

        data.columns = data.iloc[0]
        data = data.iloc[1:]
        m1 = self.body_combox.itemText(self.body_combox.currentIndex())
        m2 = self.comboBox_2.itemText(self.comboBox_2.currentIndex())

        # 2022-09-14 20 2022-09-14 21
        now = []
        for i in range(data.shape[0]):
            now.append(str(data['日期'].tolist()[i])[0:10] + ' ' + str(data['时间'].tolist()[i])[0:2])
        data['time'] = now
        data_time = data['time'].tolist()
        content00 = self.textEdit.toPlainText()
        content01 = str(content00)[0:13]
        content02 = str(content00)[14:27]
        index_one = data_time.index(content01)
        index_two = data_time.index(content02)

        date_format = '%Y-%m-%d %H'
        date1 = datetime.strptime(content01, date_format)
        date2 = datetime.strptime(content02, date_format)
        time_difference = date2 - date1
        hours_difference = time_difference.total_seconds() / 3600

        # 公式
        E = hours_difference * (data[m1].tolist()[index_two] - data[m1].tolist()[index_one]) / (
                data[m2].tolist()[index_two] - data[m2].tolist()[index_one])
        gsc = E * 101.3 / (0.610788 * math.e ** (
                17.27 * data[m1].tolist()[index_two] / (data[m1].tolist()[index_two] + 237.3)) * (
                                   1 - data[m1].tolist()[index_one]))
        print('气孔导度：', gsc)

class LoginDialog(QtWidgets.QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("登录")
        self.setFixedSize(200, 120)

        self.username_label = QtWidgets.QLabel("用户名:", self)
        self.username_label.move(20, 20)
        self.username_input = QtWidgets.QLineEdit(self)
        self.username_input.move(70, 20)
        self.username_input.resize(100, 20)

        self.password_label = QtWidgets.QLabel("密码:", self)
        self.password_input = QtWidgets.QLineEdit(self)
        self.password_input.setEchoMode(QtWidgets.QLineEdit.Password)
        self.password_label.move(20, 50)
        self.password_input.move(70, 50)
        self.password_input.resize(100, 20)

        self.login_button = QtWidgets.QPushButton("登录", self)
        self.login_button.move(70, 80)
        self.login_button.clicked.connect(self.check_credentials)

    def check_credentials(self):
        # 这里应该添加验证用户名和密码的逻辑
        if self.username_input.text() == "user" and self.password_input.text() == "pass":  # 示例用户名和密码
            self.accept()
        else:
            QtWidgets.QMessageBox.warning(self, "错误", "用户名或密码不正确！")
if __name__ == '__main__':
    QtCore.QCoreApplication.setAttribute(QtCore.Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    app = QtWidgets.QApplication(sys.argv)

    login_dialog = LoginDialog()
    if login_dialog.exec_() == QtWidgets.QDialog.Accepted:
        main_window = LineMainWidget()
        main_window.showMaximized()
        app.exec()
    else:
        sys.exit()
