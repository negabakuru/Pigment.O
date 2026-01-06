# Pigment.O is a Krita plugin and it is a Color Picker and Color Mixer and Color Sampler.
# Copyright ( C ) 2020  Ricardo Jeremias.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# ( at your option ) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


#region Import Modules

# Python
import math
import random
import os
import time
import sys
import webbrowser
import datetime
import shutil
import re
# Krita
from krita import *
# PyQt5
from PyQt5 import QtWidgets, QtCore, QtGui, uic
# Pigment.O
from .picker_extension import Picker_Extension
from .picker_modulo import ( 
    # Header
    Color_Header,
    Harmony_Swatch,
    Harmony_Spread,
    # Panels
    Panel_Fill,
    Panel_Square,
    Panel_HueCircle,
    Panel_Gamut,
    Panel_Hexagon,
    Panel_Dot,
    Panel_Mask,
    # Sliders
    Channel_Slider,
    # Mixer
    Pin_Color,
    )
# Engine
from .engine_names import *
from .engine_constants import *
from .engine_calculations import (
    Geometry,
    Convert,
    Analyse,
    )

#endregion
#region Global Variables

DOCKER_NAME = "Pigment.O Picker"
version = "2026_01_01"

#endregion


class Picker_Docker( DockWidget ):
    """
    Color Picker and Mixer
    """

    #region Initialize

    def __init__( self ):
        super( Picker_Docker, self ).__init__()

        # Construct
        self.User_Interface()
        self.Variables()
        self.Connections()
        self.Modules()
        self.Style()
        self.Timer()
        self.Extension()
        self.Settings()
        self.Plugin_Load()

    def User_Interface( self ):
        # Window
        self.setWindowTitle( DOCKER_NAME )

        # Operating System
        self.OS = str( QSysInfo.kernelType() ) # WINDOWS=winnt & LINUX=linux
        if self.OS == "winnt": # Unlocks icons in Krita for Menu Mode
            QApplication.setAttribute( Qt.AA_DontShowIconsInMenus, False )

        # Path Name
        self.directory_plugin = str( os.path.dirname( os.path.realpath( __file__ ) ) )

        # Widget Docker
        self.layout = uic.loadUi( os.path.join( self.directory_plugin, "picker_docker.ui" ), QWidget( self ) )
        self.setWidget( self.layout )

        # Settings
        self.dialog = uic.loadUi( os.path.join( self.directory_plugin, "picker_settings.ui" ), QDialog( self ) )
        self.dialog.setWindowTitle( f"{ DOCKER_NAME } : Settings" )
        self.dialog.accept() # Hides the Dialog

        # Panel Entries
        self.dialog.panel_index.addItem( panel_fill )
        self.dialog.panel_index.addItem( panel_square )
        self.dialog.panel_index.addItem( panel_hue )
        self.dialog.panel_index.addItem( panel_gamut )
        self.dialog.panel_index.addItem( panel_hexagon )
        self.dialog.panel_index.addItem( panel_luma )
        self.dialog.panel_index.addItem( panel_dot )
        self.dialog.panel_index.addItem( panel_mask )
    def Variables( self ):
        # Paths
        mask_set = os.path.join( self.directory_plugin, "MASK" )
        self.mask_set = os.path.join( mask_set, "SPHERE" )

        # Widget
        self.mode_index = 0
        self.cursor_inside = False
        self.active_ab = True
        self.cor = kac
        self.widget_press = False # cursor pressing widget
        self.slider_height = 15
        self.depth_previous = 0
        # Document
        self.doc = self.Current_Document()
        self.fill = False

        # Harmony
        self.harmony_index = 1 # 1-5
        self.harmony_rule = "Analogous" # "Monochromatic" "Complementary" "Analogous" "Triadic" "Tetradic"
        self.harmony_edit = False
        self.harmony_span = 0.2

        # Panels
        self.panel_index = panel_square
        self.zoom = False
        # Color Wheel
        self.wheel_mode = "DIGITAL" # "DIGITAL" "ANALOG"
        self.wheel_space = "HSV" # "HSV" "HSL" "HCY" "ARD"
        # Hue
        self.huecircle_shape = "Square" # "None" "Triangle" "Square" "Diamond"
        # Gamut
        self.gamut_mask = "None" # "None" "Triangle" "Square" "1 Circle" "2 Circle" "3 Pie" "Reset"
        self.gamut_profile = [
            [ ( 0.5, 0.5 ), ( 0.5, 0.1 ), ( 0.84641, 0.7 ), ( 0.15359, 0.7 ) ],
            [ ( 0.5, 0.5 ), ( 0.5, 0.1 ), ( 0.9, 0.5 ), ( 0.5, 0.9 ), ( 0.1, 0.5 ) ],
            [ ( 0.5, 0.5 ), ( 0.5, 0.1 ), ( 0.9, 0.5 ), ( 0.5, 0.9 ), ( 0.1, 0.5 ) ],
            [ ( 0.5, 0.275 ), ( 0.5, 0.1 ), ( 0.675, 0.275 ), ( 0.5, 0.45 ), ( 0.325, 0.275 ), ( 0.5, 0.725 ), ( 0.5, 0.55 ), ( 0.675, 0.725 ), ( 0.5, 0.9 ), ( 0.325, 0.725 ) ],
            [ ( 0.5, 0.5 ), ( 0.5, 0.15359 ), ( 0.8, 0.32679 ), ( 0.8, 0.67321 ), ( 0.5, 0.84641 ), ( 0.2, 0.67321 ), ( 0.2, 0.32679 ) ],
            ]
        # Dots
        self.dot_interpolation = "RGB"
        self.dot_dimension = 11
        self.dot_edit = False
        self.dot_1 = color_true.copy()
        self.dot_2 = color_true.copy()
        self.dot_3 = color_true.copy()
        self.dot_4 = color_true.copy()
        # Mask
        self.mask_live = {
            "b1" : False,
            "b2" : False,
            "b3" : False,
            "d1" : False,
            "d2" : False,
            "d3" : False,
            "d4" : False,
            "d5" : False,
            "d6" : False,
            "f1" : False,
            "f2" : False,
            "f3" : False,
            }
        self.mask_color = {
            "b1" : "#7f7f7f",
            "b2" : "#000000",
            "b3" : "#000000",
            "d1" : "#231402",
            "d2" : "#543713",
            "d3" : "#fe9f0e",
            "d4" : "#ffca32",
            "d5" : "#000000",
            "d6" : "#000000",
            "f1" : "#000000",
            "f2" : "#ffff96",
            "f3" : "#ffffff",
            }
        self.mask_alpha = {
            "b1" : 0.0,
            "b2" : 1.0,
            "b3" : 1.0,
            "d1" : 1.0,
            "d2" : 1.0,
            "d3" : 1.0,
            "d4" : 1.0,
            "d5" : 0.0,
            "d6" : 0.0,
            "f1" : 1.0,
            "f2" : 1.0,
            "f3" : 1.0,
            }
        self.mask_edit = False
        self.mask_write = False

        # Dialog UI
        self.ui_harmony = False
        self.ui_channel = True
        self.ui_mixer = False
        self.ui_pin = False
        self.ui_history = False

        # Pole
        self.pole_percent = 0.5
        self.pole_mix = color_true.copy()
        self.pole_cor_a = color_true.copy()
        self.pole_cor_n = color_true.copy()
        self.pole_cor_b = color_true.copy()
        # Mixers
        self.mixer_space = "HSV"
        self.mixer_count = 0
        self.mixer_widget = list()
        self.mixer_module = list()
        self.mixer_colors = list()
        # Pins
        self.pin_widget = list()
        self.pin_module = list()
        self.pin_cor = list()

        # Channels
        self.chan_aaa = False
        self.chan_rgb = False
        self.chan_cmy = False
        self.chan_cmyk = False
        self.chan_ryb = False
        self.chan_yuv = False
        self.chan_hsv = True
        self.chan_hsl = False
        self.chan_hcy = False
        self.chan_ard = False
        self.chan_xyz = False
        self.chan_xyy = False
        self.chan_lab = False
        self.chan_lch = False
        # Non Color
        self.chan_kkk = False
        self.chan_hex = False
        self.chan_sum = False
        # Locks
        self.lock_cmyk_4 = False

        # Hex
        self.hex_code = "#000000"

        # Channel Format
        self.disp_labels = False
        self.disp_values = False
        self.hue_shine = False

        # Shortcut
        self.key_1_chan = "[KEY 1]"
        self.key_2_chan = "[KEY 2]"
        self.key_3_chan = "[KEY 3]"
        self.key_4_chan = "[KEY 4]"
        self.key_1_factor = 1
        self.key_2_factor = 1
        self.key_3_factor = 1
        self.key_4_factor = 1

        # Annotations
        self.annotation_kra = False
        self.annotation_file = False

        # Color Space
        self.cs_luminosity = "ITU-R BT.709"
        self.cs_matrix = "sRGB (D65)"
        # Performance
        self.performance_release = False
        self.performance_inaccurate = False

        # Analyse
        self.analyse_display = False
        self.analyse_collection = None

        # Style Sheets
        self.bg_alpha = str( "background-color: rgba( 0, 0, 0, 50 );" )
    def Connections( self ):
        #region Panel Dot

        self.layout.dot_swap.clicked.connect( self.Dot_Swap )

        #endregion
        #region Panel Mask

        self.layout.fg_3_live.toggled.connect( self.Mask_Live_F3 )
        self.layout.fg_2_live.toggled.connect( self.Mask_Live_F2 )
        self.layout.fg_1_live.toggled.connect( self.Mask_Live_F1 )

        self.layout.dif_6_live.toggled.connect( self.Mask_Live_D6 )
        self.layout.dif_5_live.toggled.connect( self.Mask_Live_D5 )
        self.layout.dif_4_live.toggled.connect( self.Mask_Live_D4 )
        self.layout.dif_3_live.toggled.connect( self.Mask_Live_D3 )
        self.layout.dif_2_live.toggled.connect( self.Mask_Live_D2 )
        self.layout.dif_1_live.toggled.connect( self.Mask_Live_D1 )

        self.layout.bg_3_live.toggled.connect( self.Mask_Live_B3 )
        self.layout.bg_2_live.toggled.connect( self.Mask_Live_B2 )
        self.layout.bg_1_live.toggled.connect( self.Mask_Live_B1 )
        
        #endregion
        #region Locks

        self.layout.cmyk_4_label.toggled.connect( self.Lock_CMYK_4 )

        #endregion
        #region Channels Ranges

        # AAA
        self.layout.aaa_1_value.setMinimum( 0 )
        self.layout.aaa_1_value.setMaximum( krange["aaa_1"] )
        # RGB
        self.layout.rgb_1_value.setMinimum( 0 )
        self.layout.rgb_2_value.setMinimum( 0 )
        self.layout.rgb_3_value.setMinimum( 0 )
        self.layout.rgb_1_value.setMaximum( krange["rgb_1"] )
        self.layout.rgb_2_value.setMaximum( krange["rgb_2"] )
        self.layout.rgb_3_value.setMaximum( krange["rgb_3"] )
        # CMY
        self.layout.cmy_1_value.setMinimum( 0 )
        self.layout.cmy_2_value.setMinimum( 0 )
        self.layout.cmy_3_value.setMinimum( 0 )
        self.layout.cmy_1_value.setMaximum( krange["cmy_1"] )
        self.layout.cmy_2_value.setMaximum( krange["cmy_2"] )
        self.layout.cmy_3_value.setMaximum( krange["cmy_3"] )
        # CMYK
        self.layout.cmyk_1_value.setMinimum( 0 )
        self.layout.cmyk_2_value.setMinimum( 0 )
        self.layout.cmyk_3_value.setMinimum( 0 )
        self.layout.cmyk_4_value.setMinimum( 0 )
        self.layout.cmyk_1_value.setMaximum( krange["cmyk_1"] )
        self.layout.cmyk_2_value.setMaximum( krange["cmyk_2"] )
        self.layout.cmyk_3_value.setMaximum( krange["cmyk_3"] )
        self.layout.cmyk_4_value.setMaximum( krange["cmyk_4"] )
        # RYB
        self.layout.ryb_1_value.setMinimum( 0 )
        self.layout.ryb_2_value.setMinimum( 0 )
        self.layout.ryb_3_value.setMinimum( 0 )
        self.layout.ryb_1_value.setMaximum( krange["ryb_1"] )
        self.layout.ryb_2_value.setMaximum( krange["ryb_2"] )
        self.layout.ryb_3_value.setMaximum( krange["ryb_3"] )
        # YUV
        self.layout.yuv_1_value.setMinimum( 0 )
        self.layout.yuv_2_value.setMinimum( 0 )
        self.layout.yuv_3_value.setMinimum( 0 )
        self.layout.yuv_1_value.setMaximum( krange["yuv_1"] )
        self.layout.yuv_2_value.setMaximum( krange["yuv_2"] )
        self.layout.yuv_3_value.setMaximum( krange["yuv_3"] )

        # HSV
        self.layout.hsv_1_value.setMinimum( 0 )
        self.layout.hsv_2_value.setMinimum( 0 )
        self.layout.hsv_3_value.setMinimum( 0 )
        self.layout.hsv_1_value.setMaximum( krange["hsv_1"] )
        self.layout.hsv_2_value.setMaximum( krange["hsv_2"] )
        self.layout.hsv_3_value.setMaximum( krange["hsv_3"] )
        # HSL
        self.layout.hsl_1_value.setMinimum( 0 )
        self.layout.hsl_2_value.setMinimum( 0 )
        self.layout.hsl_3_value.setMinimum( 0 )
        self.layout.hsl_1_value.setMaximum( krange["hsl_1"] )
        self.layout.hsl_2_value.setMaximum( krange["hsl_2"] )
        self.layout.hsl_3_value.setMaximum( krange["hsl_3"] )
        # HCY
        self.layout.hcy_1_value.setMinimum( 0 )
        self.layout.hcy_2_value.setMinimum( 0 )
        self.layout.hcy_3_value.setMinimum( 0 )
        self.layout.hcy_1_value.setMaximum( krange["hcy_1"] )
        self.layout.hcy_2_value.setMaximum( krange["hcy_2"] )
        self.layout.hcy_3_value.setMaximum( krange["hcy_3"] )
        # ARD
        self.layout.ard_1_value.setMinimum( 0 )
        self.layout.ard_2_value.setMinimum( 0 )
        self.layout.ard_3_value.setMinimum( 0 )
        self.layout.ard_1_value.setMaximum( krange["ard_1"] )
        self.layout.ard_2_value.setMaximum( krange["ard_2"] )
        self.layout.ard_3_value.setMaximum( krange["ard_3"] )

        # XYZ
        self.layout.xyz_1_value.setMinimum( 0 )
        self.layout.xyz_2_value.setMinimum( 0 )
        self.layout.xyz_3_value.setMinimum( 0 )
        self.layout.xyz_1_value.setMaximum( krange["xyz_1"] )
        self.layout.xyz_2_value.setMaximum( krange["xyz_2"] )
        self.layout.xyz_3_value.setMaximum( krange["xyz_3"] )
        # XYY
        self.layout.xyy_1_value.setMinimum( 0 )
        self.layout.xyy_2_value.setMinimum( 0 )
        self.layout.xyy_3_value.setMinimum( 0 )
        self.layout.xyy_1_value.setMaximum( krange["xyy_1"] )
        self.layout.xyy_2_value.setMaximum( krange["xyy_2"] )
        self.layout.xyy_3_value.setMaximum( krange["xyy_3"] )
        # LAB
        self.layout.lab_1_value.setMinimum( 0 )
        self.layout.lab_2_value.setMinimum( 0 )
        self.layout.lab_3_value.setMinimum( 0 )
        self.layout.lab_1_value.setMaximum( krange["lab_1"] )
        self.layout.lab_2_value.setMaximum( krange["lab_2"] )
        self.layout.lab_3_value.setMaximum( krange["lab_3"] )

        # LCH
        self.layout.lch_1_value.setMinimum( 0 )
        self.layout.lch_2_value.setMinimum( 0 )
        self.layout.lch_3_value.setMinimum( 0 )
        self.layout.lch_1_value.setMaximum( krange["lch_1"] )
        self.layout.lch_2_value.setMaximum( krange["lch_2"] )
        self.layout.lch_3_value.setMaximum( krange["lch_3"] )

        #endregion
        #region Channels Connections

        # AAA
        self.layout.aaa_1_value.valueChanged.connect( self.Channel_AAA_1_Value )
        # RGB
        self.layout.rgb_1_value.valueChanged.connect( self.Channel_RGB_1_Value )
        self.layout.rgb_2_value.valueChanged.connect( self.Channel_RGB_2_Value )
        self.layout.rgb_3_value.valueChanged.connect( self.Channel_RGB_3_Value )
        # CMY
        self.layout.cmy_1_value.valueChanged.connect( self.Channel_CMY_1_Value )
        self.layout.cmy_2_value.valueChanged.connect( self.Channel_CMY_2_Value )
        self.layout.cmy_3_value.valueChanged.connect( self.Channel_CMY_3_Value )
        # CMYK
        self.layout.cmyk_1_value.valueChanged.connect( self.Channel_CMYK_1_Value )
        self.layout.cmyk_2_value.valueChanged.connect( self.Channel_CMYK_2_Value )
        self.layout.cmyk_3_value.valueChanged.connect( self.Channel_CMYK_3_Value )
        self.layout.cmyk_4_value.valueChanged.connect( self.Channel_CMYK_4_Value )
        # RYB
        self.layout.ryb_1_value.valueChanged.connect( self.Channel_RYB_1_Value )
        self.layout.ryb_2_value.valueChanged.connect( self.Channel_RYB_2_Value )
        self.layout.ryb_3_value.valueChanged.connect( self.Channel_RYB_3_Value )
        # YUV
        self.layout.yuv_1_value.valueChanged.connect( self.Channel_YUV_1_Value )
        self.layout.yuv_2_value.valueChanged.connect( self.Channel_YUV_2_Value )
        self.layout.yuv_3_value.valueChanged.connect( self.Channel_YUV_3_Value )

        # HSV
        self.layout.hsv_1_value.valueChanged.connect( self.Channel_HSV_1_Value )
        self.layout.hsv_2_value.valueChanged.connect( self.Channel_HSV_2_Value )
        self.layout.hsv_3_value.valueChanged.connect( self.Channel_HSV_3_Value )
        # HSL
        self.layout.hsl_1_value.valueChanged.connect( self.Channel_HSL_1_Value )
        self.layout.hsl_2_value.valueChanged.connect( self.Channel_HSL_2_Value )
        self.layout.hsl_3_value.valueChanged.connect( self.Channel_HSL_3_Value )
        # HCY
        self.layout.hcy_1_value.valueChanged.connect( self.Channel_HCY_1_Value )
        self.layout.hcy_2_value.valueChanged.connect( self.Channel_HCY_2_Value )
        self.layout.hcy_3_value.valueChanged.connect( self.Channel_HCY_3_Value )
        # ARD
        self.layout.ard_1_value.valueChanged.connect( self.Channel_ARD_1_Value )
        self.layout.ard_2_value.valueChanged.connect( self.Channel_ARD_2_Value )
        self.layout.ard_3_value.valueChanged.connect( self.Channel_ARD_3_Value )

        # XYZ
        self.layout.xyz_1_value.valueChanged.connect( self.Channel_XYZ_1_Value )
        self.layout.xyz_2_value.valueChanged.connect( self.Channel_XYZ_2_Value )
        self.layout.xyz_3_value.valueChanged.connect( self.Channel_XYZ_3_Value )
        # XYY
        self.layout.xyy_1_value.valueChanged.connect( self.Channel_XYY_1_Value )
        self.layout.xyy_2_value.valueChanged.connect( self.Channel_XYY_2_Value )
        self.layout.xyy_3_value.valueChanged.connect( self.Channel_XYY_3_Value )
        # LAB*
        self.layout.lab_1_value.valueChanged.connect( self.Channel_LAB_1_Value )
        self.layout.lab_2_value.valueChanged.connect( self.Channel_LAB_2_Value )
        self.layout.lab_3_value.valueChanged.connect( self.Channel_LAB_3_Value )

        # LCH
        self.layout.lch_1_value.valueChanged.connect( self.Channel_LCH_1_Value )
        self.layout.lch_2_value.valueChanged.connect( self.Channel_LCH_2_Value )
        self.layout.lch_3_value.valueChanged.connect( self.Channel_LCH_3_Value )

        # KKK
        self.layout.kkk_1_value.valueChanged.connect( self.Channel_KKK_1_Value )

        # HEX
        self.layout.hex_string.returnPressed.connect( lambda: self.Color_HEX( self.layout.hex_string.text() ) )

        #endregion
        #region History

        self.layout.history_list.clicked.connect( self.History_APPLY )

        #endregion
        #region Footer

        self.layout.fill.toggled.connect( self.Menu_FILL )
        self.layout.sample_screen.clicked.connect( self.Menu_SampleScreen )
        self.layout.settings.clicked.connect( self.Menu_Settings )

        #endregion
        #region Dialog Header

        self.dialog.harmony.toggled.connect( self.Menu_Harmony )
        self.dialog.channel.toggled.connect( self.Menu_Channel )
        self.dialog.mixer.toggled.connect( self.Menu_Mixer )
        self.dialog.pin.toggled.connect( self.Menu_Pin )
        self.dialog.history.toggled.connect( self.Menu_History )

        #endregion
        #region Dialog Option

        # Panels
        self.dialog.panel_index.currentTextChanged.connect( self.Panel_Index )
        # Wheel
        self.dialog.wheel_mode.currentTextChanged.connect( self.Wheel_Mode )
        self.dialog.wheel_space.currentTextChanged.connect( self.Wheel_Space )
        # Analyse
        self.dialog.analyse_document.clicked.connect( self.Analyse_Document )
        self.dialog.analyse_display.toggled.connect( self.Analyse_Display )
        # Mixers
        self.dialog.mixer_space.currentTextChanged.connect( self.Mixer_Space )
        self.dialog.mixer_count.valueChanged.connect( self.Mixer_Count )

        #endregion
        #region Dialog Color

        # Channels
        self.dialog.chan_aaa.toggled.connect( self.Channel_AAA )
        self.dialog.chan_rgb.toggled.connect( self.Channel_RGB )
        self.dialog.chan_cmy.toggled.connect( self.Channel_CMY )
        self.dialog.chan_cmyk.toggled.connect( self.Channel_CMYK )
        self.dialog.chan_ryb.toggled.connect( self.Channel_RYB )
        self.dialog.chan_yuv.toggled.connect( self.Channel_YUV )
        self.dialog.chan_hsv.toggled.connect( self.Channel_HSV )
        self.dialog.chan_hsl.toggled.connect( self.Channel_HSL )
        self.dialog.chan_hcy.toggled.connect( self.Channel_HCY )
        self.dialog.chan_ard.toggled.connect( self.Channel_ARD )
        self.dialog.chan_xyz.toggled.connect( self.Channel_XYZ )
        self.dialog.chan_xyy.toggled.connect( self.Channel_XYY )
        self.dialog.chan_lab.toggled.connect( self.Channel_LAB )
        self.dialog.chan_lch.toggled.connect( self.Channel_LCH )

        # Ranges
        self.dialog.range_aaa.valueChanged.connect( self.Range_AAA )
        self.dialog.range_rgb.valueChanged.connect( self.Range_RGB )
        self.dialog.range_cmy.valueChanged.connect( self.Range_CMY )
        self.dialog.range_cmyk.valueChanged.connect( self.Range_CMYK )
        self.dialog.range_ryb.valueChanged.connect( self.Range_RYB )
        self.dialog.range_yuv.valueChanged.connect( self.Range_YUV )
        self.dialog.range_hue.valueChanged.connect( self.Range_HUE )
        self.dialog.range_hsv.valueChanged.connect( self.Range_HSV )
        self.dialog.range_hsl.valueChanged.connect( self.Range_HSL )
        self.dialog.range_hcy.valueChanged.connect( self.Range_HCY )
        self.dialog.range_ard.valueChanged.connect( self.Range_ARD )
        self.dialog.range_xyz.valueChanged.connect( self.Range_XYZ )
        self.dialog.range_xyy.valueChanged.connect( self.Range_XYY )
        self.dialog.range_lab.valueChanged.connect( self.Range_LAB )
        self.dialog.range_lch.valueChanged.connect( self.Range_LCH )

        # Resets
        self.dialog.reset_aaa.clicked.connect( self.Reset_AAA )
        self.dialog.reset_rgb.clicked.connect( self.Reset_RGB )
        self.dialog.reset_cmy.clicked.connect( self.Reset_CMY )
        self.dialog.reset_cmyk.clicked.connect( self.Reset_CMYK )
        self.dialog.reset_ryb.clicked.connect( self.Reset_RYB )
        self.dialog.reset_yuv.clicked.connect( self.Reset_YUV )
        self.dialog.reset_hue.clicked.connect( self.Reset_HUE )
        self.dialog.reset_hsv.clicked.connect( self.Reset_HSV )
        self.dialog.reset_hsl.clicked.connect( self.Reset_HSL )
        self.dialog.reset_hcy.clicked.connect( self.Reset_HCY )
        self.dialog.reset_ard.clicked.connect( self.Reset_ARD )
        self.dialog.reset_xyz.clicked.connect( self.Reset_XYZ )
        self.dialog.reset_xyy.clicked.connect( self.Reset_XYY )
        self.dialog.reset_lab.clicked.connect( self.Reset_LAB )
        self.dialog.reset_lch.clicked.connect( self.Reset_LCH )

        # Non Color Kelvin
        self.dialog.chan_kkk.toggled.connect( self.Channel_KKK )
        # Non Color Hex
        self.dialog.chan_hex.toggled.connect( self.Channel_HEX )
        self.dialog.chan_sum.toggled.connect( self.Channel_SUM )

        # Format
        self.dialog.disp_labels.toggled.connect( self.Display_Labels )
        self.dialog.disp_values.toggled.connect( self.Display_Values )
        self.dialog.hue_shine.toggled.connect( self.Hue_Shine )

        # Reference
        self.dialog.name_display.clicked.connect( self.Color_Name )
        self.dialog.names_closest.clicked.connect( self.HEX_Closest )

        # Shortcuts
        self.dialog.key_1_chan.currentTextChanged.connect( self.Key_1_Channel )
        self.dialog.key_2_chan.currentTextChanged.connect( self.Key_2_Channel )
        self.dialog.key_3_chan.currentTextChanged.connect( self.Key_3_Channel )
        self.dialog.key_4_chan.currentTextChanged.connect( self.Key_4_Channel )
        self.dialog.key_1_factor.valueChanged.connect( self.Key_1_Factor )
        self.dialog.key_2_factor.valueChanged.connect( self.Key_2_Factor )
        self.dialog.key_3_factor.valueChanged.connect( self.Key_3_Factor )
        self.dialog.key_4_factor.valueChanged.connect( self.Key_4_Factor )

        #endregion
        #region Dialog System

        # Color Space
        self.dialog.cs_luminosity.currentTextChanged.connect( self.CS_Luminosity )
        self.dialog.cs_matrix.currentTextChanged.connect( self.CS_Matrix )

        # Performance
        self.dialog.performance_release.toggled.connect( self.Performace_Release )
        self.dialog.performance_inaccurate.toggled.connect( self.Performace_Inaccurate )

        #endregion
        #region Dialog Footer

        self.dialog.manual.clicked.connect( self.Menu_Manual )
        self.dialog.license.clicked.connect( self.Menu_License )

        #endregion
        #region Event Filter

        # Panel
        self.layout.panel_set.installEventFilter( self )
        self.layout.panel_dot.installEventFilter( self )
        self.layout.panel_mask.installEventFilter( self )
        # Channel
        self.layout.aaa_slider.installEventFilter( self )
        self.layout.rgb_slider.installEventFilter( self )
        self.layout.cmy_slider.installEventFilter( self )
        self.layout.cmyk_slider.installEventFilter( self )
        self.layout.ryb_slider.installEventFilter( self )
        self.layout.yuv_slider.installEventFilter( self )
        self.layout.hsv_slider.installEventFilter( self )
        self.layout.hsl_slider.installEventFilter( self )
        self.layout.hcy_slider.installEventFilter( self )
        self.layout.ard_slider.installEventFilter( self )
        self.layout.xyz_slider.installEventFilter( self )
        self.layout.xyy_slider.installEventFilter( self )
        self.layout.lab_slider.installEventFilter( self )
        self.layout.lch_slider.installEventFilter( self )
        self.layout.kkk_slider.installEventFilter( self )
        # Mixer
        self.layout.pole_slider.installEventFilter( self )
        self.layout.mixer_set.installEventFilter( self )
        # Footer
        self.layout.mode.installEventFilter( self ) # Mode Index
        self.layout.history_list.installEventFilter( self ) # History Clear

        #endregion
    def Modules( self ):
        #region Notifier

        self.notifier = Krita.instance().notifier()
        self.notifier.applicationClosing.connect( self.Application_Closing )
        self.notifier.configurationChanged.connect( self.Configuration_Changed )
        self.notifier.imageClosed.connect( self.Image_Closed )
        self.notifier.imageCreated.connect( self.Image_Created )
        self.notifier.imageSaved.connect( self.Image_Saved )
        self.notifier.viewClosed.connect( self.View_Closed )
        self.notifier.viewCreated.connect( self.View_Created )
        self.notifier.windowCreated.connect( self.Window_Created )
        self.notifier.windowIsBeingCreated.connect( self.Window_IsBeingCreated )

        #endregion
        #region Calculations

        # Geometry
        self.geometry = Geometry()
        # Convert
        self.convert = Convert()
        self.convert.Set_Document( "RGB", "U8", "sRGB-elle-V2-srgtrc.icc" )
        self.convert.Set_Hue( zero )
        self.convert.Set_Luminosity( self.cs_luminosity )
        self.convert.Set_Gamma( gamma_y, gamma_l )
        self.convert.Set_Matrix( self.cs_matrix )
        # Analyse
        self.analyse = Analyse()

        #endregion
        #region Header

        self.color_header = Color_Header( self.layout.color_header )
        self.color_header.Set_Mode_AB( True ) # FG
        self.color_header.Set_Progress( 1 )
        self.color_header.SIGNAL_SHIFT.connect( self.Header_Shift )
        self.color_header.SIGNAL_SWAP.connect( self.Header_Swap )
        self.color_header.SIGNAL_RANDOM.connect( self.Color_Random )
        self.color_header.SIGNAL_COMP.connect( self.Color_Complementary )

        #endregion
        #region Harmony

        self.harmony_swatch = Harmony_Swatch( self.layout.harmony_swatch )
        self.harmony_swatch.SIGNAL_RULE.connect( self.Harmony_Rule )
        self.harmony_swatch.SIGNAL_EDIT.connect( self.Harmony_Edit )
        self.harmony_swatch.SIGNAL_INDEX.connect( self.Harmony_Index )

        self.harmony_spread = Harmony_Spread( self.layout.harmony_spread )
        self.harmony_spread.SIGNAL_SPAN.connect( self.Harmony_Spread )
        self.harmony_spread.SIGNAL_RELEASE.connect( self.Pigmento_RELEASE )

        #endregion
        #region Panel FGC

        self.panel_fill = Panel_Fill( self.layout.panel_fill )

        #endregion
        #region Panel Square

        self.panel_square = Panel_Square( self.layout.panel_square )
        self.panel_square.Init_Convert( self.convert )
        self.panel_square.Set_Tangent_Range( 360 )
        self.panel_square.Set_ColorSpace_inDocument( self.directory_plugin, "RGB", self.wheel_space, "4" ) # Square
        
        self.panel_square.SIGNAL_VALUE.connect( self.Square_Value )
        self.panel_square.SIGNAL_TAN.connect( self.Square_Tangent )
        self.panel_square.SIGNAL_RELEASE.connect( self.Pigmento_RELEASE )
        self.panel_square.SIGNAL_PIN_INDEX.connect( self.Pin_Apply )
        self.panel_square.SIGNAL_PIN_EDIT.connect( self.Square_Pin )

        #endregion
        #region Panel HUE

        self.panel_huecircle = Panel_HueCircle( self.layout.panel_hue )
        self.panel_huecircle.Init_Convert( self.convert )
        self.panel_huecircle.SIGNAL_VALUE.connect( self.HueCircle_Value )
        self.panel_huecircle.SIGNAL_RELEASE.connect( self.Pigmento_RELEASE )
        self.panel_huecircle.SIGNAL_SUBPANEL.connect( self.HueCircle_SubPanel )

        self.panel_huesubpanel = Panel_Square( self.layout.panel_huesubpanel )
        self.panel_huesubpanel.Init_Convert( self.convert )
        self.panel_huesubpanel.Set_Tangent_Range( 360 )
        self.panel_huesubpanel.Set_ColorSpace_inDocument( self.directory_plugin, "RGB", self.wheel_space, "4" ) # Square
        self.panel_huesubpanel.SIGNAL_VALUE.connect( self.Square_Value )
        self.panel_huesubpanel.SIGNAL_TAN.connect( self.Square_Tangent )
        self.panel_huesubpanel.SIGNAL_RELEASE.connect( self.Pigmento_RELEASE )
        self.panel_huesubpanel.SIGNAL_PIN_INDEX.connect( self.Pin_Apply )
        self.panel_huesubpanel.SIGNAL_PIN_EDIT.connect( self.Square_Pin )

        #endregion
        #region Panel Gamut

        self.panel_gamut = Panel_Gamut( self.layout.panel_gamut )
        self.panel_gamut.Init_Convert( self.convert )
        self.panel_gamut.Set_ColorSpace_inDocument( self.directory_plugin, "RGB", self.wheel_space, "D" ) # DIGITAL
        self.panel_gamut.SIGNAL_VALUE.connect( self.Gamut_Value )
        self.panel_gamut.SIGNAL_TAN.connect( self.Gamut_Tangent )
        self.panel_gamut.SIGNAL_RELEASE.connect( self.Pigmento_RELEASE )
        self.panel_gamut.SIGNAL_MASK.connect( self.Gamut_Mask )
        self.panel_gamut.SIGNAL_PROFILE.connect( self.Gamut_Profile )
        self.panel_gamut.SIGNAL_PIN_INDEX.connect( self.Pin_Apply )
        self.panel_gamut.SIGNAL_PIN_EDIT.connect( self.Gamut_Pin )

        #endregion
        #region Panel Hexagon

        self.panel_hexagon = Panel_Hexagon( self.layout.panel_hexagon )
        self.panel_hexagon.Init_Convert( self.convert )
        self.panel_hexagon.Set_ColorSpace_inDocument( self.directory_plugin, "RGB" )

        self.panel_hexagon.SIGNAL_VALUE.connect( self.Hexagon_Value )
        self.panel_hexagon.SIGNAL_TAN.connect( self.Hexagon_Depth )
        self.panel_hexagon.SIGNAL_RELEASE.connect( self.Pigmento_RELEASE )
        self.panel_hexagon.SIGNAL_PIN_INDEX.connect( self.Pin_Apply )
        self.panel_hexagon.SIGNAL_PIN_EDIT.connect( self.Hexagon_Pin )

        #endregion
        #region Panel Luma

        self.panel_luma = Panel_Square( self.layout.panel_luma )
        self.panel_luma.Init_Convert( self.convert )
        self.panel_luma.Set_Tangent_Range( 255 )
        self.panel_luma.Set_ColorSpace_inDocument( self.directory_plugin, "RGB", "YUV", "4" ) # Square

        self.panel_luma.SIGNAL_VALUE.connect( self.Luma_Value )
        self.panel_luma.SIGNAL_TAN.connect( self.Luma_Tangent )
        self.panel_luma.SIGNAL_RELEASE.connect( self.Pigmento_RELEASE )
        self.panel_luma.SIGNAL_PIN_INDEX.connect( self.Pin_Apply )
        self.panel_luma.SIGNAL_PIN_EDIT.connect( self.Luma_Pin )

        #endregion
        #region Panel Dot

        self.panel_dot = Panel_Dot( self.layout.panel_dot )
        self.panel_dot.Init_Convert( self.convert )
        self.panel_dot.SIGNAL_VALUE.connect( self.Dot_Value )
        self.panel_dot.SIGNAL_RELEASE.connect( self.Pigmento_RELEASE )
        self.panel_dot.SIGNAL_INTERPOLATION.connect( self.Dot_Interpolation )
        self.panel_dot.SIGNAL_DIMENSION.connect( self.Dot_Dimension )
        self.panel_dot.SIGNAL_EDIT.connect( self.Dot_Edit )
        self.panel_dot.SIGNAL_ZORN.connect( self.Dot_Zorn )

        #endregion
        #region Dot Pins

        self.pin_d1 = Pin_Color( self.layout.dot_1 )
        self.pin_d1.SIGNAL_APPLY.connect( self.Dot_Apply_1 )
        self.pin_d1.SIGNAL_SAVE.connect( self.Dot_Save_1 )
        self.pin_d1.SIGNAL_CLEAN.connect( self.Dot_Clean_1 )
        self.pin_d1.SIGNAL_TEXT.connect( self.Label_String )

        self.pin_d2 = Pin_Color( self.layout.dot_2 )
        self.pin_d2.SIGNAL_APPLY.connect( self.Dot_Apply_2 )
        self.pin_d2.SIGNAL_SAVE.connect( self.Dot_Save_2 )
        self.pin_d2.SIGNAL_CLEAN.connect( self.Dot_Clean_2 )
        self.pin_d2.SIGNAL_TEXT.connect( self.Label_String )

        self.pin_d3 = Pin_Color( self.layout.dot_3 )
        self.pin_d3.SIGNAL_APPLY.connect( self.Dot_Apply_3 )
        self.pin_d3.SIGNAL_SAVE.connect( self.Dot_Save_3 )
        self.pin_d3.SIGNAL_CLEAN.connect( self.Dot_Clean_3 )
        self.pin_d3.SIGNAL_TEXT.connect( self.Label_String )

        self.pin_d4 = Pin_Color( self.layout.dot_4 )
        self.pin_d4.SIGNAL_APPLY.connect( self.Dot_Apply_4 )
        self.pin_d4.SIGNAL_SAVE.connect( self.Dot_Save_4 )
        self.pin_d4.SIGNAL_CLEAN.connect( self.Dot_Clean_4 )
        self.pin_d4.SIGNAL_TEXT.connect( self.Label_String )

        #endregion
        #region Panel Mask

        self.panel_mask = Panel_Mask( self.layout.panel_mask )
        self.panel_mask.Set_Directory( os.path.join( self.directory_plugin, "MASK" ) )
        self.panel_mask.SIGNAL_VALUE.connect( self.Mask_Value )
        self.panel_mask.SIGNAL_RELEASE.connect( self.Pigmento_RELEASE )
        self.panel_mask.SIGNAL_MASKSET.connect( self.Mask_Set )
        self.panel_mask.SIGNAL_EDIT.connect( self.Mask_Edit )
        self.panel_mask.SIGNAL_RESET.connect( self.Mask_Read )
        self.panel_mask.SIGNAL_LIVE_OFF.connect( self.Mask_Live_Close )

        #endregion
        #region Mask Pins

        self.mask_f3 = Pin_Color( self.layout.fg_3_color )
        self.mask_f2 = Pin_Color( self.layout.fg_2_color )
        self.mask_f1 = Pin_Color( self.layout.fg_1_color )
        self.mask_d6 = Pin_Color( self.layout.dif_6_color )
        self.mask_d5 = Pin_Color( self.layout.dif_5_color )
        self.mask_d4 = Pin_Color( self.layout.dif_4_color )
        self.mask_d3 = Pin_Color( self.layout.dif_3_color )
        self.mask_d2 = Pin_Color( self.layout.dif_2_color )
        self.mask_d1 = Pin_Color( self.layout.dif_1_color )
        self.mask_b3 = Pin_Color( self.layout.bg_3_color )
        self.mask_b2 = Pin_Color( self.layout.bg_2_color )
        self.mask_b1 = Pin_Color( self.layout.bg_1_color )

        self.mask_f3.Set_Alpha( 1.0 )
        self.mask_f2.Set_Alpha( 1.0 )
        self.mask_f1.Set_Alpha( 1.0 )
        self.mask_d6.Set_Alpha( 1.0 )
        self.mask_d5.Set_Alpha( 1.0 )
        self.mask_d4.Set_Alpha( 1.0 )
        self.mask_d3.Set_Alpha( 1.0 )
        self.mask_d2.Set_Alpha( 1.0 )
        self.mask_d1.Set_Alpha( 1.0 )
        self.mask_b3.Set_Alpha( 1.0 )
        self.mask_b2.Set_Alpha( 1.0 )
        self.mask_b1.Set_Alpha( 1.0 )

        self.mask_f3.SIGNAL_APPLY.connect( self.Mask_Apply_F3 )
        self.mask_f2.SIGNAL_APPLY.connect( self.Mask_Apply_F2 )
        self.mask_f1.SIGNAL_APPLY.connect( self.Mask_Apply_F1 )
        self.mask_d6.SIGNAL_APPLY.connect( self.Mask_Apply_D6 )
        self.mask_d5.SIGNAL_APPLY.connect( self.Mask_Apply_D5 )
        self.mask_d4.SIGNAL_APPLY.connect( self.Mask_Apply_D4 )
        self.mask_d3.SIGNAL_APPLY.connect( self.Mask_Apply_D3 )
        self.mask_d2.SIGNAL_APPLY.connect( self.Mask_Apply_D2 )
        self.mask_d1.SIGNAL_APPLY.connect( self.Mask_Apply_D1 )
        self.mask_b3.SIGNAL_APPLY.connect( self.Mask_Apply_B3 )
        self.mask_b2.SIGNAL_APPLY.connect( self.Mask_Apply_B2 )
        self.mask_b1.SIGNAL_APPLY.connect( self.Mask_Apply_B1 )

        self.mask_f3.SIGNAL_SAVE.connect( self.Mask_Save_F3 )
        self.mask_f2.SIGNAL_SAVE.connect( self.Mask_Save_F2 )
        self.mask_f1.SIGNAL_SAVE.connect( self.Mask_Save_F1 )
        self.mask_d6.SIGNAL_SAVE.connect( self.Mask_Save_D6 )
        self.mask_d5.SIGNAL_SAVE.connect( self.Mask_Save_D5 )
        self.mask_d4.SIGNAL_SAVE.connect( self.Mask_Save_D4 )
        self.mask_d3.SIGNAL_SAVE.connect( self.Mask_Save_D3 )
        self.mask_d2.SIGNAL_SAVE.connect( self.Mask_Save_D2 )
        self.mask_d1.SIGNAL_SAVE.connect( self.Mask_Save_D1 )
        self.mask_b3.SIGNAL_SAVE.connect( self.Mask_Save_B3 )
        self.mask_b2.SIGNAL_SAVE.connect( self.Mask_Save_B2 )
        self.mask_b1.SIGNAL_SAVE.connect( self.Mask_Save_B1 )

        self.mask_f3.SIGNAL_CLEAN.connect( self.Mask_Clean_F3 )
        self.mask_f2.SIGNAL_CLEAN.connect( self.Mask_Clean_F2 )
        self.mask_f1.SIGNAL_CLEAN.connect( self.Mask_Clean_F1 )
        self.mask_d6.SIGNAL_CLEAN.connect( self.Mask_Clean_D6 )
        self.mask_d5.SIGNAL_CLEAN.connect( self.Mask_Clean_D5 )
        self.mask_d4.SIGNAL_CLEAN.connect( self.Mask_Clean_D4 )
        self.mask_d3.SIGNAL_CLEAN.connect( self.Mask_Clean_D3 )
        self.mask_d2.SIGNAL_CLEAN.connect( self.Mask_Clean_D2 )
        self.mask_d1.SIGNAL_CLEAN.connect( self.Mask_Clean_D1 )
        self.mask_b3.SIGNAL_CLEAN.connect( self.Mask_Clean_B3 )
        self.mask_b2.SIGNAL_CLEAN.connect( self.Mask_Clean_B2 )
        self.mask_b1.SIGNAL_CLEAN.connect( self.Mask_Clean_B1 )

        self.mask_f3.SIGNAL_ALPHA.connect( self.Mask_Alpha_F3 )
        self.mask_f2.SIGNAL_ALPHA.connect( self.Mask_Alpha_F2 )
        self.mask_f1.SIGNAL_ALPHA.connect( self.Mask_Alpha_F1 )
        self.mask_d6.SIGNAL_ALPHA.connect( self.Mask_Alpha_D6 )
        self.mask_d5.SIGNAL_ALPHA.connect( self.Mask_Alpha_D5 )
        self.mask_d4.SIGNAL_ALPHA.connect( self.Mask_Alpha_D4 )
        self.mask_d3.SIGNAL_ALPHA.connect( self.Mask_Alpha_D3 )
        self.mask_d2.SIGNAL_ALPHA.connect( self.Mask_Alpha_D2 )
        self.mask_d1.SIGNAL_ALPHA.connect( self.Mask_Alpha_D1 )
        self.mask_b3.SIGNAL_ALPHA.connect( self.Mask_Alpha_B3 )
        self.mask_b2.SIGNAL_ALPHA.connect( self.Mask_Alpha_B2 )
        self.mask_b1.SIGNAL_ALPHA.connect( self.Mask_Alpha_B1 )

        self.mask_f3.SIGNAL_TEXT.connect( self.Label_String )
        self.mask_f2.SIGNAL_TEXT.connect( self.Label_String )
        self.mask_f1.SIGNAL_TEXT.connect( self.Label_String )
        self.mask_d6.SIGNAL_TEXT.connect( self.Label_String )
        self.mask_d5.SIGNAL_TEXT.connect( self.Label_String )
        self.mask_d4.SIGNAL_TEXT.connect( self.Label_String )
        self.mask_d3.SIGNAL_TEXT.connect( self.Label_String )
        self.mask_d2.SIGNAL_TEXT.connect( self.Label_String )
        self.mask_d1.SIGNAL_TEXT.connect( self.Label_String )
        self.mask_b3.SIGNAL_TEXT.connect( self.Label_String )
        self.mask_b2.SIGNAL_TEXT.connect( self.Label_String )
        self.mask_b1.SIGNAL_TEXT.connect( self.Label_String )

        #endregion
        #region Sliders Module

        # AAA
        self.aaa_1_slider = Channel_Slider( self.layout.aaa_1_slider )
        self.aaa_1_slider.Set_Mode( "LINEAR" )
        self.aaa_1_slider.Set_Limits( 0, 0.5, 1 )
        self.aaa_1_slider.Set_Stops( stops["aaa_1"] )
        # RGB
        self.rgb_1_slider = Channel_Slider( self.layout.rgb_1_slider )
        self.rgb_2_slider = Channel_Slider( self.layout.rgb_2_slider )
        self.rgb_3_slider = Channel_Slider( self.layout.rgb_3_slider )
        self.rgb_1_slider.Set_Mode( "LINEAR" )
        self.rgb_2_slider.Set_Mode( "LINEAR" )
        self.rgb_3_slider.Set_Mode( "LINEAR" )
        self.rgb_1_slider.Set_Limits( 0, 0.5, 1 )
        self.rgb_2_slider.Set_Limits( 0, 0.5, 1 )
        self.rgb_3_slider.Set_Limits( 0, 0.5, 1 )
        self.rgb_1_slider.Set_Stops( stops["rgb_1"] )
        self.rgb_2_slider.Set_Stops( stops["rgb_2"] )
        self.rgb_3_slider.Set_Stops( stops["rgb_3"] )
        # CMY
        self.cmy_1_slider = Channel_Slider( self.layout.cmy_1_slider )
        self.cmy_2_slider = Channel_Slider( self.layout.cmy_2_slider )
        self.cmy_3_slider = Channel_Slider( self.layout.cmy_3_slider )
        self.cmy_1_slider.Set_Mode( "LINEAR" )
        self.cmy_2_slider.Set_Mode( "LINEAR" )
        self.cmy_3_slider.Set_Mode( "LINEAR" )
        self.cmy_1_slider.Set_Limits( 0, 0.5, 1 )
        self.cmy_2_slider.Set_Limits( 0, 0.5, 1 )
        self.cmy_3_slider.Set_Limits( 0, 0.5, 1 )
        self.cmy_1_slider.Set_Stops( stops["cmy_1"] )
        self.cmy_2_slider.Set_Stops( stops["cmy_2"] )
        self.cmy_3_slider.Set_Stops( stops["cmy_3"] )
        # CMYK
        self.cmyk_1_slider = Channel_Slider( self.layout.cmyk_1_slider )
        self.cmyk_2_slider = Channel_Slider( self.layout.cmyk_2_slider )
        self.cmyk_3_slider = Channel_Slider( self.layout.cmyk_3_slider )
        self.cmyk_4_slider = Channel_Slider( self.layout.cmyk_4_slider )
        self.cmyk_1_slider.Set_Mode( "LINEAR" )
        self.cmyk_2_slider.Set_Mode( "LINEAR" )
        self.cmyk_3_slider.Set_Mode( "LINEAR" )
        self.cmyk_4_slider.Set_Mode( "LINEAR" )
        self.cmyk_1_slider.Set_Limits( 0, 0.5, 1 )
        self.cmyk_2_slider.Set_Limits( 0, 0.5, 1 )
        self.cmyk_3_slider.Set_Limits( 0, 0.5, 1 )
        self.cmyk_4_slider.Set_Limits( 0, 0.5, 1 )
        self.cmyk_1_slider.Set_Stops( stops["cmyk_1"] )
        self.cmyk_2_slider.Set_Stops( stops["cmyk_2"] )
        self.cmyk_3_slider.Set_Stops( stops["cmyk_3"] )
        self.cmyk_4_slider.Set_Stops( stops["cmyk_4"] )
        # RYB
        self.ryb_1_slider = Channel_Slider( self.layout.ryb_1_slider )
        self.ryb_2_slider = Channel_Slider( self.layout.ryb_2_slider )
        self.ryb_3_slider = Channel_Slider( self.layout.ryb_3_slider )
        self.ryb_1_slider.Set_Mode( "LINEAR" )
        self.ryb_2_slider.Set_Mode( "LINEAR" )
        self.ryb_3_slider.Set_Mode( "LINEAR" )
        self.ryb_1_slider.Set_Limits( 0, 0.5, 1 )
        self.ryb_2_slider.Set_Limits( 0, 0.5, 1 )
        self.ryb_3_slider.Set_Limits( 0, 0.5, 1 )
        self.ryb_1_slider.Set_Stops( stops["ryb_1"] )
        self.ryb_2_slider.Set_Stops( stops["ryb_2"] )
        self.ryb_3_slider.Set_Stops( stops["ryb_3"] )
        # YUV
        self.yuv_1_slider = Channel_Slider( self.layout.yuv_1_slider )
        self.yuv_2_slider = Channel_Slider( self.layout.yuv_2_slider )
        self.yuv_3_slider = Channel_Slider( self.layout.yuv_3_slider )
        self.yuv_1_slider.Set_Mode( "LINEAR" )
        self.yuv_2_slider.Set_Mode( "LINEAR" )
        self.yuv_3_slider.Set_Mode( "LINEAR" )
        self.yuv_1_slider.Set_Limits( 0, 0.5, 1 )
        self.yuv_2_slider.Set_Limits( 0, 0.5, 1 )
        self.yuv_3_slider.Set_Limits( 0, 0.5, 1 )
        self.yuv_1_slider.Set_Stops( stops["yuv_1"] )
        self.yuv_2_slider.Set_Stops( stops["yuv_2"] )
        self.yuv_3_slider.Set_Stops( stops["yuv_3"] )

        # HSV
        self.hsv_1_slider = Channel_Slider( self.layout.hsv_1_slider )
        self.hsv_2_slider = Channel_Slider( self.layout.hsv_2_slider )
        self.hsv_3_slider = Channel_Slider( self.layout.hsv_3_slider )
        self.hsv_1_slider.Set_Mode( "CIRCULAR" )
        self.hsv_2_slider.Set_Mode( "LINEAR" )
        self.hsv_3_slider.Set_Mode( "LINEAR" )
        self.hsv_1_slider.Set_Limits( 0, 0.5, 1 )
        self.hsv_2_slider.Set_Limits( 0, 0.5, 1 )
        self.hsv_3_slider.Set_Limits( 0, 0.5, 1 )
        self.hsv_1_slider.Set_Stops( stops["hsv_1"] )
        self.hsv_2_slider.Set_Stops( stops["hsv_2"] )
        self.hsv_3_slider.Set_Stops( stops["hsv_3"] )
        # HSL
        self.hsl_1_slider = Channel_Slider( self.layout.hsl_1_slider )
        self.hsl_2_slider = Channel_Slider( self.layout.hsl_2_slider )
        self.hsl_3_slider = Channel_Slider( self.layout.hsl_3_slider )
        self.hsl_1_slider.Set_Mode( "CIRCULAR" )
        self.hsl_2_slider.Set_Mode( "LINEAR" )
        self.hsl_3_slider.Set_Mode( "LINEAR" )
        self.hsl_1_slider.Set_Limits( 0, 0.5, 1 )
        self.hsl_2_slider.Set_Limits( 0, 0.5, 1 )
        self.hsl_3_slider.Set_Limits( 0, 0.5, 1 )
        self.hsl_1_slider.Set_Stops( stops["hsl_1"] )
        self.hsl_2_slider.Set_Stops( stops["hsl_2"] )
        self.hsl_3_slider.Set_Stops( stops["hsl_3"] )
        # HCY
        self.hcy_1_slider = Channel_Slider( self.layout.hcy_1_slider )
        self.hcy_2_slider = Channel_Slider( self.layout.hcy_2_slider )
        self.hcy_3_slider = Channel_Slider( self.layout.hcy_3_slider )
        self.hcy_1_slider.Set_Mode( "CIRCULAR" )
        self.hcy_2_slider.Set_Mode( "LINEAR" )
        self.hcy_3_slider.Set_Mode( "LINEAR" )
        self.hcy_1_slider.Set_Limits( 0, 0.5, 1 )
        self.hcy_2_slider.Set_Limits( 0, 0.5, 1 )
        self.hcy_3_slider.Set_Limits( 0, 0.5, 1 )
        self.hcy_1_slider.Set_Stops( stops["hcy_1"] )
        self.hcy_2_slider.Set_Stops( stops["hcy_2"] )
        self.hcy_3_slider.Set_Stops( stops["hcy_3"] )
        # ARD
        self.ard_1_slider = Channel_Slider( self.layout.ard_1_slider )
        self.ard_2_slider = Channel_Slider( self.layout.ard_2_slider )
        self.ard_3_slider = Channel_Slider( self.layout.ard_3_slider )
        self.ard_1_slider.Set_Mode( "CIRCULAR" )
        self.ard_2_slider.Set_Mode( "LINEAR" )
        self.ard_3_slider.Set_Mode( "LINEAR" )
        self.ard_1_slider.Set_Limits( 0, 0.5, 1 )
        self.ard_2_slider.Set_Limits( 0, 0.5, 1 )
        self.ard_3_slider.Set_Limits( 0, 0.5, 1 )
        self.ard_1_slider.Set_Stops( stops["ard_1"] )
        self.ard_2_slider.Set_Stops( stops["ard_2"] )
        self.ard_3_slider.Set_Stops( stops["ard_3"] )

        # XYZ
        self.xyz_1_slider = Channel_Slider( self.layout.xyz_1_slider )
        self.xyz_2_slider = Channel_Slider( self.layout.xyz_2_slider )
        self.xyz_3_slider = Channel_Slider( self.layout.xyz_3_slider )
        self.xyz_1_slider.Set_Mode( "LINEAR" )
        self.xyz_2_slider.Set_Mode( "LINEAR" )
        self.xyz_3_slider.Set_Mode( "LINEAR" )
        self.xyz_1_slider.Set_Limits( 0, 0.5, 1 )
        self.xyz_2_slider.Set_Limits( 0, 0.5, 1 )
        self.xyz_3_slider.Set_Limits( 0, 0.5, 1 )
        self.xyz_1_slider.Set_Stops( stops["xyz_1"] )
        self.xyz_2_slider.Set_Stops( stops["xyz_2"] )
        self.xyz_3_slider.Set_Stops( stops["xyz_3"] )
        # XYY
        self.xyy_1_slider = Channel_Slider( self.layout.xyy_1_slider )
        self.xyy_2_slider = Channel_Slider( self.layout.xyy_2_slider )
        self.xyy_3_slider = Channel_Slider( self.layout.xyy_3_slider )
        self.xyy_1_slider.Set_Mode( "LINEAR" )
        self.xyy_2_slider.Set_Mode( "LINEAR" )
        self.xyy_3_slider.Set_Mode( "LINEAR" )
        self.xyy_1_slider.Set_Limits( 0, 0.5, 1 )
        self.xyy_2_slider.Set_Limits( 0, 0.5, 1 )
        self.xyy_3_slider.Set_Limits( 0, 0.5, 1 )
        self.xyy_1_slider.Set_Stops( stops["xyy_1"] )
        self.xyy_2_slider.Set_Stops( stops["xyy_2"] )
        self.xyy_3_slider.Set_Stops( stops["xyy_3"] )
        # LAB
        self.lab_1_slider = Channel_Slider( self.layout.lab_1_slider )
        self.lab_2_slider = Channel_Slider( self.layout.lab_2_slider )
        self.lab_3_slider = Channel_Slider( self.layout.lab_3_slider )
        self.lab_1_slider.Set_Mode( "LINEAR" )
        self.lab_2_slider.Set_Mode( "LINEAR" )
        self.lab_3_slider.Set_Mode( "LINEAR" )
        self.lab_1_slider.Set_Limits( 0, 0.5, 1 )
        self.lab_2_slider.Set_Limits( 0, 0.5, 1 )
        self.lab_3_slider.Set_Limits( 0, 0.5, 1 )
        self.lab_1_slider.Set_Stops( stops["lab_1"] )
        self.lab_2_slider.Set_Stops( stops["lab_2"] )
        self.lab_3_slider.Set_Stops( stops["lab_3"] )

        # LCH
        self.lch_1_slider = Channel_Slider( self.layout.lch_1_slider )
        self.lch_2_slider = Channel_Slider( self.layout.lch_2_slider )
        self.lch_3_slider = Channel_Slider( self.layout.lch_3_slider )
        self.lch_1_slider.Set_Mode( "LINEAR" )
        self.lch_2_slider.Set_Mode( "LINEAR" )
        self.lch_3_slider.Set_Mode( "CIRCULAR" )
        self.lch_1_slider.Set_Limits( 0, 0.5, 1 )
        self.lch_2_slider.Set_Limits( 0, 0.5, 1 )
        self.lch_3_slider.Set_Limits( 0, 0.5, 1 )
        self.lch_1_slider.Set_Stops( stops["lch_1"] )
        self.lch_2_slider.Set_Stops( stops["lch_2"] )
        self.lch_3_slider.Set_Stops( stops["lch_3"] )

        #endregion
        #region Sliders Connects

        # AAA 1
        self.aaa_1_slider.SIGNAL_VALUE.connect( self.Channel_AAA_1_Slider )
        self.aaa_1_slider.SIGNAL_RELEASE.connect( self.Pigmento_RELEASE )
        self.aaa_1_slider.SIGNAL_STOPS.connect( self.Channel_AAA_1_Stops )
        self.aaa_1_slider.SIGNAL_TEXT.connect( self.Label_String )

        # RGB 1
        self.rgb_1_slider.SIGNAL_VALUE.connect( self.Channel_RGB_1_Slider )
        self.rgb_1_slider.SIGNAL_RELEASE.connect( self.Pigmento_RELEASE )
        self.rgb_1_slider.SIGNAL_STOPS.connect( self.Channel_RGB_1_Stops )
        self.rgb_1_slider.SIGNAL_TEXT.connect( self.Label_String )
        # RGB 2
        self.rgb_2_slider.SIGNAL_VALUE.connect( self.Channel_RGB_2_Slider )
        self.rgb_2_slider.SIGNAL_RELEASE.connect( self.Pigmento_RELEASE )
        self.rgb_2_slider.SIGNAL_STOPS.connect( self.Channel_RGB_2_Stops )
        self.rgb_2_slider.SIGNAL_TEXT.connect( self.Label_String )
        # RGB 3
        self.rgb_3_slider.SIGNAL_VALUE.connect( self.Channel_RGB_3_Slider )
        self.rgb_3_slider.SIGNAL_RELEASE.connect( self.Pigmento_RELEASE )
        self.rgb_3_slider.SIGNAL_STOPS.connect( self.Channel_RGB_3_Stops )
        self.rgb_3_slider.SIGNAL_TEXT.connect( self.Label_String )

        # CMY 1
        self.cmy_1_slider.SIGNAL_VALUE.connect( self.Channel_CMY_1_Slider )
        self.cmy_1_slider.SIGNAL_RELEASE.connect( self.Pigmento_RELEASE )
        self.cmy_1_slider.SIGNAL_STOPS.connect( self.Channel_CMY_1_Stops )
        self.cmy_1_slider.SIGNAL_TEXT.connect( self.Label_String )
        # CMY 2
        self.cmy_2_slider.SIGNAL_VALUE.connect( self.Channel_CMY_2_Slider )
        self.cmy_2_slider.SIGNAL_RELEASE.connect( self.Pigmento_RELEASE )
        self.cmy_2_slider.SIGNAL_STOPS.connect( self.Channel_CMY_2_Stops )
        self.cmy_2_slider.SIGNAL_TEXT.connect( self.Label_String )
        # CMY 3
        self.cmy_3_slider.SIGNAL_VALUE.connect( self.Channel_CMY_3_Slider )
        self.cmy_3_slider.SIGNAL_RELEASE.connect( self.Pigmento_RELEASE )
        self.cmy_3_slider.SIGNAL_STOPS.connect( self.Channel_CMY_3_Stops )
        self.cmy_3_slider.SIGNAL_TEXT.connect( self.Label_String )

        # CMYK 1
        self.cmyk_1_slider.SIGNAL_VALUE.connect( self.Channel_CMYK_1_Slider )
        self.cmyk_1_slider.SIGNAL_RELEASE.connect( self.Pigmento_RELEASE )
        self.cmyk_1_slider.SIGNAL_STOPS.connect( self.Channel_CMYK_1_Stops )
        self.cmyk_1_slider.SIGNAL_TEXT.connect( self.Label_String )
        # CMYK 2
        self.cmyk_2_slider.SIGNAL_VALUE.connect( self.Channel_CMYK_2_Slider )
        self.cmyk_2_slider.SIGNAL_RELEASE.connect( self.Pigmento_RELEASE )
        self.cmyk_2_slider.SIGNAL_STOPS.connect( self.Channel_CMYK_2_Stops )
        self.cmyk_2_slider.SIGNAL_TEXT.connect( self.Label_String )
        # CMYK 3
        self.cmyk_3_slider.SIGNAL_VALUE.connect( self.Channel_CMYK_3_Slider )
        self.cmyk_3_slider.SIGNAL_RELEASE.connect( self.Pigmento_RELEASE )
        self.cmyk_3_slider.SIGNAL_STOPS.connect( self.Channel_CMYK_3_Stops )
        self.cmyk_3_slider.SIGNAL_TEXT.connect( self.Label_String )
        # CMYK 4
        self.cmyk_4_slider.SIGNAL_VALUE.connect( self.Channel_CMYK_4_Slider )
        self.cmyk_4_slider.SIGNAL_RELEASE.connect( self.Pigmento_RELEASE )
        self.cmyk_4_slider.SIGNAL_STOPS.connect( self.Channel_CMYK_4_Stops )
        self.cmyk_4_slider.SIGNAL_TEXT.connect( self.Label_String )

        # RYB 1
        self.ryb_1_slider.SIGNAL_VALUE.connect( self.Channel_RYB_1_Slider )
        self.ryb_1_slider.SIGNAL_RELEASE.connect( self.Pigmento_RELEASE )
        self.ryb_1_slider.SIGNAL_STOPS.connect( self.Channel_RYB_1_Stops )
        self.ryb_1_slider.SIGNAL_TEXT.connect( self.Label_String )
        # RYB 2
        self.ryb_2_slider.SIGNAL_VALUE.connect( self.Channel_RYB_2_Slider )
        self.ryb_2_slider.SIGNAL_RELEASE.connect( self.Pigmento_RELEASE )
        self.ryb_2_slider.SIGNAL_STOPS.connect( self.Channel_RYB_2_Stops )
        self.ryb_2_slider.SIGNAL_TEXT.connect( self.Label_String )
        # RYB 3
        self.ryb_3_slider.SIGNAL_VALUE.connect( self.Channel_RYB_3_Slider )
        self.ryb_3_slider.SIGNAL_RELEASE.connect( self.Pigmento_RELEASE )
        self.ryb_3_slider.SIGNAL_STOPS.connect( self.Channel_RYB_3_Stops )
        self.ryb_3_slider.SIGNAL_TEXT.connect( self.Label_String )

        # YUV 1
        self.yuv_1_slider.SIGNAL_VALUE.connect( self.Channel_YUV_1_Slider )
        self.yuv_1_slider.SIGNAL_RELEASE.connect( self.Pigmento_RELEASE )
        self.yuv_1_slider.SIGNAL_STOPS.connect( self.Channel_YUV_1_Stops )
        self.yuv_1_slider.SIGNAL_TEXT.connect( self.Label_String )
        # YUV 2
        self.yuv_2_slider.SIGNAL_VALUE.connect( self.Channel_YUV_2_Slider )
        self.yuv_2_slider.SIGNAL_RELEASE.connect( self.Pigmento_RELEASE )
        self.yuv_2_slider.SIGNAL_STOPS.connect( self.Channel_YUV_2_Stops )
        self.yuv_2_slider.SIGNAL_TEXT.connect( self.Label_String )
        # YUV 3
        self.yuv_3_slider.SIGNAL_VALUE.connect( self.Channel_YUV_3_Slider )
        self.yuv_3_slider.SIGNAL_RELEASE.connect( self.Pigmento_RELEASE )
        self.yuv_3_slider.SIGNAL_STOPS.connect( self.Channel_YUV_3_Stops )
        self.yuv_3_slider.SIGNAL_TEXT.connect( self.Label_String )


        # HSV 1
        self.hsv_1_slider.SIGNAL_VALUE.connect( self.Channel_HSV_1_Slider )
        self.hsv_1_slider.SIGNAL_RELEASE.connect( self.Pigmento_RELEASE )
        self.hsv_1_slider.SIGNAL_STOPS.connect( self.Channel_HSV_1_Stops )
        self.hsv_1_slider.SIGNAL_TEXT.connect( self.Label_String )
        # HSV 2
        self.hsv_2_slider.SIGNAL_VALUE.connect( self.Channel_HSV_2_Slider )
        self.hsv_2_slider.SIGNAL_RELEASE.connect( self.Pigmento_RELEASE )
        self.hsv_2_slider.SIGNAL_STOPS.connect( self.Channel_HSV_2_Stops )
        self.hsv_2_slider.SIGNAL_TEXT.connect( self.Label_String )
        # HSV 3
        self.hsv_3_slider.SIGNAL_VALUE.connect( self.Channel_HSV_3_Slider )
        self.hsv_3_slider.SIGNAL_RELEASE.connect( self.Pigmento_RELEASE )
        self.hsv_3_slider.SIGNAL_STOPS.connect( self.Channel_HSV_3_Stops )
        self.hsv_3_slider.SIGNAL_TEXT.connect( self.Label_String )

        # HSL 1
        self.hsl_1_slider.SIGNAL_VALUE.connect( self.Channel_HSL_1_Slider )
        self.hsl_1_slider.SIGNAL_RELEASE.connect( self.Pigmento_RELEASE )
        self.hsl_1_slider.SIGNAL_STOPS.connect( self.Channel_HSL_1_Stops )
        self.hsl_1_slider.SIGNAL_TEXT.connect( self.Label_String )
        # HSL 2
        self.hsl_2_slider.SIGNAL_VALUE.connect( self.Channel_HSL_2_Slider )
        self.hsl_2_slider.SIGNAL_RELEASE.connect( self.Pigmento_RELEASE )
        self.hsl_2_slider.SIGNAL_STOPS.connect( self.Channel_HSL_2_Stops )
        self.hsl_2_slider.SIGNAL_TEXT.connect( self.Label_String )
        # HSL 3
        self.hsl_3_slider.SIGNAL_VALUE.connect( self.Channel_HSL_3_Slider )
        self.hsl_3_slider.SIGNAL_RELEASE.connect( self.Pigmento_RELEASE )
        self.hsl_3_slider.SIGNAL_STOPS.connect( self.Channel_HSL_3_Stops )
        self.hsl_3_slider.SIGNAL_TEXT.connect( self.Label_String )

        # HCY 1
        self.hcy_1_slider.SIGNAL_VALUE.connect( self.Channel_HCY_1_Slider )
        self.hcy_1_slider.SIGNAL_RELEASE.connect( self.Pigmento_RELEASE )
        self.hcy_1_slider.SIGNAL_STOPS.connect( self.Channel_HCY_1_Stops )
        self.hcy_1_slider.SIGNAL_TEXT.connect( self.Label_String )
        # HCY 2
        self.hcy_2_slider.SIGNAL_VALUE.connect( self.Channel_HCY_2_Slider )
        self.hcy_2_slider.SIGNAL_RELEASE.connect( self.Pigmento_RELEASE )
        self.hcy_2_slider.SIGNAL_STOPS.connect( self.Channel_HCY_2_Stops )
        self.hcy_2_slider.SIGNAL_TEXT.connect( self.Label_String )
        # HCY 3
        self.hcy_3_slider.SIGNAL_VALUE.connect( self.Channel_HCY_3_Slider )
        self.hcy_3_slider.SIGNAL_RELEASE.connect( self.Pigmento_RELEASE )
        self.hcy_3_slider.SIGNAL_STOPS.connect( self.Channel_HCY_3_Stops )
        self.hcy_3_slider.SIGNAL_TEXT.connect( self.Label_String )

        # ARD 1
        self.ard_1_slider.SIGNAL_VALUE.connect( self.Channel_ARD_1_Slider )
        self.ard_1_slider.SIGNAL_RELEASE.connect( self.Pigmento_RELEASE )
        self.ard_1_slider.SIGNAL_STOPS.connect( self.Channel_ARD_1_Stops )
        self.ard_1_slider.SIGNAL_TEXT.connect( self.Label_String )
        # ARD 2
        self.ard_2_slider.SIGNAL_VALUE.connect( self.Channel_ARD_2_Slider )
        self.ard_2_slider.SIGNAL_RELEASE.connect( self.Pigmento_RELEASE )
        self.ard_2_slider.SIGNAL_STOPS.connect( self.Channel_ARD_2_Stops )
        self.ard_2_slider.SIGNAL_TEXT.connect( self.Label_String )
        # ARD 3
        self.ard_3_slider.SIGNAL_VALUE.connect( self.Channel_ARD_3_Slider )
        self.ard_3_slider.SIGNAL_RELEASE.connect( self.Pigmento_RELEASE )
        self.ard_3_slider.SIGNAL_STOPS.connect( self.Channel_ARD_3_Stops )
        self.ard_3_slider.SIGNAL_TEXT.connect( self.Label_String )

        # XYZ 1
        self.xyz_1_slider.SIGNAL_VALUE.connect( self.Channel_XYZ_1_Slider )
        self.xyz_1_slider.SIGNAL_RELEASE.connect( self.Pigmento_RELEASE )
        self.xyz_1_slider.SIGNAL_STOPS.connect( self.Channel_XYZ_1_Stops )
        self.xyz_1_slider.SIGNAL_TEXT.connect( self.Label_String )
        # XYZ 2
        self.xyz_2_slider.SIGNAL_VALUE.connect( self.Channel_XYZ_2_Slider )
        self.xyz_2_slider.SIGNAL_RELEASE.connect( self.Pigmento_RELEASE )
        self.xyz_2_slider.SIGNAL_STOPS.connect( self.Channel_XYZ_2_Stops )
        self.xyz_2_slider.SIGNAL_TEXT.connect( self.Label_String )
        # XYZ 3
        self.xyz_3_slider.SIGNAL_VALUE.connect( self.Channel_XYZ_3_Slider )
        self.xyz_3_slider.SIGNAL_RELEASE.connect( self.Pigmento_RELEASE )
        self.xyz_3_slider.SIGNAL_STOPS.connect( self.Channel_XYZ_3_Stops )
        self.xyz_3_slider.SIGNAL_TEXT.connect( self.Label_String )

        # XYY 1
        self.xyy_1_slider.SIGNAL_VALUE.connect( self.Channel_XYY_1_Slider )
        self.xyy_1_slider.SIGNAL_RELEASE.connect( self.Pigmento_RELEASE )
        self.xyy_1_slider.SIGNAL_STOPS.connect( self.Channel_XYY_1_Stops )
        self.xyy_1_slider.SIGNAL_TEXT.connect( self.Label_String )
        # XYY 2
        self.xyy_2_slider.SIGNAL_VALUE.connect( self.Channel_XYY_2_Slider )
        self.xyy_2_slider.SIGNAL_RELEASE.connect( self.Pigmento_RELEASE )
        self.xyy_2_slider.SIGNAL_STOPS.connect( self.Channel_XYY_2_Stops )
        self.xyy_2_slider.SIGNAL_TEXT.connect( self.Label_String )
        # XYY 3
        self.xyy_3_slider.SIGNAL_VALUE.connect( self.Channel_XYY_3_Slider )
        self.xyy_3_slider.SIGNAL_RELEASE.connect( self.Pigmento_RELEASE )
        self.xyy_3_slider.SIGNAL_STOPS.connect( self.Channel_XYY_3_Stops )
        self.xyy_3_slider.SIGNAL_TEXT.connect( self.Label_String )

        # LAB 1
        self.lab_1_slider.SIGNAL_VALUE.connect( self.Channel_LAB_1_Slider )
        self.lab_1_slider.SIGNAL_RELEASE.connect( self.Pigmento_RELEASE )
        self.lab_1_slider.SIGNAL_STOPS.connect( self.Channel_LAB_1_Stops )
        self.lab_1_slider.SIGNAL_TEXT.connect( self.Label_String )
        # LAB 2
        self.lab_2_slider.SIGNAL_VALUE.connect( self.Channel_LAB_2_Slider )
        self.lab_2_slider.SIGNAL_RELEASE.connect( self.Pigmento_RELEASE )
        self.lab_2_slider.SIGNAL_STOPS.connect( self.Channel_LAB_2_Stops )
        self.lab_2_slider.SIGNAL_TEXT.connect( self.Label_String )
        # LAB 3
        self.lab_3_slider.SIGNAL_VALUE.connect( self.Channel_LAB_3_Slider )
        self.lab_3_slider.SIGNAL_RELEASE.connect( self.Pigmento_RELEASE )
        self.lab_3_slider.SIGNAL_STOPS.connect( self.Channel_LAB_3_Stops )
        self.lab_3_slider.SIGNAL_TEXT.connect( self.Label_String )

        # LCH 1
        self.lch_1_slider.SIGNAL_VALUE.connect( self.Channel_LCH_1_Slider )
        self.lch_1_slider.SIGNAL_RELEASE.connect( self.Pigmento_RELEASE )
        self.lch_1_slider.SIGNAL_STOPS.connect( self.Channel_LCH_1_Stops )
        self.lch_1_slider.SIGNAL_TEXT.connect( self.Label_String )
        # LCH 2
        self.lch_2_slider.SIGNAL_VALUE.connect( self.Channel_LCH_2_Slider )
        self.lch_2_slider.SIGNAL_RELEASE.connect( self.Pigmento_RELEASE )
        self.lch_2_slider.SIGNAL_STOPS.connect( self.Channel_LCH_2_Stops )
        self.lch_2_slider.SIGNAL_TEXT.connect( self.Label_String )
        # LCH 3
        self.lch_3_slider.SIGNAL_VALUE.connect( self.Channel_LCH_3_Slider )
        self.lch_3_slider.SIGNAL_RELEASE.connect( self.Pigmento_RELEASE )
        self.lch_3_slider.SIGNAL_STOPS.connect( self.Channel_LCH_3_Stops )
        self.lch_3_slider.SIGNAL_TEXT.connect( self.Label_String )

        #endregion
        #region Sliders Non Color Space

        # Kelvin
        self.kkk_1_slider = Channel_Slider( self.layout.kkk_1_slider )
        self.kkk_1_slider.Set_Mode( "LINEAR" )
        self.kkk_1_slider.Set_Limits( 0, 0.5, 1 )
        self.kkk_1_slider.Set_Stops( 4 )
        self.kkk_1_slider.SIGNAL_VALUE.connect( self.Channel_KKK_1_Slider )
        self.kkk_1_slider.SIGNAL_RELEASE.connect( self.Pigmento_RELEASE )
        self.kkk_1_slider.SIGNAL_STOPS.connect( self.Channel_KKK_1_Stops )
        self.kkk_1_slider.SIGNAL_TEXT.connect( self.Label_String )

        #endregion
        #region Mixer

        # Pole Slider
        self.pole_slider = Channel_Slider( self.layout.pole_slider )
        self.pole_slider.Set_Mode( "LINEAR" )
        self.pole_slider.Set_Limits( 0, 0.5, 1 )
        self.pole_slider.Set_Stops( 4 )
        self.pole_slider.SIGNAL_VALUE.connect( self.Channel_Pole_Slider )
        self.pole_slider.SIGNAL_RELEASE.connect( self.Pigmento_RELEASE )
        self.pole_slider.SIGNAL_STOPS.connect( self.Channel_Pole_Stops )
        self.pole_slider.SIGNAL_TEXT.connect( self.Label_String )
        # Pole 1 A
        self.pole_pin_a = Pin_Color( self.layout.pole_pin_a )
        self.pole_pin_a.SIGNAL_APPLY.connect( self.Pole_Apply_1A )
        self.pole_pin_a.SIGNAL_SAVE.connect( self.Pole_Save_1A )
        self.pole_pin_a.SIGNAL_CLEAN.connect( self.Pole_Clean_1A )
        self.pole_pin_a.SIGNAL_TEXT.connect( self.Label_String )
        # Pole 1 B
        self.pole_pin_b = Pin_Color( self.layout.pole_pin_b )
        self.pole_pin_b.SIGNAL_APPLY.connect( self.Pole_Apply_1B )
        self.pole_pin_b.SIGNAL_SAVE.connect( self.Pole_Save_1B )
        self.pole_pin_b.SIGNAL_CLEAN.connect( self.Pole_Clean_1B )
        self.pole_pin_b.SIGNAL_TEXT.connect( self.Label_String )

        #endregion
        #region Pin

        self.pin_widget = [
            self.layout.pin_00,
            self.layout.pin_01,
            self.layout.pin_02,
            self.layout.pin_03,
            self.layout.pin_04,
            self.layout.pin_05,
            self.layout.pin_06,
            self.layout.pin_07,
            self.layout.pin_08,
            self.layout.pin_09,
            self.layout.pin_10,
            ]
        length = len( self.pin_widget )
        for i in range( 0, length ):
            self.pin_module.append( Pin_Color( self.pin_widget[i] ) )
        for i in range( 0, length ):
            self.pin_module[i].Set_Index( i )
            self.pin_module[i].SIGNAL_APPLY.connect( self.Pin_Apply )
            self.pin_module[i].SIGNAL_SAVE.connect( self.Pin_Save )
            self.pin_module[i].SIGNAL_CLEAN.connect( self.Pin_Clean )
            self.pin_module[i].SIGNAL_TEXT.connect( self.Label_String )
        for i in range( 0, length ):
            self.pin_cor.append( color_false.copy() )

        #endregion
    def Style( self ):
        # Variables
        ki = Krita.instance()

        # Icons
        self.qicon_on           = ki.icon( "showColoring" )
        self.qicon_write        = ki.icon( "media-playback-start" )
        self.qicon_read         = ki.icon( "system-help" )
        self.qicon_off          = ki.icon( "showColoringOff" )
        qicon_swap              = ki.icon( "fileLayer" )
        qicon_fill              = ki.icon( "folder-documents" )
        qicon_sample_screen     = ki.icon( "sample-screen" )
        qicon_settings          = ki.icon( "settings-button" )
        self.qicon_lock_layout  = ki.icon( "layer-locked" )
        self.qicon_lock_dialog  = ki.icon( "docker_lock_b" )
        self.qicon_none         = QIcon()

        # Widgets
        self.layout.dot_swap.setIcon( qicon_swap )
        self.layout.mode.setIcon( self.qicon_on )
        self.layout.fill.setIcon( qicon_fill )
        self.layout.sample_screen.setIcon( qicon_sample_screen )
        self.layout.settings.setIcon( qicon_settings )

        # Tool Tips
        self.layout.mode.setToolTip( "Mode" )
        self.layout.fill.setToolTip( "Fill Pixel" )
        self.layout.sample_screen.setToolTip( "Sample Screen" )
        self.layout.hex_string.setToolTip( "Hex Code" )
        self.layout.settings.setToolTip( "Settings" )

        # Panel Icons
        qpixmap_fill = QPixmap( 100, 100 )
        qpixmap_fill.fill( QColor( "#000000" ) )
        icon_path =     os.path.join( self.directory_plugin, "ICON" )
        path_square =   os.path.join( icon_path, "SQUARE.png" )
        path_hue =      os.path.join( icon_path, "HUE.png" )
        path_gamut =    os.path.join( icon_path, "GAMUT.png" )
        path_hexagon =  os.path.join( icon_path, "HEXAGON.png" )
        path_luma =     os.path.join( icon_path, "LUMA.png" )
        path_dot =      os.path.join( icon_path, "DOT.png" )
        path_mask =     os.path.join( icon_path, "MASK.png" )
        self.dialog.panel_index.blockSignals( True )
        self.dialog.panel_index.setItemIcon( 0, QIcon( qpixmap_fill ) )
        self.dialog.panel_index.setItemIcon( 1, QIcon( path_square ) )
        self.dialog.panel_index.setItemIcon( 2, QIcon( path_hue ) )
        self.dialog.panel_index.setItemIcon( 3, QIcon( path_gamut ) )
        self.dialog.panel_index.setItemIcon( 4, QIcon( path_hexagon ) )
        self.dialog.panel_index.setItemIcon( 5, QIcon( path_luma ) )
        self.dialog.panel_index.setItemIcon( 6, QIcon( path_dot ) )
        self.dialog.panel_index.setItemIcon( 7, QIcon( path_mask ) )
        self.dialog.panel_index.blockSignals( False )

        # StyleSheets Layout
        self.Theme_Changed()
    def Timer( self ):
        #region QTimer

        if check_timer >= 30:
            self.timer_pulse = QtCore.QTimer( self )
            self.timer_pulse.timeout.connect( self.Krita_to_Pigmento )

        #endregion
        #region Randomizer Seed

        today = datetime.date.today()
        y = str( today )[0:4]
        m = str( today )[5:7]
        d = str( today )[8:10]
        seed = int( str( y + m + d ) )
        random.seed( seed )

        #endregion
    def Extension( self ):
        # Install Extension for Pigmento Docker
        extension = Picker_Extension( parent = Krita.instance() )
        Krita.instance().addExtension( extension )
        # Connect Extension Signals
        extension.SIGNAL_PIN.connect( self.Extension_PIN )
        extension.SIGNAL_KEY_1.connect( self.Extension_KEY_1 )
        extension.SIGNAL_KEY_2.connect( self.Extension_KEY_2 )
        extension.SIGNAL_KEY_3.connect( self.Extension_KEY_3 )
        extension.SIGNAL_KEY_4.connect( self.Extension_KEY_4 )
        extension.SIGNAL_LOCK.connect( self.Extension_LOCK )
    def Settings( self ):
        #region Dictionaries

        # Pigmento
        self.Dict_Copy( krange, self.Set_Read( "EVAL", "krange", krange ) )
        self.Dict_Copy( stops, self.Set_Read( "EVAL", "stops", stops ) )
        self.Dict_Copy( kac, self.Set_Read( "EVAL", "kac", kac ) )
        self.Dict_Copy( kbc, self.Set_Read( "EVAL", "kbc", kbc ) )

        # Colors
        self.zorn_yellow = self.Color_Convert( "HEX", "#edb525", 0, 0, 0, color_true.copy() )
        self.zorn_red = self.Color_Convert( "HEX", "#b72e35", 0, 0, 0, color_true.copy() )
        self.zorn_white = self.Color_Convert( "HEX", "#edf0ec", 0, 0, 0, color_true.copy() )
        self.zorn_black = self.Color_Convert( "HEX", "#292421", 0, 0, 0, color_true.copy() )
        # Pole
        self.pole_mix = self.Color_Convert( "HEX", "#8b8a86", 0, 0, 0, color_true.copy() )
        self.pole_cor_n = self.Color_Convert( "HEX", "#8b8a86", 0, 0, 0, color_true.copy() )

        #endregion
        #region Dictionaries Pin

        self.pin_cor = self.Set_Read( "EVAL", "pin_cor", self.pin_cor )

        #endregion
        #region Harmony

        # Colors
        self.Dict_Copy( har_01, self.Set_Read( "EVAL", "har_01", har_01 ) )
        self.Dict_Copy( har_02, self.Set_Read( "EVAL", "har_02", har_02 ) )
        self.Dict_Copy( har_03, self.Set_Read( "EVAL", "har_03", har_03 ) )
        self.Dict_Copy( har_04, self.Set_Read( "EVAL", "har_04", har_04 ) )
        self.Dict_Copy( har_05, self.Set_Read( "EVAL", "har_05", har_05 ) )

        # Variables
        self.harmony_index = self.Set_Read( "EVAL", "harmony_index", self.harmony_index )
        self.harmony_rule = self.Set_Read( "STR", "harmony_rule", self.harmony_rule )
        self.harmony_edit = self.Set_Read( "EVAL", "harmony_edit", self.harmony_edit )
        self.harmony_span = self.Set_Read( "EVAL", "harmony_span", self.harmony_span )

        #endregion
        #region Panels
        
        # HUE
        self.huecircle_shape = self.Set_Read( "STR", "huecircle_shape", self.huecircle_shape )

        # Gamut
        self.gamut_mask = self.Set_Read( "STR", "gamut_mask", self.gamut_mask )
        self.gamut_profile = self.Set_Read( "EVAL", "gamut_profile", self.gamut_profile )

        # DOT Variables
        self.dot_interpolation = self.Set_Read( "STR", "dot_interpolation", self.dot_interpolation )
        self.dot_dimension = self.Set_Read( "EVAL", "dot_dimension", self.dot_dimension )
        self.dot_edit = self.Set_Read( "EVAL", "dot_edit", self.dot_edit )
        # DOT Colors
        self.dot_1 = self.Set_Read( "EVAL", "dot_1", self.Color_Convert( "HEX", "#edb525", 0, 0, 0, self.dot_1 ) )
        self.dot_2 = self.Set_Read( "EVAL", "dot_2", self.Color_Convert( "HEX", "#b72e35", 0, 0, 0, self.dot_2 ) )
        self.dot_3 = self.Set_Read( "EVAL", "dot_3", self.Color_Convert( "HEX", "#edf0ec", 0, 0, 0, self.dot_3 ) )
        self.dot_4 = self.Set_Read( "EVAL", "dot_4", self.Color_Convert( "HEX", "#292421", 0, 0, 0, self.dot_4 ) )

        # Mask
        self.mask_set = self.Set_Read( "STR", "mask_set", self.mask_set )
        self.mask_edit = self.Set_Read( "EVAL", "mask_edit", self.mask_edit )

        #endregion
        #region Mixer

        # Pole
        self.Dict_Copy( self.pole_cor_a, self.zorn_white )
        self.Dict_Copy( self.pole_cor_b, self.zorn_black )
        self.pole_cor_a = self.Set_Read( "EVAL", "pole_cor_a", self.pole_cor_a )
        self.pole_cor_b = self.Set_Read( "EVAL", "pole_cor_b", self.pole_cor_b )
        # Mixer
        self.mixer_colors = self.Set_Read( "EVAL", "mixer_colors", self.mixer_colors )

        #endregion
        #region Dialog Option

        # Panels
        self.dialog.panel_index.setCurrentText( self.Set_Read( "STR", "panel_index", self.panel_index ) )
        self.dialog.wheel_mode.setCurrentText( self.Set_Read( "STR", "wheel_mode", self.wheel_mode ) )
        self.dialog.wheel_space.setCurrentText( self.Set_Read( "STR", "wheel_space", self.wheel_space ) )
        self.dialog.analyse_display.setChecked( self.Set_Read( "EVAL", "analyse_display", self.analyse_display ) )
        # Mixers
        self.dialog.mixer_space.setCurrentText( self.Set_Read( "STR", "mixer_space", self.mixer_space ) )
        self.dialog.mixer_count.setValue( self.Set_Read( "INT", "mixer_count", self.mixer_count ) )

        #endregion
        #region Dialog Color

        # Color Space
        self.dialog.chan_aaa.setChecked( self.Set_Read( "EVAL", "chan_aaa", self.chan_aaa ) )
        self.dialog.chan_rgb.setChecked( self.Set_Read( "EVAL", "chan_rgb", self.chan_rgb ) )
        self.dialog.chan_cmy.setChecked( self.Set_Read( "EVAL", "chan_cmy", self.chan_cmy ) )
        self.dialog.chan_cmyk.setChecked( self.Set_Read( "EVAL", "chan_cmyk", self.chan_cmyk ) )
        self.dialog.chan_ryb.setChecked( self.Set_Read( "EVAL", "chan_ryb", self.chan_rgb ) )
        self.dialog.chan_yuv.setChecked( self.Set_Read( "EVAL", "chan_yuv", self.chan_rgb ) )
        self.dialog.chan_hsv.setChecked( self.Set_Read( "EVAL", "chan_hsv", self.chan_hsv ) )
        self.dialog.chan_hsl.setChecked( self.Set_Read( "EVAL", "chan_hsl", self.chan_hsl ) )
        self.dialog.chan_hcy.setChecked( self.Set_Read( "EVAL", "chan_hcy", self.chan_hcy ) )
        self.dialog.chan_ard.setChecked( self.Set_Read( "EVAL", "chan_ard", self.chan_ard ) )
        self.dialog.chan_xyz.setChecked( self.Set_Read( "EVAL", "chan_xyz", self.chan_xyz ) )
        self.dialog.chan_xyy.setChecked( self.Set_Read( "EVAL", "chan_xyy", self.chan_xyy ) )
        self.dialog.chan_lab.setChecked( self.Set_Read( "EVAL", "chan_lab", self.chan_lab ) )
        self.dialog.chan_lch.setChecked( self.Set_Read( "EVAL", "chan_lch", self.chan_lch ) )
        # Non Color
        self.dialog.chan_kkk.setChecked( self.Set_Read( "EVAL", "chan_kkk", self.chan_kkk ) )
        self.dialog.chan_hex.setChecked( self.Set_Read( "EVAL", "chan_hex", self.chan_hex ) )
        self.dialog.chan_sum.setChecked( self.Set_Read( "EVAL", "chan_sum", self.chan_sum ) )

        # Format
        self.dialog.disp_labels.setChecked( self.Set_Read( "EVAL", "disp_labels", self.disp_labels ) )
        self.dialog.disp_values.setChecked( self.Set_Read( "EVAL", "disp_values", self.disp_values ) )
        self.dialog.hue_shine.setChecked( self.Set_Read( "EVAL", "hue_shine", self.hue_shine ) )

        # Shortcuts
        self.dialog.key_1_chan.setCurrentText( self.Set_Read( "STR", "key_1_chan", self.key_1_chan ) )
        self.dialog.key_2_chan.setCurrentText( self.Set_Read( "STR", "key_2_chan", self.key_2_chan ) )
        self.dialog.key_3_chan.setCurrentText( self.Set_Read( "STR", "key_3_chan", self.key_3_chan ) )
        self.dialog.key_4_chan.setCurrentText( self.Set_Read( "STR", "key_4_chan", self.key_4_chan ) )
        self.dialog.key_1_factor.setValue( self.Set_Read( "INT", "key_1_factor", self.key_1_factor ) )
        self.dialog.key_2_factor.setValue( self.Set_Read( "INT", "key_2_factor", self.key_2_factor ) )
        self.dialog.key_3_factor.setValue( self.Set_Read( "INT", "key_3_factor", self.key_3_factor ) )
        self.dialog.key_4_factor.setValue( self.Set_Read( "INT", "key_4_factor", self.key_4_factor ) )

        #endregion
        #region Dialog System

        # Color Space
        self.dialog.cs_luminosity.setCurrentText( self.Set_Read( "STR", "cs_luminosity", self.cs_luminosity ) )
        self.dialog.cs_matrix.setCurrentText( self.Set_Read( "STR", "cs_matrix", self.cs_matrix ) )

        # Performance
        self.dialog.performance_release.setChecked( self.Set_Read( "EVAL", "performance_release", self.performance_release ) )
        self.dialog.performance_inaccurate.setChecked( self.Set_Read( "EVAL", "performance_inaccurate", self.performance_inaccurate ) )

        #endregion
        #region Dialog Header

        self.dialog.harmony.setChecked( self.Set_Read( "EVAL", "ui_harmony", self.ui_harmony ) )
        self.dialog.channel.setChecked( self.Set_Read( "EVAL", "ui_channel", self.ui_channel ) )
        self.dialog.mixer.setChecked( self.Set_Read( "EVAL", "ui_mixer", self.ui_mixer ) )
        self.dialog.pin.setChecked( self.Set_Read( "EVAL", "ui_pin", self.ui_pin ) )
        self.dialog.history.setChecked( self.Set_Read( "EVAL", "ui_history", self.ui_history ) )

        #endregion
    def Plugin_Load( self ):
        try:
            self.Loader()
        except Exception as e:
            self.Message_Warnning( "ERROR", f"Load \n{ e }" )
            self.Variables()
            self.Loader()

    def Loader( self ):
        # Harmony
        self.harmony_swatch.Update_Harmony( self.harmony_rule, self.harmony_edit, self.harmony_index )
        self.harmony_spread.Update_Span( self.harmony_span )
        # Hue
        self.panel_huecircle.Set_Shape( self.huecircle_shape )
        self.HueCircle_SubPanel( self.huecircle_shape )
        # Gamut
        self.panel_gamut.Update_Mask( self.gamut_mask )
        self.panel_gamut.Update_Profile( self.gamut_profile )
        # Dot
        self.panel_dot.Set_Interpolation( self.dot_interpolation )
        self.panel_dot.Set_Dimension( self.dot_dimension )
        self.panel_dot.Set_Edit( self.dot_edit )
        self.Dot_Widget( self.dot_edit )
        self.Update_Panel_Dot()
        self.Update_Edit_Dot()
        # Mask
        self.panel_mask.Set_Edit( self.mask_edit )
        self.Mask_Widget( self.mask_edit )

        # Dictionaries
        self.Range_Load( krange )
        self.Sliders_Stops_Load( stops )
        # Panel
        self.Mask_Load()
        # Channel Color
        self.Channel_AAA( self.dialog.chan_aaa.isChecked() )
        self.Channel_RGB( self.dialog.chan_rgb.isChecked() )
        self.Channel_CMY( self.dialog.chan_cmy.isChecked() )
        self.Channel_CMYK( self.dialog.chan_cmyk.isChecked() )
        self.Channel_RYB( self.dialog.chan_ryb.isChecked() )
        self.Channel_YUV( self.dialog.chan_yuv.isChecked() )
        self.Channel_HSV( self.dialog.chan_hsv.isChecked() )
        self.Channel_HSL( self.dialog.chan_hsl.isChecked() )
        self.Channel_HCY( self.dialog.chan_hcy.isChecked() )
        self.Channel_ARD( self.dialog.chan_ard.isChecked() )
        self.Channel_XYZ( self.dialog.chan_xyz.isChecked() )
        self.Channel_XYY( self.dialog.chan_xyy.isChecked() )
        self.Channel_LAB( self.dialog.chan_lab.isChecked() )
        self.Channel_LCH( self.dialog.chan_lch.isChecked() )
        # Channels Non Color
        self.Channel_KKK( self.dialog.chan_kkk.isChecked() )
        self.Channel_HEX( self.dialog.chan_hex.isChecked() )
        self.Channel_SUM( self.dialog.chan_sum.isChecked() )
        # Mixer
        self.Pole_LOAD( self.pole_cor_a, self.pole_cor_b )
        self.Mixer_LOAD()
        # Pin
        self.Pin_LOAD()

        # Dialog Option
        self.Panel_Index( self.dialog.panel_index.currentText() )
        self.Wheel_Mode( self.dialog.wheel_mode.currentText() )
        self.Wheel_Space( self.dialog.wheel_space.currentText() )
        self.Mixer_Space( self.dialog.mixer_space.currentText() )
        # Dialog Color
        self.Display_Labels( self.dialog.disp_labels.isChecked() )
        self.Display_Values( self.dialog.disp_values.isChecked() )
        self.Hue_Shine( self.dialog.hue_shine.isChecked() )
        # UI Layout
        self.Menu_Harmony( self.dialog.harmony.isChecked() )
        self.Menu_Channel( self.dialog.channel.isChecked() )
        self.Menu_Mixer( self.dialog.mixer.isChecked() )
        self.Menu_Pin( self.dialog.pin.isChecked() )
        self.Menu_History( self.dialog.history.isChecked() )

        # Sync
        self.Pigmento_RELEASE()
        self.Harmony_Update()
    def Set_Read( self, mode, entry, default ):
        setting = Krita.instance().readSetting( DOCKER_NAME, entry, "" )
        if setting == "":
            read = default
        else:
            try:
                if mode == "EVAL":
                    read = eval( setting )
                elif mode == "STR":
                    read = str( setting )
                elif mode == "INT":
                    read = int( setting )
                elif mode == "LIST":
                    read = list( setting )
            except:
                read = default
        Krita.instance().writeSetting( DOCKER_NAME, entry, str( read ) )
        return read

    #endregion
    #region Menu

    # Mode Index
    def Mode_Index( self, index ):
        self.mode_index = index
        if index == 0: # On
            self.layout.mode.setIcon( self.qicon_on )
            self.timer_pulse.start( check_timer )
        if index == 1: # Write
            self.layout.mode.setIcon( self.qicon_write )
            self.timer_pulse.stop()
        if index == 2: # Read
            self.layout.mode.setIcon( self.qicon_read )
            self.timer_pulse.start( check_timer )
        if index == 3: # Off
            self.layout.mode.setIcon( self.qicon_off )
            self.timer_pulse.stop()

    # Extra Functions
    def Menu_FILL( self, boolean ):
        if ( ( self.canvas() is not None ) and ( self.canvas().view() is not None ) ):
            # Variables
            fill["active"] = boolean
            # UI
            if boolean == True:
                # Variables
                fill["node_uid"] = Krita.instance().activeDocument().activeNode().uniqueId()
                fill["alphalock_before"] = Krita.instance().activeDocument().activeNode().alphaLocked()
                # UI
                self.layout.fill.setIcon( Krita.instance().icon( "fillLayer" ) )
                # Layers
                Krita.instance().activeDocument().activeNode().setAlphaLocked( boolean )
            else:
                # Layers
                try:
                    Krita.instance().activeDocument().nodeByUniqueID( fill["node_uid"] ).setAlphaLocked( fill["alphalock_before"] )
                except:
                    pass
                # UI
                self.layout.fill.setIcon( Krita.instance().icon( "folder-documents" ) )
                # Variables
                fill["node_uid"] = None
                fill["alphalock_before"] = None
        else:
            self.Fill_None()
    def Menu_SampleScreen( self ):
        Krita.instance().action( "sample_screen_color_real_canvas" ).trigger()

    # UI Toggle
    def Menu_Harmony( self, boolean ):
        # Variables
        if boolean == True:
            # Variables
            text = "[HARMONY]"
            a = 10
            b = 20
            c = 10
        else:
            # Variables
            text = "HARMONY"
            a = 30
            b = 0
            c = 0
        # UI
        self.dialog.harmony.setText( text )
        self.layout.color_header.setMinimumHeight( a )
        self.layout.color_header.setMaximumHeight( a )
        self.layout.harmony_swatch.setMinimumHeight( b )
        self.layout.harmony_swatch.setMaximumHeight( b )
        self.layout.harmony_spread.setMinimumHeight( c )
        self.layout.harmony_spread.setMaximumHeight( c )
        # Update
        if self.ui_harmony != boolean:
            self.ui_harmony = boolean
            self.Harmony_Index( self.harmony_index )
        # Save
        Krita.instance().writeSetting( DOCKER_NAME, "ui_harmony", str( self.ui_harmony ) )
    def Menu_Channel( self, boolean ):
        # Variables
        if boolean == True:
            text_c = "[CHANNEL]"
            sc = 16777215
        else:
            text_c = "CHANNEL"
            sc = 0
        # UI
        self.dialog.channel.setText( text_c )
        self.layout.channel_set.setMinimumHeight( sc )
        self.layout.channel_set.setMaximumHeight( sc )
        # layout
        self.layout.channel_set.setSizePolicy( QSizePolicy.Ignored, QSizePolicy.Fixed )
        # Update
        if self.ui_channel != boolean:
            self.ui_channel = boolean
        self.Channel_Active()
        # Save
        Krita.instance().writeSetting( DOCKER_NAME, "ui_channel", str( self.ui_channel ) )
    def Menu_Mixer( self, boolean ):
        # Variables
        if boolean == True:
            text = "[MIXER]"
            horz = 0
            vert = 1
            a = 10
            b = max_val
        else:
            text = "MIXER"
            horz = 0
            vert = 0
            a = 0
            b = 0
        # UI
        self.dialog.mixer.setText( text )
        self.layout.mixer_set.setMinimumHeight( a )
        self.layout.mixer_set.setMaximumHeight( b )
        # layout
        self.layout.mixer_set_layout.setContentsMargins( horz, vert, horz, vert )
        self.layout.mixer_set_layout.setVerticalSpacing( vert )
        # Update
        if self.ui_mixer != boolean:
            self.ui_mixer = boolean
        # Save
        Krita.instance().writeSetting( DOCKER_NAME, "ui_mixer", str( self.ui_mixer ) )
    def Menu_Pin( self, boolean ):
        # Variables
        if boolean == True:
            text = "[PIN]"
            horz = 0
            vert = 1
            a = 10
            b = 20
        else:
            text = "PIN"
            horz = 0
            vert = 0
            a = 0
            b = 0
        # UI
        self.dialog.pin.setText( text )
        self.layout.pin_set.setMinimumHeight( a )
        self.layout.pin_set.setMaximumHeight( b )
        # layout
        self.layout.pin_set_layout.setContentsMargins( horz, vert, horz, vert )
        self.layout.pin_set_layout.setVerticalSpacing( vert )
        # Update
        if self.ui_pin != boolean:
            self.ui_pin = boolean
        # Save
        Krita.instance().writeSetting( DOCKER_NAME, "ui_pin", str( self.ui_pin ) )
    def Menu_History( self, boolean ):
        # Variables
        if boolean == True:
            text = "[HISTORY]"
            horz = 0
            vert = 1
            a = 10
            b = 20
        else:
            text = "HISTORY"
            horz = 0
            vert = 0
            a = 0
            b = 0
        # UI
        self.dialog.history.setText( text )
        self.layout.history_set.setMinimumHeight( a )
        self.layout.history_set.setMaximumHeight( b )
        # layout
        self.layout.history_set_layout.setContentsMargins( horz, vert, horz, vert )
        # Update
        if self.ui_history != boolean:
            self.ui_history = boolean
        # Save
        Krita.instance().writeSetting( DOCKER_NAME, "ui_history", str( self.ui_history ) )

    # Panels
    def Panel_Index( self, index ):
        # UI
        if index == panel_fill:     self.layout.panel_set.setCurrentIndex( 0 )
        if index == panel_square:   self.layout.panel_set.setCurrentIndex( 1 )
        if index == panel_hue:      self.layout.panel_set.setCurrentIndex( 2 )
        if index == panel_gamut:    self.layout.panel_set.setCurrentIndex( 3 )
        if index == panel_hexagon:  self.layout.panel_set.setCurrentIndex( 4 )
        if index == panel_luma:     self.layout.panel_set.setCurrentIndex( 5 )
        if index == panel_dot:      self.layout.panel_set.setCurrentIndex( 6 )
        if index == panel_mask:     self.layout.panel_set.setCurrentIndex( 7 )
        # Update
        if self.panel_index != index:
            self.panel_index = index
            self.Update_Size()
        # Save
        Krita.instance().writeSetting( DOCKER_NAME, "panel_index", str( self.panel_index ) )
    # Wheel
    def Wheel_Mode( self, wheel_mode ):
        # Variables
        self.wheel_mode = wheel_mode
        # UI display
        if self.dialog.wheel_mode.currentText() != self.wheel_mode:
            self.dialog.wheel_mode.setCurrentText( self.wheel_mode )
        # Modules
        self.panel_huecircle.Set_WheelMode( self.wheel_mode )
        self.panel_gamut.Set_WheelMode( self.wheel_mode )
        # Save
        Krita.instance().writeSetting( DOCKER_NAME, "wheel_mode", str( self.wheel_mode ) )
    def Wheel_Space( self, wheel_space ):
        # Variables
        self.wheel_space = wheel_space

        # UI display
        if self.dialog.wheel_space.currentText() != self.wheel_space:
            self.dialog.wheel_space.setCurrentText( self.wheel_space )

        # Panel Square
        self.panel_square.Set_WheelSpace( self.wheel_space )
        # Panel Hue
        self.panel_huecircle.Set_WheelSpace( self.wheel_space )
        if self.huecircle_shape == "Triangle":
            self.panel_huesubpanel.Set_WheelSpace( "HSL" )
        if self.huecircle_shape == "Square":
            self.panel_huesubpanel.Set_WheelSpace( self.wheel_space )
        if self.huecircle_shape == "Diamond":
            self.panel_huesubpanel.Set_WheelSpace( "HSL" )
        # Panel Gamut
        self.panel_gamut.Set_WheelSpace( self.wheel_space )

        # Save
        Krita.instance().writeSetting( DOCKER_NAME, "wheel_space", str( self.wheel_space ) )
    # Analyse
    def Analyse_Document( self ):
        # Variables
        self.analyse_collection = None
        # Read
        canvas = self.canvas()
        view = canvas.view()
        qimage = self.Select_Alpha( canvas, view )
        if qimage != None:
            self.Analyse_Pixel( qimage )
    def Analyse_Pixel( self, qimage ):
        if qimage.isNull() == False:
            # Scale
            size = 200
            qimage = qimage.scaled( size, size, Qt.KeepAspectRatio, Qt.FastTransformation )

            # Variables
            width = qimage.width()
            height = qimage.height()

            # Pixel Check
            p = list()
            for h in range( 0, height ):
                # Progress bar
                h1 = ( h + 1 )
                if ( h1 % 5 == 0 or h1 == height ):
                    percent = round( h1 / height, 4 )
                    self.color_header.Set_Progress( percent )
                    QApplication.processEvents()
                # Rox of Pixels
                for w in range( 0, width ):
                    # RGB
                    qcolor = qimage.pixelColor( w, h )
                    r = qcolor.redF()
                    g = qcolor.greenF()
                    b = qcolor.blueF()
                    a = qcolor.alphaF()
                    rgb = [ r, g, b ]
                    # Logic
                    if ( a > 0 and rgb not in p ):
                        p.append( rgb )
            # Color
            len_p = len( p )
            analyse_collection = list()
            for i in range( 0, len_p ):
                c = color_neutral.copy()
                color = self.Color_Convert( "RGB", p[i][0], p[i][1], p[i][2], 0, c )
                analyse_collection.append( color )
            self.analyse_collection = analyse_collection

            # UI
            self.color_header.Set_Progress( 1 )
            self.Pigmento_RELEASE()
            # System
            self.Message_Log( "ANALYSE", "Complete" )
    def Analyse_Display( self, boolean ):
        # Variables
        self.analyse_display = boolean
        # Update
        self.Pigmento_RELEASE()
        # Save
        Krita.instance().writeSetting( DOCKER_NAME, "analyse_display", str( self.analyse_display ) )
    def Select_Alpha( self, canvas, view ):
        qimage = None
        if ( canvas is not None ) and ( view is not None ):
            # Variables
            ad = Krita.instance().activeDocument()
            n_cd = ad.activeNode().colorDepth()
            if n_cd == "U8":
                k = 255
            elif n_cd == "U16":
                k = 65535
            elif n_cd == "F16":
                # k = 65535
                k = 15360
            elif n_cd == "F32":
                # k = 4294836225
                k = 1065353216

            # Source
            ss = ad.selection()
            if ss == None:
                dx = int( 0 )
                dy = int( 0 )
                dw = int( ad.width() )
                dh = int( ad.height() )
            else:
                dx = int( ss.x() )
                dy = int( ss.y() )
                dw = int( ss.width() )
                dh = int( ss.height() )

            # QImage
            qimage = ad.projection( dx, dy, dw, dh )

            # Selection into Alpha
            if ss != None:
                # Selection
                pds = ss.pixelData( dx, dy, dw, dh )
                num_array = self.analyse.Bytes_to_Integer( pds, n_cd )

                # Clip
                counter = 0
                for h in range( 0, dh ):
                    for w in range( 0, dw ):
                        # Variables
                        s = num_array[counter] / k
                        # Read
                        qcolor = qimage.pixelColor( w, h )
                        a = qcolor.alphaF()
                        # Logic
                        var = a * s
                        # Write
                        qcolor.setAlphaF( var )
                        qimage.setPixelColor( w, h, qcolor )
                        # Cycle
                        counter += 1
        return qimage

    # Mixer
    def Mixer_Space( self, mixer_space ):
        self.mixer_space = mixer_space
        self.Mixer_Set_Style()
        Krita.instance().writeSetting( DOCKER_NAME, "mixer_space", str( self.mixer_space ) )
    def Mixer_Count( self, count ):
        self.dialog.mixer_count.setEnabled( False )
        self.Count_Construct( self.mixer_count, count )
        self.mixer_count = count
        self.Update_Size()
        self.dialog.mixer_count.setEnabled( True )
        Krita.instance().writeSetting( DOCKER_NAME, "mixer_count", str( self.mixer_count ) )
    def Count_Construct( self, old, new ):
        # Widgets
        check = int( new - old )
        if check > 0:   self.Count_Plus( old, new ) # Create
        elif check < 0: self.Count_Subtract( old, new ) # Delete
        # Variables
        self.mixer_colors = self.mixer_colors[0:new]
        self.mixer_module = self.mixer_module[0:new]
        self.mixer_widget = self.mixer_widget[0:new]
    def Count_Plus( self, old, new ):
        for i in range( old, new ):
            # Widegts
            left = QWidget()
            middle = QWidget()
            right = QWidget()
            # Dimensions
            left = self.Geo_Square( left, i )
            middle = self.Geo_Slider( middle, i )
            right = self.Geo_Square( right, i )
            # Layout
            self.layout.mixer_set_layout.addWidget( left, i+1, 0 )
            self.layout.mixer_set_layout.addWidget( middle, i+1, 1 )
            self.layout.mixer_set_layout.addWidget( right, i+1, 2 )

            # Variables
            self.mixer_widget.append( { "l" : left, "m" : middle, "r" : right } )
            self.mixer_module.append( { "l" : Pin_Color( left ), "m" : Channel_Slider( middle ), "r" : Pin_Color( right ) } )
            self.mixer_colors.append( { "l" : color_false.copy(), "m" : 0, "r" : color_false.copy() } )

            # Left
            self.mixer_module[i]["l"].Set_Index( i )
            self.mixer_module[i]["l"].SIGNAL_APPLY.connect( self.Mixer_Apply_L )
            self.mixer_module[i]["l"].SIGNAL_SAVE.connect( self.Mixer_Save_L )
            self.mixer_module[i]["l"].SIGNAL_CLEAN.connect( self.Mixer_Clean_L )
            self.mixer_module[i]["l"].SIGNAL_TEXT.connect( self.Label_String )
            # Gradient
            self.mixer_module[i]["m"].Set_Index( i )
            self.mixer_module[i]["m"].Set_Mode( "MIXER" )
            self.mixer_module[i]["m"].Set_Limits( 0, 0.5, 1 )
            self.mixer_module[i]["m"].Set_Stops( 2 )
            self.mixer_module[i]["m"].Set_Value( 0 )
            self.mixer_module[i]["m"].SIGNAL_VALUE.connect( self.Mixer_Slider_M )
            self.mixer_module[i]["m"].SIGNAL_STOPS.connect( self.Mixer_Stops_M )
            self.mixer_module[i]["m"].SIGNAL_RELEASE.connect( self.Pigmento_RELEASE )
            self.mixer_module[i]["m"].SIGNAL_TEXT.connect( self.Label_String )
            # Right
            self.mixer_module[i]["r"].Set_Index( i )
            self.mixer_module[i]["r"].SIGNAL_APPLY.connect( self.Mixer_Apply_R )
            self.mixer_module[i]["r"].SIGNAL_SAVE.connect( self.Mixer_Save_R )
            self.mixer_module[i]["r"].SIGNAL_CLEAN.connect( self.Mixer_Clean_R )
            self.mixer_module[i]["r"].SIGNAL_TEXT.connect( self.Label_String )

            # Delete Objects
            del left
            del middle
            del right
    def Count_Subtract( self, old, new ):
        for i in range( new, old ):
            self.layout.mixer_set_layout.removeWidget( self.mixer_widget[i]["l"] )
            self.layout.mixer_set_layout.removeWidget( self.mixer_widget[i]["m"] )
            self.layout.mixer_set_layout.removeWidget( self.mixer_widget[i]["r"] )
    def Geo_Square( self, square, r ):
        # Dimensions
        square.setMinimumHeight( 15 )
        square.setMaximumHeight( 20 )
        square.setMaximumWidth( 20 )
        # Size Policy
        square.setSizePolicy( QSizePolicy.Fixed, QSizePolicy.Preferred )
        # Return
        return square
    def Geo_Slider( self, slider, r ):
        # Geometry
        width = self.layout.pole_slider.width()
        slider.setGeometry( 0, 0, width, 20)
        # Dimensions
        slider.setMinimumHeight( 15 )
        slider.setMaximumHeight( 20 )
        # Size Policy
        slider.setSizePolicy( QSizePolicy.Ignored, QSizePolicy.Preferred )
        # Return
        return slider

    # Space Channels UI
    def Channel_Active( self ):
        # Check UI
        chan_aaa = self.dialog.chan_aaa.isChecked()
        chan_rgb = self.dialog.chan_rgb.isChecked()
        chan_cmy = self.dialog.chan_cmy.isChecked()
        chan_cmyk = self.dialog.chan_cmyk.isChecked()
        chan_ryb = self.dialog.chan_ryb.isChecked()
        chan_yuv = self.dialog.chan_yuv.isChecked()
        chan_hsv = self.dialog.chan_hsv.isChecked()
        chan_hsl = self.dialog.chan_hsl.isChecked()
        chan_hcy = self.dialog.chan_hcy.isChecked()
        chan_ard = self.dialog.chan_ard.isChecked()
        chan_xyz = self.dialog.chan_xyz.isChecked()
        chan_xyy = self.dialog.chan_xyy.isChecked()
        chan_lab = self.dialog.chan_lab.isChecked()
        chan_lch = self.dialog.chan_lch.isChecked()
        chan_kkk = self.dialog.chan_kkk.isChecked()

        # Activate Corresponding
        self.Channel_AAA( chan_aaa )
        self.Channel_RGB( chan_rgb )
        self.Channel_CMY( chan_cmy )
        self.Channel_CMYK( chan_cmyk )
        self.Channel_RYB( chan_ryb )
        self.Channel_YUV( chan_yuv )
        self.Channel_HSV( chan_hsv )
        self.Channel_HSL( chan_hsl )
        self.Channel_HCY( chan_hcy )
        self.Channel_ARD( chan_ard )
        self.Channel_XYZ( chan_xyz )
        self.Channel_XYY( chan_xyy )
        self.Channel_LAB( chan_lab )
        self.Channel_LCH( chan_lch )
        self.Channel_KKK( chan_kkk )
    def Channel_AAA( self, boolean ):
        self.chan_aaa = boolean
        if ( boolean == True and self.ui_channel == True ):
            maxi = max_val
            horz = 0
            vert = 1
        else:
            maxi = 0
            horz = 0
            vert = 0

        # layout
        self.layout.aaa_label.setMaximumHeight( maxi )
        self.layout.aaa_slider.setMaximumHeight( maxi )
        self.layout.aaa_value.setMaximumHeight( maxi )
        self.layout.aaa_label_layout.setContentsMargins( horz, vert, horz, vert )
        self.layout.aaa_slider_layout.setContentsMargins( horz, vert, horz, vert )
        self.layout.aaa_value_layout.setContentsMargins( horz, vert, horz, vert )
        self.Pigmento_RELEASE()
        # Save
        Krita.instance().writeSetting( DOCKER_NAME, "chan_aaa", str( self.chan_aaa ) )
    def Channel_RGB( self, boolean ):
        self.chan_rgb = boolean
        if ( boolean == True and self.ui_channel == True ):
            maxi = max_val
            horz = 0
            vert = 1
        else:
            maxi = 0
            horz = 0
            vert = 0

        # layout
        self.layout.rgb_label.setMaximumHeight( maxi )
        self.layout.rgb_slider.setMaximumHeight( maxi )
        self.layout.rgb_value.setMaximumHeight( maxi )
        self.layout.rgb_label_layout.setContentsMargins( horz, vert, horz, vert )
        self.layout.rgb_slider_layout.setContentsMargins( horz, vert, horz, vert )
        self.layout.rgb_value_layout.setContentsMargins( horz, vert, horz, vert )
        self.Pigmento_RELEASE()
        # Save
        Krita.instance().writeSetting( DOCKER_NAME, "chan_rgb", str( self.chan_rgb ) )
    def Channel_CMY( self, boolean ):
        self.chan_cmy = boolean
        if ( boolean == True and self.ui_channel == True ):
            maxi = max_val
            horz = 0
            vert = 1
        else:
            maxi = 0
            horz = 0
            vert = 0

        # layout
        self.layout.cmy_label.setMaximumHeight( maxi )
        self.layout.cmy_slider.setMaximumHeight( maxi )
        self.layout.cmy_value.setMaximumHeight( maxi )
        self.layout.cmy_label_layout.setContentsMargins( horz, vert, horz, vert )
        self.layout.cmy_slider_layout.setContentsMargins( horz, vert, horz, vert )
        self.layout.cmy_value_layout.setContentsMargins( horz, vert, horz, vert )
        self.Pigmento_RELEASE()
        # Save
        Krita.instance().writeSetting( DOCKER_NAME, "chan_cmy", str( self.chan_cmy ) )
    def Channel_CMYK( self, boolean ):
        self.chan_cmyk = boolean
        if ( boolean == True and self.ui_channel == True ):
            maxi = max_val
            horz = 0
            vert = 1
        else:
            maxi = 0
            horz = 0
            vert = 0

        # layout
        self.layout.cmyk_label.setMaximumHeight( maxi )
        self.layout.cmyk_slider.setMaximumHeight( maxi )
        self.layout.cmyk_value.setMaximumHeight( maxi )
        self.layout.cmyk_label_layout.setContentsMargins( horz, vert, horz, vert )
        self.layout.cmyk_slider_layout.setContentsMargins( horz, vert, horz, vert )
        self.layout.cmyk_value_layout.setContentsMargins( horz, vert, horz, vert )
        self.Pigmento_RELEASE()
        # Save
        Krita.instance().writeSetting( DOCKER_NAME, "chan_cmyk", str( self.chan_cmyk ) )
    def Channel_RYB( self, boolean ):
        self.chan_ryb = boolean
        if ( boolean == True and self.ui_channel == True ):
            maxi = max_val
            horz = 0
            vert = 1
        else:
            maxi = 0
            horz = 0
            vert = 0

        # layout
        self.layout.ryb_label.setMaximumHeight( maxi )
        self.layout.ryb_slider.setMaximumHeight( maxi )
        self.layout.ryb_value.setMaximumHeight( maxi )
        self.layout.ryb_label_layout.setContentsMargins( horz, vert, horz, vert )
        self.layout.ryb_slider_layout.setContentsMargins( horz, vert, horz, vert )
        self.layout.ryb_value_layout.setContentsMargins( horz, vert, horz, vert )
        self.Pigmento_RELEASE()
        # Save
        Krita.instance().writeSetting( DOCKER_NAME, "chan_ryb", str( self.chan_ryb ) )
    def Channel_YUV( self, boolean ):
        self.chan_yuv = boolean
        if ( boolean == True and self.ui_channel == True ):
            maxi = max_val
            horz = 0
            vert = 1
        else:
            maxi = 0
            horz = 0
            vert = 0

        # layout
        self.layout.yuv_label.setMaximumHeight( maxi )
        self.layout.yuv_slider.setMaximumHeight( maxi )
        self.layout.yuv_value.setMaximumHeight( maxi )
        self.layout.yuv_label_layout.setContentsMargins( horz, vert, horz, vert )
        self.layout.yuv_slider_layout.setContentsMargins( horz, vert, horz, vert )
        self.layout.yuv_value_layout.setContentsMargins( horz, vert, horz, vert )
        self.Pigmento_RELEASE()
        # Save
        Krita.instance().writeSetting( DOCKER_NAME, "chan_yuv", str( self.chan_yuv ) )
    def Channel_HSV( self, boolean ):
        self.chan_hsv = boolean
        if ( boolean == True and self.ui_channel == True ):
            maxi = max_val
            horz = 0
            vert = 1
        else:
            maxi = 0
            horz = 0
            vert = 0

        # layout
        self.layout.hsv_label.setMaximumHeight( maxi )
        self.layout.hsv_slider.setMaximumHeight( maxi )
        self.layout.hsv_value.setMaximumHeight( maxi )
        self.layout.hsv_label_layout.setContentsMargins( horz, vert, horz, vert )
        self.layout.hsv_slider_layout.setContentsMargins( horz, vert, horz, vert )
        self.layout.hsv_value_layout.setContentsMargins( horz, vert, horz, vert )
        self.Pigmento_RELEASE()
        # Save
        Krita.instance().writeSetting( DOCKER_NAME, "chan_hsv", str( self.chan_hsv ) )
    def Channel_HSL( self, boolean ):
        self.chan_hsl = boolean
        if ( boolean == True and self.ui_channel == True ):
            maxi = max_val
            horz = 0
            vert = 1
        else:
            maxi = 0
            horz = 0
            vert = 0

        # layout
        self.layout.hsl_label.setMaximumHeight( maxi )
        self.layout.hsl_slider.setMaximumHeight( maxi )
        self.layout.hsl_value.setMaximumHeight( maxi )
        self.layout.hsl_label_layout.setContentsMargins( horz, vert, horz, vert )
        self.layout.hsl_slider_layout.setContentsMargins( horz, vert, horz, vert )
        self.layout.hsl_value_layout.setContentsMargins( horz, vert, horz, vert )
        self.Pigmento_RELEASE()
        # Save
        Krita.instance().writeSetting( DOCKER_NAME, "chan_hsl", str( self.chan_hsl ) )
    def Channel_HCY( self, boolean ):
        self.chan_hcy = boolean
        if ( boolean == True and self.ui_channel == True ):
            maxi = max_val
            horz = 0
            vert = 1
        else:
            maxi = 0
            horz = 0
            vert = 0

        # layout
        self.layout.hcy_label.setMaximumHeight( maxi )
        self.layout.hcy_slider.setMaximumHeight( maxi )
        self.layout.hcy_value.setMaximumHeight( maxi )
        self.layout.hcy_label_layout.setContentsMargins( horz, vert, horz, vert )
        self.layout.hcy_slider_layout.setContentsMargins( horz, vert, horz, vert )
        self.layout.hcy_value_layout.setContentsMargins( horz, vert, horz, vert )
        self.Pigmento_RELEASE()
        # Save
        Krita.instance().writeSetting( DOCKER_NAME, "chan_hcy", str( self.chan_hcy ) )
    def Channel_ARD( self, boolean ):
        self.chan_ard = boolean
        if ( boolean == True and self.ui_channel == True ):
            maxi = max_val
            horz = 0
            vert = 1
        else:
            maxi = 0
            horz = 0
            vert = 0

        # layout
        self.layout.ard_label.setMaximumHeight( maxi )
        self.layout.ard_slider.setMaximumHeight( maxi )
        self.layout.ard_value.setMaximumHeight( maxi )
        self.layout.ard_label_layout.setContentsMargins( horz, vert, horz, vert )
        self.layout.ard_slider_layout.setContentsMargins( horz, vert, horz, vert )
        self.layout.ard_value_layout.setContentsMargins( horz, vert, horz, vert )
        self.Pigmento_RELEASE()
        # Save
        Krita.instance().writeSetting( DOCKER_NAME, "chan_ard", str( self.chan_ard ) )
    def Channel_XYZ( self, boolean ):
        self.chan_xyz = boolean
        if ( boolean == True and self.ui_channel == True ):
            maxi = max_val
            horz = 0
            vert = 1
        else:
            maxi = 0
            horz = 0
            vert = 0

        # layout
        self.layout.xyz_label.setMaximumHeight( maxi )
        self.layout.xyz_slider.setMaximumHeight( maxi )
        self.layout.xyz_value.setMaximumHeight( maxi )
        self.layout.xyz_label_layout.setContentsMargins( horz, vert, horz, vert )
        self.layout.xyz_slider_layout.setContentsMargins( horz, vert, horz, vert )
        self.layout.xyz_value_layout.setContentsMargins( horz, vert, horz, vert )
        self.Pigmento_RELEASE()
        # Save
        Krita.instance().writeSetting( DOCKER_NAME, "chan_xyz", str( self.chan_xyz ) )
    def Channel_XYY( self, boolean ):
        self.chan_xyy = boolean
        if ( boolean == True and self.ui_channel == True ):
            maxi = max_val
            horz = 0
            vert = 1
        else:
            maxi = 0
            horz = 0
            vert = 0

        # layout
        self.layout.xyy_label.setMaximumHeight( maxi )
        self.layout.xyy_slider.setMaximumHeight( maxi )
        self.layout.xyy_value.setMaximumHeight( maxi )
        self.layout.xyy_label_layout.setContentsMargins( horz, vert, horz, vert )
        self.layout.xyy_slider_layout.setContentsMargins( horz, vert, horz, vert )
        self.layout.xyy_value_layout.setContentsMargins( horz, vert, horz, vert )
        self.Pigmento_RELEASE()
        # Save
        Krita.instance().writeSetting( DOCKER_NAME, "chan_xyy", str( self.chan_xyy ) )
    def Channel_LAB( self, boolean ):
        self.chan_lab = boolean
        if ( boolean == True and self.ui_channel == True ):
            maxi = max_val
            horz = 0
            vert = 1
        else:
            maxi = 0
            horz = 0
            vert = 0

        # layout
        self.layout.lab_label.setMaximumHeight( maxi )
        self.layout.lab_slider.setMaximumHeight( maxi )
        self.layout.lab_value.setMaximumHeight( maxi )
        self.layout.lab_label_layout.setContentsMargins( horz, vert, horz, vert )
        self.layout.lab_slider_layout.setContentsMargins( horz, vert, horz, vert )
        self.layout.lab_value_layout.setContentsMargins( horz, vert, horz, vert )
        self.Pigmento_RELEASE()
        # Save
        Krita.instance().writeSetting( DOCKER_NAME, "chan_lab", str( self.chan_lab ) )
    def Channel_LCH( self, boolean ):
        self.chan_lch = boolean
        if ( boolean == True and self.ui_channel == True ):
            maxi = max_val
            horz = 0
            vert = 1
        else:
            maxi = 0
            horz = 0
            vert = 0

        # layout
        self.layout.lch_label.setMaximumHeight( maxi )
        self.layout.lch_slider.setMaximumHeight( maxi )
        self.layout.lch_value.setMaximumHeight( maxi )
        self.layout.lch_label_layout.setContentsMargins( horz, vert, horz, vert )
        self.layout.lch_slider_layout.setContentsMargins( horz, vert, horz, vert )
        self.layout.lch_value_layout.setContentsMargins( horz, vert, horz, vert )
        self.Pigmento_RELEASE()
        # Save
        Krita.instance().writeSetting( DOCKER_NAME, "chan_lch", str( self.chan_lch ) )
    def Channel_KKK( self, boolean ):
        self.chan_kkk = boolean
        if ( boolean == True and self.ui_channel == True ):
            maxi = max_val
            horz = 0
            vert = 1
        else:
            maxi = 0
            horz = 0
            vert = 0

        # layout
        self.layout.kkk_label.setMaximumHeight( maxi )
        self.layout.kkk_slider.setMaximumHeight( maxi )
        self.layout.kkk_value.setMaximumHeight( maxi )
        self.layout.kkk_label_layout.setContentsMargins( horz, vert, horz, vert )
        self.layout.kkk_slider_layout.setContentsMargins( horz, vert, horz, vert )
        self.layout.kkk_value_layout.setContentsMargins( horz, vert, horz, vert )
        self.Pigmento_RELEASE()
        # Save
        Krita.instance().writeSetting( DOCKER_NAME, "chan_kkk", str( self.chan_kkk ) )
    def Channel_HEX( self, boolean ):
        # Variables
        self.chan_hex = boolean
        self.Channel_HEX_SUM( self.chan_hex, self.chan_sum )
        self.Pigmento_RELEASE()
        # Save
        Krita.instance().writeSetting( DOCKER_NAME, "chan_hex", str( self.chan_hex ) )
    def Channel_SUM( self, boolean ):
        # Variables
        self.chan_sum = boolean
        self.Channel_HEX_SUM( self.chan_hex, self.chan_sum )
        self.Pigmento_RELEASE()
        # Save
        Krita.instance().writeSetting( DOCKER_NAME, "chan_sum", str( self.chan_sum ) )
    def Channel_HEX_SUM( self, chan_hex, chan_sum ):
        if chan_hex == True and chan_sum == True:
            self.layout.hex_string.setMaximumWidth( 90 )
            self.layout.sum_string.setMaximumWidth( 90 )
        elif chan_hex == True or chan_sum == True:
            self.layout.hex_string.setMaximumWidth( 180 * chan_hex )
            self.layout.sum_string.setMaximumWidth( 180 * chan_sum )
        else:
            self.layout.hex_string.setMaximumWidth( 0 )
            self.layout.sum_string.setMaximumWidth( 0 )

    # Space Range Load
    def Range_Load( self, dict ):
        # Dialog Range
        self.Range_Block( True )
        self.Range_Maximum( dict )
        self.Range_Set( dict )
        self.Range_Block( False )
    def Range_Block( self, boolean ):
        self.dialog.range_aaa.blockSignals( boolean )
        self.dialog.range_rgb.blockSignals( boolean )
        self.dialog.range_cmy.blockSignals( boolean )
        self.dialog.range_cmyk.blockSignals( boolean )
        self.dialog.range_ryb.blockSignals( boolean )
        self.dialog.range_yuv.blockSignals( boolean )

        self.dialog.range_hue.blockSignals( boolean )
        self.dialog.range_hsv.blockSignals( boolean )
        self.dialog.range_hsl.blockSignals( boolean )
        self.dialog.range_hcy.blockSignals( boolean )
        self.dialog.range_ard.blockSignals( boolean )

        self.dialog.range_xyz.blockSignals( boolean )
        self.dialog.range_xyy.blockSignals( boolean )
        self.dialog.range_lab.blockSignals( boolean )

        self.dialog.range_lch.blockSignals( boolean )
    def Range_Maximum( self, dict ):
        self.layout.aaa_1_value.setMaximum( dict["aaa_1"] )
        self.layout.rgb_1_value.setMaximum( dict["rgb_1"] )
        self.layout.rgb_2_value.setMaximum( dict["rgb_2"] )
        self.layout.rgb_3_value.setMaximum( dict["rgb_3"] )
        self.layout.cmy_1_value.setMaximum( dict["cmy_1"] )
        self.layout.cmy_2_value.setMaximum( dict["cmy_2"] )
        self.layout.cmy_3_value.setMaximum( dict["cmy_3"] )
        self.layout.cmyk_1_value.setMaximum( dict["cmyk_1"] )
        self.layout.cmyk_2_value.setMaximum( dict["cmyk_2"] )
        self.layout.cmyk_3_value.setMaximum( dict["cmyk_3"] )
        self.layout.cmyk_4_value.setMaximum( dict["cmyk_4"] )
        self.layout.ryb_1_value.setMaximum( dict["ryb_1"] )
        self.layout.ryb_2_value.setMaximum( dict["ryb_2"] )
        self.layout.ryb_3_value.setMaximum( dict["ryb_3"] )
        self.layout.yuv_1_value.setMaximum( dict["yuv_1"] )
        self.layout.yuv_2_value.setMaximum( dict["yuv_2"] )
        self.layout.yuv_3_value.setMaximum( dict["yuv_3"] )

        self.layout.hsv_1_value.setMaximum( dict["hsv_1"] )
        self.layout.hsv_2_value.setMaximum( dict["hsv_2"] )
        self.layout.hsv_3_value.setMaximum( dict["hsv_3"] )
        self.layout.hsl_1_value.setMaximum( dict["hsl_1"] )
        self.layout.hsl_2_value.setMaximum( dict["hsl_2"] )
        self.layout.hsl_3_value.setMaximum( dict["hsl_3"] )
        self.layout.hcy_1_value.setMaximum( dict["hcy_1"] )
        self.layout.hcy_2_value.setMaximum( dict["hcy_2"] )
        self.layout.hcy_3_value.setMaximum( dict["hcy_3"] )
        self.layout.ard_1_value.setMaximum( dict["ard_1"] )
        self.layout.ard_2_value.setMaximum( dict["ard_2"] )
        self.layout.ard_3_value.setMaximum( dict["ard_3"] )

        self.layout.xyz_1_value.setMaximum( dict["xyz_1"] )
        self.layout.xyz_2_value.setMaximum( dict["xyz_2"] )
        self.layout.xyz_3_value.setMaximum( dict["xyz_3"] )
        self.layout.xyy_1_value.setMaximum( dict["xyy_1"] )
        self.layout.xyy_2_value.setMaximum( dict["xyy_2"] )
        self.layout.xyy_3_value.setMaximum( dict["xyy_3"] )
        self.layout.lab_1_value.setMaximum( dict["lab_1"] )
        self.layout.lab_2_value.setMaximum( dict["lab_2"] )
        self.layout.lab_3_value.setMaximum( dict["lab_3"] )

        self.layout.lch_1_value.setMaximum( dict["lch_1"] )
        self.layout.lch_2_value.setMaximum( dict["lch_2"] )
        self.layout.lch_3_value.setMaximum( dict["lch_3"] )
    def Range_Set( self, dict ):
        self.dialog.range_aaa.setValue( dict["aaa_1"] )
        self.dialog.range_rgb.setValue( dict["rgb_1"] )
        self.dialog.range_cmy.setValue( dict["cmy_1"] )
        self.dialog.range_cmyk.setValue( dict["cmyk_1"] )
        self.dialog.range_ryb.setValue( dict["ryb_1"] )
        self.dialog.range_yuv.setValue( dict["yuv_1"] )
        self.dialog.range_hue.setValue( dict["hsv_1"] )
        self.dialog.range_hsv.setValue( dict["hsv_2"] )
        self.dialog.range_hsl.setValue( dict["hsl_2"] )
        self.dialog.range_hcy.setValue( dict["hcy_2"] )
        self.dialog.range_ard.setValue( dict["ard_2"] )
        self.dialog.range_xyz.setValue( dict["xyz_1"] )
        self.dialog.range_xyy.setValue( dict["xyy_1"] )
        self.dialog.range_lab.setValue( dict["lab_1"] )
        self.dialog.range_lch.setValue( dict["lch_1"] )

    # Space Range Value
    def Range_AAA( self, chan_range ):
        chan_range = int( self.geometry.Limit_Unit( chan_range ) )
        krange["aaa_1"] = chan_range
        self.layout.aaa_1_value.setMaximum( chan_range )
        self.Pigmento_RELEASE()
        Krita.instance().writeSetting( DOCKER_NAME, "krange", str( krange ) )
    def Range_RGB( self, chan_range ):
        chan_range = int( self.geometry.Limit_Unit( chan_range ) )
        krange["rgb_1"] = chan_range
        krange["rgb_2"] = chan_range
        krange["rgb_3"] = chan_range
        self.layout.rgb_1_value.setMaximum( chan_range )
        self.layout.rgb_2_value.setMaximum( chan_range )
        self.layout.rgb_3_value.setMaximum( chan_range )
        self.Pigmento_RELEASE()
        Krita.instance().writeSetting( DOCKER_NAME, "krange", str( krange ) )
    def Range_CMY( self, chan_range ):
        chan_range = int( self.geometry.Limit_Unit( chan_range ) )
        krange["cmy_1"] = chan_range
        krange["cmy_2"] = chan_range
        krange["cmy_3"] = chan_range
        self.layout.cmy_1_value.setMaximum( chan_range )
        self.layout.cmy_2_value.setMaximum( chan_range )
        self.layout.cmy_3_value.setMaximum( chan_range )
        self.Pigmento_RELEASE()
        Krita.instance().writeSetting( DOCKER_NAME, "krange", str( krange ) )
    def Range_CMYK( self, chan_range ):
        chan_range = int( self.geometry.Limit_Unit( chan_range ) )
        krange["cmyk_1"] = chan_range
        krange["cmyk_2"] = chan_range
        krange["cmyk_3"] = chan_range
        krange["cmyk_4"] = chan_range
        self.layout.cmyk_1_value.setMaximum( chan_range )
        self.layout.cmyk_2_value.setMaximum( chan_range )
        self.layout.cmyk_3_value.setMaximum( chan_range )
        self.layout.cmyk_4_value.setMaximum( chan_range )
        self.Pigmento_RELEASE()
        Krita.instance().writeSetting( DOCKER_NAME, "krange", str( krange ) )
    def Range_RYB( self, chan_range ):
        chan_range = int( self.geometry.Limit_Unit( chan_range ) )
        krange["ryb_1"] = chan_range
        krange["ryb_2"] = chan_range
        krange["ryb_3"] = chan_range
        self.layout.ryb_1_value.setMaximum( chan_range )
        self.layout.ryb_2_value.setMaximum( chan_range )
        self.layout.ryb_3_value.setMaximum( chan_range )
        self.Pigmento_RELEASE()
        Krita.instance().writeSetting( DOCKER_NAME, "krange", str( krange ) )
    def Range_YUV( self, chan_range ):
        chan_range = int( self.geometry.Limit_Unit( chan_range ) )
        krange["yuv_1"] = chan_range
        krange["yuv_2"] = chan_range
        krange["yuv_3"] = chan_range
        self.layout.yuv_1_value.setMaximum( chan_range )
        self.layout.yuv_2_value.setMaximum( chan_range )
        self.layout.yuv_3_value.setMaximum( chan_range )
        self.Pigmento_RELEASE()
        Krita.instance().writeSetting( DOCKER_NAME, "krange", str( krange ) )
    def Range_HUE( self, chan_range ):
        chan_range = int( self.geometry.Limit_Unit( chan_range ) )
        krange["hsv_1"] = chan_range
        krange["hsl_1"] = chan_range
        krange["hcy_1"] = chan_range
        krange["ard_1"] = chan_range
        self.layout.hsv_1_value.setMaximum( chan_range )
        self.layout.hsl_1_value.setMaximum( chan_range )
        self.layout.hcy_1_value.setMaximum( chan_range )
        self.layout.ard_1_value.setMaximum( chan_range )
        self.Pigmento_RELEASE()
        Krita.instance().writeSetting( DOCKER_NAME, "krange", str( krange ) )
    def Range_HSV( self, chan_range ):
        chan_range = int( self.geometry.Limit_Unit( chan_range ) )
        krange["hsv_2"] = chan_range
        krange["hsv_3"] = chan_range
        self.layout.hsv_2_value.setMaximum( chan_range )
        self.layout.hsv_3_value.setMaximum( chan_range )
        self.Pigmento_RELEASE()
        Krita.instance().writeSetting( DOCKER_NAME, "krange", str( krange ) )
    def Range_HSL( self, chan_range ):
        chan_range = int( self.geometry.Limit_Unit( chan_range ) )
        krange["hsl_2"] = chan_range
        krange["hsl_3"] = chan_range
        self.layout.hsl_2_value.setMaximum( chan_range )
        self.layout.hsl_3_value.setMaximum( chan_range )
        self.Pigmento_RELEASE()
        Krita.instance().writeSetting( DOCKER_NAME, "krange", str( krange ) )
    def Range_HCY( self, chan_range ):
        chan_range = int( self.geometry.Limit_Unit( chan_range ) )
        krange["hcy_2"] = chan_range
        krange["hcy_3"] = chan_range
        self.layout.hcy_2_value.setMaximum( chan_range )
        self.layout.hcy_3_value.setMaximum( chan_range )
        self.Pigmento_RELEASE()
        Krita.instance().writeSetting( DOCKER_NAME, "krange", str( krange ) )
    def Range_ARD( self, chan_range ):
        chan_range = int( self.geometry.Limit_Unit( chan_range ) )
        krange["ard_2"] = chan_range
        krange["ard_3"] = chan_range
        self.layout.ard_2_value.setMaximum( chan_range )
        self.layout.ard_3_value.setMaximum( chan_range )
        self.Pigmento_RELEASE()
        Krita.instance().writeSetting( DOCKER_NAME, "krange", str( krange ) )
    def Range_XYZ( self, chan_range ):
        chan_range = int( self.geometry.Limit_Unit( chan_range ) )
        krange["xyz_1"] = chan_range
        krange["xyz_2"] = chan_range
        krange["xyz_3"] = chan_range
        self.layout.xyz_1_value.setMaximum( chan_range )
        self.layout.xyz_2_value.setMaximum( chan_range )
        self.layout.xyz_3_value.setMaximum( chan_range )
        self.Pigmento_RELEASE()
        Krita.instance().writeSetting( DOCKER_NAME, "krange", str( krange ) )
    def Range_XYY( self, chan_range ):
        chan_range = int( self.geometry.Limit_Unit( chan_range ) )
        krange["xyy_1"] = chan_range
        krange["xyy_2"] = chan_range
        krange["xyy_3"] = chan_range
        self.layout.xyy_1_value.setMaximum( chan_range )
        self.layout.xyy_2_value.setMaximum( chan_range )
        self.layout.xyy_3_value.setMaximum( chan_range )
        self.Pigmento_RELEASE()
        Krita.instance().writeSetting( DOCKER_NAME, "krange", str( krange ) )
    def Range_LAB( self, chan_range ):
        chan_range = int( self.geometry.Limit_Unit( chan_range ) )
        krange["lab_1"] = chan_range
        krange["lab_2"] = chan_range
        krange["lab_3"] = chan_range
        self.layout.lab_1_value.setMaximum( chan_range )
        self.layout.lab_2_value.setMaximum( chan_range )
        self.layout.lab_3_value.setMaximum( chan_range )
        self.Pigmento_RELEASE()
        Krita.instance().writeSetting( DOCKER_NAME, "krange", str( krange ) )
    def Range_LCH( self, chan_range ):
        chan_range = int( self.geometry.Limit_Unit( chan_range ) )
        krange["lch_1"] = chan_range
        krange["lch_2"] = chan_range
        krange["lch_3"] = chan_range
        self.layout.lch_1_value.setMaximum( chan_range )
        self.layout.lch_2_value.setMaximum( chan_range )
        self.layout.lch_3_value.setMaximum( chan_range )
        self.Pigmento_RELEASE()
        Krita.instance().writeSetting( DOCKER_NAME, "krange", str( krange ) )
    # Space Range Reset
    def Reset_AAA( self ):
        self.dialog.range_aaa.setValue( self.doc["depth"] )
        self.Pigmento_RELEASE()
        self.Reset_UnFocus()
    def Reset_RGB( self ):
        self.dialog.range_rgb.setValue( self.doc["depth"] )
        self.Pigmento_RELEASE()
        self.Reset_UnFocus()
    def Reset_CMY( self ):
        self.dialog.range_cmy.setValue( self.doc["depth"] )
        self.Pigmento_RELEASE()
        self.Reset_UnFocus()
    def Reset_CMYK( self ):
        self.dialog.range_cmyk.setValue( self.doc["depth"] )
        self.Pigmento_RELEASE()
        self.Reset_UnFocus()
    def Reset_RYB( self ):
        self.dialog.range_ryb.setValue( self.doc["depth"] )
        self.Pigmento_RELEASE()
        self.Reset_UnFocus()
    def Reset_YUV( self ):
        self.dialog.range_yuv.setValue( self.doc["depth"] )
        self.Pigmento_RELEASE()
        self.Reset_UnFocus()
    def Reset_HUE( self ):
        self.dialog.range_hue.setValue( 360 )
        self.Pigmento_RELEASE()
        self.Reset_UnFocus()
    def Reset_HSV( self ):
        self.dialog.range_hsv.setValue( self.doc["depth"] )
        self.Pigmento_RELEASE()
        self.Reset_UnFocus()
    def Reset_HSL( self ):
        self.dialog.range_hsl.setValue( self.doc["depth"] )
        self.Pigmento_RELEASE()
        self.Reset_UnFocus()
    def Reset_HCY( self ):
        self.dialog.range_hcy.setValue( self.doc["depth"] )
        self.Pigmento_RELEASE()
        self.Reset_UnFocus()
    def Reset_ARD( self ):
        self.dialog.range_ard.setValue( self.doc["depth"] )
        self.Pigmento_RELEASE()
        self.Reset_UnFocus()
    def Reset_XYZ( self ):
        self.dialog.range_xyz.setValue( self.doc["depth"] )
        self.Pigmento_RELEASE()
        self.Reset_UnFocus()
    def Reset_XYY( self ):
        self.dialog.range_xyy.setValue( self.doc["depth"] )
        self.Pigmento_RELEASE()
        self.Reset_UnFocus()
    def Reset_LAB( self ):
        self.dialog.range_lab.setValue( self.doc["depth"]+1 )
        self.Pigmento_RELEASE()
        self.Reset_UnFocus()
    def Reset_LCH( self ):
        self.dialog.range_lch.setValue( self.doc["depth"] )
        self.Pigmento_RELEASE()
        self.Reset_UnFocus()
    # Reset Focus
    def Reset_UnFocus( self ):
        self.dialog.range_aaa.clearFocus()
        self.dialog.range_rgb.clearFocus()
        self.dialog.range_cmy.clearFocus()
        self.dialog.range_cmyk.clearFocus()
        self.dialog.range_ryb.clearFocus()
        self.dialog.range_yuv.clearFocus()

        self.dialog.range_hue.clearFocus()
        self.dialog.range_hsv.clearFocus()
        self.dialog.range_hsl.clearFocus()
        self.dialog.range_hcy.clearFocus()
        self.dialog.range_ard.clearFocus()

        self.dialog.range_xyz.clearFocus()
        self.dialog.range_xyy.clearFocus()
        self.dialog.range_lab.clearFocus()

        self.dialog.range_lch.clearFocus()

    # Locks
    def Lock_CMYK_4( self, boolean ):
        # UI
        if boolean == True:
            self.layout.cmyk_4_label.setText( "" ) # LOCKED
            self.layout.cmyk_4_label.setIcon( self.qicon_lock_layout )
            self.dialog.chan_cmyk.setIcon( self.qicon_lock_dialog )
        else:
            self.layout.cmyk_4_label.setText( "K" ) # Unlocked
            self.layout.cmyk_4_label.setIcon( self.qicon_none )
            self.dialog.chan_cmyk.setIcon( self.qicon_none )
        # Variables
        self.lock_cmyk_4 = boolean
        self.update()
        # Save
        Krita.instance().writeSetting( DOCKER_NAME, "lock_cmyk_4", str( self.lock_cmyk_4 ) )

    # Format
    def Display_Labels( self, boolean ):
        # Variables
        self.disp_labels = boolean
        if boolean == True:
            l = 20
            s = 1
        else:
            l = 0
            s = 0

        self.layout.aaa_label.setMaximumWidth( l )
        self.layout.rgb_label.setMaximumWidth( l )
        self.layout.cmy_label.setMaximumWidth( l )
        self.layout.cmyk_label.setMaximumWidth( l )
        self.layout.ryb_label.setMaximumWidth( l )
        self.layout.yuv_label.setMaximumWidth( l )
        self.layout.hsv_label.setMaximumWidth( l )
        self.layout.hsl_label.setMaximumWidth( l )
        self.layout.hcy_label.setMaximumWidth( l )
        self.layout.ard_label.setMaximumWidth( l )
        self.layout.xyz_label.setMaximumWidth( l )
        self.layout.xyy_label.setMaximumWidth( l )
        self.layout.lab_label.setMaximumWidth( l )
        self.layout.lch_label.setMaximumWidth( l )
        self.layout.kkk_label.setMaximumWidth( l )

        # Channel Set
        self.layout.channel_set_layout.setHorizontalSpacing( s )
        # Update
        self.Update_Size()

        # Save
        Krita.instance().writeSetting( DOCKER_NAME, "disp_labels", str( self.disp_labels ) )
    def Display_Values( self, boolean ):
        # Variables
        self.disp_values = boolean
        if boolean == True:
            v = 100
            s = 1
        else:
            v = 0
            s = 0

        self.layout.aaa_value.setMaximumWidth( v )
        self.layout.rgb_value.setMaximumWidth( v )
        self.layout.cmy_value.setMaximumWidth( v )
        self.layout.cmyk_value.setMaximumWidth( v )
        self.layout.ryb_value.setMaximumWidth( v )
        self.layout.yuv_value.setMaximumWidth( v )
        self.layout.hsv_value.setMaximumWidth( v )
        self.layout.hsl_value.setMaximumWidth( v )
        self.layout.hcy_value.setMaximumWidth( v )
        self.layout.ard_value.setMaximumWidth( v )
        self.layout.xyz_value.setMaximumWidth( v )
        self.layout.xyy_value.setMaximumWidth( v )
        self.layout.lab_value.setMaximumWidth( v )
        self.layout.lch_value.setMaximumWidth( v )
        self.layout.kkk_value.setMaximumWidth( v )

        # Channel Set
        self.layout.channel_set_layout.setHorizontalSpacing( s )
        # Update
        self.Update_Size()

        # Save
        Krita.instance().writeSetting( DOCKER_NAME, "disp_values", str( self.disp_values ) )
    def Hue_Shine( self, boolean ):
        self.hue_shine = boolean
        self.Channel_Set_Style()
        Krita.instance().writeSetting( DOCKER_NAME, "hue_shine", str( self.hue_shine ) )

    # Shortcuts Channel
    def Key_1_Channel( self ):
        self.key_1_chan = self.dialog.key_1_chan.currentText()
        Krita.instance().writeSetting( DOCKER_NAME, "key_1_chan", str( self.key_1_chan ) )
    def Key_2_Channel( self ):
        self.key_2_chan = self.dialog.key_2_chan.currentText()
        Krita.instance().writeSetting( DOCKER_NAME, "key_2_chan", str( self.key_2_chan ) )
    def Key_3_Channel( self ):
        self.key_3_chan = self.dialog.key_3_chan.currentText()
        Krita.instance().writeSetting( DOCKER_NAME, "key_3_chan", str( self.key_3_chan ) )
    def Key_4_Channel( self ):
        self.key_4_chan = self.dialog.key_4_chan.currentText()
        Krita.instance().writeSetting( DOCKER_NAME, "key_4_chan", str( self.key_4_chan ) )
    # Shortcuts Factor
    def Key_1_Factor( self, factor ):
        self.key_1_factor = factor
        Krita.instance().writeSetting( DOCKER_NAME, "key_1_factor", str( self.key_1_factor ) )
    def Key_2_Factor( self, factor ):
        self.key_2_factor = factor
        Krita.instance().writeSetting( DOCKER_NAME, "key_2_factor", str( self.key_2_factor ) )
    def Key_3_Factor( self, factor ):
        self.key_3_factor = factor
        Krita.instance().writeSetting( DOCKER_NAME, "key_3_factor", str( self.key_3_factor ) )
    def Key_4_Factor( self, factor ):
        self.key_4_factor = factor
        Krita.instance().writeSetting( DOCKER_NAME, "key_4_factor", str( self.key_4_factor ) )

    # Reference
    def Color_Name( self ):
        color_name = self.dialog.name_display.text()
        if color_name != "":
            hc = QApplication.clipboard()
            hc.clear()
            hc.setText( color_name )
            self.Label_String( "NAME COPY" )

    # Colors Spaces
    def CS_Luminosity( self, cs_luminosity ):
        # Variables
        self.convert.Set_Luminosity( cs_luminosity )
        # Update
        self.Pigmento_RELEASE()
        self.Panel_Convert_Update()
        self.update()
        # Save
        Krita.instance().writeSetting( DOCKER_NAME, "cs_luminosity", str( cs_luminosity ) )
    def CS_Matrix( self, cs_matrix ):
        # Variables
        self.convert.Set_Matrix( cs_matrix )
        # Update
        self.Panel_Convert_Update()
        self.update()
        # Save
        Krita.instance().writeSetting( DOCKER_NAME, "cs_matrix", str( cs_matrix ) )
    def Panel_Convert_Update( self ):
        self.panel_square.Init_Convert( self.convert )
        self.panel_huecircle.Init_Convert( self.convert )
        self.panel_huesubpanel.Init_Convert( self.convert )
        self.panel_gamut.Init_Convert( self.convert )
        self.panel_hexagon.Init_Convert( self.convert )
        self.panel_luma.Init_Convert( self.convert )
        self.panel_dot.Init_Convert( self.convert )

    # Performance
    def Performace_Release( self, boolean ):
        self.performance_release = boolean
        Krita.instance().writeSetting( DOCKER_NAME, "performance_release", str( self.performance_release ) )
    def Performace_Inaccurate( self, boolean ):
        self.performance_inaccurate = boolean
        Krita.instance().writeSetting( DOCKER_NAME, "performance_inaccurate", str( self.performance_inaccurate ) )

    # Dialogs
    def Menu_Settings( self ):
        # Display
        self.dialog.show()
        # Resize Geometry
        qmw = Krita.instance().activeWindow().qwindow()
        px = qmw.x()
        py = qmw.y()
        w2 = qmw.width() * 0.5
        h2 = qmw.height() * 0.5
        size = 500
        self.dialog.setGeometry( int( px + w2 - size * 0.5 ), int( py + h2 - size * 0.5 ), int( size ), int( size ) )
    def Menu_Manual( self ):
        url = "https://github.com/EyeOdin/Pigment.O/wiki"
        webbrowser.open_new( url )
    def Menu_License( self ):
        url = "https://github.com/EyeOdin/Pigment.O/blob/master/LICENSE"
        webbrowser.open_new( url )

    # Event Filter
    def Menu_Context_History( self, event ):
        # Menu
        qmenu = QMenu( self )
        qmenu_clear = qmenu.addAction( "CLEAR" )
        # Execute
        widget = self.layout.history_set.mapToGlobal( self.layout.history_list.geometry().topLeft() )
        mouse = event.pos()
        qpoint = QPoint( widget.x()+mouse.x(), widget.y()+mouse.y() )
        action = qmenu.exec_( qpoint )
        # Triggers
        if action == qmenu_clear:
            self.History_CLEAR()
    def Menu_Mode_Press( self, event ):
        # Menu
        qmenu = QMenu( self )
        # Actions
        qmenu_on = qmenu.addAction( "ON" )
        qmenu_write = qmenu.addAction( "WRITE" )
        qmenu_read = qmenu.addAction( "READ" )
        qmenu_off = qmenu.addAction( "OFF" )
        # Icons
        qmenu_on.setIcon( self.qicon_on )
        qmenu_write.setIcon( self.qicon_write )
        qmenu_read.setIcon( self.qicon_read )
        qmenu_off.setIcon( self.qicon_off )

        # Execute
        geo = self.layout.mode.geometry()
        qpoint = geo.bottomLeft()
        position = self.layout.footer_widget.mapToGlobal( qpoint )
        action = qmenu.exec_( position )
        # Triggers
        if action == qmenu_on:
            self.Mode_Index( 0 )
        elif action == qmenu_write:
            self.Mode_Index( 1 )
        elif action == qmenu_read:
            self.Mode_Index( 2 )
        elif action == qmenu_off:
            self.Mode_Index( 3 )
    def Menu_Mode_Wheel( self, event ):
        delta = event.angleDelta()
        if event.modifiers() == QtCore.Qt.NoModifier:
            delta_y = delta.y()
            value = 0
            if delta_y > 20:
                value = -1
            if delta_y < -20:
                value = 1
            if ( value == -1 or value == 1 ):
                new_index = self.geometry.Limit_Range( self.mode_index + value, 0, 3 )
                if self.mode_index != new_index:
                    self.Mode_Index( new_index )

    # Resize Event
    def Update_Size( self ):
        #region Header

        self.color_header.Set_Size( self.layout.color_header.width(), self.layout.color_header.height() )
        self.harmony_swatch.Set_Size( self.layout.harmony_swatch.width(), self.layout.harmony_swatch.height() )
        self.harmony_spread.Set_Size( self.layout.harmony_spread.width(), self.layout.harmony_spread.height() )

        #endregion
        #region Panels

        # Fill
        self.panel_fill.Set_Size( self.layout.panel_fill.width(), self.layout.panel_fill.height() )
        # Square
        self.panel_square.Set_Size( self.layout.panel_square.width(), self.layout.panel_square.height() )
        # Hue
        self.panel_huecircle.Set_Size( self.layout.panel_hue.width(), self.layout.panel_hue.height(), self.huecircle_shape )
        self.HueCircle_Geo( self.layout.panel_hue.width(), self.layout.panel_hue.height() )
        # Gamut
        self.panel_gamut.Set_Size( self.layout.panel_gamut.width(), self.layout.panel_gamut.height() )
        # Hexagon
        self.panel_hexagon.Set_Size( self.layout.panel_hexagon.width(), self.layout.panel_hexagon.height() )
        # Yuv
        self.panel_luma.Set_Size( self.layout.panel_luma.width(), self.layout.panel_luma.height() )
        # Dot
        self.panel_dot.Set_Size( self.layout.panel_dot.width(), self.layout.panel_dot.height() )
        self.pin_d1.Set_Size( self.layout.dot_1.width(), self.layout.dot_1.height() )
        self.pin_d2.Set_Size( self.layout.dot_2.width(), self.layout.dot_2.height() )
        self.pin_d3.Set_Size( self.layout.dot_3.width(), self.layout.dot_3.height() )
        self.pin_d4.Set_Size( self.layout.dot_4.width(), self.layout.dot_4.height() )
        # Mask
        self.panel_mask.Set_Size( self.layout.panel_mask.width(), self.layout.panel_mask.height() )
        self.mask_f3.Set_Size( self.layout.fg_3_color.width(), self.layout.fg_3_color.height() )
        self.mask_f2.Set_Size( self.layout.fg_2_color.width(), self.layout.fg_2_color.height() )
        self.mask_f1.Set_Size( self.layout.fg_1_color.width(), self.layout.fg_1_color.height() )
        self.mask_d6.Set_Size( self.layout.dif_6_color.width(), self.layout.dif_6_color.height() )
        self.mask_d5.Set_Size( self.layout.dif_5_color.width(), self.layout.dif_5_color.height() )
        self.mask_d4.Set_Size( self.layout.dif_4_color.width(), self.layout.dif_4_color.height() )
        self.mask_d3.Set_Size( self.layout.dif_3_color.width(), self.layout.dif_3_color.height() )
        self.mask_d2.Set_Size( self.layout.dif_2_color.width(), self.layout.dif_2_color.height() )
        self.mask_d1.Set_Size( self.layout.dif_1_color.width(), self.layout.dif_1_color.height() )
        self.mask_b3.Set_Size( self.layout.bg_3_color.width(), self.layout.bg_3_color.height() )
        self.mask_b2.Set_Size( self.layout.bg_2_color.width(), self.layout.bg_2_color.height() )
        self.mask_b1.Set_Size( self.layout.bg_1_color.width(), self.layout.bg_1_color.height() )

        self.Panels_Set_Value()

        #endregion
        #region Channels

        # AAA
        self.aaa_1_slider.Set_Size( self.layout.aaa_1_slider.width(), self.layout.aaa_1_slider.height() )
        # RGB
        self.rgb_1_slider.Set_Size( self.layout.rgb_1_slider.width(), self.layout.rgb_1_slider.height() )
        self.rgb_2_slider.Set_Size( self.layout.rgb_2_slider.width(), self.layout.rgb_2_slider.height() )
        self.rgb_3_slider.Set_Size( self.layout.rgb_3_slider.width(), self.layout.rgb_3_slider.height() )
        # CMY
        self.cmy_1_slider.Set_Size( self.layout.cmy_1_slider.width(), self.layout.cmy_1_slider.height() )
        self.cmy_2_slider.Set_Size( self.layout.cmy_2_slider.width(), self.layout.cmy_2_slider.height() )
        self.cmy_3_slider.Set_Size( self.layout.cmy_3_slider.width(), self.layout.cmy_3_slider.height() )
        # CMYK
        self.cmyk_1_slider.Set_Size( self.layout.cmyk_1_slider.width(), self.layout.cmyk_1_slider.height() )
        self.cmyk_2_slider.Set_Size( self.layout.cmyk_2_slider.width(), self.layout.cmyk_2_slider.height() )
        self.cmyk_3_slider.Set_Size( self.layout.cmyk_3_slider.width(), self.layout.cmyk_3_slider.height() )
        self.cmyk_4_slider.Set_Size( self.layout.cmyk_4_slider.width(), self.layout.cmyk_4_slider.height() )
        # RYB
        self.ryb_1_slider.Set_Size( self.layout.ryb_1_slider.width(), self.layout.ryb_1_slider.height() )
        self.ryb_2_slider.Set_Size( self.layout.ryb_2_slider.width(), self.layout.ryb_2_slider.height() )
        self.ryb_3_slider.Set_Size( self.layout.ryb_3_slider.width(), self.layout.ryb_3_slider.height() )
        # YUV
        self.yuv_1_slider.Set_Size( self.layout.yuv_1_slider.width(), self.layout.yuv_1_slider.height() )
        self.yuv_2_slider.Set_Size( self.layout.yuv_2_slider.width(), self.layout.yuv_2_slider.height() )
        self.yuv_3_slider.Set_Size( self.layout.yuv_3_slider.width(), self.layout.yuv_3_slider.height() )

        # HSV
        self.hsv_1_slider.Set_Size( self.layout.hsv_1_slider.width(), self.layout.hsv_1_slider.height() )
        self.hsv_2_slider.Set_Size( self.layout.hsv_2_slider.width(), self.layout.hsv_2_slider.height() )
        self.hsv_3_slider.Set_Size( self.layout.hsv_3_slider.width(), self.layout.hsv_3_slider.height() )
        # HSL
        self.hsl_1_slider.Set_Size( self.layout.hsl_1_slider.width(), self.layout.hsl_1_slider.height() )
        self.hsl_2_slider.Set_Size( self.layout.hsl_2_slider.width(), self.layout.hsl_2_slider.height() )
        self.hsl_3_slider.Set_Size( self.layout.hsl_3_slider.width(), self.layout.hsl_3_slider.height() )
        # HCY
        self.hcy_1_slider.Set_Size( self.layout.hcy_1_slider.width(), self.layout.hcy_1_slider.height() )
        self.hcy_2_slider.Set_Size( self.layout.hcy_2_slider.width(), self.layout.hcy_2_slider.height() )
        self.hcy_3_slider.Set_Size( self.layout.hcy_3_slider.width(), self.layout.hcy_3_slider.height() )
        # ARD
        self.ard_1_slider.Set_Size( self.layout.ard_1_slider.width(), self.layout.ard_1_slider.height() )
        self.ard_2_slider.Set_Size( self.layout.ard_2_slider.width(), self.layout.ard_2_slider.height() )
        self.ard_3_slider.Set_Size( self.layout.ard_3_slider.width(), self.layout.ard_3_slider.height() )

        # XYZ
        self.xyz_1_slider.Set_Size( self.layout.xyz_1_slider.width(), self.layout.xyz_1_slider.height() )
        self.xyz_2_slider.Set_Size( self.layout.xyz_2_slider.width(), self.layout.xyz_2_slider.height() )
        self.xyz_3_slider.Set_Size( self.layout.xyz_3_slider.width(), self.layout.xyz_3_slider.height() )
        # XYY
        self.xyy_1_slider.Set_Size( self.layout.xyy_1_slider.width(), self.layout.xyy_1_slider.height() )
        self.xyy_2_slider.Set_Size( self.layout.xyy_2_slider.width(), self.layout.xyy_2_slider.height() )
        self.xyy_3_slider.Set_Size( self.layout.xyy_3_slider.width(), self.layout.xyy_3_slider.height() )
        # LAB
        self.lab_1_slider.Set_Size( self.layout.lab_1_slider.width(), self.layout.lab_1_slider.height() )
        self.lab_2_slider.Set_Size( self.layout.lab_2_slider.width(), self.layout.lab_2_slider.height() )
        self.lab_3_slider.Set_Size( self.layout.lab_3_slider.width(), self.layout.lab_3_slider.height() )

        # LCH
        self.lch_1_slider.Set_Size( self.layout.lch_1_slider.width(), self.layout.lch_1_slider.height() )
        self.lch_2_slider.Set_Size( self.layout.lch_2_slider.width(), self.layout.lch_2_slider.height() )
        self.lch_3_slider.Set_Size( self.layout.lch_3_slider.width(), self.layout.lch_3_slider.height() )

        # KKK
        self.kkk_1_slider.Set_Size( self.layout.kkk_1_slider.width(), self.layout.kkk_1_slider.height() )

        # Adjust Handles
        self.Update_Values()

        #endregion
        #region Mixer

        # POLE
        self.pole_slider.Set_Size( self.layout.pole_slider.width(), self.layout.pole_slider.height() )
        self.pole_pin_a.Set_Size( self.layout.pole_pin_a.width(), self.layout.pole_pin_a.height() )
        self.pole_pin_b.Set_Size( self.layout.pole_pin_b.width(), self.layout.pole_pin_b.height() )
        # Mixer 000
        for i in range( 0, len( self.mixer_module) ):
            self.mixer_module[i]["l"].Set_Size( self.mixer_widget[i]["l"].width(), self.mixer_widget[i]["l"].height() )
            self.mixer_module[i]["m"].Set_Size( self.mixer_widget[i]["m"].width(), self.mixer_widget[i]["m"].height() )
            self.mixer_module[i]["r"].Set_Size( self.mixer_widget[i]["r"].width(), self.mixer_widget[i]["r"].height() )

        #endregion
        #region Pin

        for i in range( 0, len( self.pin_module ) ):
            self.pin_module[i].Set_Size( self.pin_widget[i].width(), self.pin_widget[i].height() )

        #endregion

        self.update()
    def Resize_Print( self, event ):
        # Used doing a photoshoot
        width = self.width()
        height = self.height()
        self.Message_Log( "SIZE", f"{ width } x { height }" )

    #endregion
    #region Management

    # Communication
    def Message_Log( self, operation, message ):
        string = f"{ DOCKER_NAME } | { operation } { message }"
        try:QtCore.qDebug( string )
        except:pass
    def Message_Warnning( self, operation, message ):
        string = f"{ DOCKER_NAME } | { operation.upper() } { message }"
        QMessageBox.information( QWidget(), i18n( "Warnning" ), i18n( string ) )
    def Message_Float( self, operation, message, icon ):
        ki = Krita.instance()
        string = f"{ DOCKER_NAME } | { operation.upper() } { message }"
        ki.activeWindow().activeView().showFloatingMessage( string, ki.icon( icon ), 5000, 0 )

    # Document
    def Current_Document( self ):
        # Active Node Type
        # type_layer = ["paintlayer", "grouplayer", "clonelayer", "vectorlayer", "filterlayer", "filllayer", "filelayer"]
        # type_mask = ["transparencymask", "filtermask", "colorizemask", "transformmask", "selectionmask"]
        try:
            # Instance
            ki = Krita.instance()
            ad = ki.activeDocument()
            aw = ki.activeWindow()
            av = aw.activeView()
            # Canvas
            vc = av.canvas()
            # Document Color
            d_cm = ad.colorModel()
            d_cd = ad.colorDepth()
            d_cp = ad.colorProfile()
            # Vector Layers
            vi = self.Vector_Index( ad )
            # Node
            an = ad.activeNode()
            n_cm = an.colorModel()
            n_cd = an.colorDepth()
            n_cp = an.colorProfile()
            n_uid = an.uniqueId()
            # Colors
            fgc = av.foregroundColor()
            bgc = av.backgroundColor()
            # Biggest value for Bit Depth
            depth = self.Node_Depth( n_cd )
            # Color Model
            cmodel = self.Node_Color_Model( n_cm )

            # Create List
            document = {
                "ad"        : ad,
                "vc"        : vc,
                "vi"        : vi,
                "n_cm"      : n_cm,
                "n_cd"      : n_cd,
                "n_cp"      : n_cp,
                "n_uid"     : n_uid,
                "fgc"       : fgc,
                "bgc"       : bgc,
                "depth"     : depth,
                "cmodel"    : cmodel,
                }
        except:
            document = self.Document_None()
        return document
    def Document_None( self ):
        document = {
            "ad"        : None,
            "vc"        : None,
            "vi"        : None,
            "n_cm"      : None,
            "n_cd"      : None,
            "n_cp"      : None,
            "n_uid"     : None,
            "fgc"       : None,
            "bgc"       : None,
            "b_cm"      : None,
            "b_cd"      : None,
            "b_cp"      : None,
            "depth"     : 255,
            "cmodel"    : None,
            }
        return document
    def Node_Color_Model( self, mode ):
        color_model = None
        if mode in [ "A", "GRAYA" ]:    color_model = "A"
        elif mode in [ "RGBA", None ]:  color_model = "RGB"
        elif mode == "CMYKA":           color_model = "CMYK"
        elif mode == "YCbCr":           color_model = "YUV"
        elif mode == "XYZA":            color_model = "XYZ"
        elif mode == "LABA":            color_model = "LAB"
        return color_model
    def Node_Depth( self, depth ):
        color_depth = None
        if depth == "U8":               color_depth = 255
        elif depth == "U16":            color_depth = 65535
        elif depth in [ "F16", "F32" ]: color_depth = 1
        return color_depth
    def Vector_Index( self, ad ):
        node = ad.activeNode()
        if node.type() == "vectorlayer":
            index = []
            shapes = node.shapes()
            for i in range( 0, len( shapes ) ):
                if shapes[i].isSelected():
                    index.append( i )
            if len( index ) == 0:
                index = None
        else:
            index = None
        return index

    # Leave Event
    def Clear_Focus( self ):
        # AAA
        self.layout.aaa_1_value.clearFocus()
        # RGB
        self.layout.rgb_1_value.clearFocus()
        self.layout.rgb_2_value.clearFocus()
        self.layout.rgb_3_value.clearFocus()
        # CMY
        self.layout.cmy_1_value.clearFocus()
        self.layout.cmy_2_value.clearFocus()
        self.layout.cmy_3_value.clearFocus()
        # CMYK
        self.layout.cmyk_1_value.clearFocus()
        self.layout.cmyk_2_value.clearFocus()
        self.layout.cmyk_3_value.clearFocus()
        self.layout.cmyk_4_value.clearFocus()
        # RYB
        self.layout.ryb_1_value.clearFocus()
        self.layout.ryb_2_value.clearFocus()
        self.layout.ryb_3_value.clearFocus()
        # YUV
        self.layout.yuv_1_value.clearFocus()
        self.layout.yuv_2_value.clearFocus()
        self.layout.yuv_3_value.clearFocus()

        # HSV
        self.layout.hsv_1_value.clearFocus()
        self.layout.hsv_2_value.clearFocus()
        self.layout.hsv_3_value.clearFocus()
        # HSL
        self.layout.hsl_1_value.clearFocus()
        self.layout.hsl_2_value.clearFocus()
        self.layout.hsl_3_value.clearFocus()
        # HCY
        self.layout.hcy_1_value.clearFocus()
        self.layout.hcy_2_value.clearFocus()
        self.layout.hcy_3_value.clearFocus()
        # ARD
        self.layout.ard_1_value.clearFocus()
        self.layout.ard_2_value.clearFocus()
        self.layout.ard_3_value.clearFocus()

        # XYZ
        self.layout.xyz_1_value.clearFocus()
        self.layout.xyz_2_value.clearFocus()
        self.layout.xyz_3_value.clearFocus()
        # XYY
        self.layout.xyy_1_value.clearFocus()
        self.layout.xyy_2_value.clearFocus()
        self.layout.xyy_3_value.clearFocus()
        # LAB
        self.layout.lab_1_value.clearFocus()
        self.layout.lab_2_value.clearFocus()
        self.layout.lab_3_value.clearFocus()

        # LCH
        self.layout.lch_1_value.clearFocus()
        self.layout.lch_2_value.clearFocus()
        self.layout.lch_3_value.clearFocus()

        # KKK
        self.layout.kkk_1_value.clearFocus()

        # HEX
        self.layout.hex_string.clearFocus()

    # Modules variables
    def Label_String( self, text ):
        self.layout.label.setText( str( text ) )
    def Text_Index( self, mode ):
        chan_0 = ""
        chan_1 = ""
        chan_2 = ""
        chan_3 = ""
        if mode == "A":
            chan_0 = "Gray"
        if mode == "RGB":
            chan_0 = "Red"
            chan_1 = "Green"
            chan_2 = "Blue"
        if mode == "CMY":
            chan_0 = "Cyan"
            chan_1 = "Magenta"
            chan_2 = "Yellow"
        if mode == "CMYK":
            chan_0 = "Cyan"
            chan_1 = "Magenta"
            chan_2 = "Yellow"
            chan_3 = "Key"
        if mode == "RYB":
            chan_0 = "Red"
            chan_1 = "Yellow"
            chan_2 = "Blue"
        if mode == "YUV":
            chan_0 = "Luma"
            chan_1 = "Comp Blue"
            chan_2 = "Comp Red"
        if mode == "HSV":
            chan_0 = "Hue"
            chan_1 = "Saturation"
            chan_2 = "Value"
        if mode == "HSL":
            chan_0 = "Hue"
            chan_1 = "Saturation"
            chan_2 = "Lightness"
        if mode == "HCY":
            chan_0 = "Hue"
            chan_1 = "Chroma"
            chan_2 = "Luma"
        if mode == "ARD":
            chan_0 = "Angle"
            chan_1 = "Ratio"
            chan_2 = "Depth"
        if mode == "XYZ":
            chan_0 = "XYZ X"
            chan_1 = "XYZ Y"
            chan_2 = "XYZ Z"
        if mode == "XYY":
            chan_0 = "xyY x"
            chan_1 = "xyY y"
            chan_2 = "xyY Y"
        if mode == "LAB":
            chan_0 = "LAB L*"
            chan_1 = "LAB A*"
            chan_2 = "LAB B*"
        if mode == "LCH":
            chan_0 = "Luminosity"
            chan_1 = "Chroma"
            chan_2 = "Hue"
        return chan_0, chan_1, chan_2, chan_3

    # Dictionanries
    def Dict_Copy( self, active, load ):
        keys = list( active.keys() )
        for k in keys:
            active[k] = load[k]

    # Hue
    def Hue_Index( self, mode ):
        c1 = f"{ mode.lower() }_1"
        c2 = f"{ mode.lower() }_2"
        c3 = f"{ mode.lower() }_3"
        return c1, c2, c3

    # Stops
    def Sliders_Stops_Load( self, dictionary ):
        # AAA
        self.aaa_1_slider.Set_Stops( dictionary["aaa_1"] )
        # RGB
        self.rgb_1_slider.Set_Stops( dictionary["rgb_1"] )
        self.rgb_2_slider.Set_Stops( dictionary["rgb_2"] )
        self.rgb_3_slider.Set_Stops( dictionary["rgb_3"] )
        # CMY
        self.cmy_1_slider.Set_Stops( dictionary["cmy_1"] )
        self.cmy_2_slider.Set_Stops( dictionary["cmy_2"] )
        self.cmy_3_slider.Set_Stops( dictionary["cmy_3"] )
        # CMYK
        self.cmyk_1_slider.Set_Stops( dictionary["cmyk_1"] )
        self.cmyk_2_slider.Set_Stops( dictionary["cmyk_2"] )
        self.cmyk_3_slider.Set_Stops( dictionary["cmyk_3"] )
        self.cmyk_4_slider.Set_Stops( dictionary["cmyk_4"] )
        # RYB
        self.ryb_1_slider.Set_Stops( dictionary["ryb_1"] )
        self.ryb_2_slider.Set_Stops( dictionary["ryb_2"] )
        self.ryb_3_slider.Set_Stops( dictionary["ryb_3"] )
        # YUV
        self.yuv_1_slider.Set_Stops( dictionary["yuv_1"] )
        self.yuv_2_slider.Set_Stops( dictionary["yuv_2"] )
        self.yuv_3_slider.Set_Stops( dictionary["yuv_3"] )

        # HSV
        self.hsv_1_slider.Set_Stops( dictionary["hsv_1"] )
        self.hsv_2_slider.Set_Stops( dictionary["hsv_2"] )
        self.hsv_3_slider.Set_Stops( dictionary["hsv_3"] )
        # HSL
        self.hsl_1_slider.Set_Stops( dictionary["hsl_1"] )
        self.hsl_2_slider.Set_Stops( dictionary["hsl_2"] )
        self.hsl_3_slider.Set_Stops( dictionary["hsl_3"] )
        # HCY
        self.hcy_1_slider.Set_Stops( dictionary["hcy_1"] )
        self.hcy_2_slider.Set_Stops( dictionary["hcy_2"] )
        self.hcy_3_slider.Set_Stops( dictionary["hcy_3"] )
        # ARD
        self.ard_1_slider.Set_Stops( dictionary["ard_1"] )
        self.ard_2_slider.Set_Stops( dictionary["ard_2"] )
        self.ard_3_slider.Set_Stops( dictionary["ard_3"] )

        # XYZ
        self.xyz_1_slider.Set_Stops( dictionary["xyz_1"] )
        self.xyz_2_slider.Set_Stops( dictionary["xyz_2"] )
        self.xyz_3_slider.Set_Stops( dictionary["xyz_3"] )
        # XYY
        self.xyy_1_slider.Set_Stops( dictionary["xyy_1"] )
        self.xyy_2_slider.Set_Stops( dictionary["xyy_2"] )
        self.xyy_3_slider.Set_Stops( dictionary["xyy_3"] )
        # LAB
        self.lab_1_slider.Set_Stops( dictionary["lab_1"] )
        self.lab_2_slider.Set_Stops( dictionary["lab_2"] )
        self.lab_3_slider.Set_Stops( dictionary["lab_3"] )

        # LCH
        self.lch_1_slider.Set_Stops( dictionary["lch_1"] )
        self.lch_2_slider.Set_Stops( dictionary["lch_2"] )
        self.lch_3_slider.Set_Stops( dictionary["lch_3"] )

        # KKK
        self.kkk_1_slider.Set_Stops( dictionary["kkk_1"] )

        # POLE
        self.pole_slider.Set_Stops( dictionary["pole_1"] )
        # Mixers
        for i in range( 0, len( self.mixer_widget ) ):
            self.mixer_module[i]["m"].Set_Stops( dictionary["mixer"] )

    # Troubleshooting
    def Inspect():
        functions = list()
        ins = inspect.stack()
        for item in ins:
            functions.append( item[3] )
        QtCore.qDebug( f"Inspect = { functions }" )

    #endregion
    #region API

    # Read
    def API_Request_FG( self ):
        self.Update_WhenInvisible()
        return kac
    def API_Request_BG( self ):
        self.Update_WhenInvisible()
        return kbc
    def API_Request_Wheel_Space( self ):
        self.Update_WhenInvisible()
        return self.wheel_space
    def Update_WhenInvisible( self ):
        if self.layout.isVisible() == False:
            self.Krita_to_Pigmento()
    # Convert
    def API_Color_Name( self, hex ):
        name = self.convert.hex6_to_name( hex, color_names )
        return name
    def API_Convert_Color( self, mode, var_1, var_2, var_3, var_4, color ):
        convert = self.Color_Convert( mode, var_1, var_2, var_3, var_4, color )
        return convert
    # Write
    def API_Input_Kelvin( self, kelvin ):
        # range : 1000-12000 neutral : 6500
        self.Kelvin_Class( kelvin )
        percent = self.convert.kkk_scale_to_percent( kelvin )
        self.Pigmento_PRESS( "KKK", percent, kelvin, 0, 0, self.cor )
        return self.cor
    def API_Input_Preview( self, mode, var_1, var_2, var_3, var_4 ):
        # mode : color space
        # var : 0-1
        self.widget_press = True
        self.Color_Convert( mode, var_1, var_2, var_3, var_4, self.cor )
        self.Sync_Elements( False, True, False )
        return self.cor
    def API_Input_Apply( self, mode, var_1, var_2, var_3, var_4 ):
        # mode : color space
        # var : 0-1
        self.widget_press = False
        self.Color_Convert( mode, var_1, var_2, var_3, var_4, self.cor )
        self.Sync_Elements( True, True, True )
        return self.cor
    def API_Image_Analyse( self, qimage ):
        try:
            report = True
            self.Analyse_Pixel( qimage )
        except:
            report = False
        return report

    # Panel Printer
    def API_Printer( self, mode, geo, directory, render, start_from, max_val ):
        # mode - color space of the map
        # geo - geometric shape of the map
        # directory - location to save zip file
        # render - location to render images. This folder is deleted and recreated after a cycle
        # start_from - start from given given number. Default is zero but if non zero nothing will be deleted.
        # max_val - finish at given number.
        # notes - YUV=255 UVD=255 HSV=360 HSL=360 HCY=360 CD_CA=255

        # Variables
        size = 256
        s2 = size * 0.5
        wtri = 0.5 * math.sqrt( 3 ) * size
        cda = [ "D", "A" ]

        # Range
        if start_from == None:
            start_from = 0
        if max_val == None:
            if geo in cda:
                max_val = 255
            else:
                max_val = 360

        # Document Modifier
        doc = self.Current_Document()
        cmodel = doc["cmodel"]
        n_cm = doc["n_cm"]
        n_cd = doc["n_cd"]
        n_cp = doc["n_cp"]
        vc = doc["vc"]

        # Temporary Folder
        zipname = f"{ cmodel }_{ mode }_{ geo }"
        temporary = os.path.join( render, zipname )
        os.mkdir( temporary, 0o666 )

        # Third Axis Loop
        for h in range( start_from, max_val+1 ):
            # Process update
            QApplication.processEvents()

            # Base Image to Edit
            qpixmap = QPixmap( size, size )
            qpixmap.fill( QColor( 0, 0, 0, 255 ) )
            qimage = qpixmap.toImage()

            # Calculate Pixels
            for y in range( 0, size ):
                for x in range( 0, size ):
                    # Variables
                    if geo in [ "3", "4", "R" ]:
                        # Hue
                        hue = h / max_val
                        # Hsx
                        inv_y = size-y
                        hsx = inv_y / size
                    if geo in cda:
                        # Hsx
                        hsx = h / max_val

                    # Geometry influence
                    if geo == "3":
                        if y >= 0 and y <= size * 0.5:
                            ix, iy = self.geometry.Trig_2D_Points_Lines_Intersection( 0, y, size, y, 1, 0, wtri + 1, size * 0.5 )
                        elif y > size * 0.5 and y <= size:
                            ix, iy = self.geometry.Trig_2D_Points_Lines_Intersection( 0, y, size, y, wtri + 1, size * 0.5, 1, size )
                        sat = self.geometry.Limit_Float( x / ix )
                    if geo == "4":
                        sat = x / size
                    if geo == "R":
                        if y >= 0 and y <= size * 0.5:
                            lix, liy = self.geometry.Trig_2D_Points_Lines_Intersection( 0, y, size, y, 0,    size * 0.5, size * 0.5, 0 )
                            rix, riy = self.geometry.Trig_2D_Points_Lines_Intersection( 0, y, size, y, size, size * 0.5, size * 0.5, 0 )
                        elif y > size*0.5 and y <= size:
                            lix, liy = self.geometry.Trig_2D_Points_Lines_Intersection( 0, y, size, y, 0,    size * 0.5, size * 0.5, size )
                            rix, riy = self.geometry.Trig_2D_Points_Lines_Intersection( 0, y, size, y, size, size * 0.5, size * 0.5, size )
                        dist = abs( rix - lix )
                        margin = abs( ( size - dist ) * 0.5 )
                        dx = x - margin
                        if ( dx > 0 and dist > 0 ):
                            sat = self.geometry.Limit_Range( dx / dist, 0, 1 )
                        else:
                            sat = 0
                    if geo in cda:
                        # Geometry
                        dist = self.geometry.Trig_2D_Points_Distance( x, y, s2, s2 )
                        if geo == "D":
                            angle = self.geometry.Trig_2D_Points_Lines_Angle( 0, s2, s2, s2, x, y ) / 360
                        if geo == "A":
                            hhh = self.geometry.Limit_Looper( self.geometry.Trig_2D_Points_Lines_Angle( 0, s2, s2, s2, x, y ) + hue_a, 360 )
                            angle = self.convert.huea_to_hued( hhh / 360 )
                        # Values
                        hue = angle
                        sat = self.geometry.Limit_Range( dist / s2, 0, 1 )

                    # Color Spaces to RGB
                    if mode == "YUV":
                        rgb = self.convert.yuv_to_rgb( h / max_val, x / 255, inv_y / 255 )
                    if mode == "UVD":
                        rgb = self.convert.uvd_to_rgb( x / 127.5 - 1, inv_y / 127.5 - 1, h / max_val )
                    if mode == "HSV":
                        rgb = self.convert.hsv_to_rgb( hue, sat, hsx )
                    if mode == "HSL":
                        rgb = self.convert.hsl_to_rgb( hue, sat, hsx )
                    if mode == "HCY":
                        rgb = self.convert.hcy_to_rgb( hue, sat, hsx )
                    if mode == "ARD":
                        rgb = self.convert.ard_to_rgb( hue, sat, hsx )

                    # Node Modifier
                    if cmodel == None:
                        color = rgb
                    if cmodel == "A":
                        aaa = self.convert.rgb_to_aaa( rgb[0], rgb[1], rgb[2] )
                        color = self.Color_Display( cmodel, n_cm, n_cd, n_cp, vc, aaa )
                    if cmodel == "RGB":
                        color = self.Color_Display( cmodel, n_cm, n_cd, n_cp, vc, rgb )
                    if cmodel == "CMYK":
                        cmyk = self.convert.rgb_to_cmyk( rgb[0], rgb[1], rgb[2], None )
                        color = self.Color_Display( cmodel, n_cm, n_cd, n_cp, vc, cmyk )
                    if cmodel == "YUV":
                        yuv = self.convert.rgb_to_yuv( rgb[0], rgb[1], rgb[2] )
                        color = self.Color_Display( cmodel, n_cm, n_cd, n_cp, vc, yuv )

                    # Write Pixels
                    qimage.setPixelColor( x, y, QColor( int( color[0] * 255 ), int( color[1] * 255 ), int( color[2] * 255 ) ) )

            # Save Image to File
            qpixmap = QPixmap().fromImage( qimage )
            filename = mode + "_" + geo + "_" + str( h ).zfill( 3 ) + ".png"
            location = os.path.join( temporary, filename )
            qpixmap.save( location )

        if start_from == 0:
            # Create Zip File
            basename = os.path.join( directory, zipname )
            shutil.make_archive( basename, "zip", temporary )

            # Delete all Render Files
            shutil.rmtree( temporary )
    # Script Examples
    def Pigmento_Sample_Script( self ):
        # Import Pigment.O reference object
        """
        import krita

        pyid = "pykrita_pigment_o_picker_docker"
        dockers = Krita.instance().dockers()
        for i in range( 0, len( dockers ) ):
            if dockers[i].objectName() == pyid:
                pigment_o = dockers[i]
                break
        """

        # Print Maps
        """
        space = [ "HSV", "HSL", "HCY" ]
        geo = [ "3", "4", "R" ]
        directory = "C:\\Users\\EyeOd\\Desktop\\pigmento\\Directory" # path to finished zip folder
        render = "C:\\Users\\EyeOd\\Desktop\\pigmento\\Render" # path to temporary render folder
        for g in range( 0, len( geo ) ):
            for s in range( 0, len( space ) ):
                pigment_o.API_Printer( space[s], geo[g], directory, render, None, None )
        """

        # Apply Color
        """
        pigment_o.API_Input_FG( "RGB", 0.25, 0.50, 0.75, 0 )
        """
    def Krita_Sample_Script( self ):
        # Read Color
        """
        from krita import *

        color_fg = Krita.instance().activeWindow().activeView().foregroundColor()
        order_fg = color_fg.componentsOrdered()
        r = order_fg[0]
        g = order_fg[1]
        b = order_fg[2]

        print( "red " + str( r ) )
        print( "green " + str( g ) )
        print( "blue " + str( b ) )
        """

        # Write Color
        """
        from krita import *

        n_cm = Krita.instance().activeDocument().colorModel()
        n_cd = Krita.instance().activeDocument().colorDepth()
        n_cp = Krita.instance().activeDocument().colorProfile()

        managed_color = ManagedColor( n_cm, n_cd, n_cp )
        comp = managed_color.components()
        red   = 0.4
        green = 0.5
        blue  = 0.6
        alpha = 1
        comp = [blue, green, red, alpha]
        managed_color.setComponents( comp )
        Krita.instance().activeWindow().activeView().setForeGroundColor( managed_color )
        """

    #endregion
    #region Pigmento & Krita

    # Krita
    def Krita_to_Pigmento( self ):
        # Variables
        doc = self.Current_Document()
        cmodel = doc["cmodel"]
        n_cd = doc["n_cd"]
        n_cp = doc["n_cp"]
        # Current Document
        if self.doc["cmodel"] != cmodel:
            self.Panel_inSpace( cmodel )
        # Canvas
        if ( self.canvas() is not None ) and ( self.canvas().view() is not None ):
            # Read Color
            check = self.mode_index == 0 and ( self.widget_press == False or self.doc != doc )
            # check = self.mode_index == 0 and self.widget_press == False
            if check == True:
                self.Read_Color()
            elif self.mode_index == 2:
                self.Read_Only()
            # Fill Check ( case active node changes )
            if self.Fill_Check( doc ) == False:
                self.Fill_None()
        else:
            self.Fill_None()
        # Variables for next Cycle
        if self.doc != doc:
            self.doc = doc
            self.convert.Set_Document( cmodel, n_cd, n_cp )
    def Pigmento_to_Krita( self, release ):
        if ( self.canvas() is not None ) and ( self.canvas().view() is not None ) :
            if self.mode_index in ( 0 , 1 ) and release == True:
                # Check Eraser Mode ON or OFF
                eraser = Krita.instance().action( "erase_action" )
                # Current Document
                doc = self.Current_Document()
                n_cm = doc["n_cm"]
                n_cd = doc["n_cd"]
                n_cp = doc["n_cp"]
                vc = doc["vc"]
                cmodel = doc["cmodel"]

                # Managed Color
                if self.ui_harmony == True:
                    if self.harmony_index == 1:
                        self.Color_Managed( cmodel, n_cm, n_cd, n_cp, vc, "FG", har_01 )
                    if self.harmony_index == 2:
                        self.Color_Managed( cmodel, n_cm, n_cd, n_cp, vc, "FG", har_02 )
                    if self.harmony_index == 3:
                        self.Color_Managed( cmodel, n_cm, n_cd, n_cp, vc, "FG", har_03 )
                    if self.harmony_index == 4:
                        self.Color_Managed( cmodel, n_cm, n_cd, n_cp, vc, "FG", har_04 )
                    if self.harmony_index == 5:
                        self.Color_Managed( cmodel, n_cm, n_cd, n_cp, vc, "FG", har_05 )
                else:
                    self.Color_Managed( cmodel, n_cm, n_cd, n_cp, vc, "FG", kac )
                    self.Color_Managed( cmodel, n_cm, n_cd, n_cp, vc, "BG", kbc )

                # Save
                Krita.instance().writeSetting( DOCKER_NAME, "kac", str( kac ) )
                Krita.instance().writeSetting( DOCKER_NAME, "kbc", str( kbc ) )

                # If Eraser was true, set it ON again
                if eraser.isChecked():
                    eraser.trigger()

                # Fill with Foreground Color
                if self.Fill_Check( doc ) == True:
                    Krita.instance().action( "fill_selection_foreground_color_opacity" ).trigger()
                else:
                    self.Fill_None()
    def Pigmento_Update( self ):
        if ( ( self.canvas() is not None ) and ( self.canvas().view() is not None ) ):
            self.Read_Color()

    #endregion
    #region Pigmento Paths

    def Pigmento_READ( self, mode, var_1, var_2, var_3, var_4, color ):
        self.Color_Convert( mode, var_1, var_2, var_3, var_4, color )
        self.Sync_Elements( False, True, True )
    def Pigmento_APPLY( self, mode, var_1, var_2, var_3, var_4, color ):
        self.Color_Convert( mode, var_1, var_2, var_3, var_4, color )
        self.Sync_Elements( True, True, True )
    def Pigmento_PRESS( self, mode, var_1, var_2, var_3, var_4, color ):
        self.widget_press = True
        self.Color_Convert( mode, var_1, var_2, var_3, var_4, color )
        self.Sync_Elements( not self.performance_release, True, False )
    def Pigmento_RELEASE( self ):
        self.widget_press = False
        self.Sync_Elements( True, True, True )

    #endregion
    #region Color

    # Function
    def Color_Harmony( self, span, hue_1, hue_2, hue_3, hue_4, hue_5 ):
        # Variables
        comp = 0.5
        angle_1 = 0
        angle_2 = 0
        angle_3 = 0
        angle_4 = 0
        angle_5 = 0

        # Wheel
        if self.wheel_mode == "DIGITAL":index = "hue_d"
        if self.wheel_mode == "ANALOG" :index = "hue_a"

        # Director Angle
        if self.harmony_index == 1:angulus = hue_1[ index ]
        if self.harmony_index == 2:angulus = hue_2[ index ]
        if self.harmony_index == 3:angulus = hue_3[ index ]
        if self.harmony_index == 4:angulus = hue_4[ index ]
        if self.harmony_index == 5:angulus = hue_5[ index ]

        # Rules
        if self.harmony_rule == "Monochromatic":
            if self.harmony_index in ( 1, 2, 3, 4, 5 ):
                angle_1 = angulus
                angle_2 = angulus
                angle_3 = angulus
                angle_4 = angulus
                angle_5 = angulus
        if self.harmony_rule == "Complementary":
            if self.harmony_index in ( 1, 2, 3 ):
                angle_1 = angulus
                angle_2 = angulus
                angle_3 = angulus
                angle_4 = self.geometry.Limit_Looper( angulus + comp , 1 )
                angle_5 = self.geometry.Limit_Looper( angulus + comp , 1 )
            if self.harmony_index in ( 4, 5 ):
                angle_1 = self.geometry.Limit_Looper( angulus - comp , 1 )
                angle_2 = self.geometry.Limit_Looper( angulus - comp , 1 )
                angle_3 = self.geometry.Limit_Looper( angulus - comp , 1 )
                angle_4 = angulus
                angle_5 = angulus
        if self.harmony_rule == "Analogous":
            if self.harmony_index == 1:
                angle_1 = angulus
                angle_2 = self.geometry.Limit_Looper( angulus + span * 0.25 , 1 )
                angle_3 = self.geometry.Limit_Looper( angulus + span * 0.50 , 1 )
                angle_4 = self.geometry.Limit_Looper( angulus + span * 0.75 , 1 )
                angle_5 = self.geometry.Limit_Looper( angulus + span * 1.00 , 1 )
            if self.harmony_index == 2:
                angle_1 = self.geometry.Limit_Looper( angulus - span * 0.25 , 1 )
                angle_2 = angulus
                angle_3 = self.geometry.Limit_Looper( angulus + span * 0.25 , 1 )
                angle_4 = self.geometry.Limit_Looper( angulus + span * 0.50 , 1 )
                angle_5 = self.geometry.Limit_Looper( angulus + span * 0.75 , 1 )
            if self.harmony_index == 3:
                angle_1 = self.geometry.Limit_Looper( angulus - span * 0.50 , 1 )
                angle_2 = self.geometry.Limit_Looper( angulus - span * 0.25 , 1 )
                angle_3 = angulus
                angle_4 = self.geometry.Limit_Looper( angulus + span * 0.25 , 1 )
                angle_5 = self.geometry.Limit_Looper( angulus + span * 0.50 , 1 )
            if self.harmony_index == 4:
                angle_1 = self.geometry.Limit_Looper( angulus - span * 0.75 , 1 )
                angle_2 = self.geometry.Limit_Looper( angulus - span * 0.50 , 1 )
                angle_3 = self.geometry.Limit_Looper( angulus - span * 0.25 , 1 )
                angle_4 = angulus
                angle_5 = self.geometry.Limit_Looper( angulus + span * 0.25 , 1 )
            if self.harmony_index == 5:
                angle_1 = self.geometry.Limit_Looper( angulus - span * 1.00 , 1 )
                angle_2 = self.geometry.Limit_Looper( angulus - span * 0.75 , 1 )
                angle_3 = self.geometry.Limit_Looper( angulus - span * 0.50 , 1 )
                angle_4 = self.geometry.Limit_Looper( angulus - span * 0.25 , 1 )
                angle_5 = angulus
        if self.harmony_rule == "Triadic":
            if self.harmony_index == 1:
                angle_1 = angulus
                angle_2 = self.geometry.Limit_Looper( angulus + comp - span * 0.50 , 1 )
                angle_3 = self.geometry.Limit_Looper( angulus + comp + span * 0.50 , 1 )
            if self.harmony_index == 2:
                angle_1 = self.geometry.Limit_Looper( angulus + comp + span * 0.50 , 1 )
                angle_2 = angulus
                angle_3 = self.geometry.Limit_Looper( angulus + span * 1.00        , 1 )
            if self.harmony_index == 3:
                angle_1 = self.geometry.Limit_Looper( angulus + comp - span * 0.50 , 1 )
                angle_2 = self.geometry.Limit_Looper( angulus - span * 1.00        , 1 )
                angle_3 = angulus
            angle_4 = 0
            angle_5 = 0
        if self.harmony_rule == "Tetradic":
            if self.harmony_index == 1:
                angle_1 = angulus
                angle_2 = self.geometry.Limit_Looper( angulus + span        , 1 )
                angle_3 = self.geometry.Limit_Looper( angulus + comp        , 1 )
                angle_4 = self.geometry.Limit_Looper( angulus + comp + span , 1 )
            if self.harmony_index == 2:
                angle_1 = self.geometry.Limit_Looper( angulus - span        , 1 )
                angle_2 = angulus
                angle_3 = self.geometry.Limit_Looper( angulus + comp - span , 1 )
                angle_4 = self.geometry.Limit_Looper( angulus + comp        , 1 )
            if self.harmony_index == 3:
                angle_1 = self.geometry.Limit_Looper( angulus + comp        , 1 )
                angle_2 = self.geometry.Limit_Looper( angulus + comp + span , 1 )
                angle_3 = angulus
                angle_4 = self.geometry.Limit_Looper( angulus + span        , 1 )
            if self.harmony_index == 4:
                angle_1 = self.geometry.Limit_Looper( angulus + comp - span , 1 )
                angle_2 = self.geometry.Limit_Looper( angulus + comp        , 1 )
                angle_3 = self.geometry.Limit_Looper( angulus - span        , 1 )
                angle_4 = angulus
            angle_5 = 0

        if self.wheel_mode == "ANALOG":
            angle_1 = self.convert.huea_to_hued( angle_1 )
            angle_2 = self.convert.huea_to_hued( angle_2 )
            angle_3 = self.convert.huea_to_hued( angle_3 )
            angle_4 = self.convert.huea_to_hued( angle_4 )
            angle_5 = self.convert.huea_to_hued( angle_5 )

        # Wheel Mode
        mode = self.wheel_space
        if self.panel_index == "Hexagon":
            mode = "ARD"
        if self.panel_index == "Luma":
            mode = "YUV"
        # Channels
        c1, c2, c3 = self.Hue_Index( mode )

        if self.panel_index == "Luma":
            luma = self.cor[c1]
            # Angulus no Edit
            if self.harmony_edit == False:
                y1, u1, v1 = self.convert.uv_to_hue( self.cor[c1], self.cor[c2], self.cor[c3], angle_1 )
                y2, u2, v2 = self.convert.uv_to_hue( self.cor[c1], self.cor[c2], self.cor[c3], angle_2 )
                y3, u3, v3 = self.convert.uv_to_hue( self.cor[c1], self.cor[c2], self.cor[c3], angle_3 )
                y4, u4, v4 = self.convert.uv_to_hue( self.cor[c1], self.cor[c2], self.cor[c3], angle_4 )
                y5, u5, v5 = self.convert.uv_to_hue( self.cor[c1], self.cor[c2], self.cor[c3], angle_5 )
            # Angulus with Edit
            if self.harmony_edit == True:
                y1, u1, v1 = self.convert.uv_to_hue( har_01[c1], har_01[c2], har_01[c3], angle_1 )
                y2, u2, v2 = self.convert.uv_to_hue( har_02[c1], har_02[c2], har_02[c3], angle_2 )
                y3, u3, v3 = self.convert.uv_to_hue( har_03[c1], har_03[c2], har_03[c3], angle_3 )
                y4, u4, v4 = self.convert.uv_to_hue( har_04[c1], har_04[c2], har_04[c3], angle_4 )
                y5, u5, v5 = self.convert.uv_to_hue( har_05[c1], har_05[c2], har_05[c3], angle_5 )
            # Others
            if self.harmony_index != 1:self.Color_Convert( mode, luma, u1, v1, 0, har_01 )
            if self.harmony_index != 2:self.Color_Convert( mode, luma, u2, v2, 0, har_02 )
            if self.harmony_index != 3:self.Color_Convert( mode, luma, u3, v3, 0, har_03 )
            if self.harmony_index != 4:self.Color_Convert( mode, luma, u4, v4, 0, har_04 )
            if self.harmony_index != 5:self.Color_Convert( mode, luma, u5, v5, 0, har_05 )
            # Active
            if self.harmony_index == 1:self.Color_Convert( mode, luma, u1, v1, 0, har_01 )
            if self.harmony_index == 2:self.Color_Convert( mode, luma, u2, v2, 0, har_02 )
            if self.harmony_index == 3:self.Color_Convert( mode, luma, u3, v3, 0, har_03 )
            if self.harmony_index == 4:self.Color_Convert( mode, luma, u4, v4, 0, har_04 )
            if self.harmony_index == 5:self.Color_Convert( mode, luma, u5, v5, 0, har_05 )
        else:
            # Angulus no Edit
            if self.harmony_edit == False:
                # Others
                if self.harmony_index != 1:self.Color_Convert( mode, angle_1, self.cor[c2], self.cor[c3], 0, har_01 )
                if self.harmony_index != 2:self.Color_Convert( mode, angle_2, self.cor[c2], self.cor[c3], 0, har_02 )
                if self.harmony_index != 3:self.Color_Convert( mode, angle_3, self.cor[c2], self.cor[c3], 0, har_03 )
                if self.harmony_index != 4:self.Color_Convert( mode, angle_4, self.cor[c2], self.cor[c3], 0, har_04 )
                if self.harmony_index != 5:self.Color_Convert( mode, angle_5, self.cor[c2], self.cor[c3], 0, har_05 )
                # Active
                if self.harmony_index == 1:self.Color_Convert( mode, angle_1, self.cor[c2], self.cor[c3], 0, har_01 )
                if self.harmony_index == 2:self.Color_Convert( mode, angle_2, self.cor[c2], self.cor[c3], 0, har_02 )
                if self.harmony_index == 3:self.Color_Convert( mode, angle_3, self.cor[c2], self.cor[c3], 0, har_03 )
                if self.harmony_index == 4:self.Color_Convert( mode, angle_4, self.cor[c2], self.cor[c3], 0, har_04 )
                if self.harmony_index == 5:self.Color_Convert( mode, angle_5, self.cor[c2], self.cor[c3], 0, har_05 )
            # Angulus with Edit
            if self.harmony_edit == True:
                # Others
                if self.harmony_index != 1:self.Color_Convert( mode, angle_1, har_01[c2], har_01[c3], 0, har_01 )
                if self.harmony_index != 2:self.Color_Convert( mode, angle_2, har_02[c2], har_02[c3], 0, har_02 )
                if self.harmony_index != 3:self.Color_Convert( mode, angle_3, har_03[c2], har_03[c3], 0, har_03 )
                if self.harmony_index != 4:self.Color_Convert( mode, angle_4, har_04[c2], har_04[c3], 0, har_04 )
                if self.harmony_index != 5:self.Color_Convert( mode, angle_5, har_05[c2], har_05[c3], 0, har_05 )
                # Active
                if self.harmony_index == 1:self.Color_Convert( mode, angle_1, har_01[c2], har_01[c3], 0, har_01 )
                if self.harmony_index == 2:self.Color_Convert( mode, angle_2, har_02[c2], har_02[c3], 0, har_02 )
                if self.harmony_index == 3:self.Color_Convert( mode, angle_3, har_03[c2], har_03[c3], 0, har_03 )
                if self.harmony_index == 4:self.Color_Convert( mode, angle_4, har_04[c2], har_04[c3], 0, har_04 )
                if self.harmony_index == 5:self.Color_Convert( mode, angle_5, har_05[c2], har_05[c3], 0, har_05 )

        # Active ( cleanup )
        har_01[ "active" ] = True
        har_02[ "active" ] = True
        har_03[ "active" ] = True
        har_04[ "active" ] = True
        har_05[ "active" ] = True

        # Save
        Krita.instance().writeSetting( DOCKER_NAME, "har_01", str( har_01 ) )
        Krita.instance().writeSetting( DOCKER_NAME, "har_02", str( har_02 ) )
        Krita.instance().writeSetting( DOCKER_NAME, "har_03", str( har_03 ) )
        Krita.instance().writeSetting( DOCKER_NAME, "har_04", str( har_04 ) )
        Krita.instance().writeSetting( DOCKER_NAME, "har_05", str( har_05 ) )
    def Color_Convert( self, mode, var_1, var_2, var_3, var_4, color ):
        # cmyk calculation uses self.lock_cmyk_4
        # hue calculation uses self.wheel_mode

        #region Adjustments

        if mode == "KKK":
            color[ "kkk_percent" ] = var_1
            color[ "kkk_scale" ] = var_2
            self.Kelvin_Class( var_2 )

        #endregion
        #region Convert to RGB+XYZ

        if mode == "A":
            aaa = [ var_1 ]
            rgb = [ aaa[0], aaa[0], aaa[0] ]
            xyz = self.convert.rgb_to_xyz( rgb[0], rgb[1], rgb[2] )
            hue_d = 0
        if mode == "RGB":
            rgb = [ var_1, var_2, var_3 ]
            xyz = self.convert.rgb_to_xyz( rgb[0], rgb[1], rgb[2] )
            hue_d = self.convert.rgb_to_hue( var_1, var_2, var_3 )
        if mode == "UVD":
            uvd = [ var_1, var_2, var_3 ]
            rgb = self.convert.uvd_to_rgb( uvd[0], uvd[1], uvd[2] )
            xyz = self.convert.rgb_to_xyz( rgb[0], rgb[1], rgb[2] )
            hue_d = self.convert.rgb_to_hue( rgb[0], rgb[1], rgb[2] )
        if mode == "CMY":
            cmy = [ var_1, var_2, var_3 ]
            rgb = self.convert.cmy_to_rgb( cmy[0], cmy[1], cmy[2] )
            xyz = self.convert.rgb_to_xyz( rgb[0], rgb[1], rgb[2] )
            hue_d = self.convert.rgb_to_hue( rgb[0], rgb[1], rgb[2] )
        if mode == "CMYK":
            cmyk = [ var_1, var_2, var_3, var_4 ]
            rgb = self.convert.cmyk_to_rgb( cmyk[0], cmyk[1], cmyk[2], cmyk[3] )
            xyz = self.convert.rgb_to_xyz( rgb[0], rgb[1], rgb[2] )
            hue_d = self.convert.rgb_to_hue( rgb[0], rgb[1], rgb[2] )
        if mode == "RYB":
            ryb = [ var_1, var_2, var_3 ]
            rgb = self.convert.ryb_to_rgb( ryb[0], ryb[1], ryb[2] )
            xyz = self.convert.rgb_to_xyz( rgb[0], rgb[1], rgb[2] )
            hue_d = self.convert.rgb_to_hue( rgb[0], rgb[1], rgb[2] )
        if mode == "YUV":
            yuv = [ var_1, var_2, var_3 ]
            rgb = self.convert.yuv_to_rgb( yuv[0], yuv[1], yuv[2] )
            xyz = self.convert.rgb_to_xyz( rgb[0], rgb[1], rgb[2] )
            hue_d = self.convert.rgb_to_hue( rgb[0], rgb[1], rgb[2] )

        if mode == "HSV":
            hue_d = var_1
            hsv = [ var_1, var_2, var_3 ]
            rgb = self.convert.hsv_to_rgb( hsv[0], hsv[1], hsv[2] )
            xyz = self.convert.rgb_to_xyz( rgb[0], rgb[1], rgb[2] )
        if mode == "HSL":
            hue_d = var_1
            hsl = [ var_1, var_2, var_3 ]
            rgb = self.convert.hsl_to_rgb( hsl[0], hsl[1], hsl[2] )
            xyz = self.convert.rgb_to_xyz( rgb[0], rgb[1], rgb[2] )
        if mode == "HCY":
            hue_d = var_1
            hcy = [ var_1, var_2, var_3 ]
            rgb = self.convert.hcy_to_rgb( hcy[0], hcy[1], hcy[2] )
            xyz = self.convert.rgb_to_xyz( rgb[0], rgb[1], rgb[2] )
        if mode == "ARD":
            hue_d = var_1
            ard = [ var_1, var_2, var_3 ]
            rgb = self.convert.ard_to_rgb( ard[0], ard[1], ard[2] )
            xyz = self.convert.rgb_to_xyz( rgb[0], rgb[1], rgb[2] )

        if mode == "XYZ":
            xyz = [ var_1, var_2, var_3 ]
            rgb = self.convert.xyz_to_rgb( xyz[0], xyz[1], xyz[2] )
            hue_d = self.convert.rgb_to_hue( rgb[0], rgb[1], rgb[2] )
        if mode == "XYY":
            xyy = [ var_1, var_2, var_3 ]
            xyz = self.convert.xyy_to_xyz( xyy[0], xyy[1], xyy[2] )
            rgb = self.convert.xyz_to_rgb( xyz[0], xyz[1], xyz[2] )
            hue_d = self.convert.rgb_to_hue( rgb[0], rgb[1], rgb[2] )
        if mode == "LAB":
            lab = [ var_1, var_2, var_3 ]
            xyz = self.convert.lab_to_xyz( lab[0], lab[1], lab[2] )
            rgb = self.convert.xyz_to_rgb( xyz[0], xyz[1], xyz[2] )
            hue_d = self.convert.rgb_to_hue( rgb[0], rgb[1], rgb[2] )

        if mode == "LCH":
            lch = [ var_1, var_2, var_3 ]
            lab = self.convert.lch_to_lab( lch[0], lch[1], lch[2] )
            xyz = self.convert.lab_to_xyz( lab[0], lab[1], lab[2] )
            rgb = self.convert.xyz_to_rgb( xyz[0], xyz[1], xyz[2] )
            hue_d = self.convert.rgb_to_hue( rgb[0], rgb[1], rgb[2] )

        if mode == "KKK":
            kkk = self.convert.kkk_to_rgb( color["kkk_scale"], kelvin_rgb )
            rgb = ( color["rgb_1"], color["rgb_2"], color["rgb_3"] )
            xyz = self.convert.rgb_to_xyz( rgb[0], rgb[1], rgb[2] )
            hue_d = self.convert.rgb_to_hue( rgb[0], rgb[1], rgb[2] )

        if mode == "HEX":
            rgb = self.convert.hex6_to_rgb( var_1 )
            xyz = self.convert.rgb_to_xyz( rgb[0], rgb[1], rgb[2] )
            hue_d = self.convert.rgb_to_hue( rgb[0], rgb[1], rgb[2] )

        #endregion
        #region Convert RGB+XYZ into Other

        # HUE
        self.convert.Set_Hue( hue_d )
        hue_a = self.convert.hued_to_huea( hue_d )

        if mode != "A":
            aaa = self.convert.rgb_to_aaa( rgb[0], rgb[1], rgb[2] )
        if mode != "RGB":
            pass
        if mode != "UVD":
            uvd = self.convert.rgb_to_uvd( rgb[0], rgb[1], rgb[2] )
        if mode != "CMY":
            cmy = self.convert.rgb_to_cmy( rgb[0], rgb[1], rgb[2] )
        if mode != "CMYK":
            key = lambda k: None if k==False else color["cmyk_4"]
            cmyk = self.convert.rgb_to_cmyk( rgb[0], rgb[1], rgb[2], key( self.lock_cmyk_4 ) )
        if mode != "RYB":
            ryb = self.convert.rgb_to_ryb( rgb[0], rgb[1], rgb[2] )
        if mode != "YUV":
            yuv = self.convert.rgb_to_yuv( rgb[0], rgb[1], rgb[2] )

        if mode != "HSV":
            hsv = self.convert.rgb_to_hsv( rgb[0], rgb[1], rgb[2] )
        if mode != "HSL":
            hsl = self.convert.rgb_to_hsl( rgb[0], rgb[1], rgb[2] )
        if mode != "HCY":
            hcy = self.convert.rgb_to_hcy( rgb[0], rgb[1], rgb[2] )
        if mode != "ARD":
            ard = self.convert.rgb_to_ard( rgb[0], rgb[1], rgb[2] )

        if mode != "XYZ":
            pass
        if mode != "XYY":
            xyy = self.convert.xyz_to_xyy( xyz[0], xyz[1], xyz[2] )
        if mode != "LAB":
            lab = self.convert.xyz_to_lab( xyz[0], xyz[1], xyz[2] )

        if mode != "LCH":
            lch = self.convert.lab_to_lch( lab[0], lab[1], lab[2] )

        if mode != "KKK":
            kkk = self.convert.kkk_to_rgb( color["kkk_scale"], kelvin_rgb )

        #endregion
        #region Variables

        # HEX
        hex_code = self.convert.rgb_to_hex6( rgb[0], rgb[1], rgb[2] )
        name = self.convert.hex6_to_name( hex_code, color_names )
        color[ "hex6" ] = hex_code
        color[ "name" ] = name
        # RGB Depth Error Correction
        checkdepth = uvd[2] - self.depth_previous
        if ( checkdepth >= -( 1 / krange[ "uvd_3" ] ) and checkdepth <= ( 1 / krange[ "uvd_3" ] ) ):
            uvd[2] = self.depth_previous
            ard[2] = self.depth_previous

        # AAA
        color[ "aaa_1" ] = aaa[0]
        # RGB
        color[ "rgb_1" ] = rgb[0]
        color[ "rgb_2" ] = rgb[1]
        color[ "rgb_3" ] = rgb[2]
        # UVD
        color[ "uvd_1" ] = uvd[0]
        color[ "uvd_2" ] = uvd[1]
        color[ "uvd_3" ] = uvd[2]
        # CMY
        color[ "cmy_1" ] = cmy[0]
        color[ "cmy_2" ] = cmy[1]
        color[ "cmy_3" ] = cmy[2]
        # CMYK
        color[ "cmyk_1" ] = cmyk[0]
        color[ "cmyk_2" ] = cmyk[1]
        color[ "cmyk_3" ] = cmyk[2]
        color[ "cmyk_4" ] = cmyk[3]
        # RYB
        color[ "ryb_1" ] = ryb[0]
        color[ "ryb_2" ] = ryb[1]
        color[ "ryb_3" ] = ryb[2]
        # YUV
        color[ "yuv_1" ] = yuv[0]
        color[ "yuv_2" ] = yuv[1]
        color[ "yuv_3" ] = yuv[2]

        # HUE
        color[ "hue_d" ] = hue_d
        color[ "hue_a" ] = hue_a
        # HSV
        color[ "hsv_1" ] = hue_d
        color[ "hsv_2" ] = hsv[1]
        color[ "hsv_3" ] = hsv[2]
        # HSL
        color[ "hsl_1" ] = hue_d
        color[ "hsl_2" ] = hsl[1]
        color[ "hsl_3" ] = hsl[2]
        # HCY
        color[ "hcy_1" ] = hue_d
        color[ "hcy_2" ] = hcy[1]
        color[ "hcy_3" ] = hcy[2]
        # ARD
        color[ "ard_1" ] = hue_d
        color[ "ard_2" ] = ard[1]
        color[ "ard_3" ] = ard[2]

        # XYZ
        color[ "xyz_1" ] = xyz[0]
        color[ "xyz_2" ] = xyz[1]
        color[ "xyz_3" ] = xyz[2]
        # XYY
        color[ "xyy_1" ] = xyy[0]
        color[ "xyy_2" ] = xyy[1]
        color[ "xyy_3" ] = xyy[2]
        # LAB
        color[ "lab_1" ] = lab[0]
        color[ "lab_2" ] = lab[1]
        color[ "lab_3" ] = lab[2]

        # LCH
        color[ "lch_1" ] = lch[0]
        color[ "lch_2" ] = lch[1]
        color[ "lch_3" ] = lch[2]

        # Display
        display = [ rgb[0], rgb[1], rgb[2] ]

        #endregion
        #region Finish

        # Kelvin Multiplication
        kr = rgb[0] * kkk[0]
        kg = rgb[1] * kkk[1]
        kb = rgb[2] * kkk[2]
        display = [ kr, kg, kb ]

        # Display
        doc = self.Current_Document()
        cmodel = doc[ "cmodel" ]
        disp_rgb = self.Color_Display( cmodel, doc[ "n_cm" ], doc[ "n_cd" ], doc[ "n_cp" ], doc[ "vc" ], display )
        # A
        kaaa = self.convert.rgb_to_aaa( kr, kg, kb )
        color[ "aaa_d1" ] = kaaa[0]
        # RGB
        color[ "rgb_d1" ] = disp_rgb[0]
        color[ "rgb_d2" ] = disp_rgb[1]
        color[ "rgb_d3" ] = disp_rgb[2]
        # CMYK
        if cmodel == "CMYK":
            if self.lock_cmyk_4 == True:    key = self.convert.rgb_to_k( kr, kg, kb )
            else:                           key = None
            kcmyk = self.convert.rgb_to_cmyk( kr, kg, kb, key )
            color[ "cmyk_d1" ] = kcmyk[0]
            color[ "cmyk_d2" ] = kcmyk[1]
            color[ "cmyk_d3" ] = kcmyk[2]
            color[ "cmyk_d4" ] = kcmyk[3]
        # YUV
        elif cmodel == "YUV":
            kyuv = self.convert.rgb_to_yuv( kr, kg, kb )
            color[ "yuv_d1" ] = kyuv[0]
            color[ "yuv_d2" ] = kyuv[1]
            color[ "yuv_d3" ] = kyuv[2]
        # XYZ
        elif cmodel == "XYZ":
            kxyz = self.convert.rgb_to_xyz( kr, kg, kb )
            color[ "xyz_d1" ] = kxyz[0]
            color[ "xyz_d2" ] = kxyz[1]
            color[ "xyz_d3" ] = kxyz[2]
        # LAB
        elif cmodel == "LAB":
            klab = self.convert.rgb_to_lab( kr, kg, kb )
            color[ "lab_d1" ] = klab[0]
            color[ "lab_d2" ] = klab[1]
            color[ "lab_d3" ] = klab[2]
        # HEX
        color[ "hex6_d" ] = self.convert.rgb_to_hex6( disp_rgb[0], disp_rgb[1], disp_rgb[2] )

        #endregion

        # Return
        return color
    def Color_HEX( self, hex_code ):
        try:
            # Variables
            check_null = ( hex_code == None or hex_code == "" )
            check_hex6 = self.HEX_Valid( hex_code, 6 )
            check_hex3 = self.HEX_Valid( hex_code, 3 )
            space = list( filter( None, re.findall( r"(GRAY|CMYK|AAA|RGB|CMY|RYB|YUV|HSV|HSL|HCY|XYZ|XYY|LAB|LCH)+", hex_code.upper() ) ) )
            if len( space ) > 0:
                color_space = space[0].upper()
            else:
                color_space = None
            values = list( filter( None, re.findall( r"[0-9\.0-9]*", hex_code) ) )
            vector = len( values )

            # Logic
            if check_null == True: # Null == Black (r=0, g=0, b=0)
                self.Color_Convert( "RGB", 0, 0, 0, 0, self.cor )
                self.Sync_Elements( True, True, True )
            elif ( check_hex6 == True or check_hex3 == True ): # HEX format
                if hex_code.startswith( "#" ) == False: # correct nomenclature
                    hex_code = "#" + hex_code
                if ( check_hex6 == True and len( hex_code ) == 7 ): #123456
                    rgb = self.convert.hex6_to_rgb( hex_code )
                    self.Color_Convert( "RGB", rgb[0], rgb[1], rgb[2], 0, self.cor )
                    self.Sync_Elements( True, True, True )
                if ( check_hex3 == True and len( hex_code ) == 4 ): #123
                    rgb = self.convert.hex3_to_rgb( hex_code )
                    self.Color_Convert( "RGB", rgb[0], rgb[1], rgb[2], 0, self.cor )
                    self.Sync_Elements( True, True, True )
            elif ( color_space in [ "A", "GRAY" ] and vector == 1 ): # GRAY(100)
                self.Color_Convert( color_space, int( values[0] ) / 255, 0, 0, 0, self.cor )
                self.Sync_Elements( True, True, True )
            elif ( color_space in [ "RGB", "CMY", "RYB", "YUV", "XYZ", "XYY", "LAB", "LCH" ] and vector == 3 ): # RGB(100, 100, 100)
                self.Color_Convert( color_space, int( values[0] ) / 255, int( values[1] ) / 255, int( values[2] ) / 255, 0, self.cor )
                self.Sync_Elements( True, True, True )
            elif ( color_space in [ "CMYK" ] and vector == 4 ): # CMYK(100, 100, 100, 100)
                self.Color_Convert( color_space, int( values[0] ) / 255, int( values[1] ) / 255, int( values[2] ) / 255, int( values[3] ) / 255, self.cor )
                self.Sync_Elements( True, True, True )
            elif ( color_space in [ "HSV", "HSL","HCY" ] and vector == 3 ): #HSV(100, 100, 100)
                self.Color_Convert( color_space, int( values[0] ) / 360, int( values[1] ) / 100, int( values[2] ) / 100, 0, self.cor )
                self.Sync_Elements( True, True, True )
            else:# Red Green Blue
                # Variables
                name = hex_code.lower()
                item = list( color_names.items() )
                # Search Dictionary with color names
                for i in range( 0, len( item ) ):
                    key_i = item[i][0]
                    value_i = item[i][1]
                    for j in range( 0, len( value_i ) ):
                        value_ij = value_i[j].lower()
                        if value_ij == name:
                            self.Color_Convert( "HEX", key_i, 0, 0, 0, self.cor )
                            self.Sync_Elements( True, True, True )
                            break
        except:
            Message_Log( self, "ERROR", "input value" )

    # Read
    def Read_Color( self ):
        try:
            # Variables
            ki = Krita.instance()
            # Document
            doc = self.Current_Document()
            cmodel = doc["cmodel"]
            n_cd = doc["n_cd"]
            n_cp = doc["n_cp"]
            d = doc["depth"]

            # Check Eraser Mode ON or OFF
            eraser = ki.action( "erase_action" )
            # Current Krita Active Colors
            active_view = ki.activeWindow().activeView()
            color_fg = active_view.foregroundColor()
            color_bg = active_view.backgroundColor()
            order_fg = color_fg.componentsOrdered()
            order_bg = color_bg.componentsOrdered()

            # Depth
            self.depth_previous = self.cor["uvd_3"]

            # Harmony
            if self.ui_harmony == True:
                if self.harmony_index == 1:
                    ka = har_01
                if self.harmony_index == 2:
                    ka = har_02
                if self.harmony_index == 3:
                    ka = har_03
                if self.harmony_index == 4:
                    ka = har_04
                if self.harmony_index == 5:
                    ka = har_05
            else:
                ka = kac
                kb = kbc

            # Read if Colors Differs
            if doc["vi"] == None: # Pixel Read
                if cmodel == "A":
                    # Foreground and Background Colors ( Krita is in AAA )
                    a1 = order_fg[0]
                    b1 = order_bg[0]
                    m1 = self.pole_mix["aaa_d1"]

                    # Range
                    if n_cd in [ "U8", "U16" ]:
                        ca1 = ( a1 < ( ( int( ka["aaa_d1"] * d ) ) / d ) ) or ( a1 >= ( ( int( ka["aaa_d1"] * d ) + 1 ) / d ) )
                        cb1 = ( b1 < ( ( int( kb["aaa_d1"] * d ) ) / d ) ) or ( b1 >= ( ( int( kb["aaa_d1"] * d ) + 1 ) / d ) )
                    if n_cd in [ "F16", "F32" ]:
                        ca1 = a1 != a["aaa_d1"]
                        cb1 = b1 != b["aaa_d1"]

                    # Operation
                    if ca1 == True:
                        if not eraser.isChecked():
                            self.Pigmento_READ( "A", a1, 0, 0, 0, ka )
                        if a1 != m1:
                            self.Pole_Neutral()
                    if cb1 == True:
                        if not eraser.isChecked():
                            self.Pigmento_READ( "A", b1, 0, 0, 0, kb )
                elif cmodel in [ "RGB", None ]:
                    # Foreground and Background Colors ( Krita is in RGB )
                    a1 = order_fg[0] # Red
                    a2 = order_fg[1] # Green
                    a3 = order_fg[2] # Blue
                    b1 = order_bg[0]
                    b2 = order_bg[1]
                    b3 = order_bg[2]
                    m1 = self.pole_mix["rgb_d1"]
                    m2 = self.pole_mix["rgb_d2"]
                    m3 = self.pole_mix["rgb_d3"]

                    # Range
                    if n_cd in [ "U8", "U16" ]:
                        ca1 = ( a1 < ( ( int( ka["rgb_d1"] * d ) ) / d ) ) or ( a1 >= ( ( int( ka["rgb_d1"] * d ) + 1 ) / d ) )
                        ca2 = ( a2 < ( ( int( ka["rgb_d2"] * d ) ) / d ) ) or ( a2 >= ( ( int( ka["rgb_d2"] * d ) + 1 ) / d ) )
                        ca3 = ( a3 < ( ( int( ka["rgb_d3"] * d ) ) / d ) ) or ( a3 >= ( ( int( ka["rgb_d3"] * d ) + 1 ) / d ) )
                        cb1 = ( b1 < ( ( int( kb["rgb_d1"] * d ) ) / d ) ) or ( b1 >= ( ( int( kb["rgb_d1"] * d ) + 1 ) / d ) )
                        cb2 = ( b2 < ( ( int( kb["rgb_d2"] * d ) ) / d ) ) or ( b2 >= ( ( int( kb["rgb_d2"] * d ) + 1 ) / d ) )
                        cb3 = ( b3 < ( ( int( kb["rgb_d3"] * d ) ) / d ) ) or ( b3 >= ( ( int( kb["rgb_d3"] * d ) + 1 ) / d ) )
                    if n_cd in [ "F16", "F32" ]:
                        ca1 = a1 != ka["rgb_d1"]
                        ca2 = a2 != ka["rgb_d2"]
                        ca3 = a3 != ka["rgb_d3"]
                        cb1 = b1 != kb["rgb_d1"]
                        cb2 = b2 != kb["rgb_d2"]
                        cb3 = b3 != kb["rgb_d3"]

                    # Operation
                    if ca1 == True or ca2 == True or ca3 == True:
                        if not eraser.isChecked():
                            self.Pigmento_READ( "RGB", a1, a2, a3, 0, ka )
                        if a1 != m1 or a2 != m2 or a3 != m3:
                            self.Pole_Neutral()
                    if cb1 == True or cb2 == True or cb3 == True:
                        if not eraser.isChecked():
                            self.Pigmento_READ( "RGB", b1, b2, b3, 0, kb )
                elif cmodel == "CMYK":
                    # Foreground and Background Colors ( Krita is in CMYK )
                    a1 = order_fg[0]
                    a2 = order_fg[1]
                    a3 = order_fg[2]
                    a4 = order_fg[3]
                    b1 = order_bg[0]
                    b2 = order_bg[1]
                    b3 = order_bg[2]
                    b4 = order_bg[3]
                    m1 = self.pole_mix["cmyk_d1"]
                    m2 = self.pole_mix["cmyk_d2"]
                    m3 = self.pole_mix["cmyk_d3"]
                    m4 = self.pole_mix["cmyk_d4"]

                    # Range
                    if n_cd in [ "U8", "U16" ]:
                        ca1 = ( a1 < ( ( int( ka["cmyk_d1"] * d ) ) / d ) ) or ( a1 >= ( ( int( ka["cmyk_d1"] * d ) + 1 ) / d ) )
                        ca2 = ( a2 < ( ( int( ka["cmyk_d2"] * d ) ) / d ) ) or ( a2 >= ( ( int( ka["cmyk_d2"] * d ) + 1 ) / d ) )
                        ca3 = ( a3 < ( ( int( ka["cmyk_d3"] * d ) ) / d ) ) or ( a3 >= ( ( int( ka["cmyk_d3"] * d ) + 1 ) / d ) )
                        ca4 = ( a4 < ( ( int( ka["cmyk_d4"] * d ) ) / d ) ) or ( a4 >= ( ( int( ka["cmyk_d4"] * d ) + 1 ) / d ) )
                        cb1 = ( b1 < ( ( int( kb["cmyk_d1"] * d ) ) / d ) ) or ( b1 >= ( ( int( kb["cmyk_d1"] * d ) + 1 ) / d ) )
                        cb2 = ( b2 < ( ( int( kb["cmyk_d2"] * d ) ) / d ) ) or ( b2 >= ( ( int( kb["cmyk_d2"] * d ) + 1 ) / d ) )
                        cb3 = ( b3 < ( ( int( kb["cmyk_d3"] * d ) ) / d ) ) or ( b3 >= ( ( int( kb["cmyk_d3"] * d ) + 1 ) / d ) )
                        cb4 = ( b4 < ( ( int( kb["cmyk_d4"] * d ) ) / d ) ) or ( b4 >= ( ( int( kb["cmyk_d4"] * d ) + 1 ) / d ) )
                    if n_cd in [ "F16", "F32" ]:
                        ca1 = a1 != ka["cmyk_d1"]
                        ca2 = a2 != ka["cmyk_d2"]
                        ca3 = a3 != ka["cmyk_d3"]
                        ca4 = a4 != ka["cmyk_d4"]
                        cb1 = b1 != kb["cmyk_d1"]
                        cb2 = b2 != kb["cmyk_d2"]
                        cb3 = b3 != kb["cmyk_d3"]
                        cb4 = b4 != kb["cmyk_d4"]

                    # Operation
                    if ca1 == True or ca2 == True or ca3 == True or ca4 == True:
                        if not eraser.isChecked():
                            self.Pigmento_READ( "CMYK", a1, a2, a3, a4, a )
                        if a1 != m1 or a2 != m2 or a3 != m3 or a4 != m4:
                            self.Pole_Neutral()
                    if cb1 == True or cb2 == True or cb3 == True or cb4 == True:
                        if not eraser.isChecked():
                            self.Pigmento_READ( "CMYK", b1, b2, b3, b4, b )
                elif cmodel == "YUV":
                    # Foreground and Background Colors ( Krita is in YUV )
                    a1 = order_fg[0]
                    a2 = order_fg[1]
                    a3 = order_fg[2]
                    b1 = order_bg[0]
                    b2 = order_bg[1]
                    b3 = order_bg[2]
                    m1 = self.pole_mix["yuv_d1"]
                    m2 = self.pole_mix["yuv_d2"]
                    m3 = self.pole_mix["yuv_d3"]

                    # Range
                    if n_cd in [ "U8", "U16" ]:
                        ca1 = ( a1 < ( ( int( a["yuv_d1"] * kd ) ) / d ) ) or ( a1 >= ( ( int( ka["yuv_d1"] * d ) + 1 ) / d ) )
                        ca2 = ( a2 < ( ( int( a["yuv_d2"] * kd ) ) / d ) ) or ( a2 >= ( ( int( ka["yuv_d2"] * d ) + 1 ) / d ) )
                        ca3 = ( a3 < ( ( int( a["yuv_d3"] * kd ) ) / d ) ) or ( a3 >= ( ( int( ka["yuv_d3"] * d ) + 1 ) / d ) )
                        cb1 = ( b1 < ( ( int( b["yuv_d1"] * kd ) ) / d ) ) or ( b1 >= ( ( int( kb["yuv_d1"] * d ) + 1 ) / d ) )
                        cb2 = ( b2 < ( ( int( b["yuv_d2"] * kd ) ) / d ) ) or ( b2 >= ( ( int( kb["yuv_d2"] * d ) + 1 ) / d ) )
                        cb3 = ( b3 < ( ( int( b["yuv_d3"] * kd ) ) / d ) ) or ( b3 >= ( ( int( kb["yuv_d3"] * d ) + 1 ) / d ) )
                    if n_cd in [ "F16", "F32" ]:
                        ca1 = a1 != ka["yuv_d1"]
                        ca2 = a2 != ka["yuv_d2"]
                        ca3 = a3 != ka["yuv_d3"]
                        cb1 = b1 != kb["yuv_d1"]
                        cb2 = b2 != kb["yuv_d2"]
                        cb3 = b3 != kb["yuv_d3"]

                    # Operation
                    if ca1 == True or ca2 == True or ca3 == True:
                        if not eraser.isChecked():
                            self.Pigmento_READ( "YUV", a1, a2, a3, 0, ka )
                        if a1 != m1 or a2 != m2 or a3 != m3:
                            self.Pole_Neutral()
                    if cb1 == True or cb2 == True or cb3 == True:
                        if not eraser.isChecked():
                            self.Pigmento_READ( "YUV", b1, b2, b3, 0, kb )
                elif cmodel == "XYZ":
                    # Foreground and Background Colors ( Krita is in XYZ )
                    a1 = order_fg[0]
                    a2 = order_fg[1]
                    a3 = order_fg[2]
                    b1 = order_bg[0]
                    b2 = order_bg[1]
                    b3 = order_bg[2]
                    m1 = self.pole_mix["xyz_d1"]
                    m2 = self.pole_mix["xyz_d2"]
                    m3 = self.pole_mix["xyz_d3"]

                    # Range
                    if n_cd in [ "U8", "U16" ]:
                        ca1 = ( a1 < ( ( int( ka["xyz_d1"] * d ) ) / d ) ) or ( a1 >= ( ( int( ka["xyz_d1"] * d ) + 1 ) / d ) )
                        ca2 = ( a2 < ( ( int( ka["xyz_d2"] * d ) ) / d ) ) or ( a2 >= ( ( int( ka["xyz_d2"] * d ) + 1 ) / d ) )
                        ca3 = ( a3 < ( ( int( ka["xyz_d3"] * d ) ) / d ) ) or ( a3 >= ( ( int( ka["xyz_d3"] * d ) + 1 ) / d ) )
                        cb1 = ( b1 < ( ( int( kb["xyz_d1"] * d ) ) / d ) ) or ( b1 >= ( ( int( kb["xyz_d1"] * d ) + 1 ) / d ) )
                        cb2 = ( b2 < ( ( int( kb["xyz_d2"] * d ) ) / d ) ) or ( b2 >= ( ( int( kb["xyz_d2"] * d ) + 1 ) / d ) )
                        cb3 = ( b3 < ( ( int( kb["xyz_d3"] * d ) ) / d ) ) or ( b3 >= ( ( int( kb["xyz_d3"] * d ) + 1 ) / d ) )
                    if n_cd in [ "F16", "F32" ]:
                        ca1 = a1 != ka["xyz_d1"]
                        ca2 = a2 != ka["xyz_d2"]
                        ca3 = a3 != ka["xyz_d3"]
                        cb1 = b1 != kb["xyz_d1"]
                        cb2 = b2 != kb["xyz_d2"]
                        cb3 = b3 != kb["xyz_d3"]

                    # Operation
                    if ca1 == True or ca2 == True or ca3 == True:
                        if not eraser.isChecked():
                            self.Pigmento_READ( "XYZ", a1, a2, a3, 0, ka )
                        if a1 != m1 or a2 != m2 or a3 != m3:
                            self.Pole_Neutral()
                    if cb1 == True or cb2 == True or cb3 == True:
                        if not eraser.isChecked():
                            self.Pigmento_READ( "XYZ", b1, b2, b3, 0, kb )
                elif cmodel == "LAB":
                    # Foreground and Background Colors ( Krita is in LAB )
                    a1 = order_fg[0]
                    a2 = order_fg[1]
                    a3 = order_fg[2]
                    b1 = order_bg[0]
                    b2 = order_bg[1]
                    b3 = order_bg[2]
                    m1 = self.pole_mix["lab_d1"]
                    m2 = self.pole_mix["lab_d2"]
                    m3 = self.pole_mix["lab_d3"]

                    # Range
                    if n_cd in [ "U8", "U16" ]:
                        ca1 = ( a1 < ( ( int( ka["lab_d1"] * d ) ) / d ) ) or ( a1 >= ( ( int( ka["lab_d1"] * d ) + 1 ) / d ) )
                        ca2 = ( a2 < ( ( int( ka["lab_d2"] * d ) ) / d ) ) or ( a2 >= ( ( int( ka["lab_d2"] * d ) + 1 ) / d ) )
                        ca3 = ( a3 < ( ( int( ka["lab_d3"] * d ) ) / d ) ) or ( a3 >= ( ( int( ka["lab_d3"] * d ) + 1 ) / d ) )
                        cb1 = ( b1 < ( ( int( kb["lab_d1"] * d ) ) / d ) ) or ( b1 >= ( ( int( kb["lab_d1"] * d ) + 1 ) / d ) )
                        cb2 = ( b2 < ( ( int( kb["lab_d2"] * d ) ) / d ) ) or ( b2 >= ( ( int( kb["lab_d2"] * d ) + 1 ) / d ) )
                        cb3 = ( b3 < ( ( int( kb["lab_d3"] * d ) ) / d ) ) or ( b3 >= ( ( int( kb["lab_d3"] * d ) + 1 ) / d ) )
                    if n_cd in [ "F16", "F32" ]:
                        ca1 = a1 != ka["lab_d1"]
                        ca2 = a2 != ka["lab_d2"]
                        ca3 = a3 != ka["lab_d3"]
                        cb1 = b1 != kb["lab_d1"]
                        cb2 = b2 != kb["lab_d2"]
                        cb3 = b3 != kb["lab_d3"]

                    # Operation
                    if ca1 == True or ca2 == True or ca3 == True:
                        if not eraser.isChecked():
                            self.Pigmento_READ( "LAB", a1, a2, a3, 0, ka )
                        if a1 != m1 or a2 != m2 or a3 != m3:
                            self.Pole_Neutral()
                    if cb1 == True or cb2 == True or cb3 == True:
                        if not eraser.isChecked():
                            self.Pigmento_READ( "LAB", b1, b2, b3, 0, kb )
            else: # Vector Read
                # Variables
                v = 255

                # Foreground Color
                fgc_canvas = doc["fgc"].colorForCanvas( doc["vc"] )
                a1 = fgc_canvas.red() / v
                a2 = fgc_canvas.green() / v
                a3 = fgc_canvas.blue() / v
                # Background Color
                bgc_canvas = doc["bgc"].colorForCanvas( doc["vc"] )
                b1 = bgc_canvas.red() / v
                b2 = bgc_canvas.green() / v
                b3 = bgc_canvas.blue() / v
                # Pole
                m1 = self.pole_mix["rgb_d1"]
                m2 = self.pole_mix["rgb_d2"]
                m3 = self.pole_mix["rgb_d3"]

                # Range
                ca1 = ( a1 < ( ( int( ka["rgb_d1"] * v ) ) / v ) ) or ( a1 >= ( ( int( ka["rgb_d1"] * v ) + 1 ) / v ) )
                ca2 = ( a2 < ( ( int( ka["rgb_d2"] * v ) ) / v ) ) or ( a2 >= ( ( int( ka["rgb_d2"] * v ) + 1 ) / v ) )
                ca3 = ( a3 < ( ( int( ka["rgb_d3"] * v ) ) / v ) ) or ( a3 >= ( ( int( ka["rgb_d3"] * v ) + 1 ) / v ) )
                cb1 = ( b1 < ( ( int( kb["rgb_d1"] * v ) ) / v ) ) or ( b1 >= ( ( int( kb["rgb_d1"] * v ) + 1 ) / v ) )
                cb2 = ( b2 < ( ( int( kb["rgb_d2"] * v ) ) / v ) ) or ( b2 >= ( ( int( kb["rgb_d2"] * v ) + 1 ) / v ) )
                cb3 = ( b3 < ( ( int( kb["rgb_d3"] * v ) ) / v ) ) or ( b3 >= ( ( int( kb["rgb_d3"] * v ) + 1 ) / v ) )

                # Operation
                if ca1 == True or ca2 == True or ca3 == True:
                    self.Pigmento_READ( "RGB", a1, a2, a3, 0, ka )
                    if a1 != m1 or a2 != m2 or a3 != m3:
                        self.Pole_Neutral()
                if cb1 == True or cb2 == True or cb3 == True:
                    self.Pigmento_READ( "RGB", b1, b2, b3, 0, kb )
        except:
            pass
    def Read_Only( self ):
        # Variables
        c1 = krange["rgb_1"]
        c2 = krange["rgb_2"]
        c3 = krange["rgb_3"]

        # Foreground Color
        color_fg = Krita.instance().activeWindow().activeView().foregroundColor()
        order_fg = color_fg.componentsOrdered()
        fg_1 = order_fg[0] * c1
        fg_2 = order_fg[1] * c2
        fg_3 = order_fg[2] * c3

        # Foreground Color
        color_bg = Krita.instance().activeWindow().activeView().backgroundColor()
        order_bg = color_bg.componentsOrdered()
        bg_1 = order_bg[0] * c1
        bg_2 = order_bg[1] * c2
        bg_3 = order_bg[2] * c3

        # Print Debug
        try:
            QtCore.qDebug( f"KRITA COLOR ( with range )" )
            QtCore.qDebug( f"" )
            QtCore.qDebug( f"fg_1 = { fg_1 }" )
            QtCore.qDebug( f"fg_2 = { fg_2 }" )
            QtCore.qDebug( f"fg_3 = { fg_3 }" )
            QtCore.qDebug( f"" )
            QtCore.qDebug( f"bg_1 = { bg_1 }" )
            QtCore.qDebug( f"bg_2 = { bg_2 }" )
            QtCore.qDebug( f"bg_3 = { bg_3 }" )
            QtCore.qDebug( f"" )
        except:
            pass

    # Write
    def Color_Display( self, cmodel, n_cm, n_cd, n_cp, vc, color ):
        if ( self.performance_inaccurate == False and ( self.canvas() is not None ) and ( self.canvas().view() is not None ) ):
            mc = ManagedColor( n_cm, n_cd, n_cp )
            if cmodel == "A":
                mc.setComponents( [ color[0], 1.0 ] )
            elif cmodel in ["RGB", None ]:
                if n_cd in [ "U8", "U16" ]:
                    mc.setComponents( [ color[2], color[1], color[0], 1.0 ] )
                if n_cd in [ "F16", "F32" ]:
                    mc.setComponents( [ color[0], color[1], color[2], 1.0 ] )
            elif cmodel == "CMYK":
                mc.setComponents( [ color[0], color[1], color[2], color[3], 1.0 ] )
            elif cmodel == "YUV":
                mc.setComponents( [ color[0], color[1], color[2], 1.0 ] )
            elif cmodel == "XYZ":
                mc.setComponents( [ color[0], color[1], color[2], 1.0 ] )
            elif cmodel == "LAB":
                mc.setComponents( [ color[0], color[1], color[2], 1.0 ] )
            qcolor = mc.colorForCanvas( vc )
            r = qcolor.redF()
            g = qcolor.greenF()
            b = qcolor.blueF()
        else:
            r = color[0]
            g = color[1]
            b = color[2]
        # Return
        return [r, g, b]
    def Color_Managed( self, cmodel, n_cm, n_cd, n_cp, vc, side, color ):
        # Managed Colors
        managed_color = ManagedColor( n_cm, n_cd, n_cp )
        comp = managed_color.components()
        if cmodel == "A":
            kac_1 = color["aaa_d1"]
            comp = [kac_1, 1]
        elif cmodel in [ "RGB", None ]:
            kac_1 = color["rgb_d1"]
            kac_2 = color["rgb_d2"]
            kac_3 = color["rgb_d3"]
            if n_cd in [ "U8", "U16" ]:
                comp = [kac_3, kac_2, kac_1, 1]
            if n_cd in [ "F16", "F32" ]:
                comp = [kac_1, kac_2, kac_3, 1]
        elif cmodel == "CMYK":
            kac_1 = color["cmyk_d1"]
            kac_2 = color["cmyk_d2"]
            kac_3 = color["cmyk_d3"]
            kac_4 = color["cmyk_d4"]
            comp = [kac_1, kac_2, kac_3, kac_4, 1]
        elif cmodel == "YUV":
            kac_1 = color["yuv_d1"]
            kac_2 = color["yuv_d2"]
            kac_3 = color["yuv_d3"]
            comp = [kac_1, kac_2, kac_3, 1]
        elif cmodel == "XYZ":
            kac_1 = color["xyz_d1"]
            kac_2 = color["xyz_d2"]
            kac_3 = color["xyz_d3"]
            comp = [kac_1, kac_2, kac_3, 1]
        elif cmodel == "LAB":
            kac_1 = color["lab_d1"]
            kac_2 = color["lab_d2"]
            kac_3 = color["lab_d3"]
            comp = [kac_1, kac_2, kac_3, 1]
        managed_color.setComponents( comp )
        # Color for Canvas
        if self.performance_inaccurate == False:
            display = managed_color.colorForCanvas( vc )
            r = display.redF()
            g = display.greenF()
            b = display.blueF()
        else:
            r = color["rgb_1"]
            g = color["rgb_2"]
            b = color["rgb_3"]
        color["hex6_d"] = self.convert.rgb_to_hex6( r, g, b )
        # Operation
        if side == "FG":    Krita.instance().activeWindow().activeView().setForeGroundColor( managed_color )
        if side == "BG":    Krita.instance().activeWindow().activeView().setBackGroundColor( managed_color )

    # Elements
    def Color_Swap( self ):
        keys = list( kac.keys() )
        for k in keys:
            aa = kac[k]
            bb = kbc[k]
            kac[k] = bb
            kbc[k] = aa
    def Color_Random( self ):
        r = random.randrange( 0,255,1 ) / 255
        g = random.randrange( 0,255,1 ) / 255
        b = random.randrange( 0,255,1 ) / 255
        self.Pigmento_APPLY( "RGB", r, g, b, 0, self.cor )
    def Color_Complementary( self ):
        # Wheel Influence
        if self.wheel_mode == "DIGITAL":
            hue = self.geometry.Limit_Looper( self.cor["hue_d"] + 0.5, 1 )
        if self.wheel_mode == "ANALOG":
            hue = self.convert.huea_to_hued( self.geometry.Limit_Looper( self.cor["hue_a"] + 0.5, 1 ) )

        # Color Space Influence
        if self.wheel_space == "HSV":
            self.Pigmento_APPLY( "HSV", hue, self.cor["hsv_2"], self.cor["hsv_3"], 0, self.cor )
        if self.wheel_space == "HSL":
            self.Pigmento_APPLY( "HSL", hue, self.cor["hsl_2"], self.cor["hsl_3"], 0, self.cor )
        if self.wheel_space == "HCY":
            self.Pigmento_APPLY( "HCY", hue, self.cor["hcy_2"], self.cor["hcy_3"], 0, self.cor )
        if self.wheel_space == "ARD":
            self.Pigmento_APPLY( "ARD", hue, self.cor["ard_2"], self.cor["ard_3"], 0, self.cor )
    def Color_Interpolate( self, mode, color_a, color_b, factor ):
        # Parse
        color_a = self.convert.color_vector( mode, color_a )
        color_b = self.convert.color_vector( mode, color_b )
        # Interpolation
        channels = len( color_a )
        lerp = self.convert.color_lerp( mode, channels, color_a, color_b, factor )
        # Conversion
        color = color_true.copy()
        if mode == "A":
            color = self.Color_Convert( mode, lerp[0], 0, 0, 0, color )
        elif ( mode == "CMYK" or mode == "CMYK" ):
            color = self.Color_Convert( mode, lerp[0], lerp[1], lerp[2], lerp[3], color )
        else:
            color = self.Color_Convert( mode, lerp[0], lerp[1], lerp[2], 0, color )
        # Return
        return color
    def Color_Vector( self, mode, cor ):
        # RGB Linear
        if mode == "A":         vector = [ cor["aaa_1"], ]
        elif mode == "RGB":     vector = [ cor["rgb_1"],  cor["rgb_2"],  cor["rgb_3"] ]
        elif mode == "CMY":     vector = [ cor["cmy_1"],  cor["cmy_2"],  cor["cmy_3"] ]
        elif mode == "CMYK":    vector = [ cor["cmyk_1"], cor["cmyk_2"], cor["cmyk_3"], cor["cmyk_4"] ]
        elif mode == "RYB":     vector = [ cor["ryb_1"],  cor["ryb_2"],  cor["ryb_3"] ]
        elif mode == "YUV":     vector = [ cor["yuv_1"],  cor["yuv_2"],  cor["yuv_3"] ]
        # RGB Hue
        elif mode == "HSV":     vector = [ cor["hsv_1"],  cor["hsv_2"],  cor["hsv_3"] ]
        elif mode == "HSL":     vector = [ cor["hsl_1"],  cor["hsl_2"],  cor["hsl_3"] ]
        elif mode == "HCY":     vector = [ cor["hcy_1"],  cor["hcy_2"],  cor["hcy_3"] ]
        elif mode == "ARD":     vector = [ cor["ard_1"],  cor["ard_2"],  cor["ard_3"] ]
        # XYZ Linear
        elif mode == "XYZ":     vector = [ cor["xyz_1"],  cor["xyz_2"],  cor["xyz_3"] ]
        elif mode == "XYY":     vector = [ cor["xyy_1"],  cor["xyy_2"],  cor["xyy_3"] ]
        elif mode == "LAB":     vector = [ cor["lab_1"],  cor["lab_2"],  cor["lab_3"] ]
        # XYZ Hue
        elif mode == "LCH":     vector = [ cor["lch_1"],  cor["lch_2"],  cor["lch_3"] ]
        # Return
        return vector

    #endregion
    #region Syncronization

    def Sync_Elements( self, p2k, color_active, color_previous ):
        # Signals
        self.Block_Channels( True )
        # Layout
        self.Pigmento_to_Krita( p2k )
        self.Harmony_Header( har_01, har_02, har_03, har_04, har_05 )
        self.Update_Header( color_active, color_previous )
        self.Panels_Set_Value()
        self.Update_Values()
        self.Channel_Set_Style()
        self.Mixer_Set_Style()
        self.Pin_Active()
        self.History_List( self.cor["rgb_d1"], self.cor["rgb_d2"], self.cor["rgb_d3"] )
        # Signals
        self.Block_Channels( False )
        # Dialog
        self.Reference_Name()
        # Save
        Krita.instance().writeSetting( DOCKER_NAME, "kac", str( kac ) )
        Krita.instance().writeSetting( DOCKER_NAME, "kbc", str( kbc ) )

    def Block_Channels( self, boolean ):
        # AAA
        self.layout.aaa_1_slider.blockSignals( boolean )
        self.layout.aaa_1_value.blockSignals( boolean )
        # RGB
        self.layout.rgb_1_slider.blockSignals( boolean )
        self.layout.rgb_2_slider.blockSignals( boolean )
        self.layout.rgb_3_slider.blockSignals( boolean )
        self.layout.rgb_1_value.blockSignals( boolean )
        self.layout.rgb_2_value.blockSignals( boolean )
        self.layout.rgb_3_value.blockSignals( boolean )
        # CMY
        self.layout.cmy_1_slider.blockSignals( boolean )
        self.layout.cmy_2_slider.blockSignals( boolean )
        self.layout.cmy_3_slider.blockSignals( boolean )
        self.layout.cmy_1_value.blockSignals( boolean )
        self.layout.cmy_2_value.blockSignals( boolean )
        self.layout.cmy_3_value.blockSignals( boolean )
        # CMYK
        self.layout.cmyk_1_slider.blockSignals( boolean )
        self.layout.cmyk_2_slider.blockSignals( boolean )
        self.layout.cmyk_3_slider.blockSignals( boolean )
        self.layout.cmyk_4_slider.blockSignals( boolean )
        self.layout.cmyk_1_value.blockSignals( boolean )
        self.layout.cmyk_2_value.blockSignals( boolean )
        self.layout.cmyk_3_value.blockSignals( boolean )
        self.layout.cmyk_4_value.blockSignals( boolean )
        # RYB
        self.layout.ryb_1_slider.blockSignals( boolean )
        self.layout.ryb_2_slider.blockSignals( boolean )
        self.layout.ryb_3_slider.blockSignals( boolean )
        self.layout.ryb_1_value.blockSignals( boolean )
        self.layout.ryb_2_value.blockSignals( boolean )
        self.layout.ryb_3_value.blockSignals( boolean )
        # YUV
        self.layout.yuv_1_slider.blockSignals( boolean )
        self.layout.yuv_2_slider.blockSignals( boolean )
        self.layout.yuv_3_slider.blockSignals( boolean )
        self.layout.yuv_1_value.blockSignals( boolean )
        self.layout.yuv_2_value.blockSignals( boolean )
        self.layout.yuv_3_value.blockSignals( boolean )

        # HSV
        self.layout.hsv_1_slider.blockSignals( boolean )
        self.layout.hsv_2_slider.blockSignals( boolean )
        self.layout.hsv_3_slider.blockSignals( boolean )
        self.layout.hsv_1_value.blockSignals( boolean )
        self.layout.hsv_2_value.blockSignals( boolean )
        self.layout.hsv_3_value.blockSignals( boolean )
        # HSL
        self.layout.hsl_1_slider.blockSignals( boolean )
        self.layout.hsl_2_slider.blockSignals( boolean )
        self.layout.hsl_3_slider.blockSignals( boolean )
        self.layout.hsl_1_value.blockSignals( boolean )
        self.layout.hsl_2_value.blockSignals( boolean )
        self.layout.hsl_3_value.blockSignals( boolean )
        # HCY
        self.layout.hcy_1_slider.blockSignals( boolean )
        self.layout.hcy_2_slider.blockSignals( boolean )
        self.layout.hcy_3_slider.blockSignals( boolean )
        self.layout.hcy_1_value.blockSignals( boolean )
        self.layout.hcy_2_value.blockSignals( boolean )
        self.layout.hcy_3_value.blockSignals( boolean )
        # ARD
        self.layout.ard_1_slider.blockSignals( boolean )
        self.layout.ard_2_slider.blockSignals( boolean )
        self.layout.ard_3_slider.blockSignals( boolean )
        self.layout.ard_1_value.blockSignals( boolean )
        self.layout.ard_2_value.blockSignals( boolean )
        self.layout.ard_3_value.blockSignals( boolean )

        # XYZ
        self.layout.xyz_1_slider.blockSignals( boolean )
        self.layout.xyz_2_slider.blockSignals( boolean )
        self.layout.xyz_3_slider.blockSignals( boolean )
        self.layout.xyz_1_value.blockSignals( boolean )
        self.layout.xyz_2_value.blockSignals( boolean )
        self.layout.xyz_3_value.blockSignals( boolean )
        # XYY
        self.layout.xyy_1_slider.blockSignals( boolean )
        self.layout.xyy_2_slider.blockSignals( boolean )
        self.layout.xyy_3_slider.blockSignals( boolean )
        self.layout.xyy_1_value.blockSignals( boolean )
        self.layout.xyy_2_value.blockSignals( boolean )
        self.layout.xyy_3_value.blockSignals( boolean )
        # LAB
        self.layout.lab_1_slider.blockSignals( boolean )
        self.layout.lab_2_slider.blockSignals( boolean )
        self.layout.lab_3_slider.blockSignals( boolean )
        self.layout.lab_1_value.blockSignals( boolean )
        self.layout.lab_2_value.blockSignals( boolean )
        self.layout.lab_3_value.blockSignals( boolean )

        # LCH
        self.layout.lch_1_slider.blockSignals( boolean )
        self.layout.lch_2_slider.blockSignals( boolean )
        self.layout.lch_3_slider.blockSignals( boolean )
        self.layout.lch_1_value.blockSignals( boolean )
        self.layout.lch_2_value.blockSignals( boolean )
        self.layout.lch_3_value.blockSignals( boolean )

        # KKK
        self.layout.kkk_1_slider.blockSignals( boolean )
        self.layout.kkk_1_value.blockSignals( boolean )
    def Harmony_Header( self, har_01, har_02, har_03, har_04, har_05 ):
        # Variables
        self.Color_Harmony( self.harmony_span, har_01, har_02, har_03, har_04, har_05 )
        # Update
        self.Harmony_Update()
        self.harmony_spread.Update_Span( self.harmony_span )
    def Update_Header( self, active, previous ):
        # Left
        if self.ui_harmony == True:
            if self.harmony_index == 1:
                self.color_header.Set_Color_A1( har_01["hex6_d"] )
            if self.harmony_index == 2:
                self.color_header.Set_Color_A1( har_02["hex6_d"] )
            if self.harmony_index == 3:
                self.color_header.Set_Color_A1( har_03["hex6_d"] )
            if self.harmony_index == 4:
                self.color_header.Set_Color_A1( har_04["hex6_d"] )
            if self.harmony_index == 5:
                self.color_header.Set_Color_A1( har_05["hex6_d"] )
        else:
            if self.active_ab == True:
                if active == True:
                    self.color_header.Set_Color_A1( kac["hex6_d"] )
                if previous == True:
                    self.color_header.Set_Color_B1( kbc["hex6_d"] )
            if self.active_ab == False:
                if active == True:
                    self.color_header.Set_Color_B1( kbc["hex6_d"] )
                if previous == True:
                    self.color_header.Set_Color_A1( kac["hex6_d"] )

        # Right
        if ( active == True and previous == True ):
            if self.ui_harmony == True:
                if self.harmony_index == 1:
                    self.color_header.Set_Color_A1( har_01["hex6_d"] )
                    self.color_header.Set_Color_A2( har_01["hex6_d"] )
                if self.harmony_index == 2:
                    self.color_header.Set_Color_A1( har_02["hex6_d"] )
                    self.color_header.Set_Color_A2( har_02["hex6_d"] )
                if self.harmony_index == 3:
                    self.color_header.Set_Color_A1( har_03["hex6_d"] )
                    self.color_header.Set_Color_A2( har_03["hex6_d"] )
                if self.harmony_index == 4:
                    self.color_header.Set_Color_A1( har_04["hex6_d"] )
                    self.color_header.Set_Color_A2( har_04["hex6_d"] )
                if self.harmony_index == 5:
                    self.color_header.Set_Color_A1( har_05["hex6_d"] )
                    self.color_header.Set_Color_A2( har_05["hex6_d"] )
            else:
                self.color_header.Set_Color_A2( kac["hex6_d"] )
                self.color_header.Set_Color_B2( kbc["hex6_d"] )
            self.zoom = False
            # Label
            self.Label_String( "" )
    def Panels_Set_Value( self ):
        # Place Cursor
        if self.panel_index == panel_fill:      self.Update_Panel_Fill()
        if self.panel_index == panel_square:    self.Update_Panel_Square()
        if self.panel_index == panel_hue:       self.Update_Panel_HueCircle()
        if self.panel_index == panel_gamut:     self.Update_Panel_Gamut()
        if self.panel_index == panel_hexagon:   self.Update_Panel_Hexagon()
        if self.panel_index == panel_luma:      self.Update_Panel_Luma()
        if self.panel_index == panel_dot:       pass # only changes when the dot color changes
        if self.panel_index == panel_mask:      self.Mask_Live_Update()
    def Update_Values( self ):
        # AAA
        if self.chan_aaa == True:
            self.aaa_1_slider.Set_Value( self.cor["aaa_1"] )
            self.layout.aaa_1_value.setValue( self.cor["aaa_1"] * krange["aaa_1"] )
        # RGB
        if self.chan_rgb == True:
            self.rgb_1_slider.Set_Value( self.cor["rgb_1"] )
            self.rgb_2_slider.Set_Value( self.cor["rgb_2"] )
            self.rgb_3_slider.Set_Value( self.cor["rgb_3"] )
            self.layout.rgb_1_value.setValue( self.cor["rgb_1"] * krange["rgb_1"] )
            self.layout.rgb_2_value.setValue( self.cor["rgb_2"] * krange["rgb_2"] )
            self.layout.rgb_3_value.setValue( self.cor["rgb_3"] * krange["rgb_3"] )
        # CMY
        if self.chan_cmy == True:
            self.cmy_1_slider.Set_Value( self.cor["cmy_1"] )
            self.cmy_2_slider.Set_Value( self.cor["cmy_2"] )
            self.cmy_3_slider.Set_Value( self.cor["cmy_3"] )
            self.layout.cmy_1_value.setValue( self.cor["cmy_1"] * krange["cmy_1"] )
            self.layout.cmy_2_value.setValue( self.cor["cmy_2"] * krange["cmy_2"] )
            self.layout.cmy_3_value.setValue( self.cor["cmy_3"] * krange["cmy_3"] )
        # CMYK
        if self.chan_cmyk == True:
            self.cmyk_1_slider.Set_Value( self.cor["cmyk_1"] )
            self.cmyk_2_slider.Set_Value( self.cor["cmyk_2"] )
            self.cmyk_3_slider.Set_Value( self.cor["cmyk_3"] )
            self.cmyk_4_slider.Set_Value( self.cor["cmyk_4"] )
            self.layout.cmyk_1_value.setValue( self.cor["cmyk_1"] * krange["cmyk_1"] )
            self.layout.cmyk_2_value.setValue( self.cor["cmyk_2"] * krange["cmyk_2"] )
            self.layout.cmyk_3_value.setValue( self.cor["cmyk_3"] * krange["cmyk_3"] )
            self.layout.cmyk_4_value.setValue( self.cor["cmyk_4"] * krange["cmyk_4"] )
        # RYB
        if self.chan_ryb == True:
            self.ryb_1_slider.Set_Value( self.cor["ryb_1"] )
            self.ryb_2_slider.Set_Value( self.cor["ryb_2"] )
            self.ryb_3_slider.Set_Value( self.cor["ryb_3"] )
            self.layout.ryb_1_value.setValue( self.cor["ryb_1"] * krange["ryb_1"] )
            self.layout.ryb_2_value.setValue( self.cor["ryb_2"] * krange["ryb_2"] )
            self.layout.ryb_3_value.setValue( self.cor["ryb_3"] * krange["ryb_3"] )
        # YUV
        if self.chan_yuv == True:
            self.yuv_1_slider.Set_Value( self.cor["yuv_1"] )
            self.yuv_2_slider.Set_Value( self.cor["yuv_2"] )
            self.yuv_3_slider.Set_Value( self.cor["yuv_3"] )
            self.layout.yuv_1_value.setValue( self.cor["yuv_1"] * krange["yuv_1"] )
            self.layout.yuv_2_value.setValue( self.cor["yuv_2"] * krange["yuv_2"] )
            self.layout.yuv_3_value.setValue( self.cor["yuv_3"] * krange["yuv_3"] )

        # HSV
        if self.chan_hsv == True:
            self.hsv_1_slider.Set_Value( self.cor["hsv_1"] )
            self.hsv_2_slider.Set_Value( self.cor["hsv_2"] )
            self.hsv_3_slider.Set_Value( self.cor["hsv_3"] )
            self.layout.hsv_1_value.setValue( self.cor["hsv_1"] * krange["hsv_1"] )
            self.layout.hsv_2_value.setValue( self.cor["hsv_2"] * krange["hsv_2"] )
            self.layout.hsv_3_value.setValue( self.cor["hsv_3"] * krange["hsv_3"] )
        # HSL
        if self.chan_hsl == True:
            self.hsl_1_slider.Set_Value( self.cor["hsl_1"] )
            self.hsl_2_slider.Set_Value( self.cor["hsl_2"] )
            self.hsl_3_slider.Set_Value( self.cor["hsl_3"] )
            self.layout.hsl_1_value.setValue( self.cor["hsl_1"] * krange["hsl_1"] )
            self.layout.hsl_2_value.setValue( self.cor["hsl_2"] * krange["hsl_2"] )
            self.layout.hsl_3_value.setValue( self.cor["hsl_3"] * krange["hsl_3"] )
        # HCY
        if self.chan_hcy == True:
            self.hcy_1_slider.Set_Value( self.cor["hcy_1"] )
            self.hcy_2_slider.Set_Value( self.cor["hcy_2"] )
            self.hcy_3_slider.Set_Value( self.cor["hcy_3"] )
            self.layout.hcy_1_value.setValue( self.cor["hcy_1"] * krange["hcy_1"] )
            self.layout.hcy_2_value.setValue( self.cor["hcy_2"] * krange["hcy_2"] )
            self.layout.hcy_3_value.setValue( self.cor["hcy_3"] * krange["hcy_3"] )
        # ARD
        if self.chan_ard == True:
            self.ard_1_slider.Set_Value( self.cor["ard_1"] )
            self.ard_2_slider.Set_Value( self.cor["ard_2"] )
            self.ard_3_slider.Set_Value( self.cor["ard_3"] )
            self.layout.ard_1_value.setValue( self.cor["ard_1"] * krange["ard_1"] )
            self.layout.ard_2_value.setValue( self.cor["ard_2"] * krange["ard_2"] )
            self.layout.ard_3_value.setValue( self.cor["ard_3"] * krange["ard_3"] )

        # XYZ
        if self.chan_xyz == True:
            self.xyz_1_slider.Set_Value( self.cor["xyz_1"] )
            self.xyz_2_slider.Set_Value( self.cor["xyz_2"] )
            self.xyz_3_slider.Set_Value( self.cor["xyz_3"] )
            self.layout.xyz_1_value.setValue( self.cor["xyz_1"] * krange["xyz_1"] )
            self.layout.xyz_2_value.setValue( self.cor["xyz_2"] * krange["xyz_2"] )
            self.layout.xyz_3_value.setValue( self.cor["xyz_3"] * krange["xyz_3"] )
        # XYY
        if self.chan_xyy == True:
            self.xyy_1_slider.Set_Value( self.cor["xyy_1"] )
            self.xyy_2_slider.Set_Value( self.cor["xyy_2"] )
            self.xyy_3_slider.Set_Value( self.cor["xyy_3"] )
            self.layout.xyy_1_value.setValue( self.cor["xyy_1"] * krange["xyy_1"] )
            self.layout.xyy_2_value.setValue( self.cor["xyy_2"] * krange["xyy_2"] )
            self.layout.xyy_3_value.setValue( self.cor["xyy_3"] * krange["xyy_3"] )
        # LAB
        if self.chan_lab == True:
            self.lab_1_slider.Set_Value( self.cor["lab_1"] )
            self.lab_2_slider.Set_Value( self.cor["lab_2"] )
            self.lab_3_slider.Set_Value( self.cor["lab_3"] )
            self.layout.lab_1_value.setValue( self.cor["lab_1"] * krange["lab_1"] )
            self.layout.lab_2_value.setValue( self.cor["lab_2"] * krange["lab_2"] )
            self.layout.lab_3_value.setValue( self.cor["lab_3"] * krange["lab_3"] )

        # LCH
        if self.chan_lch == True:
            self.lch_1_slider.Set_Value( self.cor["lch_1"] )
            self.lch_2_slider.Set_Value( self.cor["lch_2"] )
            self.lch_3_slider.Set_Value( self.cor["lch_3"] )
            self.layout.lch_1_value.setValue( self.cor["lch_1"] * krange["lch_1"] )
            self.layout.lch_2_value.setValue( self.cor["lch_2"] * krange["lch_2"] )
            self.layout.lch_3_value.setValue( self.cor["lch_3"] * krange["lch_3"] )

        # KKK
        if self.chan_kkk == True:
            self.kkk_1_slider.Set_Value( self.cor["kkk_percent"] )
            self.layout.kkk_1_value.setValue( self.cor["kkk_scale"] )

        # Mixers
        if self.ui_mixer == True:
            # Pole
            self.pole_slider.Set_Value( self.pole_percent )
            # Custom
            for i in range( 0, len( self.mixer_colors ) ):
                try:self.mixer_module[i]["m"].Set_Value( self.mixer_colors[i]["m"] )
                except:pass

        # HEX
        if self.chan_hex == True:
            hex_code = self.cor["hex6_d"]
            self.layout.hex_string.setText( hex_code )
        if self.chan_sum == True:
            percentage = self.convert.cmyk_to_tic( self.cor["cmyk_1"], self.cor["cmyk_2"], self.cor["cmyk_3"], self.cor["cmyk_4"] )
            sum_text = "Σ" + str( percentage ).zfill(3)
            self.layout.sum_string.setText( sum_text )

    def Channel_Set_Style( self ):
        # Variables
        linear = 8 # 4 stops
        circular = 12 # 6 stops
        # RGB Linear
        if self.chan_aaa == True:
            aaa_1 = self.Gradient_Style( "A", False, linear, [0], [1] )
            self.aaa_1_slider.Set_Colors( aaa_1, 1 )
        if self.chan_rgb == True:
            rgb_1 = self.Gradient_Style( "RGB", False, linear, [0, self.cor["rgb_2"], self.cor["rgb_3"]], [1, self.cor["rgb_2"], self.cor["rgb_3"]] )
            rgb_2 = self.Gradient_Style( "RGB", False, linear, [self.cor["rgb_1"], 0, self.cor["rgb_3"]], [self.cor["rgb_1"], 1, self.cor["rgb_3"]] )
            rgb_3 = self.Gradient_Style( "RGB", False, linear, [self.cor["rgb_1"], self.cor["rgb_2"], 0], [self.cor["rgb_1"], self.cor["rgb_2"], 1] )
            self.rgb_1_slider.Set_Colors( rgb_1, 1 )
            self.rgb_2_slider.Set_Colors( rgb_2, 1 )
            self.rgb_3_slider.Set_Colors( rgb_3, 1 )
        if self.chan_cmy == True:
            cmy_1 = self.Gradient_Style( "CMY", False, linear, [0, self.cor["cmy_2"], self.cor["cmy_3"]], [1, self.cor["cmy_2"], self.cor["cmy_3"]] )
            cmy_2 = self.Gradient_Style( "CMY", False, linear, [self.cor["cmy_1"], 0, self.cor["cmy_3"]], [self.cor["cmy_1"], 1, self.cor["cmy_3"]] )
            cmy_3 = self.Gradient_Style( "CMY", False, linear, [self.cor["cmy_1"], self.cor["cmy_2"], 0], [self.cor["cmy_1"], self.cor["cmy_2"], 1] )
            self.cmy_1_slider.Set_Colors( cmy_1, 1 )
            self.cmy_2_slider.Set_Colors( cmy_2, 1 )
            self.cmy_3_slider.Set_Colors( cmy_3, 1 )
        if self.chan_cmyk == True:
            cmyk_1 = self.Gradient_Style( "CMYK", False, linear, [0, self.cor["cmyk_2"], self.cor["cmyk_3"], self.cor["cmyk_4"]], [1, self.cor["cmyk_2"], self.cor["cmyk_3"], self.cor["cmyk_4"]] )
            cmyk_2 = self.Gradient_Style( "CMYK", False, linear, [self.cor["cmyk_1"], 0, self.cor["cmyk_3"], self.cor["cmyk_4"]], [self.cor["cmyk_1"], 1, self.cor["cmyk_3"], self.cor["cmyk_4"]] )
            cmyk_3 = self.Gradient_Style( "CMYK", False, linear, [self.cor["cmyk_1"], self.cor["cmyk_2"], 0, self.cor["cmyk_4"]], [self.cor["cmyk_1"], self.cor["cmyk_2"], 1, self.cor["cmyk_4"]] )
            cmyk_4 = self.Gradient_Style( "CMYK", False, linear, [self.cor["cmyk_1"], self.cor["cmyk_2"], self.cor["cmyk_3"], 0], [self.cor["cmyk_1"], self.cor["cmyk_2"], self.cor["cmyk_3"], 1] )
            self.cmyk_1_slider.Set_Colors( cmyk_1, 1 )
            self.cmyk_2_slider.Set_Colors( cmyk_2, 1 )
            self.cmyk_3_slider.Set_Colors( cmyk_3, 1 )
            self.cmyk_4_slider.Set_Colors( cmyk_4, 1 )
        if self.chan_ryb == True:
            ryb_1 = self.Gradient_Style( "RYB", False, linear, [0, self.cor["ryb_2"], self.cor["ryb_3"]], [1, self.cor["ryb_2"], self.cor["ryb_3"]] )
            ryb_2 = self.Gradient_Style( "RYB", False, linear, [self.cor["ryb_1"], 0, self.cor["ryb_3"]], [self.cor["ryb_1"], 1, self.cor["ryb_3"]] )
            ryb_3 = self.Gradient_Style( "RYB", False, linear, [self.cor["ryb_1"], self.cor["ryb_2"], 0], [self.cor["ryb_1"], self.cor["ryb_2"], 1] )
            self.ryb_1_slider.Set_Colors( ryb_1, 1 )
            self.ryb_2_slider.Set_Colors( ryb_2, 1 )
            self.ryb_3_slider.Set_Colors( ryb_3, 1 )
        if self.chan_yuv == True:
            yuv_1 = self.Gradient_Style( "YUV", False, linear, [0, self.cor["yuv_2"], self.cor["yuv_3"]], [1, self.cor["yuv_2"], self.cor["yuv_3"]] )
            yuv_2 = self.Gradient_Style( "YUV", False, linear, [self.cor["yuv_1"], 0, self.cor["yuv_3"]], [self.cor["yuv_1"], 1, self.cor["yuv_3"]] )
            yuv_3 = self.Gradient_Style( "YUV", False, linear, [self.cor["yuv_1"], self.cor["yuv_2"], 0], [self.cor["yuv_1"], self.cor["yuv_2"], 1] )
            self.yuv_1_slider.Set_Colors( yuv_1, 1 )
            self.yuv_2_slider.Set_Colors( yuv_2, 1 )
            self.yuv_3_slider.Set_Colors( yuv_3, 1 )
        # RGB Hue
        if self.chan_hsv == True:
            if self.hue_shine == True:
                hsv_1 = self.Gradient_Style( "HSV", False, circular, [0, 1, 1], [1, 1, 1] )
            else:
                hsv_1 = self.Gradient_Style( "HSV", False, circular, [0, self.cor["hsv_2"], self.cor["hsv_3"]], [1, self.cor["hsv_2"], self.cor["hsv_3"]] )
            hsv_2 = self.Gradient_Style( "HSV", False, linear, [self.cor["hsv_1"], 0, self.cor["hsv_3"]], [self.cor["hsv_1"], 1, self.cor["hsv_3"]] )
            hsv_3 = self.Gradient_Style( "HSV", False, linear, [self.cor["hsv_1"], self.cor["hsv_2"], 0], [self.cor["hsv_1"], self.cor["hsv_2"], 1] )
            self.hsv_1_slider.Set_Colors( hsv_1, 1 )
            self.hsv_2_slider.Set_Colors( hsv_2, 1 )
            self.hsv_3_slider.Set_Colors( hsv_3, 1 )
        if self.chan_hsl == True:
            if self.hue_shine == True:
                hsl_1 = self.Gradient_Style( "HSV", False, circular, [0, 1, 1], [1, 1, 1] )
            else:
                hsl_1 = self.Gradient_Style( "HSL", False, circular, [0, self.cor["hsl_2"], self.cor["hsl_3"]], [1, self.cor["hsl_2"], self.cor["hsl_3"]] )
            hsl_2 = self.Gradient_Style( "HSL", False, linear, [self.cor["hsl_1"], 0, self.cor["hsl_3"]], [self.cor["hsl_1"], 1, self.cor["hsl_3"]] )
            hsl_3 = self.Gradient_Style( "HSL", False, linear, [self.cor["hsl_1"], self.cor["hsl_2"], 0], [self.cor["hsl_1"], self.cor["hsl_2"], 1] )
            self.hsl_1_slider.Set_Colors( hsl_1, 1 )
            self.hsl_2_slider.Set_Colors( hsl_2, 1 )
            self.hsl_3_slider.Set_Colors( hsl_3, 1 )
        if self.chan_hcy == True:
            if self.hue_shine == True:
                hcy_1 = self.Gradient_Style( "HSV", False, circular, [0, 1, 1], [1, 1, 1] )
            else:
                hcy_1 = self.Gradient_Style( "HCY", False, circular, [0, self.cor["hcy_2"], self.cor["hcy_3"]], [1, self.cor["hcy_2"], self.cor["hcy_3"]] )
            hcy_2 = self.Gradient_Style( "HCY", False, linear, [self.cor["hcy_1"], 0, self.cor["hcy_3"]], [self.cor["hcy_1"], 1, self.cor["hcy_3"]] )
            hcy_3 = self.Gradient_Style( "HCY", False, linear, [self.cor["hcy_1"], self.cor["hcy_2"], 0], [self.cor["hcy_1"], self.cor["hcy_2"], 1] )
            self.hcy_1_slider.Set_Colors( hcy_1, 1 )
            self.hcy_2_slider.Set_Colors( hcy_2, 1 )
            self.hcy_3_slider.Set_Colors( hcy_3, 1 )
        if self.chan_ard == True:
            if self.hue_shine == True:
                ard_1 = self.Gradient_Style( "HSV", False, circular, [0, 1, 1], [1, 1, 1] )
            else:
                ard_1 = self.Gradient_Style( "ARD", False, circular, [0, self.cor["ard_2"], self.cor["ard_3"]], [1, self.cor["ard_2"], self.cor["ard_3"]] )
            ard_2 = self.Gradient_Style( "ARD", False, linear, [self.cor["ard_1"], 0, self.cor["ard_3"]], [self.cor["ard_1"], 1, self.cor["ard_3"]] )
            ard_3 = self.Gradient_Style( "ARD", False, linear, [self.cor["ard_1"], self.cor["ard_2"], 0], [self.cor["ard_1"], self.cor["ard_2"], 1] )
            self.ard_1_slider.Set_Colors( ard_1, 1 )
            self.ard_2_slider.Set_Colors( ard_2, 1 )
            self.ard_3_slider.Set_Colors( ard_3, 1 )
        # XYZ Linear
        if self.chan_xyz == True:
            xyz_1 = self.Gradient_Style( "XYZ", False, linear, [0, self.cor["xyz_2"], self.cor["xyz_3"]], [1, self.cor["xyz_2"], self.cor["xyz_3"]] )
            xyz_2 = self.Gradient_Style( "XYZ", False, linear, [self.cor["xyz_1"], 0, self.cor["xyz_3"]], [self.cor["xyz_1"], 1, self.cor["xyz_3"]] )
            xyz_3 = self.Gradient_Style( "XYZ", False, linear, [self.cor["xyz_1"], self.cor["xyz_2"], 0], [self.cor["xyz_1"], self.cor["xyz_2"], 1] )
            self.xyz_1_slider.Set_Colors( xyz_1, 1 )
            self.xyz_2_slider.Set_Colors( xyz_2, 1 )
            self.xyz_3_slider.Set_Colors( xyz_3, 1 )
        if self.chan_xyy == True:
            xyy_1 = self.Gradient_Style( "XYY", False, linear, [0, self.cor["xyy_2"], self.cor["xyy_3"]], [1, self.cor["xyy_2"], self.cor["xyy_3"]] )
            xyy_2 = self.Gradient_Style( "XYY", False, linear, [self.cor["xyy_1"], 0, self.cor["xyy_3"]], [self.cor["xyy_1"], 1, self.cor["xyy_3"]] )
            xyy_3 = self.Gradient_Style( "XYY", False, linear, [self.cor["xyy_1"], self.cor["xyy_2"], 0], [self.cor["xyy_1"], self.cor["xyy_2"], 1] )
            self.xyy_1_slider.Set_Colors( xyy_1, 1 )
            self.xyy_2_slider.Set_Colors( xyy_2, 1 )
            self.xyy_3_slider.Set_Colors( xyy_3, 1 )
        if self.chan_lab == True:
            lab_1 = self.Gradient_Style( "LAB", False, linear, [0, self.cor["lab_2"], self.cor["lab_3"]], [1, self.cor["lab_2"], self.cor["lab_3"]] )
            lab_2 = self.Gradient_Style( "LAB", False, linear, [self.cor["lab_1"], 0, self.cor["lab_3"]], [self.cor["lab_1"], 1, self.cor["lab_3"]] )
            lab_3 = self.Gradient_Style( "LAB", False, linear, [self.cor["lab_1"], self.cor["lab_2"], 0], [self.cor["lab_1"], self.cor["lab_2"], 1] )
            self.lab_1_slider.Set_Colors( lab_1, 1 )
            self.lab_2_slider.Set_Colors( lab_2, 1 )
            self.lab_3_slider.Set_Colors( lab_3, 1 )
        # XYZ Hue
        if self.chan_lch == True:
            lch_1 = self.Gradient_Style( "LCH", False, linear, [0, self.cor["lch_2"], self.cor["lch_3"]], [1, self.cor["lch_2"], self.cor["lch_3"]] )
            lch_2 = self.Gradient_Style( "LCH", False, linear, [self.cor["lch_1"], 0, self.cor["lch_3"]], [self.cor["lch_1"], 1, self.cor["lch_3"]] )
            lch_3 = self.Gradient_Style( "LCH", False, linear, [self.cor["lch_1"], self.cor["lch_2"], 0], [self.cor["lch_1"], self.cor["lch_2"], 1] )
            self.lch_1_slider.Set_Colors( lch_1, 1 )
            self.lch_2_slider.Set_Colors( lch_2, 1 )
            self.lch_3_slider.Set_Colors( lch_3, 1 )
        # Non Color
        if self.chan_kkk == True:
            kkk_1 = self.Gradient_Kelvin( linear, self.cor["rgb_1"], self.cor["rgb_2"], self.cor["rgb_3"] )
            self.kkk_1_slider.Set_Colors( kkk_1, 1 )

            # pass
    def Mixer_Set_Style( self ):
        # Channels
        self.Channel_Pole_Style()
        # Mixer
        for i in range( 0, len( self.mixer_colors ) ):
            # Variables
            mode = self.mixer_space
            short = True
            stops = 20
            ll = self.mixer_colors[i]["l"]
            rr = self.mixer_colors[i]["r"]
            # Active
            al = ll["active"]
            ar = rr["active"]
            # Render Colors
            try:
                if ( al == False or ar == False ):
                    self.mixer_module[i]["m"].Set_Colors( None, 1 )
                elif ( al == True and ar == True ):
                    # Variables
                    if mode == "A":                 mixed = self.Gradient_Style( mode, short, stops, [ ll["aaa_1"] ], [ rr["aaa_1"] ] )
                    elif mode in [ "RGB", None ]:   mixed = self.Gradient_Style( "RGB", short, stops, [ ll["rgb_1"], ll["rgb_2"], ll["rgb_3"] ], [ rr["rgb_1"], rr["rgb_2"], rr["rgb_3"] ] )
                    elif mode == "CMY":             mixed = self.Gradient_Style( mode, short, stops, [ ll["cmy_1"], ll["cmy_2"], ll["cmy_3"] ], [ rr["cmy_1"], rr["cmy_2"], rr["cmy_3"] ] )
                    elif mode == "CMYK":            mixed = self.Gradient_Style( mode, short, stops, [ ll["cmyk_1"], ll["cmyk_2"], ll["cmyk_3"], ll["cmyk_4"] ], [ rr["cmyk_1"], rr["cmyk_2"], rr["cmyk_3"], rr["cmyk_4"] ] )
                    elif mode == "RYB":             mixed = self.Gradient_Style( mode, short, stops, [ ll["ryb_1"], ll["ryb_2"], ll["ryb_3"] ], [ rr["ryb_1"], rr["ryb_2"], rr["ryb_3"] ] )
                    elif mode == "YUV":             mixed = self.Gradient_Style( mode, short, stops, [ ll["yuv_1"], ll["yuv_2"], ll["yuv_3"] ], [ rr["yuv_1"], rr["yuv_2"], rr["yuv_3"] ] )
                    elif mode == "HSV":             mixed = self.Gradient_Style( mode, short, stops, [ ll["hsv_1"], ll["hsv_2"], ll["hsv_3"] ], [ rr["hsv_1"], rr["hsv_2"], rr["hsv_3"] ] )
                    elif mode == "HSL":             mixed = self.Gradient_Style( mode, short, stops, [ ll["hsl_1"], ll["hsl_2"], ll["hsl_3"] ], [ rr["hsl_1"], rr["hsl_2"], rr["hsl_3"] ] )
                    elif mode == "HCY":             mixed = self.Gradient_Style( mode, short, stops, [ ll["hcy_1"], ll["hcy_2"], ll["hcy_3"] ], [ rr["hcy_1"], rr["hcy_2"], rr["hcy_3"] ] )
                    elif mode == "ARD":             mixed = self.Gradient_Style( mode, short, stops, [ ll["ard_1"], ll["ard_2"], ll["ard_3"] ], [ rr["ard_1"], rr["ard_2"], rr["ard_3"] ] )
                    elif mode == "XYZ":             mixed = self.Gradient_Style( mode, short, stops, [ ll["xyz_1"], ll["xyz_2"], ll["xyz_3"] ], [ rr["xyz_1"], rr["xyz_2"], rr["xyz_3"] ] )
                    elif mode == "XYY":             mixed = self.Gradient_Style( mode, short, stops, [ ll["xyy_1"], ll["xyy_2"], ll["xyy_3"] ], [ rr["xyy_1"], rr["xyy_2"], rr["xyy_3"] ] )
                    elif mode == "LAB":             mixed = self.Gradient_Style( mode, short, stops, [ ll["lab_1"], ll["lab_2"], ll["lab_3"] ], [ rr["lab_1"], rr["lab_2"], rr["lab_3"] ] )
                    elif mode == "LCH":             mixed = self.Gradient_Style( mode, short, stops, [ ll["lch_1"], ll["lch_2"], ll["lch_3"] ], [ rr["lch_1"], rr["lch_2"], rr["lch_3"] ] )
                    # Render
                    self.mixer_module[i]["m"].Set_Colors( mixed, 1 )
            except:
                pass
    def Pin_Active( self ):
        # Variables
        rgb_cor = self.cor["hex6"]

        # Activate Pin
        for i in range( 0, len( self.pin_module ) ):
            if ( self.pin_cor[i]["active"] == True and self.pin_cor[i]["hex6"] == rgb_cor ):
                self.pin_module[i].Set_Active( True )
            else:
                self.pin_module[i].Set_Active( False )

    def Reference_Name( self ):
        self.dialog.name_display.setText( self.cor["name"] )
        self.dialog.kelvin_class.setText( kelvin["class"] )
        self.dialog.kelvin_discription.setText( kelvin["description"] )

    #endregion
    #region Gradients 

    def Gradient_Style( self, mode, short, stops, cl, cr ):
        # mode = color space
        # short = straight ahead or shortest distance
        # stops = amount of divisions
        # cl and cr = colors in 0-1 format

        len_l = len( cl )
        len_r = len( cr )
        if len_l == len_r:
            length = len_l
            pl, dl = self.Gradient_Point_Delta( mode, short, stops, cl, cr, length )
            output = self.Gradient_Stops( mode, stops, length, pl, dl )
            return output
    def Gradient_Kelvin( self, stops, red, green, blue ):
        # Variables
        delta = kkk_delta / stops
        # Calculations
        output = []
        for i in range( 0, stops+1 ):
            # Temperature
            temp = kkk_min_scale + ( delta * i )
            rgb = self.convert.kkk_to_rgb( temp, kelvin_rgb )
            rgb = [ rgb[0] * red, rgb[1] * green, rgb[2] * blue ]
            # Output
            output.append( rgb )
        # Return
        return output
    def Gradient_Pole( self, mode, short, stops, cl, cn, cr ):
        # Vector
        vl = self.Color_Vector( mode, cl )
        vn = self.Color_Vector( mode, cn )
        vr = self.Color_Vector( mode, cr )
        # Variables
        len_l = len( vl )
        len_n = len( vn )
        len_r = len( vr )
        if len_l == len_n == len_r:
            # Size
            length = len_l
            # Left to Neutral
            pl, dl = self.Gradient_Point_Delta( mode, short, stops, vl, vn, length )
            output = self.Gradient_Stops( mode, stops, length, pl, dl )
            # Neutral to Right
            pn, dn = self.Gradient_Point_Delta( mode, short, stops, vn, vr, length )
            extra = self.Gradient_Stops( mode, stops, length, pn, dn )
            # Construct
            output.extend( extra )
            return output

    def Gradient_Point_Delta( self, mode, short, stops, cl, cr, length ):
        # Variables
        hue = [ "HSV", "HSL", "HCY", "ARD" ]
        pl = list()
        dl = list()

        # Left End
        pl.append( cl[0] )
        if length >= 3:
            pl.append( cl[1] )
            pl.append( cl[2] )
        if length >= 4:
            pl.append( cl[3] )

        # Delta from Left
        d1 = ( cr[0] - cl[0] ) / stops
        dl.append( d1 )
        if length >= 3:
            d2 = ( cr[1] - cl[1] ) / stops
            d3 = ( cr[2] - cl[2] ) / stops
            dl.append( d2 )
            dl.append( d3 )
        if length >= 4:
            d4 = ( cr[3] - cl[3] ) / stops
            dl.append( d4 )
        return pl, dl
    def Gradient_Stops( self, mode, stops, length, left, delta ):
        # Output
        output = list()
        for i in range( 0, stops + 1 ):
            # Value Interpolated
            stop_i = [ self.geometry.Limit_Looper( left[0] + ( delta[0] * i ), 1 ) ]
            if length >= 3:
                stop_i.append( left[1] + ( delta[1] * i ) )
                stop_i.append( left[2] + ( delta[2] * i ) )
            if length >= 4:
                stop_i.append( left[3] + ( delta[3] * i ) )

            # Calculate RGB Linear
            if mode == "A":     rgb = self.convert.aaa_to_rgb( *stop_i )
            if mode == "RGB":   rgb = stop_i
            if mode == "CMY":   rgb = self.convert.cmy_to_rgb( *stop_i )
            if mode == "CMYK":  rgb = self.convert.cmyk_to_rgb( *stop_i )
            if mode == "RYB":   rgb = self.convert.ryb_to_rgb( *stop_i )
            if mode == "YUV":   rgb = self.convert.yuv_to_rgb( *stop_i )
            # Calculate RGB Hue
            if mode == "HSV":   rgb = self.convert.hsv_to_rgb( *stop_i )
            if mode == "HSL":   rgb = self.convert.hsl_to_rgb( *stop_i )
            if mode == "HCY":   rgb = self.convert.hcy_to_rgb( *stop_i )
            if mode == "ARD":   rgb = self.convert.ard_to_rgb( *stop_i )
            # Calculate XYZ Linear
            if mode == "XYZ":   rgb = self.convert.xyz_to_rgb( *stop_i )
            if mode == "XYY":   rgb = self.convert.xyy_to_rgb( *stop_i )
            if mode == "LAB":   rgb = self.convert.lab_to_rgb( *stop_i )
            # Calculate XYZ Hue
            if mode == "LCH":   rgb = self.convert.lch_to_rgb( *stop_i )

            # Output
            output.append( rgb )
        return output

    #endregion
    #region Header

    def Header_Shift( self, SIGNAL_SHIFT ):
        # Shift Foreground and Background
        if SIGNAL_SHIFT == True:
            self.cor = kac
        if SIGNAL_SHIFT == False:
            self.cor = kbc

        # Save Mode
        self.active_ab = SIGNAL_SHIFT
        self.Pigmento_RELEASE()
    def Header_Swap( self ):
        self.Color_Swap()
        self.Pigmento_RELEASE()

    #endregion
    #region Harmony

    # Context Menu
    def Harmony_Index( self, harmony_index ):
        self.harmony_index = harmony_index
        self.Cor_Number()
        self.Pigmento_RELEASE()
        Krita.instance().writeSetting( DOCKER_NAME, "harmony_index", str( self.harmony_index ) )
    def Harmony_Rule( self, harmony_rule ):
        self.harmony_rule = harmony_rule
        self.harmony_spread.Set_Rule( self.harmony_rule )
        self.Pigmento_RELEASE()
        Krita.instance().writeSetting( DOCKER_NAME, "harmony_rule", str( self.harmony_rule ) )
    def Harmony_Edit( self, harmony_edit ):
        self.harmony_edit = harmony_edit
        self.Pigmento_RELEASE()
        Krita.instance().writeSetting( DOCKER_NAME, "harmony_edit", str( self.harmony_edit ) )
    def Harmony_Spread( self, harmony_span ):
        self.harmony_span = harmony_span
        self.Pigmento_RELEASE()
        self.Label_String( f"{ round( self.harmony_span * 360, 2 )}º" )
        Krita.instance().writeSetting( DOCKER_NAME, "harmony_span", str( self.harmony_span ) )

    # Interaction
    def Cor_Number( self ):
        if self.ui_harmony == True:
            try:
                if self.harmony_index == 1:
                    self.cor = har_01
                elif self.harmony_index == 2:
                    self.cor = har_02
                elif self.harmony_index == 3:
                    self.cor = har_03
                elif self.harmony_index == 4:
                    self.cor = har_04
                elif self.harmony_index == 5:
                    self.cor = har_05
            except:
                self.harmony_index = 1
                self.cor = har_01
        else:
            if self.active_ab == True:
                self.cor = kac
            if self.active_ab == False:
                self.cor = kbc

    # Send
    def Harmony_Update( self ):
        if self.harmony_rule == "Triadic":
            parts = 3
            colors = [ har_01["hex6"], har_02["hex6"], har_03["hex6"] ]
        elif self.harmony_rule == "Tetradic":
            parts = 4
            colors = [ har_01["hex6"], har_02["hex6"], har_03["hex6"], har_04["hex6"] ]
        else:
            parts = 5
            colors = [ har_01["hex6"], har_02["hex6"], har_03["hex6"], har_04["hex6"], har_05["hex6"] ]
        self.harmony_swatch.Set_Harmony_Parts( parts, colors )

    #endregion
    #region Panel

    def Panel_inSpace( self, cmodel ):
        # Document
        if cmodel != "CMYK":
            cmodel = "RGB"
        # Panels
        self.panel_square.Set_ColorModel( cmodel )
        self.panel_huesubpanel.Set_ColorModel( cmodel )
        self.panel_gamut.Set_ColorModel( cmodel )
        self.panel_hexagon.Set_ColorModel( cmodel )
        self.panel_luma.Set_ColorModel( cmodel )

    #endregion
    #region Panel Fill

    def Update_Panel_Fill( self ):
        # Foreground Color
        self.panel_fill.Update_Panel( self.cor )

    #endregion
    #region Panel Square

    # Send
    def Update_Panel_Square( self ):
        # Cor
        self.panel_square.Update_Panel( self.cor )
        # Harmony
        if self.ui_harmony == True:
            if self.harmony_rule == "Triadic":
                harmony_list = [har_01, har_02, har_03]
            elif self.harmony_rule == "Tetradic":
                harmony_list = [har_01, har_02, har_03, har_04]
            else:
                harmony_list = [har_01, har_02, har_03, har_04, har_05]
            self.panel_square.Update_Harmony( self.harmony_rule, self.harmony_index, harmony_list )
        else:
            self.panel_square.Update_Harmony( None, None, None )
        # Pins
        if self.ui_pin == True:
            self.panel_square.Update_Pin( self.pin_cor )
        else:
            self.panel_square.Update_Pin( None )
        # Analyze
        if self.analyse_display == True:
            self.panel_square.Update_Analyse( self.analyse_collection )
        else:
            self.panel_square.Update_Analyse( None )
    # Recieve
    def Square_Value( self, value ):
        self.widget_press = True
        c1, c2, c3 = self.Hue_Index( value["mode"] )
        self.Color_Convert( value["mode"], self.cor[c1], value["c2"], value["c3"], 0, self.cor )
        self.Sync_Elements( not self.performance_release, True, False )
    def Square_Tangent( self, tangent ):
        self.widget_press = True
        c1, c2, c3 = self.Hue_Index( self.wheel_space )
        self.Color_Convert( self.wheel_space, tangent, self.cor[c2], self.cor[c3], 0, self.cor )
        self.Sync_Elements( not self.performance_release, True, False )
    def Square_Pin( self, pin ):
        # Variables
        mode = pin["mode"]
        index = pin["pin_index"]
        # Color
        color = self.Color_Convert( mode, self.cor[f"{ mode.lower() }_1"], pin["c2"], pin["c3"], 0, self.pin_cor[index] )
        self.Dict_Copy( self.pin_cor[index], color )
        self.pin_module[index].Set_Color( self.pin_cor[index]["hex6"] )
        self.Pigmento_RELEASE()
        # Save
        Krita.instance().writeSetting( DOCKER_NAME, "pin_cor", str( self.pin_cor ) )

    #endregion
    #region Panel Hue

    # Send
    def Update_Panel_HueCircle( self ):
        # Cor
        self.panel_huecircle.Update_Panel( self.cor )
        # Harmony
        if self.ui_harmony == True:
            if self.harmony_rule == "Triadic":
                harmony_list = [har_01, har_02, har_03]
            elif self.harmony_rule == "Tetradic":
                harmony_list = [har_01, har_02, har_03, har_04]
            else:
                harmony_list = [har_01, har_02, har_03, har_04, har_05]
            self.panel_huecircle.Update_Harmony( self.harmony_rule, self.harmony_index, harmony_list )
        else:
            self.panel_huecircle.Update_Harmony( None, None, None )
        # Pins
        if self.ui_pin == True:
            self.panel_huecircle.Update_Pin( self.pin_cor )
        else:
            self.panel_huecircle.Update_Pin( None )

        # Subpanel
        self.panel_huesubpanel.Update_Panel( self.cor )
        # Harmony
        if self.ui_harmony == True:
            if self.harmony_rule == "Triadic":
                harmony = [ har_01, har_02, har_03 ]
            elif self.harmony_rule == "Tetradic":
                harmony = [ har_01, har_02, har_03, har_04 ]
            else:
                harmony = [ har_01, har_02, har_03, har_04, har_05 ]
            self.panel_huesubpanel.Update_Harmony( self.harmony_rule, self.harmony_index, harmony_list )
        else:
            self.panel_huesubpanel.Update_Harmony( None, None, None )
        # Pins
        if self.ui_pin == True:
            self.panel_huesubpanel.Update_Pin( self.pin_cor )
        else:
            self.panel_huesubpanel.Update_Pin( None )
        # Analyze
        if self.analyse_display == True:
            self.panel_huesubpanel.Update_Analyse( self.analyse_collection )
        else:
            self.panel_huesubpanel.Update_Analyse( None )
    # Recieve
    def HueCircle_Value( self, angle ):
        self.widget_press = True
        c1, c2, c3 = self.Hue_Index( self.wheel_space )
        self.Color_Convert( self.wheel_space, angle, self.cor[c2], self.cor[c3], 0, self.cor )
        self.Sync_Elements( not self.performance_release, True, False )
    def HueCircle_SubPanel( self, huecircle_shape ):
        # Variable
        self.huecircle_shape = huecircle_shape
        # Modules
        if self.huecircle_shape == "Triangle":
            self.panel_huesubpanel.Set_ColorSpace_inDocument( self.directory_plugin, "RGB", "HSL", "3" ) # Triangle
        if self.huecircle_shape == "Square":
            self.panel_huesubpanel.Set_ColorSpace_inDocument( self.directory_plugin, "RGB", self.wheel_space, "4" ) # Square
        if self.huecircle_shape == "Diamond":
            self.panel_huesubpanel.Set_ColorSpace_inDocument( self.directory_plugin, "RGB", "HSL", "R" ) # Diamond
        # Modules
        self.Update_Size() # Updates Mask
        # Save
        Krita.instance().writeSetting( DOCKER_NAME, "huecircle_shape", str( self.huecircle_shape ) )
    def HueCircle_Geo( self, width, height ):
        # Widget
        w2 = int( width * 0.5 )
        h2 = int( height * 0.5 )
        # Frame
        if width >= height:
            side = height
            px = int( w2 - ( side * 0.5 ) )
            py = 0
        else:
            side = width
            px = 0
            py = int( h2 - ( side * 0.5 ) )

        # Variables
        if self.huecircle_shape == "None":
            index = 0
            px = -10
            py = -10
            w = 10
            h = 10
        if self.huecircle_shape == "Triangle":
            index = 0
            k = 0.07
            x = 0.28
            y1 = 0.13
            y2 = 2 * y1
            px = int( px + x * side )
            py = int( py + y1 * side + 1 )
            w = int( side - x * side - k * side )
            h = int( side - y2 * side )
        if self.huecircle_shape == "Square":
            index = 1
            k1 = 0.2
            k2 = 2 * k1
            px = int( px + k1 * side )
            py = int( py + k1 * side )
            w = int( side - k2 * side )
            h = int( side - k2 * side )
        if self.huecircle_shape == "Diamond":
            index = 2
            k1 = 0.07
            k2 = 2 * k1
            px = int( px + k1 * side )
            py = int( py + k1 * side + 1 )
            w = int( side - k2 * side )
            h = int( side - k2 * side )
            
        # Geometry
        self.layout.panel_huesubpanel.setGeometry( px, py, w, h )
        self.panel_huesubpanel.Set_Size( w, h )

    #endregion
    #region Panel Gamut

    # Send
    def Update_Panel_Gamut( self ):
        # Cor
        self.panel_gamut.Update_Panel( self.cor )
        # Harmony
        if self.ui_harmony == True:
            if self.harmony_rule == "Triadic":
                harmony_list = [har_01, har_02, har_03]
            elif self.harmony_rule == "Tetradic":
                harmony_list = [har_01, har_02, har_03, har_04]
            else:
                harmony_list = [har_01, har_02, har_03, har_04, har_05]
            self.panel_gamut.Update_Harmony( self.harmony_rule, self.harmony_index, harmony_list )
        else:
            self.panel_gamut.Update_Harmony( None, None, None )
        # Pins
        if self.ui_pin == True:
            self.panel_gamut.Update_Pin( self.pin_cor )
        else:
            self.panel_gamut.Update_Pin( None )
        # Analyze
        if self.analyse_display == True:
            self.panel_gamut.Update_Analyse( self.analyse_collection )
        else:
            self.panel_gamut.Update_Analyse( None )
    # Recieve
    def Gamut_Value( self, value ):
        self.widget_press = True
        mode = self.wheel_space
        self.Color_Convert( mode, value["c1"], value["c2"], self.cor[f"{ mode.lower() }_3"], 0, self.cor )
        self.Sync_Elements( not self.performance_release, True, False )
    def Gamut_Tangent( self, tangent ):
        self.widget_press = True
        index = self.wheel_space.lower()
        self.Color_Convert( self.wheel_space, self.cor[f"{index}_1"], self.cor[f"{index}_2"], tangent, 0, self.cor )
        self.Sync_Elements( not self.performance_release, True, False )
    def Gamut_Mask( self, gamut_mask ):
        self.gamut_mask = gamut_mask
        Krita.instance().writeSetting( DOCKER_NAME, "gamut_mask", str( self.gamut_mask ) )
    def Gamut_Profile( self, gamut_profile ):
        self.gamut_profile = gamut_profile
        Krita.instance().writeSetting( DOCKER_NAME, "gamut_profile", str( self.gamut_profile ) )
    def Gamut_Pin( self, pin ):
        # Variables
        mode = self.wheel_space
        index = pin["pin_index"]
        # Color
        color = self.Color_Convert( mode, pin["c1"], pin["c2"], self.cor[f"{ mode.lower() }_3"], 0, self.pin_cor[index] )
        self.Dict_Copy( self.pin_cor[index], color )
        self.pin_module[index].Set_Color( self.pin_cor[index]["hex6"] )
        self.Pigmento_RELEASE()
        # Save
        Krita.instance().writeSetting( DOCKER_NAME, "pin_cor", str( self.pin_cor ) )

    #endregion
    #region Panel Hexagon

    # Send
    def Update_Panel_Hexagon( self ):
        # Cor
        self.panel_hexagon.Update_Panel( self.cor )
        # Harmony
        if self.ui_harmony == True:
            if self.harmony_rule == "Triadic":
                harmony_list = [har_01, har_02, har_03]
            elif self.harmony_rule == "Tetradic":
                harmony_list = [har_01, har_02, har_03, har_04]
            else:
                harmony_list = [har_01, har_02, har_03, har_04, har_05]
            self.panel_hexagon.Update_Harmony( self.harmony_rule, self.harmony_index, harmony_list )
        else:
            self.panel_hexagon.Update_Harmony( None, None, None )
        # Pins
        if self.ui_pin == True:
            self.panel_hexagon.Update_Pin( self.pin_cor )
        else:
            self.panel_hexagon.Update_Pin( None )
        # Analyze
        if self.analyse_display == True:
            self.panel_hexagon.Update_Analyse( self.analyse_collection )
        else:
            self.panel_hexagon.Update_Analyse( None )
    # Recieve
    def Hexagon_Value( self, value ):
        self.widget_press = True
        self.Color_Convert( "UVD", value["c1"], value["c2"], self.cor["uvd_3"], 0, self.cor )
        self.Sync_Elements( not self.performance_release, True, False )
    def Hexagon_Depth( self, depth ):
        self.widget_press = True
        self.Color_Convert( "ARD", self.cor["ard_1"], self.cor["ard_2"], depth, 0, self.cor )
        self.Sync_Elements( not self.performance_release, True, False )
    def Hexagon_Pin( self, pin ):
        index = pin["pin_index"]
        color = self.Color_Convert( "UVD", pin["c1"], pin["c2"], self.cor["uvd_3"], 0, self.pin_cor[index] )
        self.Dict_Copy( self.pin_cor[index], color )
        self.pin_module[index].Set_Color( self.pin_cor[index]["hex6"] )
        self.Pigmento_RELEASE()
        Krita.instance().writeSetting( DOCKER_NAME, "pin_cor", str( self.pin_cor ) )

    #endregion
    #region Panel Luma

    # Send
    def Update_Panel_Luma( self ):
        # Cor
        self.panel_luma.Update_Panel( self.cor )
        # Harmony
        if self.ui_harmony == True:
            if self.harmony_rule == "Triadic":
                harmony_list = [ har_01, har_02, har_03 ]
            elif self.harmony_rule == "Tetradic":
                harmony_list = [ har_01, har_02, har_03, har_04 ]
            else:
                harmony_list = [ har_01, har_02, har_03, har_04, har_05 ]
            self.panel_luma.Update_Harmony( self.harmony_rule, self.harmony_index, harmony_list )
        else:
            self.panel_luma.Update_Harmony( None, None, None )
        # Pins
        if self.ui_pin == True:
            self.panel_luma.Update_Pin( self.pin_cor )
        else:
            self.panel_luma.Update_Pin( None )
        # Analyze
        if self.analyse_display == True:
            self.panel_luma.Update_Analyse( self.analyse_collection )
        else:
            self.panel_luma.Update_Analyse( None )
    # Recieve
    def Luma_Value( self, value ):
        self.widget_press = True
        c1, c2, c3 = self.Hue_Index( value["mode"] )
        self.Color_Convert( value["mode"], self.cor[c1], value["c2"], value["c3"], 0, self.cor )
        self.Sync_Elements( not self.performance_release, True, False )
    def Luma_Tangent( self, tangent ):
        self.widget_press = True
        self.Color_Convert( "YUV", tangent, self.cor["yuv_2"], self.cor["yuv_3"], 0, self.cor )
        self.Sync_Elements( not self.performance_release, True, False )
    def Luma_Pin( self, pin ):
        # Variables
        index = pin["pin_index"]
        # Color
        color = self.Color_Convert( "YUV", self.cor[f"yuv_1"], pin["c2"], pin["c3"], 0, self.pin_cor[index] )
        self.Dict_Copy( self.pin_cor[index], color )
        self.pin_module[index].Set_Color( self.pin_cor[index]["hex6"] )
        self.Pigmento_RELEASE()
        # Save
        Krita.instance().writeSetting( DOCKER_NAME, "pin_cor", str( self.pin_cor ) )

    #endregion
    #region Panel Dot

    # UI
    def Dot_Widget( self, boolean ):
        if boolean == True:
            horz = 5
            vert = 2
            mini = 5
            maxi = 120
        else:
            horz = 0
            vert = 0
            mini = 0
            maxi = 0
        self.layout.edit_dot.setMinimumWidth( mini )
        self.layout.edit_dot.setMaximumWidth( maxi )
        self.layout.edit_dot_layout.setContentsMargins( horz, vert, horz, vert )

    # Send
    def Dot_Update( self ):
        self.Update_Panel_Dot()
        self.Pigmento_RELEASE()
        Krita.instance().writeSetting( DOCKER_NAME, "dot_1", str( self.dot_1 ) )
        Krita.instance().writeSetting( DOCKER_NAME, "dot_2", str( self.dot_2 ) )
        Krita.instance().writeSetting( DOCKER_NAME, "dot_3", str( self.dot_3 ) )
        Krita.instance().writeSetting( DOCKER_NAME, "dot_4", str( self.dot_4 ) )
    def Update_Panel_Dot( self ):
        # Color Lines
        line_top = []
        for i in range( 0, self.dot_dimension ):
            line_top.append( self.dot_3 )
        line_mid = []
        for i in range( 0, self.dot_dimension ):
            if i == self.dot_dimension:
                color = dot_2
            else:
                factor = i / ( self.dot_dimension-1 )
                color = self.Color_Interpolate( self.dot_interpolation, self.dot_1, self.dot_2, factor )
            line_mid.append( color )
        line_bot = []
        for i in range( 0, self.dot_dimension ):
            line_bot.append( self.dot_4 )

        # Color Matrix
        dot_matrix = []
        value_top = 0
        value_mid = int( self.dot_dimension * 0.5 )
        value_bot = self.dot_dimension - 1
        for y in range( 0, self.dot_dimension ):
            line = []
            for x in range( 0, self.dot_dimension ):
                if y == value_top:
                    line.append( line_top[x]["hex6"] )
                if ( y > value_top and y < value_mid ):
                    factor = y / value_mid
                    color_a = line_top[x]
                    color_b = line_mid[x]
                    color = self.Color_Interpolate( self.dot_interpolation, color_a, color_b, factor )
                    line.append( color["hex6"] )
                if y == value_mid:
                    line.append( line_mid[x]["hex6"] )
                if ( y > value_mid and y < value_bot ):
                    factor = ( y-value_mid ) / value_mid
                    color_a = line_mid[x]
                    color_b = line_bot[x]
                    color = self.Color_Interpolate( self.dot_interpolation, color_a, color_b, factor )
                    line.append( color["hex6"] )
                if y == value_bot:
                    line.append( line_bot[x]["hex6"] )
            dot_matrix.append( line )
        if len( dot_matrix ) == 0:
            dot_matrix = None

        # Update
        self.panel_dot.Update_Color( dot_matrix )
    def Update_Edit_Dot( self ):
        self.pin_d1.Set_Color( self.dot_1["hex6"] )
        self.pin_d2.Set_Color( self.dot_2["hex6"] )
        self.pin_d3.Set_Color( self.dot_3["hex6"] )
        self.pin_d4.Set_Color( self.dot_4["hex6"] )
    # Recieve
    def Dot_Value( self, SIGNAL_VALUE ):
        self.widget_press = True
        hex_code = SIGNAL_VALUE
        valid_code = self.HEX_Valid( hex_code, 6 )
        if valid_code == True:
            rgb = self.convert.hex6_to_rgb( SIGNAL_VALUE )
            self.Color_Convert( "RGB", rgb[0], rgb[1], rgb[2], 0, self.cor )
            self.Sync_Elements( not self.performance_release, True, True )
    def Dot_Interpolation( self, SIGNAL_INTERPOLATION ):
        self.dot_interpolation = SIGNAL_INTERPOLATION
        self.panel_dot.Set_Interpolation( SIGNAL_INTERPOLATION )
        self.Update_Panel_Dot()
        Krita.instance().writeSetting( DOCKER_NAME, "dot_interpolation", str( self.dot_interpolation ) )
    def Dot_Dimension( self, SIGNAL_DIMENSION ):
        self.dot_dimension = SIGNAL_DIMENSION
        self.panel_dot.Set_Dimension( SIGNAL_DIMENSION )
        self.Update_Panel_Dot()
        Krita.instance().writeSetting( DOCKER_NAME, "dot_dimension", str( self.dot_dimension ) )
    def Dot_Edit( self, SIGNAL_EDIT ):
        # Signals
        self.dot_edit = SIGNAL_EDIT
        self.panel_dot.Set_Edit( SIGNAL_EDIT )
        self.Dot_Widget( SIGNAL_EDIT )
        self.Update_Panel_Dot()
        # Size
        self.Update_Size()
        # Save
        Krita.instance().writeSetting( DOCKER_NAME, "dot_edit", str( self.dot_edit ) )
    def Dot_Zorn( self, SIGNAL_ZORN ):
        # Variables
        self.dot_1 = self.Color_Convert( "HEX", "#edb525", 0, 0, 0, self.dot_1 )
        self.dot_2 = self.Color_Convert( "HEX", "#b72e35", 0, 0, 0, self.dot_2 )
        self.dot_3 = self.Color_Convert( "HEX", "#edf0ec", 0, 0, 0, self.dot_3 )
        self.dot_4 = self.Color_Convert( "HEX", "#292421", 0, 0, 0, self.dot_4 )
        self.dot_1["active"] = True
        self.dot_2["active"] = True
        self.dot_3["active"] = True
        self.dot_4["active"] = True
        # Update
        self.Update_Panel_Dot()
        # Pins
        self.pin_d1.Set_Color( self.dot_1["hex6"] )
        self.pin_d2.Set_Color( self.dot_2["hex6"] )
        self.pin_d3.Set_Color( self.dot_3["hex6"] )
        self.pin_d4.Set_Color( self.dot_4["hex6"] )
        # Save
        Krita.instance().writeSetting( DOCKER_NAME, "dot_1", str( self.dot_1 ) )
        Krita.instance().writeSetting( DOCKER_NAME, "dot_2", str( self.dot_2 ) )
        Krita.instance().writeSetting( DOCKER_NAME, "dot_3", str( self.dot_3 ) )
        Krita.instance().writeSetting( DOCKER_NAME, "dot_4", str( self.dot_4 ) )

    # Button
    def Dot_Swap( self ):
        # Initial Swap
        a = self.dot_1.copy()
        b = self.dot_2.copy()
        c = self.dot_3.copy()
        d = self.dot_4.copy()
        # Final Swap
        self.dot_1 = c.copy()
        self.dot_2 = d.copy()
        self.dot_3 = a.copy()
        self.dot_4 = b.copy()
        # Functions
        self.pin_d1.Set_Color( self.dot_1["hex6"] )
        self.pin_d2.Set_Color( self.dot_2["hex6"] )
        self.pin_d3.Set_Color( self.dot_3["hex6"] )
        self.pin_d4.Set_Color( self.dot_4["hex6"] )
        # Update
        self.Update_Panel_Dot()

    # Apply
    def Dot_Apply_1( self, SIGNAL_APPLY ):
        if self.dot_1["active"] == True:
            self.Color_Convert( "HEX", self.dot_1["hex6"], 0, 0, 0, self.cor )
            self.Pigmento_RELEASE()
    def Dot_Apply_2( self, SIGNAL_APPLY ):
        if self.dot_2["active"] == True:
            self.Color_Convert( "HEX", self.dot_2["hex6"], 0, 0, 0, self.cor )
            self.Pigmento_RELEASE()
    def Dot_Apply_3( self, SIGNAL_APPLY ):
        if self.dot_3["active"] == True:
            self.Color_Convert( "HEX", self.dot_3["hex6"], 0, 0, 0, self.cor )
            self.Pigmento_RELEASE()
    def Dot_Apply_4( self, SIGNAL_APPLY ):
        if self.dot_4["active"] == True:
            self.Color_Convert( "HEX", self.dot_4["hex6"], 0, 0, 0, self.cor )
            self.Pigmento_RELEASE()
    # Save
    def Dot_Save_1( self, SIGNAL_SAVE ):
        self.dot_1["active"] = True
        self.Dict_Copy( self.dot_1, self.cor )
        self.pin_d1.Set_Color( self.dot_1["hex6"] )
        self.Dot_Update()
    def Dot_Save_2( self, SIGNAL_SAVE ):
        self.dot_2["active"] = True
        self.Dict_Copy( self.dot_2, self.cor )
        self.pin_d2.Set_Color( self.dot_2["hex6"] )
        self.Dot_Update()
    def Dot_Save_3( self, SIGNAL_SAVE ):
        self.dot_3["active"] = True
        self.Dict_Copy( self.dot_3, self.cor )
        self.pin_d3.Set_Color( self.dot_3["hex6"] )
        self.Dot_Update()
    def Dot_Save_4( self, SIGNAL_SAVE ):
        self.dot_4["active"] = True
        self.Dict_Copy( self.dot_4, self.cor )
        self.pin_d4.Set_Color( self.dot_4["hex6"] )
        self.Dot_Update()
    # Clean
    def Dot_Clean_1( self, SIGNAL_CLEAN ):
        self.dot_1["active"] = False
        self.Dict_Copy( self.dot_1, color_false )
        self.pin_d1.Set_Color( None )
        self.Dot_Update()
    def Dot_Clean_2( self, SIGNAL_CLEAN ):
        self.dot_2["active"] = False
        self.Dict_Copy( self.dot_2, color_false )
        self.pin_d2.Set_Color( None )
        self.Dot_Update()
    def Dot_Clean_3( self, SIGNAL_CLEAN ):
        self.dot_3["active"] = False
        self.Dict_Copy( self.dot_3, color_false )
        self.pin_d3.Set_Color( None )
        self.Dot_Update()
    def Dot_Clean_4( self, SIGNAL_CLEAN ):
        self.dot_4["active"] = False
        self.Dict_Copy( self.dot_4, color_false )
        self.pin_d4.Set_Color( None )
        self.Dot_Update()

    #endregion
    #region Panel Mask

    # UI
    def Mask_Widget( self, boolean ):
        if boolean == True:
            horz = 5
            vert = 2
            mini = 5
            maxi = 120
        else:
            horz = 0
            vert = 0
            mini = 0
            maxi = 0
        self.layout.edit_mask.setMinimumWidth( mini )
        self.layout.edit_mask.setMaximumWidth( maxi )
        self.layout.edit_mask_layout.setContentsMargins( horz, vert, horz, vert )

    # Send
    def Update_Panel_Mask( self ):
        self.panel_mask.Update_Color( self.mask_color, self.mask_alpha )
    # Recieve
    def Mask_Value( self, SIGNAL_VALUE ):
        self.Pigmento_APPLY( "HEX", SIGNAL_VALUE, 0, 0, 0, self.cor )
    def Mask_Set( self, SIGNAL_MASKSET ):
        self.mask_set = SIGNAL_MASKSET
        self.Mask_Read( False )
        # Save
        Krita.instance().writeSetting( DOCKER_NAME, "mask_set", str( self.mask_set ) )
        self.Mask_Write()
    def Mask_Edit( self, SIGNAL_EDIT ):
        # Signals
        self.mask_edit = SIGNAL_EDIT
        self.panel_mask.Set_Edit( SIGNAL_EDIT )
        self.Mask_Widget( SIGNAL_EDIT )
        # Size
        self.Update_Size()
        # Save
        Krita.instance().writeSetting( DOCKER_NAME, "mask_edit", str( self.mask_edit ) )

    # Operators
    def Mask_Load( self ):
        # Open File
        path = os.path.join( self.mask_set, "color.eo" )
        exists = os.path.exists( path )
        if exists == True:
            with open( path, "r" ) as color:
                data = color.readlines()

                for i in range( len( data ) ):
                    index = data[i]
                    if index.startswith( "mask_color=" ) == True:
                        line = index.replace( "mask_color=", "" )
                        self.mask_color = eval( line )
                    if index.startswith( "mask_alpha=" ) == True:
                        line = index.replace( "mask_alpha=", "" )
                        self.mask_alpha = eval( line )

                # Update
                self.Update_Panel_Mask()
                # Pins
                self.Mask_Pin_Color( self.mask_color )
                self.Mask_Pin_Alpha( self.mask_alpha )
    def Mask_Read( self, SIGNAL_RESET ):
        if self.panel_index == panel_mask:
            # Live
            self.Mask_Live_Close()
            # Open File
            path = os.path.join( self.mask_set, "color.eo" )
            with open( path, "r" ) as color:
                data = color.readlines()
                for i in range( len( data ) ):
                    index = data[i]
                    if SIGNAL_RESET == True:
                        if index.startswith( "default_color=" ) == True:
                            line = index.replace( "default_color=", "" )
                            self.mask_color = eval( line )
                        if index.startswith( "default_alpha=" ) == True:
                            line = index.replace( "default_alpha=", "" )
                            self.mask_alpha = eval( line )
                    else:
                        if index.startswith( "mask_color=" ) == True:
                            line = index.replace( "mask_color=", "" )
                            self.mask_color = eval( line )
                        if index.startswith( "mask_alpha=" ) == True:
                            line = index.replace( "mask_alpha=", "" )
                            self.mask_alpha = eval( line )

                # Update
                self.Update_Panel_Mask()
                # Pins
                self.Mask_Pin_Color( self.mask_color )
                self.Mask_Pin_Alpha( self.mask_alpha )
    def Mask_Write( self ):
        if ( self.panel_index == panel_mask and self.mask_write == False ):
            # Variables
            self.mask_write = True
            path = os.path.join( self.mask_set, "color.eo" )

            # Read
            with open( path, "r" ) as note:
                read = note.readlines()

            # Edit
            edit = ""
            for i in range( len( read ) ):
                index = read[i]
                if index.startswith( "mask_color=" ) == True:
                    line = f"mask_color={ self.mask_color }\n"
                    index = line
                if index.startswith( "mask_alpha=" ) == True:
                    line = f"mask_alpha={ self.mask_alpha }\n"
                    index = line
                edit += index

                # Write
                with open( path, "w" ) as note:
                    note.write( edit )
            
            # Variables
            self.mask_write = False

    # Pin
    def Mask_Pin_Color( self, mask_color ):
        # Background
        self.mask_b1.Set_Color( mask_color["b1"] )
        self.mask_b2.Set_Color( mask_color["b2"] )
        self.mask_b3.Set_Color( mask_color["b3"] )
        # Diffuse
        self.mask_d1.Set_Color( mask_color["d1"] )
        self.mask_d2.Set_Color( mask_color["d2"] )
        self.mask_d3.Set_Color( mask_color["d3"] )
        self.mask_d4.Set_Color( mask_color["d4"] )
        self.mask_d5.Set_Color( mask_color["d5"] )
        self.mask_d6.Set_Color( mask_color["d6"] )
        # Foreground
        self.mask_f1.Set_Color( mask_color["f1"] )
        self.mask_f2.Set_Color( mask_color["f2"] )
        self.mask_f3.Set_Color( mask_color["f3"] )
    def Mask_Pin_Alpha( self, mask_alpha ):
        # Background
        self.mask_b1.Set_Alpha( mask_alpha["b1"] )
        self.mask_b2.Set_Alpha( mask_alpha["b2"] )
        self.mask_b3.Set_Alpha( mask_alpha["b3"] )
        # Diffuse
        self.mask_d1.Set_Alpha( mask_alpha["d1"] )
        self.mask_d2.Set_Alpha( mask_alpha["d2"] )
        self.mask_d3.Set_Alpha( mask_alpha["d3"] )
        self.mask_d4.Set_Alpha( mask_alpha["d4"] )
        self.mask_d5.Set_Alpha( mask_alpha["d5"] )
        self.mask_d6.Set_Alpha( mask_alpha["d6"] )
        # Foreground
        self.mask_f1.Set_Alpha( mask_alpha["f1"] )
        self.mask_f2.Set_Alpha( mask_alpha["f2"] )
        self.mask_f3.Set_Alpha( mask_alpha["f3"] )
    # Live
    def Mask_Live_Update( self ):
        # Live
        if self.mask_live["b1"] == True:    self.Mask_Save_B1( 0 )
        if self.mask_live["b2"] == True:    self.Mask_Save_B2( 0 )
        if self.mask_live["b3"] == True:    self.Mask_Save_B3( 0 )
        if self.mask_live["d1"] == True:    self.Mask_Save_D1( 0 )
        if self.mask_live["d2"] == True:    self.Mask_Save_D2( 0 )
        if self.mask_live["d3"] == True:    self.Mask_Save_D3( 0 )
        if self.mask_live["d4"] == True:    self.Mask_Save_D4( 0 )
        if self.mask_live["d5"] == True:    self.Mask_Save_D5( 0 )
        if self.mask_live["d6"] == True:    self.Mask_Save_D6( 0 )
        if self.mask_live["f1"] == True:    self.Mask_Save_F1( 0 )
        if self.mask_live["f2"] == True:    self.Mask_Save_F2( 0 )
        if self.mask_live["f3"] == True:    self.Mask_Save_F3( 0 )

        # Update
        if True in self.mask_live:          self.Update_Panel_Mask()
    def Mask_Live_Uncheck( self, item ):
        if item != "b1":    self.layout.bg_1_live.setChecked( False )
        if item != "b2":    self.layout.bg_2_live.setChecked( False )
        if item != "b3":    self.layout.bg_3_live.setChecked( False )
        if item != "d1":    self.layout.dif_1_live.setChecked( False )
        if item != "d2":    self.layout.dif_2_live.setChecked( False )
        if item != "d3":    self.layout.dif_3_live.setChecked( False )
        if item != "d4":    self.layout.dif_4_live.setChecked( False )
        if item != "d5":    self.layout.dif_5_live.setChecked( False )
        if item != "d6":    self.layout.dif_6_live.setChecked( False )
        if item != "f1":    self.layout.fg_1_live.setChecked( False )
        if item != "f2":    self.layout.fg_2_live.setChecked( False )
        if item != "f3":    self.layout.fg_3_live.setChecked( False )

    # Live
    def Mask_Live_Close( self ):
        self.layout.fg_3_live.setChecked( False )
        self.layout.fg_2_live.setChecked( False )
        self.layout.fg_1_live.setChecked( False )
        self.layout.dif_6_live.setChecked( False )
        self.layout.dif_5_live.setChecked( False )
        self.layout.dif_4_live.setChecked( False )
        self.layout.dif_3_live.setChecked( False )
        self.layout.dif_2_live.setChecked( False )
        self.layout.dif_1_live.setChecked( False )
        self.layout.bg_3_live.setChecked( False )
        self.layout.bg_2_live.setChecked( False )
        self.layout.bg_1_live.setChecked( False )
    def Mask_Live_B1( self, boolean ):
        self.mask_live["b1"] = boolean
        if boolean == True:
            self.Mask_Live_Uncheck( "b1" )
            self.Pigmento_APPLY( "HEX", self.mask_color["b1"], 0, 0, 0, self.cor )
    def Mask_Live_B2( self, boolean ):
        self.mask_live["b2"] = boolean
        if boolean == True:
            self.Mask_Live_Uncheck( "b2" )
            self.Pigmento_APPLY( "HEX", self.mask_color["b2"], 0, 0, 0, self.cor )
    def Mask_Live_B3( self, boolean ):
        self.mask_live["b3"] = boolean
        if boolean == True:
            self.Mask_Live_Uncheck( "b3" )
            self.Pigmento_APPLY( "HEX", self.mask_color["b3"], 0, 0, 0, self.cor )
    def Mask_Live_D1( self, boolean ):
        self.mask_live["d1"] = boolean
        if boolean == True:
            self.Mask_Live_Uncheck( "d1" )
            self.Pigmento_APPLY( "HEX", self.mask_color["d1"], 0, 0, 0, self.cor )
    def Mask_Live_D2( self, boolean ):
        self.mask_live["d2"] = boolean
        if boolean == True:
            self.Mask_Live_Uncheck( "d2" )
            self.Pigmento_APPLY( "HEX", self.mask_color["d2"], 0, 0, 0, self.cor )
    def Mask_Live_D3( self, boolean ):
        self.mask_live["d3"] = boolean
        if boolean == True:
            self.Mask_Live_Uncheck( "d3" )
            self.Pigmento_APPLY( "HEX", self.mask_color["d3"], 0, 0, 0, self.cor )
    def Mask_Live_D4( self, boolean ):
        self.mask_live["d4"] = boolean
        if boolean == True:
            self.Mask_Live_Uncheck( "d4" )
            self.Pigmento_APPLY( "HEX", self.mask_color["d4"], 0, 0, 0, self.cor )
    def Mask_Live_D5( self, boolean ):
        self.mask_live["d5"] = boolean
        if boolean == True:
            self.Mask_Live_Uncheck( "d5" )
            self.Pigmento_APPLY( "HEX", self.mask_color["d5"], 0, 0, 0, self.cor )
    def Mask_Live_D6( self, boolean ):
        self.mask_live["d6"] = boolean
        if boolean == True:
            self.Mask_Live_Uncheck( "d6" )
            self.Pigmento_APPLY( "HEX", self.mask_color["d6"], 0, 0, 0, self.cor )
    def Mask_Live_F1( self, boolean ):
        self.mask_live["f1"] = boolean
        if boolean == True:
            self.Mask_Live_Uncheck( "f1" )
            self.Pigmento_APPLY( "HEX", self.mask_color["f1"], 0, 0, 0, self.cor )
    def Mask_Live_F2( self, boolean ):
        self.mask_live["f2"] = boolean
        if boolean == True:
            self.Mask_Live_Uncheck( "f2" )
            self.Pigmento_APPLY( "HEX", self.mask_color["f2"], 0, 0, 0, self.cor )
    def Mask_Live_F3( self, boolean ):
        self.mask_live["f3"] = boolean
        if boolean == True:
            self.Mask_Live_Uncheck( "f3" )
            self.Pigmento_APPLY( "HEX", self.mask_color["f3"], 0, 0, 0, self.cor )
    # Apply
    def Mask_Apply_B1( self, SIGNAL_APPLY ):
        self.Pigmento_APPLY( "HEX", self.mask_color["b1"], 0, 0, 0, self.cor )
    def Mask_Apply_B2( self, SIGNAL_APPLY ):
        self.Pigmento_APPLY( "HEX", self.mask_color["b2"], 0, 0, 0, self.cor )
    def Mask_Apply_B3( self, SIGNAL_APPLY ):
        self.Pigmento_APPLY( "HEX", self.mask_color["b3"], 0, 0, 0, self.cor )
    def Mask_Apply_D1( self, SIGNAL_APPLY ):
        self.Pigmento_APPLY( "HEX", self.mask_color["d1"], 0, 0, 0, self.cor )
    def Mask_Apply_D2( self, SIGNAL_APPLY ):
        self.Pigmento_APPLY( "HEX", self.mask_color["d2"], 0, 0, 0, self.cor )
    def Mask_Apply_D3( self, SIGNAL_APPLY ):
        self.Pigmento_APPLY( "HEX", self.mask_color["d3"], 0, 0, 0, self.cor )
    def Mask_Apply_D4( self, SIGNAL_APPLY ):
        self.Pigmento_APPLY( "HEX", self.mask_color["d4"], 0, 0, 0, self.cor )
    def Mask_Apply_D5( self, SIGNAL_APPLY ):
        self.Pigmento_APPLY( "HEX", self.mask_color["d5"], 0, 0, 0, self.cor )
    def Mask_Apply_D6( self, SIGNAL_APPLY ):
        self.Pigmento_APPLY( "HEX", self.mask_color["d6"], 0, 0, 0, self.cor )
    def Mask_Apply_F1( self, SIGNAL_APPLY ):
        self.Pigmento_APPLY( "HEX", self.mask_color["f1"], 0, 0, 0, self.cor )
    def Mask_Apply_F2( self, SIGNAL_APPLY ):
        self.Pigmento_APPLY( "HEX", self.mask_color["f2"], 0, 0, 0, self.cor )
    def Mask_Apply_F3( self, SIGNAL_APPLY ):
        self.Pigmento_APPLY( "HEX", self.mask_color["f3"], 0, 0, 0, self.cor )
    # Save
    def Mask_Save_B1( self, SIGNAL_SAVE ):
        cor = self.cor["hex6"]
        self.mask_color["b1"] = cor
        self.mask_b1.Set_Color( cor )
        self.mask_b1.Set_Alpha( 1 )
        self.Update_Panel_Mask()
        Krita.instance().writeSetting( DOCKER_NAME, "mask_color", str( self.mask_color ) )
    def Mask_Save_B2( self, SIGNAL_SAVE ):
        cor = self.cor["hex6"]
        self.mask_color["b2"] = cor
        self.mask_b2.Set_Color( cor )
        self.mask_b2.Set_Alpha( 1 )
        self.Update_Panel_Mask()
        Krita.instance().writeSetting( DOCKER_NAME, "mask_color", str( self.mask_color ) )
    def Mask_Save_B3( self, SIGNAL_SAVE ):
        cor = self.cor["hex6"]
        self.mask_color["b3"] = cor
        self.mask_b3.Set_Color( cor )
        self.mask_b3.Set_Alpha( 1 )
        self.Update_Panel_Mask()
        Krita.instance().writeSetting( DOCKER_NAME, "mask_color", str( self.mask_color ) )
    def Mask_Save_D1( self, SIGNAL_SAVE ):
        cor = self.cor["hex6"]
        self.mask_color["d1"] = cor
        self.mask_d1.Set_Color( cor )
        self.mask_d1.Set_Alpha( 1 )
        self.Update_Panel_Mask()
        Krita.instance().writeSetting( DOCKER_NAME, "mask_color", str( self.mask_color ) )
    def Mask_Save_D2( self, SIGNAL_SAVE ):
        cor = self.cor["hex6"]
        self.mask_color["d2"] = cor
        self.mask_d2.Set_Color( cor )
        self.mask_d2.Set_Alpha( 1 )
        self.Update_Panel_Mask()
        Krita.instance().writeSetting( DOCKER_NAME, "mask_color", str( self.mask_color ) )
    def Mask_Save_D3( self, SIGNAL_SAVE ):
        cor = self.cor["hex6"]
        self.mask_color["d3"] = cor
        self.mask_d3.Set_Color( cor )
        self.mask_d3.Set_Alpha( 1 )
        self.Update_Panel_Mask()
        Krita.instance().writeSetting( DOCKER_NAME, "mask_color", str( self.mask_color ) )
    def Mask_Save_D4( self, SIGNAL_SAVE ):
        cor = self.cor["hex6"]
        self.mask_color["d4"] = cor
        self.mask_d4.Set_Color( cor )
        self.mask_d4.Set_Alpha( 1 )
        self.Update_Panel_Mask()
        Krita.instance().writeSetting( DOCKER_NAME, "mask_color", str( self.mask_color ) )
    def Mask_Save_D5( self, SIGNAL_SAVE ):
        cor = self.cor["hex6"]
        self.mask_color["d5"] = cor
        self.mask_d5.Set_Color( cor )
        self.mask_d5.Set_Alpha( 1 )
        self.Update_Panel_Mask()
        Krita.instance().writeSetting( DOCKER_NAME, "mask_color", str( self.mask_color ) )
    def Mask_Save_D6( self, SIGNAL_SAVE ):
        cor = self.cor["hex6"]
        self.mask_color["d6"] = cor
        self.mask_d6.Set_Color( cor )
        self.mask_d6.Set_Alpha( 1 )
        self.Update_Panel_Mask()
        Krita.instance().writeSetting( DOCKER_NAME, "mask_color", str( self.mask_color ) )
    def Mask_Save_F1( self, SIGNAL_SAVE ):
        cor = self.cor["hex6"]
        self.mask_color["f1"] = cor
        self.mask_f1.Set_Color( cor )
        self.mask_f1.Set_Alpha( 1 )
        self.Update_Panel_Mask()
        Krita.instance().writeSetting( DOCKER_NAME, "mask_color", str( self.mask_color ) )
    def Mask_Save_F2( self, SIGNAL_SAVE ):
        cor = self.cor["hex6"]
        self.mask_color["f2"] = cor
        self.mask_f2.Set_Color( cor )
        self.mask_f2.Set_Alpha( 1 )
        self.Update_Panel_Mask()
        Krita.instance().writeSetting( DOCKER_NAME, "mask_color", str( self.mask_color ) )
    def Mask_Save_F3( self, SIGNAL_SAVE ):
        cor = self.cor["hex6"]
        self.mask_color["f3"] = cor
        self.mask_f3.Set_Color( cor )
        self.mask_f3.Set_Alpha( 1 )
        self.Update_Panel_Mask()
        Krita.instance().writeSetting( DOCKER_NAME, "mask_color", str( self.mask_color ) )
    # Clean
    def Mask_Clean_B1( self, SIGNAL_CLEAN ):
        cor = "#000000"
        self.mask_color["b1"] = cor
        self.mask_alpha["b1"] = 0
        self.mask_b1.Set_Color( cor )
        self.mask_b1.Set_Alpha( 0 )
        self.Update_Panel_Mask()
        Krita.instance().writeSetting( DOCKER_NAME, "mask_color", str( self.mask_color ) )
        Krita.instance().writeSetting( DOCKER_NAME, "mask_alpha", str( self.mask_alpha ) )
    def Mask_Clean_B2( self, SIGNAL_CLEAN ):
        cor = "#000000"
        self.mask_color["b2"] = cor
        self.mask_alpha["b2"] = 0
        self.mask_b2.Set_Color( cor )
        self.mask_b2.Set_Alpha( 0 )
        self.Update_Panel_Mask()
        Krita.instance().writeSetting( DOCKER_NAME, "mask_color", str( self.mask_color ) )
        Krita.instance().writeSetting( DOCKER_NAME, "mask_alpha", str( self.mask_alpha ) )
    def Mask_Clean_B3( self, SIGNAL_CLEAN ):
        cor = "#000000"
        self.mask_color["b3"] = cor
        self.mask_alpha["b3"] = 0
        self.mask_b3.Set_Color( cor )
        self.mask_b3.Set_Alpha( 0 )
        self.Update_Panel_Mask()
        Krita.instance().writeSetting( DOCKER_NAME, "mask_color", str( self.mask_color ) )
        Krita.instance().writeSetting( DOCKER_NAME, "mask_alpha", str( self.mask_alpha ) )
    def Mask_Clean_D1( self, SIGNAL_CLEAN ):
        cor = "#000000"
        self.mask_color["d1"] = cor
        self.mask_alpha["d1"] = 0
        self.mask_d1.Set_Color( cor )
        self.mask_d1.Set_Alpha( 0 )
        self.Update_Panel_Mask()
        Krita.instance().writeSetting( DOCKER_NAME, "mask_color", str( self.mask_color ) )
        Krita.instance().writeSetting( DOCKER_NAME, "mask_alpha", str( self.mask_alpha ) )
    def Mask_Clean_D2( self, SIGNAL_CLEAN ):
        cor = "#000000"
        self.mask_color["d2"] = cor
        self.mask_alpha["d2"] = 0
        self.mask_d2.Set_Color( cor )
        self.mask_d2.Set_Alpha( 0 )
        self.Update_Panel_Mask()
        Krita.instance().writeSetting( DOCKER_NAME, "mask_color", str( self.mask_color ) )
        Krita.instance().writeSetting( DOCKER_NAME, "mask_alpha", str( self.mask_alpha ) )
    def Mask_Clean_D3( self, SIGNAL_CLEAN ):
        cor = "#000000"
        self.mask_color["d3"] = cor
        self.mask_alpha["d3"] = 0
        self.mask_d3.Set_Color( cor )
        self.mask_d3.Set_Alpha( 0 )
        self.Update_Panel_Mask()
        Krita.instance().writeSetting( DOCKER_NAME, "mask_color", str( self.mask_color ) )
        Krita.instance().writeSetting( DOCKER_NAME, "mask_alpha", str( self.mask_alpha ) )
    def Mask_Clean_D4( self, SIGNAL_CLEAN ):
        cor = "#000000"
        self.mask_color["d4"] = cor
        self.mask_alpha["d4"] = 0
        self.mask_d4.Set_Color( cor )
        self.mask_d4.Set_Alpha( 0 )
        self.Update_Panel_Mask()
        Krita.instance().writeSetting( DOCKER_NAME, "mask_color", str( self.mask_color ) )
        Krita.instance().writeSetting( DOCKER_NAME, "mask_alpha", str( self.mask_alpha ) )
    def Mask_Clean_D5( self, SIGNAL_CLEAN ):
        cor = "#000000"
        self.mask_color["d5"] = cor
        self.mask_alpha["d5"] = 0
        self.mask_d5.Set_Color( cor )
        self.mask_d5.Set_Alpha( 0 )
        self.Update_Panel_Mask()
        Krita.instance().writeSetting( DOCKER_NAME, "mask_color", str( self.mask_color ) )
        Krita.instance().writeSetting( DOCKER_NAME, "mask_alpha", str( self.mask_alpha ) )
    def Mask_Clean_D6( self, SIGNAL_CLEAN ):
        cor = "#000000"
        self.mask_color["d6"] = cor
        self.mask_alpha["d6"] = 0
        self.mask_d6.Set_Color( cor )
        self.mask_d6.Set_Alpha( 0 )
        self.Update_Panel_Mask()
        Krita.instance().writeSetting( DOCKER_NAME, "mask_color", str( self.mask_color ) )
        Krita.instance().writeSetting( DOCKER_NAME, "mask_alpha", str( self.mask_alpha ) )
    def Mask_Clean_F1( self, SIGNAL_CLEAN ):
        cor = "#000000"
        self.mask_color["f1"] = cor
        self.mask_alpha["f1"] = 0
        self.mask_f1.Set_Color( cor )
        self.mask_f1.Set_Alpha( 0 )
        self.Update_Panel_Mask()
        Krita.instance().writeSetting( DOCKER_NAME, "mask_color", str( self.mask_color ) )
        Krita.instance().writeSetting( DOCKER_NAME, "mask_alpha", str( self.mask_alpha ) )
    def Mask_Clean_F2( self, SIGNAL_CLEAN ):
        cor = "#000000"
        self.mask_color["f2"] = cor
        self.mask_alpha["f2"] = 0
        self.mask_f2.Set_Color( cor )
        self.mask_f2.Set_Alpha( 0 )
        self.Update_Panel_Mask()
        Krita.instance().writeSetting( DOCKER_NAME, "mask_color", str( self.mask_color ) )
        Krita.instance().writeSetting( DOCKER_NAME, "mask_alpha", str( self.mask_alpha ) )
    def Mask_Clean_F3( self, SIGNAL_CLEAN ):
        cor = "#000000"
        self.mask_color["f3"] = cor
        self.mask_alpha["f3"] = 0
        self.mask_f3.Set_Color( cor )
        self.mask_f3.Set_Alpha( 0 )
        self.Update_Panel_Mask()
        Krita.instance().writeSetting( DOCKER_NAME, "mask_color", str( self.mask_color ) )
        Krita.instance().writeSetting( DOCKER_NAME, "mask_alpha", str( self.mask_alpha ) )
    # Alpha
    def Mask_Alpha_B1( self, SIGNAL_ALPHA ):
        self.mask_alpha["b1"] = SIGNAL_ALPHA
        self.Update_Panel_Mask()
        Krita.instance().writeSetting( DOCKER_NAME, "mask_alpha", str( self.mask_alpha ) )
    def Mask_Alpha_B2( self, SIGNAL_ALPHA ):
        self.mask_alpha["b2"] = SIGNAL_ALPHA
        self.Update_Panel_Mask()
        Krita.instance().writeSetting( DOCKER_NAME, "mask_alpha", str( self.mask_alpha ) )
    def Mask_Alpha_B3( self, SIGNAL_ALPHA ):
        self.mask_alpha["b3"] = SIGNAL_ALPHA
        self.Update_Panel_Mask()
        Krita.instance().writeSetting( DOCKER_NAME, "mask_alpha", str( self.mask_alpha ) )
    def Mask_Alpha_D1( self, SIGNAL_ALPHA ):
        self.mask_alpha["d1"] = SIGNAL_ALPHA
        self.Update_Panel_Mask()
        Krita.instance().writeSetting( DOCKER_NAME, "mask_alpha", str( self.mask_alpha ) )
    def Mask_Alpha_D2( self, SIGNAL_ALPHA ):
        self.mask_alpha["d2"] = SIGNAL_ALPHA
        self.Update_Panel_Mask()
        Krita.instance().writeSetting( DOCKER_NAME, "mask_alpha", str( self.mask_alpha ) )
    def Mask_Alpha_D3( self, SIGNAL_ALPHA ):
        self.mask_alpha["d3"] = SIGNAL_ALPHA
        self.Update_Panel_Mask()
        Krita.instance().writeSetting( DOCKER_NAME, "mask_alpha", str( self.mask_alpha ) )
    def Mask_Alpha_D4( self, SIGNAL_ALPHA ):
        self.mask_alpha["d4"] = SIGNAL_ALPHA
        self.Update_Panel_Mask()
        Krita.instance().writeSetting( DOCKER_NAME, "mask_alpha", str( self.mask_alpha ) )
    def Mask_Alpha_D5( self, SIGNAL_ALPHA ):
        self.mask_alpha["d5"] = SIGNAL_ALPHA
        self.Update_Panel_Mask()
        Krita.instance().writeSetting( DOCKER_NAME, "mask_alpha", str( self.mask_alpha ) )
    def Mask_Alpha_D6( self, SIGNAL_ALPHA ):
        self.mask_alpha["d6"] = SIGNAL_ALPHA
        self.Update_Panel_Mask()
        Krita.instance().writeSetting( DOCKER_NAME, "mask_alpha", str( self.mask_alpha ) )
    def Mask_Alpha_F1( self, SIGNAL_ALPHA ):
        self.mask_alpha["f1"] = SIGNAL_ALPHA
        self.Update_Panel_Mask()
        Krita.instance().writeSetting( DOCKER_NAME, "mask_alpha", str( self.mask_alpha ) )
    def Mask_Alpha_F2( self, SIGNAL_ALPHA ):
        self.mask_alpha["f2"] = SIGNAL_ALPHA
        self.Update_Panel_Mask()
        Krita.instance().writeSetting( DOCKER_NAME, "mask_alpha", str( self.mask_alpha ) )
    def Mask_Alpha_F3( self, SIGNAL_ALPHA ):
        self.mask_alpha["f3"] = SIGNAL_ALPHA
        self.Update_Panel_Mask()
        Krita.instance().writeSetting( DOCKER_NAME, "mask_alpha", str( self.mask_alpha ) )

    #endregion
    #region Channel Sliders

    # AAA
    def Channel_AAA_1_Slider( self, index, value ):
        self.Pigmento_PRESS( "A", value, 0, 0, 0, self.cor )
    # RGB
    def Channel_RGB_1_Slider( self, index, value ):
        self.Pigmento_PRESS( "RGB", value, self.cor["rgb_2"], self.cor["rgb_3"], 0, self.cor )
    def Channel_RGB_2_Slider( self, index, value ):
        self.Pigmento_PRESS( "RGB", self.cor["rgb_1"], value, self.cor["rgb_3"], 0, self.cor )
    def Channel_RGB_3_Slider( self, index, value ):
        self.Pigmento_PRESS( "RGB", self.cor["rgb_1"], self.cor["rgb_2"], value, 0, self.cor )
    # CMY
    def Channel_CMY_1_Slider( self, index, value ):
        self.Pigmento_PRESS( "CMY", value, self.cor["cmy_2"], self.cor["cmy_3"], 0, self.cor )
    def Channel_CMY_2_Slider( self, index, value ):
        self.Pigmento_PRESS( "CMY", self.cor["cmy_1"], value, self.cor["cmy_3"], 0, self.cor )
    def Channel_CMY_3_Slider( self, index, value ):
        self.Pigmento_PRESS( "CMY", self.cor["cmy_1"], self.cor["cmy_2"], value, 0, self.cor )
    # CMYK
    def Channel_CMYK_1_Slider( self, index, value ):
        self.Pigmento_PRESS( "CMYK", value, self.cor["cmyk_2"], self.cor["cmyk_3"], self.cor["cmyk_4"], self.cor )
    def Channel_CMYK_2_Slider( self, index, value ):
        self.Pigmento_PRESS( "CMYK", self.cor["cmyk_1"], value, self.cor["cmyk_3"], self.cor["cmyk_4"], self.cor )
    def Channel_CMYK_3_Slider( self, index, value ):
        self.Pigmento_PRESS( "CMYK", self.cor["cmyk_1"], self.cor["cmyk_2"], value, self.cor["cmyk_4"], self.cor )
    def Channel_CMYK_4_Slider( self, index, value ):
        self.Pigmento_PRESS( "CMYK", self.cor["cmyk_1"], self.cor["cmyk_2"], self.cor["cmyk_3"], value, self.cor )
    # RYB
    def Channel_RYB_1_Slider( self, index, value ):
        self.Pigmento_PRESS( "RYB", value, self.cor["ryb_2"], self.cor["ryb_3"], 0, self.cor )
    def Channel_RYB_2_Slider( self, index, value ):
        self.Pigmento_PRESS( "RYB", self.cor["ryb_1"], value, self.cor["ryb_3"], 0, self.cor )
    def Channel_RYB_3_Slider( self, index, value ):
        self.Pigmento_PRESS( "RYB", self.cor["ryb_1"], self.cor["ryb_2"], value, 0, self.cor )
    # YUV
    def Channel_YUV_1_Slider( self, index, value ):
        self.Pigmento_PRESS( "YUV", value, self.cor["yuv_2"], self.cor["yuv_3"], 0, self.cor )
    def Channel_YUV_2_Slider( self, index, value ):
        self.Pigmento_PRESS( "YUV", self.cor["yuv_1"], value, self.cor["yuv_3"], 0, self.cor )
    def Channel_YUV_3_Slider( self, index, value ):
        self.Pigmento_PRESS( "YUV", self.cor["yuv_1"], self.cor["yuv_2"], value, 0, self.cor )

    # HSV
    def Channel_HSV_1_Slider( self, index, value ):
        self.Pigmento_PRESS( "HSV", value, self.cor["hsv_2"], self.cor["hsv_3"], 0, self.cor )
    def Channel_HSV_2_Slider( self, index, value ):
        self.Pigmento_PRESS( "HSV", self.cor["hsv_1"], value, self.cor["hsv_3"], 0, self.cor )
    def Channel_HSV_3_Slider( self, index, value ):
        self.Pigmento_PRESS( "HSV", self.cor["hsv_1"], self.cor["hsv_2"], value, 0, self.cor )
    # HSL
    def Channel_HSL_1_Slider( self, index, value ):
        self.Pigmento_PRESS( "HSL", value, self.cor["hsl_2"], self.cor["hsl_3"], 0, self.cor )
    def Channel_HSL_2_Slider( self, index, value ):
        self.Pigmento_PRESS( "HSL", self.cor["hsl_1"], value, self.cor["hsl_3"], 0, self.cor )
    def Channel_HSL_3_Slider( self, index, value ):
        self.Pigmento_PRESS( "HSL", self.cor["hsl_1"], self.cor["hsl_2"], value, 0, self.cor )
    # HCY
    def Channel_HCY_1_Slider( self, index, value ):
        self.Pigmento_PRESS( "HCY", value, self.cor["hcy_2"], self.cor["hcy_3"], 0, self.cor )
    def Channel_HCY_2_Slider( self, index, value ):
        self.Pigmento_PRESS( "HCY", self.cor["hcy_1"], value, self.cor["hcy_3"], 0, self.cor )
    def Channel_HCY_3_Slider( self, index, value ):
        self.Pigmento_PRESS( "HCY", self.cor["hcy_1"], self.cor["hcy_2"], value, 0, self.cor )
    # ARD
    def Channel_ARD_1_Slider( self, index, value ):
        self.Pigmento_PRESS( "ARD", value, self.cor["ard_2"], self.cor["ard_3"], 0, self.cor )
    def Channel_ARD_2_Slider( self, index, value ):
        self.Pigmento_PRESS( "ARD", self.cor["ard_1"], value, self.cor["ard_3"], 0, self.cor )
    def Channel_ARD_3_Slider( self, index, value ):
        self.Pigmento_PRESS( "ARD", self.cor["ard_1"], self.cor["ard_2"], value, 0, self.cor )

    # XYZ
    def Channel_XYZ_1_Slider( self, index, value ):
        self.Pigmento_PRESS( "XYZ", value, self.cor["xyz_2"], self.cor["xyz_3"], 0, self.cor )
    def Channel_XYZ_2_Slider( self, index, value ):
        self.Pigmento_PRESS( "XYZ", self.cor["xyz_1"], value, self.cor["xyz_3"], 0, self.cor )
    def Channel_XYZ_3_Slider( self, index, value ):
        self.Pigmento_PRESS( "XYZ", self.cor["xyz_1"], self.cor["xyz_2"], value, 0, self.cor )
    # XYY
    def Channel_XYY_1_Slider( self, index, value ):
        self.Pigmento_PRESS( "XYY", value, self.cor["xyy_2"], self.cor["xyy_3"], 0, self.cor )
    def Channel_XYY_2_Slider( self, index, value ):
        self.Pigmento_PRESS( "XYY", self.cor["xyy_1"], value, self.cor["xyy_3"], 0, self.cor )
    def Channel_XYY_3_Slider( self, index, value ):
        self.Pigmento_PRESS( "XYY", self.cor["xyy_1"], self.cor["xyy_2"], value, 0, self.cor )
    # LAB
    def Channel_LAB_1_Slider( self, index, value ):
        self.Pigmento_PRESS( "LAB", value, self.cor["lab_2"], self.cor["lab_3"], 0, self.cor )
    def Channel_LAB_2_Slider( self, index, value ):
        self.Pigmento_PRESS( "LAB", self.cor["lab_1"], value, self.cor["lab_3"], 0, self.cor )
    def Channel_LAB_3_Slider( self, index, value ):
        self.Pigmento_PRESS( "LAB", self.cor["lab_1"], self.cor["lab_2"], value, 0, self.cor )

    # LCH
    def Channel_LCH_1_Slider( self, index, value ):
        self.Pigmento_PRESS( "LCH", value, self.cor["lch_2"], self.cor["lch_3"], 0, self.cor )
    def Channel_LCH_2_Slider( self, index, value ):
        self.Pigmento_PRESS( "LCH", self.cor["lch_1"], value, self.cor["lch_3"], 0, self.cor )
    def Channel_LCH_3_Slider( self, index, value ):
        self.Pigmento_PRESS( "LCH", self.cor["lch_1"], self.cor["lch_2"], value, 0, self.cor )

    #endregion
    #region Channel Stops

    # AAA
    def Channel_AAA_1_Stops( self, ss ):
        stops["aaa_1"] = ss
        Krita.instance().writeSetting( DOCKER_NAME, "stops", str( stops ) )
    # RGB
    def Channel_RGB_1_Stops( self, ss ):
        stops["rgb_1"] = ss
        Krita.instance().writeSetting( DOCKER_NAME, "stops", str( stops ) )
    def Channel_RGB_2_Stops( self, ss ):
        stops["rgb_2"] = ss
        Krita.instance().writeSetting( DOCKER_NAME, "stops", str( stops ) )
    def Channel_RGB_3_Stops( self, ss ):
        stops["rgb_3"] = ss
        Krita.instance().writeSetting( DOCKER_NAME, "stops", str( stops ) )
    # CMY
    def Channel_CMY_1_Stops( self, ss ):
        stops["cmy_1"] = ss
        Krita.instance().writeSetting( DOCKER_NAME, "stops", str( stops ) )
    def Channel_CMY_2_Stops( self, ss ):
        stops["cmy_2"] = ss
        Krita.instance().writeSetting( DOCKER_NAME, "stops", str( stops ) )
    def Channel_CMY_3_Stops( self, ss ):
        stops["cmy_3"] = ss
        Krita.instance().writeSetting( DOCKER_NAME, "stops", str( stops ) )
    # CMYK
    def Channel_CMYK_1_Stops( self, ss ):
        stops["cmyk_1"] = ss
        Krita.instance().writeSetting( DOCKER_NAME, "stops", str( stops ) )
    def Channel_CMYK_2_Stops( self, ss ):
        stops["cmyk_2"] = ss
        Krita.instance().writeSetting( DOCKER_NAME, "stops", str( stops ) )
    def Channel_CMYK_3_Stops( self, ss ):
        stops["cmyk_3"] = ss
        Krita.instance().writeSetting( DOCKER_NAME, "stops", str( stops ) )
    def Channel_CMYK_4_Stops( self, ss ):
        stops["cmyk_4"] = ss
        Krita.instance().writeSetting( DOCKER_NAME, "stops", str( stops ) )
    # RYB
    def Channel_RYB_1_Stops( self, ss ):
        stops["ryb_1"] = ss
        Krita.instance().writeSetting( DOCKER_NAME, "stops", str( stops ) )
    def Channel_RYB_2_Stops( self, ss ):
        stops["ryb_2"] = ss
        Krita.instance().writeSetting( DOCKER_NAME, "stops", str( stops ) )
    def Channel_RYB_3_Stops( self, ss ):
        stops["ryb_3"] = ss
        Krita.instance().writeSetting( DOCKER_NAME, "stops", str( stops ) )
    # YUV
    def Channel_YUV_1_Stops( self, ss ):
        stops["yuv_1"] = ss
        Krita.instance().writeSetting( DOCKER_NAME, "stops", str( stops ) )
    def Channel_YUV_2_Stops( self, ss ):
        stops["yuv_2"] = ss
        Krita.instance().writeSetting( DOCKER_NAME, "stops", str( stops ) )
    def Channel_YUV_3_Stops( self, ss ):
        stops["yuv_3"] = ss
        Krita.instance().writeSetting( DOCKER_NAME, "stops", str( stops ) )

    # HSV
    def Channel_HSV_1_Stops( self, ss ):
        stops["hsv_1"] = ss
        Krita.instance().writeSetting( DOCKER_NAME, "stops", str( stops ) )
    def Channel_HSV_2_Stops( self, ss ):
        stops["hsv_2"] = ss
        Krita.instance().writeSetting( DOCKER_NAME, "stops", str( stops ) )
    def Channel_HSV_3_Stops( self, ss ):
        stops["hsv_3"] = ss
        Krita.instance().writeSetting( DOCKER_NAME, "stops", str( stops ) )
    # HSL
    def Channel_HSL_1_Stops( self, ss ):
        stops["hsl_1"] = ss
        Krita.instance().writeSetting( DOCKER_NAME, "stops", str( stops ) )
    def Channel_HSL_2_Stops( self, ss ):
        stops["hsl_2"] = ss
        Krita.instance().writeSetting( DOCKER_NAME, "stops", str( stops ) )
    def Channel_HSL_3_Stops( self, ss ):
        stops["hsl_3"] = ss
        Krita.instance().writeSetting( DOCKER_NAME, "stops", str( stops ) )
    # HCY
    def Channel_HCY_1_Stops( self, ss ):
        stops["hcy_1"] = ss
        Krita.instance().writeSetting( DOCKER_NAME, "stops", str( stops ) )
    def Channel_HCY_2_Stops( self, ss ):
        stops["hcy_2"] = ss
        Krita.instance().writeSetting( DOCKER_NAME, "stops", str( stops ) )
    def Channel_HCY_3_Stops( self, ss ):
        stops["hcy_3"] = ss
        Krita.instance().writeSetting( DOCKER_NAME, "stops", str( stops ) )
    # ARD
    def Channel_ARD_1_Stops( self, ss ):
        stops["ard_1"] = ss
        Krita.instance().writeSetting( DOCKER_NAME, "stops", str( stops ) )
    def Channel_ARD_2_Stops( self, ss ):
        stops["ard_2"] = ss
        Krita.instance().writeSetting( DOCKER_NAME, "stops", str( stops ) )
    def Channel_ARD_3_Stops( self, ss ):
        stops["ard_3"] = ss
        Krita.instance().writeSetting( DOCKER_NAME, "stops", str( stops ) )

    # XYZ
    def Channel_XYZ_1_Stops( self, ss ):
        stops["xyz_1"] = ss
        Krita.instance().writeSetting( DOCKER_NAME, "stops", str( stops ) )
    def Channel_XYZ_2_Stops( self, ss ):
        stops["xyz_2"] = ss
        Krita.instance().writeSetting( DOCKER_NAME, "stops", str( stops ) )
    def Channel_XYZ_3_Stops( self, ss ):
        stops["xyz_3"] = ss
        Krita.instance().writeSetting( DOCKER_NAME, "stops", str( stops ) )
    # XYY
    def Channel_XYY_1_Stops( self, ss ):
        stops["xyy_1"] = ss
        Krita.instance().writeSetting( DOCKER_NAME, "stops", str( stops ) )
    def Channel_XYY_2_Stops( self, ss ):
        stops["xyy_2"] = ss
        Krita.instance().writeSetting( DOCKER_NAME, "stops", str( stops ) )
    def Channel_XYY_3_Stops( self, ss ):
        stops["xyy_3"] = ss
        Krita.instance().writeSetting( DOCKER_NAME, "stops", str( stops ) )
    # LAB
    def Channel_LAB_1_Stops( self, ss ):
        stops["lab_1"] = ss
        Krita.instance().writeSetting( DOCKER_NAME, "stops", str( stops ) )
    def Channel_LAB_2_Stops( self, ss ):
        stops["lab_2"] = ss
        Krita.instance().writeSetting( DOCKER_NAME, "stops", str( stops ) )
    def Channel_LAB_3_Stops( self, ss ):
        stops["lab_3"] = ss
        Krita.instance().writeSetting( DOCKER_NAME, "stops", str( stops ) )

    # LCH
    def Channel_LCH_1_Stops( self, ss ):
        stops["lch_1"] = ss
        Krita.instance().writeSetting( DOCKER_NAME, "stops", str( stops ) )
    def Channel_LCH_2_Stops( self, ss ):
        stops["lch_2"] = ss
        Krita.instance().writeSetting( DOCKER_NAME, "stops", str( stops ) )
    def Channel_LCH_3_Stops( self, ss ):
        stops["lch_3"] = ss
        Krita.instance().writeSetting( DOCKER_NAME, "stops", str( stops ) )

    #endregion
    #region Channel Values

    # AAA
    def Channel_AAA_1_Value( self, sv ):
        value = sv / krange["aaa_1"]
        self.Pigmento_PRESS( "A", value, 0, 0, 0, self.cor )
        self.Label_String( f"{ round( value * 100, 2 ) } %" )
    # RGB
    def Channel_RGB_1_Value( self, sv ):
        value = sv / krange["rgb_1"]
        self.Pigmento_PRESS( "RGB", value, self.cor["rgb_2"], self.cor["rgb_3"], 0, self.cor )
        self.Label_String( f"{ round( value * 100, 2 ) } %" )
    def Channel_RGB_2_Value( self, sv ):
        value = sv / krange["rgb_2"]
        self.Pigmento_PRESS( "RGB", self.cor["rgb_1"], value, self.cor["rgb_3"], 0, self.cor )
        self.Label_String( f"{ round( value * 100, 2 ) } %" )
    def Channel_RGB_3_Value( self, sv ):
        value = sv / krange["rgb_3"]
        self.Pigmento_PRESS( "RGB", self.cor["rgb_1"], self.cor["rgb_2"], value, 0, self.cor )
        self.Label_String( f"{ round( value * 100, 2 ) } %" )
    # CMY
    def Channel_CMY_1_Value( self, sv ):
        value = sv / krange["cmy_1"]
        self.Pigmento_PRESS( "CMY", value, self.cor["cmy_2"], self.cor["cmy_3"], 0, self.cor )
        self.Label_String( f"{ round( value * 100, 2 ) } %" )
    def Channel_CMY_2_Value( self, sv ):
        value = sv / krange["cmy_2"]
        self.Pigmento_PRESS( "CMY", self.cor["cmy_1"], value, self.cor["cmy_3"], 0, self.cor )
        self.Label_String( f"{ round( value * 100, 2 ) } %" )
    def Channel_CMY_3_Value( self, sv ):
        value = sv / krange["cmy_3"]
        self.Pigmento_PRESS( "CMY", self.cor["cmy_1"], self.cor["cmy_2"], value, 0, self.cor )
        self.Label_String( f"{ round( value * 100, 2 ) } %" )
    # CMYK
    def Channel_CMYK_1_Value( self, sv ):
        value = sv / krange["cmyk_1"]
        self.Pigmento_PRESS( "CMYK", value, self.cor["cmyk_2"], self.cor["cmyk_3"], self.cor["cmyk_4"], self.cor )
        self.Label_String( f"{ round( value * 100, 2 ) } %" )
    def Channel_CMYK_2_Value( self, sv ):
        value = sv / krange["cmyk_2"]
        self.Pigmento_PRESS( "CMYK", self.cor["cmyk_1"], value, self.cor["cmyk_3"], self.cor["cmyk_4"], self.cor )
        self.Label_String( f"{ round( value * 100, 2 ) } %" )
    def Channel_CMYK_3_Value( self, sv ):
        value = sv / krange["cmyk_3"]
        self.Pigmento_PRESS( "CMYK", self.cor["cmyk_1"], self.cor["cmyk_2"], value, self.cor["cmyk_4"], self.cor )
        self.Label_String( f"{ round( value * 100, 2 ) } %" )
    def Channel_CMYK_4_Value( self, sv ):
        value = sv / krange["cmyk_4"]
        self.Pigmento_PRESS( "CMYK", self.cor["cmyk_1"], self.cor["cmyk_2"], self.cor["cmyk_3"], value, self.cor )
        self.Label_String( f"{ round( value * 100, 2 ) } %" )
    # RYB
    def Channel_RYB_1_Value( self, sv ):
        value = sv / krange["ryb_1"]
        self.Pigmento_PRESS( "RYB", value, self.cor["ryb_2"], self.cor["ryb_3"], 0, self.cor )
        self.Label_String( f"{ round( value * 100, 2 ) } %" )
    def Channel_RYB_2_Value( self, sv ):
        value = sv / krange["ryb_2"]
        self.Pigmento_PRESS( "RYB", self.cor["ryb_1"], value, self.cor["ryb_3"], 0, self.cor )
        self.Label_String( f"{ round( value * 100, 2 ) } %" )
    def Channel_RYB_3_Value( self, sv ):
        value = sv / krange["ryb_3"]
        self.Pigmento_PRESS( "RYB", self.cor["ryb_1"], self.cor["ryb_2"], value, 0, self.cor )
        self.Label_String( f"{ round( value * 100, 2 ) } %" )
    # YUV
    def Channel_YUV_1_Value( self, sv ):
        value = sv / krange["yuv_1"]
        self.Pigmento_PRESS( "YUV", value, self.cor["yuv_2"], self.cor["yuv_3"], 0, self.cor )
        self.Label_String( f"{ round( value * 100, 2 ) } %" )
    def Channel_YUV_2_Value( self, sv ):
        value = sv / krange["yuv_2"]
        self.Pigmento_PRESS( "YUV", self.cor["yuv_1"], value, self.cor["yuv_3"], 0, self.cor )
        self.Label_String( f"{ round( value * 100, 2 ) } %" )
    def Channel_YUV_3_Value( self, sv ):
        value = sv / krange["yuv_3"]
        self.Pigmento_PRESS( "YUV", self.cor["yuv_1"], self.cor["yuv_2"], value, 0, self.cor )
        self.Label_String( f"{ round( value * 100, 2 ) } %" )

    # HSV
    def Channel_HSV_1_Value( self, sv ):
        value = sv / krange["hsv_1"]
        self.Pigmento_PRESS( "HSV", value, self.cor["hsv_2"], self.cor["hsv_3"], 0, self.cor )
        self.Label_String( f"{ round( value * 100, 2 ) } %" )
    def Channel_HSV_2_Value( self, sv ):
        value = sv / krange["hsv_2"]
        self.Pigmento_PRESS( "HSV", self.cor["hsv_1"], value, self.cor["hsv_3"], 0, self.cor )
        self.Label_String( f"{ round( value * 100, 2 ) } %" )
    def Channel_HSV_3_Value( self, sv ):
        value = sv / krange["hsv_3"]
        self.Pigmento_PRESS( "HSV", self.cor["hsv_1"], self.cor["hsv_2"], value, 0, self.cor )
        self.Label_String( f"{ round( value * 100, 2 ) } %" )
    # HSL
    def Channel_HSL_1_Value( self, sv ):
        value = sv / krange["hsl_1"]
        self.Pigmento_PRESS( "HSL", value, self.cor["hsl_2"], self.cor["hsl_3"], 0, self.cor )
        self.Label_String( f"{ round( value * 100, 2 ) } %" )
    def Channel_HSL_2_Value( self, sv ):
        value = sv / krange["hsl_2"]
        self.Pigmento_PRESS( "HSL", self.cor["hsl_1"], value, self.cor["hsl_3"], 0, self.cor )
        self.Label_String( f"{ round( value * 100, 2 ) } %" )
    def Channel_HSL_3_Value( self, sv ):
        value = sv / krange["hsl_3"]
        self.Pigmento_PRESS( "HSL", self.cor["hsl_1"], self.cor["hsl_2"], value, 0, self.cor )
        self.Label_String( f"{ round( value * 100, 2 ) } %" )
    # HCY
    def Channel_HCY_1_Value( self, sv ):
        value = sv / krange["hcy_1"]
        self.Pigmento_PRESS( "HCY", value, self.cor["hcy_2"], self.cor["hcy_3"], 0, self.cor )
        self.Label_String( f"{ round( value * 100, 2 ) } %" )
    def Channel_HCY_2_Value( self, sv ):
        value = sv / krange["hcy_2"]
        self.Pigmento_PRESS( "HCY", self.cor["hcy_1"], value, self.cor["hcy_3"], 0, self.cor )
        self.Label_String( f"{ round( value * 100, 2 ) } %" )
    def Channel_HCY_3_Value( self, sv ):
        value = sv / krange["hcy_3"]
        self.Pigmento_PRESS( "HCY", self.cor["hcy_1"], self.cor["hcy_2"], value, 0, self.cor )
        self.Label_String( f"{ round( value * 100, 2 ) } %" )
    # ARD
    def Channel_ARD_1_Value( self, sv ):
        value = sv / krange["ard_1"]
        self.Pigmento_PRESS( "ARD", value, self.cor["ard_2"], self.cor["ard_3"], 0, self.cor )
        self.Label_String( f"{ round( value * 100, 2 ) } %" )
    def Channel_ARD_2_Value( self, sv ):
        value = sv / krange["ard_2"]
        self.Pigmento_PRESS( "ARD", self.cor["ard_1"], value, self.cor["ard_3"], 0, self.cor )
        self.Label_String( f"{ round( value * 100, 2 ) } %" )
    def Channel_ARD_3_Value( self, sv ):
        value = sv / krange["ard_3"]
        self.Pigmento_PRESS( "ARD", self.cor["ard_1"], self.cor["ard_2"], value, 0, self.cor )
        self.Label_String( f"{ round( value * 100, 2 ) } %" )

    # XYZ
    def Channel_XYZ_1_Value( self, sv ):
        value = sv / krange["xyz_1"]
        self.Pigmento_PRESS( "XYZ", value, self.cor["xyz_2"], self.cor["xyz_3"], 0, self.cor )
        self.Label_String( f"{ round( value * 100, 2 ) } %" )
    def Channel_XYZ_2_Value( self, sv ):
        value = sv / krange["xyz_2"]
        self.Pigmento_PRESS( "XYZ", self.cor["xyz_1"], value, self.cor["xyz_3"], 0, self.cor )
        self.Label_String( f"{ round( value * 100, 2 ) } %" )
    def Channel_XYZ_3_Value( self, sv ):
        value = sv / krange["xyz_3"]
        self.Pigmento_PRESS( "XYZ", self.cor["xyz_1"], self.cor["xyz_2"], value, 0, self.cor )
        self.Label_String( f"{ round( value * 100, 2 ) } %" )
    # XYY
    def Channel_XYY_1_Value( self, sv ):
        value = sv / krange["xyy_1"]
        self.Pigmento_PRESS( "XYY", value, self.cor["xyy_2"], self.cor["xyy_3"], 0, self.cor )
        self.Label_String( f"{ round( value * 100, 2 ) } %" )
    def Channel_XYY_2_Value( self, sv ):
        value = sv / krange["xyy_2"]
        self.Pigmento_PRESS( "XYY", self.cor["xyy_1"], value, self.cor["xyy_3"], 0, self.cor )
        self.Label_String( f"{ round( value * 100, 2 ) } %" )
    def Channel_XYY_3_Value( self, sv ):
        value = sv / krange["xyy_3"]
        self.Pigmento_PRESS( "XYY", self.cor["xyy_1"], self.cor["xyy_2"], value, 0, self.cor )
        self.Label_String( f"{ round( value * 100, 2 ) } %" )
    # LAB
    def Channel_LAB_1_Value( self, sv ):
        value = sv / krange["lab_1"]
        self.Pigmento_PRESS( "LAB", value, self.cor["lab_2"], self.cor["lab_3"], 0, self.cor )
        self.Label_String( f"{ round( value * 100, 2 ) } %" )
    def Channel_LAB_2_Value( self, sv ):
        value = sv / krange["lab_2"]
        self.Pigmento_PRESS( "LAB", self.cor["lab_1"], value, self.cor["lab_3"], 0, self.cor )
        self.Label_String( f"{ round( value * 100, 2 ) } %" )
    def Channel_LAB_3_Value( self, sv ):
        value = sv / krange["lab_3"]
        self.Pigmento_PRESS( "LAB", self.cor["lab_1"], self.cor["lab_2"], value, 0, self.cor )
        self.Label_String( f"{ round( value * 100, 2 ) } %" )

    # LCH
    def Channel_LCH_1_Value( self, sv ):
        value = sv / krange["lch_1"]
        self.Pigmento_PRESS( "LCH", value, self.cor["lch_2"], self.cor["lch_3"], 0, self.cor )
        self.Label_String( f"{ round( value * 100, 2 ) } %" )
    def Channel_LCH_2_Value( self, sv ):
        value = sv / krange["lch_2"]
        self.Pigmento_PRESS( "LCH", self.cor["lch_1"], value, self.cor["lch_3"], 0, self.cor )
        self.Label_String( f"{ round( value * 100, 2 ) } %" )
    def Channel_LCH_3_Value( self, sv ):
        value = sv / krange["lch_3"]
        self.Pigmento_PRESS( "LCH", self.cor["lch_1"], self.cor["lch_2"], value, 0, self.cor )
        self.Label_String( f"{ round( value * 100, 2 ) } %" )

    #endregion
    #region Channel Kelvin

    # KKK
    def Channel_KKK_1_Slider( self, index, value ):
        percent = value
        scale = self.convert.kkk_percent_to_scale( value )
        self.Pigmento_PRESS( "KKK", percent, scale, 0, 0, self.cor )
    def Channel_KKK_1_Stops( self, ss ):
        stops["kkk_1"] = ss
        Krita.instance().writeSetting( DOCKER_NAME, "stops", str( stops ) )
    def Channel_KKK_1_Value( self, sv ):
        percent = self.convert.kkk_scale_to_percent( sv )
        scale = sv
        self.Pigmento_PRESS( "KKK", percent, scale, 0, 0, self.cor )
        self.Label_String( str( round( percent*100, 2 ) ) + " %" )
    def Kelvin_Class( self, scale ):
        # Variables
        cd = self.convert.kkk_to_cd( scale, kelvin_illuminants )
        # Write
        kelvin["class"] = cd[0]
        kelvin["description"] = cd[1]

    #endregion
    #region Mixer

    # Pole Slider
    def Channel_Pole_Slider( self, index, value ):
        self.pole_percent = value
        ms = self.mixer_space
        factor = 2 * abs( value - 0.5 )
        if value <= 0.5:    cor = self.Color_Interpolate( self.mixer_space, self.pole_cor_n, self.pole_cor_a, 2 * abs( 0.5 - value ) )
        elif value > 0.5:   cor = self.Color_Interpolate( self.mixer_space, self.pole_cor_n, self.pole_cor_b, 2 * abs( value - 0.5 ) )
        self.Pigmento_PRESS( "RGB", cor["rgb_1"], cor["rgb_2"], cor["rgb_3"], 0, self.cor )
        self.Dict_Copy( self.pole_mix, self.cor )
    def Channel_Pole_Stops( self, ss ):
        stops["pole_1"] = ss
        Krita.instance().writeSetting( DOCKER_NAME, "stops", str( stops ) )
    # Pole
    def Pole_LOAD( self, cor_a, cor_b ):
        if cor_a["active"] == True: self.pole_pin_a.Set_Color( cor_a["hex6"] )
        else:                       self.pole_pin_a.Set_Clean()
        if cor_b["active"] == True: self.pole_pin_b.Set_Color( cor_b["hex6"] )
        else:                       self.pole_pin_b.Set_Clean()
    # Pole A
    def Pole_Apply_1A( self ):
        if self.pole_cor_a["active"] == True:
            self.pole_percent = 0
            self.pole_slider.Set_Value( self.pole_percent )
            self.Dict_Copy( self.cor, self.pole_cor_a )
            self.Pigmento_RELEASE()
    def Pole_Save_1A( self ):
        self.Dict_Copy( self.pole_cor_a, self.cor )
        self.pole_pin_a.Set_Color( self.pole_cor_a["hex6"] )
        self.Pigmento_RELEASE()
        Krita.instance().writeSetting( DOCKER_NAME, "pole_cor_a", str( self.pole_cor_a ) )
    def Pole_Clean_1A( self ):
        self.pole_percent = 0.5
        self.pole_slider.Set_Value( self.pole_percent )
        self.Dict_Copy( self.pole_cor_a, self.zorn_white )
        self.pole_pin_a.Set_Color( self.pole_cor_a["hex6"] )
        self.Pigmento_RELEASE()
        Krita.instance().writeSetting( DOCKER_NAME, "pole_cor_a", str( self.pole_cor_a ) )
    # Pole B
    def Pole_Apply_1B( self ):
        if self.pole_cor_b["active"] == True:
            self.pole_percent = 1
            self.pole_slider.Set_Value( self.pole_percent )
            self.Dict_Copy( self.cor, self.pole_cor_b )
            self.Pigmento_RELEASE()
    def Pole_Save_1B( self ):
        self.Dict_Copy( self.pole_cor_b, self.cor )
        self.pole_pin_b.Set_Color( self.pole_cor_b["hex6"] )
        self.Pigmento_RELEASE()
        Krita.instance().writeSetting( DOCKER_NAME, "pole_cor_b", str( self.pole_cor_b ) )
    def Pole_Clean_1B( self ):
        self.pole_percent = 0.5
        self.pole_slider.Set_Value( self.pole_percent )
        self.Dict_Copy( self.pole_cor_b, self.zorn_black )
        self.pole_pin_b.Set_Color( self.pole_cor_b["hex6"] )
        self.Pigmento_RELEASE()
        Krita.instance().writeSetting( DOCKER_NAME, "pole_cor_b", str( self.pole_cor_b ) )
    # Pole Neutral
    def Pole_Neutral( self ):
        self.pole_percent = 0.5
        self.pole_slider.Set_Value( self.pole_percent )
        self.Dict_Copy( self.pole_mix, self.cor )
        self.Dict_Copy( self.pole_cor_n, self.cor )
        self.Channel_Pole_Style()
    def Channel_Pole_Style( self ):
        pole_1 = self.Gradient_Pole( self.mixer_space, False, 8, self.pole_cor_a, self.pole_cor_n, self.pole_cor_b )
        alpha = int( self.pole_cor_a["active"] * self.pole_cor_n["active"] * self.pole_cor_b["active"] )
        self.pole_slider.Set_Colors( pole_1, alpha )

    # Load
    def Mixer_LOAD( self ):
        # Render
        length = len( self.mixer_colors )
        for i in range( 0, length ):
            # Variables
            item = self.mixer_colors[i]
            al = item["l"]["active"]
            ar = item["r"]["active"]
            # Modules
            if al == True:
                try:self.mixer_module[i]["l"].Set_Color( item["l"]["hex6"] )
                except:pass
            if ar == True:
                try:self.mixer_module[i]["r"].Set_Color( item["r"]["hex6"] )
                except:pass
            try:self.mixer_module[i]["m"].Set_Value( item["m"] )
            except:pass
    # Pin LEFT
    def Mixer_Apply_L( self, index ):
        if self.mixer_colors[index]["l"]["active"] == True:
            self.Dict_Copy( self.cor, self.mixer_colors[index]["l"] )
            self.Pigmento_RELEASE()
    def Mixer_Save_L( self, index ):
        self.Dict_Copy( self.mixer_colors[index]["l"], self.cor )
        self.mixer_module[index]["l"].Set_Color( self.cor["hex6"] )
        self.Pigmento_RELEASE()
        Krita.instance().writeSetting( DOCKER_NAME, "mixer_colors", str( self.mixer_colors ) )
    def Mixer_Clean_L( self, index ):
        self.Dict_Copy( self.mixer_colors[index]["l"], color_false )
        self.mixer_module[index]["l"].Set_Clean()
        self.Pigmento_RELEASE()
        Krita.instance().writeSetting( DOCKER_NAME, "mixer_colors", str( self.mixer_colors ) )
    # Pin RIGHT
    def Mixer_Apply_R( self, index ):
        if self.mixer_colors[index]["r"]["active"] == True:
            self.Dict_Copy( self.cor, self.mixer_colors[index]["r"] )
            self.Pigmento_RELEASE()
    def Mixer_Save_R( self, index ):
        self.Dict_Copy( self.mixer_colors[index]["r"], self.cor )
        self.mixer_module[index]["r"].Set_Color( self.cor["hex6"] )
        self.Pigmento_RELEASE()
        Krita.instance().writeSetting( DOCKER_NAME, "mixer_colors", str( self.mixer_colors ) )
    def Mixer_Clean_R( self, index ):
        self.Dict_Copy( self.mixer_colors[index]["r"], color_false )
        self.mixer_module[index]["r"].Set_Clean()
        self.Pigmento_RELEASE()
        Krita.instance().writeSetting( DOCKER_NAME, "mixer_colors", str( self.mixer_colors ) )
    # Slider
    def Mixer_Slider_M( self, index, value ):
        mode = self.mixer_space
        self.mixer_colors[index]["m"] = value
        al = self.mixer_colors[index]["l"]["active"]
        ar = self.mixer_colors[index]["r"]["active"]
        if ( al == True and ar == True ):
            color = self.Color_Interpolate( mode, self.mixer_colors[index]["l"], self.mixer_colors[index]["r"], value )
            if mode == "A":     self.Pigmento_PRESS( mode, color["aaa_1"], 0, 0, 0, self.cor )
            if mode == "RGB":   self.Pigmento_PRESS( mode, color["rgb_1"], color["rgb_2"], color["rgb_3"], 0, self.cor )
            if mode == "CMY":   self.Pigmento_PRESS( mode, color["cmy_1"], color["cmy_2"], color["cmy_3"], 0, self.cor )
            if mode == "CMYK":  self.Pigmento_PRESS( mode, color["cmyk_1"], color["cmyk_2"], color["cmyk_3"], color["cmyk_4"], self.cor )
            if mode == "RYB":   self.Pigmento_PRESS( mode, color["ryb_1"], color["ryb_2"], color["ryb_3"], 0, self.cor )
            if mode == "YUV":   self.Pigmento_PRESS( mode, color["yuv_1"], color["yuv_2"], color["yuv_3"], 0, self.cor )
            if mode == "HSV":   self.Pigmento_PRESS( mode, color["hsv_1"], color["hsv_2"], color["hsv_3"], 0, self.cor )
            if mode == "HSL":   self.Pigmento_PRESS( mode, color["hsl_1"], color["hsl_2"], color["hsl_3"], 0, self.cor )
            if mode == "HCY":   self.Pigmento_PRESS( mode, color["hcy_1"], color["hcy_2"], color["hcy_3"], 0, self.cor )
            if mode == "ARD":   self.Pigmento_PRESS( mode, color["ard_1"], color["ard_2"], color["ard_3"], 0, self.cor )
            if mode == "XYZ":   self.Pigmento_PRESS( mode, color["xyz_1"], color["xyz_2"], color["xyz_3"], 0, self.cor )
            if mode == "XYY":   self.Pigmento_PRESS( mode, color["xyy_1"], color["xyy_2"], color["xyy_3"], 0, self.cor )
            if mode == "LAB":   self.Pigmento_PRESS( mode, color["lab_1"], color["lab_2"], color["lab_3"], 0, self.cor )
            if mode == "LCH":   self.Pigmento_PRESS( mode, color["lch_1"], color["lch_2"], color["lch_3"], 0, self.cor )
        Krita.instance().writeSetting( DOCKER_NAME, "mixer_colors", str( self.mixer_colors ) )
    def Mixer_Stops_M( self, ss ):
        stops["mixer"] = ss
        Krita.instance().writeSetting( DOCKER_NAME, "stops", str( stops ) )

    #endregion
    #region Pin

    def Pin_LOAD( self ):
        for i in range( 0, len( self.pin_cor ) ):
            if self.pin_cor[i]["active"] == True:
                self.pin_module[i].Set_Color( self.pin_cor[i]["hex6"] )
            else:
                self.pin_module[i].Set_Clean()
    def Pin_Apply( self, index ):
        if index in range( 0, len( self.pin_cor ) ):
            if self.pin_cor[index]["active"] == True:
                self.Dict_Copy( self.cor, self.pin_cor[index] )
                self.Pigmento_RELEASE()
    def Pin_Save( self, index ):
        self.Dict_Copy( self.pin_cor[index], self.cor )
        self.pin_module[index].Set_Color( self.pin_cor[index]["hex6"] )
        self.Pigmento_RELEASE()
        Krita.instance().writeSetting( DOCKER_NAME, "pin_cor", str( self.pin_cor ) )
    def Pin_Clean( self, index ):
        self.Dict_Copy( self.pin_cor[index], color_false )
        self.pin_module[index].Set_Clean()
        self.Pigmento_RELEASE()
        Krita.instance().writeSetting( DOCKER_NAME, "pin_cor", str( self.pin_cor ) )

    #endregion
    #region History

    def History_List( self, red, green, blue ):
        # Last Entry
        last_item = self.layout.history_list.item( 0 )
        if last_item == None:
            self.History_Add( red, green, blue )
        else:
            if ( self.widget_press == False and self.cursor_inside == False ):
                # Input Color
                input_r = int( red * 255 )
                input_g = int( green * 255 )
                input_b = int( blue * 255 )
                # Last Colors
                last_color = last_item.background().color()
                last_r = int( last_color.red() )
                last_g = int( last_color.green() )
                last_b = int( last_color.blue() )
                # Apply Colors Values
                if ( input_r != last_r ) or ( input_g != last_g ) or ( input_b != last_b ):
                    self.History_Add( red, green, blue )
                    self.HEX_Copy( self.cor["hex6"] )
    def History_Add( self, red, green, blue ):
        color = QColor( int( red * 255 ), int( green * 255 ), int( blue * 255 ) )
        pixmap = QPixmap( 10,20 )
        pixmap.fill( color )
        item = QListWidgetItem()
        item.setIcon( QIcon( pixmap ) )
        item.setBackground( QBrush( color ) )
        self.layout.history_list.insertItem( 0, item )
    def History_APPLY( self ):
        current = self.layout.history_list.currentItem()
        color = current.background().color()
        red = color.red() / 255
        green = color.green() / 255
        blue = color.blue() / 255
        self.Pigmento_APPLY( "RGB", red, green, blue, 0, self.cor )
    def History_CLEAR( self ):
        self.layout.history_list.clear()

    #endregion
    #region Fill Pixels

    def Fill_Check( self, doc ):
        try:
            check_alpha = Krita.instance().activeDocument().nodeByUniqueID( fill["node_uid"] ).alphaLocked()
            check_fill = fill["active"] == True and fill["node_uid"] == doc["n_uid"] and check_alpha == True
        except:
            check_fill = False
        return check_fill
    def Fill_None( self ):
        # Layers
        try:
            node = Krita.instance().activeDocument().nodeByUniqueID( fill["node_uid"] )
            try:node.setAlphaLocked( fill["alphalock_before"] )
            except:node.setAlphaLocked( False )
            else:pass
        except:
            pass
        # Variables
        fill["active"] = False
        fill["node_uid"] = None
        fill["alphalock_before"] = None
        # UI
        self.layout.fill.blockSignals( True )
        self.layout.fill.setIcon( Krita.instance().icon( "folder-documents" ) )
        self.layout.fill.setChecked( False )
        self.layout.fill.blockSignals( False )

    #endregion
    #region HEX Codes

    # Copy-Paste
    def HEX_Copy( self, hex_code ):
        clip_board = QApplication.clipboard()
        clip_board.setText( str( hex_code ) )
    def HEX_Paste( self ):
        clip_board = QApplication.clipboard()
        hex_code = clip_board.text()
        check_hex6 = self.HEX_Valid( hex_code, 6 )
        check_hex3 = self.HEX_Valid( hex_code, 3 )
        if check_hex6 == True or check_hex3 == True:
            self.Color_HEX( hex_code )

    # Operators
    def HEX_Valid( self, hex_code, length ):
        if ( hex_code == "" or hex_code == None ):
            return False
        else:
            # Variables
            valid = ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "a", "b", "c", "d", "e", "f", "A", "B", "C", "D", "E", "F"]
            # Checks
            checks = []
            if hex_code[0] == "#":
                hex_code = hex_code[1:]
                checks.append( True )
            if len( hex_code ) == length:
                for i in range( 0, len( hex_code ) ):
                    if hex_code[i] in valid:
                        checks.append( True )
                    else:
                        checks.append( False )
            else:
                checks.append( False )
            # Validity
            valid = True
            for i in range( 0, len( checks ) ):
                if checks[i] == False:
                    valid = False
                    break
            # Return
            return valid
    def HEX_Closest( self ):
        # Original HEX Point
        hex_start = self.cor["hex6"]
        ps = self.convert.hex6_to_rgb( hex_start )
        # Calculate Distances
        lista = list( color_names )
        index = [0,5]
        for i in range( len( lista ) ):
            pe = self.convert.hex6_to_rgb( lista[i] )
            d = self.geometry.Trig_3D_Points_Distance( ps[0], ps[1], ps[2], pe[0], pe[1], pe[2] )
            if d < index[1]:
                index = [i , d]
        # Final Color
        rgb = self.convert.hex6_to_rgb( lista[index[0]] )
        # Move Location to Closest Point
        self.Pigmento_APPLY( "RGB", rgb[0], rgb[1], rgb[2], 0, self.cor )

    # Non Color
    def HEX_Sum( self, boolean ):
        self.hex_sum = boolean
        self.Update_Values()
        Krita.instance().writeSetting( DOCKER_NAME, "hex_sum", str( self.hex_sum ) )

    #endregion
    #region Extension

    # COR
    def Extension_PIN( self, SIGNAL_PIN ):
        self.Pin_Apply( SIGNAL_PIN )
    # KEYs
    def Extension_KEY_1( self, SIGNAL_KEY_1 ):
        self.Extension_KEY_Apply( self.key_1_chan, SIGNAL_KEY_1 * self.key_1_factor )
    def Extension_KEY_2( self, SIGNAL_KEY_2 ):
        self.Extension_KEY_Apply( self.key_2_chan, SIGNAL_KEY_2 * self.key_2_factor )
    def Extension_KEY_3( self, SIGNAL_KEY_3 ):
        self.Extension_KEY_Apply( self.key_3_chan, SIGNAL_KEY_3 * self.key_3_factor )
    def Extension_KEY_4( self, SIGNAL_KEY_4 ):
        self.Extension_KEY_Apply( self.key_4_chan, SIGNAL_KEY_4 * self.key_4_factor )
    def Extension_KEY_Apply( self, key, delta ):
        # AAA
        if key == "A 1":
            value = self.geometry.Limit_Float( self.cor["aaa_1"] + delta / krange["aaa_1"] )
            self.Pigmento_APPLY( "A", value, 0, 0, 0, self.cor )
        # RGB
        if key == "RGB 1":
            value = self.geometry.Limit_Float( self.cor["rgb_1"] + delta / krange["rgb_1"] )
            self.Pigmento_APPLY( "RGB", value, self.cor["rgb_2"], self.cor["rgb_3"], 0, self.cor )
        if key == "RGB 2":
            value = self.geometry.Limit_Float( self.cor["rgb_2"] + delta / krange["rgb_2"] )
            self.Pigmento_APPLY( "RGB", self.cor["rgb_1"], value, self.cor["rgb_3"], 0, self.cor )
        if key == "RGB 3":
            value = self.geometry.Limit_Float( self.cor["rgb_3"] + delta / krange["rgb_3"] )
            self.Pigmento_APPLY( "RGB", self.cor["rgb_1"], self.cor["rgb_2"], value, 0, self.cor )
        # CMY
        if key == "CMY 1":
            value = self.geometry.Limit_Float( self.cor["cmy_1"] + delta / krange["cmy_1"] )
            self.Pigmento_APPLY( "CMY", value, self.cor["cmy_2"], self.cor["cmy_3"], 0, self.cor )
        if key == "CMY 2":
            value = self.geometry.Limit_Float( self.cor["cmy_2"] + delta / krange["cmy_2"] )
            self.Pigmento_APPLY( "CMY", self.cor["cmy_1"], value, self.cor["cmy_3"], 0, self.cor )
        if key == "CMY 3":
            value = self.geometry.Limit_Float( self.cor["cmy_3"] + delta / krange["cmy_3"] )
            self.Pigmento_APPLY( "CMY", self.cor["cmy_1"], self.cor["cmy_2"], value, 0, self.cor )
        # CMYK
        if key == "CMYK 1":
            value = self.geometry.Limit_Float( self.cor["cmyk_1"] + delta / krange["cmyk_1"] )
            self.Pigmento_APPLY( "CMYK", value, self.cor["cmyk_2"], self.cor["cmyk_3"], self.cor["cmyk_4"], self.cor )
        if key == "CMYK 2":
            value = self.geometry.Limit_Float( self.cor["cmyk_2"] + delta / krange["cmyk_2"] )
            self.Pigmento_APPLY( "CMYK", self.cor["cmyk_1"], value, self.cor["cmyk_3"], self.cor["cmyk_4"], self.cor )
        if key == "CMYK 3":
            value = self.geometry.Limit_Float( self.cor["cmyk_3"] + delta / krange["cmyk_3"] )
            self.Pigmento_APPLY( "CMYK", self.cor["cmyk_1"], self.cor["cmyk_2"], value, self.cor["cmyk_4"], self.cor )
        if key == "CMYK 4":
            value = self.geometry.Limit_Float( self.cor["cmyk_4"] + delta / krange["cmyk_4"] )
            self.Pigmento_APPLY( "CMYK", self.cor["cmyk_1"], self.cor["cmyk_2"], self.cor["cmyk_3"], value, self.cor )
        # RYB
        if key == "RYB 1":
            value = self.geometry.Limit_Float( self.cor["ryb_1"] + delta / krange["ryb_1"] )
            self.Pigmento_APPLY( "RYB", value, self.cor["ryb_2"], self.cor["ryb_3"], 0, self.cor )
        if key == "RYB 2":
            value = self.geometry.Limit_Float( self.cor["ryb_2"] + delta / krange["ryb_2"] )
            self.Pigmento_APPLY( "RYB", self.cor["ryb_1"], value, self.cor["ryb_3"], 0, self.cor )
        if key == "RYB 3":
            value = self.geometry.Limit_Float( self.cor["ryb_3"] + delta / krange["ryb_3"] )
            self.Pigmento_APPLY( "RYB", self.cor["ryb_1"], self.cor["ryb_2"], value, 0, self.cor )
        # YUV
        if key == "YUV 1":
            value = self.geometry.Limit_Float( self.cor["yuv_1"] + delta / krange["yuv_1"] )
            self.Pigmento_APPLY( "YUV", value, self.cor["yuv_2"], self.cor["yuv_3"], 0, self.cor )
        if key == "YUV 2":
            value = self.geometry.Limit_Float( self.cor["yuv_2"] + delta / krange["yuv_2"] )
            self.Pigmento_APPLY( "YUV", self.cor["yuv_1"], value, self.cor["yuv_3"], 0, self.cor )
        if key == "YUV 3":
            value = self.geometry.Limit_Float( self.cor["yuv_3"] + delta / krange["yuv_3"] )
            self.Pigmento_APPLY( "YUV", self.cor["yuv_1"], self.cor["yuv_2"], value, 0, self.cor )

        # HSV
        if key == "HSV 1":
            value = self.geometry.Limit_Looper( self.cor["hsv_1"] + delta / krange["hsv_1"], 1 )
            self.Pigmento_APPLY( "HSV", value, self.cor["hsv_2"], self.cor["hsv_3"], 0, self.cor )
        if key == "HSV 2":
            value = self.geometry.Limit_Float( self.cor["hsv_2"] + delta / krange["hsv_2"] )
            self.Pigmento_APPLY( "HSV", self.cor["hsv_1"], value, self.cor["hsv_3"], 0, self.cor )
        if key == "HSV 3":
            value = self.geometry.Limit_Float( self.cor["hsv_3"] + delta / krange["hsv_3"] )
            self.Pigmento_APPLY( "HSV", self.cor["hsv_1"], self.cor["hsv_2"], value, 0, self.cor )
        # HSL
        if key == "HSL 1":
            value = self.geometry.Limit_Looper( self.cor["hsl_1"] + delta / krange["hsl_1"], 1 )
            self.Pigmento_APPLY( "HSL", value, self.cor["hsl_2"], self.cor["hsl_3"], 0, self.cor )
        if key == "HSL 2":
            value = self.geometry.Limit_Float( self.cor["hsl_2"] + delta / krange["hsl_2"] )
            self.Pigmento_APPLY( "HSL", self.cor["hsl_1"], value, self.cor["hsl_3"], 0, self.cor )
        if key == "HSL 3":
            value = self.geometry.Limit_Float( self.cor["hsl_3"] + delta / krange["hsl_3"] )
            self.Pigmento_APPLY( "HSL", self.cor["hsl_1"], self.cor["hsl_2"], value, 0, self.cor )
        # HCY
        if key == "HCY 1":
            value = self.geometry.Limit_Looper( self.cor["hcy_1"] + delta / krange["hcy_1"], 1 )
            self.Pigmento_APPLY( "HCY", value, self.cor["hcy_2"], self.cor["hcy_3"], 0, self.cor )
        if key == "HCY 2":
            value = self.geometry.Limit_Float( self.cor["hcy_2"] + delta / krange["hcy_2"] )
            self.Pigmento_APPLY( "HCY", self.cor["hcy_1"], value, self.cor["hcy_3"], 0, self.cor )
        if key == "HCY 3":
            value = self.geometry.Limit_Float( self.cor["hcy_3"] + delta / krange["hcy_3"] )
            self.Pigmento_APPLY( "HCY", self.cor["hcy_1"], self.cor["hcy_2"], value, 0, self.cor )
        # ARD
        if key == "ARD 1":
            value = self.geometry.Limit_Looper( self.cor["ard_1"] + delta / krange["ard_1"], 1 )
            self.Pigmento_APPLY( "ARD", value, self.cor["ard_2"], self.cor["ard_3"], 0, self.cor )
        if key == "ARD 2":
            value = self.geometry.Limit_Float( self.cor["ard_2"] + delta / krange["ard_2"] )
            self.Pigmento_APPLY( "ARD", self.cor["ard_1"], value, self.cor["ard_3"], 0, self.cor )
        if key == "ARD 3":
            value = self.geometry.Limit_Float( self.cor["ard_3"] + delta / krange["ard_3"] )
            self.Pigmento_APPLY( "ARD", self.cor["ard_1"], self.cor["ard_2"], value, 0, self.cor )

        # XYZ
        if key == "XYZ 1":
            value = self.geometry.Limit_Float( self.cor["xyz_1"] + delta / krange["xyz_1"] )
            self.Pigmento_APPLY( "XYZ", value, self.cor["xyz_2"], self.cor["xyz_3"], 0, self.cor )
        if key == "XYZ 2":
            value = self.geometry.Limit_Float( self.cor["xyz_2"] + delta / krange["xyz_2"] )
            self.Pigmento_APPLY( "XYZ", self.cor["xyz_1"], value, self.cor["xyz_3"], 0, self.cor )
        if key == "XYZ 3":
            value = self.geometry.Limit_Float( self.cor["xyz_3"] + delta / krange["xyz_3"] )
            self.Pigmento_APPLY( "XYZ", self.cor["xyz_1"], self.cor["xyz_2"], value, 0, self.cor )
        # XYY
        if key == "XYY 1":
            value = self.geometry.Limit_Float( self.cor["xyy_1"] + delta / krange["xyy_1"] )
            self.Pigmento_APPLY( "XYY", value, self.cor["xyy_2"], self.cor["xyy_3"], 0, self.cor )
        if key == "XYY 2":
            value = self.geometry.Limit_Float( self.cor["xyy_2"] + delta / krange["xyy_2"] )
            self.Pigmento_APPLY( "XYY", self.cor["xyy_1"], value, self.cor["xyy_3"], 0, self.cor )
        if key == "XYY 3":
            value = self.geometry.Limit_Float( self.cor["xyy_3"] + delta / krange["xyy_3"] )
            self.Pigmento_APPLY( "XYY", self.cor["xyy_1"], self.cor["xyy_2"], value, 0, self.cor )
        # LAB
        if key == "LAB 1":
            value = self.geometry.Limit_Float( self.cor["lab_1"] + delta / krange["lab_1"] )
            self.Pigmento_APPLY( "LAB", value, self.cor["lab_2"], self.cor["lab_3"], 0, self.cor )
        if key == "LAB 2":
            value = self.geometry.Limit_Float( self.cor["lab_2"] + delta / krange["lab_2"] )
            self.Pigmento_APPLY( "LAB", self.cor["lab_1"], value, self.cor["lab_3"], 0, self.cor )
        if key == "LAB 3":
            value = self.geometry.Limit_Float( self.cor["lab_3"] + delta / krange["lab_3"] )
            self.Pigmento_APPLY( "LAB", self.cor["lab_1"], self.cor["lab_2"], value, 0, self.cor )

        # LCH
        if key == "LCH 1":
            value = self.geometry.Limit_Float( self.cor["lch_1"] + delta / krange["lch_1"] )
            self.Pigmento_APPLY( "LCH", value, self.cor["lch_2"], self.cor["lch_3"], 0, self.cor )
        if key == "LCH 2":
            value = self.geometry.Limit_Float( self.cor["lch_2"] + delta / krange["lch_2"] )
            self.Pigmento_APPLY( "LCH", self.cor["lch_1"], value, self.cor["lch_3"], 0, self.cor )
        if key == "LCH 3":
            value = self.geometry.Limit_Float( self.cor["lch_3"] + delta / krange["lch_3"] )
            self.Pigmento_APPLY( "LCH", self.cor["lch_1"], self.cor["lch_2"], value, 0, self.cor )

        # KKK
        if key == "K 1":
            scale = int( self.geometry.Limit_Range( self.cor["kkk_scale"] + delta * 10, kkk_min_scale, kkk_max_scale ) )
            percent = self.convert.kkk_scale_to_percent( scale )
            self.Pigmento_APPLY( "KKK", percent, scale, 0, 0, self.cor )
    # LOCKs
    def Extension_LOCK( self, SIGNAL_LOCK ):
        if SIGNAL_LOCK == "CMYK":
            if self.layout.cmyk_4_label.isChecked():
                self.layout.cmyk_4_label.setChecked( False )
            else:
                self.layout.cmyk_4_label.setChecked( True )
        if SIGNAL_LOCK == "KKK":
            if self.layout.kkk_1_label.isChecked():
                self.layout.kkk_1_label.setChecked( False )
            else:
                self.layout.kkk_1_label.setChecked( True )

    #endregion
    #region Notifier

    # Notifier
    def Application_Closing( self ):
        pass
    def Configuration_Changed( self ):
        pass
    def Image_Closed( self ):
        pass
    def Image_Created( self ):
        pass
    def Image_Saved( self ):
        pass
    def View_Closed( self ):
        pass
    def View_Created( self ):
        pass
    def Window_Created( self ):
        # Module
        self.window = Krita.instance().activeWindow()
        # Signals
        self.window.activeViewChanged.connect( self.View_Changed )
        self.window.themeChanged.connect( self.Theme_Changed )
        self.window.windowClosed.connect( self.Window_Closed )
    def Window_IsBeingCreated( self ):
        pass

    # Window
    def View_Changed( self ):
        pass
    def Theme_Changed( self ):
        """
        Theme Breeze Dark
        alternateBase = #31363b
        base = #232629
        brightText = #ffffff
        button = #31363b
        buttonText = #eff0f1
        dark = #1d2023
        highlight = #3daee9
        highlightedText = #eff0f1
        light = #464d54
        link = #2980b9
        linkVisited = #7f8c8d
        mid = #2b3034
        midlight = #3c4248
        placeholderText = #eff0f1
        shadow = #151719
        text = #eff0f1
        toolTipBase = #31363b
        toolTipText = #eff0f1
        window = #31363b
        windowText = #eff0f1
        """

        # Read
        palette = QApplication.palette()
        # Theme Colors
        # Window ( Dark )
        w_alternate   = palette.alternateBase().color().name()
        w_base        = palette.base().color().name()
        w_button      = palette.button().color().name()
        w_dark        = palette.dark().color().name()
        w_light       = palette.light().color().name()
        w_mid         = palette.mid().color().name()
        w_midlight    = palette.midlight().color().name()
        w_shadow      = palette.shadow().color().name()
        w_tool_tip    = palette.toolTipBase().color().name()
        w_window      = palette.window().color().name()
        # Text ( Bright )
        t_bright      = palette.brightText().color().name()
        t_button      = palette.buttonText().color().name()
        t_highlighted = palette.highlightedText().color().name()
        t_placeholder = palette.placeholderText().color().name()
        t_text        = palette.text().color().name()
        t_tool_tip    = palette.toolTipText().color().name()
        t_window      = palette.windowText().color().name()
        # Color
        c_highlight   = palette.highlight().color().name()
        c_link        = palette.link().color().name()
        c_visited     = palette.linkVisited().color().name()
        # c_accent      = palette.accent().color().name() # qt6

        # Panels
        self.panel_huecircle.Set_Theme( t_button, w_dark, w_midlight )
        self.panel_gamut.Set_Theme( t_button, w_dark, w_midlight )
        # Panel Backgrounds
        self.layout.panel_fill.setStyleSheet( "#panel_fill{ background-color: " + w_base + "; }" )
        self.layout.panel_square.setStyleSheet( "#panel_square{ background-color: " + w_base + "; }" )
        self.layout.panel_hue.setStyleSheet( "#panel_hue{ background-color: " + w_base + "; }" )
        self.layout.panel_gamut.setStyleSheet( "#panel_gamut{ background-color: " + w_base + "; }" )
        self.layout.panel_hexagon.setStyleSheet( "#panel_hexagon{ background-color: " + w_base + "; }" )
        self.layout.panel_luma.setStyleSheet( "#panel_luma{ background-color: " + w_base + "; }" )
        self.layout.panel_dot.setStyleSheet( "#panel_dot{ background-color: " + w_base + "; }" )
        self.layout.panel_mask.setStyleSheet( "#panel_mask{ background-color: " + w_base + "; }" )

        # AAA
        self.aaa_1_slider.Set_Theme( t_button, w_dark )
        # RGB
        self.rgb_1_slider.Set_Theme( t_button, w_dark )
        self.rgb_2_slider.Set_Theme( t_button, w_dark )
        self.rgb_3_slider.Set_Theme( t_button, w_dark )
        # CMY
        self.cmy_1_slider.Set_Theme( t_button, w_dark )
        self.cmy_2_slider.Set_Theme( t_button, w_dark )
        self.cmy_3_slider.Set_Theme( t_button, w_dark )
        # CMYK
        self.cmyk_1_slider.Set_Theme( t_button, w_dark )
        self.cmyk_2_slider.Set_Theme( t_button, w_dark )
        self.cmyk_3_slider.Set_Theme( t_button, w_dark )
        self.cmyk_4_slider.Set_Theme( t_button, w_dark )
        # RYB
        self.ryb_1_slider.Set_Theme( t_button, w_dark )
        self.ryb_2_slider.Set_Theme( t_button, w_dark )
        self.ryb_3_slider.Set_Theme( t_button, w_dark )
        # YUV
        self.yuv_1_slider.Set_Theme( t_button, w_dark )
        self.yuv_2_slider.Set_Theme( t_button, w_dark )
        self.yuv_3_slider.Set_Theme( t_button, w_dark )
        # HSV
        self.hsv_1_slider.Set_Theme( t_button, w_dark )
        self.hsv_2_slider.Set_Theme( t_button, w_dark )
        self.hsv_3_slider.Set_Theme( t_button, w_dark )
        # HSL
        self.hsl_1_slider.Set_Theme( t_button, w_dark )
        self.hsl_2_slider.Set_Theme( t_button, w_dark )
        self.hsl_3_slider.Set_Theme( t_button, w_dark )
        # HCY
        self.hcy_1_slider.Set_Theme( t_button, w_dark )
        self.hcy_2_slider.Set_Theme( t_button, w_dark )
        self.hcy_3_slider.Set_Theme( t_button, w_dark )
        # ARD
        self.ard_1_slider.Set_Theme( t_button, w_dark )
        self.ard_2_slider.Set_Theme( t_button, w_dark )
        self.ard_3_slider.Set_Theme( t_button, w_dark )
        # XYZ
        self.xyz_1_slider.Set_Theme( t_button, w_dark )
        self.xyz_2_slider.Set_Theme( t_button, w_dark )
        self.xyz_3_slider.Set_Theme( t_button, w_dark )
        # XYY
        self.xyy_1_slider.Set_Theme( t_button, w_dark )
        self.xyy_2_slider.Set_Theme( t_button, w_dark )
        self.xyy_3_slider.Set_Theme( t_button, w_dark )
        # LAB
        self.lab_1_slider.Set_Theme( t_button, w_dark )
        self.lab_2_slider.Set_Theme( t_button, w_dark )
        self.lab_3_slider.Set_Theme( t_button, w_dark )
        # LCH
        self.lch_1_slider.Set_Theme( t_button, w_dark )
        self.lch_2_slider.Set_Theme( t_button, w_dark )
        self.lch_3_slider.Set_Theme( t_button, w_dark )
        # Kelvin
        self.kkk_1_slider.Set_Theme( t_button, w_dark )

        # Pole
        self.pole_slider.Set_Theme( t_button, w_dark )
        # Mixer
        for item in self.mixer_module:
            try:item["m"].Set_Theme( t_button, w_dark )
            except:pass

        # Style Sheets Dialog
        self.dialog.scroll_area_contents_option.setStyleSheet( "#scroll_area_contents_option{background-color: " + w_mid + ";}" )
        self.dialog.scroll_area_contents_color.setStyleSheet( "#scroll_area_contents_color{background-color: " + w_mid + ";}" )
        self.dialog.scroll_area_contents_system.setStyleSheet( "#scroll_area_contents_system{background-color: " + w_mid + ";}" )
    def Window_Closed( self ):
        pass

    #endregion
    #region Widget Events 

    def showEvent( self, event ):
        # UI
        self.Update_Size()
        # QTimer
        if check_timer >= 30:
            self.timer_pulse.start( check_timer )
    def resizeEvent( self, event ):
        # self.Resize_Print( event )
        self.Update_Size()
    def enterEvent( self, event ):
        # Variables
        self.cursor_inside = True
        # Check Krita/Clipboard Once before editing Pigmento
        if self.mode_index == 0:
            self.Pigmento_RELEASE()
        # Update
        if self.mode_index == 1:
            self.Pigmento_Update()
    def leaveEvent( self, event ):
        # Variables
        self.cursor_inside = False
        # Widgets
        self.Pigmento_RELEASE()
        self.Clear_Focus()
        # Save
        self.Mask_Write()
    def closeEvent( self, event ):
        # QTimer
        self.timer_pulse.stop()

    def eventFilter( self, source, event ):
        # Panels
        panels = [
            self.layout.panel_set,
            self.layout.panel_dot,
            self.layout.panel_mask,

            self.layout.aaa_slider,
            self.layout.rgb_slider,
            self.layout.cmy_slider,
            self.layout.cmyk_slider,
            self.layout.ryb_slider,
            self.layout.yuv_slider,
            self.layout.hsv_slider,
            self.layout.hsl_slider,
            self.layout.hcy_slider,
            self.layout.ard_slider,
            self.layout.xyz_slider,
            self.layout.xyy_slider,
            self.layout.lab_slider,
            self.layout.lch_slider,
            self.layout.kkk_slider,

            self.layout.pole_slider,
            self.layout.mixer_set,
            ]
        if ( event.type() == QEvent.Resize and source in panels ):
            self.Update_Size()
            return True

        # History
        if ( event.type() == QEvent.ContextMenu and source is self.layout.history_list ):
            self.Menu_Context_History( event )
            return True

        # Mode
        if ( event.type() == QEvent.MouseButtonPress and source is self.layout.mode ):
            self.Menu_Mode_Press( event )
            return True
        if ( event.type() == QEvent.Wheel and source is self.layout.mode ):
            self.Menu_Mode_Wheel( event )
            return True

        return super().eventFilter( source, event )

    def canvasChanged( self, canvas ):
        pass

    #endregion
    #region Notes

    """
    # Label Message
    self.layout.label.setText( "message" )

    # Pop Up Message
    QMessageBox.information( QWidget(), i18n( "Warnning" ), i18n( "message" ) )

    # Log Viewer Message
    QtCore.qDebug( f"value = { value }" )
    QtCore.qDebug( "message" )
    QtCore.qWarning( "message" )
    QtCore.qCritical( "message" )

    # qimage = QImage( byte_array, width, height, QImage.Format_RGBA8888 )
    """

    """
    # Krita Theme
    color_theme = QApplication.palette().color( QPalette.Window )
    if color_theme.value() > 128:
        self.color_1 = QColor( "#191919" )
        self.color_2 = QColor( "#e5e5e5" )
    else:
        self.color_1 = QColor( "#e5e5e5" )
        self.color_2 = QColor( "#191919" )
    """

    #endregion


"""
Investigate Krita
- YUV / YCbCr color conversion formula - YUV formula is RED and Blue inverted ? or is it Krita ?

Krita Bugs:
- Byte data of a U16 document is not in RGB like on the API notes but it is in BGR.
Pigmento Bugs
- Mixer in 16 bit goes crazy.
- Fix Linear RGB

Ideas To Do:
- Sample (Bit Depth + Color model )
O U8
O U16
- F16
- F32
- Profile UVD / ARD LUTs
- Implement OKLAB and OKHSV
- Hexagon have 2 cursors, one for Gamma and another projected in sRGB to correct the conversion

New:
- Sample Screen
- Faster display ( circles and cursor )
- New implementation of copy paste hex
- new masks on Hue and Gamut
- Sum is a seperate entity
- Pole Mixer with 3 colors. 1 dynamic color
- auto hex copy with new history color
- bug fixed mask reset
- qol Panel Mask Pin when saved sets the Alpha back to 1
"""
