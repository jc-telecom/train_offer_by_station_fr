import pandas as pd
import numpy as np
import streamlit as st
from datetime import datetime
import time

from typing import Type, List, Dict, Any

import locale
try:
    locale.setlocale(locale.LC_ALL, 'fr_FR.UTF-8')
except locale.Error:
    locale.setlocale(locale.LC_ALL, '')  # Set to system default
