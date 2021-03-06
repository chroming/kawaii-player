"""
Copyright (C) 2017 kanishka-linux kanishka.linux@gmail.com

This file is part of kawaii-player.

kawaii-player is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

kawaii-player is distributed in the hope that it will be useful, 
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with kawaii-player.  If not, see <http://www.gnu.org/licenses/>.
"""

import os
import sys
if getattr(sys, 'frozen', False):
    BASEDIR, BASEFILE = os.path.split(os.path.abspath(sys.executable))
else:
    BASEDIR, BASEFILE = os.path.split(os.path.abspath(__file__))
print(BASEDIR, BASEFILE, os.getcwd())
sys.path.insert(0, BASEDIR)
print(sys.path)

import urllib.parse
import urllib.request
import imp
import shutil
from io import StringIO, BytesIO
from tempfile import mkstemp, mkdtemp
import re
import subprocess
import lxml
import calendar
import datetime
import time
import random
import textwrap
from functools import partial
import weakref
import socket
import struct
import sqlite3
import json
import base64
import ipaddress
import ssl
import hashlib
import uuid

from http.server import BaseHTTPRequestHandler, HTTPServer
from socketserver import ThreadingMixIn, TCPServer
import pycurl
from bs4 import BeautifulSoup
import PIL
from PIL import Image, ImageDraw
from PyQt5 import QtCore, QtGui, QtNetwork, QtWidgets
from PyQt5.QtCore import QUrl
from PyQt5.QtCore import pyqtSlot, pyqtSignal

from player_functions import write_files, ccurl, send_notification
from player_functions import wget_string, open_files, get_config_options
from player_functions import get_tmp_dir, naturallysorted, set_logger
from player_functions import get_home_dir, change_opt_file, create_ssl_cert
from player_functions import set_user_password, get_lan_ip
from yt import get_yt_url, get_yt_sub_

HOME_DIR = get_home_dir()
HOME_OPT_FILE = os.path.join(HOME_DIR, 'other_options.txt')
BROWSER_BACKEND = get_config_options(HOME_OPT_FILE, 'BROWSER_BACKEND')
QT_WEB_ENGINE = True
print(BROWSER_BACKEND)
if (not BROWSER_BACKEND or (BROWSER_BACKEND != 'QTWEBKIT' 
        and BROWSER_BACKEND != 'QTWEBENGINE')):
    if os.path.exists(HOME_OPT_FILE) and not BROWSER_BACKEND:
        write_files(HOME_OPT_FILE, 'BROWSER_BACKEND=QTWEBENGINE', line_by_line=True)
    else:
        change_opt_file(HOME_OPT_FILE, 'BROWSER_BACKEND=', 'BROWSER_BACKEND=QTWEBENGINE')
    BROWSER_BACKEND = 'QTWEBENGINE'

if BROWSER_BACKEND == 'QTWEBENGINE':
    try:
        from PyQt5 import QtWebEngineWidgets, QtWebEngineCore
        from PyQt5.QtWebEngineWidgets import QWebEngineView
        from browser import Browser
        from hls_webengine.hls_engine import BrowseUrlT
        QT_WEB_ENGINE = True
        print('Using QTWEBENGINE')
    except Exception as err_msg:
        print(err_msg)
        try:
            from PyQt5 import QtWebKitWidgets
            from PyQt5.QtWebKitWidgets import QWebView
            from browser_webkit import Browser
            from hls_webkit.hls_engine_webkit import BrowseUrlT
            QT_WEB_ENGINE = False
            print('Using QTWEBKIT')
            change_opt_file(HOME_OPT_FILE, 'BROWSER_BACKEND=', 'BROWSER_BACKEND=QTWEBKIT')
            BROWSER_BACKEND = 'QTWEBKIT'
        except Exception as err_msg:
            print(err_msg)
            msg_txt = 'Browser Backend Not Available. Install either QtWebKit or QtWebEngine'
            send_notification(msg_txt)
elif BROWSER_BACKEND == 'QTWEBKIT':
    try:
        from PyQt5 import QtWebKitWidgets
        from PyQt5.QtWebKitWidgets import QWebView
        from browser_webkit import Browser
        from hls_webkit.hls_engine_webkit import BrowseUrlT
        QT_WEB_ENGINE = False
        print('Directly Using QTWEBKIT')
    except:
        msg_txt = 'QTWEBKIT Not Available, Try QTWEBENGINE'
        send_notification(msg_txt)

TMPDIR = get_tmp_dir()

if TMPDIR and not os.path.exists(TMPDIR):
    try:
        os.makedirs(TMPDIR)
    except OSError as e:
        print(e)
        TMPDIR = mkdtemp(suffix=None, prefix='kawaii-player_')
        
logger = set_logger('kawaii-player.log', TMPDIR)

OSNAME=os.name
print(TMPDIR, OSNAME)

try:
    import mutagen
except Exception as e:
    print(e,'--143--')

try:
    import dbus
    import dbus.service
    import dbus.mainloop.pyqt5
    from mpris_dbus import MprisServer
except Exception as e:
    from mpris_nodbus import MprisServer
    print(e, 'No mpris server')

try:
    import libtorrent as lt
    from stream import ThreadServer, TorrentThread, get_torrent_info
    from stream import set_torrent_info, get_torrent_info_magnet
    from stream import set_new_torrent_file_limit, torrent_session_status
    from stream import get_torrent_download_location
except Exception as e:
    print(e, '---156---')
    notify_txt = 'python3 bindings for libtorrent are broken\nTorrent Streaming feature will be disabled'
    send_notification(notify_txt, display='posix')

from settings_widget import LoginAuth
from media_server import ThreadServerLocal
from database import MediaDatabase
from player import PlayerWidget
from widgets.thumbnail import ThumbnailWidget, TitleThumbnailWidget
from widgets.playlist import PlaylistWidget
from widgets.titlelist import TitleListWidget
from widgets.traywidget import SystemAppIndicator, FloatWindowWidget
from widgets.optionwidgets import *
from widgets.scrollwidgets import *
from thread_modules import FindPosterThread, ThreadingThumbnail
from thread_modules import ThreadingExample, DownloadThread
from thread_modules import GetIpThread, YTdlThread, PlayerWaitThread
from thread_modules import DiscoverServer, BroadcastServer, GetServerEpisodeInfo
from stylesheet import WidgetStyleSheet
from serverlib import ServerLib

def set_mainwindow_palette(fanart, first_time=None):
    logger.info('\n{0}:  mainwindow background\n'.format(fanart))
    if not os.path.isfile(fanart) or ui.keep_background_constant:
        fanart = ui.default_background
    if os.path.isfile(fanart):
        if not ui.keep_background_constant or first_time:
            palette	= QtGui.QPalette()
            palette.setBrush(QtGui.QPalette.Background, 
                            QtGui.QBrush(QtGui.QPixmap(fanart)))
            MainWindow.setPalette(palette)
            ui.current_background = fanart


class DoGetSignalNew(QtCore.QObject):
    new_signal = pyqtSignal(str)
    def __init__(self):
        QtCore.QObject.__init__(self)
        self.new_signal.connect(goto_ui_jump)
        
@pyqtSlot(str)
def goto_ui_jump(nm):
    global ui
    url = ui.getdb.epn_return_from_bookmark(nm, from_client=True)


class MainWindowWidget(QtWidgets.QWidget):

    def __init__(self):
        super(MainWindowWidget, self).__init__()

    def mouseMoveEvent(self, event):
        global site, ui
        pos = event.pos()
        px = pos.x()
        x = self.width()
        dock_w = ui.dockWidget_3.width()
        if ui.orientation_dock == 'right':
            if px <= x and px >= x-6:
                ui.dockWidget_3.show()
                ui.btn1.setFocus()
                logger.info('show options sidebar')
            elif px <= x-dock_w and ui.auto_hide_dock:
                ui.dockWidget_3.hide()
                if not ui.list1.isHidden():
                    ui.list1.setFocus()
                elif not ui.list2.isHidden():
                    ui.list2.setFocus()
        else:
            if px >= 0 and px <= 10:
                ui.dockWidget_3.show()
                ui.btn1.setFocus()
                logger.info('show options sidebar')
            elif px >= dock_w and ui.auto_hide_dock:
                ui.dockWidget_3.hide()
                if not ui.list1.isHidden():
                    ui.list1.setFocus()
                elif not ui.list2.isHidden():
                    ui.list2.setFocus()

        if self.isFullScreen() and not ui.tab_5.isHidden():
            logger.info('FullScreen Window but not video')
            ht = self.height()
            if pos.y() <= ht and pos.y() > ht - 5 and ui.frame1.isHidden():
                ui.frame1.show()
                ui.frame1.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
            elif pos.y() <= ht-32 and not ui.frame1.isHidden():
                ui.frame1.hide()


class MyEventFilter(QtCore.QObject):

    def eventFilter(self, receiver, event):
        global tray, MainWindow, ui
        print(event)
        if event.type():
            if(event.type() == QtCore.QEvent.ToolTip):
                pos = event.pos()
                print(pos)
                if MainWindow.isHidden() and ui.float_window.isHidden():
                    tray.right_menu._detach_video()
                return 0
        else:
            #Call Base Class Method to Continue Normal Event Processing
            return super(MyEventFilter, self).eventFilter(receiver, event)


class EventFilterFloatWindow(QtCore.QObject):

    def eventFilter(self, receiver, event):
        global tray, MainWindow, ui
        if event.type():
            #print("event is {0} with id {1}".format(event, event.type()))
            if(event.type() == QtCore.QEvent.Enter):
                if ui.float_timer.isActive():
                    ui.float_timer.stop()
                if ui.new_tray_widget.hasFocus():
                    print('focus')
                else:
                    print('unFocus')
                return 0
            elif(event.type() == QtCore.QEvent.Leave):
                if ui.new_tray_widget.remove_toolbar:
                    if ui.float_timer.isActive():
                        ui.float_timer.stop()
                    ui.float_timer.start(10)
                return 0
            else:
                return super(EventFilterFloatWindow, self).eventFilter(receiver, event)
        else:
            return super(EventFilterFloatWindow, self).eventFilter(receiver, event)


class ScaledLabel(QtWidgets.QLabel):

    def __init__(self, *args, **kwargs):
        QtWidgets.QLabel.__init__(self)
        self._pixmap = QtGui.QPixmap(self.pixmap())

    def resizeEvent(self, event):
        self.setPixmap(self._pixmap.scaled(
        self.width(), self.height(), 
        QtCore.Qt.KeepAspectRatio))


class labelDock(QtWidgets.QLabel):

    def __init__(self, *args, **kwargs):
        QtWidgets.QLabel.__init__(self)
        
    def mouseMoveEvent(self, event):
        logger.info(event.pos())


class Btn1(QtWidgets.QComboBox):
    
    def __init__(self, parent):
        super(Btn1, self).__init__(parent)
        
    def keyPressEvent(self, event):
        global iconv_r
        if event.key() == QtCore.Qt.Key_Right:
            if not ui.list1.isHidden():
                ui.list1.setFocus()
            elif not ui.scrollArea.isHidden():
                ui.scrollArea.setFocus()
            elif not ui.scrollArea1.isHidden():
                ui.scrollArea1.setFocus()
            if ui.auto_hide_dock:
                ui.dockWidget_3.hide()
        elif event.key() == QtCore.Qt.Key_Left:
            if self.currentText() == 'Addons':
                ui.btnAddon.setFocus()
            else:
                ui.list3.setFocus()
        super(Btn1, self).keyPressEvent(event)


class tab6(QtWidgets.QWidget):
    
    def __init__(self, parent):
        super(tab6, self).__init__(parent)
        
    def resizeEvent(self, event):
        global tab_6_size_indicator, total_till, browse_cnt, thumbnail_indicator
        global tab_6_player
        
        if (ui.tab_6.width() > 500 and tab_6_player == "False" 
                    and iconv_r != 1 and not ui.lock_process):
                #browse_cnt = 0
                if tab_6_size_indicator:
                    tab_6_size_indicator.pop()
                tab_6_size_indicator.append(ui.tab_6.width())
                if not ui.scrollArea.isHidden():
                        print('--------resizing----')
                        ui.next_page('not_deleted')
                        QtWidgets.QApplication.processEvents()
                elif not ui.scrollArea1.isHidden():
                        ui.thumbnail_label_update()
                        
    def mouseMoveEvent(self, event):
        print('Tab_6')
        if not ui.scrollArea1.isHidden():
            ui.scrollArea1.setFocus()
        elif not ui.scrollArea.isHidden():
            ui.scrollArea.setFocus()
        
    def keyPressEvent(self, event):
        global Player, wget, cycle_pause, cache_empty, buffering_mplayer
        global curR, pause_indicator, thumbnail_indicator, iconv_r_indicator
        global cur_label_num
        global fullscr, idwMain, idw, quitReally, new_epn, toggleCache
        global site, iconv_r, browse_cnt, total_till, browse_cnt
        global tab_6_size_indicator
        
        if tab_6_size_indicator:
            tab_6_size_indicator.pop()
        tab_6_size_indicator.append(ui.tab_6.width())
        if event.key() == QtCore.Qt.Key_F:
            if tab_6_size_indicator:
                tab_6_size_indicator.pop()
            if self.width() > 500:
                tab_6_size_indicator.append(self.width())
            fullscr = 1 - fullscr
            if not MainWindow.isFullScreen():
                ui.text.hide()
                ui.label.hide()
                ui.frame1.hide()
                ui.goto_epn.hide()
                ui.btn10.hide()
                if wget:
                    if wget.processId() > 0:
                        ui.progress.hide()
                ui.list2.hide()
                ui.list6.hide()
                ui.list1.hide()
                ui.frame.hide()
                ui.gridLayout.setContentsMargins(0, 0, 0, 0)
                ui.gridLayout.setSpacing(0)
                ui.superGridLayout.setContentsMargins(0, 0, 0, 0)
                ui.gridLayout1.setContentsMargins(0, 0, 0, 0)
                ui.gridLayout1.setSpacing(10)
                ui.gridLayout2.setContentsMargins(0, 0, 0, 0)
                ui.gridLayout2.setSpacing(10)
                ui.horizontalLayout10.setContentsMargins(0, 0, 0, 0)
                ui.horizontalLayout10.setSpacing(0)
                ui.tab_6.show()
                ui.tab_6.setFocus()
                MainWindow.showFullScreen()
            else:
                ui.gridLayout.setSpacing(5)
                ui.superGridLayout.setContentsMargins(5, 5, 5, 5)
                ui.gridLayout1.setSpacing(10)
                ui.gridLayout1.setContentsMargins(10, 10, 10, 10)
                ui.gridLayout2.setSpacing(10)
                ui.gridLayout2.setContentsMargins(10, 10, 10, 10)
                ui.horizontalLayout10.setContentsMargins(10, 10, 10, 10)
                ui.horizontalLayout10.setSpacing(10)
                if wget:
                    if wget.processId() > 0:
                        ui.goto_epn.hide()
                        ui.progress.show()
                MainWindow.showNormal()
                MainWindow.showMaximized()
        

class QDockNew(QtWidgets.QDockWidget):
    
    def __init__(self, parent):
        global cycle_pause
        super(QDockNew, self).__init__(parent)
        
    def mouseReleaseEvent(self, ev):
        if ev.button() == QtCore.Qt.LeftButton:
            self.hide()
            ui.list4.hide()


try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s


try:
    _encoding = QtWidgets.QApplication.UnicodeUTF8
    def _translate(context, text, disambig):
        return QtWidgets.QApplication.translate(context, text, disambig, _encoding)
except AttributeError:
    def _translate(context, text, disambig):
        return QtWidgets.QApplication.translate(context, text, disambig)


class Ui_MainWindow(object):
    def setupUi(self, MainWindow, media_data=None, home_val=None,
                scr_width=None, scr_height=None):
        global BASEDIR, screen_width, screen_height, home
        MainWindow.setObjectName(_fromUtf8("MainWindow"))
        #MainWindow.resize(875, 600)
        if media_data is not None:
            self.media_data = media_data
        if home_val is not None:
            home = home_val
        if scr_width is not None:
            screen_width = scr_width
        if scr_height is not None:
            screen_height = scr_height
        icon_path = os.path.join(BASEDIR, 'tray.png')
        if not os.path.exists(icon_path):
            icon_path = '/usr/share/kawaii-player/tray.png'
        if os.path.exists(icon_path):
            icon = QtGui.QIcon(icon_path)
        else:
            icon = QtGui.QIcon("")
        MainWindow.setWindowIcon(icon)
        self.superTab = QtWidgets.QWidget(MainWindow)
        self.superTab.setObjectName(_fromUtf8("superTab"))
        self.superGridLayout = QtWidgets.QGridLayout(MainWindow)
        self.superGridLayout.setObjectName(_fromUtf8("superGridLayout"))
        self.gridLayout = QtWidgets.QGridLayout(self.superTab)
        #self.gridLayout.setMouseTracking(True)
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.superTab.setMouseTracking(True)
        self.superGridLayout.addWidget(self.superTab, 0, 1, 1, 1)
        self.superGridLayout.setContentsMargins(5, 5, 5, 5)
        self.superGridLayout.setSpacing(0)
        self.gridLayout.setSpacing(5)
        self.gridLayout.setContentsMargins(5, 5, 5, 5)
        
        self.horizontalLayout_7 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_7.setObjectName(_fromUtf8("horizontalLayout_7"))
        self.gridLayout.addLayout(self.horizontalLayout_7, 1, 0, 1, 1)
        
        self.VerticalLayoutLabel = QtWidgets.QHBoxLayout()
        self.VerticalLayoutLabel.setObjectName(_fromUtf8("VerticalLayoutLabel"))
        self.gridLayout.addLayout(self.VerticalLayoutLabel, 0, 1, 1, 1)
        
        
        self.verticalLayout_40 = QtWidgets.QVBoxLayout()
        self.verticalLayout_40.setObjectName(_fromUtf8("verticalLayout_40"))
        self.gridLayout.addLayout(self.verticalLayout_40, 0, 2, 1, 1)
        
        self.verticalLayout_50 = QtWidgets.QVBoxLayout()
        self.verticalLayout_50.setObjectName(_fromUtf8("verticalLayout_50"))
        self.gridLayout.addLayout(self.verticalLayout_50, 0, 3, 1, 1)
        
        
        self.label = ThumbnailWidget(MainWindow)
        self.label.setup_globals(MainWindow, self, home, TMPDIR,
                                 logger, screen_width, screen_height)
        #self.label.setSizePolicy(sizePolicy)
        
        #self.label.setMinimumSize(QtCore.QSize(300, 250))
        self.label.setText(_fromUtf8(""))
        #self.label.setScaledContents(True)
        self.label.setObjectName(_fromUtf8("label"))
        #self.text = QtWidgets.QTextBrowser(MainWindow)
        self.text = QtWidgets.QTextEdit(MainWindow)
        self.text.setAcceptRichText(False)
        self.text.setObjectName(_fromUtf8("text"))
        self.text.copyAvailable.connect(self.text_editor_changed)
        self.text_save_btn = QtWidgets.QPushButton(MainWindow)
        self.text_save_btn.setText('Save')
        self.text_save_btn.setMinimumSize(QtCore.QSize(30, 25))
        self.text_save_btn.clicked.connect(self.save_text_edit)
        self.text_save_btn.hide()
        self.text_save_btn_timer = QtCore.QTimer()
        #self.text.setMaximumSize(QtCore.QSize(450, 250))
        #self.text.setMinimumSize(QtCore.QSize(450, 250))
        self.text_save_btn_timer.timeout.connect(self.text_save_btn_hide)
        self.text_save_btn_timer.setSingleShot(True)
        
        self.text.lineWrapMode()
        #self.VerticalLayoutLabel.setStretch(2, 1)
        self.VerticalLayoutLabel.insertWidget(0, self.label, 0)
        self.VerticalLayoutLabel.insertWidget(1, self.text, 0)
        #self.VerticalLayoutLabel.setStretch(1, 2)
        self.VerticalLayoutLabel.addStretch(1)
        #self.text.hide()
        self.label.setAlignment(QtCore.Qt.AlignCenter|QtCore.Qt.AlignBottom)
        self.text.setAlignment(QtCore.Qt.AlignCenter)
        self.VerticalLayoutLabel.setAlignment(QtCore.Qt.AlignLeft|QtCore.Qt.AlignBottom)
        self.VerticalLayoutLabel.setSpacing(5)
        self.VerticalLayoutLabel.setContentsMargins(0, 0, 0, 0)
        
        self.list1 = TitleListWidget(MainWindow, self, home, TMPDIR, logger)
        self.list1.setObjectName(_fromUtf8("list1"))
        #self.list1.setMaximumSize(QtCore.QSize(400, 16777215))
        self.list1.setMouseTracking(True)
        #self.list1.setMinimumSize(QtCore.QSize(450, 16777215))
        self.verticalLayout_40.insertWidget(0, self.list1, 0)
        
        self.btnEpnList = QtWidgets.QComboBox(MainWindow)
        self.btnEpnList.setObjectName(_fromUtf8("btnEpnList"))
        self.verticalLayout_40.addWidget(self.btnEpnList)
        self.btnEpnList.hide()
        #self.btnEpnList.setMaximumSize(QtCore.QSize(350, 16777215))
        ###################################
        #self.list2 = QtGui.QListWidget(self.tab)
        self.list2 = PlaylistWidget(MainWindow, self, home, TMPDIR, logger)
        self.list2.setObjectName(_fromUtf8("list2"))
        #self.list2.setMaximumSize(QtCore.QSize(400, 16777215))
        self.list2.setMouseTracking(True)
        
        self.verticalLayout_40.setAlignment(QtCore.Qt.AlignBottom)
        
        #self.verticalLayout_50.insertWidget(0, self.list1, 0)
        self.verticalLayout_50.insertWidget(0, self.list2, 0)
        #self.verticalLayout_50.insertWidget(2, self.text, 0)
        #self.verticalLayout_50.insertWidget(3, self.label, 0)
        self.verticalLayout_50.setAlignment(QtCore.Qt.AlignBottom)
        
        self.list4 = FilterTitleList(MainWindow, self, home)
        self.list4.setObjectName(_fromUtf8("list4"))
        #self.list4.setMaximumSize(QtCore.QSize(400, 16777215))
        self.list4.setMouseTracking(True)
        
        self.list4.hide()
        
        self.list5 = FilterPlaylist(MainWindow, self, home, logger)
        self.list5.setObjectName(_fromUtf8("list5"))
        #self.list4.setMaximumSize(QtCore.QSize(400, 16777215))
        self.list5.setMouseTracking(True)
        self.verticalLayout_50.insertWidget(1, self.list5, 0)
        self.list5.hide()
        
        self.list6 = QueueListWidget(MainWindow, self, home)
        self.list6.setObjectName(_fromUtf8("list6"))
        #self.list4.setMaximumSize(QtCore.QSize(400, 16777215))
        self.list6.setMouseTracking(True)
        self.verticalLayout_50.insertWidget(2, self.list6, 0)
        self.list6.hide()
        self.list6.addItem("Queue Empty:\nSelect Item and Press 'Q' to EnQueue it.\nIf Queue List is Empty then Items Will be\nPlayed Sequentially as per Playlist.\n(Queue Feature Works Only With\n Local/Offline Content)\n\nSelect Item and Press 'W' to toggle \nwatch/unwatch status\n")
        #self.gridLayout.addWidget(self.list2, 0, 2, 1, 1)
        self.frame = QtWidgets.QFrame(MainWindow)
        #self.frame.setMinimumSize(QtCore.QSize(500, 22))
        self.frame.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.frame.setFrameShadow(QtWidgets.QFrame.Raised)
        self.frame.setObjectName(_fromUtf8("frame"))
        self.horizontalLayout_3 = QtWidgets.QHBoxLayout(self.frame)
        self.horizontalLayout_3.setObjectName(_fromUtf8("horizontalLayout_3"))
        
        self.backward = QtWidgets.QPushButton(self.frame)
        self.backward.setObjectName(_fromUtf8("backward"))
        self.horizontalLayout_3.addWidget(self.backward)
        
        self.hide_btn_list1 = QtWidgets.QPushButton(self.frame)
        self.hide_btn_list1.setObjectName(_fromUtf8("hide_btn_list1"))
        
        self.hide_btn_list1.setMinimumHeight(30)
        self.hide_btn_list1_menu = QtWidgets.QMenu()
        self.hide_btn_menu_option = ['Sort', 'Shuffle']
        self.action_player_menu2 =[]
        for i in self.hide_btn_menu_option:
            self.action_player_menu2.append(
                self.hide_btn_list1_menu.addAction(i, lambda x=i:self.playerPlaylist1(x)))
                
        self.hide_btn_list1.setMenu(self.hide_btn_list1_menu)
        self.hide_btn_list1.setCheckable(True)
        self.hide_btn_list1.setText('Order')
        self.filter_btn = QtWidgets.QPushButton(self.frame)
        self.filter_btn.setObjectName(_fromUtf8("filter_btn"))
        
        self.filter_btn.setMinimumHeight(30)
        self.filter_btn.hide()
        #self.go_page = QtGui.QLineEdit(self.frame)
        
        self.page_number = QtWidgets.QLineEdit(self.frame)
        self.page_number.setObjectName(_fromUtf8("page_number"))
        
        self.page_number.setMaximumWidth(48)
        self.page_number.setMinimumHeight(30)
        
        self.go_page = QLineCustom(self.frame)
        self.go_page.setObjectName(_fromUtf8("go_page"))
        self.go_page.setMinimumHeight(30)
        self.go_page.setPlaceholderText('Filter')
        #self.go_page.hide()
        
        self.forward = QtWidgets.QPushButton(self.frame)
        self.forward.setObjectName(_fromUtf8("forward"))
        self.horizontalLayout_3.addWidget(self.forward)
        self.forward.hide()
        self.backward.hide()
        
        self.horizontalLayout_3.insertWidget(2, self.page_number, 0)
        self.horizontalLayout_3.insertWidget(3, self.go_page, 0)
        self.horizontalLayout_3.insertWidget(4, self.filter_btn, 0)
        self.horizontalLayout_3.insertWidget(5, self.hide_btn_list1, 0)
        
        self.goto_epn = QtWidgets.QFrame(MainWindow)
        self.goto_epn.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.goto_epn.setFrameShadow(QtWidgets.QFrame.Raised)
        self.goto_epn.setObjectName(_fromUtf8("goto_epn"))
        self.horizontalLayout_goto_epn = QtWidgets.QHBoxLayout(self.goto_epn)
        self.horizontalLayout_goto_epn.setObjectName(_fromUtf8("horizontalLayout_goto_epn"))
        self.horizontalLayout_goto_epn.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout_goto_epn.setSpacing(5)
        #self.gridLayout.addWidget(self.goto_epn, 1, 2, 1, 1)
        self.horizontalLayout_3.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout_3.setSpacing(5)
        
        self.goto_epn.hide()
        self.frame.hide()
        
        #self.progress = QtWidgets.QProgressBar(MainWindow)
        self.progress = QProgressBarCustom(MainWindow, self)
        self.progress.setObjectName(_fromUtf8("progress"))
        #self.gridLayout.addWidget(self.progress, 1, 3, 1, 1)
        self.verticalLayout_50.insertWidget(3, self.progress, 0)
        self.progress.setMinimum(0)
        self.progress.setMaximum(100)
        self.progress.setTextVisible(True)
        self.progress.hide()
        self.progress.setToolTip("Click for more options")
        self.player_buttons = {
            'play':'\u25B8', 'pause':'\u2225', 'stop':'\u25FE', 
            'prev':'\u2190', 'next':'\u2192', 'lock':'\u21BA', 
            'unlock':'\u21C4', 'quit':'\u2127', 'attach':'\u2022', 
            'left':'\u21A2', 'right':'\u21A3', 'pr':'\u226A', 
            'nxt':'\u226B', 'min':'\u2581', 'max':'\u25A2', 
            'close':'\u2715', 'resize':'M', 'up':'\u21E1', 
            'down':'\u21E3', 'browser':'\u25CC'
            }
                                
        self.check_symbol = '\u2714'
        self.torrent_frame = QtWidgets.QFrame(MainWindow)
        self.torrent_frame.setMaximumSize(QtCore.QSize(300, 16777215))
        self.torrent_frame.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.torrent_frame.setFrameShadow(QtWidgets.QFrame.Raised)
        self.torrent_frame.setObjectName(_fromUtf8("torrent_frame"))
        self.verticalLayout_50.insertWidget(4, self.torrent_frame, 0)
        self.horizontalLayout_torrent_frame = QtWidgets.QHBoxLayout(self.torrent_frame)
        self.horizontalLayout_torrent_frame.setContentsMargins(0, 2, 0, 2)
        self.horizontalLayout_torrent_frame.setSpacing(2)
        self.horizontalLayout_torrent_frame.setObjectName(_fromUtf8("horizontalLayout_torrent_frame"))
        self.torrent_frame.hide()
        
        self.label_torrent_stop = QtWidgets.QPushButton(self.torrent_frame)
        self.label_torrent_stop.setObjectName(_fromUtf8("label_torrent_stop"))
        self.label_torrent_stop.setText(self.player_buttons['stop'])
        self.label_torrent_stop.setMinimumWidth(24)
        self.horizontalLayout_torrent_frame.insertWidget(0, self.label_torrent_stop, 0)
        #self.label_torrent_stop.setToolTip("Stop Torrent")
        
        self.label_down_speed = QtWidgets.QLineEdit(self.torrent_frame)
        self.label_down_speed.setObjectName(_fromUtf8("label_down_speed"))
        self.label_down_speed.setToolTip("Set Download Speed Limit For Current Session in KB\nEnter Only Integer Values")
        self.horizontalLayout_torrent_frame.insertWidget(1, self.label_down_speed, 0)
        #self.label_down_speed.setMaximumWidth(100)
        self.label_up_speed = QtWidgets.QLineEdit(self.torrent_frame)
        self.label_up_speed.setObjectName(_fromUtf8("label_up_speed"))
        self.label_up_speed.setToolTip("Set Upload Speed Limit in KB for Current Session\nEnter Only Integer Values")
        self.horizontalLayout_torrent_frame.insertWidget(2, self.label_up_speed, 0)
        
        self.frame1 = QtWidgets.QFrame(MainWindow)
        self.frame1.setMaximumSize(QtCore.QSize(10000, 32))
        self.frame1.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.frame1.setFrameShadow(QtWidgets.QFrame.Raised)
        self.frame1.setObjectName(_fromUtf8("frame1"))
        self.horizontalLayout_31 = QtWidgets.QVBoxLayout(self.frame1)
        self.horizontalLayout_31.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout_31.setSpacing(0)
        self.horizontalLayout_31.setObjectName(_fromUtf8("horizontalLayout_31"))
        #self.gridLayout.addWidget(self.frame1, 1, 0, 1, 1)
        
        self.frame2 = QtWidgets.QFrame(MainWindow)
        self.frame2.setMaximumSize(QtCore.QSize(10000, 32))
        self.frame2.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.frame2.setFrameShadow(QtWidgets.QFrame.Raised)
        self.frame2.setObjectName(_fromUtf8("frame2"))
        self.horizontalLayout_101= QtWidgets.QHBoxLayout(self.frame2)
        self.horizontalLayout_101.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout_101.setSpacing(10)
        self.horizontalLayout_101.setObjectName(_fromUtf8("horizontalLayout_101"))
        #self.gridLayout.addWidget(self.frame1, 1, 0, 1, 1)
    
        
        self.progressEpn = QtWidgets.QProgressBar(self.frame1)
        self.progressEpn.setObjectName(_fromUtf8("progressEpn"))
        #self.gridLayout.addWidget(self.progressEpn, 1, 0, 1, 1)
        self.progressEpn.setMinimum(0)
        self.progressEpn.setMaximum(100)
        self.progressEpn.setMaximumSize(QtCore.QSize(10000, 32))
        self.progressEpn.setTextVisible(True)
        
        self.slider = MySlider(self.frame1, self, home)
        self.slider.setObjectName(_fromUtf8("slider"))
        self.slider.setOrientation(QtCore.Qt.Horizontal)
        
        self.slider.setRange(0, 100)
        self.slider.setMouseTracking(True)
        try:
            aspect = (screen_width/screen_height)
        except NameError:
            screen_width = 800
            screen_height = 400
            aspect = (screen_width/screen_height)
            home = os.path.join(os.path.expanduser('~'), '.config', 'kawaii_player_test')
            if not os.path.exists(home):
                os.makedirs(home)
        self.width_allowed = int((screen_width)/4.5)
        self.height_allowed = (self.width_allowed/aspect) #int((screen_height)/3.3)
        self.image_aspect_allowed = (self.width_allowed/self.height_allowed)
        print(self.width_allowed, '--width--allowed--')
        self.list1.setMaximumWidth(self.width_allowed)
        self.list2.setMaximumWidth(self.width_allowed)
        self.list2.setIconSize(QtCore.QSize(128, 128))
        self.frame.setMaximumWidth(self.width_allowed)
        self.list4.setMaximumWidth(self.width_allowed)
        self.list5.setMaximumWidth(self.width_allowed)
        self.list6.setMaximumWidth(self.width_allowed)
        self.goto_epn.setMaximumWidth(self.width_allowed)
        self.text.setMaximumWidth(screen_width-2*self.width_allowed-280)
        self.text.setMaximumHeight(self.height_allowed)
        self.text.setMinimumWidth(self.width_allowed)
        self.label.setMaximumHeight(self.height_allowed)
        self.label.setMinimumHeight(self.height_allowed)
        self.label.setMaximumWidth(self.width_allowed)
        self.label.setMinimumWidth(self.width_allowed)
        self.progress.setMaximumSize(QtCore.QSize(self.width_allowed, 16777215))
        self.thumbnail_video_width = int(self.width_allowed*2.5)
        #self.label.setMaximumSize(QtCore.QSize(280, 250))
        #self.label.setMinimumSize(QtCore.QSize(280, 250))
        
        self.list1.setWordWrap(True)
        self.list1.setTextElideMode(QtCore.Qt.ElideRight)
        self.list2.setWordWrap(True)
        self.list2.setTextElideMode(QtCore.Qt.ElideRight)
        self.list4.setWordWrap(True)
        self.list4.setTextElideMode(QtCore.Qt.ElideRight)
        self.list5.setWordWrap(True)
        self.list5.setTextElideMode(QtCore.Qt.ElideRight)
        self.list6.setWordWrap(True)
        self.list6.setTextElideMode(QtCore.Qt.ElideRight)
        
        #self.gridLayout.setAlignment(QtCore.Qt.AlignLeft)#Can cause video disappear in fullscreen mode
        #self.superGridLayout.setAlignment(QtCore.Qt.AlignRight)Can cause video disappear in fullscreen mode
        #self.verticalLayout_40.insertWidget(1, self.frame, 0)
        
        self.player_opt = QtWidgets.QFrame(self.frame1)
        self.player_opt.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.player_opt.setFrameShadow(QtWidgets.QFrame.Raised)
        self.player_opt.setObjectName(_fromUtf8("player_opt"))
        self.horizontalLayout_player_opt = QtWidgets.QHBoxLayout(self.player_opt)
        self.horizontalLayout_player_opt.setObjectName(_fromUtf8("horizontalLayout_player_opt"))
        self.horizontalLayout_player_opt.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout_player_opt.setSpacing(0)
        self.horizontalLayout_31.insertWidget(0, self.player_opt, 0)
        self.horizontalLayout_31.insertWidget(1, self.progressEpn, 0)
        self.horizontalLayout_31.insertWidget(2, self.slider, 0)
        
        self.player_opt_toolbar= QtWidgets.QPushButton(self.player_opt)
        self.player_opt_toolbar.setObjectName(_fromUtf8("player_opt_toolbar"))
        self.horizontalLayout_player_opt.insertWidget(0, self.player_opt_toolbar, 0)
        self.player_opt_toolbar.setText("Options")
        self.player_opt_toolbar.setToolTip('Shift+G')
        
        self.sd_hd = QtWidgets.QPushButton(self.player_opt)
        self.sd_hd.setObjectName(_fromUtf8("sd_hd"))
        self.horizontalLayout_player_opt.insertWidget(1, self.sd_hd, 0)
        self.sd_hd.setText("SD")
        
        self.audio_track = QtWidgets.QPushButton(self.player_opt)
        self.audio_track.setObjectName(_fromUtf8("audio_track"))
        self.horizontalLayout_player_opt.insertWidget(2, self.audio_track, 0)
        self.audio_track.setText("A/V")
        self.audio_track.setToolTip('Toggle Audio (K)')
        
        self.subtitle_track = QtWidgets.QPushButton(self.player_opt)
        self.subtitle_track.setObjectName(_fromUtf8("subtitle_track"))
        self.horizontalLayout_player_opt.insertWidget(3, self.subtitle_track, 0)
        self.subtitle_track.setText("SUB")
        self.subtitle_track.setToolTip('Toggle Subtitle (J)')
        
        self.player_loop_file = QtWidgets.QPushButton(self.player_opt)
        self.player_loop_file.setObjectName(_fromUtf8("player_loop_file"))
        self.horizontalLayout_player_opt.insertWidget(4, self.player_loop_file, 0)
        self.player_loop_file.setText(self.player_buttons['unlock'])
        self.player_loop_file.setToolTip('Lock/unLock File (L)')
        #self.player_loop_file.hide()
        
        self.player_stop = QtWidgets.QPushButton(self.player_opt)
        self.player_stop.setObjectName(_fromUtf8("player_stop"))
        self.horizontalLayout_player_opt.insertWidget(5, self.player_stop, 0)
        self.player_stop.setText(self.player_buttons['stop'])
        
        self.player_play_pause = QtWidgets.QPushButton(self.player_opt)
        self.player_play_pause.setObjectName(_fromUtf8("player_play_pause"))
        self.horizontalLayout_player_opt.insertWidget(6, self.player_play_pause, 0)
        self.player_play_pause.setText(self.player_buttons['play'])
        
        self.player_prev = QtWidgets.QPushButton(self.player_opt)
        self.player_prev.setObjectName(_fromUtf8("player_prev"))
        self.horizontalLayout_player_opt.insertWidget(7, self.player_prev, 0)
        self.player_prev.setText(self.player_buttons['prev'])
        self.player_prev.setToolTip('<')
        
        self.player_next = QtWidgets.QPushButton(self.player_opt)
        self.player_next.setObjectName(_fromUtf8("player_next"))
        self.horizontalLayout_player_opt.insertWidget(8, self.player_next, 0)
        self.player_next.setText(self.player_buttons['next'])
        self.player_next.setToolTip('>')
        
        
        
        self.player_showhide_title_list = QtWidgets.QPushButton(self.player_opt)
        self.player_showhide_title_list.setObjectName(_fromUtf8("player_showhide_title_list"))
        self.horizontalLayout_player_opt.insertWidget(9, self.player_showhide_title_list, 0)
        self.player_showhide_title_list.setText('T')
        self.player_showhide_title_list.clicked.connect(lambda x=0:self.playerPlaylist("Show/Hide Title List"))
        self.player_showhide_title_list.setToolTip('Show/Hide Title List')
        
        self.player_showhide_playlist = QtWidgets.QPushButton(self.player_opt)
        self.player_showhide_playlist.setObjectName(_fromUtf8("player_showhide_playlist"))
        self.horizontalLayout_player_opt.insertWidget(10, self.player_showhide_playlist, 0)
        #self.player_showhide_playlist.setText('\u2118')
        self.player_showhide_playlist.setText('PL')
        self.player_showhide_playlist.clicked.connect(
            lambda x=0:self.playerPlaylist("Show/Hide Playlist"))
        self.player_showhide_playlist.setToolTip('Show/Hide Playlist')
        
        self.queue_manage = QtWidgets.QPushButton(self.goto_epn)
        self.queue_manage.setObjectName(_fromUtf8("queue_manage"))
        self.horizontalLayout_player_opt.insertWidget(11, self.queue_manage, 0)
        self.queue_manage.setText("Q")
        self.queue_manage.setToolTip('Show/Hide Queue')
        #self.queue_manage.setMinimumWidth(30)
        self.queue_manage.clicked.connect(self.queue_manage_list)
        
        self.player_filter = QtWidgets.QPushButton(self.player_opt)
        self.player_filter.setObjectName(_fromUtf8("player_filter"))
        self.horizontalLayout_player_opt.insertWidget(12, self.player_filter, 0)
        self.player_filter.setText('Y')
        self.player_filter.setToolTip('Show/Hide Filter and other options (Ctrl+F)')
        self.player_filter.clicked.connect(self.show_hide_filter_toolbar)
        
        self.btnWebHide = QtWidgets.QPushButton(self.player_opt)
        self.btnWebHide.setObjectName(_fromUtf8("btnWebHide"))
        
        self.horizontalLayout_player_opt.insertWidget(13, self.btnWebHide, 0)
        self.btnWebHide.setText(self.player_buttons['browser'])
        self.btnWebHide.clicked.connect(self.webHide)
        self.btnWebHide.setToolTip('Show/Hide Browser (Ctrl+X)')
        
        self.player_playlist = QtWidgets.QPushButton(self.player_opt)
        self.player_playlist.setObjectName(_fromUtf8("player_playlist"))
        self.horizontalLayout_player_opt.insertWidget(14, self.player_playlist, 0)
        self.player_playlist.setText("More")
        self.player_menu = QtWidgets.QMenu()
        self.player_menu_option = [
                'Show/Hide Video', 'Show/Hide Cover And Summary', 
                'Lock Playlist', 'Shuffle', 'Stop After Current File', 
                'Continue(default Mode)', 'Set Media Server User/PassWord', 
                'Start Media Server', 'Broadcast Server', 'Turn ON Remote Control', 
                'Set Current Background As Default', 'Settings'
                ]
                                
        self.action_player_menu =[]
        for i in self.player_menu_option:
            self.action_player_menu.append(
                self.player_menu.addAction(i, lambda x=i:self.playerPlaylist(x)))
                
        
        self.player_seek_10 = QtWidgets.QPushButton(self.player_opt)
        self.player_seek_10.setObjectName(_fromUtf8("player_seek_10"))
        self.horizontalLayout_player_opt.insertWidget(15, self.player_seek_10, 0)
        self.player_seek_10.setText('+10s')
        self.player_seek_10.clicked.connect(lambda x=0: self.seek_to_val(10))
        self.player_seek_10.hide()
        
        self.player_seek_10_ = QtWidgets.QPushButton(self.player_opt)
        self.player_seek_10_.setObjectName(_fromUtf8("player_seek_10_"))
        self.horizontalLayout_player_opt.insertWidget(16, self.player_seek_10_, 0)
        self.player_seek_10_.setText('-10s')
        self.player_seek_10_.clicked.connect(lambda x=0: self.seek_to_val(-10))
        self.player_seek_10_.hide()
        
        self.player_vol_5 = QtWidgets.QPushButton(self.player_opt)
        self.player_vol_5.setObjectName(_fromUtf8("player_vol_5"))
        self.horizontalLayout_player_opt.insertWidget(17, self.player_vol_5, 0)
        self.player_vol_5.setText('+5')
        self.player_vol_5.clicked.connect(lambda x=0: self.seek_to_vol_val(5))
        self.player_vol_5.hide()
        
        self.player_vol_5_ = QtWidgets.QPushButton(self.player_opt)
        self.player_vol_5_.setObjectName(_fromUtf8("player_vol_5_"))
        self.horizontalLayout_player_opt.insertWidget(18, self.player_vol_5_, 0)
        self.player_vol_5_.setText('-5')
        self.player_vol_5_.clicked.connect(lambda x=0: self.seek_to_vol_val(-5))
        self.player_vol_5_.hide()
        
        self.player_fullscreen = QtWidgets.QPushButton(self.player_opt)
        self.player_fullscreen.setObjectName(_fromUtf8("player_fullscreen"))
        self.horizontalLayout_player_opt.insertWidget(19, self.player_fullscreen, 0)
        self.player_fullscreen.setText('F')
        self.player_fullscreen.clicked.connect(self.remote_fullscreen)
        self.player_fullscreen.hide()
        
        self.player_seek_60 = QtWidgets.QPushButton(self.player_opt)
        self.player_seek_60.setObjectName(_fromUtf8("player_seek_60"))
        self.horizontalLayout_player_opt.insertWidget(20, self.player_seek_60, 0)
        self.player_seek_60.setText('60s')
        self.player_seek_60.clicked.connect(lambda x=0: self.seek_to_val(60))
        self.player_seek_60.hide()
        
        self.player_seek_60_ = QtWidgets.QPushButton(self.player_opt)
        self.player_seek_60_.setObjectName(_fromUtf8("player_seek_60_"))
        self.horizontalLayout_player_opt.insertWidget(21, self.player_seek_60_, 0)
        self.player_seek_60_.setText('-60s')
        self.player_seek_60_.clicked.connect(lambda x=0: self.seek_to_val(-60))
        self.player_seek_60_.hide()
        
        self.player_seek_5m = QtWidgets.QPushButton(self.player_opt)
        self.player_seek_5m.setObjectName(_fromUtf8("player_seek_5m"))
        self.horizontalLayout_player_opt.insertWidget(22, self.player_seek_5m, 0)
        self.player_seek_5m.setText('5m')
        self.player_seek_5m.clicked.connect(lambda x=0: self.seek_to_val(300))
        self.player_seek_5m.hide()
        
        self.player_seek_5m_ = QtWidgets.QPushButton(self.player_opt)
        self.player_seek_5m_.setObjectName(_fromUtf8("player_seek_5m_"))
        self.horizontalLayout_player_opt.insertWidget(23, self.player_seek_5m_, 0)
        self.player_seek_5m_.setText('-5m')
        self.player_seek_5m_.clicked.connect(lambda x=0: self.seek_to_val(-300))
        self.player_seek_5m_.hide()
        
        self.player_show_btn = QtWidgets.QPushButton(self.player_opt)
        self.player_show_btn.setObjectName(_fromUtf8("player_show_btn"))
        self.horizontalLayout_player_opt.insertWidget(24, self.player_show_btn, 0)
        self.player_show_btn.setText('Show')
        self.player_show_btn.clicked.connect(MainWindow.show)
        self.player_show_btn.hide()
        
        self.player_hide_btn = QtWidgets.QPushButton(self.player_opt)
        self.player_hide_btn.setObjectName(_fromUtf8("player_hide_btn"))
        self.horizontalLayout_player_opt.insertWidget(25, self.player_hide_btn, 0)
        self.player_hide_btn.setText('Hide')
        self.player_hide_btn.clicked.connect(MainWindow.hide)
        self.player_hide_btn.hide()
        
        self.player_playlist.setMenu(self.player_menu)
        self.player_playlist.setCheckable(True)
        
        self.mirror_change = QtWidgets.QPushButton(self.goto_epn)
        self.mirror_change.setObjectName(_fromUtf8("mirror_change"))
        self.horizontalLayout_goto_epn.insertWidget(1, self.mirror_change, 0)
        self.mirror_change.setText("Mirror")
        self.mirror_change.hide()
        
        self.goto_epn_filter = QtWidgets.QPushButton(self.goto_epn)
        self.goto_epn_filter.setObjectName(_fromUtf8("Filter Button"))
        self.horizontalLayout_goto_epn.insertWidget(2, self.goto_epn_filter, 0)
        self.goto_epn_filter.setText("Filter")
        self.goto_epn_filter.hide()
        
        self.goto_epn_filter_txt = QLineCustomEpn(self.goto_epn)
        self.goto_epn_filter_txt.setObjectName(_fromUtf8("Filter Text"))
        self.horizontalLayout_goto_epn.insertWidget(3, self.goto_epn_filter_txt, 0)
        self.goto_epn_filter_txt.setPlaceholderText("Filter")
        #self.goto_epn_filter_txt.hide()
        
        self.player_playlist1 = QtWidgets.QPushButton(self.goto_epn)
        self.player_playlist1.setObjectName(_fromUtf8("player_playlist1"))
        self.horizontalLayout_goto_epn.insertWidget(4, self.player_playlist1, 0)
        self.player_playlist1.setText("Order")
        self.player_menu1 = QtWidgets.QMenu()
        self.player_menu_option1 = [
            'Order by Name(Ascending)', 'Order by Name(Descending)', 
            'Order by Date(Ascending)', 'Order by Date(Descending)'
            ]
        self.action_player_menu1 =[]
        for i in self.player_menu_option1:
            self.action_player_menu1.append(
                self.player_menu1.addAction(i, lambda x=i: self.playerPlaylist(x)))
            
        self.player_playlist1.setMenu(self.player_menu1)
        self.player_playlist1.setCheckable(True)
        
        self.frame1.setMinimumHeight(60)
        self.frame.setMinimumHeight(30)
        self.goto_epn.setMinimumHeight(30)
        self.frame1.setMaximumHeight(60)
        self.frame.setMaximumHeight(30)
        self.goto_epn.setMaximumHeight(30)
        
        self.mirror_change.setMaximumHeight(30)
        self.player_playlist1.setMaximumHeight(30)
        self.backward.setMaximumHeight(30)
        self.forward.setMaximumHeight(30)
        self.goto_epn_filter.setMaximumHeight(30)
        self.goto_epn_filter_txt.setMaximumHeight(30)
        self.queue_manage.setMaximumWidth(30)
        self.queue_manage.setMaximumHeight(30)
        
        #self.frame.setMaximumWidth(300)
        #self.tabWidget1.addTab(self.tab_2, _fromUtf8(""))
        self.tab_5 = PlayerWidget(MainWindow, ui=self, logr= logger, tmp=TMPDIR)
        #self.tab_5 = tab5(None)
        self.tab_5.setObjectName(_fromUtf8("tab_5"))
        #self.tabWidget1.addTab(self.tab_5, _fromUtf8(""))
        self.gridLayout.addWidget(self.tab_5, 0, 1, 1, 1)
        self.tab_5.setMouseTracking(True)
        #self.tab_5.setMaximumSize(100000, 100000)
        #self.VerticalLayoutLabel.insertWidget(1, self.tab_5, 0)
        self.tab_5.hide()
        #self.tab_5.setMinimumSize(100, 100)
        #self.tab_6 = QtGui.QWidget(MainWindow)
        self.tab_6 = tab6(MainWindow)
        self.tab_6.setMouseTracking(True)
        #self.tab_6 = QtGui.QWidget()
        #self.gridLayout.addWidget(self.tab_6)
        #ui.gridLayout.addWidget(ui.tab_6, 0, 4, 1, 1)
        self.tab_6.setObjectName(_fromUtf8("tab_6"))
        #self.tabWidget1.addTab(self.tab_6, _fromUtf8(""))
        self.tab_6.hide()
        self.tab_2 = QtWidgets.QWidget()
        self.tab_2.setObjectName(_fromUtf8("tab_2"))
        self.gridLayout.addWidget(self.tab_2, 0, 2, 1, 1)
        #self.superGridLayout.addWidget(self.tab_2, 2, 1, 1, 1)
        self.gridLayout.addWidget(self.tab_6, 0, 1, 1, 1)
        self.tab_2.hide()
        
        self.dockWidget_3 = QtWidgets.QFrame(MainWindow)
        self.dock_vert = QtWidgets.QVBoxLayout(self.dockWidget_3)
        self.dock_vert.setContentsMargins(0, 0, 0, 0)
        self.dockWidget_3.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.dockWidget_3.setFrameShadow(QtWidgets.QFrame.Raised)
        
        self.dockWidget_3.setMouseTracking(True)
        self.dockWidget_3.setObjectName(_fromUtf8("dockWidget_3"))
        self.dockWidget_3.setMaximumWidth(self.width_allowed-100)
        #self.dockWidget_3.setMaximumHeight(500)
        
        #self.gridLayout.addLayout(self.VerticalLayoutLabel, 0, 0, 1, 1)
        
        #self.dockWidget_3.setMaximumSize(QtCore.QSize(150, 1000))
        self.dockWidgetContents_3 = QtWidgets.QWidget()
        self.dockWidgetContents_3.setObjectName(_fromUtf8("dockWidgetContents_3"))
        self.dock_vert.insertWidget(0, self.dockWidgetContents_3, 0)
        
        self.VerticalLayoutLabel_Dock3 = QtWidgets.QVBoxLayout(self.dockWidgetContents_3)
        self.VerticalLayoutLabel_Dock3.setObjectName(_fromUtf8("VerticalLayoutLabel_Dock3"))
        
        self.list3 = SidebarWidget(self.dockWidgetContents_3, self, home)
        self.list3.setMouseTracking(True)
        self.list3.setGeometry(QtCore.QRect(20, 100, 130, 201))
        self.list3.setObjectName(_fromUtf8("list3"))
        self.line = QtWidgets.QLineEdit(self.dockWidgetContents_3)
        self.line.setGeometry(QtCore.QRect(20, 20, 130, 26))
        #self.line.setGeometry(QtCore.QRect(20, 55, 130, 31))
        self.line.setObjectName(_fromUtf8("line"))
        #self.line.hide()
        self.line.setReadOnly(True)
        self.btn1 = Btn1(self.dockWidgetContents_3)
        #self.btn1.setGeometry(QtCore.QRect(20, 55, 130, 31))
        #self.btn1.setGeometry(QtCore.QRect(20, 20, 130, 26))
        self.btn1.setObjectName(_fromUtf8("btn1"))
        
        self.btnAddon = Btn1(self.dockWidgetContents_3)
        self.btnAddon.setObjectName(_fromUtf8("btnAddon"))
        self.btnAddon.hide()
        #self.btn1.setEditable(True)
        #self.btn1.lineEdit().setAlignment(QtCore.Qt.AlignCenter)
        
        #self.dockWidget_3.setWidget(self.dockWidgetContents_3)
        #MainWindow.addDockWidget(QtCore.Qt.DockWidgetArea(1), self.dockWidget_3)
        self.dockWidget_4 = QtWidgets.QDockWidget(MainWindow)
        ##self.dockWidget_4.setMinimumSize(QtCore.QSize(92, 159))
        self.dockWidget_4.setMaximumSize(QtCore.QSize(52000, 200))
        self.dockWidget_4.setObjectName(_fromUtf8("dockWidget_4"))
        
        self.dockWidgetContents_4 = QtWidgets.QWidget()
        self.dockWidgetContents_4.setObjectName(_fromUtf8("dockWidgetContents_4"))
        self.horizontalLayout = QtWidgets.QHBoxLayout(self.dockWidgetContents_4)
        self.horizontalLayout.setObjectName(_fromUtf8("horizontalLayout"))
        #self.text = QtGui.QTextBrowser(self.dockWidgetContents_4)
        #self.text.setObjectName(_fromUtf8("text"))
        #self.horizontalLayout.addWidget(self.text)
        self.dockWidget_4.setWidget(self.dockWidgetContents_4)
        
        ###################  Browser Layout  ##############################
        self.horizontalLayout_5 = QtWidgets.QVBoxLayout(self.tab_2)
        #MainWindow.addDockWidget(QtCore.Qt.DockWidgetArea(8), self.dockWidget_4)
        
        self.horizontalLayout_5.setObjectName(_fromUtf8("horizontalLayout_5"))
        self.dialog = QtWidgets.QDialog()
        #self.web = QWebView(self.tab_2)
        self.web = ''
        #self.web = Browser()
        #self.web.setObjectName(_fromUtf8("web"))
        #self.horizontalLayout_5.addWidget(self.web)
        ##self.gridLayout.addWidget(self.tab_2, 2, 1, 1, 1)
        #self.web.hide()
        self.horizLayout_web = QtWidgets.QHBoxLayout()
        self.horizLayout_web.setObjectName(_fromUtf8("horizLayout_web"))
        self.horizontalLayout_5.addLayout(self.horizLayout_web)
        
        
        
        self.btnWebClose = QtWidgets.QPushButton(self.tab_2)
        self.btnWebClose.setObjectName(_fromUtf8("btnWebClose"))
        self.btnWebClose.setMaximumSize(200, 50)
        self.horizLayout_web.insertWidget(1, self.btnWebClose, 0)
        self.btnWebClose.setText(self.player_buttons['close'])
        self.btnWebClose.clicked.connect(self.webClose)
        
        self.btnWebResize = QtWidgets.QPushButton(self.tab_2)
        self.btnWebResize.setObjectName(_fromUtf8("btnWebResize"))
        self.btnWebResize.setMaximumSize(200, 50)
        self.horizLayout_web.insertWidget(2, self.btnWebResize, 0)
        self.btnWebResize.setText(self.player_buttons['resize'])
        self.btnWebResize.clicked.connect(self.webResize)
        
        self.btnWebPrev = QtWidgets.QPushButton(self.tab_2)
        self.btnWebPrev.setObjectName(_fromUtf8("btnWebPrev"))
        self.btnWebPrev.setMaximumSize(200, 50)
        self.horizLayout_web.insertWidget(3, self.btnWebPrev, 0)
        self.btnWebPrev.clicked.connect(self.go_prev_web_page)
        self.btnWebPrev.setText(self.player_buttons['pr'])
        
        self.btnWebNext = QtWidgets.QPushButton(self.tab_2)
        self.btnWebNext.setObjectName(_fromUtf8("btnWebNext"))
        self.btnWebNext.setMaximumSize(200, 50)
        self.horizLayout_web.insertWidget(4, self.btnWebNext, 0)
        self.btnWebNext.clicked.connect(self.go_next_web_page)
        self.btnWebNext.setText(self.player_buttons['nxt'])
        
        self.btnWebReviews = QtWidgets.QComboBox(self.tab_2)
        self.btnWebReviews.setObjectName(_fromUtf8("btnWebReviews"))
        self.horizLayout_web.insertWidget(5, self.btnWebReviews, 0)
        self.btnWebReviews.setMaximumSize(200, 50)
        
        self.btnGoWeb = QtWidgets.QPushButton(self.tab_2)
        self.btnGoWeb.setObjectName(_fromUtf8("btnGoWeb"))
        self.horizLayout_web.insertWidget(6, self.btnGoWeb, 0)
        self.btnGoWeb.setMaximumSize(200, 50)
        self.btnGoWeb.setText("Go")
        self.btnGoWeb.clicked.connect(
            lambda x=0: self.reviewsWeb(action='btn_pushed')
            )
        
        self.btnWebReviews_search = QtWidgets.QLineEdit(self.tab_2)
        self.btnWebReviews_search.setObjectName(_fromUtf8("btnWebReviews_search"))
        self.horizLayout_web.insertWidget(7, self.btnWebReviews_search, 0)
        self.btnWebReviews_search.setMaximumSize(200, 50)
        self.btnWebReviews_search.setPlaceholderText('Search Web')
        self.btnWebReviews_search.returnPressed.connect(
            lambda x=0:self.reviewsWeb(action='return_pressed')
            )
        
        ##################
        
        self.btn2 = QtWidgets.QComboBox(self.dockWidgetContents_3)
        self.btn2.setObjectName(_fromUtf8("btn2"))
        self.btn3 = QtWidgets.QPushButton(self.dockWidgetContents_3)
        self.btn3.setObjectName(_fromUtf8("btn3"))
        self.btn3.setMinimumHeight(30)
        
        self.horizontalLayout10 = QtWidgets.QVBoxLayout(self.tab_6)
        self.horizontalLayout10.setObjectName(_fromUtf8("horizontalLayout"))
        self.scrollArea = QtGuiQWidgetScroll(self.tab_6, self)
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setObjectName(_fromUtf8("scrollArea"))
        self.scrollAreaWidgetContents = QtWidgets.QWidget()
        self.scrollAreaWidgetContents.setObjectName(_fromUtf8("scrollAreaWidgetContents"))
        self.gridLayout1 = QtWidgets.QGridLayout(self.scrollAreaWidgetContents)
        self.gridLayout1.setObjectName(_fromUtf8("gridLayout1"))
        self.scrollArea1 = QtGuiQWidgetScroll1(self.tab_6, self)
        self.scrollArea1.setWidgetResizable(True)
        
        self.scrollArea1.setObjectName(_fromUtf8("scrollArea1"))
        
        self.scrollAreaWidgetContents1 = QtWidgets.QWidget()
        self.scrollAreaWidgetContents1.setObjectName(_fromUtf8("scrollAreaWidgetContents1"))
        self.gridLayout2 = QtWidgets.QGridLayout(self.scrollAreaWidgetContents1)
        self.gridLayout2.setObjectName(_fromUtf8("gridLayout2"))
        self.gridLayout2.setSpacing(0)
        
        self.btn10 = QtWidgets.QComboBox(self.scrollAreaWidgetContents)
        self.btn10.setObjectName(_fromUtf8("btn10"))
        self.btn10.hide()
        self.gridLayout1.addWidget(self.btn10, 0, 0, 1, 1)
        
        """                        Thumbnail Mode                          """
        
        self.horizontalLayout_20 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_20.setObjectName(_fromUtf8("horizontalLayout_20"))
        self.gridLayout1.addLayout(self.horizontalLayout_20, 0, 1, 1, 1)
        self.gridLayout1.setAlignment(QtCore.Qt.AlignTop|QtCore.Qt.AlignCenter)
        self.gridLayout2.setAlignment(QtCore.Qt.AlignTop|QtCore.Qt.AlignCenter)
        self.gridLayout2.setSpacing(5)
        
        
        
        self.btn30 = Btn1(self.scrollAreaWidgetContents)
        self.btn30.setObjectName(_fromUtf8("btn30"))
        self.horizontalLayout_20.insertWidget(0, self.btn30, 0)
        self.comboBox20 = QtWidgets.QComboBox(self.scrollAreaWidgetContents)
        self.comboBox20.setObjectName(_fromUtf8("comboBox20"))
        self.horizontalLayout_20.insertWidget(1, self.comboBox20, 0)
        
        self.horizontalLayout_30 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_30.setObjectName(_fromUtf8("horizontalLayout_30"))
        self.gridLayout1.addLayout(self.horizontalLayout_30, 0, 2, 1, 1)
        
        self.comboBox30 = QtWidgets.QComboBox(self.scrollAreaWidgetContents)
        self.comboBox30.setObjectName(_fromUtf8("comboBox30"))
        self.horizontalLayout_30.insertWidget(0, self.comboBox30, 0)
        
        self.comboBoxMode = QtWidgets.QComboBox(self.scrollAreaWidgetContents)
        self.comboBoxMode.setObjectName(_fromUtf8("comboBoxMode"))
        
        self.btn20 = QtWidgets.QPushButton(self.scrollAreaWidgetContents)
        self.btn20.setObjectName(_fromUtf8("btn20"))
        
        self.labelFrame2 = QtWidgets.QLabel(self.scrollAreaWidgetContents)
        self.labelFrame2.setObjectName(_fromUtf8("labelFrame2"))
        self.labelFrame2.setScaledContents(True)
        self.labelFrame2.setAlignment(QtCore.Qt.AlignCenter)
        
        self.label_search = QtWidgets.QLineEdit(self.scrollAreaWidgetContents)
        self.label_search.setObjectName(_fromUtf8("label_search"))
        self.label_search.setMaximumWidth(100)
        
        self.btn201 = QtWidgets.QPushButton(self.scrollAreaWidgetContents)
        self.btn201.setObjectName(_fromUtf8("btn201"))
        self.float_window = QLabelFloat()
        self.float_window.set_globals(self, home)
        self.float_window_layout = QtWidgets.QVBoxLayout(self.float_window)
        self.float_window.setMinimumSize(200, 100)
        self.float_window.hide()
        self.float_window_dim = [1023, 28, 337, 226]
        self.float_window.setMouseTracking(True)
        #self.float_window.setScaledContents(True)
        self.float_window.setObjectName(_fromUtf8("float_window"))
        try:
            self.float_window.setWindowIcon(icon)
        except Exception as err:
            print(err, '--2170--')
        #self.float_window.setWindowFlags(QtCore.Qt.Window | QtCore.Qt.FramelessWindowHint)
        self.float_window.setWindowFlags(
            QtCore.Qt.Window | QtCore.Qt.WindowStaysOnTopHint)
        self.float_window_layout.setContentsMargins(0, 0, 0, 0)
        self.float_window_layout.setSpacing(0)
        
        self.horizontalLayout10.insertWidget(2, self.frame2, 0)
        
        self.horizontalLayout_101.insertWidget(0, self.btn20, 0)
        self.horizontalLayout_101.insertWidget(1, self.comboBoxMode, 0)
        self.horizontalLayout_101.insertWidget(2, self.labelFrame2, 0)
        self.horizontalLayout_101.insertWidget(3, self.btn201, 0)
        self.horizontalLayout_101.insertWidget(4, self.label_search, 0)
        
        ####################################################
        self.comboBox20.hide()
        self.comboBox30.hide()
        self.btn30.hide()
        self.btn10.setMaximumSize(QtCore.QSize(350, 16777215))
        self.comboBox20.setMaximumSize(QtCore.QSize(100, 16777215))
        
        self.chk = QtWidgets.QComboBox(self.dockWidget_3) 
        self.chk.setObjectName(_fromUtf8("chk"))
        self.comboView = QtWidgets.QComboBox(self.dockWidget_3) 
        self.comboView.setObjectName(_fromUtf8("comboView"))
        self.comboView.hide()
        
        #############################################
        self.btnOpt = QtWidgets.QComboBox(MainWindow)
        self.btnOpt.setObjectName(_fromUtf8("btnOpt"))
        self.horizontalLayout_7.addWidget(self.btnOpt)
        self.btnOpt.hide()
        self.go_opt = QtWidgets.QPushButton(MainWindow)
        self.go_opt.setObjectName(_fromUtf8("go_opt"))
        self.horizontalLayout_7.addWidget(self.go_opt)
        self.go_opt.hide()
        #####################################################
        self.close_frame = QtWidgets.QFrame(MainWindow)
        self.close_frame.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.close_frame.setFrameShadow(QtWidgets.QFrame.Raised)
        self.horiz_close_frame = QtWidgets.QHBoxLayout(self.close_frame)
        self.horiz_close_frame.setSpacing(0)
        self.horiz_close_frame.setContentsMargins(0, 0, 0, 0)
        self.scrollArea.setWidget(self.scrollAreaWidgetContents)
        self.horizontalLayout10.addWidget(self.scrollArea)
        self.scrollArea1.setWidget(self.scrollAreaWidgetContents1)
        self.horizontalLayout10.addWidget(self.scrollArea1)
        self.btn4 = QtWidgets.QPushButton(self.dockWidgetContents_3)
        self.btn4.setObjectName(_fromUtf8("btn4"))
        self.btn4.setMinimumHeight(30)
        self.btn4.setText('--')
        self.btn4.setToolTip('Auto-Hide On/Off')
        self.btn4.clicked.connect(self.close_frame_btn)
        self.auto_hide_dock = True
        
        self.btn_orient = QtWidgets.QPushButton(self.dockWidgetContents_3)
        self.btn_orient.setObjectName(_fromUtf8("btn_orient"))
        self.btn_orient.setMinimumHeight(30)
        self.btn_orient.setText(self.player_buttons['right'])
        self.btn_orient.setToolTip('Move Dock to Right')
        self.btn_orient.clicked.connect(self.orient_dock)
        self.orientation_dock = 'left'
        
        self.btn_quit = QtWidgets.QPushButton(self.dockWidgetContents_3)
        self.btn_quit.setObjectName(_fromUtf8("btn_quit"))
        self.btn_quit.setMinimumHeight(30)
        self.btn_quit.setText(self.player_buttons['quit'])
        self.btn_quit.setToolTip('Quit')
        self.btn_quit.clicked.connect(QtWidgets.qApp.quit)
        
        self.horiz_close_frame.insertWidget(0, self.btn_quit, 0)
        self.horiz_close_frame.insertWidget(1, self.btn_orient, 0)
        self.horiz_close_frame.insertWidget(2, self.btn4, 0)
        
        self.btnHistory = QtWidgets.QPushButton(self.dockWidgetContents_3)
        self.btnHistory.setObjectName(_fromUtf8("btnHistory"))
        self.btnHistory.hide()
        
        self.VerticalLayoutLabel_Dock3.insertWidget(0, self.line, 0)
        self.VerticalLayoutLabel_Dock3.insertWidget(1, self.btn1, 0)
        self.VerticalLayoutLabel_Dock3.insertWidget(2, self.btnAddon, 0)
        self.VerticalLayoutLabel_Dock3.insertWidget(3, self.list3, 0)
        self.VerticalLayoutLabel_Dock3.insertWidget(4, self.btnHistory, 0)
        self.VerticalLayoutLabel_Dock3.insertWidget(5, self.btn3, 0)
        self.VerticalLayoutLabel_Dock3.insertWidget(6, self.chk, 0)
        self.VerticalLayoutLabel_Dock3.insertWidget(7, self.comboView, 0)
        self.VerticalLayoutLabel_Dock3.insertWidget(8, self.close_frame, 0)
        
        self.btn3.setMinimumHeight(30)
        self.line.setMinimumHeight(30)
        self.btn1.setMinimumHeight(30)
        self.chk.setMinimumHeight(30)
        self.comboView.setMinimumHeight(30)
        self.btnHistory.setMinimumHeight(30)
        
        self.superGridLayout.addWidget(self.frame1, 1, 1, 1, 1)
        
        self.verticalLayout_50.insertWidget(0, self.list2, 0)
        self.verticalLayout_50.insertWidget(1, self.list6, 0)
        self.verticalLayout_50.insertWidget(2, self.list5, 0)
        self.verticalLayout_50.insertWidget(3, self.goto_epn, 0)
        
        self.verticalLayout_40.insertWidget(0, self.list1, 0)
        self.verticalLayout_40.insertWidget(1, self.list4, 0)
        self.verticalLayout_40.insertWidget(2, self.frame, 0)
        self.verticalLayout_40.setSpacing(5)
        self.verticalLayout_50.setSpacing(5)
        
        self.frame_timer = QtCore.QTimer()
        self.frame_timer.timeout.connect(self.frame_options)
        self.frame_timer.setSingleShot(True)
    
        self.mplayer_timer = QtCore.QTimer()
        self.mplayer_timer.timeout.connect(self.mplayer_unpause)
        self.mplayer_timer.setSingleShot(True)
        self.version_number = (2, 2, 0, 0)
        self.threadPool = []
        self.threadPoolthumb = []
        self.thumbnail_cnt = 0
        self.player_setLoop_var = 0
        self.playerPlaylist_setLoop_var = 0
        self.thread_server = QtCore.QThread()
        self.do_get_thread = QtCore.QThread()
        self.mplayer_status_thread = QtCore.QThread()
        self.stream_session = None
        self.start_streaming = False
        self.local_http_server = QtCore.QThread()
        self.local_ip = ''
        self.local_port = ''
        self.local_ip_stream = ''
        self.local_port_stream = ''
        self.search_term = ''
        self.mpv_cnt = 0
        self.remote_control = False
        self.remote_control_field = False
        self.local_file_index = []
        self.quality_val = 'sd'
        self.client_quality_val = 'sd'
        self.client_yt_mode = 'offline'
        self.playlist_auth_dict_ui = {}
        self.media_server_key = None
        self.my_public_ip = None
        self.get_ip_interval = 1
        self.access_from_outside_network = False
        self.cloud_ip_file = None
        self.keep_background_constant = False
        self.https_media_server = False
        self.media_server_cookie = False
        self.cookie_expiry_limit = 24
        self.cookie_playlist_expiry_limit = 24
        self.logging_module = False
        self.ytdl_path = 'default'
        self.ytdl_arr = []
        self.anime_review_site = False
        self.get_artist_metadata = False
        self.https_cert_file = os.path.join(home, 'cert.pem')
        self.progress_counter = 0
        self.posterfound_arr = []
        self.client_auth_arr = ['127.0.0.1', '0.0.0.0']
        self.current_background = os.path.join(home, 'default.jpg')
        self.default_background = os.path.join(home, 'default.jpg')
        self.yt_sub_folder = os.path.join(home, 'External-Subtitle')
        self.torrent_type = 'file'
        self.torrent_handle = ''
        self.list_with_thumbnail = False
        self.mpvplayer_val = QtCore.QProcess()
        self.options_mode = 'legacy'
        self.broadcast_message = 'kawaii-player {0}'.format(self.version_number)
        self.broadcast_server = False
        self.broadcast_thread = None
        self.discover_server = False
        self.discover_thread = None
        self.broadcast_server_list = []
        self.myserver_cache = {}
        self.newlistfound_thread_box = []
        self.myserver_threads_count = 0
        self.mpvplayer_aspect = {'0':'-1', '1':'16:9', '2':'4:3', '3':'2.35:1'}
        self.mpvplayer_aspect_cycle = 0
        self.setuploadspeed = 0
        self.category_dict = {
            'anime':'Anime', 'movies':'Movies', 'tv shows':'TV Shows',
            'cartoons':'Cartoons', 'others':'Others'
            }
        self.category_array = ['Anime', 'Movies', 'TV Shows', 'Cartoons', 'Others']
        self.update_video_dict_criteria()
        self.posterfind_batch = 0
        self.epn_arr_list = []
        self.icon_size_arr = []
        self.original_path_name = []
        self.download_video = 0
        self.total_seek = 0
        self.new_tray_widget = None
        self.widget_style = WidgetStyleSheet(self, home, BASEDIR)
        self.player_val = 'mpv'
        self.addons_option_arr = []
        self.mpvplayer_started = False
        self.mplayerLength = 0
        self.mpvplayer_command = []
        self.torrent_upload_limit = 0
        self.torrent_download_limit = 0
        self.torrent_download_folder = TMPDIR
        self.default_download_location = TMPDIR
        self.tmp_download_folder = TMPDIR
        self.logger = logger
        self.home_folder = home
        self.last_dir = os.path.expanduser("~")
        self.epn_name_in_list = ''
        self.getdb = None
        self.review_site_code = 'g'
        self.external_url = False
        self.subtitle_new_added = False
        self.window_frame = 'true'
        self.float_window_open = False
        self.music_mode_dim = [454, 29, 910, 340]
        self.music_mode_dim_show = False
        self.site_var = ''
        self.record_history = False
        self.depth_list = 0
        self.display_list = False
        self.tmp_web_srch = ''
        self.get_fetch_library = 'pycurl'
        self.image_fit_option_val = 3
        self.tmp_folder_remove = 'no'
        self.video_mode_index = 1
        self.current_thumbnail_position = (0, 0, 1, 1)
        self.fullscreen_mode = 0
        self.mplayer_pause_buffer = False
        self.mplayer_nop_error_pause = False
        self.started_from_external_client = False
        self.music_type_arr = [
            'mp3', 'flac', 'ogg', 'wav', 'aac', 'wma',
            'm4a', 'm4b', 'opus', 'webm'
            ]
        self.video_type_arr = [
            'mkv', 'mp4', 'avi', 'flv', 'ogg', 'wmv', 'webm'
            ]
        self.video_dict = {}
        self.update_proc = QtCore.QProcess()
        self.btn30.addItem(_fromUtf8(""))
        self.btn30.addItem(_fromUtf8(""))
        self.btn30.addItem(_fromUtf8(""))
        self.btn30.addItem(_fromUtf8(""))
        self.btn30.addItem(_fromUtf8(""))
        self.btn30.addItem(_fromUtf8(""))
        self.btn30.addItem(_fromUtf8(""))
        self.btn30.addItem(_fromUtf8(""))
        self.btn2.addItem(_fromUtf8(""))
        self.btn2.addItem(_fromUtf8(""))
        self.btn2.addItem(_fromUtf8(""))
        self.btn2.addItem(_fromUtf8(""))
        self.btn2.addItem(_fromUtf8(""))
        self.btn2.addItem(_fromUtf8(""))
        self.btn2.addItem(_fromUtf8(""))
        self.btn2.addItem(_fromUtf8(""))
        self.btn2.addItem(_fromUtf8(""))
        self.btnWebReviews.addItem(_fromUtf8(""))
        self.btnWebReviews.addItem(_fromUtf8(""))
        self.btnWebReviews.addItem(_fromUtf8(""))
        self.btnWebReviews.addItem(_fromUtf8(""))
        self.btnWebReviews.addItem(_fromUtf8(""))
        self.btnWebReviews.addItem(_fromUtf8(""))
        self.btnWebReviews.addItem(_fromUtf8(""))
        if 'AnimeWatch' in home:
            self.btnWebReviews.addItem(_fromUtf8(""))
            self.btnWebReviews.addItem(_fromUtf8(""))
            self.btnWebReviews.addItem(_fromUtf8(""))
            self.btnWebReviews.addItem(_fromUtf8(""))
            self.btnWebReviews.addItem(_fromUtf8(""))
            self.btnWebReviews.addItem(_fromUtf8(""))
        self.chk.addItem(_fromUtf8(""))
        self.chk.addItem(_fromUtf8(""))
        self.chk.addItem(_fromUtf8(""))
        self.chk.addItem(_fromUtf8(""))
        self.chk.addItem(_fromUtf8(""))
        self.comboBox20.addItem(_fromUtf8(""))
        self.comboBox20.addItem(_fromUtf8(""))
        self.comboBox20.addItem(_fromUtf8(""))
        self.comboBox20.addItem(_fromUtf8(""))
        self.comboBox20.addItem(_fromUtf8(""))
        self.comboView.addItem(_fromUtf8(""))
        self.comboView.addItem(_fromUtf8(""))
        self.comboView.addItem(_fromUtf8(""))
        self.comboBoxMode.addItem(_fromUtf8(""))
        self.comboBoxMode.addItem(_fromUtf8(""))
        self.comboBoxMode.addItem(_fromUtf8(""))
        self.comboBoxMode.addItem(_fromUtf8(""))
        QtWidgets.QShortcut(QtGui.QKeySequence("Shift+F"), 
                            MainWindow, self.fullscreenToggle)
        QtWidgets.QShortcut(QtGui.QKeySequence("Shift+L"), 
                            MainWindow, self.setPlayerFocus)
        QtWidgets.QShortcut(QtGui.QKeySequence("Shift+G"), 
                            MainWindow, self.dockShowHide)
        
        QtWidgets.QShortcut(QtGui.QKeySequence("Ctrl+F"), MainWindow, 
                            self.show_hide_filter_toolbar)
        QtWidgets.QShortcut(QtGui.QKeySequence("Ctrl+Z"), MainWindow, 
                            self.IconView)
        QtWidgets.QShortcut(QtGui.QKeySequence("Shift+Z"), MainWindow, 
                            self.IconViewEpn)
        QtWidgets.QShortcut(QtGui.QKeySequence("Ctrl+X"), MainWindow, 
                            self.webHide)
        QtWidgets.QShortcut(QtGui.QKeySequence("ESC"), MainWindow, 
                            self.HideEveryThing)
        QtWidgets.QShortcut(QtGui.QKeySequence("Ctrl+1"), MainWindow, 
                            lambda x=1:self.change_fanart_aspect(1))
        QtWidgets.QShortcut(QtGui.QKeySequence("Ctrl+2"), MainWindow, 
                            lambda x=1:self.change_fanart_aspect(2))
        QtWidgets.QShortcut(QtGui.QKeySequence("Ctrl+3"), MainWindow, 
                            lambda x=1:self.change_fanart_aspect(3))
        QtWidgets.QShortcut(QtGui.QKeySequence("Ctrl+4"), MainWindow, 
                            lambda x=1:self.change_fanart_aspect(4))
        QtWidgets.QShortcut(QtGui.QKeySequence("Ctrl+5"), MainWindow, 
                            lambda x=1:self.change_fanart_aspect(5))
        QtWidgets.QShortcut(QtGui.QKeySequence("Ctrl+6"), MainWindow, 
                            lambda x=1:self.change_fanart_aspect(6))
        QtWidgets.QShortcut(QtGui.QKeySequence("Ctrl+7"), MainWindow, 
                            lambda x=1:self.change_fanart_aspect(7))
        QtWidgets.QShortcut(QtGui.QKeySequence("Ctrl+8"), MainWindow, 
                            lambda x=1:self.change_fanart_aspect(8))
        QtWidgets.QShortcut(QtGui.QKeySequence("Ctrl+9"), MainWindow, 
                            lambda x=1:self.change_fanart_aspect(9))
        QtWidgets.QShortcut(QtGui.QKeySequence("Ctrl+0"), MainWindow, 
                            lambda x=1:self.change_fanart_aspect(10))
        QtWidgets.QShortcut(QtGui.QKeySequence("Alt+Right"), MainWindow, 
                            lambda x=1:self.direct_web('right'))
        QtWidgets.QShortcut(QtGui.QKeySequence("Alt+Left"), MainWindow, 
                            lambda x=1:self.direct_web('left'))
        
        self.list1.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.list1.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.list2.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.list2.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.text.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.list3.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.list3.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.list4.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.list4.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.list5.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.list5.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.list6.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.list6.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.scrollArea.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.scrollArea.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        if OSNAME == 'posix':
            self.scrollArea1.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.scrollArea1.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.retranslateUi(MainWindow)
        
        self.player_opt_toolbar.clicked.connect(self.player_opt_toolbar_dock)
        self.sd_hd.clicked.connect(self.selectQuality)
        self.goto_epn_filter.clicked.connect(self.goto_epn_filter_on)
        self.audio_track.clicked.connect(self.toggleAudio)
        self.subtitle_track.clicked.connect(self.toggleSubtitle)
        self.player_stop.clicked.connect(self.playerStop)
        self.player_prev.clicked.connect(self.mpvPrevEpnList)
        self.player_play_pause.clicked.connect(self.playerPlayPause)
        self.player_loop_file.clicked.connect(
            lambda x=0: self.playerLoopFile(self.player_loop_file)
            )
        self.player_next.clicked.connect(self.mpvNextEpnList)
        self.mirror_change.clicked.connect(self.mirrorChange)
        self.btn20.clicked.connect(lambda r = 0: self.thumbnailHide('clicked'))
        self.btn201.clicked.connect(self.prev_thumbnails)
        
        self.go_opt.clicked.connect(self.go_opt_options)
        self.btn10.currentIndexChanged['int'].connect(self.browse_epn)
        self.line.returnPressed.connect(self.searchNew)
        self.label_down_speed.returnPressed.connect(self.set_new_download_speed)
        self.label_up_speed.returnPressed.connect(self.set_new_upload_speed)
        self.label_torrent_stop.clicked.connect(self.stop_torrent)
        self.page_number.returnPressed.connect(self.gotopage)
        self.btn1.currentIndexChanged['int'].connect(self.ka)
        self.btnAddon.currentIndexChanged['int'].connect(self.ka2)
        self.btn30.currentIndexChanged['int'].connect(self.ka1)
        self.comboBox20.currentIndexChanged['int'].connect(self.browserView_view)
        self.comboView.currentIndexChanged['int'].connect(self.viewPreference)
        self.comboBoxMode.currentIndexChanged['int'].connect(self.set_video_mode)
        self.btnWebReviews.currentIndexChanged['int'].connect(
            lambda x: self.reviewsWeb(action='index_changed')
            )
        self.list1.itemDoubleClicked['QListWidgetItem*'].connect(self.list1_double_clicked)
        self.list1.currentRowChanged['int'].connect(self.history_highlight)
        self.list3.currentRowChanged['int'].connect(self.options_clicked)
        self.list4.currentRowChanged['int'].connect(self.search_highlight)
        self.list2.itemDoubleClicked['QListWidgetItem*'].connect(self.epnClicked)
        self.list2.currentRowChanged['int'].connect(self.epn_highlight)
        self.list3.itemDoubleClicked['QListWidgetItem*'].connect(
            lambda var = 'clicked':self.newoptions('clicked')
            )
        self.forward.clicked.connect(lambda r= "": self.nextp('next'))
        self.backward.clicked.connect(lambda r= "": self.backp('back'))
        self.filter_btn.clicked.connect(self.filter_btn_options)
        self.hide_btn_list1.clicked.connect(self.hide_btn_list1_pressed)
        self.go_page.textChanged['QString'].connect(self.filter_list)
        self.label_search.textChanged['QString'].connect(self.filter_label_list)
        self.goto_epn_filter_txt.textChanged['QString'].connect(self.filter_epn_list_txt)
        self.btn3.clicked.connect(self.addToLibrary)
        self.btnHistory.clicked.connect(self.setPreOpt)
        self.chk.currentIndexChanged['int'].connect(self.preview)
        
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

        self.btn2.hide()
        self.line.setPlaceholderText("Search")
        self.label_search.setPlaceholderText("Filter")
        self.go_page.setPlaceholderText("Filter")
        
    def retranslateUi(self, MainWindow):
        global home
        MainWindow.setWindowTitle("Kawaii-Player")
        self.float_window.setWindowTitle("Kawaii-Player")
        self.line.setToolTip(
            _translate("MainWindow", 
            "<html><head/><body><p>Enter Search Keyword</p></body></html>", 
            None)
            )
        self.backward.setText(_translate("MainWindow", "Previous", None))
        self.filter_btn.setText(_translate("MainWindow", "Filter", None))
        self.btnHistory.setText(_translate("MainWindow", "History", None))
        self.go_opt.setText(_translate("MainWindow", "Go", None))
        self.go_page.setToolTip(
            _translate("MainWindow", 
            "<html><head/><body><p>Filter or Search</p></body></html>", 
            None)
            )
        self.forward.setText(_translate("MainWindow", "Next", None))
        self.page_number.setToolTip(
            _translate("MainWindow", 
            "<html><head/><body><p align=\"center\">Enter Page Number</p></body></html>", 
            None)
            )
        self.btn30.setItemText(0, _translate("MainWindow", "Select", None))
        self.btn30.setItemText(1, _translate("MainWindow", "Select", None))
        self.btn30.setItemText(2, _translate("MainWindow", "Select", None))
        self.btn30.setItemText(3, _translate("MainWindow", "Select", None))
        self.btn30.setItemText(4, _translate("MainWindow", "Select", None))
        self.btn30.setItemText(5, _translate("MainWindow", "Select", None))
        self.btn30.setItemText(6, _translate("MainWindow", "Select", None))
        self.btn30.setItemText(7, _translate("MainWindow", "Select", None))
        self.btn3.setText(_translate("MainWindow", "Library", None))
        self.btn2.setItemText(0, _translate("MainWindow", "Reviews", None))
        self.btn2.setItemText(1, _translate("MainWindow", "MyAnimeList", None))
        self.btn2.setItemText(2, _translate("MainWindow", "Anime-Planet", None))
        self.btn2.setItemText(3, _translate("MainWindow", "Anime-Source", None))
        self.btn2.setItemText(4, _translate("MainWindow", "TVDB", None))
        self.btn2.setItemText(5, _translate("MainWindow", "ANN", None))
        self.btn2.setItemText(6, _translate("MainWindow", "AniDB", None))
        self.btn2.setItemText(7, _translate("MainWindow", "Google", None))
        self.btn2.setItemText(8, _translate("MainWindow", "Youtube", None))
        if 'AnimeWatch' in home:
            self.btnWebReviews.setItemText(0, _translate("MainWindow", "Reviews", None))
            self.btnWebReviews.setItemText(1, _translate("MainWindow", "MyAnimeList", None))
            self.btnWebReviews.setItemText(2, _translate("MainWindow", "Anime-Planet", None))
            self.btnWebReviews.setItemText(3, _translate("MainWindow", "Anime-Source", None))
            self.btnWebReviews.setItemText(4, _translate("MainWindow", "TVDB", None))
            self.btnWebReviews.setItemText(5, _translate("MainWindow", "ANN", None))
            self.btnWebReviews.setItemText(6, _translate("MainWindow", "AniDB", None))
            self.btnWebReviews.setItemText(7, _translate("MainWindow", "Google", None))
            self.btnWebReviews.setItemText(8, _translate("MainWindow", "Youtube", None))
            self.btnWebReviews.setItemText(9, _translate("MainWindow", "DuckDuckGo", None))
            self.btnWebReviews.setItemText(10, _translate("MainWindow", "Zerochan", None))
            self.btnWebReviews.setItemText(11, _translate("MainWindow", "last.fm", None))
            self.btnWebReviews.setItemText(12, _translate("MainWindow", "TMDB", None))
        else:
            self.btnWebReviews.setItemText(0, _translate("MainWindow", "Reviews", None))
            self.btnWebReviews.setItemText(1, _translate("MainWindow", "TVDB", None))
            self.btnWebReviews.setItemText(2, _translate("MainWindow", "Google", None))
            self.btnWebReviews.setItemText(3, _translate("MainWindow", "Youtube", None))
            self.btnWebReviews.setItemText(4, _translate("MainWindow", "DuckDuckGo", None))
            self.btnWebReviews.setItemText(5, _translate("MainWindow", "last.fm", None))
            self.btnWebReviews.setItemText(6, _translate("MainWindow", "TMDB", None))
        self.chk.setItemText(0, _translate("MainWindow", "mpv", None))
        self.chk.setItemText(1, _translate("MainWindow", "mplayer", None))
        self.chk.setItemText(2, _translate("MainWindow", "vlc", None))
        self.chk.setItemText(3, _translate("MainWindow", "kodi", None))
        self.chk.setItemText(4, _translate("MainWindow", "smplayer", None))
        self.comboBox20.setItemText(0, _translate("MainWindow", "Options", None))
        self.comboBox20.setItemText(1, _translate("MainWindow", "Clear", None))
        self.comboBox20.setItemText(2, _translate("MainWindow", "MostPopular", None))
        self.comboBox20.setItemText(3, _translate("MainWindow", "Random", None))
        self.comboBox20.setItemText(4, _translate("MainWindow", "History", None))
        self.comboView.setItemText(0, _translate("MainWindow", "View Mode", None))
        self.comboView.setItemText(1, _translate("MainWindow", "List", None))
        self.comboView.setItemText(2, _translate("MainWindow", "Thumbnail", None))
        self.btn20.setText(_translate("MainWindow", self.player_buttons['close'], None))
        self.btn201.setText(_translate("MainWindow", self.player_buttons['prev'], None))
        self.comboBoxMode.setItemText(0, 'Mode 1')
        self.comboBoxMode.setItemText(1, 'Mode 2')
        self.comboBoxMode.setItemText(2, 'Mode 3')
        self.comboBoxMode.setItemText(3, 'Mode 4')
        
        self.thumb_timer = QtCore.QTimer()
        self.mplayer_OsdTimer = QtCore.QTimer()
        self.mplayer_OsdTimer.timeout.connect(self.osd_hide)
        self.mplayer_OsdTimer.setSingleShot(True)
        
        self.mplayer_SubTimer = QtCore.QTimer()
        self.mplayer_SubTimer.timeout.connect(self.subMplayer)
        self.mplayer_SubTimer.setSingleShot(True)
        
        self.external_SubTimer = QtCore.QTimer()
        self.external_SubTimer.timeout.connect(self.load_external_sub)
        self.external_SubTimer.setSingleShot(True)
        
        self.float_timer = QtCore.QTimer()
        self.float_timer.timeout.connect(self.float_activity)
        self.float_timer.setSingleShot(True)
        
        self.total_file_size = 0
        self.id_audio_bitrate = 0
        self.id_video_bitrate = 0
        self.final_playing_url = ""
        self.queue_url_list = []
        self.downloadWget = []
        self.downloadWget_cnt = 0
        self.lock_process = False
        self.mpv_thumbnail_lock = False
        
    def update_video_dict_criteria(self):
        video_dir_path = os.path.join(home, 'VideoDB')
        if not os.path.exists(video_dir_path):
            os.makedirs(video_dir_path)
        video_category_path = os.path.join(video_dir_path, 'extra_category')
        if not os.path.isfile(video_category_path):
            open(video_category_path, 'w').close()
        else:
            cat_lines = open_files(video_category_path, True)
            cat_lines = [i.strip() for i in cat_lines if i.strip()]
            for i in cat_lines:
                self.category_array.append(i)
                self.category_dict.update({i.lower():i})
            logger.info('{0}::{1}::--1808--'.format(self.category_dict, self.category_array))
            
    def direct_web(self, mode):
        if not self.tab_2.isHidden():
            if mode == 'right':
                self.go_next_web_page()
            elif mode == 'left':
                self.go_prev_web_page()
    
    def set_parameters_value(
            self, siteval=None, curRow=None, quit_r=None, thumb_indicator=None,
            iconv=None, bufm=None, cache_val=None, iconvr=None, pause_i=None,
            mpv_i=None, fullsc=None, tab_6=None, cur_label=None, path_final=None,
            idw_val=None, amp=None, cur_ply=None, t6_ply=None, inter=None,
            memory_num=None, show_hide_pl=None, show_hide_tl=None, op=None,
            qual=None, mir=None, name_val=None, catg=None, local_ip=None):
        global site, curR, quitReally, iconv_r, thumbnail_indicator
        global buffering_mplayer, cache_empty, iconv_r_indicator
        global pause_indicator, mpv_indicator, fullscr, tab_6_size_indicator
        global cur_label_num, path_final_Url, idw, current_playing_file_path
        global artist_name_mplayer, tab_6_player, interval, memory_num_arr
        global show_hide_playlist, show_hide_titlelist, opt, quality, mirrorNo
        global name, category
        if siteval:
            site = siteval
        if curRow:
            curR = curRow
        if quit_r:
            quitReally = quit_r
        if catg:
            category = catg
        if op:
            opt = op
        if qual:
            quality = qual
            self.quality_val = qual
        if local_ip:
            self.local_ip_stream = get_lan_ip()
        if mir:
            mirrorNo = mir
        if name_val:
            name = name_val
        if iconv:
            iconv_r = iconv
        if iconvr:
            iconv_r_indicator = iconvr
        if pause_i:
            pause_indicator = pause_i
        if mpv_i:
            mpv_indicator = mpv_i
        if memory_num:
            memory_num_arr = memory_num
        if cur_label:
            cur_label_num = cur_label
        if show_hide_pl:
            show_hide_playlist = show_hide_pl
        if show_hide_tl:
            show_hide_titlelist = show_hide_tl
        if tab_6:
            tab_6_size_indicator = tab_6
        if idw_val:
            idw = idw_val
        if fullsc:
            fullscr = fullsc
        if amp:
            artist_name_mplayer = amp
        if cur_ply:
            current_playing_file_path = cur_ply
        if t6_ply:
            tab_6_player = t6_ply
        if path_final:
            path_final_Url = path_final
        if inter:
            interval = inter
        if thumb_indicator:
            if thumb_indicator == 'empty':
                thumbnail_indicator[:] = []
        if bufm:
            buffering_mplayer = bufm
        if cache_val:
            cache_empty = cache_val
            
    def get_parameters_value(self, *arg, **kargs):
        global curR, path_final_Url, opt, site, siteName
        global video_local_stream, name, html_default_arr, Player
        global pause_indicator, mpv_indicator, wget, rfr_url, total_till
        global show_hide_titlelist, show_hide_cover, iconv_r_indicator
        global idw, iconv_r, cur_label_num, fullscr, tab_6_size_indicator
        global refererNeeded, server, tab_6_player, memory_num_arr
        global finalUrlFound, interval, name, opt, bookmark, status
        global base_url, embed, mirrorNo, category
        arg_dict = {}
        for key, val in kargs.items():
            arg_dict.update({'{0}'.format(val):eval(str(val))})
        logger.info(arg_dict)
        return arg_dict
        
    def remote_fullscreen(self):
        global MainWindow, wget
        if MainWindow.isHidden():
            MainWindow.show()
        if not MainWindow.isHidden():
            if not MainWindow.isFullScreen():
                if not self.tab_6.isHidden():
                    self.fullscreen_mode = 1
                elif not self.float_window.isHidden():
                    self.fullscreen_mode = 2
                else: 
                    self.fullscreen_mode = 0
                self.gridLayout.setSpacing(0)
                self.superGridLayout.setSpacing(0)
                self.gridLayout.setContentsMargins(0, 0, 0, 0)
                self.superGridLayout.setContentsMargins(0, 0, 0, 0)
                self.text.hide()
                self.label.hide()
                self.frame1.hide()
                self.tab_6.hide()
                self.goto_epn.hide()
                self.btn20.hide()
                if wget.processId() > 0 or video_local_stream:
                    self.progress.hide()
                    if not self.torrent_frame.isHidden():
                        self.torrent_frame.hide()
                self.list2.hide()
                self.list6.hide()
                self.list1.hide()
                self.frame.hide()
                self.dockWidget_3.hide()
                self.tab_5.show()
                self.tab_5.setFocus()
                if not self.tab_2.isHidden():
                    self.tab_2.hide()
                if (Player == "mplayer" or Player=="mpv"):
                    MainWindow.setCursor(QtGui.QCursor(QtCore.Qt.BlankCursor))
                MainWindow.showFullScreen()
            else:
                self.gridLayout.setSpacing(5)
                self.superGridLayout.setSpacing(0)
                self.gridLayout.setContentsMargins(5, 5, 5, 5)
                self.superGridLayout.setContentsMargins(5, 5, 5, 5)
                self.list2.show()
                self.btn20.show()
                if wget.processId() > 0 or video_local_stream:
                    self.progress.show()
                self.frame1.show()
                if Player == "mplayer" or Player=="mpv":
                    MainWindow.setCursor(QtGui.QCursor(QtCore.Qt.ArrowCursor))
                MainWindow.showNormal()
                MainWindow.showMaximized()
                if total_till != 0 or self.fullscreen_mode == 1:
                    self.tab_6.show()
                    self.list2.hide()
                    self.goto_epn.hide()
                if self.btn1.currentText().lower() == 'youtube':
                    self.list2.hide()
                    self.goto_epn.hide()
                    self.tab_2.show()
                #QtW
        else:
            if not self.float_window.isHidden():
                if not self.float_window.isFullScreen():
                    self.float_window.showFullScreen()
                else:
                    self.float_window.showNormal()
    
    def seek_to_val(self, val):
        global Player
        txt1 = '\n osd 1 \n'
        if Player == "mplayer":
            txt = '\n seek {0}\n'.format(val)
        else:
            txt = '\n seek {0} relative+exact \n'.format(val)
            print(txt)
        self.mpvplayer_val.write(bytes(txt1, 'utf-8'))
        self.mpvplayer_val.write(bytes(txt, 'utf-8'))
        
    def seek_to_vol_val(self, val):
        global Player
        txt1 = '\n osd 1 \n'
        if Player == "mplayer":
            txt = '\n volume {0} \n'.format(val)
            self.mpvplayer_val.write(b'')
        else:
            txt = '\n add ao-volume {0} \n'.format(val)
        self.mpvplayer_val.write(bytes(txt1, 'utf-8'))
        self.mpvplayer_val.write(bytes(txt, 'utf-8'))
    
    def float_activity(self):
        if not self.new_tray_widget.isHidden() and self.new_tray_widget.remove_toolbar:
            self.new_tray_widget.hide()
            print('--float--activity--')
            
    def set_video_mode(self):
        txt = self.comboBoxMode.currentText()
        txt = txt.lower()
        if txt == 'mode 1':
            self.video_mode_index = 1
        elif txt == 'mode 2':
            self.video_mode_index = 2
        elif txt == 'mode 3':
            self.video_mode_index = 3
        elif txt == 'mode 4':
            self.video_mode_index = 4
    
    def change_fanart_aspect(self, var):
        dir_name = self.get_current_directory()
        fanart = os.path.join(dir_name, 'fanart.jpg')
        poster = os.path.join(dir_name, 'poster.jpg')
        thumbnail = os.path.join(dir_name, 'thumbnail.jpg')
        summary = ''
        picn = os.path.join(dir_name, 'original-fanart.jpg')
        self.image_fit_option_val = var
        logger.info(picn)
        if not os.path.exists(picn) and os.path.exists(fanart):
            shutil.copy(fanart, picn)
        elif not os.path.exists(picn) and os.path.exists(poster):
            shutil.copy(poster, picn)
        if os.path.exists(picn):
            logger.info(
                "\npicn={0}, fanart={1}, image_fit_option={2}\n".format(
                picn, fanart, self.image_fit_option_val))
            self.image_fit_option(picn, fanart, fit_size=self.image_fit_option_val)
            set_mainwindow_palette(fanart)
        
    def webResize(self):
        global screen_width
        wdt = self.tab_2.width()
        if wdt <= 400:
            self.tab_2.setMaximumWidth(screen_width)
        else:
            self.tab_2.setMaximumWidth(400)
            
    def go_prev_web_page(self):
        if self.web:
            self.web.back()
            
    def go_next_web_page(self):
        if self.web:
            self.web.forward()
            
    def text_save_btn_hide(self):
        self.text_save_btn.hide()
        
    def save_text_edit(self):
        txt = self.text.toPlainText()
        self.text.clear()
        self.copySummary(txt)
        
    def text_editor_changed(self):
        g = self.text.geometry()
        txt = self.text.toPlainText()
        print(g.x(), g.y())
        self.text_save_btn.setGeometry(g.x()+g.width()-30, g.y()-25, 35, 25)
        self.text_save_btn.show()
        self.text_save_btn_timer.start(4000)
        
    def show_hide_filter_toolbar(self):
        go_pg = False
        go_epn = False
        if self.list1.isHidden() and self.list2.isHidden():
            pass
        elif not self.list1.isHidden() and self.list2.isHidden():
            if self.frame.isHidden():
                self.frame.show()
                #go_pg = True
            elif not self.frame.isHidden():
                self.frame.hide()
        elif self.list1.isHidden() and not self.list2.isHidden():
            if self.goto_epn.isHidden():
                self.goto_epn.show()
            elif not self.goto_epn.isHidden():
                self.goto_epn.hide()
        elif not self.list1.isHidden() and not self.list2.isHidden():
            if self.frame.isHidden() and not self.goto_epn.isHidden():
                self.goto_epn.hide()
            elif not self.frame.isHidden() and self.goto_epn.isHidden():
                self.frame.hide()
            elif not self.frame.isHidden() and not self.goto_epn.isHidden():
                self.frame.hide()
                self.goto_epn.hide()
            elif self.frame.isHidden() and self.goto_epn.isHidden():
                self.frame.show()
                self.goto_epn.show()
            
        if not self.frame.isHidden():
            self.go_page.setFocus()
        elif not self.goto_epn.isHidden():
            self.goto_epn_filter_txt.setFocus()
        
        if self.frame.isHidden() and self.goto_epn.isHidden():
            if not self.list1.isHidden():
                self.list1.setFocus()
            elif not self.list2.isHidden():
                self.list2.setFocus()
                    
    def orient_dock(self, initial_start=None):
        if initial_start:
            txt = initial_start
            if txt == 'left':
                self.btn_orient.setText(self.player_buttons['right'])
                self.btn_orient.setToolTip('Orient Dock to Right')
                self.orientation_dock = 'left'
                self.superGridLayout.addWidget(self.dockWidget_3, 0, 1, 1, 1)
            else:
                self.btn_orient.setText(self.player_buttons['left'])
                self.btn_orient.setToolTip('Orient Dock to Left')
                self.orientation_dock = 'right'
                self.superGridLayout.addWidget(self.dockWidget_3, 0, 5, 1, 1)
                #self.gridLayout.addWidget(self.dockWidget_3, 0, 3, 1, 1)
        else:
            txt = self.btn_orient.text()
            if txt == self.player_buttons['right']:
                self.btn_orient.setText(self.player_buttons['left'])
                self.btn_orient.setToolTip('Orient Dock to Left')
                self.orientation_dock = 'right'
                self.superGridLayout.addWidget(self.dockWidget_3, 0, 5, 1, 1)
                #self.gridLayout.addWidget(self.dockWidget_3, 0, 3, 1, 1)
            else:
                self.player_buttons['left']
                self.btn_orient.setText(self.player_buttons['right'])
                self.btn_orient.setToolTip('Orient Dock to Right')
                self.orientation_dock = 'left'
                self.superGridLayout.addWidget(self.dockWidget_3, 0, 1, 1, 1)
            
    def close_frame_btn(self):
        txt = self.btn4.text()
        if txt == '--':
            self.btn4.setText('+')
            #self.btn4.setToolTip('Auto Hide Off')
            self.auto_hide_dock = False
        else:
            self.btn4.setText('--')
            #self.btn4.setToolTip('Auto Hide On')
            self.auto_hide_dock = True
            self.dockWidget_3.hide()
            
    def generate_thumbnail_method(self, picn, interval, path):
        global Player
        path = path.replace('"', '')
        inter = str(interval)
        
        new_tmp = '"'+TMPDIR+'"'
        if not self.mpv_thumbnail_lock:
            if OSNAME == 'posix':
                wd = str(self.width_allowed)
                if path.endswith('.mp3') or path.endswith('.flac'):
                    try:
                        f = mutagen.File(path)
                        artwork = f.tags['APIC:'].data
                        with open(picn, 'wb') as img:
                            img.write(artwork) 
                    except Exception as e:
                        try:
                            f = open(picn, 'w').close()
                            print(e, '--9048--')
                        except Exception as e:
                            print(e, '--9065--')
                            
                else:
                    subprocess.call(["ffmpegthumbnailer", "-i", path, "-o", picn, 
                                "-t", str(inter), '-q', '10', '-s', wd])
                logger.info("{0}:{1}".format(path, picn))
                if os.path.exists(picn) and os.stat(picn).st_size:
                    self.image_fit_option(picn, picn, fit_size=6, widget=self.label)
            else:
                if inter.endswith('s'):
                    inter = inter[:-1]
                #self.progressEpn.setFormat('Generating Thumbnail Wait..')
                self.mpv_thumbnail_lock = True
                if 'youtube.com' in path:
                    new_tmp = new_tmp.replace('"', '')
                    subprocess.call(["mpv", "--vo=image", "--no-sub", "--ytdl=yes", "--quiet", 
                                    "-aid=no", "-sid=no", "--vo-image-outdir="+new_tmp, 
                                    "--start="+str(inter)+"%", "--frames=1"
                                    , path])
                else:
                    if Player == 'mpv':
                        new_tmp = new_tmp.replace('"', '')
                        subprocess.call(["mpv", "--vo=image", "--no-sub", "--ytdl=no", 
                        "--quiet", "-aid=no", "-sid=no", "--vo-image-outdir="+new_tmp, 
                        "--start="+str(inter)+"%", "--frames=1", path], shell=True)
                    elif Player == 'mplayer':
                        subprocess.call(["mplayer", "-nosub", "-nolirc", "-nosound", 
                        '-vo', "jpeg:quality=100:outdir="+new_tmp, "-ss", str(inter), 
                        "-endpos", "1", "-frames", "1", "-vf", "scale=320:180", 
                        path], shell=True)
                    
                picn_path = os.path.join(TMPDIR, '00000001.jpg')
                if os.path.exists(picn_path):
                    shutil.copy(picn_path, picn)
                    os.remove(picn_path)
                    if os.path.exists(picn) and os.stat(picn).st_size:
                        self.image_fit_option(picn, picn, fit_size=6, widget=self.label)
                self.mpv_thumbnail_lock = False
            #self.progressEpn.setFormat('Thumbnail Generated..')
    
    def create_new_image_pixel(self, art_url, pixel):
        art_url_name = str(pixel)+'px.'+os.path.basename(art_url)
        path_thumb, new_title = os.path.split(art_url)
        abs_path_thumb = os.path.join(path_thumb, art_url_name)
        try:
            if not os.path.exists(abs_path_thumb) and os.path.exists(art_url):
                basewidth = pixel
                img = Image.open(str(art_url))
                wpercent = (basewidth / float(img.size[0]))
                hsize = int((float(img.size[1]) * float(wpercent)))
                img = img.resize((basewidth, hsize), PIL.Image.ANTIALIAS)
                img.save(str(abs_path_thumb))
            elif not os.path.exists(art_url):
                art_url_name = str(pixel)+'px.'+os.path.basename(self.default_background)
                path_thumb, new_title = os.path.split(self.default_background)
                abs_path_thumb = os.path.join(path_thumb, art_url_name)

                if not os.path.exists(abs_path_thumb) and os.path.exists(self.default_background):
                    basewidth = pixel
                    img = Image.open(str(self.default_background))
                    wpercent = (basewidth / float(img.size[0]))
                    hsize = int((float(img.size[1]) * float(wpercent)))
                    img = img.resize((basewidth, hsize), PIL.Image.ANTIALIAS)
                    img.save(str(abs_path_thumb))
        except:
            art_url_name = str(pixel)+'px.'+os.path.basename(self.default_background)
            path_thumb, new_title = os.path.split(self.default_background)
            abs_path_thumb = os.path.join(path_thumb, art_url_name)
            if not os.path.exists(abs_path_thumb) and os.path.exists(self.default_background):
                basewidth = pixel
                img = Image.open(str(self.default_background))
                wpercent = (basewidth / float(img.size[0]))
                hsize = int((float(img.size[1]) * float(wpercent)))
                img = img.resize((basewidth, hsize), PIL.Image.ANTIALIAS)
                img.save(str(abs_path_thumb))
            
        return abs_path_thumb
        
    def list1_double_clicked(self):
        global show_hide_titlelist, show_hide_playlist, curR
        self.listfound()
        if site == "Music" and not self.list2.isHidden():
            self.list2.setFocus()
            self.list2.setCurrentRow(0)
            curR = 0
            self.list1.show()
            self.list1.setFocus()
        else:
            if self.list2.isHidden():
                self.list1.hide()
                self.frame.hide()
                self.list2.show()
                self.list2.setFocus()
                show_hide_titlelist = 0
                show_hide_playlist = 1
        self.update_list2()
        
    def hide_torrent_info(self):
        self.torrent_frame.hide()
        self.progress.hide()
        
    def stop_torrent(self, from_client=None):
        global video_local_stream, wget, site
        try:
            stop_now = False
            new_video_local_stream = False
            if from_client:
                if self.started_from_external_client:
                    stop_now = True
                    new_video_local_stream = True
            else:
                stop_now = True
            if stop_now:
                if video_local_stream or new_video_local_stream:
                    if self.do_get_thread.isRunning():
                        print('----------stream-----pausing-----')
                        t_list = self.stream_session.get_torrents()
                        for i in t_list:
                            logger.info('--removing--{0}'.format(i.name()))
                            self.stream_session.remove_torrent(i)
                        self.stream_session.pause()
                        #self.stream_session = None
                    elif self.stream_session:
                        if not self.stream_session.is_paused():
                            self.stream_session.pause()
                            #self.stream_session = None
                    txt = 'Torrent Stopped'
                    send_notification(txt)
                    self.torrent_frame.hide()
                else:
                    if wget.processId() > 0:
                        wget.kill()
                    txt = 'Stopping download'
                    send_notification(txt)
                    self.torrent_frame.hide()
                self.progress.hide()
        except Exception as e:
            print(e, '--9349--')
    
    def stop_torrent_forcefully(self, from_client=None):
        global video_local_stream, site
        try:
            if self.do_get_thread.isRunning():
                print('----------stream-----pausing-----')
                t_list = self.stream_session.get_torrents()
                for i in t_list:
                    logger.info('--removing--{0}'.format(i.name()))
                    self.stream_session.remove_torrent(i)
                self.stream_session.pause()
                #self.stream_session = None
            elif self.stream_session:
                if not self.stream_session.is_paused():
                    self.stream_session.pause()
                    #self.stream_session = None
            txt = 'Torrent Stopped'
            send_notification(txt)
            self.torrent_frame.hide()
            self.progress.hide()
        except Exception as e:
            print(e, '--9368--')
    
    def set_new_download_speed(self):
        txt = self.label_down_speed.text()
        try:
            self.torrent_download_limit = int(txt) * 1024
        except:
            txt_notify = 'Please enter valid speed in KB'
            send_notification(txt_notify)
        self.label_down_speed.clear()
        self.torrent_handle.set_download_limit(self.torrent_download_limit)
        #print(type(self.torrent_handle))
        down = '\u2193 SET TO: ' +str(int(self.torrent_download_limit/1024))+'K'
        self.label_down_speed.setPlaceholderText(down)
        
    def set_new_upload_speed(self):
        txt = self.label_up_speed.text()
        try:
            self.torrent_upload_limit = int(txt) * 1024
        except:
            txt_notify = 'Please enter valid speed in KB'
            send_notification(txt_notify)
        self.label_up_speed.clear()
        self.torrent_handle.set_upload_limit(self.torrent_upload_limit)
        #print(type(self.torrent_handle))
        up = '\u2191 SET TO: ' +str(int(self.torrent_upload_limit/1024))+'K'
        self.label_up_speed.setPlaceholderText(up)
        
    def quitApp(self):
        app.quit()
        
    def queueList_return_pressed(self, r):
        t = self.queue_url_list[r]
        del self.queue_url_list[r]
        
        item = self.list6.item(r)
        i = item.text()
        self.list6.takeItem(r)
        del item
        self.list6.insertItem(0, i)
        self.queue_url_list.insert(0, t)
        self.getQueueInList()
        
    def queue_manage_list(self):
        if self.list6.isHidden():
            self.list6.show()
            self.list6.setFocus()
        else:
            self.list6.hide()
            
    def goto_epn_filter_on(self):
        if self.goto_epn_filter_txt.isHidden():
            self.goto_epn_filter_txt.show()
            self.goto_epn_filter_txt.setFocus()
        else:
            self.goto_epn_filter_txt.clear()
            
    def player_started_playing(self):
        global player_start_now
        player_start_now = 1
        print("started")
        
    def player_opt_toolbar_dock(self):
        if self.dockWidget_3.isHidden():
            self.dockWidget_3.show()
        else:
            self.dockWidget_3.hide()
            
    def hide_btn_list1_pressed(self):
        if self.list1.isHidden():
            self.list1.show()
            self.hide_btn_list1.setText("Hide")
        else:
            self.list1.hide()
            self.hide_btn_list1.setText("Show")
            
    def subMplayer(self):
        global audio_id, sub_id, Player
        if Player == 'mplayer':
            t = bytes('\n'+"switch_audio "+str(audio_id)+'\n', 'utf-8')
            self.mpvplayer_val.write(t)
            t1 = bytes('\n'+"sub_select "+str(sub_id)+'\n', 'utf-8')
            self.mpvplayer_val.write(t1)
            
    def osd_hide(self):
        self.mpvplayer_val.write(b'\n osd 0 \n')
        
    def mirrorChange(self):
        global mirrorNo
        txt = str(self.mirror_change.text())
        if txt == "Mirror":
            mirrorNo = 1
            self.mirror_change.setText("1")
        else:
            mirrorNo = int(txt)
            mirrorNo = mirrorNo + 1
            if mirrorNo == 10:
                self.mirror_change.setText("Mirror")
                mirrorNo = 1
            else:
                self.mirror_change.setText(str(mirrorNo))
        
    def toggleAudio(self):
        global Player, audio_id
        if self.mpvplayer_val.processId() > 0:
            if Player == "mplayer":
                if not self.mplayer_OsdTimer.isActive():
                    self.mpvplayer_val.write(b'\n osd 1 \n')
                else:
                    self.mplayer_OsdTimer.stop()
                
                self.mpvplayer_val.write(b'\n switch_audio \n')
                self.mpvplayer_val.write(b'\n get_property switch_audio \n')
                self.mplayer_OsdTimer.start(5000)
            else:
                self.mpvplayer_val.write(b'\n cycle audio \n')
                self.mpvplayer_val.write(b'\n print-text "Audio_ID=${aid}" \n')
                self.mpvplayer_val.write(b'\n show-text "${aid}" \n')
        self.audio_track.setText("A:"+str(audio_id))
            
    def load_external_sub(self):
        global Player, sub_id, current_playing_file_path
        external_sub = False
        sub_arr = []
        new_name = self.epn_name_in_list.replace('/', '-')
        if new_name.startswith(self.check_symbol):
            new_name = new_name[1:]
        ext_arr = self.video_type_arr
        if new_name.startswith('.'):
            new_name = new_name[1:]
            new_name = new_name.strip()
        if '.' in new_name:
            ext = new_name.rsplit('.', 1)[1]
            ext_n = ext.strip()
            if ext_n in ext_arr:
                new_name = new_name.rsplit('.', 1)[0]
        new_name_original = new_name
        
        if new_name.endswith('YouTube'):
            new_name = ''.join(new_name.rsplit('YouTube', 1))
            new_name = new_name.strip()
            if new_name.endswith('-'):
                new_name = new_name[:-1]
                new_name = new_name.strip()
                
        new_path = current_playing_file_path.replace('"', '')
        if os.path.exists(new_path):
            sub_name_bytes = bytes(new_path, 'utf-8')
            h = hashlib.sha256(sub_name_bytes)
            sub_name = h.hexdigest()
            sub_path = os.path.join(self.yt_sub_folder, sub_name+'.vtt')
            if os.path.exists(sub_path):
                sub_arr.append(sub_path)
                external_sub = True
                logger.info(sub_path)
        lang_ext = ['.en', '.es', '.jp', '.fr']
        sub_ext = ['.vtt', '.srt', '.ass']
        for i in lang_ext:
            for j in sub_ext:
                k1 = new_name_original+i+j
                k2 = new_name+i+j
                sub_name_1 = os.path.join(self.yt_sub_folder, k1)
                sub_name_2 = os.path.join(self.yt_sub_folder, k2)
                #print(sub_name)
                if os.path.exists(sub_name_1):
                    sub_arr.append(sub_name_1)
                    external_sub = True
                    logger.info(sub_name_1)
                if os.path.exists(sub_name_2):
                    sub_arr.append(sub_name_2)
                    external_sub = True
                    logger.info(sub_name_2)
        logger.info('--new--name--{0}'.format(new_name))
        
            
        if self.mpvplayer_val.processId() > 0 and sub_arr:
            sub_arr.reverse()
            for title_sub in sub_arr:
                if Player == "mplayer":
                    if os.path.exists(title_sub):
                        txt = '\nsub_load '+'"'+title_sub+'"\n'
                        txt_b = bytes(txt, 'utf-8')
                        logger.info("{0} - {1}".format(txt_b, txt))
                        self.mpvplayer_val.write(txt_b)
                else:
                    if os.path.exists(title_sub):
                        txt = '\nsub_add '+'"'+title_sub+'" select\n'
                        txt_b = bytes(txt, 'utf-8')
                        logger.info("{0} - {1}".format(txt_b, txt))
                        self.mpvplayer_val.write(txt_b)
                        
    def toggleSubtitle(self):
        global Player, sub_id
        if self.mpvplayer_val.processId() > 0:
            if Player == "mplayer":
                if not self.mplayer_OsdTimer.isActive():
                    self.mpvplayer_val.write(b'\n osd 1 \n')
                else:
                    self.mplayer_OsdTimer.stop()
                self.mpvplayer_val.write(b'\n sub_select \n')
                self.mpvplayer_val.write(b'\n get_property sub \n')
                self.mplayer_OsdTimer.start(5000)
            else:
                self.mpvplayer_val.write(b'\n cycle sub \n')
                self.mpvplayer_val.write(b'\n print-text "SUB_ID=${sid}" \n')
                self.mpvplayer_val.write(b'\n show-text "${sid}" \n')
        self.subtitle_track.setText('Sub:'+str(sub_id))
    
    def mark_epn_thumbnail_label(self, num):
        global idw
        if idw and idw != str(int(self.tab_5.winId())) and idw != str(int(self.label.winId())):
            try:
                new_cnt = num + self.list2.count()
                p1 = "self.label_epn_{0}.setTextColor(QtCore.Qt.green)".format(new_cnt)
                exec (p1)
                #p1 = "ui.label_epn_{0}.toPlainText()".format(new_cnt)
                #txt = eval(p1)
                txt = self.list2.item(num).text()
                try:
                    p1 = "self.label_epn_{0}.setText('{1}')".format(new_cnt, txt)
                    exec(p1)
                except Exception as e:
                    print(e, '--line--4597--')
                    try:
                        p1 = 'self.label_epn_{0}.setText("{1}")'.format(new_cnt, txt)
                        exec(p1)
                    except Exception as e:
                        print(e)
                p1="self.label_epn_{0}.setAlignment(QtCore.Qt.AlignCenter)".format(new_cnt)
                exec(p1)
            except Exception as e:
                print(e)
    
    def update_thumbnail_position(self, context=None):
        global cur_label_num
        r = self.list2.currentRow()
        if r < 0:
            r = 0
        print(r, '--thumbnail_number--', cur_label_num)
        QtWidgets.QApplication.processEvents()
        p1="self.label_epn_"+str(cur_label_num)+".y()"
        yy=eval(p1)
        self.scrollArea1.verticalScrollBar().setValue(yy-10)
        QtWidgets.QApplication.processEvents()
        self.frame1.show()
        self.gridLayout.setContentsMargins(5, 5, 5, 5)
        self.superGridLayout.setContentsMargins(5, 5, 5, 5)
        self.gridLayout1.setContentsMargins(5, 5, 5, 5)
        self.gridLayout2.setContentsMargins(5, 5, 5, 5)
        #ui.horizontalLayout10.setContentsMargins(0, 0, 0, 0)
        #ui.horizontalLayout10.setSpacing(0)
        self.gridLayout.setSpacing(5)
        self.gridLayout1.setSpacing(5)
        self.gridLayout2.setSpacing(5)
        self.superGridLayout.setSpacing(5)
        self.tab_6.show()
        QtWidgets.QApplication.processEvents()
        p1="self.label_epn_"+str(r)+".setFocus()"
        exec(p1)
        if not context:
            self.mark_epn_thumbnail_label(cur_label_num)
        
    def thumbnail_window_present_mode(self):
        global iconv_r, MainWindow, ui, wget, iconv_r_indicator
        
        if MainWindow.isFullScreen():
            if self.list2.count() == 0:
                return 0
            cur_label = self.list2.currentRow()
            if cur_label<0:
                cur_label = 0
            w = float((self.tab_6.width()-60)/iconv_r)
            h = int(w/self.image_aspect_allowed)
            width=str(int(w))
            height=str(int(h))
            r = self.current_thumbnail_position[0]
            c = self.current_thumbnail_position[1]
            print(r, c, '--thumbnail--7323--')
            p6="self.gridLayout2.addWidget(self.label_epn_"+str(cur_label)+", "+str(r)+", "+str(c)+", 1, 1, QtCore.Qt.AlignCenter)"
            exec(p6)
            QtWidgets.QApplication.processEvents()
            p2="self.label_epn_"+str(cur_label)+".setMaximumSize(QtCore.QSize("+width+", "+height+"))"
            p3="self.label_epn_"+str(cur_label)+".setMinimumSize(QtCore.QSize("+width+", "+height+"))"
            exec(p2)
            exec(p3)

            self.gridLayout.setSpacing(5)
            #self.gridLayout.setContentsMargins(10, 10, 10, 10)
            self.superGridLayout.setContentsMargins(5, 5, 5, 5)
            if wget:
                if wget.processId() > 0:
                    self.goto_epn.hide()
                    self.progress.show()
            self.frame2.show()
            MainWindow.showNormal()
            MainWindow.showMaximized()
            self.frame1.show()
            self.gridLayout.setContentsMargins(5, 5, 5, 5)
            self.superGridLayout.setContentsMargins(5, 5, 5, 5)
            self.gridLayout1.setContentsMargins(5, 5, 5, 5)
            self.gridLayout2.setContentsMargins(5, 5, 5, 5)
            #ui.horizontalLayout10.setContentsMargins(0, 0, 0, 0)
            #ui.horizontalLayout10.setSpacing(0)
            self.gridLayout.setSpacing(5)
            self.gridLayout1.setSpacing(5)
            self.gridLayout2.setSpacing(5)
            self.superGridLayout.setSpacing(5)
            self.tab_6.show()
        else:
            self.thumbnail_label_update()
        QtCore.QTimer.singleShot(1000, partial(self.update_thumbnail_position))
            
    def playerStop(self):
        global quitReally, thumbnail_indicator, total_till, browse_cnt
        global iconv_r_indicator, iconv_r, curR, wget, Player, show_hide_cover
        global show_hide_playlist, show_hide_titlelist, video_local_stream
        global idw, new_tray_widget
        
        if self.mpvplayer_val.processId() > 0:
            quitReally = "yes"
            self.mpvplayer_val.write(b'\n quit \n')
            self.player_play_pause.setText(self.player_buttons['play'])
            if self.tab_6.isHidden() and (str(idw) == str(int(self.tab_5.winId()))):
                if not self.float_window.isHidden():
                    if self.float_window.isFullScreen():
                        self.float_window.showNormal()
                    else:
                        pass
                else:
                    self.tab_5.showNormal()
                    self.tab_5.hide()
                    if self.fullscreen_mode == 0:
                        if show_hide_titlelist == 1:
                            self.list1.show()
                            #self.frame.show()
                        if show_hide_cover == 1:
                            self.label.show()
                            self.text.show()
                        if show_hide_titlelist == 1:
                            self.list2.show()
                            #ui.goto_epn.show()
                        self.list2.setFocus()
                    elif self.fullscreen_mode == 1:
                        self.tab_6.show()
            else:
                if not self.float_window.isHidden():
                    if self.float_window.isFullScreen():
                        self.float_window.showNormal()
                    else:
                        pass
                else:
                    
                    if ((str(idw) != str(int(self.tab_5.winId()))) 
                            and (str(idw) != str(int(self.label.winId())))):
                        if iconv_r_indicator:
                            iconv_r = iconv_r_indicator[0]
                        self.thumbnail_window_present_mode()
                    elif (str(idw) == str(int(self.tab_5.winId()))):
                        self.gridLayout.addWidget(self.tab_6, 0, 1, 1, 1)
                        self.gridLayout.setSpacing(5)
                        self.tab_6.setMaximumSize(10000, 10000)
                        self.tab_5.hide()
                        i = 0
                        thumbnail_indicator[:]=[]
                        if iconv_r_indicator:
                            iconv_r = iconv_r_indicator[0]
                        else:
                            iconv_r = 5
                        QtCore.QTimer.singleShot(1000, partial(self.update_thumbnail_position))
            if MainWindow.isFullScreen():
                MainWindow.showNormal()
                MainWindow.showMaximized()
                MainWindow.setCursor(QtGui.QCursor(QtCore.Qt.ArrowCursor))
                        
                        
    def shufflePlaylist(self):
        global site
        if (site == "Local" or site =="Video" or site == "Music" 
                or site == "PlayLists" or self.epn_arr_list):
            t = self.epn_arr_list[0]
            if '	' in t:
                print("++++++++++++++++")
                m = random.sample(self.epn_arr_list, len(self.epn_arr_list))
                self.epn_arr_list[:] = []
                self.epn_arr_list = m
                self.list2.clear()
                self.update_list2()
            
    def playerPlaylist1(self, val):
        if val == "Shuffle":
            self.shuffleList()
        else:
            self.sortList()
            
    def set_playerLoopFile(self):
        global Player, quitReally, tray, new_tray_widget
        if self.mpvplayer_val.processId() > 0:
            if Player == 'mpv':
                self.mpvplayer_val.write(b'\n set loop-file inf \n')
            else:
                self.mpvplayer_val.write(b'\n set_property loop 0 \n')
                
    def playerLoopFile(self, loop_widget):
        global Player, quitReally, tray, new_tray_widget
        txt = loop_widget.text()
        #txt = self.player_loop_file.text()
        
        if txt == self.player_buttons['unlock']:
            self.player_setLoop_var = 1
            self.player_loop_file.setText(self.player_buttons['lock'])
            new_tray_widget.lock.setText(self.player_buttons['lock'])
            quitReally = 'no'
            if self.mpvplayer_val.processId() > 0:
                if Player == 'mpv':
                    self.mpvplayer_val.write(b'\n set loop-file inf \n')
                else:
                    self.mpvplayer_val.write(b'\n set_property loop 0 \n')
        else:
            self.player_setLoop_var = 0
            self.player_loop_file.setText(self.player_buttons['unlock'])
            new_tray_widget.lock.setText(self.player_buttons['unlock'])
            if self.mpvplayer_val.processId() > 0:
                if Player == 'mpv':
                    self.mpvplayer_val.write(b'\n set loop-file no \n')
                else:
                    self.mpvplayer_val.write(b'\n set_property loop -1 \n')
                
    def playerPlayPause(self):
        global curR, idw, cur_label_num
        
        txt = self.player_play_pause.text() 
        if txt == self.player_buttons['play']:
            if self.mpvplayer_val.processId() > 0:
                if Player == "mpv":
                    self.mpvplayer_val.write(b'\n set pause no \n')
                    self.player_play_pause.setText(self.player_buttons['pause'])
                    txt_osd = '\n osd 1 \n'
                    self.mpvplayer_val.write(bytes(txt_osd, 'utf-8'))
                else:
                    self.mpvplayer_val.write(b'\n pausing_toggle osd_show_progression \n')
            else:
                
                if self.list2.currentItem():
                    curR = self.list2.currentRow()
                    if not idw or idw == str(int(self.tab_5.winId())):
                        self.epnfound()
                    elif idw == str(int(self.label.winId())):
                        pass
                    else:
                        p1 = "self.label_epn_{0}.winId()".format(str(cur_label_num))
                        id_w = eval(p1)
                        idw = str(int(id_w))
                        finalUrl = self.epn_return(curR)
                        self.play_file_now(finalUrl, win_id=idw)
        elif txt == self.player_buttons['pause']:
            if self.mpvplayer_val.processId() > 0:
                if Player == "mpv":
                    self.mpvplayer_val.write(b'\n set pause yes \n')
                    self.player_play_pause.setText(self.player_buttons['play'])
                    txt_osd = '\n osd 3 \n'
                    self.mpvplayer_val.write(bytes(txt_osd, 'utf-8'))
                else:
                    self.mpvplayer_val.write(b'\n pausing_toggle osd_show_progression \n')
            else:
                
                if self.list2.currentItem():
                    curR = self.list2.currentRow()
                    self.epnfound()
        
    def playerPlaylist(self, val):
        global quitReally, playlist_show, site
        global show_hide_cover, show_hide_playlist, show_hide_titlelist
        global show_hide_player, Player, httpd, idw, cur_label_num
        
        self.player_menu_option = [
            'Show/Hide Video', 'Show/Hide Cover And Summary', 
            'Lock Playlist', 'Shuffle', 'Stop After Current File', 
            'Continue(default Mode)', 'Set Media Server User/PassWord', 
            'Start Media Server', 'Broadcast Server', 'Turn ON Remote Control',
            'Set Current Background As Default', 'Settings'
            ]
        
        print(val)
        if val == "Show/Hide Cover And Summary":
            v = str(self.action_player_menu[1].text())
            if self.text.isHidden() and self.label.isHidden():
                self.text.show()
                self.label.show()
                show_hide_cover = 1
                self.tab_5.hide()
                show_hide_player = 0
            elif self.text.isHidden() and not self.label.isHidden():
                self.text.show()
                self.label.show()
                show_hide_cover = 1
                self.tab_5.hide()
                show_hide_player = 0
            elif not self.text.isHidden() and self.label.isHidden():
                self.text.show()
                self.label.show()
                show_hide_cover = 1
                self.tab_5.hide()
                show_hide_player = 0
            else:
                self.text.hide()
                self.label.hide()
                show_hide_cover = 0
                self.tab_5.show()
                show_hide_player = 1
        elif val == "Show/Hide Playlist":
            #if self.tab_6.isHidden():
            if not self.list2.isHidden():
                self.list2.hide()
                self.goto_epn.hide()
                show_hide_playlist = 0
            else:
                self.list2.show()
                #self.goto_epn.show()
                show_hide_playlist = 1
                if MainWindow.isFullScreen():
                    MainWindow.setCursor(QtGui.QCursor(QtCore.Qt.ArrowCursor))
            #else:
            #	self.tab_6.hide()
        elif val == "Show/Hide Title List":
            if not self.list1.isHidden():
                self.list1.hide()
                self.frame.hide()
                show_hide_titlelist = 0
            else:
                self.list1.show()
                #self.frame.show()
                show_hide_titlelist = 1
                if MainWindow.isFullScreen():
                    MainWindow.setCursor(QtGui.QCursor(QtCore.Qt.ArrowCursor))
        elif val == "Lock File":
            v = str(self.action_player_menu[5].text())
            if v == "Lock File":
                self.player_setLoop_var = 1
                self.action_player_menu[5].setText("UnLock File")
                self.player_loop_file.setText("unLock")
                if Player == 'mpv':
                    self.mpvplayer_val.write(b'\n set loop-file inf \n')
                else:
                    self.mpvplayer_val.write(b'\n set_property loop 0 \n')
            elif v == "UnLock File":
                    self.player_setLoop_var = 0
                    self.action_player_menu[5].setText("Lock File")
                    self.player_loop_file.setText("Lock")
                    if Player == 'mpv':
                        self.mpvplayer_val.write(b'\n set loop-file no \n')
                    else:
                        self.mpvplayer_val.write(b'\n set_property loop -1 \n')
        elif val == "Lock Playlist":
            v = str(self.action_player_menu[2].text())
            if v == "Lock Playlist":
                self.playerPlaylist_setLoop_var = 1
                self.action_player_menu[2].setText("UnLock Playlist")
            elif v == "UnLock Playlist":
                    self.playerPlaylist_setLoop_var = 0
                    self.action_player_menu[2].setText("Lock Playlist")
        elif val == "Stop After Current File":
            quitReally = "yes"
            #self.player_setLoop_var = 0
        elif val == "Continue(default Mode)":
            quitReally = "no"
        elif val == "Shuffle":
            self.epn_arr_list = random.sample(self.epn_arr_list, len(self.epn_arr_list))
            self.update_list2()
        elif val == "Show/Hide Video":
            if self.tab_5.isHidden():
                self.tab_5.show()
                show_hide_player = 1
                if not self.label.isHidden():
                    self.label.hide()
                    self.text.hide()
                    show_hide_cover = 0
            else:
                self.tab_5.hide()
                show_hide_player = 0
        elif val =="Start Media Server":
            v= str(self.action_player_menu[7].text())
            if v == 'Start Media Server':
                self.start_streaming = True
                self.action_player_menu[7].setText("Stop Media Server")
                if not self.local_http_server.isRunning():
                    if not self.local_ip_stream:
                        self.local_ip_stream = '127.0.0.1'
                        self.local_port_stream = 9001
                    self.local_http_server = ThreadServerLocal(
                        self.local_ip_stream, self.local_port_stream, ui_widget=ui, 
                        logr=logger, hm=home, window=MainWindow)
                    self.local_http_server.start()
            elif v == 'Stop Media Server':
                self.start_streaming = False
                self.action_player_menu[7].setText("Start Media Server")
                if self.local_http_server.isRunning():
                    self.local_http_server.httpd.shutdown()
                    self.local_http_server.quit()
                    msg = 'Stopping Media Server\n '+self.local_ip_stream+':'+str(self.local_port_stream)
                    #subprocess.Popen(["notify-send", msg])
                    send_notification(msg)
        elif val =="Broadcast Server":
            v= str(self.action_player_menu[8].text())
            if v == 'Broadcast Server' and self.local_http_server.isRunning():
                self.broadcast_server = True
                self.action_player_menu[8].setText("Stop Broadcasting")
                if not self.broadcast_thread:
                    self.broadcast_thread = BroadcastServer(self)
                    self.broadcast_thread.start()
                elif isinstance(self.broadcast_thread, BroadcastServer):
                    if not self.broadcast_thread.isRunning():
                        self.broadcast_thread.start()
            elif v == 'Stop Broadcasting':
                self.broadcast_server = False
                self.action_player_menu[8].setText("Broadcast Server")
            elif not self.local_http_server.isRunning():
                send_notification('No Server To Broadcast. First Start Media Server')
        elif val.lower() == 'turn on remote control':
            v= str(self.action_player_menu[9].text()).lower()
            msg = "Not Able to Take Action"
            if v == 'turn on remote control':
                self.remote_control_field = True
                self.action_player_menu[9].setText("Turn Off Remote Control")
                change_opt_file(HOME_OPT_FILE, 'REMOTE_CONTROL=', 'REMOTE_CONTROL=True')
                msg = "Remote Control Mode Enabled, Now Start Media server to control the player remotely"
            elif v == 'turn off remote control':
                self.remote_control_field = False
                self.remote_control = False
                self.action_player_menu[9].setText("Turn ON Remote Control")
                change_opt_file(HOME_OPT_FILE, 'REMOTE_CONTROL=', 'REMOTE_CONTROL=False')
                msg = "Remote Control Mode Disabled"
            send_notification(msg)
        elif val.lower() == 'set media server user/password':
            new_set = LoginAuth(parent=MainWindow, media_server=True, ui=self, tmp=TMPDIR)
        elif val.lower() == 'settings':
            new_set = LoginAuth(parent=MainWindow, settings=True, ui=self, tmp=TMPDIR)
        elif val == "Set Current Background As Default":
            if (os.path.exists(self.current_background) 
                        and self.current_background != self.default_background):
                    shutil.copy(self.current_background, self.default_background)
        elif val == "Show/Hide Web Browser":
            if self.tab_2.isHidden():
                if self.mpvplayer_val.processId() > 0:
                    self.tab_2.show()
                else:
                    self.showHideBrowser()
            else:
                self.tab_2.hide()
        elif (site == "Music" or site == "Local" or site == "Video" 
                or site == "PlayLists"):
            if val == "Order by Name(Descending)":
                try:
                    self.epn_arr_list = sorted(
                        self.epn_arr_list, key = lambda x : str(x).split('	')[0], 
                        reverse=True)
                    #self.epn_arr_list = naturallysorted(self.epn_arr_list)
                except:
                    self.epn_arr_list = sorted(self.epn_arr_list, 
                                        key = lambda x : x.split('	')[0], 
                                        reverse=True)
                self.update_list2()
            elif val == "Order by Name(Ascending)":
                try:
                    self.epn_arr_list = naturallysorted(self.epn_arr_list)
                    #self.epn_arr_list = sorted(self.epn_arr_list, 
                    #					key = lambda x : str(x).split('	')[0])
                except:
                    self.epn_arr_list = sorted(
                        self.epn_arr_list, key = lambda x : x.split('	')[0])
                self.update_list2()
            elif val == "Order by Date(Descending)":
                try:
                    self.epn_arr_list = sorted(
                        self.epn_arr_list, key = lambda x : os.path.getmtime((
                        str(x).split('	')[1]).replace('"', '')), reverse=True)
                except Exception as e:
                    print(e, '--playlist--contains--online--and --offline--content--')
                    """self.epn_arr_list = sorted(self.epn_arr_list, 
                                        key = lambda x : os.path.getmtime((
                                        x.split('	')[1]).replace('"', '')), 
                                        reverse=True)"""
                self.update_list2()
            elif val == "Order by Date(Ascending)":
                try:
                    self.epn_arr_list = sorted(
                        self.epn_arr_list, key = lambda x : os.path.getmtime((
                        str(x).split('	')[1]).replace('"', '')))
                except Exception as e:
                    print(e, '--playlist--contains--online--and --offline--content--')
                    """self.epn_arr_list = sorted(self.epn_arr_list, 
                                        key = lambda x : os.path.getmtime((
                                        x.split('	')[1]).replace('"', '')))"""
                self.update_list2()
        
    def selectQuality(self):
        global quality
        txt = str(self.sd_hd.text())
        if txt == "SD":
            quality = "sd480p"
            self.sd_hd.setText("480")
        elif txt == "480":
            quality = "hd"
            self.sd_hd.setText("HD")
        elif txt == "HD":
            quality = "best"
            self.sd_hd.setText("BEST")
        elif txt == "BEST":
            quality = "sd"
            self.sd_hd.setText("SD")
        self.quality_val = quality
        
    def filter_btn_options(self):
        if not self.frame.isHidden() and self.tab_6.isHidden():
            if self.go_page.isHidden():
                self.go_page.show()
                self.go_page.setFocus()
                self.list4.show()
                self.go_page.clear()
            else:
                self.list4.hide()
                self.list1.setFocus()
        elif not self.tab_6.isHidden():
            self.label_search.setFocus()
            
    def addToLibrary(self):
        global home
        #self.LibraryDialog.show()
        self.LibraryDialog = QtWidgets.QDialog()
        self.LibraryDialog.setObjectName(_fromUtf8("Dialog"))
        self.LibraryDialog.resize(582, 254)
        self.listLibrary = QtWidgets.QListWidget(self.LibraryDialog)
        self.listLibrary.setGeometry(QtCore.QRect(20, 20, 341, 192))
        self.listLibrary.setObjectName(_fromUtf8("listLibrary"))
        self.AddLibraryFolder = QtWidgets.QPushButton(self.LibraryDialog)
        self.AddLibraryFolder.setGeometry(QtCore.QRect(420, 50, 94, 27))
        self.AddLibraryFolder.setObjectName(_fromUtf8("AddLibraryFolder"))
        self.RemoveLibraryFolder = QtWidgets.QPushButton(self.LibraryDialog)
        self.RemoveLibraryFolder.setGeometry(QtCore.QRect(420, 90, 94, 27))
        self.RemoveLibraryFolder.setObjectName(_fromUtf8("RemoveLibraryFolder"))
        self.LibraryClose = QtWidgets.QPushButton(self.LibraryDialog)
        self.LibraryClose.setGeometry(QtCore.QRect(420, 130, 94, 27))
        self.LibraryClose.setObjectName(_fromUtf8("LibraryClose"))
        self.LibraryDialog.setWindowTitle(_translate("Dialog", "Library Setting", None))
        self.AddLibraryFolder.setText(_translate("Dialog", "ADD", None))
        self.RemoveLibraryFolder.setText(_translate("Dialog", "Remove", None))
        self.LibraryClose.setText(_translate("Dialog", "Close", None))
        self.LibraryDialog.show()
        file_name = os.path.join(home, 'local.txt')
        if os.path.exists(file_name):
            lines = open_files(file_name, True)
            self.listLibrary.clear()
            for i in lines:
                i = i.replace('\n', '')
                self.listLibrary.addItem(i)
        self.AddLibraryFolder.clicked.connect(self.addFolderLibrary)
        self.RemoveLibraryFolder.clicked.connect(self.removeFolderLibrary)
        self.LibraryClose.clicked.connect(self.LibraryDialog.close)
        
        self.LibraryClose.setStyleSheet(
            """font: bold 12px;color:white;background:rgba(0, 0, 0, 30%);
            border:rgba(0, 0, 0, 30%);border-radius: 3px;"""
            )
        self.RemoveLibraryFolder.setStyleSheet(
            """font: bold 12px;color:white;background:rgba(0, 0, 0, 30%);
            border:rgba(0, 0, 0, 30%);border-radius: 3px;"""
            )
        self.AddLibraryFolder.setStyleSheet(
            """font: bold 12px;color:white;background:rgba(0, 0, 0, 30%);
            border:rgba(0, 0, 0, 30%);border-radius: 3px;"""
            )
        self.listLibrary.setStyleSheet(
            """QListWidget{
                font: bold 12px;color:white;background:rgba(0, 0, 0, 30%);
                border:rgba(0, 0, 0, 30%);border-radius: 3px;
                }
                QListWidget:item:selected:active {
                    background:rgba(0, 0, 0, 20%);
                    color: violet;
                }
                QListWidget:item:selected:inactive {
                    border:rgba(0, 0, 0, 30%);
                }
                QMenu{
                    font: bold 12px;color:black;background-image:url('1.png');
                }
            """
            )
        picn = self.default_background
        palette	= QtGui.QPalette()
        palette.setBrush(QtGui.QPalette.Background, QtGui.QBrush(QtGui.QPixmap(picn)))
        self.LibraryDialog.setPalette(palette)
        
    def options_clicked(self):
        global site, bookmark, siteName, opt, genre_num
        #genre_num = 0
        r = self.list3.currentRow()
        item = self.list3.item(r)
        if item and not self.lock_process:
            if not self.tab_6.isHidden():
                if site == "SubbedAnime" or site == "DubbedAnime":
                    siteName = str(self.list3.currentItem().text())
                    opt = "History"
                    self.options('history') 
                elif (site == "PlayLists" or bookmark 
                        or site == "Local" or site =="Music"):
                    self.options('local')
            else:
                if (site == "PlayLists" or bookmark
                        or site == "Local" or site =="Music"):
                    self.options('local') 
                elif site == "SubbedAnime" or site == "DubbedAnime":
                    siteName = str(self.list3.currentItem().text())
                    opt = "notHistory"
                    
    def addFolderLibrary(self):
        print("add")
        fname = QtWidgets.QFileDialog.getExistingDirectory(
                self.LibraryDialog, 'open folder', self.last_dir)
        self.last_dir = fname
        logger.info(self.last_dir)
        logger.info(fname)
        if not fname:
            pass
        else:
            self.listLibrary.addItem(fname)
            file_name = os.path.join(self.home_folder, 'local.txt')
            #if not os.path.exists(file_name):
            write_files(file_name, fname, line_by_line=True)
            
    def removeFolderLibrary(self):
        print("remove")
        index = self.listLibrary.currentRow()
        item  = self.listLibrary.item(index)
        if item:
            file_name = os.path.join(home, 'local.txt')
            lines = open_files(file_name, True)
            logger.info(self.listLibrary.item(index).text())
            self.listLibrary.takeItem(index)
            del item
            del lines[index]
            write_files(file_name, lines, line_by_line=True)
        
    def viewPreference(self):
        global viewMode
        viewMode = str(self.comboView.currentText())
        
    def prev_thumbnails(self):
        global thumbnail_indicator, total_till, browse_cnt, tmp_name
        global label_arr, total_till_epn, iconv_r, iconv_r_indicator
        
        self.scrollArea1.hide()
        self.scrollArea.show()
        i = 0
        try:
            self.labelFrame2.setText(self.list1.currentItem().text())
        except AttributeError as attr_err:
            print(attr_err)
            return 0
        if thumbnail_indicator:
            print("prev_thumb")
            print(thumbnail_indicator)
            thumbnail_indicator.pop()
            print(thumbnail_indicator)
            while(i<total_till_epn):
                t = "self.label_epn_"+str(i)+".deleteLater()"
                exec (t)
                i = i+1
            total_till_epn=0
        print(total_till, 2*self.list1.count()-1, '--prev-thumbnail--')
        if self.mpvplayer_val.processId() > 0:
            print(self.mpvplayer_val.processId(), '--prev-thumb--')
            iconv_r = 1
            self.next_page('not_deleted')
            QtWidgets.QApplication.processEvents()
            row = self.list1.currentRow()
            p1 = "self.label_"+str(row)+".y()"
            yy=eval(p1)
            self.scrollArea.verticalScrollBar().setValue(yy)
        elif total_till > 0 and total_till == 2*self.list1.count():
            row = self.list1.currentRow()
            p1 = "self.label_"+str(row)+".y()"
            yy=eval(p1)
            self.scrollArea.verticalScrollBar().setValue(yy)
            self.scrollArea1.hide()
            self.scrollArea.show()
        else:
            self.next_page('deleted')
            row = self.list1.currentRow()
            p1 = "self.label_"+str(row)+".y()"
            yy=eval(p1)
            self.scrollArea.verticalScrollBar().setValue(yy)
            self.scrollArea1.hide()
            self.scrollArea.show()
                
    def mouseMoveEvent(self, event):
        print("hello how r u" )
        
    def mplayer_unpause(self):
        global fullscr, Player, buffering_mplayer, mpv_indicator
        global cache_empty, pause_indicator
        buffering_mplayer = "no"
        self.mplayer_pause_buffer = False
        self.mplayer_nop_error_pause = False
        if Player == "mplayer":
            self.mpvplayer_val.write(b'\n pause \n')
        else:
            self.mpvplayer_val.write(b'\n set pause no \n')
            if mpv_indicator:
                mpv_indicator.pop()
                cache_empty = 'no'
            if pause_indicator:
                pause_indicator.pop()
        print("UnPausing")
        if MainWindow.isFullScreen():
            if not self.frame_timer.isActive():
                self.frame1.hide()
                
    def frame_options(self):
        global Player, wget
        global fullscr, idwMain, idw, quitReally, new_epn, toggleCache
        print("Frame Hiding" )
        if MainWindow.isFullScreen():
            self.frame1.hide()
            self.gridLayout.setSpacing(5)
            
    def webStyle(self, web):
        global desktop_session
        try:
            if desktop_session.lower() != 'plasma':
                web.setStyleSheet(
                    """font: bold 12px;color:white;background:rgba(0, 0, 0, 30%);
                    border:rgba(0, 0, 0, 30%);border-radius: 3px;""")
                web.setStyleSheet(
                    """QMenu{font: bold 12px;color:black;
                    background-image:url('1.png');}""")
        except NameError as e:
            print(e)
            desktop_session = 'lxde'

    def setPlayerFocus(self):
        global player_focus
        player_focus = 1 - player_focus
        if player_focus == 1:
            self.tab_5.show()
            self.tab_5.setFocus()
            self.list1.hide()
            self.label.hide()
            self.text.hide()
            self.frame.hide()
            if not self.tab_6.isHidden():
                self.list2.hide()
                self.goto_epn.hide()
        else:
            self.tab_5.hide()
            self.list1.show()
            self.list2.show()
            self.text.show()
            self.label.show()
            self.list1.setFocus()
            
    def PlayEpn(self):
        global name, epn, direct_epn_browser, opt, browse_cnt, curR
        val = self.btnEpnList.currentIndex()
        logger.info("val="+str(val))
        if val > 0:
            epn = str(self.btnEpnList.currentText())
            logger.info(epn)
            direct_epn_browser=1
            val = val-1
            curR = val
            self.list2.setCurrentRow(val)
            self.epnfound()
            
    def go_opt_options_btn20(self):
        global site, home, opt, browse_cnt
        global pict_arr, name_arr, summary_arr, total_till, browse_cnt, tmp_name
        global label_arr
        j=0
        opt = str(self.comboBox30.currentText())
        print(opt)
        for index in range(self.list3.count()):
            k=str(self.list3.item(index).text())
            if k == opt:
                self.list3.setCurrentRow(j)
                print(k)
                print(self.list3.currentItem().text())
                break
            j = j+1
        self.options('Nill')
        pict_arr[:]=[]
        name_arr[:]=[]
        summary_arr[:]=[]
        i = 0
        while(i<total_till):
            t = "self.label_"+str(i)+".close()"
            exec (t)
            print(str(i)+" cleared")
            i = i+1
    
        total_till=0	
        label_arr[:]=[]
        browse_cnt=0
        if opt == "History":
            self.setPreOpt()
            self.next_page('deleted')
        elif opt == "Random":
            self.shuffleList()
            self.next_page('deleted')
        else:
            self.next_page('deleted')
    
    def go_opt_options(self):
        global site, opt
        j=0
        opt = str(self.btnOpt.currentText())
        for index in range(self.list3.count()):
            k=str(self.list3.item(index).text())
            if k == opt:
                self.list3.setCurrentRow(j)
                break
            j = j+1
        self.options('Nill')
    
    def load_more(self, value):
        global browse_cnt, opt, labelGeometry
        val1 = labelGeometry
        
    def browse_epn(self):
        global name, epn, direct_epn_browser, opt, browse_cnt, curR
        if opt=="History":
            self.scrollArea.verticalScrollBar().setValue(
                self.scrollArea.verticalScrollBar().minimum())
        else:
            val=self.scrollArea.verticalScrollBar().minimum()
            self.scrollArea.verticalScrollBar().setValue(val)
        
        val = self.btn10.currentIndex()
        logger.info("val="+str(val))
        if val > 0:
            epn = str(self.btn10.currentText())
            logger.info(epn)
            direct_epn_browser=1
            val = val-1
            curR = val
            self.list2.setCurrentRow(val)
            self.epnfound()
            self.tab_6.hide()
            
    def browserView_view(self):
        global site, home, opt, browse_cnt
        global pict_arr, name_arr, summary_arr, total_till, browse_cnt, tmp_name
        global label_arr, list1_items
        pict_arr[:]=[]
        name_arr[:]=[]
        summary_arr[:]=[]
        if site == "SubbedAnime" or site == "DubbedAnime":
            j=0
            t = str(self.comboBox30.currentText())
            for index in range(self.list3.count()):
                k=str(self.list3.item(index).text())
                if k == t:
                    self.list3.setCurrentRow(j)
                    break
                j = j+1
        opt1 = ""
        opt1 = str(self.comboBox20.currentText())
        print(total_till)
        i = 0
        while(i<total_till):
            t = "self.label_"+str(i)+".close()"
            exec (t)
            #print str(i)+" cleared"
            i = i+1
        total_till=0	
        label_arr[:]=[]
        browse_cnt=0
        tmp_name[:]=[]
        if opt1 == "History":
            self.setPreOpt()
            self.next_page('deleted')
        elif opt1 == "Random" or opt1 == "List":
            self.next_page('deleted')
            
    def browserView(self):
        global site, home, opt, browse_cnt
        global pict_arr, name_arr, summary_arr, total_till, browse_cnt
        global tmp_name, label_arr, list1_items, thumbnail_indicator
        
        pict_arr[:]=[]
        name_arr[:]=[]
        summary_arr[:]=[]
        self.scrollArea1.hide()
        self.scrollArea.show()
        if site == "SubbedAnime" or site == "DubbedAnime":
            j=0
            t = str(self.comboBox30.currentText())
            for index in range(self.list3.count()):
                k=str(self.list3.item(index).text())
                if k == t:
                    self.list3.setCurrentRow(j)
                    break
                j = j+1
        opt1 = ""
        opt1 = str(self.comboBox20.currentText())
        print(total_till)
        i = 0
        thumbnail_indicator[:]=[]
        while(i<total_till):
            t = "self.label_"+str(i)+".deleteLater()"
            exec (t)
            i = i+1
        total_till=0	
        label_arr[:]=[]
        browse_cnt=0
        tmp_name[:]=[]
        if opt == "History":
            self.setPreOpt()
            self.next_page()
        else:
            self.next_page()
            
    def display_image(self, br_cnt, br_cnt_opt, dimn=None):
        global site, name, base_url, name1, embed, opt, pre_opt, mirrorNo, list1_items
        global list2_items, quality, row_history, home, epn, iconv_r
        global tab_6_size_indicator
        global labelGeometry, video_local_stream
        global pict_arr, name_arr, summary_arr, total_till, browse_cnt, tmp_name
        global label_arr, hist_arr, bookmark, status, thumbnail_indicator
        global siteName, category, finalUrlFound, refererNeeded
        
        browse_cnt = br_cnt
        name=tmp_name[browse_cnt]
        length = len(tmp_name)
        m =[]
        if (bookmark and os.path.exists(os.path.join(home, 'Bookmark', status+'.txt'))):
            file_name = os.path.join(home, 'Bookmark', status+'.txt')
            line_a = open_files(file_name, True)
            tmp = line_a[browse_cnt]
            tmp = re.sub('\n', '', tmp)
            tmp1 = tmp.split(':')
            site = tmp1[0]
            if site == "Music" or site == "Video":
                opt = "Not Defined"
                if site == "Music":
                    music_opt = tmp1[1]
                else:
                    video_opt = tmp1[1]
            else:
                opt = tmp1[1]
            pre_opt = tmp1[2]
            siteName = tmp1[2]
            base_url = int(tmp1[3])
            embed = int(tmp1[4])
            name = tmp1[5]
            logger.info(name)
            if len(tmp1) > 6:
                if tmp1[6] == "True":
                    finalUrlFound = True
                else:
                    finalUrlFound = False
                if tmp1[7] == "True":
                    refererNeeded = True
                else:
                    refererNeeded = False
                if len(tmp1) >= 9:
                    if tmp1[8] == "True":
                        video_local_stream = True
                    else:
                        video_local_stream = False
                print(finalUrlFound)
                print(refererNeeded)
                print(video_local_stream)
            else:
                refererNeeded = False
                finalUrlFound = False
                video_local_stream = False
            logger.info(site + ":"+opt)
        
        label_arr.append(name)
        label_arr.append(name)
        
        if (site == "Local") and opt !="History":
            m = []
            name=self.original_path_name[browse_cnt]
            if os.path.exists(os.path.join(home, 'Local', name)):
                if os.path.exists(os.path.join(home, 'Local', name, 'Ep.txt')):
                    lines = open_files(
                            os.path.join(home, 'Local', name, 'Ep.txt'), True)
                    for i in lines:
                        j = i.strip()
                        k = os.path.basename(j)
                        m.append(k)
                picn = os.path.join(home, 'Local', name, 'thumbnail.jpg')
                m.append(picn)
                if os.path.exists(
                        os.path.join(home, 'Local', name, 'summary.txt')):
                    summary = open_files(
                            os.path.join(home, 'Local', name, 'summary.txt'), 
                            False)
                    m.append(summary)
                else:
                    m.append("Summary Not Available")
        elif site == "Video":
            picn = os.path.join(home, 'Local', name, 'thumbnail.jpg')
            m.append(picn)
            if os.path.exists(os.path.join(home, 'Local', name, 'summary.txt')):
                summary = open_files(
                        os.path.join(home, 'Local', name, 'summary.txt'), 
                        False)
                m.append(summary)
            else:
                m.append("Summary Not Available")
        elif site == "Music":
            picn = os.path.join(home, 'Music', 'Artist', name, 'thumbnail.jpg')
            m.append(picn)
            logger.info(picn)
            if os.path.exists(os.path.join(home, 'Music', 'Artist', name, 'bio.txt')):
                summary = open_files(
                        os.path.join(home, 'Music', 'Artist', name, 'bio.txt'), 
                        False)
                m.append(summary)
            else:
                m.append("Summary Not Available")
        elif opt == "History":
            if site == "SubbedAnime" or site == "DubbedAnime":
                dir_name =os.path.join(home, 'History', site, siteName, name)	
            elif site == "Local":
                if not bookmark:
                    name = self.original_path_name[browse_cnt]
                dir_name =os.path.join(home, 'History', site, name)
            else:
                dir_name =os.path.join(home, 'History', site, name)
            if os.path.exists(dir_name):
                logger.info(dir_name)
                picn = os.path.join(home, 'History', site, name, 'poster.jpg')
                thumbnail = os.path.join(home, 'History', site, name, 'thumbnail.jpg')
                picn = thumbnail
                m.append(os.path.join(dir_name, 'poster.jpg'))
                try:	
                    summary = open_files(
                            os.path.join(dir_name, 'summary.txt'), False)
                    m.append(summary)
                except:
                    m.append("Not Available")
            else:
                m.append('No.jpg')
                m.append('Not Available')
        try:
            summary = m.pop()
        except:
            summary = "Not Available"
        try:
            picn = m.pop()
        except:
            picn = "No.jpg"
        if br_cnt_opt == "image":
            if picn != "No.jpg" and os.path.exists(picn):
                if dimn:
                    picn = self.image_fit_option(picn, '', fit_size=6, widget_size=(int(dimn[0]), int(dimn[1])))
                img = QtGui.QPixmap(picn, "1")
                q1="self.label_"+str(browse_cnt)+".setPixmap(img)"
                exec (q1)
            if site == "Local":
                name1 = name.split('@')[-1]
            else:
                name1 = name
            q3="self.label_"+str(length+browse_cnt)+".setText((name1))"
            exec (q3)
            try:
                sumry = "<html><h1>"+name1+"</h1><head/><body><p>"+summary+"</p>"+"</body></html>"
            except:
                sumry = "<html><h1>"+str(name1)+"</h1><head/><body><p>"+str(summary)+"</p>"+"</body></html>"
            q4="self.label_"+str(length+browse_cnt)+".setToolTip((sumry))"			
            exec (q4)
            p8="self.label_"+str(length+browse_cnt)+".setAlignment(QtCore.Qt.AlignCenter)"
            exec(p8)
            total_till = total_till+2
            if total_till%(2*iconv_r) == 0:
                QtWidgets.QApplication.processEvents()
        
    def next_page(self, value_str):
        global site, name, base_url, name1, embed, opt, pre_opt, mirrorNo
        global list1_items
        global list2_items, quality, row_history, home, epn, iconv_r
        global tab_6_size_indicator
        global labelGeometry, total_till
        global pict_arr, name_arr, summary_arr, total_till, browse_cnt, tmp_name
        global label_arr, hist_arr, bookmark, status, thumbnail_indicator
        global siteName, category, finalUrlFound, refererNeeded
        
        self.lock_process = True
        m=[]
        if value_str == "deleted":
            for i in range(total_till):
                t = "self.label_"+str(i)+".clear()"
                exec (t)
                t = "self.label_"+str(i)+".deleteLater()"
                exec (t)
            total_till = 0
        if total_till==0 or value_str=="not_deleted":
            tmp_name[:] = []
            for i in range(self.list1.count()):
                    txt = str(self.list1.item(i).text())
                    tmp_name.append(txt)
            length = len(tmp_name)
            logger.info(tmp_name)
        else:
            if (site == "Local" or site == "None" or site == "PlayLists" 
                    or site=="Video" or site=="Music" or opt == "History"):
                length = self.list1.count()
            
        if iconv_r == 1 and not self.tab_5.isHidden():
            self.tab_6.setMaximumSize(self.width_allowed, 10000)
        else:
            self.tab_6.setMaximumSize(10000, 10000)
        print("width="+str(self.tab_6.width()))
        
        if iconv_r > 1:
            w = float((self.tab_6.width()-60)/iconv_r)
            #h = float((9*w)/16)
            h = int(w/self.image_aspect_allowed)
            if self.tab_5.isHidden() and self.mpvplayer_val:
                if self.mpvplayer_val.processId() > 0:
                    if tab_6_size_indicator:
                        l= (tab_6_size_indicator[0]-60)/iconv_r
                    else:
                        l = self.tab_6.width()-60
                    w = float(l)
                    #h = float((9*w)/16)
                    h = int(w/self.image_aspect_allowed)
        elif iconv_r == 1:
            w = float(self.tab_6.width()-60)
            #h = float((9*w)/16)
            h = int(w/self.image_aspect_allowed)
            
        width = str(int(w))
        height = str(int(h))
        if self.icon_size_arr:
            self.icon_size_arr[:]=[]
        self.icon_size_arr.append(width)
        self.icon_size_arr.append(height)
        print(length)
        print(browse_cnt)
        dim_tuple = (width, height)
        if total_till==0 or value_str=="not_deleted":
            i = 0
            j = iconv_r+1
            k = 0
            if opt != "History":
                if (site == "Local" or site == "Video" or site == "Music" 
                        or site=='PlayLists'):
                    length = len(tmp_name)
                else:
                    length = 100
            if iconv_r == 1:
                j1 = 3
            else:
                j1 = 2*iconv_r
            if total_till == 0:
                value_str = "deleted"
            while(i<length):
                print(value_str, '--value--str--')
                if value_str == "deleted":
                    p1= "self.label_"+str(i)+" = TitleThumbnailWidget(self.scrollAreaWidgetContents)"
                    p4 = "self.label_{0}.setup_globals(self, home, TMPDIR, logger)".format(i)
                    p7 = "l_"+str(i)+" = weakref.ref(self.label_"+str(i)+")"
                    exec(p1)
                    exec(p4)
                    exec(p7)
                p2="self.label_"+str(i)+".setMaximumSize(QtCore.QSize("+width+", "+height+"))"
                p3="self.label_"+str(i)+".setMinimumSize(QtCore.QSize("+width+", "+height+"))"
                #p4="self.label_"+str(i)+".setScaledContents(True)"
                p5="self.label_"+str(i)+".setObjectName(_fromUtf8("+'"'+"label_"+str(i)+'"'+"))"
                p6="self.gridLayout1.addWidget(self.label_"+str(i)+", "+str(j)+", "+str(k)+", 1, 1, QtCore.Qt.AlignCenter)"
                p8 = "self.label_{0}.setAlignment(QtCore.Qt.AlignCenter|QtCore.Qt.AlignBottom)".format(str(i))
                p9 = "self.label_{0}.setMouseTracking(True)".format(str(i))
                exec(p2)
                exec(p3)
                #exec(p4)
                exec(p5)
                exec(p6)
                exec(p8)
                exec(p9)
                if value_str == "deleted":
                    p1="self.label_"+str(length+i)+" = QtWidgets.QTextEdit(self.scrollAreaWidgetContents)"
                    p7 = "l_"+str(length+i)+" = weakref.ref(self.label_"+str(length+i)+")"
                    exec(p1)
                    exec(p7)
                    print("creating")
                p2="self.label_"+str(length+i)+".setMinimumWidth("+width+")"
                p3="self.label_"+str(length+i)+".setMaximumHeight("+height+")"
                p4 = "self.label_"+str(length+i)+".lineWrapMode()"
                p5="self.label_"+str(length+i)+".setObjectName(_fromUtf8("+'"'+"label_"+str(length+i)+'"'+"))"
                p6="self.gridLayout1.addWidget(self.label_"+str(length+i)+", "+str(j1)+", "+str(k)+", 1, 1, QtCore.Qt.AlignCenter)"
                #p8="self.label_"+str(length+i)+".setAlignment(QtCore.Qt.AlignCenter)"
                p9="self.label_"+str(length+i)+".setReadOnly(True)"
                exec(p2)
                exec(p3)
                exec(p4)
                exec(p5)
                exec(p6)
                #exec(p8)
                exec(p9)
                if value_str == "deleted":
                    self.display_image(i, "image", dimn=dim_tuple)
                    
                i=i+1
                k = k+1
                if (i%10) == 0 or i == 0:
                    QtWidgets.QApplication.processEvents()
                if k == iconv_r:
                    j = j + 2*iconv_r
                    j1 = j1+2*iconv_r
                    k = 0
                    
        QtWidgets.QApplication.processEvents()
        self.lock_process = False
            
    def thumbnail_label_update(self):
        global total_till, browse_cnt, home, iconv_r, site
        global thumbnail_indicator, tab_6_size_indicator
        global finalUrlFound, total_till_epn
        
        m=[]
        self.scrollArea.hide()
        self.scrollArea1.show()
        if iconv_r == 1 and not self.tab_5.isHidden():
            self.tab_6.setMaximumSize(self.width_allowed, 16777215)
        else:
            self.tab_6.setMaximumSize(16777215, 16777215)
        print("width="+str(self.tab_6.width()))
        
        if iconv_r > 1:
            w = float((self.tab_6.width()-60)/iconv_r)
            #h = float((9*w)/16)
            h = int(w/self.image_aspect_allowed)
            if self.tab_5.isHidden() and self.mpvplayer_val:
                if self.mpvplayer_val.processId() > 0:
                    if tab_6_size_indicator:
                        l= (tab_6_size_indicator[0]-60)/iconv_r
                    else:
                        l = self.tab_6.width()-60
                    w = float(l)
                    #h = float((9*w)/16)
                    h = int(w/self.image_aspect_allowed)
        elif iconv_r == 1:
            w = float(self.tab_6.width()-60)
            #w = float(self.tab_6.width())
            #h = float((9*w)/16)
            h = int(w/self.image_aspect_allowed)
        width = str(int(w))
        height = str(int(h))
        print("self.width="+width)
        print("self.height="+height)
        
        if self.icon_size_arr:
            self.icon_size_arr[:]=[]
            
        self.icon_size_arr.append(width)
        self.icon_size_arr.append(height)
        
        if not thumbnail_indicator:
            thumbnail_indicator.append("Thumbnail View")
        length = self.list2.count()
    
        if total_till_epn > 0:
            i = 0
            #j = 5
            j = iconv_r+1
            k = 0
            while(i<length):
                p2="self.label_epn_"+str(i)+".setMaximumSize(QtCore.QSize("+width+", "+height+"))"
                p3="self.label_epn_"+str(i)+".setMinimumSize(QtCore.QSize("+width+", "+height+"))"
                #p4="self.label_epn_"+str(i)+".setScaledContents(True)"
                p5="self.label_epn_"+str(i)+".setObjectName(_fromUtf8("+'"'+"label_epn_"+str(i)+'"'+"))"
                p6="self.gridLayout2.addWidget(self.label_epn_"+str(i)+", "+str(j)+", "+str(k)+", 1, 1, QtCore.Qt.AlignCenter)"
                exec (p2)
                exec (p3)
                #exec (p4)
                exec (p5)
                exec (p6)
                i=i+1
                k = k+1
                if k == iconv_r:
                    j = j + 2*iconv_r
                    k = 0
                    
            length1 = 2*length
            i = length
            if iconv_r == 1:
                j = 3
            else:
                j = 2*iconv_r
            k = 0
            while(i<length1):
                p2="self.label_epn_"+str(i)+".setMinimumWidth("+width+")"
                p5="self.label_epn_"+str(i)+".setObjectName(_fromUtf8("+'"'+"label_epn_"+str(i)+'"'+"))"
                p6="self.gridLayout2.addWidget(self.label_epn_"+str(i)+", "+str(j)+", "+str(k)+", 1, 1, QtCore.Qt.AlignCenter)"
                exec (p2)
                exec (p5)
                exec (p6)
                i=i+1
                k = k+1
                if k == iconv_r:
                    j = j+2*iconv_r
                    k = 0
            total_till_epn = length1
        print(browse_cnt)
        print(length)
            
    def thumbnail_label_update_epn(self):
        global total_till, browse_cnt, home, iconv_r, site
        global thumbnail_indicator, tab_6_size_indicator
        global finalUrlFound, total_till_epn
        
        m=[]
        self.scrollArea.hide()
        self.scrollArea1.show()
        if iconv_r == 1 and not self.tab_5.isHidden():
            self.tab_6.setMaximumSize(self.width_allowed, 10000)
        else:
            self.tab_6.setMaximumSize(10000, 10000)
        print("width="+str(self.tab_6.width()))
        
        if iconv_r > 1:
            w = float((self.tab_6.width()-60)/iconv_r)
            #h = float((9*w)/16)
            h = int(w/self.image_aspect_allowed)
            if self.tab_5.isHidden() and self.mpvplayer_val:
                if self.mpvplayer_val.processId() > 0:
                    if tab_6_size_indicator:
                        l= (tab_6_size_indicator[0]-60)/iconv_r
                    else:
                        l = self.tab_6.width()-60
                    w = float(l)
                    #h = float((9*w)/16)
                    h = int(w/self.image_aspect_allowed)
        elif iconv_r == 1:
            w = float(self.tab_6.width()-60)
            #h = float((9*w)/16)
            h = int(w/self.image_aspect_allowed)
        width = str(int(w))
        height = str(int(h))
        print("self.width="+width)
        print("self.height="+height)
        if self.icon_size_arr:
            self.icon_size_arr[:]=[]
        self.icon_size_arr.append(width)
        self.icon_size_arr.append(height)
        if not thumbnail_indicator:
            thumbnail_indicator.append("Thumbnail View")
        length = self.list2.count()
    
        if total_till_epn > 0:
            i = 0
            j = iconv_r+1
            k = 0
            while(i<length):
                p2="self.label_epn_"+str(i)+".setMaximumSize(QtCore.QSize("+width+", "+height+"))"
                p3="self.label_epn_"+str(i)+".setMinimumSize(QtCore.QSize("+width+", "+height+"))"
                #p4="self.label_epn_"+str(i)+".setScaledContents(True)"
                p5="self.label_epn_"+str(i)+".setObjectName(_fromUtf8("+'"'+"label_epn_"+str(i)+'"'+"))"
                p6="self.gridLayout2.addWidget(self.label_epn_"+str(i)+", "+str(j)+", "+str(k)+", 1, 1, QtCore.Qt.AlignCenter)"
                exec (p2)
                exec (p3)
                #exec (p4)
                exec (p5)
                exec (p6)
                i=i+1
                k = k+1
                if k == iconv_r:
                    j = j + 2*iconv_r
                    k = 0
        
            length1 = 2*length
            i = length
            if iconv_r == 1:
                j = 3
            else:
                j = 2*iconv_r
            k = 0
        
            while(i<length1):
                p2="self.label_epn_"+str(i)+".setMinimumWidth("+width+")"
                p5="self.label_epn_"+str(i)+".setObjectName(_fromUtf8("+'"'+"label_epn_"+str(i)+'"'+"))"
                p6="self.gridLayout2.addWidget(self.label_epn_"+str(i)+", "+str(j)+", "+str(k)+", 1, 1, QtCore.Qt.AlignCenter)"
                exec (p2)
                exec (p5)
                exec (p6)
                i=i+1
                k = k+1
                if k == iconv_r:
                    j = j+2*iconv_r
                    k = 0
            total_till_epn = length1
            
    def get_thumbnail_image_path(self, row_cnt, row_string):
        global site, home, name
        picn = ''
        title = row_string.strip()
        
        path = ''
        if site == "Local" or site=="None" or site == "Music" or site == "Video":
            if '	' in title:
                nameEpn = title.split('	')[0]
                
                path = title.split('	')[1]
            else:
                nameEpn = os.path.basename(title)
                path = title
            if path.startswith('abs_path='):
                path = self.if_path_is_rel(path, thumbnail=True)
            if self.list1.currentItem():
                name_t = self.list1.currentItem().text()
            else:
                name_t = ''
            if self.list3.currentItem():
                if self.list3.currentItem().text() == 'Playlist':
                    picnD = os.path.join(home, 'thumbnails', 'PlayLists', name_t)
                else:
                    picnD = os.path.join(home, 'thumbnails', site, name_t)
            else:
                picnD = os.path.join(home, 'thumbnails', site, name_t)
            if not os.path.exists(picnD):
                try:
                    os.makedirs(picnD)
                except Exception as e:
                    print(e)
                    return os.path.join(home, 'default.jpg')
            picn = os.path.join(picnD, nameEpn)+'.jpg'
            picn = picn.replace('#', '', 1)
            if picn.startswith(self.check_symbol):
                picn = picn[1:]
            path = path.replace('"', '')
            if site == "Music":
                if os.path.exists(picn):
                    if os.stat(picn).st_size == 0:
                        art_n =title.split('	')[2]
                        pic = os.path.join(home, 'Music', 'Artist', art_n, 'thumbnail.jpg')
                        if os.path.exists(pic):
                            picn = pic
        elif site == "PlayLists":
            item = self.list2.item(row_cnt)
            if item:
                nameEpn = title.split('	')[0]
                nameEpn = str(nameEpn)
                try:
                    path = title.split('	')[1]
                    if path.startswith('abs_path='):
                        path = self.if_path_is_rel(path, thumbnail=True)
                except:
                    return ''
                playlist_dir = os.path.join(home, 'thumbnails', 'PlayLists')
                if not os.path.exists(playlist_dir):
                    try:
                        os.makedirs(playlist_dir)
                    except Exception as e:
                        print(e)
                        return os.path.join(home, 'default.jpg')
                pl_n = self.list1.currentItem().text()
                playlist_name = os.path.join(playlist_dir, pl_n)
                if not os.path.exists(playlist_name):
                    os.makedirs(playlist_name)
                picnD = os.path.join(playlist_name, nameEpn)
                picn = picnD+'.jpg'
                picn = picn.replace('#', '', 1)
                if picn.startswith(self.check_symbol):
                    picn = picn[1:]
                path = path.replace('"', '')
        else:
            if finalUrlFound == True:
                if '	' in title:
                    nameEpn = title.split('	')[0]
                
                else:
                    nameEpn = os.path.basename(title)
            else:
                if '	' in title:
                    nameEpn = title.split('	')[0]
                else:
                    nameEpn = title
            picnD = os.path.join(home, 'thumbnails', name)
            if not os.path.exists(picnD):
                try:
                    os.makedirs(picnD)
                except Exception as e:
                    print(e)
                    return os.path.join(home, 'default.jpg')
            picn = os.path.join(picnD, nameEpn+'.jpg')
            picn = picn.replace('#', '', 1)
            if picn.startswith(self.check_symbol):
                picn = picn[1:]
        inter = "10s"
        if ((picn and not os.path.exists(picn) and 'http' not in path) 
                or (picn and not os.path.exists(picn) and 'http' in path 
                and 'youtube.com' in path )):
            path = path.replace('"', '')
            if 'http' in path and 'youtube.com' in path and '/watch?' in path:
                path = self.create_img_url(path)
            self.threadPoolthumb.append(ThreadingThumbnail(self, logger, path, picn, inter))
            self.threadPoolthumb[len(self.threadPoolthumb)-1].finished.connect(self.thumbnail_generated)
            length = len(self.threadPoolthumb)
            if length == 1:
                if not self.threadPoolthumb[0].isRunning():
                    self.threadPoolthumb[0].start()
        return picn
        
    def thumbnailEpn(self):
        global total_till, browse_cnt, home, iconv_r, site
        global thumbnail_indicator, tab_6_size_indicator
        global finalUrlFound, home, total_till_epn
        
        m=[]
        self.scrollArea.hide()
        self.scrollArea1.show()
        if iconv_r == 1 and not self.tab_5.isHidden():
            self.tab_6.setMaximumSize(self.width_allowed, 16777215)
        else:
            self.tab_6.setMaximumSize(16777215, 16777215)
        print("width="+str(self.tab_6.width()))
        if iconv_r > 1:
            w = float((self.tab_6.width()-60)/iconv_r)
            h = int(w/self.image_aspect_allowed)
            if self.tab_5.isHidden() and self.mpvplayer_val:
                if self.mpvplayer_val.processId() > 0:
                    if tab_6_size_indicator:
                        l= (tab_6_size_indicator[0]-60)/iconv_r
                    else:
                        l = self.tab_6.width()-60
                    w = float(l)
                    h = int(w/self.image_aspect_allowed)
        elif iconv_r == 1:
            w = float(self.tab_6.width()-60)
            h = int(w/self.image_aspect_allowed)
        width = str(int(w))
        height = str(int(h))
        
        if self.icon_size_arr:
            self.icon_size_arr[:]=[]
        self.icon_size_arr.append(width)
        self.icon_size_arr.append(height)
        print("self.width="+width)
        print("self.height="+height)
        if not thumbnail_indicator:
            thumbnail_indicator.append("Thumbnail View")
        length = self.list2.count()
    
        if total_till_epn==0:
            i = 0
            #j = 5
            j = iconv_r+1
            k = 0
            while(i<length):
                p1="self.label_epn_"+str(i)+" = ThumbnailWidget(self.scrollAreaWidgetContents1)"
                p4 = "self.label_epn_{0}.setup_globals(MainWindow, ui, home, TMPDIR, logger, screen_width, screen_height)".format(i)
                p7 = "l_"+str(i)+" = weakref.ref(self.label_epn_"+str(i)+")"
                p2="self.label_epn_"+str(i)+".setMaximumSize(QtCore.QSize("+width+", "+height+"))"
                p3="self.label_epn_"+str(i)+".setMinimumSize(QtCore.QSize("+width+", "+height+"))"
                p5="self.label_epn_"+str(i)+".setObjectName(_fromUtf8("+'"'+"label_epn_"+str(i)+'"'+"))"
                p6="self.gridLayout2.addWidget(self.label_epn_"+str(i)+", "+str(j)+", "+str(k)+", 1, 1, QtCore.Qt.AlignCenter)"
                p8 = "self.label_epn_{0}.setAlignment(QtCore.Qt.AlignCenter|QtCore.Qt.AlignBottom)".format(str(i))
                p12="self.label_epn_"+str(i)+".setMouseTracking(True)"
                exec(p1)
                exec(p4)
                exec(p7)
                exec(p2)
                exec(p3)
                exec(p5)
                exec(p6)
                exec(p8)
                exec(p12)
                i=i+1
                if (i%50) == 0:
                    QtWidgets.QApplication.processEvents()
                    logger.info('created {0} label-frame'.format(i))
                k = k+1
                if k == iconv_r:
                    j = j + 2*iconv_r
                    k = 0
        
            length1 = 2*length
            i = length
            if iconv_r == 1:
                j = 3
            else:
                j = 2*iconv_r
            k = 0
            hei_ght= str(int((int(height)/2)))
            while(i<length1):
                p1="self.label_epn_"+str(i)+" = QtWidgets.QTextEdit(self.scrollAreaWidgetContents1)"
                p7 = "l_"+str(i)+" = weakref.ref(self.label_epn_"+str(i)+")"
                p2="self.label_epn_"+str(i)+".setMinimumWidth("+width+")"
                p5="self.label_epn_"+str(i)+".setObjectName(_fromUtf8("+'"'+"label_epn_"+str(i)+'"'+"))"
                p6="self.gridLayout2.addWidget(self.label_epn_"+str(i)+", "+str(j)+", "+str(k)+", 1, 1, QtCore.Qt.AlignCenter)"
                
                p9="self.label_epn_"+str(i)+".setMaximumHeight("+hei_ght+")"
                p10="self.label_epn_"+str(i)+".lineWrapMode()"
                p11="self.label_epn_"+str(i)+".setReadOnly(True)"
               
                exec(p1)
                exec(p7)
                exec(p2)
                exec(p5)
                exec(p6)
                exec(p9)
                exec(p10)
                exec(p11)
                
                i=i+1
                if (i%50) == 0:
                    logger.info('created {0} label-text-frame'.format(i))
                k = k+1
                if k == iconv_r:
                    j = j+2*iconv_r
                    k = 0
            total_till_epn = length1
    
        logger.info("browse-cnt="+str(browse_cnt))
        logger.info("length="+str(length))
        while(browse_cnt<length and browse_cnt < len(self.epn_arr_list)):
            if site == "Local" or site=="None" or site == "Music" or site == "Video":
                if '	' in self.epn_arr_list[browse_cnt]:
                    nameEpn = (self.epn_arr_list[browse_cnt]).split('	')[0]
                    
                    path = ((self.epn_arr_list[browse_cnt]).split('	')[1])
                else:
                    nameEpn = os.path.basename(self.epn_arr_list[browse_cnt])
                    path = (self.epn_arr_list[browse_cnt])
                if self.list1.currentItem():
                    name_t = self.list1.currentItem().text()
                else:
                    name_t = ''
                if self.list3.currentItem():
                    if self.list3.currentItem().text() == 'Playlist':
                        picnD = os.path.join(home, 'thumbnails', 'PlayLists', name_t)
                    else:
                        picnD = os.path.join(home, 'thumbnails', site, name_t)
                else:
                    picnD = os.path.join(home, 'thumbnails', site, name_t)
                if not os.path.exists(picnD):
                    os.makedirs(picnD)
                picn = os.path.join(picnD, nameEpn)+'.jpg'
                picn = picn.replace('#', '', 1)
                if picn.startswith(self.check_symbol):
                    picn = picn[1:]
                path = path.replace('"', '')
                if not os.path.exists(picn) and not path.startswith('http'):
                    self.generate_thumbnail_method(picn, 10, path)
                elif (not os.path.exists(picn) and path.startswith('http') 
                            and 'youtube.com' in path):
                        if '/watch?' in path:
                            a = path.split('?')[-1]
                            b = a.split('&')
                            if b:
                                for i in b:
                                    j = i.split('=')
                                    k = (j[0], j[1])
                                    m.append(k)
                            else:
                                j = a.split('=')
                                k = (j[0], j[1])
                                m.append(k)
                            d = dict(m)
                        try:
                            img_url="https://i.ytimg.com/vi/"+d['v']+"/hqdefault.jpg"
                            ccurl(img_url+'#'+'-o'+'#'+picn)
                        except:
                            pass
                if site == "Music":
                    if os.path.exists(picn):
                        if os.stat(picn).st_size == 0:
                            art_n =(self.epn_arr_list[browse_cnt]).split('	')[2]
                            pic = os.path.join(home, 'Music', 'Artist', art_n, 'thumbnail.jpg')
                            if os.path.exists(pic):
                                picn = pic
            elif site == "PlayLists":
                item = self.list2.item(browse_cnt)
                if item:
                    nameEpn = (self.epn_arr_list[browse_cnt]).split('	')[0]
                    nameEpn = str(nameEpn)
                    path = ((self.epn_arr_list[browse_cnt]).split('	')[1])
                    playlist_dir = os.path.join(home, 'thumbnails', 'PlayLists')
                    if not os.path.exists(playlist_dir):
                        os.makedirs(playlist_dir)
                    pl_n = self.list1.currentItem().text()
                    playlist_name = os.path.join(playlist_dir, pl_n)
                    if not os.path.exists(playlist_name):
                        os.makedirs(playlist_name)
                    picnD = os.path.join(playlist_name, nameEpn)
                    picn = picnD+'.jpg'
                    picn = picn.replace('#', '', 1)
                    if picn.startswith(self.check_symbol):
                        picn = picn[1:]
                    path1 = path.replace('"', '')
                    if not os.path.exists(picn) and not path1.startswith('http'):
                        self.generate_thumbnail_method(picn, 10, path1)
                    elif (not os.path.exists(picn) and path1.startswith('http') 
                            and 'youtube.com' in path1):
                        if '/watch?' in path1:
                            a = path1.split('?')[-1]
                            b = a.split('&')
                            if b:
                                for i in b:
                                    j = i.split('=')
                                    k = (j[0], j[1])
                                    m.append(k)
                            else:
                                j = a.split('=')
                                k = (j[0], j[1])
                                m.append(k)
                            d = dict(m)
                        try:
                            img_url="https://i.ytimg.com/vi/"+d['v']+"/hqdefault.jpg"
                            ccurl(img_url+'#'+'-o'+'#'+picn)
                            self.image_fit_option(picn, picn, fit_size=6, widget=self.label)
                        except:
                            pass
            else:
                if finalUrlFound == True:
                    if '	' in self.epn_arr_list[browse_cnt]:
                        nameEpn = (self.epn_arr_list[browse_cnt]).split('	')[0]
                    
                    else:
                        nameEpn = os.path.basename(self.epn_arr_list[browse_cnt])
                    nameEpn = nameEpn
                else:
                    if '	' in self.epn_arr_list[browse_cnt]:
                        nameEpn = (self.epn_arr_list[browse_cnt]).split('	')[0]
                    else:
                        nameEpn = (self.epn_arr_list[browse_cnt])
                    nameEpn = nameEpn
                picnD = os.path.join(home, 'thumbnails', name)
                if not os.path.exists(picnD):
                    os.makedirs(picnD)
                picn = picnD+'/'+nameEpn+'.jpg'
                picn = picn.replace('#', '', 1)
                if picn.startswith(self.check_symbol):
                    picn = picn[1:]
                
            if nameEpn.startswith('#'):
                nameEpn = nameEpn.replace('#', self.check_symbol, 1)
            if os.path.exists(picn):
                picn = self.image_fit_option(picn, '', fit_size=6, widget_size=(int(width), int(height)))
                img = QtGui.QPixmap(picn, "1")
                q1="self.label_epn_"+str(browse_cnt)+".setPixmap(img)"
                exec (q1)
                
            sumry = "<html><h1>"+nameEpn+"</h1></html>"
            
            q3="self.label_epn_"+str(length+browse_cnt)+".setText((nameEpn))"
            exec (q3)
            q3="self.label_epn_"+str(length+browse_cnt)+".setAlignment(QtCore.Qt.AlignCenter)"
            exec(q3)
            
            if (browse_cnt%10) == 0 or browse_cnt == 0:
                QtWidgets.QApplication.processEvents()
            browse_cnt = browse_cnt+1
        QtWidgets.QApplication.processEvents()
        QtWidgets.QApplication.processEvents()

    def searchAnime(self):
        global fullscrT, idwMain, idw
        self.filter_btn_options()
        
    def setCategoryMovie(self):
        global category, site
        category = "Movies" 
        
    def setCategoryAnime(self):
        global category, site
        category = "Animes" 
    
    def get_external_url_status(self, finalUrl):
        external_url = False
        if finalUrl.startswith('"http') or finalUrl.startswith('http'):
            try:
                ip_addr = finalUrl.split('/')[2]
                if ':' in ip_addr:
                    ip_addr = ip_addr.split(':')[0]
            except Exception as e:
                print(e)
                ip_addr = 'none'
            private_ip = False
            try:
                ip_obj = ipaddress.ip_address(ip_addr)
                print(ip_obj)
                if ip_obj.is_private:
                    private_ip = True
            except Exception as e:
                print(e)
            if not private_ip:
                external_url = True
        return external_url
    
    def get_redirected_url_if_any(self, finalUrl, external_url):
        if not external_url:
            if finalUrl.startswith('"http') or finalUrl.startswith('http'):
                finalUrl = finalUrl.replace('"', '')
                content = ccurl(finalUrl+'#'+'-H')
                if "Location:" in content:
                    m = re.findall('Location: [^\n]*', content)
                    finalUrl = re.sub('Location: |\r', '', m[-1])
        return finalUrl
            
    def epnClicked(self, dock_check=None):
        global queueNo, mpvAlive, curR, idw, Player, ui
        curR = self.list2.currentRow()
        queueNo = queueNo + 1
        mpvAlive = 0
        if self.float_window.isHidden():
            if self.mpvplayer_val.processId() > 0:
                if idw != str(int(self.tab_5.winId())):
                    self.mpvplayer_val.kill()
                    self.mpvplayer_started = False
                    idw = str(int(self.tab_5.winId()))
                if self.mpvplayer_started:
                    self.mpvNextEpnList(play_row=curR, mode='play_now')
                else:
                    self.epnfound()
            else:
                self.epnfound()
            if dock_check:
                if self.auto_hide_dock:
                    self.dockWidget_3.hide()
        else:
            if not idw or idw == str(int(self.tab_5.winId())):
                self.epnfound()
            elif idw == str(int(self.label.winId())):
                self.epnfound()
            else:
                final = self.epn_return(curR)
                self.play_file_now(final)
                self.paste_background(curR)
                try:
                    server._emitMeta("Play", site, self.epn_arr_list)
                except Exception as e:
                    print(e)
    
    def mpvNextEpnList(self, play_row=None, mode=None):
        global epn, curR, Player, site, current_playing_file_path
        print(play_row, '--play_row--', mode)
        if self.mpvplayer_val.processId() > 0:
            print("-----------inside-------")
            if play_row != None and mode == 'play_now':
                curR = play_row
            else:
                if curR == self.list2.count() - 1:
                    curR = 0
                    if (site == "Music" and not self.playerPlaylist_setLoop_var) or (self.list2.count()==1):
                        r1 = self.list1.currentRow()
                        it1 = self.list1.item(r1)
                        if it1:
                            if r1 < self.list1.count():
                                r2 = r1+1
                            else:
                                r2 = 0
                            self.list1.setCurrentRow(r2)
                            self.listfound()
                else:
                    curR = curR + 1

            self.list2.setCurrentRow(curR)
            if site != "PlayLists" and not self.queue_url_list:
                try:
                    if '	' in self.epn_arr_list[curR]:
                        epn = self.epn_arr_list[curR].split('	')[1]
                    else:
                        epn = self.list2.currentItem().text()
                    epn = epn.replace('#', '', 1)
                    if epn.startswith(self.check_symbol):
                        epn = epn[1:]
                except:
                    pass
            
            if (site == "Local" or site == "Music" or site == "Video" 
                    or site == "None" or site == "PlayLists" or site == 'MyServer'):
                logger.info('--mpv--nextepn--{0}'.format(current_playing_file_path))
                self.external_url = self.get_external_url_status(current_playing_file_path)
                if self.external_url:
                    if '	' in self.epn_arr_list[curR]:
                        lnk_epn = self.epn_arr_list[curR].split('	')[1]
                    else:
                        lnk_epn = self.list2.currentItem().text()
                    if lnk_epn.startswith('abs_path=') or lnk_epn.startswith('relative_path='):
                        print(self.mpvplayer_val.processId())
                    else:
                        self.mpvplayer_val.kill()
                        self.mpvplayer_started = False
                if len(self.queue_url_list)>0:
                    self.getQueueInList()
                else:
                    self.localGetInList()
            else:
                if Player == "mpv":
                    self.mpvplayer_val.kill()
                    self.mpvplayer_started = False
                    self.getNextInList()
                else:
                    print(self.mpvplayer_val.state())
                    self.mpvplayer_val.kill()
                    self.mpvplayer_started = False
                    print(self.mpvplayer_val.processId(), '--mpvnext---')
                    self.getNextInList()
    
    def mpvPrevEpnList(self):
        global epn, curR, Player, site
        global current_playing_file_path
        
        if self.mpvplayer_val.processId() > 0:
            print("inside")
            if curR == 0:
                curR = self.list2.count() - 1
                if ((site == "Music" and not self.playerPlaylist_setLoop_var) 
                        or (self.list2.count() == 1)):
                    r1 = self.list1.currentRow()
                    it1 = self.list1.item(r1)
                    if it1:
                        if r1 > 0:
                            r2 = r1-1
                        else:
                            r2 = self.list2.count()-1
                        curR = self.list2.count() - 1
            else:
                curR = curR - 1
            self.mpvNextEpnList(play_row=curR, mode='play_now')
    
    def HideEveryThing(self, hide_var=None):
        global fullscrT, idwMain, idw, view_layout
        fullscrT = 1 - fullscrT
        if hide_var:
            if hide_var == 'hide':
                self.tab_2.hide()
                self.tab_6.hide()
                self.list1.hide()
                self.list2.hide()
                self.tab_5.hide()
                self.label.hide()
                self.text.hide()
                self.frame.hide()
                self.dockWidget_3.hide()
                self.tab_6.hide()
                self.tab_2.hide()
                self.goto_epn.hide()
                self.list1.setFocus()
                self.frame1.hide()
            elif hide_var == 'unhide':
                self.list1.show()
                self.list2.show()
                self.label.show()
                self.text.show()
                self.frame.show()
                self.dockWidget_3.show()
                self.goto_epn.show()
                self.list1.setFocus()
                self.frame1.show()
        else:
            if fullscrT == 1:
                
                self.tab_2.hide()
                self.tab_6.hide()
                self.list1.hide()
                self.list2.hide()
                self.tab_5.hide()
                self.label.hide()
                self.text.hide()
                self.frame.hide()
                self.dockWidget_3.hide()
                self.tab_6.hide()
                self.tab_2.hide()
                self.goto_epn.hide()
                self.list1.setFocus()
                self.frame1.hide()
            else:
                self.list1.show()
                self.list2.show()
                self.label.show()
                self.text.show()
                self.frame.show()
                self.dockWidget_3.show()
                self.goto_epn.show()
                self.list1.setFocus()
                self.frame1.show()
        
    def thumbnailHide(self, context):
        global view_layout, total_till, browse_cnt, iconv_r
        global memory_num_arr, idw
        global thumbnail_indicator, iconv_r_indicator, total_till_epn
        idw = str(int(self.tab_5.winId()))
        thumbnail_indicator[:]=[]
        memory_num_arr[:]=[]
        i = 0
        if context == "ExtendedQLabel":
            pass
        else:
            if total_till > 0:
                while(i<total_till):
                    t = "self.label_"+str(i)+".deleteLater()"
                    exec(t)
                    i = i+1
            if total_till_epn > 0:
                for i in range(total_till_epn):
                    t = "self.label_epn_"+str(i)+".deleteLater()"
                    exec(t)
            total_till = 0
            total_till_epn = 0
        if iconv_r_indicator:
            iconv_r = iconv_r_indicator[0]
        else:
            iconv_r = 5
        self.tab_6.setMaximumSize(10000, 10000)
        browse_cnt = 0
        self.tab_6.hide()
        self.list1.show()
        self.list2.show()
        self.label.show()
        self.frame1.show()
        self.text.show()
        view_layout = "List"
        if self.mpvplayer_val.processId() > 0:
            self.text.hide()
            self.label.hide()
            self.list1.hide()
            self.frame.hide()
            self.tab_5.show()
                
    def webClose(self):
        global view_layout, desktop_session
        
        if not self.VerticalLayoutLabel.itemAt(2):
            self.VerticalLayoutLabel.addStretch(2)
            print('--stretch -- added--to --label and text widget--')
        
        self.tmp_web_srch = ''
        if self.web:
            self.web.setHtml('<html>Reviews:</html>')
        if desktop_session == 'ubuntu':
            print('--page--cleared--')
        else:
            try:
                QtCore.QTimer.singleShot(2000, partial(self.delete_web_instance, self.web))
            except Exception as e:
                print(e)
            print('--web closed--')
            
        self.tab_2.hide()
        self.list1.show()
        self.list2.show()
        self.label.show()
        self.text.show()
        self.frame1.show()
        
    def delete_web_instance(self, web):
        if web:
            web.close()
            web.deleteLater()
            self.web = None
        
    def webHide(self):
        if self.mpvplayer_val.processId() > 0:
            if self.tab_2.isHidden():
                self.tab_2.show()
                self.list1.hide()
                self.list2.hide()
                self.label.hide()
                self.text.hide()
            else:
                self.tab_2.hide()
                if site == 'Music':
                    self.list2.show()
                    self.label.show()
                    self.text.show()
        else:
            self.showHideBrowser()
            
    def togglePlaylist(self):
        if self.list2.isHidden():
            self.list2.show()
            #self.goto_epn.show()
        else:
            self.list2.hide()
            self.goto_epn.hide()
            
    def dockShowHide(self):
        global fullscr
        if self.dockWidget_3.isHidden():
            self.dockWidget_3.show()
            self.btn1.setFocus()
        else:
            self.dockWidget_3.hide()
            if fullscr == 1:
                self.tab_5.setFocus()
            else:
                self.list1.setFocus()
        
    def showHideBrowser(self):
        global fullscrT, idwMain, idw, view_layout
        
        if self.tab_2.isHidden():
            self.HideEveryThing(hide_var='hide')
            self.tab_2.show()
            self.frame1.show()
        else:
            self.tab_6.hide()
            self.tab_2.hide()
            self.list1.show()
            self.list2.show()
            self.label.show()
            self.text.show()
            self.frame1.show()
        
    def IconView(self):
        global fullscrT, idwMain, idw, total_till, label_arr, browse_cnt, tmp_name
        global view_layout, thumbnail_indicator, total_till_epn
        
        if self.list1.count() == 0:
            return 0
        
        thumbnail_indicator[:]=[]
        self.scrollArea1.hide()
        self.scrollArea.show()
        label_arr[:]=[]
        browse_cnt=0
        tmp_name[:]=[]
        num = self.list2.currentRow()
        i = 0
        if total_till > 0:
            while(i<total_till):
                t = "self.label_"+str(i)+".deleteLater()"
                exec (t)
                i = i+1
            total_till = 0
        
        if total_till_epn > 0:
            while(i<total_till_epn):
                t = "self.label_epn_"+str(i)+".deleteLater()"
                exec (t)
                i = i+1
            total_till_epn = 0
            
        if self.tab_6.isHidden():
            self.list1.hide()
            self.list2.hide()
            self.tab_5.hide()
            self.label.hide()
            self.text.hide()
            self.frame.hide()
            self.frame1.hide()
            self.goto_epn.hide()
            self.dockWidget_3.hide()
            self.tab_6.show()
            self.next_page('deleted')
            self.tab_2.hide()
        else:
            self.tab_6.hide()
            self.list1.show()
            self.list2.show()
            self.label.show()
            self.list1.setFocus()
            self.text.show()
            self.frame1.show()
            
    def IconViewEpn(self):
        global fullscrT, idwMain, idw, total_till, label_arr, browse_cnt, tmp_name
        global view_layout, iconv_r, curR, viewMode, thumbnail_indicator
        global site, total_till_epn
        
        if self.list2.count() == 0:
            return 0
        
        thumbnail_indicator[:]=[]
        self.scrollArea.hide()
        label_arr[:]=[]
        tmp_name[:]=[]
        num = self.list2.currentRow()
        if num < 0:
            num = 0
        i = 0
        print(viewMode, site, '--viewmode--')
        if (self.tab_6.isHidden() or (viewMode == "Thumbnail" 
                and site == "PlayLists")):
            self.list1.hide()
            self.list2.hide()
            self.tab_5.hide()
            self.label.hide()
            self.text.hide()
            self.frame.hide()
            #self.frame1.hide()
            self.goto_epn.hide()
            self.dockWidget_3.hide()
            if self.mpvplayer_val.processId()>0:
                self.tab_5.show()
                self.frame1.show()
                iconv_r = 1
                self.gridLayout.addWidget(self.tab_6, 0, 2, 1, 1)	
            else:	
                self.gridLayout.addWidget(self.tab_6, 0, 1, 1, 1)		
            self.tab_6.show()
            self.thumbnailEpn()
            self.tab_2.hide()
            if self.mpvplayer_val.processId()>0:
                self.scrollArea1.verticalScrollBar().setValue((curR+1)*200+(curR+1)*10)
            else:
                self.scrollArea1.verticalScrollBar().setValue(((num+1)/4)*200+((num+1)/4)*10)
        else:
            self.tab_6.hide()
            self.list1.show()
            self.list2.show()
            self.label.show()
            self.list1.setFocus()
            self.text.show()
            self.frame1.show()
                
    def textShowHide(self):
        global fullscrT, idwMain, idw
        if fullscrT == 1:
            self.text.show()
        else:
            self.text.hide()
            
    def fullscreenToggle(self):
        global fullscrT, idwMain, idw
        fullscrT = 1 - fullscrT
        if not MainWindow.isFullScreen():
            self.dockWidget_4.close()
            self.dockWidget_3.hide()
            MainWindow.showFullScreen()
        else:
            self.dockWidget_3.show()
            MainWindow.showNormal()
            MainWindow.showMaximized()
    
    
    def shuffleList(self):
        global list1_items, pre_opt, opt, hdr, base_url, site, embed, base_url
        global finalUrlFound
        global pict_arr, name_arr, summary_arr, total_till, browse_cnt, tmp_name
        global bookmark
        pict_arr[:]=[]
        name_arr[:]=[]
        summary_arr[:]=[]
        browse_cnt=0
        tmp_name[:]=[]
        embed = 0
        n = []
        m = []
            
        if site == "Music" or site=="Video":
            if self.original_path_name:
                tmp = self.original_path_name[0]
                if '/' in tmp:
                    p = random.sample(self.original_path_name, len(self.original_path_name))
                    self.original_path_name[:]=[]
                    self.original_path_name = p
                    
                    for i in p:
                        if site=="Video":
                            m.append(i.split('	')[0])
                        else:
                            #m.append(i.split('/')[-1])
                            m.append(os.path.basename(i))
                else:
                    for i in range(self.list1.count()):
                        n.append(str(self.list1.item(i).text()))
                    m = random.sample(n, len(n))
        else:
            m = random.sample(self.original_path_name, len(self.original_path_name))
            self.original_path_name[:]=[]
            self.original_path_name = m
            
        if m and not bookmark: 
            self.label.clear()
            self.line.clear()
            self.list1.clear()
            self.list2.clear()
            self.text.clear()
            for i in m:
                if site == "Local":
                    k = i.split('@')[-1]
                    i = k
                elif site.lower() == 'video' or site.lower() == 'music':
                    pass
                else:
                    if '	' in i:
                        i = i.split('	')[0]
                self.list1.addItem(i)
        opt = "Random"
        
    def sortList(self):
        global list1_items, pre_opt, opt, hdr, base_url, site, embed
        global finalUrlFound
        global pict_arr, name_arr, summary_arr, total_till
        global browse_cnt, tmp_name, bookmark
        
        pict_arr[:]=[]
        name_arr[:]=[]
        summary_arr[:]=[]
        browse_cnt=0
        tmp_name[:]=[]
        tmp_arr = []
        embed = 0
        n = []
        m =[]
        if site == "Local":
            m = sorted(self.original_path_name, key = lambda x: x.split('@')[-1].lower())
            self.original_path_name[:]=[]
            self.original_path_name = m
        elif site == "Music" or site == "Video":
            if self.original_path_name:
                tmp = self.original_path_name[0]
                if '/' in tmp:
                    if site == "Video":
                        p = sorted(
                            self.original_path_name, 
                            key = lambda x: x.split('	')[0].lower()
                            )
                    else:
                        p = sorted(
                            self.original_path_name, 
                            key = lambda x: os.path.basename(x).lower()
                            )
                    self.original_path_name[:]=[]
                    self.original_path_name = p
                    for i in p:
                        if site == "Video":
                            m.append(i.split('	')[0])
                        else:
                            m.append(os.path.basename(i))
                else:
                    for i in range(self.list1.count()):
                        n.append(str(self.list1.item(i).text()))
                    m = list(set(n))
                    m.sort()
        else:
            self.original_path_name.sort()
            m = self.original_path_name
        
        if m and not bookmark:
            self.label.clear()
            self.line.clear()
            self.list1.clear()
            self.list2.clear()
            self.text.clear()
            for i in m:
                if site == "Local":
                    k = i.split('@')[-1]
                    i = k
                elif site.lower() == 'music' or site.lower() == 'video':
                    pass
                else:
                    if '	' in i:
                        i = i.split('	')[0]
                self.list1.addItem(i)
        #opt = "List"
        
    def deleteArtwork(self):
            global name
            thumb = os.path.join(TMPDIR, name+'.jpg')
            self.label.clear()
            if os.path.isfile(thumb):
                    os.remove(thumb)
                    
    def get_current_directory(self):
        global name, site, opt, pre_opt, home, siteName
        print(site)
        print(opt)
        print(pre_opt)
        logger.info(name)
        if '/' in name:
            name = name.replace('/', '-')
        path = ""
        if site == "Local":
            r = self.list1.currentRow()
            name = self.original_path_name[r]
        
        if (opt == "History" and (site.lower()!= 'video' 
                and site.lower()!= 'music' and site.lower()!= 'local')):
            if site == "SubbedAnime" or site == "DubbedAnime":
                path= os.path.join(home, 'History', site, siteName, name)
            else:
                path = os.path.join(home, 'History', site, name)
        elif (site == "Local" or site == "Video"):
            path = os.path.join(home, 'Local', name)
        elif (site == "Music"):
            logger.info(name)
            try:
                r = self.list2.currentRow()
                nm = self.epn_arr_list[r].split('	')[2]
            except:
                nm = ""
            if nm:
                path = os.path.join(home, 'Music', 'Artist', nm)
            logger.info("current directory is {0} and name is {1}".format(path, nm))
        logger.info("current directory is {0} and name is {1}".format(path, name))
        return path
        
    def copyImg(self, new_name=None):
        global name, site, opt, pre_opt, home, siteName
        print(site)
        print(opt)
        print(pre_opt)
        if not new_name:
            new_name = name
        if '/' in new_name:
            new_name = new_name.replace('/', '-')
        picn = os.path.join(TMPDIR, new_name+'.jpg')
        if not new_name and site.lower() == 'music':
            try:
                nm = ''
                if new_name:
                    nm = new_name
                else:
                    if str(self.list3.currentItem().text()) == "Artist":
                        nm = self.list1.currentItem().text()
                    else:
                        r = self.list2.currentRow()
                        nm = self.epn_arr_list[r].split('	')[2]
                        nm = nm.replace('"', '')
            except:
                nm = ''
            picn = os.path.join(TMPDIR, nm+'.jpg')
        logger.info('{0}--copyimg--'.format(picn))
        if site == "Local":
            r = self.list1.currentRow()
            new_name = self.original_path_name[r]
        if not os.path.isfile(picn):
            picn = os.path.join(home, 'default.jpg')
        if (os.path.isfile(picn) and opt == "History" 
                and (site.lower()!= 'video' and site.lower()!= 'music' 
                and site.lower()!= 'local')):
            thumbnail = os.path.join(TMPDIR, new_name+'-thumbnail.jpg')
            try:
                self.image_fit_option(picn, thumbnail, fit_size=450)
                if site == "SubbedAnime" or site == "DubbedAnime":
                    shutil.copy(picn, 
                                os.path.join(home, 'History', site, siteName, new_name, 
                                'poster.jpg'))
                    if os.path.exists(thumbnail):
                        self.image_fit_option(picn, thumbnail, fit_size=6, widget=self.label)
                        shutil.copy(thumbnail, 
                                    os.path.join(home, 'History', site, siteName, 
                                    new_name, 'thumbnail.jpg'))
                    self.videoImage(
                        picn, os.path.join(home, 'History', site, siteName, 
                        new_name, 'thumbnail.jpg'), os.path.join(home, 'History', 
                        site, siteName, new_name, 'fanart.jpg'), '')
                else:
                    shutil.copy(picn, 
                                os.path.join(home, 'History', site, new_name, 
                                'poster.jpg'))
                    if os.path.exists(thumbnail):
                        self.image_fit_option(picn, thumbnail, fit_size=6, widget=self.label)
                        shutil.copy(thumbnail, 
                                    os.path.join(home, 'History', site, new_name, 
                                    'thumbnail.jpg'))
                    self.videoImage(
                        picn, os.path.join(home, 'History', site, new_name, 
                        'thumbnail.jpg'), os.path.join(home, 'History', site, 
                        new_name, 'fanart.jpg'), '')
            except Exception as e:
                print(e, '--line 10933--')
        elif os.path.isfile(picn) and (site == "Local" or site == "Video"):
            thumbnail = os.path.join(TMPDIR, new_name+'-thumbnail.jpg')
            try:
                self.image_fit_option(picn, thumbnail, fit_size=450)
                shutil.copy(picn, os.path.join(home, 'Local', new_name, 'poster.jpg'))
                if os.path.exists(thumbnail):
                    self.image_fit_option(picn, thumbnail, fit_size=6, widget=self.label)
                    shutil.copy(thumbnail, 
                                os.path.join(home, 'Local', new_name, 'thumbnail.jpg'))
                self.videoImage(
                    picn, os.path.join(home, 'Local', new_name, 'thumbnail.jpg'), 
                    os.path.join(home, 'Local', new_name, 'fanart.jpg'), '')
            except Exception as e:
                print(e, '--line 10948--')
        elif os.path.isfile(picn) and (site == "Music"):
            try:
                nm = ''
                if new_name:
                    nm = new_name
                else:
                    if str(self.list3.currentItem().text()) == "Artist":
                        nm = self.list1.currentItem().text()
                    else:
                        r = self.list2.currentRow()
                        nm = self.epn_arr_list[r].split('	')[2]
                        nm = nm.replace('"', '')
            except Exception as e:
                    print(e)
                    nm = ""
            logger.info('nm={0}'.format(nm))
            if nm and os.path.exists(os.path.join(home, 'Music', 'Artist', nm)):
                picn = os.path.join(TMPDIR, nm+'.jpg')
                thumbnail = os.path.join(TMPDIR, nm+'-thumbnail.jpg')
                logger.info('picn={0}-thumbnail={1}'.format(picn, thumbnail))
                try:
                    if os.path.exists(picn):
                        self.image_fit_option(picn, thumbnail, fit_size=450)
                        shutil.copy(picn, 
                                    os.path.join(home, 'Music', 'Artist', nm, 
                                    'poster.jpg'))
                        if os.path.exists(thumbnail):
                            self.image_fit_option(picn, thumbnail, fit_size=6, widget=self.label)
                            shutil.copy(thumbnail, 
                                        os.path.join(home, 'Music', 'Artist', nm, 
                                        'thumbnail.jpg'))
                        self.videoImage(
                            picn, os.path.join(home, 'Music', 'Artist', nm, 
                            'thumbnail.jpg'), os.path.join(home, 'Music', 
                            'Artist', nm, 'fanart.jpg'), '')
                except Exception as e:
                    print(e, ': line 10783')
    
    def copyFanart(self, new_name=None):
        global name, site, opt, pre_opt, home, siteName
        global screen_height, screen_width
        print(site)
        print(opt)
        print(pre_opt)
        if not new_name:
            new_name = name
        if '/' in new_name:
            new_name = new_name.replace('/', '-')
        picn = os.path.join(TMPDIR, new_name+'-fanart.jpg')
        if (not os.path.exists(picn) or ((os.path.exists(picn) 
                and not os.stat(picn).st_size))):
            picn = os.path.join(TMPDIR, new_name+'.jpg')
        if site == "Local":
            r = self.list1.currentRow()
            new_name = self.original_path_name[r]
        if self.image_fit_option_val in range(1, 11):
            if self.image_fit_option_val != 6:
                img_opt = self.image_fit_option_val
            else:
                img_opt = 1
        else:
            img_opt = 1
        if (os.path.isfile(picn) and opt == "History" 
                and (site.lower()!= 'video' and site.lower()!= 'music' 
                and site.lower()!= 'local')):
            try:
                if site == "SubbedAnime" or site == "DubbedAnime":
                    shutil.copy(picn, 
                                os.path.join(home, 'History', site, siteName, new_name, 
                                'original-fanart.jpg'))
                    self.image_fit_option(picn, picn, fit_size=img_opt)
                    shutil.copy(picn, 
                                os.path.join(home, 'History', site, siteName, new_name, 
                                'fanart.jpg'))
                    self.videoImage(
                        picn, os.path.join(home, 'History', site, siteName, 
                        new_name, 'thumbnail.jpg'), os.path.join(home, 'History', 
                        site, siteName, new_name, 'fanart.jpg'), '')
                else:
                    shutil.copy(picn, 
                                os.path.join(home, 'History', site, new_name, 
                                'original-fanart.jpg'))
                    self.image_fit_option(picn, picn, fit_size=img_opt)
                    shutil.copy(picn, 
                                os.path.join(home, 'History', site, new_name, 
                                'fanart.jpg'))
                    self.videoImage(
                        picn, os.path.join(home, 'History', site, new_name, 
                        'thumbnail.jpg'), os.path.join(home, 'History', site, new_name, 
                        'fanart.jpg'), '')
            except Exception as e:
                print(e, '--line--11010--')
        elif os.path.isfile(picn) and (site == "Local" or site == "Video"):
            try:
                shutil.copy(
                    picn, os.path.join(home, 'Local', new_name, 
                    'original-fanart.jpg'))
                self.image_fit_option(picn, picn, fit_size=img_opt)
                shutil.copy(
                    picn, os.path.join(home, 'Local', new_name, 'fanart.jpg'))
                self.videoImage(
                    picn, os.path.join(home, 'Local', new_name, 'thumbnail.jpg'), 
                    os.path.join(home, 'Local', new_name, 'fanart.jpg'), '')
            except Exception as e:
                print(e, '--line--11023--')
            #ui.listfound()
        elif (site == "Music"):
            try:
                if new_name:
                    nm = new_name
                else:
                    if str(self.list3.currentItem().text()) == "Artist":
                        nm = self.list1.currentItem().text()
                    else:
                        r = self.list2.currentRow()
                        nm = self.epn_arr_list[r].split('	')[2]
                        nm = nm.replace('"', '')
            except Exception as e:
                    print(e)
                    nm = ""
            logger.info('nm={0}'.format(nm))
            if nm and os.path.exists(os.path.join(home, 'Music', 'Artist', nm)):
                picn = os.path.join(TMPDIR, nm+'.jpg')
                if os.path.exists(picn):
                    shutil.copy(
                        picn, os.path.join(home, 'Music', 'Artist', nm, 
                        'original-fanart.jpg'))
                    self.image_fit_option(picn, picn, fit_size=img_opt)
                    shutil.copy(
                        picn, os.path.join(home, 'Music', 'Artist', nm, 'fanart.jpg'))
                    #print(picn, os.path.join(home, 'Music', 'Artist', nm, 'fanart.jpg'))
                    self.videoImage(
                        picn, os.path.join(home, 'Music', 'Artist', nm, 
                        'thumbnail.jpg'), os.path.join(home, 'Music', 'Artist', nm, 
                        'fanart.jpg'), '')
                
    def copySummary(self, copy_sum=None, new_name=None):
        global name, site, opt, pre_opt, home, siteName
        print(site)
        print(opt)
        print(pre_opt)
        sumry = ''
        if not new_name:
            new_name = name
        if '/' in new_name:
            new_name = new_name.replace('/', '-')
        if site == "Local":
            r = self.list1.currentRow()
            new_name = str(self.list1.currentItem().text())
        elif site == "Music":
            try:
                nm = ''
                if new_name:
                    nm = new_name
                else:
                    if str(self.list3.currentItem().text()) == "Artist":
                        nm = self.list1.currentItem().text()
                    else:
                        r = self.list2.currentRow()
                        nm = self.epn_arr_list[r].split('	')[2]
                        nm = nm.replace('"', '')
            except Exception as e:
                print(e)
                nm = ""
            sumry = os.path.join(TMPDIR, nm+'-bio.txt')
        else:
            sumry = os.path.join(TMPDIR, new_name+'-summary.txt')
        if site == "Local":
            r = self.list1.currentRow()
            new_name = self.original_path_name[r]
            logger.info('sumry={0}- new_name={1} -- copysummary--'.format(sumry, new_name))
        if copy_sum:
            write_files(sumry, copy_sum, False)
        if (os.path.isfile(sumry) and opt == "History" 
                and (site != "Local" and site != "Video" and site != 'Music')):
            if site == "SubbedAnime" or site == "DubbedAnime":
                shutil.copy(sumry, os.path.join(home, 'History', site, siteName, new_name, 'summary.txt'))
            else:
                shutil.copy(sumry, os.path.join(home, 'History', site, new_name, 'summary.txt'))
        elif os.path.isfile(sumry) and (site == "Local" or site == "Video"):
                shutil.copy(sumry, os.path.join(home, 'Local', new_name, 'summary.txt'))
        elif (site == "Music"):
            try:
                nm = ''
                if new_name:
                    nm = new_name
                else:
                    if str(self.list3.currentItem().text()) == "Artist":
                        nm = self.list1.currentItem().text()
                    else:
                        r = self.list2.currentRow()
                        nm = self.epn_arr_list[r].split('	')[2]
                        nm = nm.replace('"', '')
            except Exception as e:
                print(e)
                nm = ""
            if nm and os.path.exists(os.path.join(home, 'Music', 'Artist', nm)):
                sumry = os.path.join(TMPDIR, nm+'-bio.txt')
                if os.path.exists(sumry):
                    shutil.copy(sumry, os.path.join(home, 'Music', 'Artist', nm, 'bio.txt'))
        if os.path.exists(sumry):
            txt = open_files(sumry, False)
            logger.info('{0}--copy-summary--'.format(txt))
            self.text.setText(txt)
    
    def showImage(self):
        global name
        thumb = os.path.join(TMPDIR, name+'.jpg')
        logger.info(thumb)
        if os.path.exists(thumb):
            Image.open(thumb).show()
    
    def getTvdbEpnInfo(self, url):
        global site, finalUrlFound, hdr, home
        content = ccurl(url)
        soup = BeautifulSoup(content, 'lxml')
        m=[]
        link1 = soup.find('div', {'class':'section'})
        if not link1:
            return 0
        link = link1.findAll('td')
        n = []

        for i in range(4, len(link), 4):
            j = link[i].find('a').text
            k = link[i+1].find('a').text
            l = link[i+2].text
            p = link[i+3].find('img')
            if p:
                img_lnk = link[i].find('a')['href']
                lnk = img_lnk.split('&')
                series_id = lnk[1].split('=')[-1]
                poster_id = lnk[3].split('=')[-1]
                q = "http://thetvdb.com/banners/episodes/"+series_id+'/'+poster_id+'.jpg'
            else:
                q = "http:No Image"
            j = j.replace(' ', '')
            k = k.replace('/', '-')
            k = k.replace(':', '-')
            t = j+' '+k+':'+q
            if 'special' in j.lower():
                n.append(t)
            else:
                m.append(t)
        m = m+n
        for i in m:
            logger.info(i)
        
        for i in range(len(self.epn_arr_list)):
            if '	' in self.epn_arr_list[i]:
                j = self.epn_arr_list[i].split('	', 1)[1]
                if i < len(m):
                    k = m[i].split(':')[0]
                else:
                    k = self.epn_arr_list[i].split('	', 1)[0]
                self.epn_arr_list[i]=k+'	'+j
            else:
                j = self.epn_arr_list[i]
                if i < len(m):
                    k = m[i].split(':')[0]
                else:
                    k = self.epn_arr_list[i]
                if j.startswith('#'):
                    j = j[1:]
                    k = '#'+k
                self.epn_arr_list[i]=k+'	'+j
                
        if site=="Video":
            video_db = os.path.join(home, 'VideoDB', 'Video.db')
            conn = sqlite3.connect(video_db)
            cur = conn.cursor()
            for r in range(len(self.epn_arr_list)):
                txt = self.epn_arr_list[r].split('	')[1]
                ep_name = self.epn_arr_list[r].split('	')[0]
                qr = 'Update Video Set EP_NAME=? Where Path=?'
                cur.execute(qr, (ep_name, txt))
            conn.commit()
            conn.close()
            try:
                txt = self.original_path_name[self.list1.currentRow()].split('	')[1]
                if txt in ui.video_dict:
                    del self.video_dict[txt]
            except Exception as err:
                print(err, '--4240---')
        elif opt == "History" or site == "Local":
            if site == "SubbedAnime" or site == "DubbedAnime":
                if os.path.exists(os.path.join(home, 'History', site, siteName, name, 'Ep.txt')):
                    file_path = os.path.join(home, 'History', site, siteName, name, 'Ep.txt')
            elif site == "Local" and opt != "History":
                r = self.list1.currentRow()
                name1 = self.original_path_name[r]
                if os.path.exists(os.path.join(home, 'Local', site, name1, 'Ep.txt')):
                    file_path = os.path.join(home, 'Local', site, name1, 'Ep.txt')
            elif site == "Local" and opt == "History":
                r = self.list1.currentRow()
                name1 = self.original_path_name[r]
                if os.path.exists(os.path.join(home, 'History', site, name1, 'Ep.txt')):
                    file_path = os.path.join(home, 'History', site, name1, 'Ep.txt')
            else:
                if os.path.exists(os.path.join(home, 'History', site, name, 'Ep.txt')):
                    file_path = os.path.join(home, 'History', site, name, 'Ep.txt')
                    
            if os.path.exists(file_path):
                write_files(file_path, self.epn_arr_list, line_by_line=True)
        self.update_list2()
        
        if not self.downloadWget:
            self.downloadWget[:] = []
            self.downloadWget_cnt = 0
        else:
            running = False
            len_down = len(self.downloadWget)
            for i in range(len_down):
                if self.downloadWget[i].isRunning():
                    running = True
                    break
            if not running:
                self.downloadWget[:] = []
                self.downloadWget_cnt = 0
            else:
                print('--Thread Already Running--')
                return 0
        if (site != "Local" and site != "Video"):
            for r in range(len(self.epn_arr_list)):
                if finalUrlFound == True:
                    if '	' in self.epn_arr_list[r]:
                        newEpn = self.epn_arr_list[r].split('	')[0]
                    else:
                        newEpn = os.path.basename(self.epn_arr_list[r])
                else:
                    if '	' in self.epn_arr_list[r]:
                        newEpn = self.epn_arr_list[r].split('	')[0]
                    else:
                        newEpn = name+'-'+(self.epn_arr_list[r])
                newEpn = str(newEpn)
                newEpn = newEpn.replace('#', '', 1)
                if newEpn.startswith(self.check_symbol):
                    newEpn = newEpn[1:]
                dest = os.path.join(home, "thumbnails", name, newEpn+'.jpg')
                if r < len(m):
                    logger.info('{0}-{1}'.format(r, m[r]))
                    img_url= m[r].split(':')[2]
                    if img_url.startswith('//'):
                        img_url = "http:"+img_url
                        command = "wget --user-agent="+'"'+hdr+'" '+'"'+img_url+'"'+" -O "+'"'+dest+'"'
                        self.downloadWget.append(DownloadThread(self, img_url+'#'+'-o'+'#'+dest))
                        self.downloadWget[len(self.downloadWget)-1].finished.connect(lambda x=dest: self.download_thread_finished(dest))
                    
            if self.downloadWget:
                length = len(self.downloadWget)
                for i in range(5):
                    if i < length:
                        self.downloadWget[i].start()
                
    def download_thread_finished(self, dest):
        logger.info("Download tvdb image: {0} :completed".format(dest))
        self.image_fit_option(dest, dest, fit_size=6, widget=self.label)
        logger.info("Image: {0} : aspect ratio changed".format(dest))
        self.downloadWget_cnt = self.downloadWget_cnt+1
        if self.downloadWget_cnt == 5:
            self.downloadWget = self.downloadWget[5:]
            length = len(self.downloadWget)
            self.downloadWget_cnt = 0
            for i in range(5):
                if i < length:
                    self.downloadWget[i].start()
    
    def posterfound_new(
            self, name, site=None, url=None, copy_poster=None, copy_fanart=None, 
            copy_summary=None, direct_url=None, use_search=None, get_all=None):
        
        logger.info('{0}-{1}-{2}--posterfound--new--'.format(url, direct_url, name))
        
        self.posterfound_arr.append(FindPosterThread(
            self, logger, TMPDIR, name, url, direct_url,
            copy_fanart, copy_poster, copy_summary, use_search))
        if get_all:
            self.posterfound_arr[len(self.posterfound_arr)-1].finished.connect(
                lambda x=0: self.posterfound_thread_all_finished(name, url,
                    direct_url, copy_fanart, copy_poster, copy_summary, use_search))
        else:
            self.posterfound_arr[len(self.posterfound_arr)-1].finished.connect(
                lambda x=0: self.posterfound_thread_finished(name, copy_fanart, 
                copy_poster, copy_summary))
        
        self.posterfound_arr[len(self.posterfound_arr)-1].start()
            
            
    def posterfound_thread_finished(self, name, copy_fan, copy_poster, copy_summary):
        logger.info('{0}-{1}-{2}--{3}--posterfound_thread_finished--'.format(name, copy_fan, copy_poster, copy_summary))
        copy_sum = 'Not Available'
        if copy_summary:
            copy_sum = self.text.toPlainText().replace('Wait..Downloading Poster and Fanart..\n\n', '')
        if copy_poster:
            self.copyImg(new_name=name)
        if copy_fan:
            self.copyFanart(new_name=name)
        if copy_summary:
            self.text.setText(copy_sum)
    
    def posterfound_thread_all_finished(
            self, name, url, direct_url, copy_fanart, copy_poster,
            copy_summary, use_search):
        self.posterfind_batch += 1
        logger.info('{0}-{1}-{2}--{3}--posterfound_thread_finished--'.format(name, copy_fanart, copy_poster, copy_summary))
        copy_sum = 'Not Available'
        if copy_summary:
            copy_sum = self.text.toPlainText().replace('Wait..Downloading Poster and Fanart..\n\n', '')
        if copy_poster:
            self.copyImg(new_name=name)
        if copy_fanart:
            self.copyFanart(new_name=name)
        if copy_summary:
            self.text.setText(copy_sum)
        if (self.posterfind_batch == 1) or (self.posterfind_batch % 3 == 0):
            index = self.posterfind_batch
            for i in range(0, 3):
                if index == 1:
                    row = i+1
                    if row == 3:
                        break
                else:
                    row = index + i
                if row < len(self.original_path_name):
                    nm = self.get_title_name(row)
                    self.posterfound_new(
                        name=nm, site=site, url=False, copy_poster=True, copy_fanart=True, 
                        copy_summary=True, direct_url=False, use_search=use_search, get_all=True)
    
    def get_final_link(self, url, quality, ytdl_path, loger, nm, hdr):
        logger.info('{0}-{1}-{2}--{3}--get-final--link--'.format(url, quality, ytdl_path, nm))
        self.ytdl_arr.append(YTdlThread(self, logger, url, quality, ytdl_path, loger, nm, hdr))
        length = len(self.ytdl_arr) - 1
        self.ytdl_arr[len(self.ytdl_arr)-1].finished.connect(lambda x=0: self.got_final_link(length))
        self.ytdl_arr[len(self.ytdl_arr)-1].start()
        self.tab_5.show()
        self.frame1.show()
        self.tab_2.setMaximumWidth(self.width_allowed+50)
        #self.progressEpn.setFormat('Wait....')
        #QtWidgets.QApplication.processEvents()
    
    def got_final_link(self, length):
        if length == len(self.ytdl_arr) - 1:
            del self.ytdl_arr[length]
            logger.info('--finished--getting link--')
            logger.info('arr: {0}---'.format(self.ytdl_arr))
        elif length < len(self.ytdl_arr) - 1:
            self.ytdl_arr[length] = None
            
        if self.ytdl_arr:
            empty = True
            for i in self.ytdl_arr:
                if i is not None:
                    empty = False
            if empty:
                print('empty arr')
                self.ytdl_arr[:] = []
        else:
            logger.info('--13898--link-fetched-properly')
    
    def chkMirrorTwo(self):
        global site, mirrorNo
        mirrorNo = 2
        if site == "SubbedAnime" or site == "DubbedAnime":
            self.epnfound()
        mirrorNo = 1
            
    def chkMirrorThree(self):
        global site, mirrorNo
        mirrorNo = 3
        if site == "SubbedAnime" or site == "DubbedAnime":
            self.epnfound()
        mirrorNo = 1		
        
    def chkMirrorDefault(self):
        global site, mirrorNo
        mirrorNo = 1
        if site == "SubbedAnime" or site == "DubbedAnime":
            self.epnfound()
            
    def setPreOpt(self, option_val=None):
        global pre_opt, opt, hdr, base_url, site, insidePreopt, embed, home
        global hist_arr, name, bookmark, status, viewMode, total_till, browse_cnt
        global embed, siteName
        
        insidePreopt = 1
        hist_arr[:]=[]
        var = (self.btn1.currentText())
        if var == "Select":
            return 0
        if bookmark and os.path.exists(os.path.join(home, 'Bookmark', status+'.txt')):
            opt = "History"
            line_a = open_files(os.path.join(home, 'Bookmark', status+'.txt'), True)
            self.list1.clear()
            self.original_path_name[:] = []
            for i in line_a:
                i = i.replace('\n', '')
                if i:
                    j = i.split(':')
                    logger.info(j)
                    if j[0] == "Local":
                        t = j[5].split('@')[-1]
                    else:
                        t = j[5]
                    if '	' in t:
                        t = t.split('	')[0]
                    self.list1.addItem(t)
                    hist_arr.append(j[5])
                    self.original_path_name.append(j[5])
        elif site == "SubbedAnime" or site == "DubbedAnime":
            opt = "History"
            self.options('history')	
        else:
            if option_val:
                opt = option_val
            else:
                opt = "History"
            self.options(opt.lower())
                
    def mark_video_list(self, mark_val, row):
        global site
        if site.lower() == "video":
            item = self.list2.item(row)
            if item:
                i = self.list2.item(row).text()
                if mark_val == 'mark' and i.startswith(self.check_symbol):
                    pass
                elif mark_val == 'unmark' and not i.startswith(self.check_symbol):
                    pass
                elif mark_val == 'mark' and not i.startswith(self.check_symbol):
                    url1 = self.epn_arr_list[row].split('	')[1]
                    item.setText(self.check_symbol+i)
                    self.media_data.update_video_count('mark', url1, rownum=row)
                elif mark_val == 'unmark' and i.startswith(self.check_symbol):
                    url1 = self.epn_arr_list[row].split('	')[1]
                    i = i[1:]
                    item.setText(i)
                    self.media_data.update_video_count('unmark', url1, rownum=row)
                self.list2.setCurrentRow(row)
                
    def update_playlist_file(self, file_path):
        if os.path.exists(file_path):
            write_files(file_path, self.epn_arr_list, line_by_line=True)
            
    def mark_playlist(self, mark_val, row):
        global site, home
        music_pl = False
        if site == 'music':
            if self.list3.currentItem():
                if self.list3.currentItem().text().lower() == 'playlist':
                    music_pl = True
                    
        if site.lower() == "playlists" or music_pl:
            item = self.list2.item(row)
            file_path = os.path.join(home, 'Playlists', self.list1.currentItem().text())
            if item:
                i = str(self.list2.item(row).text())
                if mark_val == 'mark' and i.startswith(self.check_symbol):
                    pass
                elif mark_val == 'unmark' and not i.startswith(self.check_symbol):
                    pass
                elif mark_val == 'mark' and not i.startswith(self.check_symbol):
                    item.setText(self.check_symbol+i)
                    self.epn_arr_list[row] = '#'+self.epn_arr_list[row]
                    self.list2.setCurrentRow(row)
                    self.update_playlist_file(file_path)
                elif mark_val == 'unmark' and i.startswith(self.check_symbol):
                    i = i[1:]
                    item.setText(i)
                    self.epn_arr_list[row] = self.epn_arr_list[row].replace('#', '', 1)
                    self.list2.setCurrentRow(row)
                    self.update_playlist_file(file_path)
                    
    def get_local_file_ep_name(self):
        global site, name, siteName
        file_path = ''
        if site.lower() == "local":
            file_path = os.path.join(home, 'History', site, name, 'Ep.txt')
        elif site.lower() == 'subbedanime' or site.lower() == 'dubbedanime':
            file_path = os.path.join(home, 'History', site, siteName, name, 'Ep.txt')
        elif site.lower() == 'playlists' and self.list1.currentItem():
            file_path = os.path.join(home, 'Playlists', self.list1.currentItem().text())
        elif site.lower() == 'music' and self.list3.currentItem():
            if self.list1.currentItem():
                file_path = os.path.join(home, 'Playlists', self.list1.currentItem().text())
        elif site.lower() != 'video':
            file_path = os.path.join(home, 'History', site, name, 'Ep.txt')
        return file_path
        
    def mark_addons_history_list(self, mark_val, row):
        global opt, site, home, site, name, siteName, finalUrlFound
        global refererNeeded, path_Local_Dir
        
        if (opt == "History" and (site.lower() !="video" 
                and site.lower()!= 'music' and site.lower()!= 'playlists' 
                and site.lower()!= 'none')):
            file_change = False
            item = self.list2.item(row)
            if item:
                if '	' in self.epn_arr_list[row]:
                    if self.epn_arr_list[row].startswith('#') and mark_val == 'unmark':
                        n_epn = self.epn_arr_list[row].replace('#', '', 1)
                    elif not self.epn_arr_list[row].startswith('#') and mark_val == 'mark':
                        n_epn = '#'+self.epn_arr_list[row]
                    else:
                        return 0
                else:
                    epn = self.epn_arr_list[row]
                    if site != "Local":
                        if epn.startswith('#') and mark_val == 'unmark':
                            n_epn = epn[1:]
                            epn = epn
                        elif not epn.startswith('#') and mark_val == 'mark':
                            n_epn = '#' + epn
                            epn = epn
                        else:
                            return 0
                    else:
                        if epn.startswith('#') and mark_val == 'unmark':
                            n_epnt = epn[1:]
                            n_epn = ((self.epn_arr_list[row])).replace('#', '', 1)
                        elif not epn.startswith('#') and mark_val == 'mark':
                            n_epnt = epn
                            n_epn = '#' + self.epn_arr_list[row]
                        else:
                            return 0
                        epn = n_epnt
                        
                file_path = self.get_local_file_ep_name()
                txt = item.text()
                
                if txt.startswith(self.check_symbol) and mark_val == 'unmark':
                    txt = txt[1:]
                    self.list2.item(row).setText(txt)
                    file_change = True
                elif not txt.startswith(self.check_symbol) and mark_val == 'mark':
                    self.list2.item(row).setText(self.check_symbol+txt)
                    file_change = True
                    
                if os.path.exists(file_path) and file_change:
                    lines = open_files(file_path, True)
                    if finalUrlFound == True:
                        if lines[row].startswith('#') and mark_val == 'unmark':
                            lines[row]=lines[row].replace('#', '', 1)
                        elif not lines[row].startswith('#') and mark_val == 'mark':
                            lines[row] = '#'+lines[row]
                    else:
                        if "\n" in lines[row]:
                            lines[row] = n_epn + "\n"
                            logger.info(lines[row])
                        else:
                            lines[row] = n_epn
                    
                    self.epn_arr_list[:]=[]
                    for i in lines:
                        i = i.strip()
                        self.epn_arr_list.append(i)
                    write_files(file_path, lines, line_by_line=True)
                self.list2.setCurrentRow(row)
        
    def watchToggle(self):
        global site, base_url, embed, epn, epn_goto, pre_opt, home, path_Local_Dir
        global opt, siteName, finalUrlFound, refererNeeded
        if (opt == "History" and (site.lower() !="video" 
                    and site.lower()!= 'music' and site.lower()!= 'playlists' 
                    and site.lower()!= 'none')):
                row = self.list2.currentRow()
                item = self.list2.item(row)
                if item:
                    i = (self.list2.item(row).text())
                    if i.startswith(self.check_symbol):
                        self.mark_addons_history_list('unmark', row)
                    else:
                        self.mark_addons_history_list('mark', row)
        elif site.lower() == "playlists":
            row = self.list2.currentRow()
            item = self.list2.item(row)
            if item:
                i = self.list2.item(row).text()
                if i.startswith(self.check_symbol):
                    self.mark_playlist('unmark', row)
                else:
                    self.mark_playlist('mark', row)
        elif site.lower() == "video":
            row = self.list2.currentRow()
            item = self.list2.item(row)
            if item:
                i = self.list2.item(row).text()
                if i.startswith(self.check_symbol):
                    self.mark_video_list('unmark', row)
                else:
                    self.mark_video_list('mark', row)
                #title_row = self.list1.currentRow()
                #dir_path, file_path = os.path.split(self.original_path_name[title_row].split('\t')[-1])
                #logger.info('--------7790----{0}'.format(dir_path))
    
    
    def search_list4_options(self):
        global opt, site, name, base_url, name1, embed, pre_opt, bookmark
        global base_url_picn
        global base_url_summary
        
        r = self.list4.currentRow()
        item = self.list4.item(r)
        if item:
            tmp = str(self.list4.currentItem().text())
            tmp1 = tmp.split(':')[0]
            num = int(tmp1)
            self.list1.setCurrentRow(num)
            self.listfound()
            self.list1.setFocus()
            self.list4.hide()
            self.go_page.clear()
            
    def search_list5_options(self):
        global opt, site, name, base_url, name1, embed, pre_opt, bookmark
        global base_url_picn
        global base_url_summary
        r = self.list5.currentRow()
        item = self.list5.item(r)
        if item:
            tmp = str(self.list5.currentItem().text())
            tmp1 = tmp.split(':')[0]
            num = int(tmp1)
            self.list2.setCurrentRow(num)
            self.epnfound()
            self.list5.setFocus()
            self.goto_epn_filter_txt.clear()
            
    def history_highlight(self):
        global opt, site, name, base_url, name1, embed, pre_opt, bookmark
        global base_url_picn, video_local_stream, category
        global base_url_summary
        if site!= "Music":
            self.subtitle_track.setText("SUB")
            self.audio_track.setText("A/V")
        if (opt == "History" or site == "Music" or site == "Video" 
                or site == "PlayLists") and site != 'MyServer':
            self.listfound()
        elif (site.lower() == 'myserver' and opt.lower() != 'history' and 
                opt.lower() != 'login' and opt.lower() != 'discover'):
            name_now = ''
            if self.list1.currentItem() and self.myserver_threads_count <= 10:
                cur_row = self.list1.currentRow()
                new_name_with_info = self.original_path_name[cur_row].strip()
                extra_info = ''
                if '	' in new_name_with_info:
                    name_now = new_name_with_info.split('	')[0]
                    extra_info = new_name_with_info.split('	')[1]
                else:
                    name_now = new_name_with_info
                self.newlistfound_thread_box.append(
                    GetServerEpisodeInfo(
                        self, logger, site, opt, siteName,
                        video_local_stream, name_now, extra_info,
                        category,from_cache=False
                    ))
                length = len(self.newlistfound_thread_box)-1
                self.newlistfound_thread_box[length].finished.connect(
                    partial(self.finished_newlistfound, length)
                    )
                self.newlistfound_thread_box[length].start()
                self.myserver_threads_count += 1
        else:
            self.rawlist_highlight()
            
    def finished_newlistfound(self, length):
        if self.myserver_threads_count:
            self.myserver_threads_count -= 1
        logger.info('{0} thread remaining'.format(self.myserver_threads_count))
        logger.info('completed {}'.format(length))
        self.update_list2()
        
    def search_highlight(self):
        global opt, site, name, base_url, name1, embed, pre_opt, bookmark
        global base_url_picn
        global base_url_summary
        r = self.list4.currentRow()
        item = self.list4.item(r)
        if item:
            tmp = str(self.list4.currentItem().text())
            tmp1 = tmp.split(':')[0]
            num = int(tmp1)
            self.list1.setCurrentRow(num)
            if opt == "History" or site == "Music":
                self.listfound()
            else:
                self.rawlist_highlight()
    
    def update_list2(self):
        global site, refererNeeded, finalUrlFound, new_tray_widget
        update_pl_thumb = True
        
        if not self.epn_arr_list:
            return 0
            
        if self.list2.isHidden():
            update_pl_thumb = False
            
        print(update_pl_thumb, 'update_playlist_thumb')
        row = self.list2.currentRow()
        self.list2.clear()
        k = 0
        for i in self.epn_arr_list:
            i = i.strip()
            if '	' in i:
                i = i.split('	')[0]
                i = i.replace('_', ' ')
                if i.startswith('#'):
                    i = i.replace('#', self.check_symbol, 1)
                    self.list2.addItem((i))
                else:
                    self.list2.addItem((i))
            else:
                if site == "Local" or finalUrlFound == True:
                    #j = i.split('/')[-1]
                    j = os.path.basename(i)
                    if i.startswith('#') and j:
                        j = j.replace('#', self.check_symbol, 1)
                else:
                    j = i
                j = j.replace('_', ' ')
                if j.startswith('#'):
                    j = j.replace('#', self.check_symbol, 1)
                    self.list2.addItem((j))	
                else:
                    self.list2.addItem((j))
            k = k+1
        self.list2.setCurrentRow(row)
        if self.list2.count() < 30:
            QtCore.QTimer.singleShot(10, partial(self.set_icon_list2, self.epn_arr_list, 
                                    self.list_with_thumbnail, update_pl_thumb))
        else:
            QtCore.QTimer.singleShot(100, partial(self.set_icon_list2, self.epn_arr_list, 
                                    self.list_with_thumbnail, update_pl_thumb))
    
    def set_icon_list2(self, epnArr, list_thumb, update_pl):
        for k in range(len(epnArr)):
            if list_thumb and update_pl:
                icon_name = self.get_thumbnail_image_path(k, epnArr[k])
                icon_new_pixel = self.create_new_image_pixel(icon_name, 128)
                if os.path.exists(icon_new_pixel):
                    try:
                        self.list2.item(k).setIcon(QtGui.QIcon(icon_new_pixel))
                    except:
                        pass
        txt_str = str(self.list1.count())+'/'+str(self.list2.count())
        self.page_number.setText(txt_str)
        
    def mark_History(self):
        global curR, opt, siteName, site, name, home
        file_path = ""
        row = self.list2.currentRow()
        if opt == "History" and site != "PlayLists":
            if site == "SubbedAnime" or site == "DubbedAnime":
                if os.path.exists(os.path.join(home, 'History', site, siteName, name, 'Ep.txt')):
                    file_path = os.path.join(home, 'History', site, siteName, name, 'Ep.txt')
            else:
                if os.path.exists(os.path.join(home, 'History', site, name, 'Ep.txt')):
                    file_path = os.path.join(home, 'History', site, name, 'Ep.txt')

            if os.path.exists(file_path):
                lines = open_files(file_path, True)
                if '#' in self.epn_arr_list[row]:
                    n_epn = self.epn_arr_list[row]
                else:
                    n_epn = '#'+self.epn_arr_list[row]
                if '\n' in lines[row]:
                    lines[row] = n_epn + '\n'
                else:
                    lines[row]= n_epn
                self.epn_arr_list[:]=[]
                for i in lines:
                    i = i.strip()
                    self.epn_arr_list.append(i)
                write_files(file_path, lines, line_by_line=True)
            self.update_list2()
        
    def deleteHistory(self):
        global opt, site, name, pre_opt, home, bookmark, base_url, embed, status, siteName
        global video_local_stream
        
        if self.list1.currentItem():
            epn = self.list1.currentItem().text()
            row = self.list1.currentRow()
        else:
            return 0
        nepn = str(epn) + "\n"
        replc = ""
    
        if site == 'None':
            return 0
            
        if (bookmark and os.path.exists(os.path.join(home, 'Bookmark', status+'.txt'))):
            file_path = os.path.join(home, 'Bookmark', status+'.txt')
            if self.list1.currentItem() and os.path.isfile(file_path):
                row = self.list1.currentRow()
                item = self.list1.item(row)
                lines = open_files(file_path, True)
                lines = [i.strip() for i in lines if i.strip()]
                if row < len(lines):
                    del lines[row]
                    write_files(file_path, lines, line_by_line=True)
                    self.list1.takeItem(row)
                    del item
        elif opt == "History":
            file_path = ''
            if site == "SubbedAnime" or site == "DubbedAnime":
                if os.path.exists(os.path.join(home, 'History', site, siteName, 'history.txt')):
                    file_path = os.path.join(home, 'History', site, siteName, 'history.txt')
            else:
                if os.path.exists(os.path.join(home, 'History', site, 'history.txt')):
                    file_path = os.path.join(home, 'History', site, 'history.txt')
            if not file_path:
                return 0
            row = self.list1.currentRow()
            item = self.list1.item(row)
            nam = str(item.text())
            if item:
                if self.epn_arr_list:
                    icon_name = self.get_thumbnail_image_path(0, self.epn_arr_list[0])
                    icon_dir_path, thumb_name = os.path.split(icon_name)
                    thumb_path = os.path.join(home, 'thumbnails')
                    logger.info('{0}--thumbnail--path--'.format(icon_dir_path))
                    if icon_dir_path.startswith(thumb_path):
                        if os.path.exists(icon_dir_path):
                            shutil.rmtree(icon_dir_path)
                            logger.info('{0}--thumbnail--directory--deleted--'.format(icon_dir_path))
                if site == "SubbedAnime" or site == "DubbedAnime":
                    dir_name =os.path.join(home, 'History', site, siteName, nam)
                    logger.info(dir_name)
                else:
                    dir_name =os.path.join(home, 'History', site, nam)
                    logger.info(dir_name)
                if os.path.exists(dir_name):
                    shutil.rmtree(dir_name)
                    if video_local_stream:
                        torrent_file = dir_name+'.torrent'
                        if os.path.exists(torrent_file):
                            os.remove(torrent_file)
                self.list1.takeItem(row)
                
                del item
                del self.original_path_name[row]
                length = self.list1.count() - 1
                write_files(file_path, self.original_path_name, line_by_line=True)
            
    def create_img_url(self, path):
        m = []
        if '/watch?' in path:
            a = path.split('?')[-1]
            b = a.split('&')
            if b:
                for i in b:
                    j = i.split('=')
                    k = (j[0], j[1])
                    m.append(k)
            else:
                j = a.split('=')
                k = (j[0], j[1])
                m.append(k)
            d = dict(m)
            img_url="https://i.ytimg.com/vi/"+d['v']+"/hqdefault.jpg"
            return img_url
    
    def epn_highlight(self):
        global home, site
        num = self.list2.currentRow()
        if num < 0:
            return 0
        if self.list2.currentItem() and num < len(self.epn_arr_list):
            epn_h = self.list2.currentItem().text()
            inter_val = 10
            
            if '	' in self.epn_arr_list[num]:
                a = (self.epn_arr_list[num]).split('	')[0]
                path = (self.epn_arr_list[num]).split('	')[1]
            else:	
                a = os.path.basename(self.epn_arr_list[num])
                path = (self.epn_arr_list[num])
            path = path.replace('#', '', 1)
            if site == "PlayLists":
                path = path.replace('"', '')
            logger.info(path)
            a1 = a
            self.text.clear()
            if site != "Music":
                self.text.setText((a1))
            a1 = a1.replace('#', '', 1)
            if a1.startswith(self.check_symbol):
                a1 = a1[1:]
            inter = str(inter_val)+'s'
            picnD = ''
            picn = ''
            if (site == "PlayLists" or site == "Local" or site == "Video" 
                    or site == "Music"):
                if site == 'PlayLists':
                    playlist_dir = os.path.join(home, 'thumbnails', 'PlayLists')
                    if not os.path.exists(playlist_dir):
                        os.makedirs(playlist_dir)
                    if self.list1.currentItem():
                        pl_n = self.list1.currentItem().text()
                        playlist_name = os.path.join(playlist_dir, pl_n)
                        if not os.path.exists(playlist_name):
                            try:
                                os.makedirs(playlist_name)
                            except Exception as e:
                                print(e)
                                return 0
                        picnD = os.path.join(playlist_name, a1)
                        try:
                            picn = picnD+'.jpg'
                        except:
                            picn = str(picnD)+'.jpg'
                else:
                    if self.list1.currentItem():
                        name_t = self.list1.currentItem().text()
                    else:
                        name_t = ''
                    if self.list3.currentItem() and site == 'Music':
                        if self.list3.currentItem().text() == 'Playlist':
                            picnD = os.path.join(home, 'thumbnails', 'PlayLists', name_t)
                        else:
                            picnD = os.path.join(home, 'thumbnails', site, name_t)
                    else:
                        picnD = os.path.join(home, 'thumbnails', site, name_t)
                    #print(picnD, '=picnD')
                    if not os.path.exists(picnD):
                        try:
                            os.makedirs(picnD)
                        except Exception as e:
                            print(e)
                            return 0
                    picn = os.path.join(picnD, a1)+'.jpg'
                if ((picn and not os.path.exists(picn) 
                        and 'http' not in path) 
                        or (picn and not os.path.exists(picn) 
                        and 'http' in path and 'youtube.com' in path )):
                    path = path.replace('"', '')
                    if 'http' in path and 'youtube.com' in path and '/watch?' in path:
                        path = self.create_img_url(path)
                    self.threadPoolthumb.append(ThreadingThumbnail(self, logger, path, picn, inter))
                    self.threadPoolthumb[len(self.threadPoolthumb)-1].finished.connect(self.thumbnail_generated)
                    length = len(self.threadPoolthumb)
                    if length == 1:
                        if not self.threadPoolthumb[0].isRunning():
                            self.threadPoolthumb[0].start()
                    
            if not picnD:
                if self.list1.currentItem():
                    name_t = self.list1.currentItem().text()
                else:
                    name_t = ''
                picnD = os.path.join(home, 'thumbnails', name_t)
                if not os.path.exists(picnD):
                    try:
                        os.makedirs(picnD)
                    except Exception as e:
                        print(e)
                        return 0
                try:
                    picn = os.path.join(picnD, a1)+'.jpg'
                except:
                    picn = os.path.join(picnD, str(a1))+'.jpg'
            if os.path.exists(picn):
                self.label.setPixmap(QtGui.QPixmap(picn, "1"))
            else:
                pass
                
    def thumbnail_generated(self):
        print("Process Ended")
        self.threadPoolthumb = self.threadPoolthumb[1:]
        length = len(self.threadPoolthumb)
        if length > 0:
            if not self.threadPoolthumb[0].isRunning():
                self.threadPoolthumb[0].start()
                
    def directepn(self):
        global epn, epn_goto
        epn_goto = 1
        epn = self.goto_epn.text()
        epn = re.sub("#", "", str(epn))
        self.epnfound()
    
    def preview(self):
        global embed, playMpv, Player
        Player = str(self.chk.currentText())
        self.player_val = Player
        if self.mpvplayer_val.processId()>0 and self.tab_2.isHidden():
            self.mpvplayer_val.kill()
            self.mpvplayer_started = False
            self.epnfound()
    
    def nextp(self, val):
        global opt, pgn, genre_num, site, embed, mirrorNo, quality, name
        global pict_arr, name_arr, summary_arr, total_till, browse_cnt, tmp_name
        global list1_items
    
        pict_arr[:]=[]
        name_arr[:]=[]
        summary_arr[:]=[]
        browse_cnt=0
        tmp_name[:]=[]
        list1_items[:]=[]
        
        if val == "next":
            r = self.list3.currentRow()
        else:
            r = val
        item = self.list3.item(r)
        print(r)
        if item:
            opt_val = str(item.text())
            print(opt_val)
            if opt_val == "History" or opt_val == "Random" or opt_val == "List":
                return 0
        elif opt == 'Search':
            opt_val = 'Search'
        else:
            return 0
            
        print(opt_val, pgn, genre_num, name)
        
        self.list1.verticalScrollBar().setValue(self.list1.verticalScrollBar().minimum())
        
        try:
            code = 6
            pgn = pgn + 1
            if opt:
                m = self.site_var.getNextPage(opt_val, pgn, genre_num, self.search_term)
                self.list1.clear()
                self.original_path_name[:] = []
                for i in m:
                    i = i.strip()
                    j = i
                    if '	' in i:
                        i = i.split('	')[0]
                    self.list1.addItem(i)
                    list1_items.append(i)
                    self.original_path_name.append(j)
        except:
            pass
        
    def backp(self, val):
        global opt, pgn, genre_num, embed, mirrorNo, quality, name
        self.list1.verticalScrollBar().setValue(self.list1.verticalScrollBar().minimum())
        if val == "back":
            r = self.list3.currentRow()
        else:
            r = val
        item = self.list3.item(r)
        if item:
            opt_val = str(item.text())
            if opt_val == "History" or opt_val == "Random" or opt_val == "List":
                return 0
        elif opt == 'Search':
            opt_val = 'Search'
        else:
            return 0
        
        try:
            pgn = pgn - 1
            if opt:
                m = self.site_var.getPrevPage(opt_val, pgn, genre_num, self.search_term)
                self.list1.clear()
                self.original_path_name[:] = []
                for i in m:
                    i = i.strip()
                    j = i
                    if '	' in i:
                        i = i.split('	')[0]
                    self.list1.addItem(i)
                    list1_items.append(i)
                    self.original_path_name.append(j)
        except:
            pass
                    
    def gotopage(self):
        key = self.page_number.text()
        global opt, pgn, site
        if (opt != "") and (site == "KissAnime"):
            if key:
                self.list1.verticalScrollBar().setValue(self.list1.verticalScrollBar().minimum())
                pgn = int(key)
                pgn = pgn - 1
                self.nextp(-1)
                
    def label_filter_list_update(self, item_index):
        global viewMode, opt, site, bookmark, thumbnail_indicator, total_till
        global label_arr, browse_cnt, tmp_name, list1_items
        
        length = len(item_index)
        if not self.scrollArea.isHidden():
            length1 = len(list1_items)
        else:
            length1 = self.list2.count()
        
        print(length, '--length-filter-epn--')
        if item_index:
            i = 0
            if not self.scrollArea.isHidden():
                while(i < length):
                    if item_index[i] == 1:
                        t = "self.label_"+str(i)+".show()"
                        exec(t)
                        t = "self.label_"+str(i+length1)+".show()"
                        exec(t)
                    else:
                        t = "self.label_"+str(i)+".hide()"
                        exec(t)
                        t = "self.label_"+str(i+length1)+".hide()"
                        exec(t)
                    i = i+1
            else:
                while(i < length):
                    if item_index[i] == 1:
                        t = "self.label_epn_"+str(i)+".show()"
                        exec(t)
                        t = "self.label_epn_"+str(i+length1)+".show()"
                        exec(t)
                    else:
                        t = "self.label_epn_"+str(i)+".hide()"
                        exec(t)
                        t = "self.label_epn_"+str(i+length1)+".hide()"
                        exec(t)
                    i = i+1
            
    def filter_label_list(self):
        global opt, pgn, site, list1_items, base_url, filter_on, base_url
        global embed, hist_arr
        print("filter label")
        filter_on = 1
        row_history = []
        key = str(self.label_search.text()).lower()
        if not key:
            filter_on = 0
        found_item = []
        found_item_index = []
        print(opt)
        print(site)
        found_item_index[:]=[]
        if not self.scrollArea.isHidden():
            if key:
                for i in range(self.list1.count()):
                    srch = str(self.list1.item(i).text()).lower()
                    if key in srch:
                        found_item.append(i)
                        found_item_index.append(1)
                    else:
                        found_item_index.append(0)
            else:
                for i in range(self.list1.count()):				
                        found_item_index.append(1)
        else:
            if key:
                for i in range(self.list2.count()):
                    srch = str(self.list2.item(i).text()).lower()
                    if key in srch:
                        found_item.append(i)
                        found_item_index.append(1)
                    else:
                        found_item_index.append(0)
            else:
                for i in range(self.list2.count()):				
                        found_item_index.append(1)
                
        self.label_filter_list_update(found_item_index)
    
    def filter_list(self):
        global opt, pgn, site, list1_items, base_url, filter_on, base_url, embed
        global hist_arr
        print("filter label")
        filter_on = 1
        row_history = []
        key = str(self.go_page.text()).lower()
        if not key:
            filter_on = 0
        found_item = []
        found_item_index = []
        print(opt)
        print(site)
        found_item_index[:]=[]
        
        if key:
            self.list4.show()
            for i in range(self.list1.count()):
                srch = str(self.list1.item(i).text())
                srch1 = srch.lower()
                if key in srch1:
                    found_item.append(str(i)+':'+srch)
                    
            length = len(found_item_index)
            self.list4.clear()
            for i in found_item:
                self.list4.addItem(i)
        else:
            self.list4.clear()
            self.list4.hide()
            self.list1.show()
                
    def filter_epn_list_txt(self):
        global opt, pgn, site, list1_items, base_url, filter_on, base_url
        global embed, hist_arr
        print("filter epn list")
        filter_on = 1
        row_history = []
        key = str(self.goto_epn_filter_txt.text()).lower()
        if not key:
            filter_on = 0
        found_item = []
        found_item_index = []
        print(opt)
        print(site)
        found_item_index[:]=[]
        
        if key:
            #self.list1.hide()
            self.list5.show()
            for i in range(len(self.epn_arr_list)):
                srch = self.epn_arr_list[i]
                
                srch1 = srch.lower()
                srch2 = str(self.list2.item(i).text())
                if key in srch1:
                    found_item.append(str(i)+':'+srch2)
                    
            length = len(found_item_index)
            self.list5.clear()
            for i in found_item:
                self.list5.addItem(i)
        else:
            self.list5.clear()
            self.list5.hide()
            self.list2.show()
            
    def ka(self):
        global site, home
        global pict_arr, name_arr, summary_arr, total_till, browse_cnt, tmp_name
        global list1_items, bookmark, total_till, thumbnail_indicator, genre_num
        global rfr_url, finalUrlFound, refererNeeded
        global video_local_stream
        
        genre_num = 0
        #total_till = 0
        if self.site_var:
            del self.site_var
            self.site_var = ''
        self.label.clear()
        self.text.clear()
        if self.myserver_cache:
            self.myserver_cache.clear()
        self.original_path_name[:]=[]
        rfr_url = ""
        finalUrlFound = False
        refererNeeded = False
        site = str(self.btn1.currentText())
        if not self.btnAddon.isHidden():
            self.btnAddon.hide()
        if not self.btnHistory.isHidden():
            self.btnHistory.hide()
        self.list3.clear()
        self.list1.clear()
        self.list2.clear()
        self.label.clear()
        self.text.clear()
        
        if site == "PlayLists":
            self.mirror_change.hide()
            self.line.setPlaceholderText("No Search Option")
            self.line.setReadOnly(True)
            refererNeeded = False
            
            bookmark = False
            criteria = os.listdir(os.path.join(home, 'Playlists'))
            criteria.sort()
            home_n = os.path.join(home, 'Playlists')
            criteria = naturallysorted(criteria)
            self.original_path_name[:] = []
            for i in criteria:
                self.list1.addItem(i)
                self.original_path_name.append(i)
            criteria = ['List', 'Open File', 'Open Url', 'Open Directory']
            for i in criteria:
                self.list3.addItem(i)
            video_local_stream = False
        elif site == "Bookmark":
            bookmark = True
            criteria = [
                'All', 'Watching', 'Completed', 'Incomplete',
                'Interesting', 'Music Videos', 'Later'
                ]
            bookmark_array = [
                'bookmark', 'Watching', 'Completed', 'Incomplete', 
                'Later', 'Interesting', 'Music Videos'
                ]
            bookmark_extra = []
            for i in bookmark_array:
                f_path = os.path.join(home, 'Bookmark', i+'.txt')
                if not os.path.exists(f_path):
                    f = open(f_path, 'w')
                    f.close()
            m = os.listdir(os.path.join(home, 'Bookmark'))
            for i in m:
                i = i.replace('.txt', '')
                if i not in bookmark_array:
                    bookmark_extra.append(i)
            self.list3.clear()
            for i in criteria:
                self.list3.addItem(i)
            for i in bookmark_extra:
                self.list3.addItem(i)
        elif site == "Select":
            site = 'None'
        elif site == "Addons":
            site = 'None'
            self.btnAddon.show()
            site = self.btnAddon.currentText()
            if self.site_var:
                del self.site_var
                self.site_var = ''
            print(type(self.site_var), site, '--addon-changed--')
            plugin_path = os.path.join(home, 'src', 'Plugins', site+'.py')
            if os.path.exists(plugin_path):
                module = imp.load_source(site, plugin_path)
            self.site_var = getattr(module, site)(TMPDIR)
            bookmark = False
            if not os.path.exists(os.path.join(home, "History", site)):
                os.makedirs(os.path.join(home, "History", site))
            self.search()
        elif site == "YouTube":
            site = 'None'
            bookmark = False
            self.search()
        else:
            bookmark = False
            if not os.path.exists(os.path.join(home, "History", site)):
                os.makedirs(os.path.join(home, "History", site))
            self.search()
        
    def ka2(self):
        global site, home
        global pict_arr, name_arr, summary_arr, total_till, browse_cnt, tmp_name
        global list1_items, bookmark, total_till, thumbnail_indicator
        global genre_num, rfr_url, finalUrlFound, refererNeeded
        
        genre_num = 0
        
        if self.site_var:
            del self.site_var
            self.site_var = ''
        self.label.clear()
        self.text.clear()
        self.original_path_name[:]=[]
        rfr_url = ""
        finalUrlFound = False
        refererNeeded = False
        self.list3.clear()
        self.list1.clear()
        self.list2.clear()
        self.label.clear()
        self.text.clear()
        site = (self.btnAddon.currentText())
        print(type(self.site_var), site, '--addon-changed--')
        plugin_path = os.path.join(home, 'src', 'Plugins', site+'.py')
        if os.path.exists(plugin_path):
            module = imp.load_source(site, plugin_path)
        self.site_var = getattr(module, site)(TMPDIR)
        print(type(self.site_var), site, '--addon-changed--')
        if site == 'SubbedAnime' or site == 'DubbedAnime':
            self.btnHistory.show()
        else:
            if not self.btnHistory.isHidden():
                self.btnHistory.hide()
        bookmark = False
        if not os.path.exists(os.path.join(home, "History", site)):
            os.makedirs(os.path.join(home, "History", site))
        self.search()
    
    def ka1(self):
        global site, home
        global pict_arr, name_arr, summary_arr, total_till, browse_cnt, tmp_name
        global list1_items, bookmark
        
        self.label.clear()
        self.text.clear()
        site = str(self.btn30.currentText())
        if site == "Bookmark":
            bookmark = True
            criteria = [
                'All', 'Watching', 'Completed', 'Incomplete', "Later", 
                'Interesting'
                ]
            self.list3.clear()
            for i in criteria:
                self.list3.addItem(i) 
        else:
            bookmark = False
            if not os.path.exists(os.path.join(home, "History", site)):
                os.makedirs(os.path.join(home, "History", site))
            self.search()
        
            
    def reviewsWeb(self, srch_txt=None, review_site=None, action=None):
        global name, nam, old_manager, new_manager, home, screen_width, quality
        global site
        
        btn_hide = self.horizontalLayout_player_opt.itemAt(14)
        print(btn_hide, '--hide--btn--')
        original_srch_txt = None
        new_url = ''
        if srch_txt:
            srch_txt = srch_txt.replace('"', '')
            original_srch_txt = srch_txt
            srch_txt = srch_txt.lower()
            srch_txt = re.sub('\[[^\]]*\]|\([^\)]*\)', '', srch_txt)
            srch_txt = re.sub('-|_| |\.', '+', srch_txt)
            srch_txt = re.sub(
                '\+sub|\+dub|subbed|dubbed|online|720p|1080p|480p|.mkv|.mp4|\+season[^"]*|\+special[^"]*|xvid|bdrip|brrip|ac3|hdtv|dvdrip', '', srch_txt)
            srch_txt = srch_txt.strip()
        if 'AnimeWatch' in home or self.anime_review_site:
            web_arr_dict = {
                'mal':'MyAnimeList', 'ap':'Anime-Planet', 
                'ans':'Anime-Source', 'tvdb':'TVDB', 'tmdb':'TMDB', 'ann':'ANN', 
                'anidb':'AniDB', 'g':'Google', 'yt':'Youtube', 
                'ddg':'DuckDuckGo', 'reviews':'Reviews', 
                'last.fm':'last.fm', 'zerochan':'Zerochan'
                }
        else:
            web_arr_dict = {
                'tvdb':'TVDB', 'tmdb':'TMDB', 
                'g':'Google', 'yt':'Youtube', 
                'ddg':'DuckDuckGo', 'reviews':'Reviews', 
                'last.fm':'last.fm'
                }
        
        if not review_site:
            review_site_tmp = self.btnWebReviews.currentText()
            for i in web_arr_dict:
                if review_site_tmp == web_arr_dict[i]:
                    review_site = i
                    break
            
        self.review_site_code = review_site
        print(self.web, '0')
        if not self.web and review_site:
            try:
                self.web = Browser(self, home, screen_width, self.quality_val, site, self.epn_arr_list)
            except NameError:
                site = 'None'
                self.epn_arr_list = []
                name = srch_txt
                self.web = Browser(self, home, screen_width, self.quality_val, site, self.epn_arr_list)
            self.web.setObjectName(_fromUtf8("web"))
            self.horizontalLayout_5.addWidget(self.web)
            print(self.web, '1')
        elif self.web:
            if QT_WEB_ENGINE:
                cur_location = self.web.url().url()
            else:
                cur_location = self.web.url().toString()
            logger.info('{0}--web--url--'.format(cur_location))
            if 'yt' in review_site.lower() and 'youtube' not in cur_location and QT_WEB_ENGINE:
                self.web.close()
                self.web.deleteLater()
                self.web = Browser(self, home, screen_width, self.quality_val, site, self.epn_arr_list)
                self.web.setObjectName(_fromUtf8("web"))
                self.horizontalLayout_5.addWidget(self.web)
            print(self.web, '2')
        
        self.list1.hide()
        self.list2.hide()
        self.dockWidget_3.hide()
        self.label.hide()
        self.text.hide()
        print(self.VerticalLayoutLabel.itemAt(2), '--itemAt--')
        if self.VerticalLayoutLabel.itemAt(2):
            self.VerticalLayoutLabel.takeAt(2)
            print('--stretch--deleted--')
        self.frame.hide()
        #self.frame1.hide()
        self.tab_2.show()
        self.goto_epn.hide()
        try:
            name = str(name)
        except:
            name = srch_txt
        name1 = re.sub('-|_| |\.', '+', name)
        name1 = name1.lower()
        name1 = re.sub('\[[^\]]*\]|\([^\)]*\)', '', name1)
        name1 = re.sub(
                '\+sub|\+dub|subbed|dubbed|online|720p|1080p|480p|.mkv|.mp4|\+season[^"]*|\+special[^"]*|xvid|bdrip|brrip|ac3|hdtv|dvdrip', '', name1)
        name1 = name1.strip()
        logger.info(name1)
        key = ''
        if action:
            if action == 'return_pressed':
                key = self.btnWebReviews_search.text()
                self.btnWebReviews_search.clear()
                self.tmp_web_srch = key
                if review_site == 'reviews':
                    review_site = 'g'
            elif action == 'context_menu' or action == 'search_by_name':
                key = srch_txt
            elif action == 'index_changed' or action == 'btn_pushed':
                if not self.tmp_web_srch:
                    key = name1
                else:
                    key = self.tmp_web_srch
            elif action == 'line_return_pressed':
                key = self.line.text()
                self.line.clear()
        else:
            key = self.line.text()
            self.line.clear()
        if key:
            name1 = str(key)
        pl_list = False
        
        if not name1:
            if self.list1.currentItem():
                name1 = self.list1.currentItem().text()
                if self.list2.currentItem() and self.btn1.currentText() == 'PlayLists':
                    name1 = self.list2.currentItem().text()
                    r = self.list2.currentRow()
                    finalUrl = self.epn_arr_list[r].split('	')[1]
                    if 'youtube.com' in finalUrl and 'list=' in finalUrl:
                        new_url = finalUrl
                        pl_list = True
            elif self.list2.currentItem():
                name1 = self.list2.currentItem().text()
                
            if name1.startswith(self.check_symbol):
                name1 = name1[1:]
                
        logger.info(self.web)
        self.webStyle(self.web)
        logger.info('--13527---{0}-{1}'.format(review_site, name1))
        self.review_site_code = review_site
        if review_site == "ap":
            self.web.load(QUrl("http://www.anime-planet.com/anime/all?name="+name1))
        elif review_site == "mal":
            self.web.load(QUrl("http://myanimelist.net/anime.php?q="+name1))
        elif review_site == "ans":
            self.web.load(QUrl("http://www.anime-source.com/banzai/modules.php?name=NuSearch&type=all&action=search&info="+name1))
        elif review_site == "tvdb":
            self.web.load(QUrl("http://thetvdb.com/?string="+name1+"&searchseriesid=&tab=listseries&function=Search"))
        elif review_site == "tmdb":
            self.web.load(QUrl("https://www.themoviedb.org/search?query="+name1))
        elif review_site == "anidb":
            self.web.load(QUrl("http://anidb.net/perl-bin/animedb.pl?adb.search="+name1+"&show=animelist&do.search=search"))
        elif review_site == "ann":
            self.web.load(QUrl("http://www.animenewsnetwork.com/encyclopedia/search/name?q="+name1))
        elif review_site == "g":
            self.web.load(QUrl("https://www.google.com/search?q="+name1))
        elif review_site == "ddg":
            self.web.load(QUrl("https://duckduckgo.com/?q="+name1))
        elif review_site == "yt":
            if not name1:
                name1 = 'GNU Linux FSF'
            if pl_list and new_url and action != 'open':
                self.web.load(QUrl(new_url))
            elif action=='open' and original_srch_txt:
                self.web.load(QUrl(original_srch_txt))
            else:
                self.web.load(QUrl("https://m.youtube.com/results?search_query="+name1))
            logger.info('{0}--yt--open--'.format(srch_txt))
        elif review_site == "last.fm":
            self.web.load(QUrl("http://www.last.fm/search?q="+name1))
        elif review_site == 'zerochan':
            self.web.load(QUrl("http://www.zerochan.net/search?q="+name1))
        elif review_site == "reviews":
            self.web.setHtml('<html>Reviews:</html>')
        
        if review_site:
            try:
                if web_arr_dict[review_site] == self.btnWebReviews.currentText():
                    self.btnWebReviews_search.setPlaceholderText('Search '+web_arr_dict[review_site])
            except Exception as e:
                print(e)
        
    def rawlist_highlight(self):
        global site, name, base_url, name1, embed, opt, pre_opt, mirrorNo, list1_items
        global list2_items, quality, row_history, home, epn, path_Local_Dir
        global bookmark, status, siteName
        global screen_height, screen_width
        #print('========raw_list_highlight==========')
        if self.list1.currentItem():
            nm = self.original_path_name[self.list1.currentRow()].strip()
            if '	' in nm:
                name = nm.split('	')[0]
            else:
                name = nm
        else:
            return 0
        cur_row = self.list1.currentRow()
        fanart = os.path.join(TMPDIR, name+'-fanart.jpg')
        thumbnail = os.path.join(TMPDIR, name+'-thumbnail.jpg')
        m = []
        self.epn_arr_list[:]=[]
        #print('========raw_list_highlight==========')
        summary = 'Summary Not Available'
        picn = 'No.jpg'
        if site == "SubbedAnime" or site == "DubbedAnime":
            if self.list3.currentItem():
                siteName = self.list3.currentItem().text()
            #r = self.list1.currentRow()
            
            file_name = os.path.join(home, 'History', site, siteName, name, 'Ep.txt')
            picn1 = os.path.join(home, 'History', site, siteName, name, 'poster.jpg')
            fanart1 = os.path.join(home, 'History', site, siteName, name, 'fanart.jpg')
            thumbnail1 = os.path.join(home, 'History', site, siteName, name, 'thumbnail.jpg')
            summary_file = os.path.join(home, 'History', site, siteName, name, 'summary.txt')
        elif site == "Local":
            
            name = self.original_path_name[cur_row]
            file_name = os.path.join(home, 'Local', name, 'Ep.txt')
            picn1 = os.path.join(home, 'Local', name, 'poster.jpg')
            fanart1 = os.path.join(home, 'Local', name, 'fanart.jpg')
            thumbnail1 = os.path.join(home, 'Local', name, 'thumbnail.jpg')
            summary_file = os.path.join(home, 'Local', name, 'summary.txt')
        else:
            file_name = os.path.join(home, 'History', site, name, 'Ep.txt')
            picn1 = os.path.join(home, 'History', site, name, 'poster.jpg')
            fanart1 = os.path.join(home, 'History', site, name, 'fanart.jpg')
            thumbnail1 = os.path.join(home, 'History', site, name, 'thumbnail.jpg')
            summary_file = os.path.join(home, 'History', site, name, 'summary.txt')
        #print "file_name="+file_name
        logger.info(file_name)
        if os.path.exists(file_name) and site!="PlayLists":
            #print(site, siteName, name, file_name)
            lines = open_files(file_name, True)
            m = []
            if site == "Local" and lines:
                for i in lines:
                    i = i.strip()
                    if i:
                        if '	'in i:
                            k = i.split('	')
                            
                            self.epn_arr_list.append(i)
                            
                            m.append(k[0])
                        else:
                            k = os.path.basename(i)
                            self.epn_arr_list.append(k+'	'+i)
                            m.append(k)
            elif lines:
                logger.info(file_name)
                for i in lines:
                    i = i.strip()
                    if i:
                        self.epn_arr_list.append(i)
                        m.append(i)
                    
            picn = picn1
            fanart = fanart1
            thumbnail = thumbnail1
            
            if os.path.isfile(summary_file):
                summary = open_files(summary_file, False)
            
            j = 0
            
            self.text.clear()
            
            self.text.lineWrapMode()
            if site!= "Local":
                pass
                
            if summary.lower() == 'summary not available':
                summary = summary+'\n'+self.original_path_name[cur_row]
                
            self.videoImage(picn, thumbnail, fanart, summary)
                
            if os.path.isfile(file_name):
                self.list2.clear()
                self.update_list2()
        else:
            if summary.lower() == 'summary not available':
                txt = self.original_path_name[cur_row]
                if '	' in txt:
                    txt1, txt2 = txt.split('	')
                    summary = summary+'\n\n'+txt1+'\n\n'+txt2
            self.text.clear()
            self.text.insertPlainText(summary)
            self.list2.clear()
            
    def searchNew(self):
        global search, name
        if self.btn1.currentText() == "Select":
            site = "None"
            return 0
        elif (self.line.placeholderText()) == "No Search Option":
            return 0
        else:
            self.search()
            name = (self.line.text())
            
    def search(self):
        code = 1
        global site, base_url, embed, list1_items, opt, mirrorNo, hdr, quality
        global site_arr, siteName, finalUrlFound
        global pict_arr, name_arr, summary_arr, total_till, browse_cnt, tmp_name
        global list2_items, bookmark, refererNeeded, video_local_stream, name
        
        pict_arr[:]=[]
        name_arr[:]=[]
        summary_arr[:]=[]
        browse_cnt=0
        tmp_name[:]=[]
        opt = "Search"
        m=[]
        criteria = []
        self.options_mode = 'legacy'
        print(site, self.btn1.currentText().lower())
        
        if site and (site not in site_arr) and self.site_var:
            print(site)
            
            self.mirror_change.hide()
            
            if self.site_var:
                criteria = self.site_var.getOptions() 
                self.list3.clear()
                print(criteria)
                tmp = criteria[-1]
                if tmp == "FinalUrl:Referer:":
                    criteria.pop()
                    finalUrlFound = True
                    refererNeeded = True
                    video_local_stream = False
                elif tmp == 'LocalStreaming':
                    criteria.pop()
                    video_local_stream = True
                    if not self.local_ip:
                        self.local_ip = get_lan_ip()
                    if not self.local_port:
                        self.local_port = 8001
                    self.torrent_type = 'file'
                elif tmp.lower() == 'newversion':
                    criteria.pop()
                    self.options_mode = 'new'
                else:
                    finalUrlFound = False
                    refererNeeded = False
                    video_local_stream = False
                for i in criteria:
                    self.list3.addItem(i)
                self.line.setPlaceholderText("Search Available")
                self.line.setReadOnly(False)
                self.line.show()
                name = self.line.text()
                if name:
                    self.line.clear()
                    self.list1.clear()
                    genre_num = 0
                    try:
                        self.text.setText('Wait...Loading')
                        QtWidgets.QApplication.processEvents()
                        m = self.site_var.search(name)
                        self.search_term = name
                        self.text.setText('Load Complete!')
                    except Exception as e:
                        print(e)
                        self.text.setText('Load Failed')
                        return 0
                    if type(m) is list:
                        self.original_path_name[:] = []
                        for i in m:
                            i = i.strip()
                            j = i
                            if '	' in i:
                                i = i.split('	')[0]
                            self.list1.addItem(i)
                            self.original_path_name.append(j)
                    else:
                        self.list1.addItem("Sorry No Search Function")
        elif site == "Local":
            self.mirror_change.hide()
            criteria = ["List", 'History', 'All']
            self.list3.clear()
            for i in criteria:
                self.list3.addItem(i)
            self.line.setPlaceholderText("No Search Option")
            self.line.setReadOnly(True)
            refererNeeded = False
            video_local_stream = False
        elif site == "Music":
            self.mirror_change.hide()
            criteria = [
                'Playlist', "Artist", 'Album', 'Title', 'Directory', 
                'Fav-Artist', 'Fav-Album', 'Fav-Directory', 
                'Last 50 Played', 'Last 50 Newly Added', 
                'Last 50 Most Played'
                ]
            self.list3.clear()
            for i in criteria:
                self.list3.addItem(i)
            self.line.setPlaceholderText("No Search Option")
            self.line.setPlaceholderText("Search Available")
            self.line.setReadOnly(False)
            refererNeeded = False
            video_local_stream = False
            nm = self.line.text()
            if nm:
                self.line.clear()
                self.list1.clear()
                music_db = os.path.join(home, 'Music', 'Music.db')
                m = self.media_data.get_music_db(music_db, 'Search', nm)
                logger.info(m)
                self.epn_arr_list[:]=[]
                self.list2.clear()
                for i in m:
                    i1 = i[1]
                    i2 = i[2]
                    i3 = i[0]
                    j = i1+'	'+i2+'	'+i3
                    try:
                        self.epn_arr_list.append(str(j))
                    except:
                        self.epn_arr_list.append(j)
                self.update_list2()
        elif site == "Video":
            self.mirror_change.hide()
            criteria = [
                'Directory', 'Available', 'History', 'Update', 'UpdateAll'
                ]
            insert_index = criteria.index('Update')
            for i in self.category_array:
                criteria.insert(insert_index, i)
                insert_index += 1
                
            self.list3.clear()
            for i in criteria:
                self.list3.addItem(i)
            self.line.setPlaceholderText("Search Available")
            self.line.setReadOnly(False)
            refererNeeded = False
            video_local_stream = False
            nm = self.line.text()
            if nm:
                self.line.clear()
                self.list1.clear()
                video_db = os.path.join(home, 'VideoDB', 'Video.db')
                m = self.media_data.get_video_db(video_db, 'Search', nm)
                logger.info(m)
                self.epn_arr_list[:]=[]
                self.list2.clear()
                for i in m:
                    j = i[0]+'	'+i[1]+'	'+'NONE'
                    try:
                        self.epn_arr_list.append(str(j))
                    except:
                        self.epn_arr_list.append(j)
                self.update_list2()
        elif ((site == "None" and self.btn1.currentText().lower() == 'youtube') or not self.tab_2.isHidden()):
            video_local_stream = False
            self.mirror_change.hide()
            self.line.setPlaceholderText("Search Available")
            self.line.setReadOnly(False)
            name_t = self.line.text()
            if name_t:
                name = name_t
                cnt = self.btnWebReviews.findText('Youtube')
                self.btnWebReviews.setCurrentIndex(cnt)
                self.reviewsWeb(srch_txt=name, review_site='yt', action='line_return_pressed')
        elif site == "DubbedAnime" or site == "SubbedAnime":
            video_local_stream = False
            self.mirror_change.show()
            
            if self.site_var:
                criteria = self.site_var.getOptions() 
                code = 7
                self.list3.clear()
                for i in criteria:
                    self.list3.addItem(i)
                self.line.setPlaceholderText("No Search Option")
                self.line.setReadOnly(True)
                name = self.line.text()
                if name:
                    self.line.clear()
                    self.list1.clear()
                    genre_num = 0
                    self.text.setText('Wait...Loading')
                    QtWidgets.QApplication.processEvents()
                    try:
                        m = self.site_var.getCompleteList(siteName, category, 'Search')
                        self.text.setText('Load Complete!')
                    except Exception as e:
                        print(e)
                        self.text.setText('Load Failed')
                        return 0
                    self.original_path_name[:] = []
                    for i in m:
                        i = i.strip()
                        j = i
                        if '	' in i:
                            i = i.split('	')[0]
                        self.list1.addItem(i)
                        self.original_path_name.append(i)
        list1_items[:] = []
        if m:
            for i in m:
                list1_items.append(i)	
    
    def get_torrent_handle(self, nm):
        handle = None
        if self.stream_session:
            t_list = self.stream_session.get_torrents()
            logger.info('--15197---')
            for i in t_list:
                old_name = i.name()
                logger.info('--check--{0}'.format(old_name))
                if old_name == nm:
                    logger.info('selecting handle: {0}'.format(nm))
                    handle = i
                    break
        return handle
    
    def summary_write_and_image_copy(self, hist_sum, summary, picn, hist_picn):
        write_files(hist_sum, summary, line_by_line=False)
        if os.path.isfile(picn):
            shutil.copy(picn, hist_picn)
            
    def get_summary_history(self, file_name):
        summary = open_files(file_name, False)
        return summary

    def get_title_name(self, row):
        global site
        name = ''
        if (site != "PlayLists" and site != "Music" and site != "Video" 
                and site!="Local" and site !="None"):
            cur_row = row
            new_name_with_info = self.original_path_name[cur_row].strip()
            extra_info = ''
            if '	' in new_name_with_info:
                name = new_name_with_info.split('	')[0]
                extra_info = new_name_with_info.split('	')[1]
            else:
                name = new_name_with_info
        elif site == 'Music':
            nm = ''
            try:
                if str(self.list3.currentItem().text()) == "Artist":
                    nm = self.list1.item(row).text()
                else:
                    row = self.list2.currentRow()
                    nm = self.epn_arr_list[row].split('	')[2]
                    nm = nm.replace('"', '')
            except Exception as e:
                    print(e)
                    nm = ""
            name = nm
            if '/' in name:
                name = name.replace('/', '-')
        elif site == 'Local':
            name = self.original_path_name[row]
        elif site == 'Video':
            item = self.list1.item(row)
            if item:
                art_n = str(self.list1.item(row).text())
                name = art_n
        return name
    
    def newlistfound(self, site, opt, siteName, video_local_stream,
                     name, extra_info, category, from_cache=None):
        global home
        m = []
        if (site != "PlayLists" and site != "Music" and site != "Video" 
                and site!="Local" and site !="None") and name:
            fanart = os.path.join(TMPDIR, name+'-fanart.jpg')
            thumbnail = os.path.join(TMPDIR, name+'-thumbnail.jpg')
            summary = "Summary Not Available"
            picn = "No.jpg"
            self.list2.clear()
            site_variable = '{0}::{1}::{2}::{3}::{4}::{5}'.format(
                    site, siteName, opt, name, extra_info, category
                    )
            print(site_variable)
            if not from_cache and site_variable not in self.myserver_cache:
                if opt != "History" or site.lower() == 'myserver':
                    #self.text.setText('Wait...Loading')
                    #QtWidgets.QApplication.processEvents()
                    try:
                        if video_local_stream:
                            siteName = os.path.join(home, 'History', site)
                            if not os.path.exists(siteName):
                                os.makedirs(siteName)
                        m, summary, picn, self.record_history, self.depth_list = self.site_var.getEpnList(
                                name, opt, self.depth_list, extra_info, siteName, 
                                category)
                        #self.text.setText('Load..Complete')
                    except Exception as e:
                        print(e)
                        #self.text.setText('Load..Failed')
                    if not m:
                        return 0
                    else:
                        self.myserver_cache.update({site_variable:m.copy()})
            else:
                m = self.myserver_cache.get(site_variable)
            self.set_parameters_value(name_val=name)
            self.epn_arr_list.clear()
            if m:
                for i in m:
                    self.epn_arr_list.append(i)
            if from_cache:
                if site.lower() == 'subbedanime' or site.lower() == 'dubbedanime':
                    hist_path = os.path.join(home, 'History', site, siteName, 'history.txt')
                else:
                    hist_path = os.path.join(home, 'History', site, 'history.txt')

                hist_dir, last_field = os.path.split(hist_path)
                hist_site = os.path.join(hist_dir, name)
                hist_epn = os.path.join(hist_site, 'Ep.txt')
                hist_sum = os.path.join(hist_site, 'summary.txt')
                hist_picn = os.path.join(hist_site, 'poster.jpg')
                self.update_list2()
                if os.path.isfile(hist_sum) or os.path.isfile(hist_picn):
                    self.videoImage(picn, thumbnail, fanart, summary)
    
    def listfound(self):
        global site, name, base_url, name1, embed, opt, pre_opt, mirrorNo, list1_items
        global list2_items, quality, row_history, home, epn, path_Local_Dir, bookmark
        global status, finalUrlFound, refererNeeded, audio_id, sub_id
        global opt_movies_indicator, base_url_picn, base_url_summary, siteName
        global img_arr_artist, screen_height, screen_width, video_local_stream
        
        img_arr_artist[:]=[]
        opt_movies_indicator[:]=[]
        new_dir_path = None
        fanart = os.path.join(TMPDIR, name+'-fanart.jpg')
        thumbnail = os.path.join(TMPDIR, name+'-thumbnail.jpg')
        summary = "Summary Not Available"
        picn = "No.jpg"
        m = []
        if bookmark and os.path.exists(os.path.join(home, 'Bookmark', status+'.txt')):
            #tmp = site+':'+opt+':'+pre_opt+':'+base_url+':'+str(embed)+':'+name':'+
            #finalUrlFound+':'+refererNeeded+':'+video_local_stream
            #f = open(os.path.join(home, 'Bookmark', status+'.txt'), 'r')
            line_a = open_files(os.path.join(home, 'Bookmark', status+'.txt'), True)
            r = self.list1.currentRow()
            if r < 0 or r >= len(line_a):
                logger.info('--wrong--value--of row--7014--')
                return 0
            tmp = line_a[r]
            tmp = tmp.strip()
            tmp1 = tmp.split(':')
            site = tmp1[0]
            if site == "Music" or site == "Video":
                opt = "Not Defined"
                if site == "Music":
                    music_opt = tmp1[1]
                else:
                    video_opt = tmp1[1]
            else:
                opt = tmp1[1]
            pre_opt = tmp1[2]
            siteName = tmp1[2]
            base_url = int(tmp1[3])
            embed = int(tmp1[4])
            name = tmp1[5]
            if site=="Local":
                name_path = name
            
            logger.info(name)
            if len(tmp1) > 6:
                if tmp1[6] == "True":
                    finalUrlFound = True
                else:
                    finalUrlFound = False
                if tmp1[7] == "True":
                    refererNeeded = True
                else:
                    refererNeeded = False
                if len(tmp1) >=9:
                    if tmp1[8] == "True":
                        video_local_stream = True
                    else:
                        video_local_stream = False
                if len(tmp1) >=10:
                    new_dir_path = tmp1[9]
                print(finalUrlFound)
                print(refererNeeded)
                print(video_local_stream)
                logger.info(new_dir_path)
            else:
                refererNeeded = False
                finalUrlFound = False
                video_local_stream = False
            logger.info(site + ":"+opt)
            if (site != "PlayLists" and site != "Music" and site != "Video" 
                    and site!="Local" and site !="None"):
                plugin_path = os.path.join(home, 'src', 'Plugins', site+'.py')
                if os.path.exists(plugin_path):
                    if self.site_var:
                        del self.site_var
                        self.site_var = ''
                    module = imp.load_source(site, plugin_path)
                    self.site_var = getattr(module, site)(TMPDIR)
                else:
                    return 0
                    
        if (site != "PlayLists" and site != "Music" and site != "Video" 
                and site!="Local" and site !="None"):
            self.list2.clear()
            if self.list1.currentItem():
                cur_row = self.list1.currentRow()
                new_name_with_info = self.original_path_name[cur_row].strip()
                extra_info = ''
                if '	' in new_name_with_info:
                    name = new_name_with_info.split('	')[0]
                    extra_info = new_name_with_info.split('	')[1]
                else:
                    name = new_name_with_info
                        
                if opt != "History" or site.lower() == 'myserver':
                    m = []
                    #try:
                    self.text.setText('Wait...Loading')
                    QtWidgets.QApplication.processEvents()
                    try:
                        if video_local_stream:
                            siteName = os.path.join(home, 'History', site)
                            if not os.path.exists(siteName):
                                os.makedirs(siteName)
                        m, summary, picn, self.record_history, self.depth_list = self.site_var.getEpnList(
                                name, opt, self.depth_list, extra_info, siteName, 
                                category)
                        self.text.setText('Load..Complete')
                    except Exception as e:
                        print(e)
                        self.text.setText('Load..Failed')
                    if not m:
                        return 0
                    
                    self.epn_arr_list[:]=[]
                    for i in m:
                        self.epn_arr_list.append(i)
                        
                    if site.lower() == 'subbedanime' or site.lower() == 'dubbedanime':
                        hist_path = os.path.join(home, 'History', site, siteName, 'history.txt')
                    else:
                        hist_path = os.path.join(home, 'History', site, 'history.txt')
                    if not os.path.isfile(hist_path):
                        hist_dir, last_field = os.path.split(hist_path)
                        if not os.path.exists(hist_dir):
                            os.makedirs(hist_dir)
                        f = open(hist_path, 'w').close()
                    print(self.record_history, '--self.record_history---')
                    if os.path.isfile(hist_path) and self.record_history:
                        if (os.stat(hist_path).st_size == 0):
                            write_files(hist_path, new_name_with_info, line_by_line=True)
                        else:
                            lines = open_files(hist_path, True)
                            line_list = []
                            for i in lines :
                                i = i.strip()
                                line_list.append(i)
                                
                            if new_name_with_info not in line_list:
                                write_files(hist_path, new_name_with_info, line_by_line=True)
                    
                    hist_dir, last_field = os.path.split(hist_path)
                    hist_site = os.path.join(hist_dir, name)
                    hist_epn = os.path.join(hist_site, 'Ep.txt')
                    if (not os.path.exists(hist_site) and self.record_history) or (os.path.exists(hist_epn)):
                        try:
                            first_try = False
                            if not os.path.exists(hist_site):
                                os.makedirs(hist_site)
                                first_try = True
                            
                            if not first_try or site == 'MyServer':
                                lines = open_files(hist_epn, True)
                                if len(m) > len(lines):
                                    length_old = len(lines)
                                    m = m[length_old:]
                                    m = lines + m
                            
                            write_files(hist_epn, m, line_by_line=True)
                            
                            if first_try:
                                hist_sum = os.path.join(hist_site, 'summary.txt')
                                hist_picn = os.path.join(hist_site, 'poster.jpg')
                                self.summary_write_and_image_copy(hist_sum, summary, picn, hist_picn)
                        except Exception as e:
                            print(e)
                            return 0
                else:
                    if site.lower() == 'subbedanime' or site.lower() == 'dubbedanime':
                        if self.list3.currentItem() and not bookmark:
                            siteName = self.list3.currentItem().text()
                        hist_site = os.path.join(home, 'History', site, siteName, name)
                    else:
                        hist_site = os.path.join(home, 'History', site, name)
                        
                    hist_epn = os.path.join(hist_site, 'Ep.txt')
                    logger.info(hist_epn)
                    if os.path.exists(hist_epn):
                        lines = open_files(hist_epn, True)
                        m = []
                        self.epn_arr_list[:]=[]
                        for i in lines:
                            i = i.strip()
                            self.epn_arr_list.append(i)
                            m.append(i)
                                
                        picn = os.path.join(hist_site, 'poster.jpg')
                        fanart = os.path.join(hist_site, 'fanart.jpg')
                        thumbnail = os.path.join(hist_site, 'thumbnail.jpg')
                        sum_file = os.path.join(hist_site, 'summary.txt')
                        summary = self.get_summary_history(sum_file)

                        f_name = os.path.join(hist_site, 'Ep.txt')
                        if os.path.exists(f_name):
                            lines = open_files(f_name, True)
                            if len(self.epn_arr_list) > len(lines):
                                write_files(f_name, m, line_by_line=True)
                self.videoImage(picn, thumbnail, fanart, summary)
        elif site == "Music":
            try:
                art_n = str(self.list1.currentItem().text())
            except:
                return 0
            music_dir = os.path.join(home, 'Music')

            music_db = os.path.join(home, 'Music', 'Music.db')
            music_file = os.path.join(home, 'Music', 'Music.txt')
            music_file_bak = os.path.join(home, 'Music', 'Music_bak.txt')
            if not bookmark:
                if not self.list3.currentItem():
                    self.list3.setCurrentRow(0)
                music_opt = self.list3.currentItem().text()

            artist =[]

            if music_opt == "Directory":
                index = self.list1.currentRow()
                art_n = self.original_path_name[index]
            if music_opt == "Fav-Directory":
                index = self.list1.currentRow()
                art_n = self.original_path_name[index]
            if music_opt == "Playlist":
                r = self.list1.currentRow()
                item = self.list1.item(r)
                if item:
                    pls = str(item.text())
                    m = open_files(os.path.join(home, 'Playlists', pls), True)
                    for i in m:
                        i = i.replace('\n', '')
                        if i:
                            j = i.split('	')
                            i1 = j[0]
                            i2 = j[1]
                            try:
                                i3 = j[2]
                            except:
                                i3 = "None"
                            artist.append(i1+'	'+i2+'	'+i3)
            else:
                m = self.media_data.get_music_db(music_db, music_opt, art_n)
                for i in m:
                    if len(i) > 2:
                        artist.append(i[1]+'	'+i[2]+'	'+i[0])
            self.epn_arr_list[:]=[]
            self.list2.clear()
            for i in artist:
                try:
                    self.epn_arr_list.append(str(i))
                except:
                    self.epn_arr_list.append((i))
                
            self.musicBackground(0, 'offline')
        elif site == "PlayLists":
            self.list2.clear()
            r = self.list1.currentRow()
            item = self.list1.item(r)
            self.epn_arr_list[:]=[]
            if item:
                pls = self.list1.currentItem().text()
                file_path = os.path.join(home, 'Playlists', str(pls))
                if os.path.exists(file_path):
                    lines = open_files(file_path, True)
                    k = 0
                    for i in lines:
                        i = i.replace('\n', '')
                        if i:	
                            self.epn_arr_list.append(i)
        elif site == "Video":
            r = self.list1.currentRow()
            item = self.list1.item(r)
            if item:
                art_n = str(self.list1.currentItem().text())
                name = art_n
                video_dir = os.path.join(home, 'VideoDB')
                
                video_db = os.path.join(video_dir, 'Video.db')
                video_file = os.path.join(video_dir, 'Video.txt')
                video_file_bak = os.path.join(video_dir, 'Video_bak.txt')
                
                artist =[]
                if not bookmark:
                    if self.list3.currentItem():
                        video_opt = str(self.list3.currentItem().text())
                    else:
                        video_opt = 'History'
                    if video_opt == "Update" or video_opt == "UpdateAll":
                        video_opt = "Available"
                        self.video_dict.clear()
                    if video_opt.lower() != "update" and video_opt.lower() != "updateall":
                        index = self.list1.currentRow()
                        art_n = self.original_path_name[index].split('	')[-1]
                        if art_n in self.video_dict:
                            m = self.video_dict[art_n]
                            logger.info('Getting from Cache')
                        else:
                            m = self.media_data.get_video_db(video_db, "Directory", art_n)
                            mlist = [list(i) for i in m]
                            self.video_dict.update({art_n:mlist})
                            logger.info('Getting from DB')
                            logger.info(type(m))
                else:
                    new_art_n = art_n
                    if new_dir_path is not None:
                        if new_dir_path.lower() != 'none':
                            new_art_n = new_dir_path
                            m = self.media_data.get_video_db(video_db, "Directory", new_art_n)
                        else:
                            m = self.media_data.get_video_db(video_db, "Bookmark", new_art_n)
                    else:
                        m = self.media_data.get_video_db(video_db, "Bookmark", new_art_n)
                    
                for i in m:
                    artist.append(i[0]+'	'+i[1])
                    
                self.epn_arr_list[:] = []
                self.list2.clear()
                for i in artist:
                    self.epn_arr_list.append((i))
                #self.epn_arr_list = naturallysorted(self.epn_arr_list)
                art_n = str(self.list1.currentItem().text())
                dir_path = os.path.join(home, 'Local', art_n)
                if os.path.exists(dir_path):
                    picn = os.path.join(home, 'Local', art_n, 'poster.jpg')
                    thumbnail = os.path.join(home, 'Local', art_n, 'thumbnail.jpg')
                    fanart = os.path.join(home, 'Local', art_n, 'fanart.jpg')
                    summary1 = os.path.join(home, 'Local', art_n, 'summary.txt')
                    if os.path.exists(summary1):
                        summary = open_files(summary1, False)
                    else:
                        summary = "Not Available"
                    
                    self.videoImage(picn, thumbnail, fanart, summary)
                    logger.info(picn)
                else:
                    os.makedirs(dir_path)
        self.current_background = fanart
        self.update_list2()

    def set_list_thumbnail(self, k):
        if self.list_with_thumbnail:
            icon_name = self.get_thumbnail_image_path(k, self.epn_arr_list[k])
            if os.path.exists(icon_name):
                self.list2.item(k).setIcon(QtGui.QIcon(icon_name))

    def musicBackground(self, val, srch):
        global name, artist_name_mplayer, site
        logger.info('{0}-{1}--music--background--'.format(val, srch))
        if self.list3.currentItem() and site.lower() == 'music':
            if self.list3.currentItem().text().lower() == "artist":
                artist_mode = True
            else:
                artist_mode = False
        else:
            artist_mode = False
        print(artist_mode, '----artist--mode---')
        if artist_mode:
            music_dir_art = os.path.join(home, 'Music', 'Artist')
            if not os.path.exists(music_dir_art):
                os.makedirs(music_dir_art)
            if self.list1.currentItem():
                if srch != "Queue":
                    nm = str(self.list1.currentItem().text())
                    if '/' in nm:
                        nm = nm.replace('/', '-')
                else:
                    nm = artist_name_mplayer
                music_dir_art_name = os.path.join(home, 'Music', 'Artist', nm)
                logger.info(music_dir_art_name)
                if not os.path.exists(music_dir_art_name):
                    os.makedirs(music_dir_art_name)
                else:
                    art_list = os.listdir(music_dir_art_name)
                    sumr = os.path.join(music_dir_art_name, 'bio.txt')
                    if os.path.exists(sumr):
                        summary = open_files(sumr, False)
                    else:
                        summary = "Not Available"
                    
                    poster = os.path.join(music_dir_art_name, 'poster.jpg')
                    fan = os.path.join(music_dir_art_name, 'fanart.jpg')
                    thumb = os.path.join(music_dir_art_name, 'thumbnail.jpg')
                    if not os.path.exists(poster) and srch != "offline" and self.get_artist_metadata:	
                        self.threadPool.append(ThreadingExample(nm, logger, TMPDIR))
                        self.threadPool[len(self.threadPool)-1].finished.connect(lambda x=nm: self.finishedM(nm))
                        self.threadPool[len(self.threadPool)-1].start()
                    else:
                        self.videoImage(poster, thumb, fan, summary)
        else:
            music_dir_art = os.path.join(home, 'Music', 'Artist')
            logger.info('{0}=music_dir_art'.format(music_dir_art))
            try:
                if srch != "Queue":
                    nm = self.epn_arr_list[val].split('	')[2]
                else:
                    nm = artist_name_mplayer
            except:
                nm = ""
            logger.info("Name of Artist is {0}".format(nm))
            if nm:
                if '/' in nm:
                    nm = nm.replace('/', '-')
                nm = nm.replace('"', '')
                #nm = nm.replace("'", "")
                if nm.lower()!= 'none' and not nm.startswith('http'):
                    artist_name_mplayer = nm
                else:
                    artist_name_mplayer = ''
                music_dir_art_name = os.path.join(home, 'Music', 'Artist', nm)
                logger.info('music_dir_art_name={0}'.format(music_dir_art_name))
                if not os.path.exists(music_dir_art_name):
                    os.makedirs(music_dir_art_name)
                #else:
                art_list = os.listdir(music_dir_art_name)
                sumr = os.path.join(music_dir_art_name, 'bio.txt')
                if os.path.exists(sumr):
                    summary = open_files(sumr, False)
                else:
                    summary = "Not Available"
                    
                poster = os.path.join(music_dir_art_name, 'poster.jpg')
                fan = os.path.join(music_dir_art_name, 'fanart.jpg')
                thumb = os.path.join(music_dir_art_name, 'thumbnail.jpg')
                logger.info('poster={0}--srch={1}--artist={2}'.format(poster, srch, artist_name_mplayer))
                if (not os.path.exists(poster) and srch != "offline" 
                        and artist_name_mplayer.lower() != "none" 
                        and artist_name_mplayer and self.get_artist_metadata):	
                    print('--starting--thread--')
                    self.threadPool.append(ThreadingExample(nm, logger, TMPDIR))
                    self.threadPool[len(self.threadPool)-1].finished.connect(lambda x=nm: self.finishedM(nm))
                    self.threadPool[len(self.threadPool)-1].start()
                elif os.path.exists(poster) or os.path.exists(fan) or os.path.exists(thumb):
                    self.videoImage(poster, thumb, fan, summary)
                else:
                    try:
                        r = self.list2.currentRow()
                        thumb_path = self.get_thumbnail_image_path(r, self.epn_arr_list[r])
                        if os.path.exists(thumb_path):
                            self.videoImage(thumb_path, thumb_path, thumb_path, '')
                    except Exception as e:
                        print('No Thumbnail Available: {0}'.format(e))
            else:
                try:
                    r = self.list2.currentRow()
                    thumb_path = self.get_thumbnail_image_path(r, self.epn_arr_list[r])
                    if os.path.exists(thumb_path):
                        self.videoImage(thumb_path, thumb_path, thumb_path, '')
                except Exception as e:
                    print('No Thumbnail Available: {0}'.format(e))
                    
    def round_corner(self, im, rad):
        circle = Image.new('L', (rad * 2, rad * 2), 0)
        draw = ImageDraw.Draw(circle)
        draw.ellipse((0, 0, rad * 2, rad * 2), fill=255)
        alpha = Image.new('L', im.size, 255)
        w, h = im.size
        #alpha.paste(circle.crop((0, 0, rad, rad)), (0, 0))
        #alpha.paste(circle.crop((0, rad, rad, rad * 2)), (0, h - rad))
        #alpha.paste(circle.crop((rad, 0, rad * 2, rad)), (w - rad, 0))
        alpha.paste(circle.crop((rad, rad, rad * 2, rad * 2)), (w - rad, h - rad))
        im.putalpha(alpha)
        return im

    def image_fit_option(self, picn, fanart, fit_size=None, widget=None,
                         widget_size=None, color=None):
        """
        fit_size = 1. Fit to Screen (Doesn't Preserve aspect ratio (A.R.))
        fit_size = 2. Fit to Screen Width (Preserve A.R.)
        fit_size = 3. Fit to Screen Height (Preserve A.R.)
        fit_size = 4. Fit to Screen Height and (screen-width - playlist_width) 
        with black border (Preserve A.R.)
        fit_size = 5. Fit to Screen Height with black border (Preserve A.R.)
        fit_size = 6. Fit to given widget size and preserve aspect ratio
        fit_size = 7. Fit to Screen Height (Left Side) with black border gap 
        between two posters
        fit_size = 8. Fit to Screen Height (Left Side) with black border
        """
        #print(color,'--color--')
        logger.info('{0}:{1}:{2}:{3}:{4}:{5}'.format(picn,fanart,fit_size,widget,widget_size,color))
        global screen_height, screen_width
        if not color:
            color = 'RGB'
        try:
            if fit_size:
                if (fit_size == 1 or fit_size == 2) or fit_size > 100:
                    if fit_size == 1 or fit_size == 2:
                        basewidth = screen_width
                    else:
                        basewidth = fit_size
                    try:
                        img = Image.open(str(picn))
                    except Exception as e:
                        print(e, 'Error in opening image, videoImage, ---13238')
                        picn = os.path.join(home, 'default.jpg')
                        img = Image.open(str(picn))
                    if fit_size == 1:
                        hsize = screen_height
                    else:
                        wpercent = (basewidth / float(img.size[0]))
                        hsize = int((float(img.size[1]) * float(wpercent)))
                    img = img.resize((basewidth, hsize), PIL.Image.ANTIALIAS)
                    bg = Image.new(color, (basewidth, hsize))
                    bg.paste(img, (0, 0))
                    bg.save(str(fanart), 'JPEG', quality=100)
                    #img.save(str(fanart))
                elif fit_size == 3:
                    baseheight = screen_height
                    try:
                        img = Image.open(str(picn))
                    except Exception as e:
                        print(e, 'Error in opening image, videoImage, ---13253')
                        picn = os.path.join(home, 'default.jpg')
                        img = Image.open(str(picn))
                    wpercent = (baseheight / float(img.size[1]))
                    wsize = int((float(img.size[0]) * float(wpercent)))
                    img = img.resize((wsize, baseheight), PIL.Image.ANTIALIAS)
                    #img.save(str(fanart), 'JPEG', quality=100)
                    bg = Image.new(color, (wsize, screen_height))
                    bg.paste(img, (0, 0))
                    bg.save(str(fanart), 'JPEG', quality=100)
                elif fit_size == 7:
                    baseheight = screen_height
                    try:
                        img = Image.open(str(picn))
                    except Exception as e:
                        print(e, 'Error in opening image, videoImage, ---13268')
                        picn = os.path.join(home, 'default.jpg')
                        img = Image.open(str(picn))
                    wpercent = (baseheight / float(img.size[1]))
                    wsize = int((float(img.size[0]) * float(wpercent)))
                    img = img.resize((wsize, baseheight), PIL.Image.ANTIALIAS)
                    bg = Image.new(color, (wsize+20, baseheight))
                    offset = (0, 0)
                    bg.paste(img, offset)
                    bg.save(str(fanart), 'JPEG', quality=100)
                elif fit_size == 5 or fit_size == 8:
                    baseheight = screen_height
                    try:
                        img = Image.open(str(picn))
                    except Exception as e:
                        print(e, 'Error in opening image, videoImage, ---13284')
                        picn = os.path.join(home, 'default.jpg')
                        img = Image.open(str(picn))
                    wpercent = (baseheight / float(img.size[1]))
                    wsize = int((float(img.size[0]) * float(wpercent)))
                    sz = (wsize, baseheight)
                    img = img.resize((wsize, baseheight), PIL.Image.ANTIALIAS)
                    bg = Image.new(color, (screen_width, screen_height))
                    if fit_size == 5:
                        offset = (int((screen_width-wsize)/2), int((screen_height-baseheight)/2))
                    else:
                        offset = (int((0)), int((screen_height-baseheight)/2))
                    bg.paste(img, offset)
                    bg.save(str(fanart), 'JPEG', quality=100)
                elif fit_size == 9 or fit_size == 10:
                    baseheight = screen_height - (self.frame1.height()+self.label.height()+100)
                    #baseheight = screen_height - self.label.x()
                    if fit_size == 9:
                        basewidth = screen_width - self.width_allowed - 40
                    else:
                        basewidth = screen_width - 2*self.width_allowed - 40
                    try:
                        img = Image.open(str(picn))
                    except Exception as e:
                        print(e, 'Error in opening image, videoImage, ---13284')
                        picn = os.path.join(home, 'default.jpg')
                        img = Image.open(str(picn))
                    #img = self.round_corner(img, 30)
                    wpercent = (basewidth / float(img.size[0]))
                    hsize = int((float(img.size[1]) * float(wpercent)))
                    bg = Image.new(color, (screen_width, screen_height))
                    #bg = Image.open(os.path.join(home, 'default.jpg'))
                    if hsize < screen_height:
                        sz = (basewidth, hsize)
                        img = img.resize((basewidth, hsize), PIL.Image.ANTIALIAS)
                        offset = (20,20)
                        #new_offset = (20+basewidth, 20)
                        bg.paste(img, offset)
                        #bg.paste(img, new_offset)
                        bg.save(str(fanart), 'JPEG', quality=100)
                    else:
                        wp = float(baseheight/hsize)
                        nbw = int(float(wp)*float(basewidth))
                        img = img.resize((nbw, baseheight), PIL.Image.ANTIALIAS)
                        offset = (20, 20)
                        if fit_size == 9:
                            new_offset = (40+nbw, 20)
                        else:
                            new_offset = (20+nbw, 20)
                        bg.paste(img, offset)
                        bg.paste(img, new_offset)
                        bg.save(str(fanart), 'JPEG', quality=100)
                elif fit_size == 6 or fit_size == 4:
                    if widget and fit_size == 6:
                        if widget == self.label:
                            basewidth = widget.maximumWidth()
                            baseheight = widget.maximumHeight()
                        else:
                            basewidth = widget.width()
                            baseheight = widget.height()
                    elif fit_size == 4:
                        basewidth = screen_width - self.width_allowed
                        baseheight = screen_height
                    else:
                        if widget_size:
                            basewidth = widget_size[0]
                            baseheight = widget_size[1]
                        else:
                            basewidth = self.float_window.width()
                            baseheight = self.float_window.height()
                    bg = Image.new(color, (basewidth, baseheight))
                    try:
                        if os.path.exists(picn) and os.stat(picn).st_size:
                            img = Image.open(str(picn))
                        else:
                            picn = os.path.join(home, 'default.jpg')
                            img = Image.open(str(picn))
                    except Exception as e:
                        print(e, 'Error in opening image, videoImage, ---13321')
                        picn = os.path.join(home, 'default.jpg')
                        img = Image.open(str(picn))
                    wpercent = (basewidth / float(img.size[0]))
                    hsize = int((float(img.size[1]) * float(wpercent)))
                    sz = (basewidth, hsize)
                    if hsize > baseheight:
                        wp = float(baseheight/hsize)
                        nbw = int(float(wp)*float(basewidth))
                        img = img.resize((nbw, baseheight), PIL.Image.ANTIALIAS)
                        offset = (int((basewidth-nbw)/2), 0)
                    else:
                        img = img.resize((basewidth, hsize), PIL.Image.ANTIALIAS)
                        offset = (0, int((baseheight-hsize)/2))
                    bg.paste(img, offset)
                    if widget and fit_size == 6:
                        if widget == self.label:
                            img.save(str(fanart), 'JPEG', quality=100)
                        elif widget == self.float_window:
                            tmp_img = (os.path.join(TMPDIR, 'tmp.jpg'))
                            bg.save(str(tmp_img), 'JPEG', quality=100)
                            return tmp_img
                    elif widget_size:
                        tmp_img = (os.path.join(TMPDIR, 'tmp.jpg'))
                        img.save(str(tmp_img), 'JPEG', quality=100)
                        return tmp_img
                    elif fit_size == 4:
                        bg.save(str(fanart), 'JPEG', quality=100)
                    else:
                        tmp_img = (os.path.join(TMPDIR, 'tmp.jpg'))
                        bg.save(str(tmp_img), 'JPEG', quality=100)
                        return tmp_img
        except Exception as e:
            print(e, ':Error in resizing and changing aspect ratio --13353--')
            
    def change_aspect_only(self, picn):
        global screen_height, screen_width
        basewidth = self.label.maximumWidth()
        baseheight = self.label.maximumHeight()
        #mask = Image.new('L', (100, 100), 0)
        try:
            img = Image.open(str(picn))
        except Exception as e:
            print(e, 'Error in opening image, videoImage, ---13364')
            picn = os.path.join(home, 'default.jpg')
            img = Image.open(str(picn))
        wpercent = (basewidth / float(img.size[0]))
        hsize = int((float(img.size[1]) * float(wpercent)))
        sz = (basewidth, hsize)
        if hsize > baseheight:
            wp = float(baseheight/hsize)
            nbw = int(float(wp)*float(basewidth))
            img = img.resize((nbw, baseheight), PIL.Image.ANTIALIAS)
            bg = Image.new('RGB', (nbw, baseheight))
        else:
            img = img.resize((basewidth, hsize), PIL.Image.ANTIALIAS)
            bg = Image.new('RGB', (basewidth, hsize))
        tmp_img = (os.path.join(TMPDIR, 'new_tmp.jpg'))
        bg.paste(img, (0, 0))
        bg.save(str(tmp_img), 'JPEG', quality=100)
        #img.save(str(tmp_img), 'JPEG', quality=100)
        return tmp_img

    def videoImage(self, picn, thumbnail, fanart, summary):
        global screen_height, screen_width
        if self.image_fit_option_val in range(1, 11):
            if self.image_fit_option_val !=6:
                img_opt = self.image_fit_option_val
            else:
                img_opt = 1
        else:
            img_opt = 2
        logger.info('img_opt={0}'.format(img_opt))
        self.label.clear()
        print(self.label.maximumWidth(), '--max--width--label--')
        try:
            image_dir, image_name = os.path.split(fanart)
            original_fanart = os.path.join(image_dir, 'original-fanart.jpg')
            logger.info('videoimage picn file is {0}'.format(picn))
            if os.path.isfile(str(picn)):
                if not os.path.isfile(fanart):
                    if not os.path.exists(original_fanart):
                        shutil.copy(picn, original_fanart)
                    self.image_fit_option(picn, fanart, fit_size=img_opt)
                if not os.path.isfile(thumbnail):
                    #self.image_fit_option(picn, thumbnail, fit_size=450)
                    self.image_fit_option(picn, thumbnail, fit_size=6, widget=self.label)
                poster = picn
                picn = thumbnail
                if (picn == thumbnail == fanart):
                    pass
                else:
                    QtCore.QTimer.singleShot(100, partial(set_mainwindow_palette, fanart))
                try:
                    if 'poster.jpg' in poster:
                        picn = self.change_aspect_only(poster)
                except Exception as e:
                    print(e, '--10147--')
                    
                logger.info(picn)
                self.label.setPixmap(QtGui.QPixmap(picn, "1"))
                if not self.float_window.isHidden():
                    picn = self.image_fit_option(
                        picn, fanart, fit_size=6, widget=self.float_window
                        )
                    self.float_window.setPixmap(QtGui.QPixmap(picn, "1"))
            else:
                if os.path.exists(self.default_background):
                    dir_n, p = os.path.split(self.default_background)
                    new_jpg =  os.path.join(dir_n, 'default_poster.jpg')
                    if not os.path.exists(new_jpg):
                        picn = self.change_aspect_only(self.default_background)
                        shutil.copy(picn, new_jpg)
                    self.label.setPixmap(QtGui.QPixmap(new_jpg, "1"))
        except Exception as e:
            print(e, '--error--in processing image--VideoImage 13432')
            if os.path.exists(self.default_background):
                QtCore.QTimer.singleShot(10, partial(set_mainwindow_palette, self.default_background))
                dir_n, p = os.path.split(self.default_background)
                new_jpg =  os.path.join(dir_n, 'default_poster.jpg')
                if not os.path.exists(new_jpg):
                    picn = self.change_aspect_only(self.default_background)
                    shutil.copy(picn, new_jpg)
                self.label.setPixmap(QtGui.QPixmap(new_jpg, "1"))

        self.text.clear()

        if summary:
            self.text.insertPlainText((summary))
        else:
            self.text.insertPlainText("No Summary Available")

    def playlistUpdate(self):
        global home
        row = self.list2.currentRow()
        item = self.list2.item(row)
        if item:
            i = str(self.list2.item(row).text())
            if not i.startswith(self.check_symbol):
                self.list2.item(row).setText(self.check_symbol+i)
                self.epn_arr_list[row] = '#'+self.epn_arr_list[row]
            else:
                self.list2.item(row).setText(i)
            self.list2.setCurrentRow(row)
            if self.list1.currentItem():
                file_path = os.path.join(home, 'Playlists', self.list1.currentItem().text())
                write_files(file_path, self.epn_arr_list, line_by_line=True)

    def get_file_name(self, row, list_widget):
        global name, site
        file_name_mkv = ''
        file_name_mp4 = ''
        if list_widget.item(row):
            new_epn = list_widget.item(row).text().replace('#', '', 1)
        else:
            new_epn = ''
        if new_epn.startswith(self.check_symbol):
            new_epn = new_epn[1:]
        new_epn = new_epn.replace('/', '-')
        new_epn = new_epn.replace('"', '')
        new_epn = re.sub('"|.mkv|.mp4', '', new_epn)
        if new_epn.startswith('.'):
            new_epn = new_epn[1:]
        opt_val = self.btn1.currentText().lower()
        if OSNAME == 'nt':
            if '?' in new_epn:
                new_epn = new_epn.replace('?', '_')
        try:
            if (site.lower() == 'playlists' or (site.lower() == 'music' 
                    and self.list3.currentItem().text().lower() == 'playlist')):
                try:
                    title = self.list1.currentItem().text()
                except:
                    title = name
            else:
                title = name
        except:
            title = self.epn_arr_list[row].split('	')[0]
            file_name_mkv = self.epn_arr_list[row].split('	')[1]
            file_name_mp4 = self.epn_arr_list[row].split('	')[1]
            logger.info('--14986--function_get_file_name={0}-{1}'.format(file_name_mkv, file_name_mp4))
            return file_name_mp4, file_name_mkv

        if (site.lower() != 'video' and site.lower() != 'music' 
                and site.lower() != 'local' and site.lower() != 'playlists' 
                and site.lower() != 'none'):
            new_epn_mkv = new_epn+'.mkv'
            new_epn_mp4 = new_epn+'.mp4'
            file_name_mkv = os.path.join(self.default_download_location, title, new_epn_mkv)
            file_name_mp4 = os.path.join(self.default_download_location, title, new_epn_mp4)
        elif (site.lower() == 'playlists' or opt_val == 'youtube' 
                or (site.lower() == 'music' 
                and self.list3.currentItem().text().lower() == 'playlist')):
            if list_widget == self.list2:
                st = self.epn_arr_list[row].split('	')[1]
            elif list_widget == self.list6:
                st = self.queue_url_list[row].split('	')[1]
            st = st.replace('"', '')
            if st.startswith('http'):
                new_epn_mkv = new_epn+'.mp4'
                new_epn_mp4 = new_epn+'.mp4'
                file_name_mkv = os.path.join(self.default_download_location, title, new_epn_mkv)
                file_name_mp4 = os.path.join(self.default_download_location, title, new_epn_mp4)
            else:
                new_epn_mkv = os.path.basename(st)
                new_epn_mp4 = new_epn_mkv
                file_name_mkv = st
                file_name_mp4 = st
        elif (site.lower() == 'video' or site.lower() == 'music' 
                or site.lower() == 'local' or site.lower() == 'none'):
            if not self.queue_url_list:
                print(row)
                file_name_mkv = self.epn_arr_list[row].split('	')[1]
                file_name_mp4 = self.epn_arr_list[row].split('	')[1]
            else:
                queue_split = []
                if row < len(self.queue_url_list):
                    queue_split = self.queue_url_list[row].split('	')
                if len(queue_split) > 1:
                    file_name_mkv = queue_split[1]
                    file_name_mp4 = queue_split[1]
                
        logger.info('function---15025--{0}-{1}'.format(file_name_mkv, file_name_mp4))
        return file_name_mp4, file_name_mkv

    def play_file_now(self, file_name, win_id=None):
        global Player, epn_name_in_list, idw, quitReally
        global current_playing_file_path, cur_label_num
            
        self.mplayerLength = 0
        quitReally = 'no'
        logger.info(file_name)
        if self.mpvplayer_val.processId() == 0:
            self.initial_view_mode()
        finalUrl = file_name.replace('"', '')
        finalUrl = '"'+finalUrl+'"'
        if finalUrl.startswith('"http'):
            current_playing_file_path = finalUrl.replace('"', '')
            finalUrl = finalUrl.replace('"', '')
        else:
            current_playing_file_path = finalUrl
        if (self.mpvplayer_val.processId() > 0 and OSNAME == 'posix' 
                and self.mpvplayer_started and not finalUrl.startswith('http')):
            epnShow = '"' + "Queued:  "+ self.epn_name_in_list + '"'
            if Player == "mplayer":
                t1 = bytes('\n '+'show_text '+epnShow+' \n', 'utf-8')
                t2 = bytes('\n '+"loadfile "+finalUrl+" replace "+'\n', 'utf-8')
            elif Player == 'mpv':
                t1 = bytes('\n '+'show-text '+epnShow+' \n', 'utf-8')
                t2 = bytes('\n '+"loadfile "+finalUrl+' replace \n', 'utf-8')
            logger.info('{0}---hello-----'.format(t2))
            self.mpvplayer_val.write(t1)
            self.mpvplayer_val.write(t2)
            if self.mplayer_SubTimer.isActive():
                self.mplayer_SubTimer.stop()
            self.mplayer_SubTimer.start(2000)
            logger.info('..function play_file_now gapless mode::::{0}'.format(finalUrl))
        else:
            if self.mpvplayer_val.processId()>0:
                self.mpvplayer_val.kill()
                self.mpvplayer_started = False
            if OSNAME == 'posix':
                if not win_id:
                    idw = str(int(self.tab_5.winId()))
                else:
                    idw = str(win_id)
            elif OSNAME == 'nt':
                if win_id:
                    idw = str(win_id)
                elif thumbnail_indicator and self.video_mode_index != 1:
                    try:
                        p1 = 'self.label_epn_{0}.winId()'.format(str(cur_label_num))
                        idw = str(int(eval(p1)))
                    except Exception as e:
                        print(e)
                        idw = str(int(self.tab_5.winId()))
                else:
                    idw = str(int(self.tab_5.winId()))
            command = self.mplayermpv_command(idw, finalUrl, Player)
            logger.info('command: function_play_file_now = {0}'.format(command))
            self.infoPlay(command)
        if not self.external_SubTimer.isActive():
            self.external_SubTimer.start(3000)

    def is_artist_exists(self, row):
        try:
            arr = self.epn_arr_list[row].split('	')
        except:
            return False
        audio_file = True
        artist = ''
        if len(arr) >=3 :
            artist = arr[2].replace('"', '')
            if '.' in arr[1]:
                ext = arr[1].rsplit('.', 1)[1]
                ext = ext.replace('"', '')
                if ext != 'mp3' and ext != 'flac':
                    audio_file = False
        if artist.lower() and (artist.lower() != 'none') and not artist.startswith('http') and audio_file:
            return True
        else:
            return False

    def if_file_path_exists_then_play(self, row, list_widget, play_now=None):
        global site, wget, video_local_stream, artist_name_mplayer
        
        file_path_name_mp4, file_path_name_mkv = self.get_file_name(row, list_widget)
        
        if ((os.path.exists(file_path_name_mp4) or os.path.exists(file_path_name_mkv)) 
                and (site.lower() != 'video' and site.lower() != 'music' 
                and site.lower() != 'local') and not video_local_stream):
            logger.info('now--playing: {0}-{1}'.format(file_path_name_mp4, file_path_name_mkv))
            if play_now:
                self.epn_name_in_list = list_widget.item(row).text().replace('#', '', 1)
                if self.epn_name_in_list.startswith(self.check_symbol):
                    self.epn_name_in_list = self.epn_name_in_list[1:]
                if os.path.exists(file_path_name_mp4):
                    self.play_file_now(file_path_name_mp4)
                    finalUrl = file_path_name_mp4
                else:
                    self.play_file_now(file_path_name_mkv)
                    finalUrl = file_path_name_mkv
                finalUrl = '"'+finalUrl+'"'
                if (site.lower() == 'playlists'):
                    if self.is_artist_exists(row):
                        self.musicBackground(row, 'get now')
                        self.media_data.update_music_count('count', finalUrl)
                    else:
                        try:
                            thumb_path = self.get_thumbnail_image_path(row, self.epn_arr_list[row])
                            logger.info("thumbnail path = {0}".format(thumb_path))
                            if os.path.exists(thumb_path):
                                self.videoImage(thumb_path, thumb_path, thumb_path, '')
                        except Exception as e:
                            logger.info('Error in getting Thumbnail: {0}'.format(e))
                else:
                    self.mark_addons_history_list('mark', row)
                return True
            else:
                if os.path.exists(file_path_name_mp4):
                    return file_path_name_mp4
                else:
                    return file_path_name_mkv
        elif (site.lower() == 'music' and self.list3.currentItem() 
                and (os.path.exists(file_path_name_mp4) 
                or os.path.exists(file_path_name_mkv)) and not video_local_stream):
            if self.list3.currentItem().text().lower() == 'playlist':
                logger.info('now--playing: {0}-{1}'.format(file_path_name_mp4, file_path_name_mkv))
                if play_now:
                    self.epn_name_in_list = list_widget.item(row).text().replace('#', '', 1)
                    if self.epn_name_in_list.startswith(self.check_symbol):
                        self.epn_name_in_list = self.epn_name_in_list[1:]
                    if os.path.exists(file_path_name_mp4):
                        self.play_file_now(file_path_name_mp4)
                        finalUrl = file_path_name_mp4
                    else:
                        self.play_file_now(file_path_name_mkv)
                        finalUrl = file_path_name_mkv
                    if list_widget == self.list6:
                        txt = self.list6.item(0).text()
                        r = self.get_index_list(list_widget, txt)
                        if r is None:
                            r = 0
                        else:
                            list_widget_row = r
                        self.list2.setCurrentRow(r)
                    else:
                        r = row
                    finalUrl = '"'+finalUrl+'"'
                    self.musicBackground(r, 'Search')
                    print(r, '--search--musicbackground--')
                    self.media_data.update_music_count('count', finalUrl)
                    return True
                else:
                    if os.path.exists(file_path_name_mp4):
                        return file_path_name_mp4
                    else:
                        return file_path_name_mkv
        elif ((os.path.exists(file_path_name_mp4) or os.path.exists(file_path_name_mkv)) 
                and (site.lower() == 'video' or site.lower() == 'music' 
                or site.lower() == 'local' or site.lower() == 'none') 
                and not video_local_stream):
            logger.info('now--playing: {0}-{1}'.format(file_path_name_mp4, file_path_name_mkv))
            if play_now:
                if list_widget.item(row):
                    self.epn_name_in_list = list_widget.item(row).text().replace('#', '', 1)
                    
                if self.epn_name_in_list.startswith(self.check_symbol):
                    self.epn_name_in_list = self.epn_name_in_list[1:]
                if os.path.exists(file_path_name_mp4):
                    self.play_file_now(file_path_name_mp4)
                    finalUrl = file_path_name_mp4
                else:
                    self.play_file_now(file_path_name_mkv)
                    finalUrl = file_path_name_mkv
                list_widget_row = None
                if list_widget == self.list6:
                    txt = self.list6.item(0).text()
                    r = self.get_index_list(list_widget, txt)
                    if r is None:
                        r = 0
                    else:
                        list_widget_row = r
                    self.list2.setCurrentRow(r)
                    logger.info('\n row = {0} txt= {1}\n'.format(r,txt))
                else:
                    r = row
                    
                if list_widget_row is not None:
                    row = list_widget_row
                
                finalUrl = finalUrl.replace('"', '')
                finalUrl = '"'+finalUrl+'"'
                if site.lower() == "music":
                    logger.info(finalUrl)
                    try:
                        artist_name_mplayer = self.epn_arr_list[row].split('	')[2]
                        if artist_name_mplayer.lower() == "none":
                            artist_name_mplayer = ""
                    except:
                        artist_name_mplayer = ""
                    if not 'youtube.com' in finalUrl.lower():
                        self.musicBackground(r, 'Search')
                        self.media_data.update_music_count('count', finalUrl)
                elif site.lower() == "video":
                    self.mark_video_list('mark', row)
                    self.media_data.update_video_count('mark', finalUrl, rownum=row)
                elif site.lower() == 'local':
                    self.mark_addons_history_list('mark', row)
                    
                if site.lower() == 'video' or site.lower() == 'local':
                    try:
                        thumb_path = self.get_thumbnail_image_path(row, self.epn_arr_list[row])
                        logger.info("thumbnail path = {0}".format(thumb_path))
                        if os.path.exists(thumb_path):
                            self.videoImage(thumb_path, thumb_path, thumb_path, '')
                    except Exception as e:
                        logger.info('Error in getting Thumbnail - localvideogetinlist: {0}'.format(e))
                    
                return True
            else:
                if os.path.exists(file_path_name_mp4):
                    return file_path_name_mp4
                else:
                    return file_path_name_mkv
        elif wget.processId() > 0 and play_now:
            return True
        else:
            return False

    def get_index_list(self, list_widget, txt):
        r = None
        txt = txt.replace('#', '', 1)
        if txt.startswith(self.check_symbol):
                txt = txt[1:]
        for i,val in enumerate(self.epn_arr_list):
            if '\t' in val:
                new_txt = val.split('\t')[0]
            else:
                new_txt = val
            if new_txt.startswith('#'):
                new_txt = new_txt[1:]
            if new_txt.lower() == txt.lower():
                r = i
            #logger.info('\ntxt={0}: new_txt={1}\n: 11116'.format(txt, new_txt))
        return r

    def set_init_settings(self):
        global music_arr_setting, default_arr_setting
        if site == "Music":
            if self.list3.currentRow() >= 0:
                music_arr_setting[0]=self.list3.currentRow()
                if self.list1.currentRow() >= 0:
                    music_arr_setting[1]=self.list1.currentRow()
                    if self.list2.currentRow() >= 0:
                        music_arr_setting[2]=self.list2.currentRow()
        else:
            if self.btn1.currentIndex() > 0:
                default_arr_setting[0]=self.btn1.currentIndex()
                if self.list3.currentRow() >= 0:
                    default_arr_setting[1]=self.list3.currentRow()
                    if self.list1.currentRow() >= 0:
                        default_arr_setting[2]=self.list1.currentRow()
                        if self.list2.currentRow() >= 0:
                            default_arr_setting[3]=self.list2.currentRow()
                if self.btnAddon.currentIndex() >= 0:
                    default_arr_setting[4]=self.btnAddon.currentIndex()

    def if_path_is_rel(self, path, thumbnail=None):
        global my_ipaddress
        nm = ''
        if path.startswith('abs_path='):
            path = path.split('abs_path=', 1)[1]
            nm = path
            nm = str(base64.b64decode(nm).decode('utf-8'))
            logger.info(nm)
            num_row = None
            if nm.startswith('http'):
                http_val = 'http'
                if ui.https_media_server:
                    http_val = "https" 
                n_url = http_val+'://'+str(self.local_ip_stream)+':'+str(self.local_port_stream)
                logger.info('abs_path_playing={0}'.format(n_url))
                if nm.startswith(n_url):
                    try:
                        num_row = self.path.rsplit('/', 1)[-1]
                        if num_row == 'server' or num_row == 'now_playing':
                            row = curR
                        else:
                            row = int(num_row)
                    except Exception as err_val:
                        print(err_val, '--1112--')
                        row = 0
                    if row < 0:
                        row = 0
                    nm = self.epn_return(row)
                    if nm.startswith('"'):
                        nm = nm.replace('"', '')
                elif 'youtube.com' in nm and not thumbnail:
                    nm = get_yt_url(nm, ui.quality_val, ui.ytdl_path, logger, mode='offline').strip()
        elif path.startswith('relative_path='):
            path = path.split('relative_path=', 1)[1]
            nm = path
            nm = str(base64.b64decode(nm).decode('utf-8'))
            logger.info('------------------{0}'.format(nm))
            nm_arr = nm.split('&')
            if len(nm_arr) > 7:
                new_tmp_arr = nm_arr[3:]
                row_index = -1
                local_stream_index = -1
                for i, j in enumerate(new_tmp_arr):
                    if j.isnumeric():
                        row = int(j)
                        row_index = i
                    if j.lower() == 'true' or j.lower() == 'false':
                        local_stream = j
                        local_stream_index = i
            else:
                local_stream = nm_arr[4]
            if local_stream == 'True':
                old_nm = nm
                new_torrent_signal = DoGetSignalNew()
                if ui.https_media_server:
                    https_val = 'https'
                else:
                    https_val = 'http'
                nm = https_val+"://"+str(self.local_ip)+':'+str(self.local_port)+'/'
                new_torrent_signal.new_signal.emit(old_nm)
                logger.info('--nm---{0}'.format(nm))
            else:
                nm = self.getdb.epn_return_from_bookmark(nm, from_client=True)
        return nm

    def epnfound(self):
        global site, base_url, embed, epn, epn_goto, mirrorNo, list2_items, quality
        global finalUrl, home, hdr, path_Local_Dir, epn_name_in_list
        global siteName, finalUrlFound, refererNeeded, show_hide_player
        global show_hide_cover
        global mpv, mpvAlive, indexQueue, Player, startPlayer
        global new_epn, idw, home1, quitReally, buffering_mplayer
        global opt_movies_indicator
        global name, artist_name_mplayer, rfr_url, server
        global current_playing_file_path
        global music_arr_setting, default_arr_setting, local_torrent_file_path
        global video_local_stream

        buffering_mplayer="no"
        self.list4.hide()
        self.player_play_pause.setText(self.player_buttons['pause'])
        quitReally = "no"

        try:
            server._emitMeta("Play", site, self.epn_arr_list)
        except:
            pass

        if video_local_stream:
            tmp_pl = os.path.join(TMPDIR, 'player_stop.txt')
            if os.path.exists(tmp_pl):
                os.remove(tmp_pl)

        if (self.mpvplayer_val.processId() > 0 and (current_playing_file_path.startswith('http') 
                or current_playing_file_path.startswith('"http'))):
            self.mpvplayer_val.kill()
            self.mpvplayer_started = False

        if epn_goto == 0 and site != "PlayLists" and self.download_video == 0:
            if self.list2.currentItem():
                epn = (self.list2.currentItem().text())
            else:
                return 0
            self.epn_name_in_list = epn
            if not epn:
                return 0

            row = self.list2.currentRow()

            if '	' in self.epn_arr_list[row]:
                epn = (self.epn_arr_list[row]).split('	')[1]
            else:
                epn = self.epn_arr_list[row].replace('#', '', 1)
            epn = epn.replace('#', '', 1)
            if epn.startswith(self.check_symbol):
                epn = epn[1:]

        self.set_init_settings()

        row = self.list2.currentRow()
        if self.if_file_path_exists_then_play(row, self.list2, True):
            self.initial_view_mode()
            return 0

        if(site != "SubbedAnime" and site!= "DubbedAnime" and site!="PlayLists" 
                and finalUrlFound == False and site !="None" and site!= "Music" 
                and site != "Video" and site!= "Local"):
            hist_path = os.path.join(home, 'History', site, name, 'Ep.txt')
            logger.info('hist_path={0}'.format(hist_path))
            if ((os.path.exists(hist_path) and (epn_goto == 0)) 
                        or (os.path.exists(hist_path) and bookmark)):
                    if self.epn_arr_list[row].startswith('#'):
                        n_epn = self.epn_arr_list[row]
                        txt = n_epn.replace('#', self.check_symbol, 1)
                    else:
                        n_epn = '#'+self.epn_arr_list[row]
                        file_path = hist_path
                        lines = open_files(file_path, True)
                        if "\n" in lines[row]:
                            lines[row] = n_epn + "\n"
                        else:
                            lines[row] = n_epn
                        
                        write_files(file_path, lines, line_by_line=True)
                        txt = self.check_symbol + self.epn_arr_list[row]
                    txt = txt.replace('_', ' ', 1)
                    if '	' in txt:
                        txt = txt.split('	')[0]
                    self.list2.item(row).setText(txt)

            else:
                i = str(self.list2.item(row).text())
                i = i.replace('_', ' ')
                if not i.startswith(self.check_symbol):
                    self.list2.item(row).setText(self.check_symbol+i)
                else:
                    self.list2.item(row).setText(i)
                #self.list2.item(row).setFont(QtGui.QFont('SansSerif', 10, italic=True))
                self.list2.setCurrentRow(row)

            if site != "Local":
                try:
                    self.progressEpn.setFormat('Wait..')
                    if video_local_stream:
                        if self.thread_server.isRunning():
                            if self.do_get_thread.isRunning():
                                row_file = os.path.join(TMPDIR, 'row.txt')
                                f = open(row_file, 'w')
                                f.write(str(row))
                                f.close()
                                if self.https_media_server:
                                    https_val = 'https'
                                else:
                                    https_val = 'http'
                                finalUrl = https_val+"://"+self.local_ip+':'+str(self.local_port)+'/'
                            else:
                                finalUrl, self.do_get_thread, self.stream_session, self.torrent_handle = self.start_torrent_stream(name, row, self.local_ip+':'+str(self.local_port), 'Next', self.torrent_download_folder, self.stream_session)
                        else:
                            finalUrl, self.thread_server, self.do_get_thread, self.stream_session, self.torrent_handle = self.start_torrent_stream(name, row, self.local_ip+':'+str(self.local_port), 'First Run', self.torrent_download_folder, self.stream_session)
                            
                        self.torrent_handle.set_upload_limit(self.torrent_upload_limit)
                        self.torrent_handle.set_download_limit(self.torrent_download_limit)
                    else:
                        finalUrl = self.site_var.getFinalUrl(name, epn, mirrorNo, quality)
                except Exception as e:
                    print(e)
                    self.progressEpn.setFormat('Load Failed!')
                    return 0
        elif site == "PlayLists":
            row = self.list2.currentRow()
            item = self.list2.item(row)
            if item:
                arr = self.epn_arr_list[row].split('	')
                if len(arr) >= 2:
                    path_rel = arr[1]
                    if path_rel.startswith('abs_path=') or path_rel.startswith('relative_path='):
                        arr[1] = self.if_path_is_rel(path_rel)
                if len(arr) > 2:
                    if arr[2].startswith('http') or arr[2].startswith('"http'):
                        finalUrl = []
                        finalUrl.append(arr[1])
                        finalUrl.append(arr[2])
                        refererNeeded = True
                    else:
                        finalUrl = arr[1]
                        refererNeeded = False
                else:
                    finalUrl = arr[1]
                    refererNeeded = False
                self.epn_name_in_list = arr[0]
                epn = self.epn_name_in_list
                self.playlistUpdate()
                if 'youtube.com' in finalUrl:
                    finalUrl = get_yt_url(finalUrl, quality, self.ytdl_path, logger).strip()
                #if is_artist_exists(row):
        elif finalUrlFound == True:
                row_num = self.list2.currentRow()
            
                final = self.epn_arr_list[row_num]
                logger.info(final)
                self.mark_History()
                finalUrl = []
                final = final.replace('#', '', 1)
                
                if '	' in final:
                    final = final.split('	')[1]
                    
                finalUrl.append(final)
                if refererNeeded == True:
                    if '	' in self.epn_arr_list[row_num]:
                        rfr_url = self.epn_arr_list[row_num].split('	')[2]
                    finalUrl.append(rfr_url)
                if len(finalUrl) == 1:
                    finalUrl = finalUrl[0]
                logger.info(finalUrl)
                print("++++++++++++++++++++")
        elif site == "SubbedAnime" or site == "DubbedAnime":
            if category != "Movies":
                file_path = os.path.join(home, 'History', site, siteName, name, 'Ep.txt')
        
                if os.path.exists(file_path) and (epn_goto == 0):
                    if '#' in self.epn_arr_list[row]:
                        n_epn = self.epn_arr_list[row]
                        txt = n_epn.replace('#', self.check_symbol, 1)
                    else:
                        n_epn = "#" + self.epn_arr_list[row]
                        lines = open_files(file_path, True)
                        if "\n" in lines[row]:
                            lines[row] = n_epn + "\n"
                        else:
                            lines[row] = n_epn
                            
                        write_files(file_path, lines, line_by_line=True)
                        txt = self.check_symbol + self.epn_arr_list[row]
                    if '	' in txt:
                        txt = txt.split('	')[0]
                    txt = txt.replace('_', ' ', 1)
                    self.list2.item(row).setText(txt)
                    
            if site == "SubbedAnime":
                code = 6
                if base_url == 16:
                    epn_t = epn.split(' ')[1]
                    new_epn = epn.split(' ')[0]
                else:
                    epn_t = epn
                if opt_movies_indicator:
                    r = self.list2.currentRow()
                    self.epn_name_in_list = self.list2.currentItem().text()
                    if cmd:
                        self.progressEpn.setFormat('Wait..')
                        QtWidgets.QApplication.processEvents()
                        try:
                            finalUrl = self.site_var.urlResolve(self.epn_arr_list[r].split('	')[1])
                        except Exception as e:
                            print(e)
                            return 0
                else:
                    if self.site_var:
                        self.progressEpn.setFormat('Wait..')
                        QtWidgets.QApplication.processEvents()
                        try:
                            finalUrl = self.site_var.getFinalUrl(
                                siteName, name, epn, mirrorNo, category, quality) 
                        except Exception as e:
                            print(e)
                            return 0
                if category == "Movies" and not opt_movies_indicator and (type(finalUrl) is list):
                    self.list2.clear()
                    self.epn_arr_list[:]=[]
                    j = 1
                    for i in finalUrl:
                        self.epn_arr_list.append("Part-"+str(j)+'	'+i)
                        self.list2.addItem("Part-"+str(j))
                        j = j+1
                    opt_movies_indicator.append("Movies")
                    self.list2.setCurrentRow(0)
                    self.list2.setFocus()
                    
                    if self.site_var:
                        self.progressEpn.setFormat('Wait..')
                        QtWidgets.QApplication.processEvents()
                        try:
                            finalUrl = self.site_var.urlResolve(self.epn_arr_list[0].split('	')[1])
                        except Exception as e:
                            print(e)
                            return 0
                    self.epn_name_in_list = name+"-"+self.list2.currentItem().text()
            elif site == "DubbedAnime":
                code = 5
                if self.site_var:
                    self.progressEpn.setFormat('Wait..')
                    QtWidgets.QApplication.processEvents()
                    try:
                        finalUrl = self.site_var.getFinalUrl(
                            siteName, name, epn, mirrorNo, quality) 
                    except Exception as e:
                        print(e)
                        return 0
        elif site == "None" or site == "Music" or site == "Video" or site == "Local":
            if site == "Local" and opt == "History":
                self.mark_History()
            if '	' in self.epn_arr_list[row]:
                    finalUrl = '"'+(self.epn_arr_list[row]).split('	')[1]+'"'
            else:
                    finalUrl = '"'+(self.epn_arr_list[row]).replace('#', '', 1)+'"'
            if self.list3.currentItem():
                if site.lower() == 'music' and self.list3.currentItem().text().lower() == 'playlist':
                    path_rel = finalUrl.replace('"', '')
                    if path_rel.startswith('abs_path=') or path_rel.startswith('relative_path='):
                        finalUrl = '"'+self.if_path_is_rel(path_rel)+'"'
            logger.info(finalUrl)
            i = str(self.list2.item(row).text())
            i = i.replace('_', ' ')
            if not i.startswith(self.check_symbol):
                self.list2.item(row).setText(self.check_symbol+i)
            else:
                self.list2.item(row).setText(i)
            #self.list2.item(row).setFont(QtGui.QFont('SansSerif', 10, italic=True))
            self.list2.setCurrentRow(row)
            
            if site == 'None' and video_local_stream:
                    finalUrl = self.local_torrent_open(local_torrent_file_path)
            elif site == 'None' and self.btn1.currentText().lower() == 'youtube':
                    finalUrl = finalUrl.replace('"', '')
                    finalUrl = get_yt_url(finalUrl, quality, self.ytdl_path, logger).strip()
                    finalUrl = '"'+finalUrl+'"'
            if 'youtube.com' in finalUrl.lower():
                finalUrl = finalUrl.replace('"', '')
                finalUrl = get_yt_url(finalUrl, quality, self.ytdl_path, logger).strip()
                finalUrl = '"'+finalUrl+'"'
                
        new_epn = self.epn_name_in_list
        
        idw = str(int(self.tab_5.winId()))
        print(self.tab_5.winId(), '----winID---', idw)
        if site != "Music":
            self.tab_5.show()
            
        logger.info(finalUrl)
        print("***********")
        if (site == "Local" or site == "Video" or site == "Music" or site == "None" 
                or site == "PlayLists" and (not type(finalUrl) is list 
                or (type(finalUrl) is list and len(finalUrl) == 1)) 
                and self.download_video == 0):
            if type(finalUrl) is list:
                finalUrl = finalUrl[0]
                
            finalUrl = finalUrl.replace('"', '')
            
            finalUrl = '"'+finalUrl+'"'
            try:
                finalUrl = str(finalUrl)
            except:
                finalUrl = finalUrl
            if self.mpvplayer_val.processId() > 0:
                self.mpvplayer_val.kill()
                self.mpvplayer_started = False
            if Player == "mpv":
                command = self.mplayermpv_command(idw, finalUrl, Player)
                logger.info(command)
                self.infoPlay(command)
            elif Player == "mplayer":
                quitReally = "no"
                
                idw = str(int(self.tab_5.winId()))
                if site != "Music":
                    self.tab_5.show()
                command = self.mplayermpv_command(idw, finalUrl, Player)
                logger.info(command)
                self.infoPlay(command)
            else:
                finalUrl = finalUrl.replace('"', '')
                subprocess.Popen([Player, finalUrl], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        else:
            if self.download_video == 0 and Player == "mpv":
                if self.mpvplayer_val.processId() > 0:
                    self.mpvplayer_val.kill()
                    self.mpvplayer_started = False
                if isinstance(finalUrl, list):
                    rfr_exists = finalUrl[-1]
                    rfr_needed = False
                    if rfr_exists == 'referer sent':
                        rfr_needed = True
                        finalUrl.pop()
                    if finalUrlFound == True or refererNeeded == True or site=="PlayLists" or rfr_needed:
                        if refererNeeded == True or rfr_needed:
                            rfr_url = finalUrl[1]
                            nepn = '"'+str(finalUrl[0])+'"'
                            command = self.mplayermpv_command(idw, nepn, Player, rfr=rfr_url)
                        else:
                            nepn = str(finalUrl[0])
                            command = self.mplayermpv_command(idw, nepn, Player)
                        logger.info(command)
                    
                    else:
                    
                        self.queue_url_list[:]=[]
                        epnShow = finalUrl[0]
                        for i in range(len(finalUrl)-1):
                            self.queue_url_list.append(finalUrl[i+1])
                        self.queue_url_list.reverse()
                        command = self.mplayermpv_command(idw, epnShow, Player)
                    self.infoPlay(command)
                else:
                    if '""' in finalUrl:
                        finalUrl = finalUrl.replace('""', '"')
                    try:
                        finalUrl = str(finalUrl)
                    except:
                        finalUrl = finalUrl
                    command = self.mplayermpv_command(idw, finalUrl, Player)
                    self.infoPlay(command)
            elif self.download_video == 0 and Player != "mpv":
                if self.mpvplayer_val.processId() > 0:
                    self.mpvplayer_val.kill()
                    self.mpvplayer_started = False
                if isinstance(finalUrl, list):
                    rfr_exists = finalUrl[-1]
                    rfr_needed = False
                    if rfr_exists == 'referer sent':
                        rfr_needed = True
                        finalUrl.pop()
                    if finalUrlFound == True or site=="PlayLists" or rfr_needed:
                        if refererNeeded == True or rfr_needed:
                            rfr_url = finalUrl[1]
                            if Player == "mplayer":
                                quitReally = "no"
                                idw = str(int(self.tab_5.winId()))
                                self.tab_5.show()
                                final_url = str(finalUrl[0])
                                command = self.mplayermpv_command(idw, final_url, Player, rfr=rfr_url)
                                logger.info(command)
                                self.infoPlay(command)
                            else:
                                subprocess.Popen([Player, "-referrer", rfr_url, finalUrl[0]])
                        else:
                            if Player == "mplayer":
                                quitReally = "no"
                                idw = str(int(self.tab_5.winId()))
                                self.tab_5.show()
                                final_url = str(finalUrl[0])
                                command = self.mplayermpv_command(idw, final_url, Player)
                                logger.info(command)
                                self.infoPlay(command)
                            else:
                                final_url = str(finalUrl[0])
                                subprocess.Popen([Player, final_url])
                    else:
                        epnShow = finalUrl[0]
                        for i in range(len(finalUrl)-1):
                            self.queue_url_list.append(finalUrl[i+1])
                        self.queue_url_list.reverse()
                        command = self.mplayermpv_command(idw, epnShow, Player)
                        logger.info(command)
                        self.infoPlay(command)
                else:
                    print(Player)
                    logger.info("15712:Final Url mplayer = {0}".format(finalUrl))
                    if '""' in finalUrl:
                        finalUrl = finalUrl.replace('""', '"')
                    finalUrl = str(finalUrl)
                    if Player == "mplayer":
                        quitReally = "no"
                        idw = str(int(self.tab_5.winId()))
                        self.tab_5.show()
                        command = self.mplayermpv_command(idw, finalUrl, Player)
                        logger.info(command)
                        self.infoPlay(command)
                    else:
                        finalUrl = re.sub('"', "", finalUrl)
                        subprocess.Popen([Player, finalUrl], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
            elif self.download_video == 1 and refererNeeded == False:
                if type(finalUrl) is list:
                    j = 0
                    length = len(finalUrl)
                    for i in finalUrl:
                        if length == 1:
                            nepn1 = new_epn
                        else:
                            nepn1 = new_epn + "-Part-" + str(j+1)
                        subprocess.Popen(["uget-gtk", "--quiet=yes",
                            "--http-user-agent="+hdr, finalUrl[j],
                            "--filename="+nepn1+".mp4"])
                        j = j+1
                else:
                    finalUrl = finalUrl.replace('"', '')
                    self.list2.setFocus()
                    r = self.list2.currentRow()
                    print(r)
                    new_epn = self.list2.item(row).text()
                    if new_epn.startswith(self.check_symbol):
                        new_epn = new_epn.replace(self.check_symbol, '', 1)
                    new_epn = new_epn.replace('/', '-')
                    new_epn = new_epn.replace('"', '')
                    if new_epn.startswith('.'):
                        new_epn = new_epn[1:]
                    if finalUrl.endswith('.mkv'):
                        new_epn = new_epn+'.mkv'
                    else:
                        new_epn = new_epn+'.mp4'
                    if site.lower() == 'playlists':
                        title = self.list1.currentItem().text()
                    else:
                        title = name
                    folder_name = os.path.join(self.default_download_location, title)
                    if not os.path.exists(folder_name):
                        os.makedirs(folder_name)
                    npn = os.path.join(folder_name, new_epn)
                    
                    if finalUrl.startswith('http'):
                        command = wget_string(finalUrl, npn, self.get_fetch_library)
                        logger.info(command)
                        self.infoWget(command, 0)
                self.download_video = 0
            elif refererNeeded == True and self.download_video == 1:
                rfr = finalUrl[1]
                logger.info(rfr)
                url1 = re.sub('#', '', finalUrl[0])
                logger.info(url1)
                url1 = str(url1)
                command = wget_string(
                    url1, os.path.join(TMPDIR, new_epn), self.get_fetch_library, rfr)
                logger.info(command)
                self.infoWget(command, 0)
                self.download_video = 0
                
        if epn_goto == 0:
            self.list2.setCurrentRow(row)
        epn_goto = 0
        
        if not isinstance(finalUrl, list):
            self.final_playing_url = finalUrl.replace('"', '')
            if self.final_playing_url.startswith('http'):
                current_playing_file_path = self.final_playing_url
            else:
                current_playing_file_path = '"'+self.final_playing_url+'"'
        else:
            self.final_playing_url = finalUrl[0].replace('"', '')
            if refererNeeded == True:
                rfr_url = finalUrl[1].replace('"', '')
                
        if self.download_video == 0:
            self.initial_view_mode()
        self.epn_name_in_list = self.epn_name_in_list.replace('#', '', 1)
        
        self.paste_background(row)


    def start_torrent_stream(
            self, name_file, epn_index, local_ip, status, path_folder, session, 
            site_name=None, from_client=None):
        global site, home
        torrent_thread = None
        index = int(epn_index)
        ip_n = local_ip.rsplit(':', 1)
        ip = ip_n[0]
        port = int(ip_n[1])
        path = path_folder
        if site_name:
            site_name_val = site_name
        else:
            if from_client:
                site_name_val = 'Torrent'
            else:
                site_name_val = site
        site_home = os.path.join(home, 'History', site_name_val)
        torrent_dest = os.path.join(site_home, name_file+'.torrent')
        logger.info('torrent_dest={0} ; index={1}; path={2}'.format(torrent_dest, index, path))
        if self.https_media_server:
            https_val = 'https'
        else:
            https_val = 'http'
        url = https_val+'://'+ip+':'+str(port)+'/'
        print(url, '-local-ip-url', status)
        
        if status.lower() == 'get next':
            self.torrent_handle = set_new_torrent_file_limit(
                torrent_dest, index, path, self.stream_session, self.list6, 
                self.progress, TMPDIR, self.media_server_key, self.client_auth_arr)
        else:
            print('--line--15410--', self.thread_server.isRunning(), '=thread_server')
            if status.lower() =='first run' and not self.thread_server.isRunning():
                thread_server = ThreadServer(
                    ip, port, self.media_server_key, self.client_auth_arr, 
                    self.https_media_server, self.https_cert_file, ui)
                thread_server.start()
            print('--line--15415--', self.thread_server.isRunning(), '=thread_server')
            handle, ses, info, cnt, cnt_limit, file_name = get_torrent_info(
                                    torrent_dest, index, path, session, self.list6, 
                                    self.progress, TMPDIR, self.media_server_key, 
                                    self.client_auth_arr)
            print('--line--15419--', self.do_get_thread.isRunning(), '--do_get--')
            if not self.do_get_thread.isRunning():
                torrent_thread = TorrentThread(
                                handle, cnt, cnt_limit, ses, row=index, 
                                from_client=from_client)
                torrent_thread.start()
            print('--line--15425--', self.do_get_thread.isRunning(), '--do_get--')
            if self.progress.isHidden():
                self.progress.show()
            if from_client:
                self.progress.hide()
                self.started_from_external_client = True
            else:
                self.started_from_external_client = False
            if status.lower() == 'first run':
                self.list6.clear()
                i=0
                for f in info.files():
                    file_path = f.path
                    file_exists = False
                    new_path = os.path.join(path, file_path)
                    new_size = f.size
                    if os.path.exists(new_path) and os.stat(new_path).st_size == new_size:
                        file_exists = True
                    if i > index and not file_exists:
                        txt = os.path.basename(file_path)+':'+str(i)
                        self.list6.addItem(txt)
                    i = i+1
                return url, thread_server, torrent_thread, ses, handle
            else:
                if torrent_thread is None:
                    torrent_thread = self.do_get_thread
                return url, torrent_thread, ses, handle
    
    def initial_view_mode(self):
        global site, show_hide_player
        
        if site.lower() == "music" and show_hide_player == 0:
            if self.float_window.isHidden():
                self.tab_5.hide()
        else:
            self.tab_5.show()
            self.list1.hide()
            self.frame.hide()
            self.text.hide()
            self.label.hide()
            
    def local_torrent_open(self, tmp):
        global local_torrent_file_path, site
        if not self.local_ip:
            self.local_ip = get_lan_ip()
        if not self.local_port:
            self.local_port = 8001
        
        ip = self.local_ip
        port = int(self.local_port)
        if not self.thread_server.isRunning():
            self.thread_server = ThreadServer(
                ip, port, self.media_server_key, self.client_auth_arr, 
                self.https_media_server, self.https_cert_file)
            self.thread_server.start()
        logger.info(tmp)
        tmp = str(tmp)
        if self.torrent_type == 'magnet' or 'magnet:' in tmp:
            
            if tmp.startswith('magnet:'):
                print('------------magnet-----------')
                path = self.torrent_download_folder
                torrent_dest = local_torrent_file_path
                logger.info('torrent_dest={0};path={1}'.format(torrent_dest, path))
                
                self.torrent_handle, self.stream_session, info = get_torrent_info_magnet(
                        tmp, path, self.list6, self.progress, self.tmp_download_folder)
                #self.handle.pause()
                file_arr = []
                self.list2.clear()
                self.epn_arr_list[:]=[]
                for f in info.files():
                    file_path = f.path
                    #if '/' in f.path:
                    #	file_path = file_path.split('/')[-1]
                    file_path = os.path.basename(file_path)
                    ##Needs Verification
                    self.epn_arr_list.append(file_path+'	'+path)
                    self.list2.addItem((file_path))
                self.torrent_handle.pause()
                self.torrent_handle.set_upload_limit(self.torrent_upload_limit)
                self.torrent_handle.set_download_limit(self.torrent_download_limit)
            else:
                index = int(self.list2.currentRow())
                
                cnt, cnt_limit = set_torrent_info(
                    self.torrent_handle, index, self.torrent_download_folder, 
                    self.stream_session, self.list6, self.progress, 
                    self.tmp_download_folder, self.media_server_key, 
                    self.client_auth_arr)
                
                self.do_get_thread = TorrentThread(
                    self.torrent_handle, cnt, cnt_limit, self.stream_session)
                self.do_get_thread.start()
                if self.https_media_server:
                    https_val = 'https'
                else:
                    https_val = 'http'
                url = https_val+'://'+ip+':'+str(port)+'/'
                print(url, '-local-ip-url')
            
                return url
            
        else:
            index = int(self.list2.currentRow())
            path = self.torrent_download_folder
            
            torrent_dest = local_torrent_file_path
            logger.info('torrent_dest={0};index={1};path={2}'.format(torrent_dest, index, path))
            
            self.torrent_handle, self.stream_session, info, cnt, cnt_limit, file_name = get_torrent_info(
                    torrent_dest, index, path, self.stream_session, self.list6, 
                    self.progress, self.tmp_download_folder, self.media_server_key, 
                    self.client_auth_arr)
            
            self.torrent_handle.set_upload_limit(self.torrent_upload_limit)
            self.torrent_handle.set_download_limit(self.torrent_download_limit)
            
            self.do_get_thread = TorrentThread(
                self.torrent_handle, cnt, cnt_limit, self.stream_session)
            self.do_get_thread.start()
            if self.https_media_server:
                https_val = 'https'
            else:
                https_val = 'http'
            url = https_val+'://'+ip+':'+str(port)+'/'
            print(url, '-local-ip-url', site)
            
            return url
                
    def epn_return(self, row, mode=None):
        global site, base_url, embed, epn_goto, mirrorNo, list2_items, quality
        global finalUrl, home, hdr, path_Local_Dir, epn_name_in_list
        global video_local_stream
        global mpv, mpvAlive, indexQueue, Player, startPlayer
        global new_epn, idw, home1, quitReally, buffering_mplayer
        global path_final_Url, siteName, finalUrlFound, refererNeeded, category
        
        if self.if_file_path_exists_then_play(row, self.list2, False):
            finalUrl = self.if_file_path_exists_then_play(row, self.list2, False)
            finalUrl = finalUrl.replace('"', '')
            finalUrl = '"'+finalUrl+'"'
            return finalUrl
        
        item = self.list2.item(row)
        if item:
            epn = item.text()
            epn = epn.replace('#', '', 1)
        else:
            return 0
        if '	' in self.epn_arr_list[row]:
            epn = (self.epn_arr_list[row]).split('	')[1]
        else:
            epn = self.epn_arr_list[row].replace('#', '', 1)
        if site == "PlayLists":
            item = self.list2.item(row)
            if item:
                arr = self.epn_arr_list[row].split('	')
                if len(arr) > 2:
                    if arr[2].startswith('http') or arr[2].startswith('"http'):
                        finalUrl = []
                        finalUrl.append(arr[1])
                        finalUrl.append(arr[2])
                        refererNeeded = True
                    else:
                        finalUrl = arr[1]
                        refererNeeded = False
                else:
                    finalUrl = arr[1]
                    refererNeeded = False
                epn = arr[0]
                if 'youtube.com' in finalUrl:
                    if mode == 'offline':
                        finalUrl = get_yt_url(finalUrl, quality, self.ytdl_path, logger, mode='offline').strip()
                    else:
                        finalUrl = get_yt_url(finalUrl, quality, self.ytdl_path, logger).strip()
        
        if (site != "SubbedAnime" and site!= "DubbedAnime" and site!="PlayLists" 
                and finalUrlFound == False and site!= "None" and site != "Music" 
                and site != "Video" and site !="Local"):
            if site != "Local":
                try:
                    if video_local_stream:
                        if self.https_media_server:
                            https_val = 'https'
                        else:
                            https_val = 'http'
                        finalUrl = https_val+"://"+self.local_ip+':'+str(self.local_port)+'/'
                        print(finalUrl, '=finalUrl--torrent--')
                        if self.thread_server.isRunning():
                            if self.do_get_thread.isRunning():
                                row_file = os.path.join(TMPDIR, 'row.txt')
                                f = open(row_file, 'w')
                                f.write(str(row))
                                f.close()
                                finalUrl = https_val+"://"+self.local_ip+':'+str(self.local_port)+'/'
                            else:
                                finalUrl, self.do_get_thread, self.stream_session, self.torrent_handle = self.start_torrent_stream(name, row, self.local_ip+':'+str(self.local_port), 'Next', self.torrent_download_folder, self.stream_session)
                        else:
                            finalUrl, self.thread_server, self.do_get_thread, self.stream_session, self.torrent_handle = self.start_torrent_stream(name, row, self.local_ip+':'+str(self.local_port), 'First Run', self.torrent_download_folder, self.stream_session)
                        self.torrent_handle.set_upload_limit(self.torrent_upload_limit)
                        self.torrent_handle.set_download_limit(self.torrent_download_limit)
                    else:
                        finalUrl = self.site_var.getFinalUrl(name, epn, mirrorNo, quality)
                except:
                    return 0
            
        elif finalUrlFound == True:
                row_num = row
            
                final = self.epn_arr_list[row_num]
                logger.info(final)
            
                finalUrl = []
                if '	' in final:
                    final = final.replace('#', '', 1)
                    final = final.split('	')[1]
                else:
                    final=re.sub('#', '', final)
                finalUrl.append(final)
                if refererNeeded == True:
                    if '	' in self.epn_arr_list[row_num]:
                        rfr_url = self.epn_arr_list[row_num].split('	')[2]
                    logger.info(rfr_url)
                    finalUrl.append(rfr_url)
        elif site == "SubbedAnime" or site == "DubbedAnime":
            if site == "SubbedAnime":
                code = 6
                if base_url == 16:
                    epn_t = epn.split(' ')[1]
                    new_epn = epn.split(' ')[0]
                else:
                    epn_t = epn
                if self.site_var:
                    try:
                        finalUrl = self.site_var.getFinalUrl(
                                siteName, name, epn, mirrorNo, category, quality
                                ) 
                    except:
                        return 0
            elif site == "DubbedAnime":
                code = 5
                if self.site_var:
                    try:
                        finalUrl = self.site_var.getFinalUrl(
                                siteName, name, epn, mirrorNo, quality
                                ) 
                    except:
                        return 0
        elif site=="None" or site == "Music" or site == "Video" or site == "Local":
            if '	' in self.epn_arr_list[row]:
                finalUrl = '"'+(self.epn_arr_list[row]).split('	')[1]+'"'
                
            else:
                finalUrl = '"'+(self.epn_arr_list[row]).replace('#', '', 1)+'"'
            if site == 'None' and self.btn1.currentText().lower() == 'youtube':
                    finalUrl = finalUrl.replace('"', '')
                    if mode == 'offline':
                        finalUrl = get_yt_url(finalUrl, quality, self.ytdl_path, logger, mode='offline').strip()
                    else:
                        finalUrl = get_yt_url(finalUrl, quality, self.ytdl_path, logger).strip()
                    finalUrl = '"'+finalUrl+'"'
            if 'youtube.com' in finalUrl.lower():
                finalUrl = finalUrl.replace('"', '')
                if mode == 'offline':
                    finalUrl = get_yt_url(finalUrl, quality, self.ytdl_path, logger, mode='offline').strip()
                else:
                    finalUrl = get_yt_url(finalUrl, quality, self.ytdl_path, logger).strip()
        return finalUrl
        
    def watchDirectly(self, finalUrl, title, quit_val):
        global site, base_url, idw, quitReally, Player, epn_name_in_list
        global path_final_Url, current_playing_file_path, curR
        curR = 0
        if title:
            self.epn_name_in_list = title
        else:
            self.epn_name_in_list = 'No Title'
            
        title_sub_path = title.replace('/', '-')
        if title_sub_path.startswith('.'):
            title_sub_path = title_sub_path[1:]
        title_sub_path = os.path.join(self.yt_sub_folder, title_sub_path+'.en.vtt')
        
        if Player=='mplayer':
            print(self.mpvplayer_val.processId(), '=self.mpvplayer_val.processId()')
            if (self.mpvplayer_val.processId()>0):
                self.mpvplayer_val.kill()
                self.mpvplayer_started = False
                #time.sleep(1)
                if self.mpvplayer_val.processId() > 0:
                    print(self.mpvplayer_val.processId(), '=self.mpvplayer_val.processId()')
                    try:
                        #subprocess.Popen(['killall', 'mplayer'])
                        print('hello')
                    except:
                        pass
        print(self.mpvplayer_val.processId(), '=self.mpvplayer_val.processId()')
        if self.mpvplayer_val.processId() > 0:
            self.mpvplayer_val.kill()
            self.mpvplayer_started = False
        quitReally = quit_val
        
        self.list1.hide()
        self.text.hide()
        self.label.hide()
        self.frame.hide()
        idw = str(int(self.tab_5.winId()))
        self.tab_5.show()
        self.tab_5.setFocus()
        
        finalUrl = str(finalUrl)
        path_final_Url = finalUrl
        current_playing_file_path = finalUrl
        command = self.mplayermpv_command(idw, finalUrl, Player)
        if os.path.exists(title_sub_path):
            if Player == 'mpv':
                command = command+' --sub-file='+title_sub_path
                logger.info(command)
        self.infoPlay(command)
        self.tab_5.setFocus()

    def finishedM(self, nm):
        global name, site
        if (site == "Music" and self.list3.currentItem()) or (site == 'PlayLists'):
            if nm:
                m_path = os.path.join(home, 'Music', 'Artist', nm, 'poster.jpg')
                t_path = os.path.join(home, 'Music', 'Artist', nm, 'thumbnail.jpg')
                f_path = os.path.join(home, 'Music', 'Artist', nm, 'fanart.jpg')
                b_path = os.path.join(home, 'Music', 'Artist', nm, 'bio.txt')
                tmp_nm = os.path.join(TMPDIR, nm)
                logger.info(tmp_nm)
                if os.path.exists(tmp_nm+'.jpg'):
                    shutil.copy(tmp_nm+'.jpg', m_path)
                if os.path.exists(tmp_nm+'-bio.txt'):
                    shutil.copy(tmp_nm+'-bio.txt', b_path)
                if os.path.exists(b_path):
                    sumr = open_files(b_path, False)
                else:
                    sumr = "Summary Not Available"
                self.videoImage(m_path, t_path, f_path, sumr)
                self.label.show()
                self.text.show()
    
    def start_offline_mode(self, row):
        global site, name, hdr
        if not self.if_file_path_exists_then_play(row, self.list2, False):
            finalUrl = self.epn_return(row, mode='offline')
            referer = False
            if type(finalUrl) is not list:
                finalUrl = finalUrl.replace('"', '')
            else:
                rfr = finalUrl[1]
                logger.info(rfr)
                finalUrl = re.sub('#|"', '', finalUrl[0])
                logger.info(finalUrl)
                referer = True
                
            self.list2.setFocus()
            r = self.list2.currentRow()
            print(r)
            new_epn = self.list2.item(row).text()
            if new_epn.startswith(self.check_symbol):
                new_epn = new_epn[1:] 
            new_epn = new_epn.replace('/', '-')
            new_epn = re.sub('"|.mkv|.mp4', '', new_epn)
            if new_epn.startswith('.'):
                new_epn = new_epn[1:]
            if finalUrl.endswith('.mkv'):
                new_epn = new_epn+'.mkv'
            else:
                new_epn = new_epn+'.mp4'
            if self.list1.currentItem():
                title = self.list1.currentItem().text()
            else:
                title = name
            folder_name = os.path.join(self.default_download_location, title)
            if not os.path.exists(folder_name):
                os.makedirs(folder_name)
            npn = os.path.join(folder_name, new_epn)
            if finalUrl.startswith('http'):
                if not referer:
                    command = wget_string(finalUrl, npn, self.get_fetch_library)
                else:
                    command = wget_string(finalUrl, npn, self.get_fetch_library, rfr)
                logger.info(command)
                self.infoWget(command, 0)
        self.download_video = 0
        
    def dataReadyW(self, p):
        global wget, new_epn, quitReally, curR, epn, opt, base_url, Player, site
        global sizeFile
        print('----------------')
        try:
            a = str(p.readAllStandardOutput(), 'utf-8').strip()
            #print(a)
        except:
            a =''
        if self.get_fetch_library.lower() == 'wget':
            if "Length:" in a:
                l = re.findall('[(][^)]*[)]', a)
                if l:
                    sizeFile = l[0]
                
            if "%" in a:
                m = re.findall('[0-9][^\n]*', a)
                if m:
                    n = re.findall('[^%]*', m[0])
                    if n:
                        try:
                            val = int(n[0])
                        except:
                            val = 0
                        self.progress.setValue(val)
                    try:
                        out = str(m[0])+" "+sizeFile
                    except:
                        out = str(m[0])+" "+'0'
                    self.progress.setFormat(out)
        else:
            b = a.split(' ')
            c = []
            for i in b:
                if i:
                    c.append(i)
            
            d = []
            for j in range(len(c)):
                if j == 2 or j == 4 or j == 5 or j == 6 or j == 7 or j == 8 or j == 9:
                    pass
                else:
                    d.append(c[j])
            if d:
                try:
                    if ':' not in d[0] and len(d) > 3:
                        percent = int(d[0])
                        self.progress.setValue(percent)
                except Exception as e:
                    print(e)
            word = ' '.join(d)
            #print(word)
            #print(c)
            if len(c)<=3 and len(c)>=2:
                self.curl_progress_end = c[-2]+' '+c[-1]
            elif len(c)>=3:
                if ':' not in c[0]:
                    self.curl_progress_init = c[0]+'% '+c[1]+' '+c[3]
                if 'k' in c[-1]:
                    self.curl_progress_end = c[-2]+' '+c[-1]
                    
            word = self.curl_progress_init+' '+self.curl_progress_end
            self.progress.setFormat(word)
                
    def startedW(self):
        global new_epn
        self.progress.setValue(0)
        self.progress.show()
        print("Process Started")
        
    def finishedW(self, src):
        global name, hdr, site
        print("Process Ended")
        self.progress.setValue(100)
        self.progress.hide()
        if self.tab_2.isHidden():
            pass
        type_int = False
        if self.queue_url_list:
            j = 0
            for i in self.queue_url_list:
                if type(i) is int:
                    type_int = True
                    break
                j = j+1
            
            if type_int:
                t = self.queue_url_list[j]
                t1 = self.list6.item(j)
                nepn = t1.text()
                nepn = re.sub('#|"', '', nepn)
                nepn = nepn.replace('/', '-')
                nepn = re.sub('"|.mkv|.mp4', '', nepn)
                nepn = nepn.replace('_', ' ')
                self.list6.takeItem(j)
                del t1
                del self.queue_url_list[j]
                print(t, '**************row------num-----------')
                finalUrl = self.epn_return(t, mode='offline')
                referer = False
                if type(finalUrl) is not list:
                    finalUrl = finalUrl.replace('"', '')
                else:
                    rfr = finalUrl[1]
                    logger.info(rfr)
                    finalUrl = re.sub('#|"', '', finalUrl[0])
                    logger.info(finalUrl)
                    referer = True
                if self.list1.currentItem():
                    title = self.list1.currentItem().text()
                else:
                    title = name
                npn = os.path.join(self.default_download_location, title, nepn)
                if finalUrl.endswith('.mkv'):
                    npn = npn+'.mkv'
                else:
                    npn = npn+'.mp4'
                if finalUrl.startswith('http'):
                    if not referer:
                        command = wget_string(finalUrl, npn, self.get_fetch_library)
                    else:
                        command = wget_string(finalUrl, npn, self.get_fetch_library, rfr)
                    logger.info(command)
                    self.infoWget(command, 0)
        
    def infoWget(self, command, src):
        global wget
        wget = QtCore.QProcess()
        wget.setProcessChannelMode(QtCore.QProcess.MergedChannels)
        self.curl_progress_init = ''
        self.curl_progress_end = ''
        wget.started.connect(self.startedW)
        wget.readyReadStandardOutput.connect(partial(self.dataReadyW, wget))
        wget.finished.connect(lambda x=src : self.finishedW(src))
        QtCore.QTimer.singleShot(1000, partial(wget.start, command))
        
    def dataReady(self, p):
        global new_epn, quitReally, curR, epn, opt, base_url, Player, site
        global wget, cache_empty, buffering_mplayer, slider_clicked
        global fullscr, artist_name_mplayer, layout_mode, server
        global new_tray_widget, video_local_stream, pause_indicator
        global epn_name_in_list, mpv_indicator, mpv_start, idw, cur_label_num
        global sub_id, audio_id, current_playing_file_path, wget, desktop_session
        
        try:
            a = str(p.readAllStandardOutput(), 'utf-8').strip()
            if 'volume' in a:
                print(a)
            if 'Video' in a:
                logger.info(a)
            if 'Audio' in a:
                logger.info(a)
            #print(a)
            if 'icy info:' in a.lower() or 'icy-title:' in a.lower():
                if 'icy info:' in a.lower():
                    song_title = re.search("'[^']*", a)
                    self.epn_name_in_list = song_title.group().replace("'", '')
                else:
                    song_title = re.search("icy-title:[^\n]*", a)
                    self.epn_name_in_list = song_title.group().replace('icy-title:', '')
                print(self.epn_name_in_list, '--radio--song--')
                self.mplayerLength = 1
                self.epn_name_in_list = self.epn_name_in_list.strip()
                server._emitMeta('internet-radio#'+self.epn_name_in_list, site, self.epn_arr_list)
                
        except Exception as e:
            print(e)
            a = ""
        #el = time.process_time() - tt
        #print(el)
        try:
            if Player == "mpv":
                if "Audio_ID" in a:
                    print('--', a, '--')
                    new_arr = a.split('\n')
                    for i in new_arr:
                        if i.startswith('Audio_ID'):
                            a_id = i.split('=')[-1]
                            break
                    #a_id = re.sub('[^"]*Audio_ID=', '', a)
                    print('--', a_id, '--')
                    audio_s = (re.search('[(][^)]*', a_id))
                    if audio_s:
                        audio_id = (audio_s.group()).replace('(', '')
                    else:
                        audio_id="no"
                    print("audio_id="+audio_id)
                    self.audio_track.setText("A:"+str(a_id[:8]))
                if "SUB_ID" in a:
                    print('--', a, '--')
                    new_arr = a.split('\n')
                    print(new_arr)
                    for i in new_arr:
                        if i.startswith('SUB_ID'):
                            print('--', i, '--')
                            s_id = i.split('=')[-1]
                            break
                    #s_id = re.sub('[^"]*SUB_ID=', '', a)
                    sub_s = (re.search('[(][^)]*', s_id))
                    if sub_s:
                        sub_id = (sub_s.group()).replace('(', '')
                    else:
                        sub_id = "no"
                    print("sub_id="+sub_id)
                    self.subtitle_track.setText("Sub:"+str(s_id[:8]))
                if "Length_Seconds=" in a and not self.mplayerLength and 'args=' not in a:
                    print(a)
                    if a.startswith(r"b'"):
                        mpl = re.sub('[^"]*Length_Seconds=', '', a)
                        mpl = mpl.replace(r"\n'", '')
                    else:
                        mpl = re.sub('[^"]*Length_Seconds=', '', a)
                    print(mpl, '--mpl--')
                    o = mpl.split(':')
                    if o and len(o) == 3:
                        if o[0].isdigit() and (o[1]).isdigit() and (o[2]).isdigit():
                            self.mplayerLength = int(o[0])*3600+int(o[1])*60+int(o[2])
                        else:
                            self.mplayerLength = 0
                        print(mpl)
                        print(self.mplayerLength)
                        self.slider.setRange(0, int(self.mplayerLength))
            
                if "AV:" in a or "A:" in a:
                    if not mpv_start:
                        mpv_start.append("Start")
                        try:
                            npn = '"'+"Playing: "+self.epn_name_in_list.replace('#', '', 1)+'"'
                            npn1 = bytes('\n'+'show-text '+npn+' 4000'+'\n', 'utf-8')
                            self.mpvplayer_val.write(npn1)
                        except:
                            pass
                        if MainWindow.isFullScreen() and layout_mode != "Music":
                            self.gridLayout.setSpacing(0)
                            if not self.frame1.isHidden():
                                self.frame1.hide()
                            if self.frame_timer.isActive():
                                self.frame_timer.stop()
                            self.frame_timer.start(5000)
                    if ("Buffering" in a and not mpv_indicator 
                            and (site != "Local" or site != "Music" 
                            or site != "Video")):
                        cache_empty = "yes"
                        mpv_indicator.append("cache empty") 
                        print("buffering")
                        self.mpvplayer_val.write(b'\n set pause yes \n')
                        self.player_play_pause.setText(self.player_buttons['play'])
                        #if self.mplayer_timer.isActive():
                        #	self.mplayer_timer.stop()
                        #self.mplayer_timer.start(5000)
                        if not pause_indicator:
                            pause_indicator.append('Pause')
                        if MainWindow.isFullScreen() and layout_mode != "Music":
                            self.gridLayout.setSpacing(0)
                            self.frame1.show()
                            if self.frame_timer.isActive():
                                self.frame_timer.stop()
                            self.frame_timer.start(5000)
                            
                    t = re.findall("AV:[^)]*[)]|A:[^)]*[)]", a)
                    #print('found ', t)
                    if not t:
                        t = re.findall("AV: [^ ]*|A: [^ ]*", a)
                        if not t:
                            t = ['AV: 00:00:00 / 00:00:00 (0%)']
                    if "Cache:" in a:
                        cache_int = 0
                        n = re.findall("Cache:[^+]*", a)
                        cache_val = re.search("[0-9][^s]*", n[0]).group()
                        
                        try:
                            cache_int = int(cache_val)
                        except Exception as err_val:
                            print(err_val)
                            cache_int = 0
                        if cache_int >= 119:
                            cache_int = 119
                        elif cache_int >=9 and cache_int < 12:
                            cache_int = 10
                        if cache_int < 10:
                            cache_val = '0'+str(cache_int)
                        else:
                            cache_val = str(cache_int)
                        out = t[0] +"  Cache:"+str(cache_val)+'s'
                    else:
                        cache_val = '0'
                        cache_int = 0
                        out = t[0]
                    try:
                        new_cache_val = cache_int
                    except Exception as e:
                        print(e, '--cache-val-error--')
                        new_cache_val = 0
                    if "Paused" in a and not mpv_indicator:
                        out = "(Paused) "+out
                        #print(out)
                    elif "Paused" in a and mpv_indicator:
                        out = "(Paused Caching..) "+out
                        #print(out)
                    out = re.sub('AV:[^0-9]*|A:[^0-9]*', '', out)
                    
                    #print(out)
                    l = re.findall("[0-9][^ ]*", out)
                    val1 = l[0].split(':')
                    val = int(val1[0])*3600+int(val1[1])*60+int(val1[2])
                    #print(val)
                    if not self.mplayerLength:
                        if self.mpv_cnt > 4:
                            m = re.findall('[/][^(]*', out)
                            try:
                                n = re.sub(' |[/]', '', m[0])
                            except Exception as err_msg:
                                print(err_msg)
                                n = '00:00:00'
                            print(n)
                            o = n.split(':')
                            self.mplayerLength = int(o[0])*3600+int(o[1])*60+int(o[2])
                            print(self.mplayerLength, "--mpvlength", a)
                            if self.mplayerLength == 0:
                                self.mplayerLength = 1
                            self.progressEpn.setMaximum(int(self.mplayerLength))
                            self.slider.setRange(0, int(self.mplayerLength))
                            self.mpv_cnt = 0
                        print(self.mplayerLength)
                        self.mpv_cnt = self.mpv_cnt + 1
                    out1 = out+" ["+self.epn_name_in_list+"]"
                    self.progressEpn.setFormat((out1))
                    if self.mplayerLength == 1:
                        val = 0
                        self.slider.setValue(0)
                    else:
                        self.slider.setValue(val)
                    self.progress_counter = val
                    if not new_tray_widget.isHidden():
                        new_tray_widget.update_signal.emit(out, val)
                    if cache_empty == 'yes':
                        try:
                            if new_cache_val > 4:
                                #if self.mplayer_timer.isActive():
                                #	self.mplayer_timer.stop()
                                #self.mplayer_timer.start(10)
                                cache_empty = 'no'
                                self.mpvplayer_val.write(b'\n set pause no \n')
                                self.player_play_pause.setText(self.player_buttons['pause'])
                                if mpv_indicator:
                                    mpv_indicator.pop()
                                if pause_indicator:
                                    pause_indicator.pop()
                        except Exception as err_val:
                            print(err_val, '--mpv--cache-error--')
                if "VO:" in a or "AO:" in a or 'Stream opened successfully' in a:
                    t = "Loading: "+self.epn_name_in_list+" (Please Wait)"
                    self.progressEpn.setFormat((t))
                    if MainWindow.isFullScreen() and layout_mode != "Music":
                        if desktop_session == 'lxde' or desktop_session == 'lxqt' or desktop_session == 'xfce':
                            self.gridLayout.setSpacing(0)
                            self.frame1.show()
                            if self.frame_timer.isActive():
                                self.frame_timer.stop()
                            self.frame_timer.start(1000)
                if ("EOF code: 1" in a or "HTTP error 403 Forbidden" in a):
                    if self.player_setLoop_var:
                        if current_playing_file_path.startswith('"'):
                            replay = '\n loadfile {0} replace \n'.format(current_playing_file_path)
                        else:
                            replay = '\n loadfile "{0}" replace \n'.format(current_playing_file_path)
                        t2 = bytes(replay, 'utf-8')
                        #logger.info(t2)
                        self.mpvplayer_val.write(t2)
                        return 0
                    else:
                        if not self.queue_url_list:
                            if self.list2.count() == 0:
                                return 0
                            if curR == self.list2.count() - 1:
                                curR = 0
                                if site == "Music" and not self.playerPlaylist_setLoop_var:
                                    r1 = self.list1.currentRow()
                                    it1 = self.list1.item(r1)
                                    if it1:
                                        if r1 < self.list1.count():
                                            r2 = r1+1
                                        else:
                                            r2 = 0
                                        self.list1.setCurrentRow(r2)
                                        self.listfound()
                            else:
                                curR = curR + 1
                            self.list2.setCurrentRow(curR)
                    self.mplayerLength = 0
                    self.total_file_size = 0
                    if mpv_start:
                        mpv_start.pop()
                    if "HTTP error 403 Forbidden" in a:
                        print(a)
                        quitReally = "yes"
                    if quitReally == "no":
                        if self.tab_5.isHidden() and thumbnail_indicator:
                            length_1 = self.list2.count()
                            q3="self.label_epn_"+str(length_1+cur_label_num)+".setText(self.epn_name_in_list)"
                            exec (q3)
                            q3="self.label_epn_"+str(length_1+cur_label_num)+".setAlignment(QtCore.Qt.AlignCenter)"
                            exec(q3)
                            #QtWidgets.QApplication.processEvents()
                        if (site == "Local" or site == "Video" or site == "Music" 
                                or site == "PlayLists" or site == "None" or site == 'MyServer'):
                            if len(self.queue_url_list)>0 and wget.processId() == 0:
                                self.getQueueInList()
                            else:
                                self.localGetInList()
                        else:
                            if len(self.queue_url_list)>0 and wget.processId() == 0:
                                self.getQueueInList()
                            else:
                                self.getNextInList()
                    elif quitReally == "yes": 
                        self.list2.setFocus()
            elif Player == "mplayer":
                if "PAUSE" in a:
                    if buffering_mplayer != 'yes':
                        self.player_play_pause.setText(self.player_buttons['play'])
                        #print('set play button text = Play')
                    if MainWindow.isFullScreen() and layout_mode != "Music":
                        self.gridLayout.setSpacing(0)
                        self.frame1.show()
                        if (buffering_mplayer == "yes"):
                            if self.frame_timer.isActive:
                                self.frame_timer.stop()
                            self.frame_timer.start(10000)
                if "Cache empty" in a:
                    cache_empty = "yes"
                    
                if "ID_VIDEO_BITRATE" in a:
                    try:
                        a0 = re.findall('ID_VIDEO_BITRATE=[^\n]*', a)
                        print(a0[0], '--videobit')
                        a1 = a0[0].replace('ID_VIDEO_BITRATE=', '')
                        self.id_video_bitrate=int(a1)
                    except:
                        self.id_video_bitrate = 0
                    
                if "ID_AUDIO_BITRATE" in a:
                    try:
                        a0 = re.findall('ID_AUDIO_BITRATE=[^\n]*', a)
                        print(a0[0], '--audiobit')
                        a1 = a0[0].replace('ID_AUDIO_BITRATE=', '')
                        self.id_audio_bitrate=int(a1)
                    except:
                        self.id_audio_bitrate=0
                if "ANS_switch_audio" in a:
                    print(a)
                    audio_id = a.split('=')[-1]
                    
                    print("audio_id="+audio_id)
                    self.audio_track.setText("A:"+str(audio_id))
                if "ANS_sub" in a:
                    sub_id = a.split('=')[-1]
                    
                    print("sub_id="+sub_id)
                    self.subtitle_track.setText("Sub:"+str(sub_id))
                
                if "ID_LENGTH" in a and not self.mplayerLength:
                    t = re.findall('ID_LENGTH=[0-9][^.]*', a)
                    self.mplayerLength = re.sub('ID_LENGTH=', '', t[0])
                    print(self.mplayerLength)
                    self.mplayerLength = int(self.mplayerLength) *1000
                    self.slider.setRange(0, int(self.mplayerLength))
                    self.total_file_size = int(((self.id_audio_bitrate+self.id_video_bitrate)*self.mplayerLength)/(8*1024*1024*1000))
                    print(self.total_file_size, ' MB')
                if ("A:" in a) or ("PAUSE" in a):
                    if not mpv_start:
                        mpv_start.append("Start")
                        try:
                            npn = '"'+"Playing: "+self.epn_name_in_list.replace('#', '', 1)+'"'
                            npn1 = bytes('\n'+'osd_show_text '+str(npn)+' 4000'+'\n', 'utf-8')
                            self.mpvplayer_val.write(npn1)
                        except:
                            pass
                        if MainWindow.isFullScreen() and layout_mode != "Music":
                            self.gridLayout.setSpacing(0)
                            if not self.frame1.isHidden():
                                self.frame1.hide()
                            if self.frame_timer.isActive():
                                self.frame_timer.stop()
                            self.frame_timer.start(1000)
                    #print(a)
                    if "PAUSE" in a:
                        print(a, 'Pause A')
                        c = None
                        c_int = 0
                        if "%" in a:
                            #print a
                            m = a.split(' ')
                            print(m)
                            if m:
                                try:
                                    c = m[-1]
                                    if len(c) > 3:
                                        c = "0%"
                                    c_int = int(c.replace('%', '')) 
                                except Exception as e:
                                    print(e, '--percent cache error--')
                        try:
                            t = str(self.progressEpn.text())
                            if c and c_int:
                                t = re.sub('Cache:[0-9]*%', '', t)
                            t = t.strip()
                            if '(Paused) ' in t:
                                t = t.replace('(Paused) ', '')
                            if '(Paused Caching..Wait) ' in t:
                                t = t.replace('(Paused Caching..Wait) ', '')
                        except:
                            t = ""
                        #print(t, ' --t val--')
                        if buffering_mplayer == "yes" or self.mplayer_pause_buffer:
                            #print(video_local_stream, '--video--local--stream--')
                            print('buffering mplayer')
                            if 'Cache:' not in t:
                                out = "(Paused Caching..Wait) "+t+' Cache:'+c
                            else:
                                out = "(Paused Caching..Wait) "+t
                            if ((not self.mplayer_timer.isActive()) 
                                    and (not video_local_stream) and c_int > 0):
                                self.mplayer_timer.start(1000)
                            elif ((not self.mplayer_timer.isActive()) 
                                    and (video_local_stream) and c_int > 5):
                                self.mplayer_timer.start(1000)
                            #buffering_mplayer = "no"
                        else:
                            if c_int and c:
                                out = "(Paused) "+t+' Cache:'+c
                            else:
                                out = "(Paused) "+t
                            
                            if ((not self.mplayer_timer.isActive()) 
                                    and (video_local_stream) and c_int > 5):
                                self.mplayer_timer.start(1000)
                        #print(out, '--out--')
                    else:
                        if "%" in a:
                            #print a
                            m = a.split(' ')
                            try:
                                c = m[-2]
                            except:
                                c = "0%"
                        else:
                            c = "0%"
                    
                        t = re.findall('A:[^.]*', a)
                        #print t
                        l = re.sub('A:[^0-9]*', '', t[0])
                        #l = int(l)
                        l =int(l)*1000
                        
                        if self.mplayerLength == 1:
                            l = 0
                            self.slider.setValue(0)
                        else:
                            self.slider.setValue(int(l))
                        
                        if site == "Music":
                            out_time = str(datetime.timedelta(milliseconds=int(l))) + " / " + str(datetime.timedelta(milliseconds=int(self.mplayerLength)))
                            
                            out = out_time + " ["+self.epn_name_in_list+'('+artist_name_mplayer+')' +"]"
                        else:
                            out_time = str(datetime.timedelta(milliseconds=int(l))) + " / " + str(datetime.timedelta(milliseconds=int(self.mplayerLength)))
                            
                            out = out_time + " ["+self.epn_name_in_list+"]" +' Cache:'+c
                            
                        if not new_tray_widget.isHidden():
                            new_tray_widget.update_signal.emit(out_time, int(l))
                        if video_local_stream:
                            if c == '0%' and not self.mplayer_pause_buffer and not self.mplayer_nop_error_pause:
                                self.mpvplayer_val.write(b'\n pause \n')
                                self.mplayer_pause_buffer = True
                    if ((cache_empty == "yes" ) 
                            and (site != "Local" or site != "Music" or site != "Video")):
                        print('---nop--error--pausing---')
                        if not self.mplayer_pause_buffer:
                            self.mpvplayer_val.write(b'\n pause \n')
                            cache_empty = "no"
                            buffering_mplayer = "yes"
                    elif (('nop_streaming_read_error' in a) 
                            and (site != "Local" or site != "Music" or site != "Video")):
                        print('---nop--error--pausing---')
                        if not self.mplayer_pause_buffer:
                            self.mpvplayer_val.write(b'\n pause \n')
                            cache_empty = "no"
                            buffering_mplayer = "yes"
                            self.mplayer_nop_error_pause = True
                    if self.total_seek != 0:
                        r = "Seeking "+str(self.total_seek)+'s'
                        self.progressEpn.setFormat((r))
                    else:
                        self.progressEpn.setFormat((out))
                if 'http' in a:
                    t = "Loading: "+self.epn_name_in_list+" (Please Wait)"
                    self.progressEpn.setFormat((t))
                    if MainWindow.isFullScreen() and layout_mode != "Music":
                        self.gridLayout.setSpacing(0)
                        self.frame1.show()
                        if self.frame_timer.isActive():
                            self.frame_timer.stop()
                        self.frame_timer.start(1000)
                if ("EOF code: 1" in a or "HTTP error 403 Forbidden" in a):
                    self.mplayerLength = 0
                    self.total_file_size = 0
                    mpv_start.pop()
                    if self.player_setLoop_var:
                        t2 = bytes('\n'+"loadfile "+(current_playing_file_path)+" replace"+'\n', 'utf-8')
                        self.mpvplayer_val.write(t2)
                        #print(t2)
                        return 0
                    else:
                        if not self.queue_url_list:
                            if self.list2.count() == 0:
                                return 0
                            if curR == self.list2.count() - 1:
                                curR = 0
                                if site == "Music" and not self.playerPlaylist_setLoop_var:
                                    r1 = self.list1.currentRow()
                                    it1 = self.list1.item(r1)
                                    if it1:
                                        if r1 < self.list1.count():
                                            r2 = r1+1
                                        else:
                                            r2 = 0
                                        self.list1.setCurrentRow(r2)
                                        self.listfound()
                            else:
                                curR = curR + 1
                            self.list2.setCurrentRow(curR)
                        
                    if "HTTP error 403 Forbidden" in a:
                        print(a)
                        quitReally = "yes"
                    if quitReally == "no":
                        if (site == "Local" or site == "Video" 
                                or site == "Music" or site == "PlayLists" 
                                or site == "None" or site == 'MyServer'):
                            if len(self.queue_url_list)>0 and wget.processId() == 0:
                                self.getQueueInList()
                            else:
                                self.localGetInList()
                        else:
                            if len(self.queue_url_list)>0 and wget.processId() == 0:
                                self.getQueueInList()
                            else:
                                self.getNextInList()
                        if self.tab_5.isHidden() and thumbnail_indicator:
                            length_1 = self.list2.count()
                            q3="self.label_epn_"+str(length_1+cur_label_num)+".setText((self.epn_name_in_list))"
                            exec (q3)
                            q3="self.label_epn_"+str(length_1+cur_label_num)+".setAlignment(QtCore.Qt.AlignCenter)"
                            exec(q3)
                            QtWidgets.QApplication.processEvents()
                    elif quitReally == "yes": 
                        self.list2.setFocus()
        except Exception as e:
            print(e, '--dataready--exception--')
        
    def started(self):
        global epn, new_epn, epn_name_in_list, fullscr, mpv_start
        global Player, cur_label_num, epn_name_in_list, site
        if self.tab_5.isHidden() and thumbnail_indicator:
            length_1 = self.list2.count()
            q3="self.label_epn_"+str(length_1+cur_label_num)+".setText((self.epn_name_in_list))"
            exec(q3)
            q3="self.label_epn_"+str(length_1+cur_label_num)+".setAlignment(QtCore.Qt.AlignCenter)"
            exec(q3)
            QtWidgets.QApplication.processEvents()
        print("Process Started")
        print(self.mpvplayer_val.processId())
        mpv_start =[]
        mpv_start[:]=[]
        t = "Loading: "+self.epn_name_in_list+" (Please Wait)"
        #print t
        self.progressEpn.setValue(0)
        self.progressEpn.setFormat((t))
        if MainWindow.isFullScreen() and site!="Music":
            self.superGridLayout.setSpacing(0)
            self.gridLayout.setSpacing(0)
            self.frame1.show()
            if self.frame_timer.isActive():
                self.frame_timer.stop()
        
    def finished(self):
        global quitReally, mpv_start
        if mpv_start:
            mpv_start.pop()
        self.mplayerLength = 0
        self.progressEpn.setMaximum(100)
        self.slider.setRange(0, 100)
        print("Process Ended")
        self.progressEpn.setValue(0)
        self.slider.setValue(0)
        self.progressEpn.setFormat("")
        print(self.mpvplayer_val.processId(), '--finished--id--')

    def infoPlay(self, command):
        global Player, site, new_epn, mpv_indicator, cache_empty
        if not command:
            t = "Loading Failed: No Url/File Found. Try Again"
            self.progressEpn.setFormat(t)
        else:
            if mpv_indicator:
                mpv_indicator.pop()
            cache_empty = 'no'
            if command.startswith('mplayer') and OSNAME == 'nt':
                command = command + ' -vo gl'
            if self.player_setLoop_var == 1:
                if Player == 'mplayer':
                    command = command+' -loop 0'
                    
            print('--line--15662--')
            if self.mpvplayer_val.processId()>0:
                self.mpvplayer_val.kill()
                self.mpvplayer_started = False
                try:
                    if not self.mplayer_status_thread.isRunning():
                        self.mplayer_status_thread = PlayerWaitThread(self, command)
                        self.mplayer_status_thread.start()
                    else:
                        self.mpvplayer_command.append(command)
                except Exception as e:
                    print(e)
            else:
                if self.mpvplayer_command:
                    command = self.mpvplayer_command[-1]
                    self.mpvplayer_command[:] = []
                self.tab_5.set_mpvplayer(player=self.player_val, mpvplayer=self.mpvplayer_val)
                self.mpvplayer_val.setProcessChannelMode(QtCore.QProcess.MergedChannels)
                self.mpvplayer_val.started.connect(self.started)
                self.mpvplayer_val.readyReadStandardOutput.connect(partial(self.dataReady, self.mpvplayer_val))
                self.mpvplayer_val.finished.connect(self.finished)
                QtCore.QTimer.singleShot(1000, partial(self.mpvplayer_val.start, command))
                logger.info(command)
                logger.info('infoplay--18165--')
                self.mpvplayer_started = True
                if self.player_setLoop_var == 1 and Player == 'mpv':
                    QtCore.QTimer.singleShot(15000, partial(self.set_playerLoopFile))
                
    def adjust_thumbnail_window(self, row):
        global thumbnail_indicator, idw, ui, cur_label_num
        if self.epn_name_in_list.startswith('#'):
            self.epn_name_in_list = self.epn_name_in_list.replace('#', '', 1)
        if (thumbnail_indicator and idw == str(int(self.tab_5.winId()))):
            try:
                title_num = row + self.list2.count()
                if self.epn_name_in_list.startswith(self.check_symbol):
                    newTitle = self.epn_name_in_list
                else:
                    newTitle = self.check_symbol+self.epn_name_in_list
                    
                sumry = "<html><h1>"+self.epn_name_in_list+"</h1></html>"
                q4="self.label_epn_"+str(title_num)+".setToolTip((sumry))"
                exec (q4)
                q3="self.label_epn_"+str(title_num)+".setText((newTitle))"
                exec (q3)
                q3="self.label_epn_"+str(title_num)+".setAlignment(QtCore.Qt.AlignCenter)"
                exec(q3)
                QtWidgets.QApplication.processEvents()
                
                p1 = "self.label_epn_"+str(row)+".y()"
                ht=eval(p1)
                
                self.scrollArea1.verticalScrollBar().setValue(ht)
                self.labelFrame2.setText(newTitle[:20]+'..')
                
                new_cnt = curR + self.list2.count()
                p1 = "self.label_epn_{0}.setTextColor(QtCore.Qt.green)".format(new_cnt)
                exec (p1)
                p1 = "self.label_epn_{0}.toPlainText()".format(new_cnt)
                txt = eval(p1)
                try:
                    p1 = "self.label_epn_{0}.setText('{1}')".format(new_cnt, txt)
                    exec(p1)
                except Exception as e:
                    print(e, '--line--4597--')
                    try:
                        p1 = 'self.label_epn_{0}.setText("{1}")'.format(new_cnt, txt)
                        exec(p1)
                    except Exception as e:
                        print(e)
                p1="self.label_epn_{0}.setAlignment(QtCore.Qt.AlignCenter)".format(new_cnt)
                exec(p1)
                QtWidgets.QApplication.processEvents()
            except Exception as e:
                print(e)
        else:
            if idw and idw != str(int(self.tab_5.winId())) and idw != str(int(self.label.winId())):
                try:
                    title_num = row + self.list2.count()
                    if self.epn_name_in_list.startswith(self.check_symbol):
                        newTitle = self.epn_name_in_list
                    else:
                        newTitle = self.check_symbol+self.epn_name_in_list
                    sumry = "<html><h1>"+self.epn_name_in_list+"</h1></html>"
                    q4="self.label_epn_"+str(title_num)+".setToolTip((sumry))"
                    exec (q4)
                    q3="self.label_epn_"+str(title_num)+".setText((newTitle))"
                    exec (q3)
                    q3="self.label_epn_"+str(title_num)+".setAlignment(QtCore.Qt.AlignCenter)"
                    exec(q3)
                    QtWidgets.QApplication.processEvents()
                    
                    if self.video_mode_index == 1:
                        p1 = "self.label_epn_"+str(row)+".y()"
                        ht=eval(p1)
                        self.scrollArea1.verticalScrollBar().setValue(ht)
                    self.labelFrame2.setText(newTitle[:20]+'..')
                    
                    new_cnt = curR + self.list2.count()
                    p1 = "self.label_epn_{0}.setTextColor(QtCore.Qt.green)".format(new_cnt)
                    exec (p1)
                    p1 = "self.label_epn_{0}.toPlainText()".format(new_cnt)
                    txt = eval(p1)
                    try:
                        p1 = "self.label_epn_{0}.setText('{1}')".format(new_cnt, txt)
                        exec(p1)
                    except Exception as e:
                        print(e, '--line--4597--')
                        try:
                            p1 = 'self.label_epn_{0}.setText("{1}")'.format(new_cnt, txt)
                            exec(p1)
                        except Exception as e:
                            print(e)
                    p1="self.label_epn_{0}.setAlignment(QtCore.Qt.AlignCenter)".format(new_cnt)
                    exec(p1)
                    
                    init_cnt = cur_label_num + self.list2.count()
                    p1 = "self.label_epn_{0}.setTextColor(QtCore.Qt.green)".format(init_cnt)
                    exec (p1)
                    try:
                        p1 = "self.label_epn_{0}.setText('{1}')".format(init_cnt, txt)
                        exec(p1)
                    except Exception as e:
                        print(e, '--line--4597--')
                        try:
                            p1 = 'self.label_epn_{0}.setText("{1}")'.format(init_cnt, txt)
                            exec(p1)
                        except Exception as e:
                            print(e)
                    p1="self.label_epn_{0}.setAlignment(QtCore.Qt.AlignCenter)".format(init_cnt)
                    exec(p1)
                except Exception as e:
                    print(e)
    
    def localGetInList(self):
        global site, base_url, embed, epn, epn_goto, mirrorNo, list2_items, quality
        global finalUrl, curR, home, buffering_mplayer, epn_name_in_list
        global opt_movies_indicator, audio_id, sub_id, siteName, artist_name_mplayer
        global mpv, mpvAlive, indexQueue, Player, startPlayer
        global new_epn, path_Local_Dir, Player, curR
        global fullscr, thumbnail_indicator, category, finalUrlFound, refererNeeded
        global server, current_playing_file_path, music_arr_setting
        global default_arr_setting, wget, idw
        
        self.external_url = False
        print(self.player_setLoop_var)
        row = self.list2.currentRow()
        print('--line--15677--')
        if row > len(self.epn_arr_list) or row < 0:
            row = len(self.epn_arr_list)-1
        finalUrl = ""
        try:
            server._emitMeta("Next", site, self.epn_arr_list)
        except:
            pass
        self.mplayerLength = 0
        buffering_mplayer = "no"
        
        if self.if_file_path_exists_then_play(row, self.list2, True):
            self.adjust_thumbnail_window(row)
            return 0
                    
        self.set_init_settings()
        
        if site != "PlayLists":
            if '	' in self.epn_arr_list[row]:
                epn = self.epn_arr_list[row].split('	')[1]
                self.epn_name_in_list = (self.epn_arr_list[row]).split('	')[0]
            else:
                epn = self.list2.currentItem().text()
                self.epn_name_in_list = str(epn)
                epn = self.epn_arr_list[row].replace('#', '', 1)
            if not epn:
                return 0
            epn = epn.replace('#', '', 1)
        else:
            item = self.list2.item(row)
            if item:
                arr = self.epn_arr_list[row].split('	')
                if len(arr) >= 2:
                    path_rel = arr[1]
                    if path_rel.startswith('abs_path=') or path_rel.startswith('relative_path='):
                        arr[1] = self.if_path_is_rel(path_rel)
                if len(arr) > 2:
                    if arr[2].startswith('http') or arr[2].startswith('"http'):
                        finalUrl = []
                        finalUrl.append(arr[1])
                        finalUrl.append(arr[2])
                        refererNeeded = True
                    else:
                        finalUrl = arr[1]
                        refererNeeded = False
                else:
                    finalUrl = arr[1]
                    refererNeeded = False
                self.epn_name_in_list = arr[0]
                epn = self.epn_name_in_list
                self.playlistUpdate()
                self.list2.setCurrentRow(row)
                if 'youtube.com' in finalUrl:
                    finalUrl = get_yt_url(finalUrl, quality, self.ytdl_path, logger).strip()
                #self.external_url = self.get_external_url_status(finalUrl)
        
        self.adjust_thumbnail_window(row)
            
        if site == "None" or site == "Music" or site == "Video" or site == 'MyServer':
            
            if '	' in self.epn_arr_list[row]:
                    finalUrl = '"'+(self.epn_arr_list[row]).split('	')[1]+'"'
            else:
                    finalUrl = '"'+(self.epn_arr_list[row]).replace('#', '', 1)+'"'
            if self.list3.currentItem():
                if site.lower() == 'music' and self.list3.currentItem().text().lower() == 'playlist':
                    path_rel = finalUrl.replace('"', '')
                    if path_rel.startswith('abs_path=') or path_rel.startswith('relative_path='):
                        finalUrl = '"'+self.if_path_is_rel(path_rel)+'"'
            logger.info('--line--15803--{0}'.format(finalUrl))
            i = str(self.list2.item(row).text())
            if not i.startswith(self.check_symbol):
                self.list2.item(row).setText(self.check_symbol+i)
            else:
                self.list2.item(row).setText(i)
            #self.list2.item(row).setFont(QtGui.QFont('SansSerif', 10, italic=True))
            self.list2.setCurrentRow(row)
            if 'youtube.com' in finalUrl.lower():
                finalUrl = finalUrl.replace('"', '')
                finalUrl = get_yt_url(finalUrl, quality, self.ytdl_path, logger).strip()
            self.external_url = self.get_external_url_status(finalUrl)
            #if not self.external_url:
            #finalUrl = self.get_redirected_url_if_any(finalUrl, self.external_url)
        new_epn = self.epn_name_in_list
    
        finalUrl = finalUrl.replace('"', '')
        finalUrl = '"'+finalUrl+'"'
        try:
            finalUrl = str(finalUrl, 'utf-8')
        except:
            finalUrl = finalUrl
            
        if self.mpvplayer_val.processId() > 0:
            if Player == "mplayer":
                command = self.mplayermpv_command(idw, finalUrl, Player, a_id=audio_id, s_id=sub_id)
                if not self.external_url and self.mpvplayer_started:
                    #try:
                    epnShow = '"' + "Queued:  "+ new_epn + '"'
                    t1 = bytes('\n '+'show_text '+(epnShow)+' \n', 'utf-8')
                    t2 = bytes('\n '+"loadfile "+(finalUrl)+" replace"+' \n', 'utf-8')
                    logger.info(t2)
                    self.mpvplayer_val.write(t2)
                    self.mpvplayer_val.write(t1)
                    if self.mplayer_SubTimer.isActive():
                        self.mplayer_SubTimer.stop()
                    self.mplayer_SubTimer.start(2000)
                else:
                    self.mpvplayer_val.kill()
                    self.mpvplayer_started = False
                    self.infoPlay(command)
                    #self.external_url = False
                    logger.info(command)
            elif Player == "mpv":
                command = self.mplayermpv_command(idw, finalUrl, Player, a_id=audio_id, s_id=sub_id)
                if not self.external_url and self.mpvplayer_started:
                    epnShow = '"' + "Playing:  "+ new_epn + '"'
                    t1 = bytes('\n '+'show-text '+epnShow+' \n', 'utf-8')
                    t2 = bytes('\n '+"loadfile "+finalUrl+' \n', 'utf-8')
                    self.mpvplayer_val.write(t2)
                    self.mpvplayer_val.write(t1)
                    logger.info(t2)
                else:
                    self.mpvplayer_val.kill()
                    self.mpvplayer_started = False
                    self.infoPlay(command)
                    #self.external_url = False
                    logger.info(command)
            
            print("mpv=" + str(self.mpvplayer_val.processId()))
        else:
            command = self.mplayermpv_command(idw, finalUrl, Player, a_id=audio_id, s_id=sub_id)
            self.infoPlay(command)
        
            print("mpv=" + str(self.mpvplayer_val.processId()))
            
        if finalUrl.startswith('"'):
            current_playing_file_path = finalUrl.replace('"', '')
        else:
            current_playing_file_path = finalUrl
                
        self.paste_background(row)
    
    def paste_background(self, row):
        global site, artist_name_mplayer
        
        try:
            if site == "Music":
                try:
                    artist_name_mplayer = self.epn_arr_list[row].split('	')[2]
                    if artist_name_mplayer.lower() == "none" or 'http' in artist_name_mplayer:
                        artist_name_mplayer = ""
                except:
                    artist_name_mplayer = ""
                if artist_name_mplayer:
                    self.media_data.update_music_count('count', finalUrl)
                    self.musicBackground(row, 'Search')
                else:
                    try:
                        thumb_path = self.get_thumbnail_image_path(row, self.epn_arr_list[row])
                        logger.info("thumbnail path = {0}".format(thumb_path))
                        if os.path.exists(thumb_path):
                            self.videoImage(thumb_path, thumb_path, thumb_path, '')
                    except Exception as e:
                        logger.info('Error in getting Thumbnail: {0}'.format(e))
            elif site.lower() == 'video' or site.lower() == 'local' or site.lower() == 'playlists':
                if site == "Video":
                    self.media_data.update_video_count('mark', finalUrl, rownum=row)
                try:
                    thumb_path = self.get_thumbnail_image_path(row, self.epn_arr_list[row])
                    logger.info("thumbnail path = {0}".format(thumb_path))
                    if os.path.exists(thumb_path):
                        self.videoImage(thumb_path, thumb_path, thumb_path, '')
                except Exception as e:
                    logger.info('Error in getting Thumbnail -14179- epnfound: {0}'.format(e))
            else:
                try:
                    thumb_path = self.get_thumbnail_image_path(row, self.epn_arr_list[row])
                    logger.info("thumbnail path = {0}".format(thumb_path))
                    if os.path.exists(thumb_path):
                        self.videoImage(thumb_path, thumb_path, thumb_path, '')
                except Exception as e:
                    logger.info('Error in getting Thumbnail: {0}'.format(e))
        except Exception as e:
            print(e, '--14180--')
        
    def getQueueInList(self):
        global curR, site, epn_name_in_list, artist_name_mplayer, idw
        global sub_id, audio_id, Player, server, current_playing_file_path, quality
        try:
            t1 = self.queue_url_list[0]
            server._emitMeta("queue"+'#'+t1, site, self.epn_arr_list)
        except:
            pass
        self.external_url = False
        #print(self.list6.item(0).text(), self.queue_url_list)
        if self.if_file_path_exists_then_play(0, self.list6, True):
            del self.queue_url_list[0]
            self.list6.takeItem(0)
            del t1
            return 0
        
        if (site == "Local" or site == "Video" or site == "Music" 
                or site == "PlayLists" or site == "None" or site == 'MyServer'):
            t = self.queue_url_list[0]
            epnShow = '"'+t.split('	')[1]+'"'
            self.epn_name_in_list = t.split('	')[0]
            if self.epn_name_in_list.startswith('#'):
                self.epn_name_in_list = self.epn_name_in_list[1:]
            if site == "Music":
                artist_name_mplayer = t.split('	')[2]
                if artist_name_mplayer == "None":
                    artist_name_mplayer = ""
            del self.queue_url_list[0]
            t1 = self.list6.item(0)
            self.list6.takeItem(0)
            del t1
            if not idw:
                idw = str(int(self.tab_5.winId()))
            if 'youtube.com' in epnShow.lower():
                finalUrl = epnShow.replace('"', '')
                finalUrl = get_yt_url(finalUrl, quality, self.ytdl_path, logger).strip()
                epnShow = finalUrl
            self.external_url = self.get_external_url_status(epnShow)
            #if not self.external_url and Player == 'mplayer':
            #	finalUrl = self.get_redirected_url_if_any(finalUrl, self.external_url)
        else:
            epnShow = self.queue_url_list.pop()
            curR = curR - 1
            print('--------inside getQueueInlist------')
            self.list2.setCurrentRow(curR)
            
        
        epnShowN = '"'+epnShow.replace('"', '')+'"'
        command = self.mplayermpv_command(idw, epnShowN, Player, a_id=audio_id, s_id=sub_id)
        if self.mpvplayer_val.processId() > 0:
            epnShow = '"'+epnShow.replace('"', '')+'"'
            t2 = bytes('\n '+"loadfile "+epnShow+" replace"+' \n', 'utf-8')
            
            if Player == 'mpv':
                if not self.external_url:
                    self.mpvplayer_val.write(t2)
                    logger.info(t2)
                else:
                    self.mpvplayer_val.write(b'\n quit \n')
                    self.infoPlay(command)
                    #self.external_url = False
                    logger.info(command)
            elif Player == "mplayer":
                if not self.external_url:
                    self.mpvplayer_val.write(t2)
                    logger.info(t2)
                    if self.mplayer_SubTimer.isActive():
                        self.mplayer_SubTimer.stop()
                    self.mplayer_SubTimer.start(2000)
                else:
                    self.mpvplayer_val.kill()
                    self.mpvplayer_started = False
                    self.infoPlay(command)
                    #self.external_url = False
                    logger.info(command)
        else:
            logger.info(command)
            self.infoPlay(command)
            self.list1.hide()
            self.frame.hide()
            self.text.hide()
            self.label.hide()
            self.tab_5.show()
        
        epnShow = epnShow.replace('"', '')
        if not epnShow.startswith('http'):
            if site == "Music":
                self.media_data.update_music_count('count', epnShowN)
                self.musicBackground(0, 'Queue')
            elif site == "Video":
                self.media_data.update_video_count('mark', epnShowN)
                logger.info('{0}--mark-video-queue----13147--'.format(epnShowN))
        if epnShow.startswith('http'):
            current_playing_file_path = epnShow
        else:
            current_playing_file_path = '"'+epnShow+'"'
        
    def mplayermpv_command(self, idw, finalUrl, player, a_id=None, s_id=None, rfr=None, a_url=None):
        global site
        finalUrl = finalUrl.replace('"', '')
        aspect_value = self.mpvplayer_aspect.get(str(self.mpvplayer_aspect_cycle))
        if player == 'mplayer':
            if finalUrl.startswith('http'):
                command = 'mplayer -idle -identify -msglevel statusline=5:global=6 -cache 100000 -cache-min 0.001 -cache-seek-min 0.001 -osdlevel 0 -slave -wid {0}'.format(idw)
            else:
                command = 'mplayer -idle -identify -msglevel statusline=5:global=6 -nocache -osdlevel 0 -slave -wid {0}'.format(idw)
        elif player == "mpv":
            command = 'mpv --cache-secs=120 --cache=auto --cache-default=100000 --cache-initial=0 --cache-seek-min=100 --cache-pause --idle -msg-level=all=v --osd-level=0 --cursor-autohide=no --no-input-cursor --no-osc --no-osd-bar --ytdl=no --input-file=/dev/stdin --input-terminal=no --input-vo-keyboard=no -video-aspect {0} -wid {1}'.format(aspect_value, idw)
        else:
            command = Player
        if a_id:
            if a_id == "auto":
                if player == 'mplayer':
                    command = command+" -aid 0"
                elif player == 'mpv':
                    command = command+" -aid auto"
            else:
                command = command+" -aid {0}".format(a_id)
            
        if s_id:
            if s_id == "auto":
                if player == 'mplayer':
                    command = command+" -sid 0"
                elif player == 'mpv':
                    command = command+" -sid auto"
            else:
                command = command+" -sid {0}".format(s_id)
                
        if rfr:
            if player == 'mplayer':
                command = command+" -referrer {0}".format(rfr)
            elif player == 'mpv':
                command = command+" --referrer={0}".format(rfr)
                
        if a_url:
            if player == 'mplayer':
                command = command+" -audiofile {0}".format(a_url)
            elif player == 'mpv':
                command = command+" --audio-file={0}".format(a_url)
        
        if site.lower() == 'music':
            if player == 'mpv':
                command = command + ' --no-video'
            elif player == 'mplayer':
                command = command + ' -novideo'
        
        if finalUrl:
            if self.quality_val == 'best':
                if 'youtube.com' in finalUrl and player == 'mpv':
                    if site.lower() == 'music':
                        final_url = get_yt_url(finalUrl, self.quality_val, self.ytdl_path, logger, mode="music").strip()
                        finalUrl = final_url.split('::')[-1]
                    else:
                        command = command.replace('ytdl=no', 'ytdl=yes')
                elif 'youtube.com' in finalUrl and player == 'mplayer':
                    finalUrl = get_yt_url(finalUrl, self.quality_val, self.ytdl_path, logger, mode="offline").strip()
            if finalUrl.startswith('http'):
                command = command + ' ' + finalUrl
            else:
                finalUrl = '"'+ finalUrl + '"'
                command = command + ' ' + finalUrl
        else:
            command = ''
        return command
        
    def getNextInList(self):
        global site, base_url, embed, epn, epn_goto, mirrorNo, list2_items, quality
        global finalUrl, curR, home, buffering_mplayer, epn_name_in_list
        global opt_movies_indicator, audio_id, sub_id, siteName, rfr_url
        global mpv, mpvAlive, indexQueue, Player, startPlayer
        global new_epn, path_Local_Dir, Player, curR
        global fullscr, thumbnail_indicator, category, finalUrlFound, refererNeeded
        global server, current_playing_file_path, default_arr_setting
        global music_arr_setting, video_local_stream, wget
        
        row = self.list2.currentRow()
        self.total_file_size = 0
        self.mplayerLength = 0
        buffering_mplayer = "no"
        
        try:
            server._emitMeta("Next", site, self.epn_arr_list)
        except:
            pass
        
        if self.if_file_path_exists_then_play(row, self.list2, True):
            self.adjust_thumbnail_window(row)
            return 0
        
        if site != "PlayLists":
            if '	' in self.epn_arr_list[row]:
                epn = self.epn_arr_list[row].split('	')[1]
                self.epn_name_in_list = (self.epn_arr_list[row]).split('	')[0]
            else:
                epn = str(self.list2.currentItem().text())
                self.epn_name_in_list = (epn)
                epn = self.epn_arr_list[row]
            if not epn:
                return 0
            epn = epn.replace('#', '', 1)
        else:
            row = self.list2.currentRow()
            item = self.list2.item(row)
            if item:
                line = str(self.list2.currentItem().text())
                
                arr = self.epn_arr_list[row].split('	')
                    
                if arr[2].startswith('http') or arr[2].startswith('"http'):
                    finalUrl = []
                    finalUrl.append(arr[1])
                    finalUrl.append(arr[2])
                    refererNeeded = True
                else:
                    finalUrl = arr[1]
                    refererNeeded = False
                
                self.epn_name_in_list = arr[0]
                epn = self.epn_name_in_list
                self.playlistUpdate()
                self.list2.setCurrentRow(row)
                if 'youtube.com' in finalUrl:
                    finalUrl = get_yt_url(finalUrl, quality, self.ytdl_path, logger).strip()
        
        self.adjust_thumbnail_window(row)
        
        self.set_init_settings()
        
        if (site != "SubbedAnime" and site!= "DubbedAnime" and site!="PlayLists" 
                and finalUrlFound == False and site!="None" and site!="Music" 
                and site!= "Video" and site!="Local"):
            if opt == "History":
                self.mark_History()
            else:
                i = str(self.list2.item(row).text())
                if not self.check_symbol in i:
                    self.list2.item(row).setText(self.check_symbol+i)
                else:
                    self.list2.item(row).setText(i)
                #self.list2.item(row).setFont(QtGui.QFont('SansSerif', 10, italic=True))
                self.list2.setCurrentRow(row)
                
            if site != "Local":
                try:
                    print(site)
                except:
                    return 0
                self.progressEpn.setFormat('Wait..')
                try:
                    if video_local_stream:
                        if self.thread_server.isRunning():
                            if self.do_get_thread.isRunning():
                                if self.https_media_server:
                                    https_val = 'https'
                                else:
                                    https_val = 'http'
                                finalUrl = https_val+"://"+self.local_ip+':'+str(self.local_port)+'/'
                                if self.torrent_handle.file_priority(row):
                                    self.start_torrent_stream(name, row, self.local_ip+':'+str(self.local_port), 'Get Next', self.torrent_download_folder, self.stream_session)
                                else:
                                    if Player == 'mplayer':
                                        self.mpvplayer_val.write(b'\n quit \n')
                            else:
                                finalUrl, self.do_get_thread, self.stream_session, self.torrent_handle = self.start_torrent_stream(name, row, self.local_ip+':'+str(self.local_port), 'Already Running', self.torrent_download_folder, self.stream_session)
                        else:
                            finalUrl, self.thread_server, self.do_get_thread, self.stream_session, self.torrent_handle = self.start_torrent_stream(name, row, self.local_ip+':'+str(self.local_port), 'First Run', self.torrent_download_folder, self.stream_session)
                        self.torrent_handle.set_upload_limit(self.torrent_upload_limit)
                        self.torrent_handle.set_download_limit(self.torrent_download_limit)
                    else:
                        finalUrl = self.site_var.getFinalUrl(name, epn, mirrorNo, quality)
                except Exception as e:
                    print(e)
                    self.progressEpn.setFormat('Load Failed!')
                    print('final url not found')
                    return 0
        elif finalUrlFound == True:
                row_num = self.list2.currentRow()
                final = self.epn_arr_list[row_num]
                logger.info(final)
                self.mark_History()
                finalUrl = []
                if '	' in final:
                    final = final.replace('#', '', 1)
                    final = final.split('	')[1]
                else:
                    final=re.sub('#', '', final)
                finalUrl.append(final)
                if refererNeeded == True:
                    if '	' in self.epn_arr_list[-1]:
                        rfr_url = self.epn_arr_list[-1].split('	')[1]
                    else:
                        rfr_url = self.epn_arr_list[-1]
                    logger.info(rfr_url)
                    finalUrl.append(rfr_url)
                if len(finalUrl) == 1:
                    finalUrl = finalUrl[0]
        elif site == "SubbedAnime" or site == "DubbedAnime":
            if category != "Movies":
                self.mark_History()
            if site == "SubbedAnime":
                code = 6
                if base_url == 16:
                    epn_t = epn.split(' ')[1]
                    new_epn = epn.split(' ')[0]
                else:
                    epn_t = epn
                if opt_movies_indicator:
                    r = self.list2.currentRow()
                    self.epn_name_in_list = name+'-'+self.list2.currentItem().text()
                    
                    if self.site_var:
                        self.progressEpn.setFormat('Wait..')
                        QtWidgets.QApplication.processEvents()
                        try:
                            finalUrl = self.site_var.urlResolve(self.epn_arr_list[r].split('	')[1])
                        except Exception as e:
                            print(e)
                            return 0
                else:
                    if self.site_var:
                        self.progressEpn.setFormat('Wait..')
                        QtWidgets.QApplication.processEvents()
                        try:
                            finalUrl = self.site_var.getFinalUrl(
                                siteName, name, epn, mirrorNo, category, quality
                                ) 
                        except Exception as e:
                            print(e)
                            return 0
            elif site == "DubbedAnime":
                code = 5
                if self.site_var:
                    self.progressEpn.setFormat('Wait..')
                    QtWidgets.QApplication.processEvents()
                    try:
                        finalUrl = self.site_var.getFinalUrl(
                            siteName, name, epn, mirrorNo, quality
                            ) 
                    except Exception as e:
                        print(e)
                        return 0
        elif site == "None" or site == "Music" or site == "Video" or site == "Local":
            if opt == "History" and site == "Local":
                self.mark_History()
            if '	' in self.epn_arr_list[row]:
                    finalUrl = '"'+(self.epn_arr_list[row]).split('	')[1]+'"'
            else:
                    finalUrl = '"'+(self.epn_arr_list[row]).replace('#', '', 1)+'"'
            logger.info(finalUrl)
            i = str(self.list2.item(row).text())
            if not i.startswith(self.check_symbol):
                self.list2.item(row).setText(self.check_symbol+i)
            else:
                self.list2.item(row).setText(i)
            #self.list2.item(row).setFont(QtGui.QFont('SansSerif', 10, italic=True))
            self.list2.setCurrentRow(row)
            if site == "Music":
                if 'youtube.com' not in finalUrl.lower():
                    self.media_data.update_music_count('count', finalUrl)
            if 'youtube.com' in finalUrl.lower():
                finalUrl = finalUrl.replace('"', '')
                finalUrl = get_yt_url(finalUrl, quality, self.ytdl_path, logger).strip()
                finalUrl = '"'+finalUrl+'"'
                
        new_epn = self.epn_name_in_list
        
        if (site == "Local" or site == "Video" or site == "Music" 
                or site == "None" or site == "PlayLists"):
            if type(finalUrl) is list:
                finalUrl = finalUrl[0]
            finalUrl = finalUrl.replace('"', '')
            finalUrl = '"'+finalUrl+'"'
            try:
                finalUrl = str(finalUrl)
            except:
                finalUrl = finalUrl
                
            command = self.mplayermpv_command(idw, finalUrl, Player, a_id=audio_id, s_id=sub_id)
            print("mpv=" + str(self.mpvplayer_val.processId()))
            logger.info(command)
            if self.mpvplayer_val.processId() > 0 :
                self.mpvplayer_val.kill()
                self.mpvplayer_started = False
            self.infoPlay(command)
        else:
            if isinstance(finalUrl, list):
                rfr_exists = finalUrl[-1]
                rfr_needed = False
                if rfr_exists == 'referer sent':
                    rfr_needed = True
                    finalUrl.pop()
                if self.mpvplayer_val:
                    if self.mpvplayer_val.processId() > 0:
                        if refererNeeded == "True":
                            finalUrl.pop()
                        epnShow = '"'+finalUrl[0]+'"'
                        t2 = bytes('\n'+"loadfile "+epnShow+" replace"+'\n', 'utf-8')
                        self.mpvplayer_val.write(t2)
                        self.queue_url_list[:]=[]
                        for i in range(len(finalUrl)-1):
                            epnShow ='"'+finalUrl[i+1]+'"'
                            self.queue_url_list.append(finalUrl[i+1])
                        self.queue_url_list.reverse()
                        logger.info('---hello-----{0}'.format(finalUrl))
                    else:
                        if finalUrlFound == True or site=="PlayLists" or rfr_needed:
                            if refererNeeded == True or rfr_needed:
                                rfr_url = finalUrl[1]
                                nepn = str(finalUrl[0])
                                epnShow = str(nepn)
                                command = self.mplayermpv_command(idw, nepn, Player, rfr=rfr_url)
                                
                            else:
                                nepn = str(finalUrl[0])
                                epnShow = nepn
                                command = self.mplayermpv_command(idw, nepn, Player)
                                
                        else:
                            self.queue_url_list[:]=[]
                            epnShow = finalUrl[0]
                            for i in range(len(finalUrl)-1):
                                self.queue_url_list.append(finalUrl[i+1])
                            self.queue_url_list.reverse()
                            command = self.mplayermpv_command(idw, epnShow, Player)
                            
                        logger.info(command)
                        if self.mpvplayer_val.processId() > 0:
                            self.mpvplayer_val.kill()
                            self.mpvplayer_started = False
                        self.infoPlay(command)
            else:
                finalUrl = finalUrl.replace('"', '')
                self.external_url = self.get_external_url_status(finalUrl)
                try:
                    finalUrl = str(finalUrl)
                except:
                    finalUrl = finalUrl
                command = self.mplayermpv_command(idw, finalUrl, Player, a_id=audio_id, s_id=sub_id)
                
                print("mpv=" + str(self.mpvplayer_val.processId()))
                print(Player, '---------state----'+str(self.mpvplayer_val.state()))
                
                if self.mpvplayer_val.processId() > 0:
                    self.mpvplayer_val.kill()
                    self.mpvplayer_started = False
                self.infoPlay(command)
                
        if not isinstance(finalUrl, list):
            self.final_playing_url = finalUrl.replace('"', '')
            if self.final_playing_url.startswith('http'):
                current_playing_file_path = self.final_playing_url
            else:
                current_playing_file_path = '"'+self.final_playing_url+'"'
        else:
            self.final_playing_url = finalUrl[0].replace('"', '')
            if refererNeeded == True:
                rfr_url = finalUrl[1].replace('"', '')
    
    def play_video_url(self, player, url):
        print('hello')
    
    def getList(self):
        global nameListArr, opt
        self.list1.clear()
        opt = "Random" 
        self.original_path_name[:] = []
        for i in nameListArr:
            i = i.strip()
            j = i
            if '	' in i:
                i = i.split('	')[0]
            self.list1.addItem(i)
            self.original_path_name.append(j)
            
    def update_playlist_original(self, pls):
        self.list2.clear()
        file_path = pls
        if os.path.exists(file_path):
            write_files(file_path, self.epn_arr_list, line_by_line=True)
            self.update_list2()
            
    def update_playlist(self, pls):
        file_path = pls
        if os.path.exists(file_path):
            index = self.btn1.findText('PlayLists')
            if index >= 0:
                self.btn1.setCurrentIndex(index)
                
        if os.path.exists(file_path) and self.btn1.currentText().lower() == 'youtube':
            self.list2.clear()
            self.epn_arr_list[:]=[]
            lines = open_files(file_path, True)
            for i in lines:
                i = i.replace('\n', '')
                if i:
                    self.epn_arr_list.append(i)
            self.update_list2()
        elif os.path.exists(file_path) and self.btn1.currentText().lower() == 'playlists':
            pl_name = os.path.basename(file_path)
            if not self.list1.currentItem():
                self.list1.setCurrentRow(0)
            if self.list1.currentItem().text() != pl_name:  
                for i in range(self.list1.count()):
                    item = self.list1.item(i)
                    if item.text() == pl_name:
                        self.list1.setCurrentRow(i)
                        break
            else:
                lines = open_files(file_path, True)
                new_epn = lines[-1].strip()
                self.epn_arr_list.append(new_epn)
                new_epn_title = new_epn.split('	')[0]
                if new_epn_title.startswith('#'):
                    new_epn_title = new_epn_title.replace('#', self.check_symbol, 1)
                self.list2.addItem(new_epn_title)
                
    def newoptions(self, val=None):
        if self.options_mode == 'legacy':
            self.options(val)
        else:
            self.newoptionmode(val)
            
    def newoptionmode(self, val):
        global opt, home, site, list1_items, pgn
        t_opt = "History"
        print(val, '----clicked---', type(val))
        if val == "clicked":
            r = self.list3.currentRow()
            item = self.list3.item(r)
            if item:
                t_opt = str(self.list3.currentItem().text())
        elif val == "history":
            t_opt = "History"
        opt = t_opt
        self.line.clear()
        self.list2.clear()
        if t_opt == "History" and site.lower() != 'myserver':
            self.list1.clear()
            opt = t_opt
            file_path = os.path.join(home, 'History', site, 'history.txt')
            if os.path.isfile(file_path):
                lines = open_files(file_path, True)
                lins = open_files(file_path, True)
                list1_items[:] = []
                list2_items[:] = []
                self.original_path_name[:] = []
                for i in lins:
                    i = i.strip()
                    j = i
                    if '	' in i:
                        i = i.split('	')[0]
                    self.list1.addItem(i)
                    list1_items.append(i)
                    list2_items.append(i)
                    self.original_path_name.append(j)
                self.forward.hide()
                self.backward.hide()
        else:
            self.text.setText('Wait...Loading')
            QtWidgets.QApplication.processEvents()
            try:
                m = self.site_var.getCompleteList(t_opt, genre_num)
                self.text.setText('Load Complete!')
            except Exception as e:
                print(e)
                m = []
                self.text.setText('Load Failed!')
                return 0
            opt = t_opt
            list_1 = list_2 = list_3 = False
            if m:
                if m[-1] == 0:
                    list_3 = True
                    m.pop()
                elif m[-1] == 1:
                    list_1 = True
                    m.pop()
                elif m[-1] == 2:
                    list_3 = True
                    m.pop()
                elif m[-1] == 3 or m[-1] == 5:
                    mval = m.pop()
                    self.myserver_cache.clear()
                    if mval == 3:
                        self.text.setText('Login Required')
                    else:
                        self.text.setText('Logged out')
                    return 0
                elif m[-1] == 4:
                    m.pop()
                    if site.lower() == 'myserver' and opt.lower() == 'discover':
                        if not self.discover_thread:
                            self.discover_thread = DiscoverServer(self, True)
                            self.discover_thread.start()
                        elif isinstance(self.discover_thread, DiscoverServer):
                            if not self.discover_thread.isRunning():
                                self.discover_thread = DiscoverServer(self, True)
                                self.discover_thread.start()
                            else:
                                self.discover_server = False
                    return 0
                        
            if not list_1 and not list_2 and not list_3:
                list_1 = True
            if list_3:
                self.list1.clear()
                self.list3.clear()
                for i in m:
                    self.list3.addItem(i)
                self.forward.hide()
                self.backward.hide()
            elif list_1:
                self.list1.clear()
                list1_items[:] = []
                self.original_path_name[:] = []
                for i in m:
                    i = i.strip()
                    if '	' in i:
                        j = i.split('	')[0]
                    else:
                        j = i
                    self.list1.addItem(j)
                    self.original_path_name.append(i)
                self.forward.show()
                self.backward.show()
            elif list_2:
                self.list1.clear()
                self.epn_arr_list.clear()
                for i in m:
                    if '\t' in i:
                        j = i.split('\t')[0]
                    self.list2.addItem(j)
                    self.epn_arr_list.append(i)
                self.forward.hide()
                self.backward.hide()
        
    def options(self, val=None):
        global opt, pgn, genre_num, site, name, base_url, name1, embed, list1_items
        global pre_opt, mirrorNo, insidePreopt, quality, home, siteName, finalUrlFound
        global nameListArr, show_hide_playlist, show_hide_titlelist
        global pict_arr, name_arr, summary_arr, total_till, browse_cnt, tmp_name
        global hist_arr, list2_items, bookmark, status, viewMode, video_local_stream
        
        hist_arr[:]=[]
        pict_arr[:]=[]
        name_arr[:]=[]
        summary_arr[:]=[]
        browse_cnt=0
        tmp_name[:]=[]
        list2_items=[]
        list1_items[:]=[]
        
        if bookmark:
            r = self.list3.currentRow()
            item = self.list3.item(r)
            if item:
                opt = item.text()
                
                if opt == "All":
                    status = "bookmark"
                else:
                    status = opt
                
                book_path = os.path.join(home, 'Bookmark', status+'.txt')
                if not os.path.isfile(book_path):
                    f = open(book_path, 'w')
                    f.close()
                else:
                    self.setPreOpt()
        elif (site!="Local" and site != "Music" and site != "SubbedAnime" 
                and site!= "DubbedAnime" and site!="PlayLists" and site!="Video"):
            t_opt = "History"
            print(val, '----clicked---', type(val))
            if val == "clicked":
                r = self.list3.currentRow()
                item = self.list3.item(r)
                if item:
                    t_opt = str(self.list3.currentItem().text())
            elif val == "history":
                t_opt = "History"
            opt = t_opt
            self.line.clear()
            self.list1.clear()
            self.list2.clear()
            #opt = str(opt)
            if (t_opt == "Genre") and (genre_num == 0):
                self.list3.clear()
                self.text.setText('Wait...Loading')
                QtWidgets.QApplication.processEvents()
                try:
                    m = self.site_var.getCompleteList(t_opt, genre_num)
                    self.text.setText('Load Complete!')
                except Exception as e:
                    print(e)
                    self.text.setText('Load Failed!')
                    return 0
                genre_num = 1
                opt = t_opt
                for i in m:
                    self.list3.addItem(i)
                #del site_var
            elif t_opt == "History":
                genre_num = 0
                opt = t_opt
                file_path = os.path.join(home, 'History', site, 'history.txt')
                if os.path.isfile(file_path):
                    lines = open_files(file_path, True)
                    lins = open_files(file_path, True)
                    list1_items = []
                    self.original_path_name[:] = []
                    for i in lins:
                        i = i.strip()
                        j = i
                        if '	' in i:
                            i = i.split('	')[0]
                        self.list1.addItem(i)
                        list1_items.append(i)
                        list2_items.append(i)
                        self.original_path_name.append(j)
                    self.forward.hide()
                    self.backward.hide()
            elif (t_opt == "MostPopular") or (t_opt == "Newest") or (t_opt == "LatestUpdate"):
                genre_num = 0
                pgn = 1
                self.text.setText('Wait...Loading')
                QtWidgets.QApplication.processEvents()
                try:
                    m = self.site_var.getCompleteList(t_opt, genre_num)
                    self.text.setText('Load Complete!')
                except Exception as e:
                    print(e)
                    self.text.setText('Load Failed!')
                    return 0
                list1_items = m
                self.original_path_name[:]=[]
                for i in m:
                    i = i.strip()
                    if '	' in i:
                        j = i.split('	')[0]
                    else:
                        j = i
                    self.list1.addItem(j)
                    self.original_path_name.append(i)
                self.forward.show()
                self.backward.show()
            elif genre_num == 1:
                    pgn = 1
                    self.text.setText('Wait...Loading')
                    QtWidgets.QApplication.processEvents()
                    try:
                        m = self.site_var.getCompleteList(t_opt, genre_num)
                        self.text.setText('Load Complete!')
                    except Exception as e:
                        print(e)
                        self.text.setText('Load Failed!')
                        return 0
                        
                    list1_items[:] = []
                    self.original_path_name[:]=[]
                    for i in m:
                        i = i.strip()
                        if '	' in i:
                            j = i.split('	')[0]
                        else:
                            j = i
                        self.list1.addItem(j)
                        self.original_path_name.append(i)
                        list1_items.append(j)
                    self.forward.show()
                    self.backward.show()
            else:
                opt = t_opt
                self.text.setText('Wait...Loading')
                QtWidgets.QApplication.processEvents()
                try:
                    if video_local_stream:
                        history_folder = os.path.join(home, 'History', site)
                        if not os.path.exists(history_folder):
                            os.makedirs(history_folder)
                        m = self.site_var.getCompleteList(
                                t_opt, self.list6, self.progress, 
                                self.tmp_download_folder, history_folder
                                )
                    else:
                        m = self.site_var.getCompleteList(t_opt, 0)
                    self.text.setText('Load Complete!')
                except Exception as e:
                    print(e)
                    self.text.setText('Load Failed!')
                    return 0
                list1_items[:] = []
                self.original_path_name[:]=[]
                for i in m:
                    i = i.strip()
                    if '	' in i:
                        j = i.split('	')[0]
                    else:
                        j = i
                    self.list1.addItem(j)
                    list1_items.append(j)
                    self.original_path_name.append(i)
                    
                self.forward.hide()
                self.backward.hide()
        elif site == "SubbedAnime" or site == "DubbedAnime":
            code = 2
            siteName = str(self.list3.currentItem().text())
            if val == "clicked":
                
                opt = "Random"
            else:
                opt = "History"
            
            self.original_path_name[:]=[]
            if opt == "History":
                    file_path = os.path.join(home, 'History', site, siteName, 'history.txt')
                    if os.path.isfile(file_path):
                        lines = open_files(file_path, True)
                        self.label.clear()
                        self.line.clear()
                        self.list1.clear()
                        self.list2.clear()
                        self.text.clear()
                        self.original_path_name[:]=[]
                        for i in lines:
                            i = i.strip()
                            if '	' in i:
                                j = i.split('	')[0]
                            else:
                                j = i
                            self.list1.addItem(j)
                            self.original_path_name.append(i)
                            
            if opt != "History":
                self.label.clear()
                self.line.clear()
                self.list1.clear()
                self.list2.clear()
                
                if self.site_var:
                    self.text.setText('Wait...Loading')
                    QtWidgets.QApplication.processEvents()
                    try:
                        m = self.site_var.getCompleteList(siteName, category, opt) 
                        self.text.setText('Load Complete!')
                    except Exception as e:
                        print(e)
                        self.text.setText('Load Failed!')
                        return 0
                list1_items[:] = []
                self.original_path_name[:]=[]
                for i in m:
                    i = i.strip()
                    if '	' in i:
                        j = i.split('	')[0]
                    else:
                        j = i
                    self.list1.addItem(j)
                    self.original_path_name.append(i)
                    list1_items.append(j)
        elif site == "Music":
            global update_start
            music_dir = os.path.join(home, 'Music')
            if not os.path.exists(music_dir):
                os.makedirs(music_dir)
            music_db = os.path.join(home, 'Music', 'Music.db')
            music_file = os.path.join(home, 'Music', 'Music.txt')
            music_file_bak = os.path.join(home, 'Music', 'Music_bak.txt')
            if not os.path.exists(music_db):
                self.media_data.create_update_music_db(music_db, music_file, music_file_bak)
                update_start = 1
            elif not update_start:
                self.text.setText('Wait..Checking New Files')
                QtWidgets.QApplication.processEvents()
                QtCore.QTimer.singleShot(
                    1000, partial(self.media_data.update_on_start_music_db, 
                    music_db, music_file, music_file_bak))
                update_start = 1
                self.text.clear()
            if self.list3.currentItem():
                music_opt = str(self.list3.currentItem().text())
            else:
                music_opt = ""
            print(music_opt)
            
            artist =[]
            if music_opt == "Playlist":
                pls = os.path.join(home, 'Playlists')
                if os.path.exists(pls):
                    m = os.listdir(pls)
                    for i in m:
                        artist.append(i)
            else:
                m = self.media_data.get_music_db(music_db, music_opt, "")
                for i in m:
                    artist.append(i[0])
            self.list1.clear()
            self.original_path_name[:] = []
            if (music_opt == "Artist" or music_opt == "Album" or music_opt == "Title" 
                    or music_opt == "Fav-Artist" or music_opt == "Fav-Album"):
                for i in artist:
                    self.original_path_name.append(i)
                    self.list1.addItem((i))
            elif music_opt == "Directory" or music_opt == "Fav-Directory":
                for i in artist:
                    self.original_path_name.append(i)
                    #i = i.split('/')[-1]
                    i = os.path.basename(i)
                    self.list1.addItem((i))
            elif music_opt == "Playlist":
                for i in artist:
                    self.original_path_name.append(os.path.join(home, 'Playlist', i))
                    self.list1.addItem((i))
            else:
                artist[:]=[]
                self.epn_arr_list[:]=[]
                self.list2.clear()
                for i in m:
                    self.epn_arr_list.append(str(i[1]+'	'+i[2]+'	'+i[0]))
                    #self.list2.addItem((i[1]))
                self.update_list2()
        elif site == "Video":
            video_dir = os.path.join(home, 'VideoDB')
            if not os.path.exists(video_dir):
                os.makedirs(video_dir)
            video_db = os.path.join(video_dir, 'Video.db')
            video_file = os.path.join(video_dir, 'Video.txt')
            video_file_bak = os.path.join(video_dir, 'Video_bak.txt')
            
            if self.list3.currentItem() and val != 'history':
                video_opt = str(self.list3.currentItem().text())
            else:
                video_opt = "History"
            print('----video-----opt', video_opt)
            if val == 'history' and video_opt == 'History':
                video_opt = "History"
            if not os.path.exists(video_db):
                self.media_data.create_update_video_db(video_db, video_file, video_file_bak)
            elif video_opt == "UpdateAll":
                self.media_data.update_on_start_video_db(video_db, video_file, video_file_bak, video_opt)
                video_opt = "Directory"
            elif video_opt == "Update":
                self.media_data.update_on_start_video_db(video_db, video_file, video_file_bak, video_opt)
                video_opt = "Directory"
            print(video_opt)
            if video_opt.lower() != 'update' and video_opt.lower() != 'updateall':
                opt = video_opt
            artist = []
            print('----video-----opt', video_opt)
            if video_opt == "Available":
                m = self.media_data.get_video_db(video_db, "Directory", "")
            elif video_opt == "History":
                m = self.media_data.get_video_db(video_db, "History", "")
            else:
                m = self.media_data.get_video_db(video_db, video_opt, "")
            #print m
            for i in m:
                artist.append(i[0]+'	'+i[1])
            #artist = list(set(artist))
            self.list1.clear()
            #print artist
            self.original_path_name[:] = []
            #artist = naturallysorted(artist)
            logger.info('\n{0}::\n'.format(video_opt))
            if video_opt.lower() != "update" or video_opt.lower() != "updateall":
                if video_opt.lower() == 'available':
                    show_all = False
                else:
                    show_all = True
                for i in artist:
                    ti = i.split('	')[0]
                    di = i.split('	')[1]
                    logger.info('{0} -- 10993--'.format(i))
                    if os.path.exists(di) or show_all:
                        #self.original_path_name.append(i)
                        if ti.lower().startswith('season') or ti.lower().startswith('special'):
                            new_di, new_ti = os.path.split(di)
                            logger.info('new_di={0}-{1}'.format(new_di, new_ti))
                            new_di = os.path.basename(new_di)
                            ti = new_di+'-'+ti
                            self.original_path_name.append(ti+'	'+di)
                        else:
                            self.original_path_name.append(i)
                        self.list1.addItem((ti))
                if video_opt.lower() != 'directory':
                    self.sortList()
            """
            elif video_opt == "Directory":
                for i in artist:
                    ti = i.split('	')[0]
                    di = i.split('	')[1]
                    #self.original_path_name.append(i)
                    if ti.lower().startswith('season') or ti.lower().startswith('special'):
                        new_di, new_ti = os.path.split(di)
                        logger.info('new_di={0}-{1}'.format(new_di, new_ti))
                        new_di = os.path.basename(new_di)
                        ti = new_di+'-'+ti
                        self.original_path_name.append(ti+'	'+di)
                    else:
                        self.original_path_name.append(i)
                    self.list1.addItem((ti))
            """
        elif site == "PlayLists" and val == 'clicked':
            if self.list3.currentItem():
                txt = self.list3.currentItem().text().lower()
                if txt == 'list':
                    criteria = os.listdir(os.path.join(home, 'Playlists'))
                    criteria.sort()
                    home_n = os.path.join(home, 'Playlists')
                    criteria = naturallysorted(criteria)
                    self.original_path_name[:] = []
                    self.list1.clear()
                    self.list2.clear()
                    for i in criteria:
                        self.list1.addItem(i)
                        self.original_path_name.append(i)
                elif txt == 'open file':
                    a = 0
                    print("add")
                    fname = QtWidgets.QFileDialog.getOpenFileNames(
                            MainWindow, 'Select One or More Files', self.last_dir)
                    if fname:
                        logger.info(fname)
                        if fname[0]:
                            self.last_dir, file_choose = os.path.split(fname[0][0])
                        self.list2.clear()
                        file_list = fname[0]
                        self.epn_arr_list[:] = []
                        for i in file_list:
                            j = os.path.basename(i)
                            if '.' in j:
                                k = j.rsplit('.', 1)[1]
                                if (k in self.music_type_arr 
                                        or k in self.video_type_arr or k == 'm3u'
                                        or k == 'pls'):
                                    if k != 'm3u' and k != 'pls':
                                        new_val = j+'	'+i+'	'+'NONE'
                                        self.epn_arr_list.append(new_val)
                                        self.list2.addItem(j)
                                    else:
                                        self.watch_external_video(i)
                        if self.epn_arr_list:
                            file_name = os.path.join(home, 'Playlists', 'TMP_PLAYLIST')
                            f = open(file_name, 'w').close()
                            write_files(file_name, self.epn_arr_list, True)
                            self.list1.clear()
                            self.list1.addItem('TMP_PLAYLIST')
                elif txt == 'open url':
                    item, ok = QtWidgets.QInputDialog.getText(
                        MainWindow, 'Input Dialog', 'Enter Url of External Media or Playlist')
                    if ok and item:
                        self.list2.clear()
                        self.list1.clear()
                        if item.startswith('http'):
                            self.watch_external_video(item)
                elif txt == 'open directory':
                    fname = QtWidgets.QFileDialog.getExistingDirectory(
                            MainWindow, 'Add Directory', self.last_dir)
                    if fname:
                        if os.path.exists(fname):
                            self.last_dir = fname
                            self.watch_external_video(fname)
        self.page_number.setText(str(self.list1.count()))
        insidePreopt = 0
        if opt == "History":
            for i in list2_items:
                hist_arr.append(i)
        
        if ((viewMode == "Thumbnail" or not self.tab_6.isHidden()) 
                and (opt == "History" or site == "Local" or bookmark 
                or site == "PlayLists")):
            if site == "NotMentioned":
                print("PlayLists")
            else:
                self.list1.hide()
                self.list2.hide()
                self.tab_5.hide()
                self.label.hide()
                self.text.hide()
                self.frame.hide()
                self.frame1.hide()
                self.goto_epn.hide()
                self.tab_6.show()
                self.tab_2.hide()
                self.scrollArea1.hide()
                self.scrollArea.show()
                
                if (opt == "History" or (site == "Local" or site == 'PlayLists') 
                        or bookmark):
                    i = 0
                    print(total_till, 2*self.list1.count()-1, '--count--')
                    if total_till > 0 and not self.lock_process:
                        if not self.scrollArea.isHidden():
                            self.next_page('deleted')
                        elif not self.scrollArea1.isHidden():
                            self.thumbnail_label_update()
                    elif total_till == 0:
                        if not self.scrollArea.isHidden():
                            self.next_page('deleted')
                        elif not self.scrollArea1.isHidden():
                            self.thumbnail_label_update()
                    
        list1_items[:] = []	
        for i in range(self.list1.count()):
            list1_items.append(str(self.list1.item(i).text()))
        if opt != "History":
            nameListArr[:]=[]
            for i in range(len(self.original_path_name)):
                nameListArr.append(self.original_path_name[i])
                
        if self.list1.isHidden() and not self.list2.isHidden():
            if self.list1.count() > 0:
                self.list1.show()
                show_hide_titlelist = 1
                self.list2.hide()
                self.goto_epn.hide()
                show_hide_playlist = 0
        elif not self.list1.isHidden() and self.list2.isHidden():
            if self.list1.count() == 0 and self.list2.count() > 0:
                self.list1.hide()
                self.frame.hide()
                show_hide_titlelist = 0
                self.list2.show()
                show_hide_playlist = 1
        
    def music_mode_layout(self):
        global layout_mode, screen_width, show_hide_cover, show_hide_player
        global show_hide_playlist, show_hide_titlelist, music_arr_setting
        global opt, new_tray_widget, tray
        #ui.VerticalLayoutLabel.takeAt(2)
        if not self.float_window.isHidden():
            tray.right_menu._detach_video()
            
        self.music_mode_dim_show = True
        self.list_with_thumbnail = False
        self.image_fit_option_val = 3
        
        print('Music Mode')
        layout_mode = "Music"
        print(self.music_mode_dim, '--music--mode--')
        MainWindow.showNormal()
        MainWindow.setGeometry(
            ui.music_mode_dim[0], ui.music_mode_dim[1], 
            ui.music_mode_dim[2], ui.music_mode_dim[3]
            )
        #MainWindow.showMaximized()
        MainWindow.hide()
        MainWindow.show()
        self.text.show()
        self.label.show()
        show_hide_cover = 1
        self.tab_5.hide()
        show_hide_player = 0
        self.sd_hd.hide()
        self.audio_track.hide()
        self.subtitle_track.hide()
        self.player_loop_file.show()
        
        cnt = self.btn1.findText("Music")
        print(music_arr_setting, '--music-setting--')
        if cnt >=0 and cnt < self.btn1.count():
            self.btn1.setCurrentIndex(cnt)
            self.list3.setCurrentRow(music_arr_setting[0])
            self.list1.setCurrentRow(music_arr_setting[1])
            self.list1.hide()
            self.frame.hide()
            show_hide_titlelist = 0
            self.list2.setCurrentRow(music_arr_setting[2])
            self.list2.show()
            #ui.goto_epn.show()
            show_hide_playlist = 1
            self.list2.setFocus()
        self.widget_style.apply_stylesheet(self.list2)
        
    def video_mode_layout(self):
        global layout_mode, default_arr_setting, opt, new_tray_widget, tray
        #ui.VerticalLayoutLabel.addStretch(1)
        if not self.float_window.isHidden():
            tray.right_menu._detach_video()
        print('default Mode')
        if self.music_mode_dim_show:
            self.music_mode_dim = [
                MainWindow.pos().x(), MainWindow.pos().y(), 
                MainWindow.width(), MainWindow.height()
                ]
        print(self.music_mode_dim, '--video--mode--')
        self.music_mode_dim_show = False
        
        layout_mode = "Default"
        self.sd_hd.show()
        self.audio_track.show()
        self.subtitle_track.show()
        self.list1.show()
        #ui.frame.show()
        self.list2.show()
        #ui.goto_epn.show()
        
        print(default_arr_setting, '--default-setting--')
        if default_arr_setting[0] > 0 and default_arr_setting[0] < self.btn1.count():
            self.btn1.setCurrentIndex(default_arr_setting[0])
            if self.btn1.currentText() == 'Addons':
                self.btnAddon.setCurrentIndex(default_arr_setting[4])
                if (self.btnAddon.currentText() == 'SubbedAnime' 
                        or self.btnAddon.currentText() == 'DubbedAnime'):
                    self.btnHistory.show()
                else:
                    if not self.btnHistory.isHidden():
                        self.btnHistory.hide()
            self.list3.setCurrentRow(default_arr_setting[1])
            try:
                option_val = self.list3.currentItem().text()
            except:
                option_val = "History"
            if (option_val and (option_val == 'History' or option_val == 'Available' 
                    or option_val == 'Directory')):
                if option_val == 'History':
                    print('--setting-history-option--')
                    opt = 'History'
                else:
                    opt = option_val
                self.setPreOpt()
            self.list1.setCurrentRow(default_arr_setting[2])
            self.list2.setCurrentRow(default_arr_setting[3])
            self.list2.setFocus()
            
        MainWindow.showMaximized()
        self.widget_style.apply_stylesheet(self.list2)
        
    def _set_window_frame(self):
        global new_tray_widget
        txt = self.window_frame
        if txt.lower() == 'false':
            MainWindow.setWindowFlags(
                QtCore.Qt.Window | QtCore.Qt.FramelessWindowHint)
            self.float_window.setWindowFlags(
                QtCore.Qt.Window | QtCore.Qt.FramelessWindowHint 
                | QtCore.Qt.WindowStaysOnTopHint)
        else:
            MainWindow.setWindowFlags(QtCore.Qt.Window 
                                      | QtCore.Qt.WindowTitleHint)
            self.float_window.setWindowFlags(
                QtCore.Qt.Window | QtCore.Qt.WindowTitleHint 
                | QtCore.Qt.WindowStaysOnTopHint)
        MainWindow.show()
        
    def watch_external_video(self, var):
        global quitReally, video_local_stream, curR, site
        global home
        t = var
        logger.info(t)
        file_exists = False
        site = 'None'
        if os.path.exists(var):
            file_exists = True
        if (("file:///" in t or t.startswith('/') or t.startswith('http') or 
                file_exists) and not t.endswith('.torrent') and not 'magnet:' in t):
            quitReally="no"
            logger.info(t)
            txt_file = True
            if 'http' in t:
                t = re.search('http[^"]*', t).group()
                logger.info(t)
            if t.endswith('.m3u') or t.endswith('.pls'):
                t = urllib.parse.unquote(t)
                if os.path.exists(t):
                    lines = open_files(t, True)
                    logger.info(lines)
                elif t.startswith('http'):
                    content = ccurl(t)
                    logger.info(content)
                    if content:
                        lines = content.split('\n')
                    else:
                        lines = None
                    logger.info(lines)
                else:
                    lines = None
                if lines:
                    self.epn_arr_list[:] = []
                    cnt = len(lines)
                    i = 0
                    site = "PlayLists"
                    self.btn1.setCurrentIndex(self.btn1.findText(site))
                    self.list2.clear()
                    if t.endswith('.m3u'):
                        while i < cnt:
                            try:
                                if 'EXTINF' in lines[i]:
                                    n_epn = (lines[i].strip()).split(',', 1)[1]
                                    if n_epn.startswith('NONE - '):
                                        n_epn = n_epn.replace('NONE - ', '', 1)
                                    self.list2.addItem(n_epn)
                                    if i+1 < cnt:
                                        entry_epn = n_epn+'	'+lines[i+1].strip()+'	'+'NONE'
                                        self.epn_arr_list.append(entry_epn)
                                    i = i+2
                                else:
                                    i = i+1
                            except Exception as e:
                                print(e)
                                i = i+1
                    else:
                        while i < cnt:
                            try:
                                if lines[i].lower().startswith('file'):
                                    n_url = lines[i].strip().split('=', 1)[1]
                                    if i+1 < cnt:
                                        n_epn = str(i)
                                        if lines[i+1].lower().startswith('title'):
                                            n_epn = (lines[i+1].strip()).split('=', 1)[1]
                                            i = i+2
                                        elif lines[i-1].lower().startswith('title'):
                                            n_epn = (lines[i+1].strip()).split('=', 1)[1]
                                            i = i+1
                                        else:
                                            i = i+2
                                        if n_epn.startswith('NONE - '):
                                            n_epn = n_epn.replace('NONE - ', '', 1)
                                        self.list2.addItem(n_epn)
                                        entry_epn = n_epn+'	'+n_url+'	'+'NONE'
                                        self.epn_arr_list.append(entry_epn)
                                else:
                                    i = i+1
                            except Exception as e:
                                print(e)
                                i = i+1
                    if self.epn_arr_list:
                        file_name = os.path.join(home, 'Playlists', 'TMP_PLAYLIST')
                        f = open(file_name, 'w').close()
                        write_files(file_name, self.epn_arr_list, True)
                        self.list1.clear()
                        self.list1.addItem('TMP_PLAYLIST')
            elif t.startswith('http'):
                site = "PlayLists"
                t = urllib.parse.unquote(t)
                content = ccurl(t+'#'+'-I')
                if ('www-authenticate' in content.lower() 
                        or '401 unauthorized' in content.lower()):
                    dlg = LoginAuth(parent=MainWindow, url=t, ui=self, tmp=TMPDIR)
                    return 0
                    
                if ('audio/mpegurl' in content) or ('text/html' in content):
                    content = ccurl(t)
                    txt_file = True
                else:
                    txt_file = False
                if txt_file and '#EXTM3U' in content:
                    lines = content.split('\n')
                    if lines:
                        self.epn_arr_list[:] = []
                        cnt = len(lines)
                        i = 0
                        self.btn1.setCurrentIndex(self.btn1.findText(site))
                        self.list2.clear()
                        while i < cnt:
                            try:
                                if 'EXTINF' in lines[i]:
                                    n_epn = (lines[i].strip()).split(',', 1)[1]
                                    if n_epn.startswith('NONE - '):
                                        n_epn = n_epn.replace('NONE - ', '', 1)
                                    self.list2.addItem(n_epn)
                                    if i+1 < cnt:
                                        entry_epn = n_epn+'	'+lines[i+1].strip()+'	'+'NONE'
                                        self.epn_arr_list.append(entry_epn)
                                    i = i+2
                                else:
                                    i = i+1
                            except Exception as e:
                                print(e)
                        if self.epn_arr_list:
                            file_name = os.path.join(home, 'Playlists', 'TMP_PLAYLIST')
                            f = open(file_name, 'w').close()
                            write_files(file_name, self.epn_arr_list, True)
                            self.list1.clear()
                            self.list1.addItem('TMP_PLAYLIST')
                else:
                    site == 'None'
                    finalUrl = t
                    if 'youtube.com' in t:
                        finalUrl = get_yt_url(t, self.quality_val, self.ytdl_path, logger)
                    self.epn_arr_list[:] = []
                    self.epn_arr_list.append(t+'	'+finalUrl+'	'+'NONE')
                    self.watchDirectly(finalUrl, '', 'no')
                    if self.epn_arr_list:
                        file_name = os.path.join(home, 'Playlists', 'TMP_PLAYLIST')
                        f = open(file_name, 'w').close()
                        write_files(file_name, self.epn_arr_list, True)
                        self.list1.clear()
                        self.list1.addItem('TMP_PLAYLIST')
            else:
                if os.path.isfile(t):
                    new_epn = os.path.basename(t)
                    self.epn_name_in_list = urllib.parse.unquote(new_epn)
                    self.watchDirectly(urllib.parse.unquote('"'+t+'"'), '', 'no')
                    self.dockWidget_3.hide()
                    site = "PlayLists"
                    self.btn1.setCurrentIndex(self.btn1.findText(site))
                    self.list2.clear()
                    m = []
                    try:
                        path_Local_Dir, name = os.path.split(t)
                        list_dir = os.listdir(path_Local_Dir)
                    except Exception as e:
                        print(e)
                        return 0
                else:
                    self.dockWidget_3.hide()
                    site = "PlayLists"
                    self.btn1.setCurrentIndex(self.btn1.findText(site))
                    self.list2.clear()
                    m = []
                    try:
                        path_Local_Dir = t
                        list_dir = os.listdir(path_Local_Dir)
                    except Exception as e:
                        print(e)
                        return 0
                for z in list_dir:
                    if ('.mkv' in z or '.mp4' in z or '.avi' in z or '.mp3' in z 
                                or '.flv' in z or '.flac' in z or '.wma' in z
                                or '.wmv' in z or '.ogg' in z or '.webm' in z
                                or '.wma' in z):
                            m.append(os.path.join(path_Local_Dir, z))
                m=naturallysorted(m)
                #print m
                self.epn_arr_list[:]=[]
                j = 0
                row = 0
                t = t.replace('"', '')
                t=urllib.parse.unquote(t)
                
                e = os.path.basename(t)
                
                for i in m:
                    i1 = i
                    #i = i.split('/')[-1]
                    i = os.path.basename(i)
                    self.epn_arr_list.append(i+'	'+i1+'	'+'NONE')
                    self.list2.addItem((i))
                    i = i
                    if i == e:
                        row = j
                    j =j+1
                self.list2.setCurrentRow(row)
                curR = row
                if self.epn_arr_list:
                    file_name = os.path.join(home, 'Playlists', 'TMP_PLAYLIST')
                    f = open(file_name, 'w').close()
                    write_files(file_name, self.epn_arr_list, True)
                    self.list1.clear()
                    self.list1.addItem('TMP_PLAYLIST')
        elif t.endswith('.torrent'):
            self.torrent_type = 'file'
            video_local_stream = True
            site = 'None'
            t = t.replace('file:///', '/')
            t=urllib.parse.unquote(t)
            logger.info(t)
            local_torrent_file_path = t
            info = lt.torrent_info(t)
            file_arr = []
            self.list2.clear()
            self.epn_arr_list[:]=[]
            QtWidgets.QApplication.processEvents()
            for f in info.files():
                file_path = f.path
                logger.info(file_path)
                file_path = os.path.basename(file_path)
                self.epn_arr_list.append(file_path+'	'+t)
                self.list2.addItem((file_path))
        elif 'magnet:' in t:
            t = re.search('magnet:[^"]*', t).group()
            site = 'None'
            self.torrent_type = 'magnet'
            video_local_stream = True
            self.local_torrent_open(t)
        else:
            quitReally="yes"
            new_epn = os.path.basename(t)
            t = '"'+t+'"'
            self.epn_name_in_list = urllib.parse.unquote(new_epn)
            site = 'None'
            self.watchDirectly(urllib.parse.unquote(t), '', 'no')
            self.dockWidget_3.hide()


def main():
    global ui, MainWindow, tray, hdr, name, pgn, genre_num, site, name, epn, base_url
    global name1, embed, epn_goto, list1_items, opt, mirrorNo, mpv, queueNo, playMpv
    global mpvAlive, pre_opt, insidePreopt, posterManually, labelGeometry
    global new_tray_widget
    global list2_items, quality, indexQueue, Player, startPlayer
    global rfr_url, category, fullscr, curR, idw, idwMain, home, home1
    global player_focus, fullscrT, artist_name_mplayer
    global pict_arr, name_arr, summary_arr, total_till, tmp_name, browse_cnt
    global label_arr, hist_arr, nxtImg_cnt, view_layout, quitReally, toggleCache
    global status, wget, playlist_show, img_arr_artist
    global cache_empty, buffering_mplayer, slider_clicked, interval
    global iconv_r, path_final_Url, memory_num_arr, mpv_indicator
    global pause_indicator, default_option_arr
    global thumbnail_indicator, opt_movies_indicator, epn_name_in_list
    global cur_label_num, iconv_r_indicator, tab_6_size_indicator, viewMode
    global tab_6_player, audio_id, sub_id, site_arr, siteName, finalUrlFound
    global refererNeeded, base_url_picn, base_url_summary, nameListArr
    global update_start, screen_width, screen_height, total_till_epn
    global mpv_start
    global show_hide_cover, show_hide_playlist, show_hide_titlelist, server
    global show_hide_player, layout_mode, current_playing_file_path
    global music_arr_setting, default_arr_setting, video_local_stream
    global local_torrent_file_path, wait_player, desktop_session
    global html_default_arr, app
    
    wait_player = False
    local_torrent_file_path = ''
    path_final_Url = ''
    video_local_stream = False
    default_arr_setting = [0, 0, 0, 0, 0]
    music_arr_setting = [0, 0, 0]
    layout_mode = "Default"
    show_hide_player = 0
    show_hide_cover = 1
    show_hide_playlist = 1
    show_hide_titlelist = 1
    mpv_start = []
    total_till_epn = 0
    idw = ""
    update_start = 0
    nameListArr = []
    artist_name_mplayer =""
    img_arr_artist = []
    playlist_show = 1
    siteName = ""
    finalUrlFound = False
    refererNeeded = False
    base_url_picn = ""
    base_url_summary = ""
    site_arr = [
        "SubbedAnime", "DubbedAnime", "Local", "PlayLists", "Bookmark", 
        "Music", 'Video', 'YouTube', 'None'
        ]
    default_option_arr = [
        "Select", "Video", "Music", "Bookmark", 
        "PlayLists", "YouTube", "Addons"
        ]
    html_default_arr = ["Select", "Video", "Music", "Bookmark", "PlayLists"]
    MUSIC_EXT_LIST = [
        'mp3', 'flac', 'ogg', 'wav', 'aac', 'wma',
        'm4a', 'm4b', 'opus', 'webm'
        ]
    VIDEO_EXT_LIST = [
        'mkv', 'mp4', 'avi', 'flv', 'ogg', 'wmv',
        'webm', 'mpg', 'mpeg', 'mov'
        ]
    audio_id = "auto"
    sub_id = "auto"
    tab_6_player = "False"
    viewMode = "List"
    tab_6_size_indicator = []
    iconv_r_indicator = []
    cur_label_num = 0
    labelGeometry = 0
    opt_movies_indicator=[]
    thumbnail_indicator=[]
    pause_indicator = []
    mpv_indicator = []
    memory_num_arr = []
    iconv_r = 5
    interval = 0
    slider_clicked = "no"
    buffering_mplayer = "no"
    cache_empty = "no"
    fullscrT = 0
    player_focus = 0
    wget = QtCore.QProcess()
    
        
    status = "bookmark"
    toggleCache = 0
    quitReally = "no"
    view_layout = "List"
    nxtImg_cnt = 0
    hist_arr=[]
    label_arr=[]
    total_till = 0
    pict_arr=[]
    name_arr=[]
    summary_arr=[]
    browse_cnt = 0
    tmp_name=[]
    home1 = os.path.expanduser("~")
    home = os.path.join(home1, '.config', 'kawaii-player')
    curR = 0
    fullscr = 0
    category = "Animes"
    rfr_url = ""
    startPlayer = "Yes"
    
    Player = "mpv"
    indexQueue = 0
    quality = "sd"
    list2_items = []
    posterManually = 0
    insidePreopt = 0
    pre_opt = ""
    mpvAlive = 0
    playMpv = 1
    queueNo = 0
    mpv = ""
    mirrorNo = 1
    list1_items = []
    epn_goto = 0
    epn = ""
    embed = 0
    name1 = ""
    base_url = 0
    epn = ''
    name = ''
    site = "Local"
    genre_num = 0
    opt = ""
    pgn = 1
    site_index = 0
    addon_index = 0
    option_index = -1
    name_index = -1
    episode_index = -1
    option_val = ''
    dock_opt = 1
    pos_x = 0
    pos_y = 0
    w_ht = 0
    w_wdt = 50
    old_version = (0, 0, 0, 0)
    hdr = "Mozilla/5.0 (X11; Ubuntu; Linux i686; rv:45.0) Gecko/20100101 Firefox/45.0"
    
    try:
        dbus.mainloop.pyqt5.DBusQtMainLoop(set_as_default=True)
    except:
        pass
    desktop_session = os.getenv('DESKTOP_SESSION')
    if desktop_session:
        desktop_session = desktop_session.lower()
    else:
        desktop_session = 'lxde'
    print(OSNAME, desktop_session)
    app = QtWidgets.QApplication(sys.argv)
    media_data = MediaDatabase(
        home=home, logger=logger,
        music_ext=MUSIC_EXT_LIST, video_ext=VIDEO_EXT_LIST)
    screen_resolution = app.desktop().screenGeometry()
    screen_width = screen_resolution.width()
    screen_height = screen_resolution.height()
    print(screen_height, screen_width)
    MainWindow = MainWindowWidget()
    MainWindow.setMouseTracking(True)
    ui = Ui_MainWindow()
    ui.setupUi(MainWindow, media_data=media_data)
    ui.media_data.set_ui(ui)
    ui.tab_5.set_mpvplayer(player=Player, mpvplayer=ui.mpvplayer_val)
    ui.getdb = ServerLib(ui, home, BASEDIR, TMPDIR, logger)
    ui.btn1.setFocus()
    ui.dockWidget_4.hide()
    if not os.path.exists(home):
        os.makedirs(home)
    if not os.path.exists(os.path.join(home, 'src')):
        src_new = os.path.join(home, 'src')
        os.makedirs(src_new)
        input_conf = os.path.join(BASEDIR, 'input.conf')
        if os.path.exists(input_conf):
            shutil.copy(input_conf, os.path.join(src_new, 'input.conf'))
        png_n = os.path.join(BASEDIR, '1.png')
        if os.path.exists(png_n):
            shutil.copy(png_n, os.path.join(src_new, '1.png'))
        introspect_xml = os.path.join(BASEDIR, 'introspect.xml')
        if os.path.exists(introspect_xml):
            shutil.copy(introspect_xml, os.path.join(src_new, 'introspect.xml'))
        tray_png = os.path.join(BASEDIR, 'tray.png')
        if os.path.exists(tray_png):
            shutil.copy(tray_png, os.path.join(src_new, 'tray.png'))
    picn = os.path.join(home, 'default.jpg')
    if not os.path.exists(picn):
        picn_1 = os.path.join(BASEDIR, 'default.jpg')
        if os.path.exists(picn_1):
            shutil.copy(picn_1, picn)
            
    QtCore.QTimer.singleShot(100, partial(set_mainwindow_palette, picn, first_time=True))
    
    ui.widget_style.apply_stylesheet()
    
    if not os.path.exists(os.path.join(home, 'src', 'Plugins')):
        os.makedirs(os.path.join(home, 'src', 'Plugins'))
        sys.path.append(os.path.join(home, 'src', 'Plugins'))
        plugin_Dir = os.path.join(home, 'src', 'Plugins')
        s_dir = os.path.join(BASEDIR, 'Plugins')
        if not os.path.exists(s_dir):
            s_dir = os.path.join(BASEDIR, 'plugins')
        if os.path.exists(s_dir):
            m_tmp = os.listdir(s_dir)
            for i in m_tmp:
                k = os.path.join(s_dir, i)
                if (os.path.isfile(k) and i != "install.py" 
                        and i != "installPlugins.py" and i != '__init__'):
                    shutil.copy(k, plugin_Dir)
                    print("addons loading....")
                        
    if os.path.exists(os.path.join(home, 'config.txt')):
        lines = open_files(os.path.join(home, 'config.txt'), True)
        for i in lines:
            if not i.startswith('#'):
                j = i.split('=')[-1]
                if "VERSION_NUMBER" in i:
                    try:
                        j = j.replace('\n', '')
                        j = j.replace('(', '')
                        j = j.replace(')', '')
                        j = j.replace(' ', '')
                        k = j.split(',')
                        jr = []
                        for l in k:
                            jr.append(int(l))
                        old_version = tuple(jr)
                    except:
                        pass
                    #print(old_version)
                elif "FloatWindow" in i:
                    try:
                        j = j.replace('\n', '')
                        j = j.replace('[', '')
                        j = j.replace(']', '')
                        j = j.replace(' ', '')
                        k = j.split(',')
                        ui.float_window_dim[:] = []
                        for l in k:
                            ui.float_window_dim.append(int(l))
                        print(ui.float_window_dim)
                    except:
                        ui.float_window_dim = [0, 0, 250, 200]
                elif "MusicWindowDim" in i:
                    try:
                        j = j.replace('\n', '')
                        j = j.replace('[', '')
                        j = j.replace(']', '')
                        j = j.replace(' ', '')
                        k = j.split(',')
                        ui.music_mode_dim[:] = []
                        for l in k:
                            ui.music_mode_dim.append(int(l))
                        print(ui.music_mode_dim, '--music--mode--dimension--set--')
                    except:
                        ui.music_mode_dim = [0, 0, 900, 350]
                elif "DefaultPlayer" in i:
                    
                    Player = re.sub('\n', '', j)
                    cnt = ui.chk.findText(Player)
                    ui.player_val = Player
                    if cnt >=0 and cnt < ui.chk.count():
                        ui.chk.setCurrentIndex(cnt)
                elif "WindowFrame" in i:
                    try:
                        j = j.replace('\n', '')
                        ui.window_frame = str(j)
                    except:
                        ui.window_frame = 'true'
                elif "DockPos" in i:
                    try:
                        j = j.strip()
                        ui.orientation_dock = str(j)
                    except:
                        ui.orientation_dock = 'left'
                elif "MusicModeDimShow" in i:
                    try:
                        j = j.replace('\n', '')
                        val_m = str(j)
                    except:
                        val_m = 'False'
                    if val_m.lower() == 'true':
                        ui.music_mode_dim_show = True
                    else:
                        ui.music_mode_dim_show = False
                elif "Video_Mode_Index" in i:
                    try:
                        j = j.replace('\n', '')
                        ui.video_mode_index = int(j)+1
                        ui.comboBoxMode.setCurrentIndex(int(j))
                    except:
                        ui.video_mode_index = 1
                        ui.comboBoxMode.setCurrentIndex(0)
                elif "List_Mode_With_Thumbnail" in i:
                    tmp_mode = re.sub('\n', '', j)
                    if tmp_mode.lower() == 'true':
                        ui.list_with_thumbnail = True
                        ui.list2.setStyleSheet("""QListWidget{font: bold 12px;
                        color:white;background:rgba(0, 0, 0, 30%);
                        border:rgba(0, 0, 0, 30%);border-radius: 3px;}
                        QListWidget:item {height: 128px;}
                        QListWidget:item:selected:active {background:rgba(0, 0, 0, 20%);
                        color: violet;}
                        QListWidget:item:selected:inactive {border:rgba(0, 0, 0, 30%);}
                        QMenu{font: bold 12px;color:black;
                        background-image:url('1.png');}""")
                    else:
                        ui.list2.setStyleSheet("""QListWidget{font: bold 12px;
                        color:white;background:rgba(0, 0, 0, 30%);
                        border:rgba(0, 0, 0, 30%);border-radius: 3px;}
                        QListWidget:item {height: 30px;}
                        QListWidget:item:selected:active {background:rgba(0, 0, 0, 20%);
                        color: violet;}
                        QListWidget:item:selected:inactive {border:rgba(0, 0, 0, 30%);}
                        QMenu{font: bold 12px;color:black;
                        background-image:url('1.png');}""")
                        ui.list_with_thumbnail = False
                elif "Site_Index" in i:
                    site_i = re.sub('\n', '', j)
                    if site_i.isdigit():
                        site_index = int(site_i)
                    print(site_index, '--site-index--')
                elif "Addon_Index" in i:
                    addon_i = re.sub('\n', '', j)
                    if addon_i.isdigit():
                        addon_index = int(addon_i)
                    print(addon_index, '--addon-index--')
                elif "Option_Index" in i:
                    opt_i = re.sub('\n', '', j)
                    if opt_i.isdigit():
                        option_index = int(opt_i)
                    print(option_index, '--option-index--')
                elif "Video_Aspect" in i:
                    video_aspect = re.sub('\n', '', j)
                    if video_aspect.isdigit():
                        ui.mpvplayer_aspect_cycle = int(video_aspect)
                    print(video_aspect, '--video-aspect--')
                elif "Upload_Speed" in i:
                    upspeed = re.sub('\n', '', j)
                    if upspeed.isnumeric():
                        ui.setuploadspeed = int(upspeed)
                    #print(upspeed, '--server-upspeed--')
                elif "Name_Index" in i:
                    name_i = re.sub('\n', '', j)
                    if name_i.isdigit():
                        name_index = int(name_i)
                    print(name_index, '--name-index--')
                elif "Episode_Index" in i:
                    epi_i = re.sub('\n', '', j)
                    if epi_i.isdigit():
                        episode_index = int(epi_i)
                    print(episode_index, '--episode-index--')
                elif "Option_Val" in i:
                    opt_v = re.sub('\n', '', j)
                    option_val = opt_v
                    print(option_val, '--option--')
                elif "Quality" in i:
                    quality = re.sub('\n', '', j)
                    ui.client_quality_val = quality
                    print(quality, '----quality---')
                    if quality == "hd":
                        ui.sd_hd.setText("HD")
                    elif quality == 'sd480p':
                        ui.sd_hd.setText("480")
                    elif quality == 'best':
                        ui.sd_hd.setText("BEST")
                    else:
                        ui.sd_hd.setText("SD")
                elif "Dock_Option" in i:
                    dock_o = re.sub('\n', '', j)
                    if dock_o.isdigit():
                        dock_opt = int(dock_o)
                elif "Show_Hide_Cover" in i:
                    try:
                        show_hide_cover = int(j)
                        if show_hide_cover == 0:
                            ui.text.hide()
                            ui.label.hide()
                    except:
                        show_hide_cover = 0
                elif "Show_Hide_Playlist" in i:
                    try:
                        show_hide_playlist = int(j)
                        if show_hide_playlist == 0:
                            ui.list2.hide()
                            ui.goto_epn.hide()
                    except:
                        show_hide_playlist = 0
                elif "Show_Hide_Titlelist" in i:
                    try:
                        show_hide_titlelist = int(j)
                        if show_hide_titlelist == 0:
                            ui.list1.hide()
                            ui.frame.hide()
                    except:
                        show_hide_titlelist = 0
                elif "Show_Hide_Player" in i:
                    try:
                        show_hide_player = int(j)
                    except:
                        show_hide_player = 0
                elif "Thumbnail_Size" in i:
                    j = j.replace('\n', '')
                    if j:
                        iconv_r = int(j)
                        iconv_r_indicator.append(iconv_r)
                elif "View" in i:
                    viewMode = j.replace('\n', '')
                    if viewMode=="Thumbnail":
                        ui.comboView.setCurrentIndex(2)
                    elif viewMode=="List":
                        ui.comboView.setCurrentIndex(1)
                elif "Layout" in i:
                    layout_mode = j.replace('\n', '')
                elif "POSX" in i:
                    posx = re.sub('\n', '', j)
                    if posx.isdigit():
                        pos_x = int(posx)
                elif "POSY" in i:
                    pos_yy = re.sub('\n', '', j)
                    if pos_yy.isdigit():
                        pos_y = int(pos_yy)
                elif "WHeight" in i:
                    ht1 = re.sub('\n', '', j)
                    if ht1.isdigit():
                        w_ht = int(ht1)
                elif "WWidth" in i:
                    wd2 = re.sub('\n', '', j)
                    if wd2.isdigit():
                        w_wdt = int(wd2)
                elif "Default_Mode" in i:
                    try:
                        def_m = re.sub('\n', '', j)
                        t_v = def_m.split(',')
                        for l,z in enumerate(t_v):
                            if z:
                                default_arr_setting[l] = int(z.strip())
                        logger.info(default_arr_setting)
                    except Exception as e:
                        print(e,'--20251--')
                elif 'Music_Mode' in i:
                    try:
                        def_m = re.sub('\n', '', j)
                        t_v = def_m.split(',')
                        for l,z in enumerate(t_v):
                            if z:
                                music_arr_setting[l] = int(z.strip())
                        logger.info(music_arr_setting)
                    except Exception as e:
                        print(e,'--20261--')
    else:
        f = open(os.path.join(home, 'config.txt'), 'w')
        f.write("DefaultPlayer=mpv")
        f.close()
    
    if os.path.exists(os.path.join(home, 'torrent_config.txt')):
        lines = open_files(os.path.join(home, 'torrent_config.txt'), True)
        #print(lines)
        for i in lines:
            if not i.startswith('#'):
                j = i.split('=')[-1]
                if "TORRENT_STREAM_IP" in i:
                    j = re.sub('\n', '', j)
                    j1 = j.split(':')
                    if len(j1) == 2:
                        if j1[0].lower()=='localhost' or not j1[0]:
                            ui.local_ip = '127.0.0.1'
                        else:
                            ui.local_ip = j1[0]
                        try:
                            ui.local_port = int(j1[1])
                        except Exception as e:
                            print(e)
                            ui.local_port = 8001
                    else:
                        ui.local_ip = '127.0.0.1'
                        ui.local_port = 8001
                    if ui.local_ip not in ui.client_auth_arr:
                        ui.client_auth_arr.append(ui.local_ip)
                elif "TORRENT_DOWNLOAD_FOLDER" in i:
                    j = re.sub('\n', '', j)
                    if j.endswith('/'):
                        j = j[:-1]
                    if os.path.exists(j):
                        ui.torrent_download_folder = j
                    else:
                        ui.torrent_download_folder = TMPDIR
                elif "TORRENT_UPLOAD_RATE" in i:
                    j = re.sub('\n', '', j)
                    try:
                        ui.torrent_upload_limit = int(j)*1024
                    except:
                        ui.torrent_upload_limit = 0
                elif "TORRENT_DOWNLOAD_RATE" in i:
                    j = re.sub('\n', '', j)
                    try:
                        ui.torrent_download_limit = int(j)*1024
                    except:
                        ui.torrent_download_limit = 0
    else:
        f = open(os.path.join(home, 'torrent_config.txt'), 'w')
        f.write("TORRENT_STREAM_IP=127.0.0.1:8001")
        f.write("\nTORRENT_DOWNLOAD_FOLDER="+TMPDIR)
        f.write("\nTORRENT_UPLOAD_RATE=0")
        f.write("\nTORRENT_DOWNLOAD_RATE=0")
        f.close()
        ui.local_ip = '127.0.0.1'
        ui.local_port = 8001
        
    if os.path.exists(os.path.join(home, 'other_options.txt')):
        lines = open_files(os.path.join(home, 'other_options.txt'), True)
        for i in lines:
            i = i.strip()
            j = i.split('=')[-1]
            if "LOCAL_STREAM_IP" in i:
                j1 = j.split(':')
                if len(j1) == 2:
                    if j1[0].lower()=='localhost' or not j1[0]:
                        ui.local_ip_stream = '127.0.0.1'
                    else:
                        ui.local_ip_stream = j1[0]
                    try:
                        ui.local_port_stream = int(j1[1])
                    except Exception as e:
                        print(e)
                        ui.local_port_stream = 9001
                else:
                    ui.local_ip_stream = '127.0.0.1'
                    ui.local_port_stream = 9001
                if ui.local_ip_stream not in ui.client_auth_arr:
                    ui.client_auth_arr.append(ui.local_ip_stream)
            elif 'DEFAULT_DOWNLOAD_LOCATION' in i:
                ui.default_download_location = j
            elif 'GET_LIBRARY' in i:
                ui.get_fetch_library = j
            elif 'TMP_REMOVE' in i:
                if j == 'yes' or j == 'no':
                    ui.tmp_folder_remove = j
                else:
                    ui.tmp_folder_remove = 'no'
            elif 'IMAGE_FIT_OPTION' in i:
                try:
                    k = int(j)
                except Exception as e:
                    print(e)
                    k = 3
                ui.image_fit_option_val = k
            elif i.startswith('AUTH='):
                try:
                    if (j.lower() != 'none'):
                        ui.media_server_key = j
                    else:
                        ui.media_server_key = None
                except Exception as e:
                    print(e)
                    ui.media_server_key = None
            elif i.startswith('ACCESS_FROM_OUTSIDE_NETWORK='):
                try:
                    if (':' in j) and (j.lower() != 'none'):
                        tmp = j.split(':')
                        if tmp[0].lower() == 'true':
                            ui.access_from_outside_network = True
                        else:
                            ui.access_from_outside_network = False
                        try:
                            ui.get_ip_interval = float(tmp[1])
                        except Exception as e:
                            print(e)
                            ui.get_ip_interval = 1
                    else:
                        if j.lower() == 'true':
                            ui.access_from_outside_network = True
                        else:
                            ui.access_from_outside_network = False
                            
                except Exception as e:
                    print(e)
                    ui.access_from_outside_network = False
            elif i.startswith('CLOUD_IP_FILE='):
                try:
                    if j.lower() == 'none' or j.lower() == 'false' or not j:
                        ui.cloud_ip_file = None
                    else:
                        if os.path.isfile(j):
                            ui.cloud_ip_file = j
                        else:
                            ui.cloud_ip_file = None
                except Exception as e:
                    print(e)
                    ui.cloud_ip_file = None
            elif i.startswith('KEEP_BACKGROUND_CONSTANT='):
                try:
                    k = j.lower()
                    if k:
                        if k == 'yes' or k == 'true' or k == '1':
                            ui.keep_background_constant = True
                        else:
                            ui.keep_background_constant = False
                except Exception as e:
                    print(e)
                    ui.keep_background_constant = False
            elif i.startswith('HTTPS_ON='):
                try:
                    k = j.lower()
                    if k:
                        if k == 'yes' or k == 'true' or k == '1':
                            ui.https_media_server = True
                        else:
                            ui.https_media_server = False
                except Exception as e:
                    print(e)
                    ui.https_media_server = False
            elif i.startswith('MEDIA_SERVER_COOKIE='):
                try:
                    k = j.lower()
                    if k:
                        if k == 'yes' or k == 'true' or k == '1':
                            ui.media_server_cookie = True
                        else:
                            ui.media_server_cookie = False
                except Exception as e:
                    print(e)
                    ui.media_server_cookie = False
            elif i.startswith('COOKIE_EXPIRY_LIMIT='):
                try:
                    k = float(j)
                    ui.cookie_expiry_limit = k
                except Exception as e:
                    print(e)
                    ui.cookie_expiry_limit = 24
            elif i.startswith('COOKIE_PLAYLIST_EXPIRY_LIMIT='):
                try:
                    k = float(j)
                    ui.cookie_playlist_expiry_limit = k
                except Exception as e:
                    print(e)
                    ui.cookie_playlist_expiry_limit = 24
            elif i.startswith('LOGGING='):
                try:
                    k = j.lower()
                    if k == 'off' or k == 'false':
                        ui.logging_module = False
                    elif k == 'on' or k == 'true':
                        ui.logging_module = True
                    else:
                        ui.logging_module = False
                except Exception as e:
                    print(e)
                    ui.logging_module = False
            elif i.startswith('GET_MUSIC_METADATA='):
                try:
                    k = j.lower()
                    if k == 'on' or k == 'true' or k == 'yes':
                        ui.get_artist_metadata = True
                except Exception as e:
                    print(e)
            elif i.startswith('REMOTE_CONTROL='):
                try:
                    k = j.lower()
                    if k == 'on' or k == 'true' or k == 'yes':
                        ui.remote_control_field = True
                        ui.action_player_menu[9].setText("Turn Off Remote Control")
                except Exception as e:
                    print(e)
            elif i.startswith('BROADCAST_MESSAGE='):
                try:
                    j = j.replace('"', '')
                    j = j.replace("'", '')
                    ui.broadcast_message = j
                except Exception as e:
                    print(e)
            elif i.startswith('ANIME_REVIEW_SITE='):
                try:
                    k = j.lower()
                    if k:
                        if k == 'yes' or k == 'true' or k == '1':
                            ui.anime_review_site = True
                        else:
                            ui.anime_review_site = False
                except Exception as e:
                    print(e)
                    ui.anime_review_site = False
            elif i.startswith('YTDL_PATH='):
                try:
                    k = j.lower()
                    if k == 'default':
                        ui.ytdl_path = 'default'
                    elif k == 'automatic':
                        if OSNAME == 'posix':
                            ui.ytdl_path = os.path.join(home, 'src', 'ytdl')
                        elif OSNAME == 'nt':
                            ui.ytdl_path = os.path.join(home, 'src', 'ytdl.exe') 
                    else:
                        if os.path.exists(j):
                            ui.ytdl_path = j
                        else:
                            ui.ytdl_path = 'default'
                except Exception as e:
                    print(e)
                    ui.ytdl_path = 'default'
    else:
        f = open(os.path.join(home, 'other_options.txt'), 'w')
        if BROWSER_BACKEND == 'QTWEBENGINE':
            f.write("BROWSER_BACKEND=QTWEBENGINE")
        elif BROWSER_BACKEND == 'QTWEBKIT':
            f.write("BROWSER_BACKEND=QTWEBKIT")
        f.write("\nLOCAL_STREAM_IP=127.0.0.1:9001")
        f.write("\nDEFAULT_DOWNLOAD_LOCATION="+TMPDIR)
        f.write("\nKEEP_BACKGROUND_CONSTANT=no")
        f.write("\nTMP_REMOVE=no")
        f.write("\nGET_LIBRARY=pycurl")
        f.write("\nIMAGE_FIT_OPTION=1")
        f.write("\nAUTH=NONE")
        f.write("\nACCESS_FROM_OUTSIDE_NETWORK=False")
        f.write("\nCLOUD_IP_FILE=none")
        f.write("\nHTTPS_ON=False")
        f.write("\nMEDIA_SERVER_COOKIE=False")
        f.write("\nCOOKIE_EXPIRY_LIMIT=24")
        f.write("\nCOOKIE_PLAYLIST_EXPIRY_LIMIT=24")
        f.write("\nLOGGING=Off")
        f.write("\nYTDL_PATH=DEFAULT")
        f.write("\nANIME_REVIEW_SITE=False")
        f.write("\nGET_MUSIC_METADATA=False")
        f.write("\nREMOTE_CONTROL=False")
        f.close()
        ui.local_ip_stream = '127.0.0.1'
        ui.local_port_stream = 9001
        
    print(ui.torrent_download_limit, ui.torrent_upload_limit)
    
    anime_review_arr = ["MyAnimeList", "Anime-Planet", "Anime-Source", "AniDB", 
                        "Zerochan"]
    if ui.anime_review_site and 'AnimeWatch' not in home:
        for i in anime_review_arr:
            ui.btnWebReviews.addItem(i)
    if not ui.logging_module:
        logger.disabled = True
    arr_setting = []
    
    arr_setting.append(show_hide_titlelist)
    arr_setting.append(show_hide_playlist)
    
    if not os.path.exists(TMPDIR):
        os.makedirs(TMPDIR)
    if not os.path.exists(home):
        os.makedirs(home)
    if os.path.exists(os.path.join(home, 'src')):
        os.chdir(os.path.join(home, 'src'))
        #sys.path.append(os.path.join(home, 'src'))
    else:
        os.chdir(BASEDIR)
    if not os.path.exists(os.path.join(home, "History")):
        os.makedirs(os.path.join(home, "History"))
    if not os.path.exists(os.path.join(home, "thumbnails")):
        os.makedirs(os.path.join(home, "thumbnails"))
    if not os.path.exists(os.path.join(home, "Local")):
        os.makedirs(os.path.join(home, "Local"))
    if not os.path.exists(os.path.join(home, "tmp")):
        os.makedirs(os.path.join(home, "tmp"))
    if not os.path.exists(os.path.join(home, "Bookmark")):
        os.makedirs(os.path.join(home, "Bookmark"))
        bookmark_array = [
            'bookmark', 'Watching', 'Completed', 'Incomplete', 
            'Later', 'Interesting', 'Music Videos'
            ]
        for i in bookmark_array:
            bookmark_path = os.path.join(home, 'Bookmark', i+'.txt')
            if not os.path.exists(bookmark_path):
                f = open(bookmark_path, 'w')
                f.close()
    if not os.path.exists(os.path.join(home, "config.txt")):
        f = open(os.path.join(home, "config.txt"), "w")
        f.write("DefaultPlayer=mpv")
        f.close()
    if not os.path.exists(os.path.join(home, "Playlists")):
        os.makedirs(os.path.join(home, "Playlists"))
    if not os.path.exists(ui.yt_sub_folder):
        os.makedirs(ui.yt_sub_folder)
    if not os.path.exists(os.path.join(home, "Playlists", "Default")):
        f = open(os.path.join(home, "Playlists", "Default"), "w")
        f.close()
    
    if os.path.exists(os.path.join(home, 'src', 'Plugins')):
        sys.path.append(os.path.join(home, 'src', 'Plugins'))
        print("plugins")
        
        if ui.version_number > old_version:
            print(ui.version_number, '>', old_version)
            plugin_Dir = os.path.join(home, 'src', 'Plugins')
            s_dir = os.path.join(BASEDIR, 'Plugins')
            if not os.path.exists(s_dir):
                s_dir = os.path.join(BASEDIR, 'plugins')
            if os.path.exists(s_dir):
                m_tmp = os.listdir(s_dir)
                for i in m_tmp:
                    k = os.path.join(s_dir, i)
                    if (os.path.isfile(k) and i != "install.py" 
                            and i != "installPlugins.py" and i != '__init__'):
                        shutil.copy(k, plugin_Dir)
                        print('Addons loading ....')
                        
        m = os.listdir(os.path.join(home, 'src', 'Plugins'))
        m.sort()
        for i in m:
            if i.endswith('.py'):
                i = i.replace('.py', '')
                if (i != 'headlessBrowser' and i != 'headlessEngine' 
                        and i!='stream' and i!='local_ip' 
                        and i!= 'headlessBrowser_webkit' and i!='installPlugins' 
                        and i != '__init__'):
                    ui.addons_option_arr.append(i)
    
    
    f = open(os.path.join(home, "History", "queue.m3u"), "w")
    f.write("#EXTM3U")
    f.close()
            
    for i in default_option_arr:
        ui.btn1.addItem(i)
    for i in ui.addons_option_arr:
        ui.btnAddon.addItem(i)
    
    print(site, site_index, '==site_index')
    if site_index >0 and site_index < ui.btn1.count():
        ui.btn1.setCurrentIndex(site_index)
        if (ui.btn1.currentText() == 'Addons' and addon_index >=0 
                and addon_index < ui.btnAddon.count()):
            ui.btnAddon.setCurrentIndex(addon_index)
    elif site_index == 0:
        ui.btn1.setCurrentIndex(1)
        ui.btn1.setCurrentIndex(0)
        
    if option_index < 0 and ui.list3.count() > 0:
        option_index = 0
        print(option_index, ui.list3.count(), '--list3--cnt--')
    
    if option_index >=0 and option_index < ui.list3.count():
        ui.list3.setCurrentRow(option_index)
        ui.list3.setFocus()
        if option_val and option_val.lower() != 'update' and option_val.lower() != 'updateall': 
            if option_val == 'History':
                print('--setting-history-option--')
                opt = 'History'
            else:
                opt = option_val
            ui.setPreOpt(option_val=opt)
    print(name_index, ui.list1.count())
    if name_index >=0 and name_index < ui.list1.count():
        ui.list1.setCurrentRow(name_index)
        ui.list1.setFocus()
        ui.list1_double_clicked()
    if episode_index >=0 and episode_index < ui.list2.count():
        ui.list2.setCurrentRow(episode_index)
        ui.list2.setFocus()
    print(dock_opt, '--dock-option---')
    if ui.orientation_dock == 'left':
        ui.orient_dock('left')
    else:
        ui.orient_dock('right')
    if dock_opt == 0:
        ui.dockWidget_3.hide()
    else:
        ui.dockWidget_3.show()
    
    
    print(int(MainWindow.winId()))
    #myFilter	 = MyEventFilter()
    #app.installEventFilter(myFilter)
    
    
    try:
        tray = SystemAppIndicator(ui_widget=ui, home=home, window=MainWindow, logr=logger)
        tray.right_menu.setup_globals(screen_width, screen_height)
        tray.show()
    except Exception as e:
        print('System Tray Failed with Exception: {0}'.format(e))
        tray = None
        
    new_tray_widget = FloatWindowWidget(ui, tray, logger)
    ui.new_tray_widget = new_tray_widget
    try:
        m_event = EventFilterFloatWindow()
        new_tray_widget.installEventFilter(m_event)
        print('Event Filter Installed in new_tray_widget')
    except Exception as e:
        print("Error in Tray Widget Event Filter with error message {0}".format(e))
    
    if ui.window_frame == 'false':
        ui._set_window_frame()
    
    try:
        server = MprisServer(ui, home, tray, new_tray_widget)
    except Exception as e:
        print("can't open Mpris plugin, Exception raised: {0}".format(e))
    
    if layout_mode == "Music":
        try:
            t1 = tray.geometry().height()
        except:
            t1 = 65
        MainWindow.setGeometry(
            ui.music_mode_dim[0], ui.music_mode_dim[1], 
            ui.music_mode_dim[2], ui.music_mode_dim[3])
        ui.image_fit_option_val = 4
    else:
        ui.sd_hd.show()
        ui.audio_track.show()
        ui.subtitle_track.show()
        MainWindow.showMaximized()
    
    show_hide_titlelist = arr_setting[0]
    show_hide_playlist = arr_setting[1]
        
    print(arr_setting)
    
    if show_hide_playlist == 1:
        ui.list2.show()
    elif show_hide_playlist == 0:
        ui.list2.hide()
        ui.goto_epn.hide()
            
    if show_hide_titlelist == 1:
        ui.list1.show()
    elif show_hide_titlelist == 0:
        ui.list1.hide()
        ui.frame.hide()
    if ui.access_from_outside_network:
        get_ip_thread = GetIpThread(ui, interval=ui.get_ip_interval, ip_file=ui.cloud_ip_file)
        get_ip_thread.start()
        print('--ip--thread--started--')
    #MainWindow.setWindowFlags(QtCore.Qt.Window | QtCore.Qt.FramelessWindowHint)
    html_default_arr = html_default_arr + ui.addons_option_arr
    MainWindow.show()
    
    if len(sys.argv) >= 2:
        logger.info(sys.argv)
        if '--start-media-server' in sys.argv or '--start-media-server' in sys.argv[1]:
            ui.playerPlaylist('Start Media Server')
            if '--update-video-db' in sys.argv:
                index = ui.btn1.findText('Video')
                if index >= 0:
                    ui.btn1.setCurrentIndex(index)
                    ui.list3.setCurrentRow(3)
            if '--update-music-db' in sys.argv:
                index = ui.btn1.findText('Music')
                if index >= 0:
                    ui.btn1.setCurrentIndex(index)
                    ui.list3.setCurrentRow(0)
            if '--user' in sys.argv:
                index = sys.argv.index('--user')
                if index+1 < len(sys.argv):
                    user_set = sys.argv[index+1]
                    if '--password' in sys.argv:
                        index = sys.argv.index('--password')
                        if index+1 < len(sys.argv):
                            pass_set = sys.argv[index+1]
                            set_user_password(user_set, pass_set)
            if '--generate-ssl' in sys.argv:
                index = sys.argv.index('--generate-ssl')
                if index+1 < len(sys.argv):
                    pass_phrase = sys.argv[index+1]
                    create_ssl_cert(ui, TMPDIR, pass_phrase)
        elif os.path.exists(sys.argv[1]):
            ui.watch_external_video(sys.argv[1])
    ui.quality_val = quality
    
    if old_version <= (2, 0, 0, 0) and old_version > (0, 0, 0, 0):
        logger.info('old version: need to change videodb schema')
        ui.media_data.alter_table_and_update(old_version)
        
    ret = app.exec_()
    
    """Starting of Final code which will be Executed just before 
    Application Quits"""
    
    if ui.dockWidget_3.isHidden() or ui.auto_hide_dock:
        dock_opt = 0
    else:
        dock_opt = 1
        
    def_val = ''
    for i in default_arr_setting:
        def_val = def_val + str(i) + ', '
    def_val = def_val[:-1]
    
    music_val = ''
    for i in music_arr_setting:
        music_val = music_val + str(i)+', '
    music_val = music_val[:-1]
    
    if ui.float_window_open:
        ui.float_window_dim = [
            ui.float_window.pos().x(), ui.float_window.pos().y(), 
            ui.float_window.width(), ui.float_window.height()
            ]
    if ui.music_mode_dim_show:
        ui.music_mode_dim = [
            MainWindow.pos().x(), MainWindow.pos().y(), 
            MainWindow.width(), MainWindow.height()
            ]
    if ui.list1.isHidden():
        show_hide_titlelist = 0
    else:
        show_hide_titlelist = 1
    if ui.list2.isHidden():
        show_hide_playlist = 0
    else:
        show_hide_playlist = 1
    if os.path.exists(os.path.join(home, "config.txt")):
                
        print(Player)
        f = open(os.path.join(home, "config.txt"), "w")
        f.write("VERSION_NUMBER="+str(ui.version_number))
        f.write("\nDefaultPlayer="+Player)
        f.write("\nWindowFrame="+str(ui.window_frame))
        f.write("\nFloatWindow="+str(ui.float_window_dim))
        f.write("\nDockPos="+str(ui.orientation_dock))
        f.write("\nMusicWindowDim="+str(ui.music_mode_dim))
        f.write("\nMusicModeDimShow="+str(ui.music_mode_dim_show))
        if iconv_r_indicator:
            iconv_r = iconv_r_indicator[0]
        f.write("\nThumbnail_Size="+str(iconv_r))
        f.write("\nView="+str(viewMode))
        f.write("\nQuality="+str(quality))
        f.write("\nSite_Index="+str(ui.btn1.currentIndex()))
        f.write("\nAddon_Index="+str(ui.btnAddon.currentIndex()))
        f.write("\nOption_Index="+str(ui.list3.currentRow()))
        f.write("\nOption_Val="+str(opt))
        f.write("\nName_Index="+str(ui.list1.currentRow()))
        f.write("\nEpisode_Index="+str(ui.list2.currentRow()))
        f.write("\nShow_Hide_Cover="+str(show_hide_cover))
        f.write("\nShow_Hide_Playlist="+str(show_hide_playlist))
        f.write("\nShow_Hide_Titlelist="+str(show_hide_titlelist))
        f.write("\nShow_Hide_Player="+str(show_hide_player))
        f.write("\nDock_Option="+str(dock_opt))
        f.write("\nPOSX="+str(MainWindow.pos().x()))
        f.write("\nPOSY="+str(MainWindow.pos().y()))
        f.write("\nWHeight="+str(MainWindow.height()))
        f.write("\nWWidth="+str(MainWindow.width()))
        f.write("\nLayout="+str(layout_mode))
        f.write("\nDefault_Mode="+str(def_val))
        f.write("\nList_Mode_With_Thumbnail="+str(ui.list_with_thumbnail))
        f.write("\nMusic_Mode="+str(music_val))
        f.write("\nVideo_Mode_Index="+str(ui.comboBoxMode.currentIndex()))
        f.write("\nVideo_Aspect="+str(ui.mpvplayer_aspect_cycle))
        f.write("\nUpload_Speed="+str(ui.setuploadspeed))
        f.close()
    if ui.mpvplayer_val.processId() > 0:
        ui.mpvplayer_val.kill()
    if os.path.exists(TMPDIR) and '.config' not in TMPDIR:
        shutil.rmtree(TMPDIR)
    print(ret, '--Return--')
    del app
    sys.exit(ret)
    
    
if __name__ == "__main__":
    main()
    
